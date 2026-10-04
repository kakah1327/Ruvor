/**
 * V-11 do M2.4 (estados e releitura): a tabela de `labState`, uma linha por estado e as
 * combinações vizinhas — a ordem das perguntas é o contrato (RF-14) —; a de `readyNote`, no
 * máximo uma nota, na ordem falha → motor → partial; a promessa de nova tentativa só com o
 * ativo `active`; e `useLabPolling` com relógio falso (RF-18): não começa na montagem nem sem
 * `pending`, começa quando o `reloadToken` muda, para no `latest`, para em 120 000 ms e pausa
 * com a aba oculta.
 */
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../src/api/client";
import type { Load } from "../src/api/resource";
import type { Lab, LabFailure, LabRun } from "../src/api/types";
import { labState, promisesRetry, readyNote } from "../src/lab/state";
import { LAB_POLL_WINDOW_MS, useLabPolling } from "../src/lab/useLabPolling";
import { MIN_SESSIONS } from "../src/risk/config";
import { POLL_INTERVAL_MS } from "../src/risk/usePolling";

// ---------------------------------------------------------------- os dados

function run(over: Partial<LabRun> = {}): LabRun {
  return {
    id: 3,
    calculated_at: "2026-10-04T04:43:02.871602-03:00",
    finished_at: "2026-10-04T04:43:07.030032-03:00",
    status: "ok",
    origin: "command",
    engine_version: "0.4.0",
    seed: 42,
    train_window_days: 252,
    first_price_date: "2016-09-22",
    decade_end: "2026-09-22",
    as_of_date: "2026-09-22",
    price_count: 2491,
    train_count: 252,
    test_count: 2238,
    year_count: 9,
    price_run: {
      id: 18,
      source: "yahoo-chart",
      started_at: "2026-10-01T22:26:25-03:00",
      finished_at: "2026-10-01T22:26:28-03:00",
    },
    price_fingerprint:
      "d2a0cec292f30a823ef94e74ce31da3d72a992fb349b48ccd54e8f4fb9710a44",
    results: [],
    ...over,
  };
}

const FAILURE: LabFailure = {
  id: 9,
  calculated_at: "2026-10-05T19:42:10-03:00",
  engine_version: "0.4.0",
  error: "série mudou durante o cálculo",
};

const COMPLETE = {
  first_price_date: "2016-09-22",
  end_date: "2026-09-22",
  last_price_date: "2026-10-02",
  complete: true,
  sessions: 2491,
};
const INCOMPLETE = {
  first_price_date: "2016-10-28",
  end_date: "2026-10-28",
  last_price_date: "2026-10-02",
  complete: false,
  sessions: 2474,
};
const NO_PRICE = {
  first_price_date: null,
  end_date: null,
  last_price_date: null,
  complete: false,
  sessions: 0,
};

function lab(over: Partial<Lab> = {}): Lab {
  return {
    ticker: "ITUB4",
    active: true,
    decade: COMPLETE,
    risk_engine_version: "0.4.0",
    pending: false,
    latest: null,
    last_failure: null,
    ...over,
  };
}

const okLoad = (data: Lab): Load<Lab> => ({ state: "ok", data });

// ---------------------------------------------------------------- labState

describe("V-11 — labState, na ordem do RF-14", () => {
  it.each([
    ["carregando", { state: "loading" } as Load<Lab>, "LOADING"],
    [
      "erro da leitura",
      {
        state: "error",
        error: new ApiError(500, "internal_error", "falhou"),
      } as Load<Lab>,
      "ERROR",
    ],
    ["latest presente", okLoad(lab({ latest: run() })), "READY"],
    [
      "latest presente vence a falha, o pending e o inativo",
      okLoad(
        lab({ latest: run(), last_failure: FAILURE, pending: true, active: false }),
      ),
      "READY",
    ],
    ["latest nulo, last_failure", okLoad(lab({ last_failure: FAILURE })), "FAILED"],
    [
      "a falha vence o pending",
      okLoad(lab({ last_failure: FAILURE, pending: true })),
      "FAILED",
    ],
    ["latest nulo, pending", okLoad(lab({ pending: true })), "PENDING"],
    ["inativo", okLoad(lab({ active: false })), "INACTIVE"],
    [
      "inativo com a década incompleta → INACTIVE",
      okLoad(lab({ active: false, decade: INCOMPLETE })),
      "INACTIVE",
    ],
    ["sem a década", okLoad(lab({ decade: INCOMPLETE })), "NO_DECADE"],
    [
      "sem a década, mesmo sem risco",
      okLoad(lab({ decade: INCOMPLETE, risk_engine_version: null })),
      "NO_DECADE",
    ],
    [
      "completa e curta → SHORT",
      okLoad(lab({ decade: { ...COMPLETE, sessions: MIN_SESSIONS - 1 } })),
      "SHORT",
    ],
    [
      "completa com o mínimo exato, sem risco → NO_RISK",
      okLoad(
        lab({
          decade: { ...COMPLETE, sessions: MIN_SESSIONS },
          risk_engine_version: null,
        }),
      ),
      "NO_RISK",
    ],
    [
      "completa, suficiente, sem risco → NO_RISK",
      okLoad(lab({ risk_engine_version: null })),
      "NO_RISK",
    ],
    [
      "sem preço → NO_RISK",
      okLoad(lab({ decade: NO_PRICE, risk_engine_version: null })),
      "NO_RISK",
    ],
  ])("%s", (_caso, load, state) => {
    expect(labState(load)).toBe(state);
  });
});

// ---------------------------------------------------------------- readyNote

describe("V-11 — readyNote: no máximo uma nota", () => {
  it.each([
    [
      "falha + motor diferente → failure",
      lab({ latest: run(), last_failure: FAILURE, risk_engine_version: "0.5.0" }),
      "failure",
    ],
    [
      "falha + partial → failure",
      lab({ latest: run({ status: "partial" }), last_failure: FAILURE }),
      "failure",
    ],
    [
      "motor diferente + partial → engine",
      lab({ latest: run({ status: "partial" }), risk_engine_version: "0.5.0" }),
      "engine",
    ],
    [
      "mesmo motor + partial → partial",
      lab({ latest: run({ status: "partial" }) }),
      "partial",
    ],
    ["ok do mesmo motor → null", lab({ latest: run() }), null],
    [
      "motor diferente no ativo inativo → sem a nota do motor",
      lab({ latest: run(), risk_engine_version: "0.5.0", active: false }),
      null,
    ],
    [
      "motor diferente + partial no inativo → partial",
      lab({
        latest: run({ status: "partial" }),
        risk_engine_version: "0.5.0",
        active: false,
      }),
      "partial",
    ],
    [
      "sem versão do risco → sem a nota do motor",
      lab({ latest: run(), risk_engine_version: null }),
      null,
    ],
  ])("%s", (_caso, data, note) => {
    expect(readyNote(data)).toBe(note);
  });
});

describe("V-11 — a promessa de nova tentativa só com o ativo active", () => {
  it.each([
    ["FAILED, ativo", lab({ last_failure: FAILURE }), true],
    ["FAILED, inativo", lab({ last_failure: FAILURE, active: false }), false],
    [
      "nota failure, inativo",
      lab({ latest: run(), last_failure: FAILURE, active: false }),
      false,
    ],
    ["nota partial, ativo", lab({ latest: run({ status: "partial" }) }), true],
    [
      "nota partial, inativo",
      lab({ latest: run({ status: "partial" }), active: false }),
      false,
    ],
  ])("%s", (_caso, data, promise) => {
    expect(promisesRetry(data)).toBe(promise);
  });
});

// ---------------------------------------------------------------- useLabPolling

describe("V-11 — useLabPolling: a releitura limitada (RF-18)", () => {
  let visibility: DocumentVisibilityState = "visible";
  const setVisibility = (state: DocumentVisibilityState) => {
    visibility = state;
    document.dispatchEvent(new Event("visibilitychange"));
  };

  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    visibility = "visible";
    vi.spyOn(document, "visibilityState", "get").mockImplementation(() => visibility);
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  type Props = { data: Lab | null; token: number };
  function mount(initial: Props) {
    const reload = vi.fn();
    const hook = renderHook(
      ({ data, token }: Props) => useLabPolling(data, reload, token),
      {
        initialProps: initial,
      },
    );
    return { reload, ...hook };
  }
  const advance = (ms: number) =>
    act(() => {
      vi.advanceTimersByTime(ms);
    });

  it("não começa na montagem, mesmo com pending", () => {
    const { reload } = mount({ data: lab({ pending: true }), token: 0 });
    advance(LAB_POLL_WINDOW_MS + 10_000);
    expect(reload).not.toHaveBeenCalled();
  });

  it("não começa sem pending, mesmo com o reloadToken mudando", () => {
    const { reload, rerender } = mount({ data: lab(), token: 0 });
    rerender({ data: lab(), token: 1 });
    advance(LAB_POLL_WINDOW_MS);
    expect(reload).not.toHaveBeenCalled();
  });

  it("começa quando o reloadToken muda, e relê a cada POLL_INTERVAL_MS depois de cada resposta", () => {
    const { reload, rerender } = mount({ data: lab({ pending: true }), token: 0 });
    rerender({ data: lab({ pending: true }), token: 1 });
    advance(POLL_INTERVAL_MS - 1);
    expect(reload).toHaveBeenCalledTimes(0);
    advance(1);
    expect(reload).toHaveBeenCalledTimes(1);
    // a resposta chega (um objeto novo), ainda pending: o próximo, 5 s depois
    rerender({ data: lab({ pending: true }), token: 1 });
    advance(POLL_INTERVAL_MS);
    expect(reload).toHaveBeenCalledTimes(2);
  });

  it("começa quando o /lab novo, depois do reloadToken, chega com pending", () => {
    const { reload, rerender } = mount({
      data: lab({ risk_engine_version: null }),
      token: 0,
    });
    rerender({ data: lab({ risk_engine_version: null }), token: 1 });
    advance(POLL_INTERVAL_MS);
    expect(reload).not.toHaveBeenCalled();
    rerender({ data: lab({ pending: true }), token: 1 });
    advance(POLL_INTERVAL_MS);
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("para no primeiro /lab com latest", () => {
    const { reload, rerender } = mount({ data: lab({ pending: true }), token: 0 });
    rerender({ data: lab({ pending: true }), token: 1 });
    advance(POLL_INTERVAL_MS);
    expect(reload).toHaveBeenCalledTimes(1);
    rerender({ data: lab({ latest: run(), pending: false }), token: 1 });
    // um /lab ainda pending depois não reabre a janela
    rerender({ data: lab({ pending: true }), token: 1 });
    advance(LAB_POLL_WINDOW_MS);
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("para no primeiro /lab com last_failure", () => {
    const { reload, rerender } = mount({ data: lab({ pending: true }), token: 0 });
    rerender({ data: lab({ pending: true }), token: 1 });
    rerender({ data: lab({ last_failure: FAILURE, pending: true }), token: 1 });
    advance(LAB_POLL_WINDOW_MS);
    expect(reload).not.toHaveBeenCalled();
  });

  it("para em 120 000 ms", () => {
    const { reload, rerender } = mount({ data: lab({ pending: true }), token: 0 });
    rerender({ data: lab({ pending: true }), token: 1 });
    // cada resposta chega na hora, sempre pending
    // (de 5 em 5 s: o efeito que agenda o próximo só roda quando o `act` de cada passo termina)
    for (let t = 0; t < LAB_POLL_WINDOW_MS; t += POLL_INTERVAL_MS) {
      const before = reload.mock.calls.length;
      advance(POLL_INTERVAL_MS);
      if (reload.mock.calls.length > before)
        rerender({ data: lab({ pending: true }), token: 1 });
    }
    const within = reload.mock.calls.length;
    // 23 ou 24: o pedido dos 120 000 ms empata com o fim da janela
    expect(within).toBeGreaterThanOrEqual(LAB_POLL_WINDOW_MS / POLL_INTERVAL_MS - 1);
    expect(within).toBeLessThanOrEqual(LAB_POLL_WINDOW_MS / POLL_INTERVAL_MS);
    for (let t = 0; t < 60_000; t += POLL_INTERVAL_MS) {
      advance(POLL_INTERVAL_MS);
      rerender({ data: lab({ pending: true }), token: 1 });
    }
    expect(reload).toHaveBeenCalledTimes(within);
  });

  it("um reloadToken novo abre outra janela", () => {
    const { reload, rerender } = mount({ data: lab({ pending: true }), token: 0 });
    rerender({ data: lab({ pending: true }), token: 1 });
    advance(LAB_POLL_WINDOW_MS + POLL_INTERVAL_MS);
    const first = reload.mock.calls.length;
    rerender({ data: lab({ pending: true }), token: 2 });
    advance(POLL_INTERVAL_MS);
    expect(reload).toHaveBeenCalledTimes(first + 1);
  });

  it("pausa com a aba oculta; ao voltar, pede na hora", () => {
    const { reload, rerender } = mount({ data: lab({ pending: true }), token: 0 });
    rerender({ data: lab({ pending: true }), token: 1 });
    act(() => setVisibility("hidden"));
    advance(30_000);
    expect(reload).not.toHaveBeenCalled();
    act(() => setVisibility("visible"));
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("desmontar cancela", () => {
    const { reload, rerender, unmount } = mount({
      data: lab({ pending: true }),
      token: 0,
    });
    rerender({ data: lab({ pending: true }), token: 1 });
    advance(1000);
    unmount();
    advance(LAB_POLL_WINDOW_MS);
    expect(reload).not.toHaveBeenCalled();
  });
});
