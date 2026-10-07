/**
 * M2.2b (T5), V-06 (a consulta) e RF-17: a fonte do risco da carteira (`useRiskSource`) com a
 * consulta repetida genérica (`usePolling`), como a página da carteira as usa, com relógio
 * falso:
 *
 * - um erro 500 ou 429 numa releitura **mantém o `data`** e um novo `GET` sai 5 s depois;
 * - 401 chama o `expired()` da sessão, e a consulta para;
 * - 404 liga `notFound`, zera o `data`, não sobe o `attempt`, e nenhum `GET` sai 5 s depois;
 * - o corpo do 202 (`accept`) com `in_progress` faz um `GET` 5 s depois;
 * - a consulta para quando não há `in_progress` e ao desmontar;
 * - a resposta de pedido já substituído é descartada.
 *
 * A fonte roda dentro do `SessionProvider` de verdade, com o `auth/me` logado.
 */
import { act, cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { PortfolioProgress, PortfolioRisk, PortfolioRun } from "../src/api/types";
import { shouldPollPortfolio } from "../src/portfolio/riskState";
import { type RiskSource, useRiskSource } from "../src/portfolio/useRiskSource";
import { POLL_INTERVAL_MS, usePolling } from "../src/risk/usePolling";
import {
  type SessionApi,
  SessionProvider,
  useSession,
} from "../src/session/SessionProvider";
import type { Me } from "../src/session/types";

// ---------------------------------------------------------------- os dados

const ID = "5b0e6c1e-0000-4000-8000-000000000000";
const RISK_PATH = `/api/v1/portfolios/${ID}/risk`;
const ME_PATH = "/api/v1/auth/me";

const ME: Me = {
  email: "ana@exemplo.com",
  name: "Ana",
  role: "admin",
  must_change_password: false,
  is_staff: false,
  organization: { name: "Ana", slug: "ana", is_personal: true },
};

const RUN: PortfolioRun = {
  id: 31,
  version: 2,
  status: "ok",
  calculated_at: "2026-10-02T18:00:00-03:00",
  finished_at: "2026-10-02T18:02:30-03:00",
  engine_version: "0.5.0",
  seed: 42,
  train_window_days: 252,
  first_date: "2016-10-03",
  as_of_date: "2026-10-02",
  session_count: 2470,
  train_count: 252,
  test_count: 2218,
  requested_models: [],
  series_sha256: "a".repeat(64),
  price_run_id: 7,
  requested_by: { email: "ana@exemplo.com", name: "Ana" },
  results: [],
  summary: [],
};

function progress(written: number): PortfolioProgress {
  return {
    id: 32,
    version: 2,
    calculated_at: "2026-10-03T10:00:00-03:00",
    requested_models: ["historical"],
    results_written: written,
    results_expected: 18,
  };
}

function risk(
  latest: PortfolioRun | null,
  inProgress: PortfolioProgress | null,
): PortfolioRisk {
  return {
    portfolio_id: ID,
    version: 2,
    notional: null,
    latest,
    in_progress: inProgress,
  };
}

// ---------------------------------------------------------------- o servidor falso

type Reply =
  | { status: number; body: unknown }
  | Promise<{ status: number; body: unknown }>;

let riskQueue: Reply[] = [];
let calls: string[] = [];
let unexpected: string[] = [];

const ok = (body: PortfolioRisk): Reply => ({
  status: 200,
  body: { portfolio_risk: body },
});
const fail = (status: number, code: string): Reply => ({
  status,
  body: { error: { code, message: `falhou: ${code}`, details: {} } },
});

/** Uma resposta que só sai quando o teste mandar. */
function deferred(): { reply: Reply; resolve(value: Awaited<Reply>): void } {
  let resolve: (value: Awaited<Reply>) => void = () => {};
  const reply = new Promise<Awaited<Reply>>((r) => {
    resolve = r;
  });
  return { reply, resolve };
}

function stubFetch(): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: RequestInit = {}) => {
      const method = init.method ?? "GET";
      calls.push(`${method} ${url}`);
      let reply: Awaited<Reply>;
      if (method === "GET" && url === ME_PATH) {
        reply = { status: 200, body: ME };
      } else if (method === "GET" && url === RISK_PATH && riskQueue.length > 0) {
        reply = await (riskQueue.shift() as Reply);
      } else {
        unexpected.push(`${method} ${url}`);
        return new Promise<Response>(() => {});
      }
      return new Response(JSON.stringify(reply.body), {
        status: reply.status,
        headers: { "Content-Type": "application/json" },
      });
    }),
  );
}

const riskCalls = () => calls.filter((c) => c === `GET ${RISK_PATH}`).length;

// ---------------------------------------------------------------- a página, reduzida

let current: {
  source: RiskSource;
  reload(): void;
  accept(body: PortfolioRisk): void;
} | null = null;
let session: SessionApi | null = null;

/** A carteira não faz nada no fim da consulta (RF-17). */
const noop = () => {};

function Probe() {
  const fonte = useRiskSource(ID);
  usePolling(
    fonte.source.data,
    shouldPollPortfolio,
    fonte.reload,
    noop,
    fonte.source.attempt,
  );
  current = fonte;
  session = useSession();
  return null;
}

function mount() {
  return render(
    <SessionProvider>
      <Probe />
    </SessionProvider>,
  );
}

const src = (): RiskSource => (current as NonNullable<typeof current>).source;

/** Deixa as promessas e os efeitos correrem, e avança o relógio falso `ms`. */
async function advance(ms: number): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
  riskQueue = [];
  calls = [];
  unexpected = [];
  current = null;
  session = null;
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  expect(unexpected).toEqual([]);
});

// ---------------------------------------------------------------- os testes

describe("a primeira leitura", () => {
  it("carregando até voltar; depois, o corpo e o attempt 1", async () => {
    const held = deferred();
    riskQueue = [held.reply];
    mount();
    await advance(0);
    expect(src()).toMatchObject({ data: null, loading: true, attempt: 0 });
    await act(async () => {
      held.resolve(ok(risk(RUN, null)) as Awaited<Reply>);
    });
    await advance(0);
    expect(src()).toMatchObject({ loading: false, attempt: 1, firstError: null });
    expect(src().data).toEqual(risk(RUN, null));
  });

  it("o erro da primeira leitura vai a firstError, e não há consulta repetida", async () => {
    riskQueue = [fail(503, "service_unavailable")];
    mount();
    await advance(0);
    expect(src().data).toBeNull();
    expect(src().loading).toBe(false);
    expect(src().firstError?.status).toBe(503);
    await advance(3 * POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(1);
  });

  it("o tentar de novo depois do erro volta a carregando e lê", async () => {
    riskQueue = [fail(500, "internal_error"), ok(risk(null, null))];
    mount();
    await advance(0);
    act(() => current?.reload());
    expect(src()).toMatchObject({ loading: true, firstError: null });
    await advance(0);
    expect(src()).toMatchObject({ loading: false, firstError: null });
    expect(src().data).toEqual(risk(null, null));
    expect(riskCalls()).toBe(2);
  });
});

describe("a consulta repetida (D-182)", () => {
  it.each([
    [500, "internal_error"],
    [429, "too_many_requests"],
    [0, "network"],
  ])(
    "um erro %i numa releitura mantém o data, e um novo GET sai 5 s depois",
    async (status, code) => {
      const first = risk(RUN, progress(3));
      const errorReply: Reply =
        status === 0
          ? Promise.reject(new TypeError("Failed to fetch"))
          : fail(status, code);
      if (status === 0) (errorReply as Promise<unknown>).catch(() => {});
      riskQueue = [ok(first), errorReply, ok(risk(RUN, progress(9)))];
      mount();
      await advance(0);
      expect(riskCalls()).toBe(1);
      expect(src().attempt).toBe(1);
      expect(src().data).toEqual(first);
      const kept = src().data;

      await advance(POLL_INTERVAL_MS);
      expect(riskCalls()).toBe(2);
      // O erro: o data é o mesmo objeto de antes, o attempt subiu.
      expect(src().data).toBe(kept);
      expect(src().attempt).toBe(2);
      expect(src().loading).toBe(false);

      await advance(POLL_INTERVAL_MS - 1);
      expect(riskCalls()).toBe(2);
      await advance(1);
      expect(riskCalls()).toBe(3);
      expect(src().data?.in_progress?.results_written).toBe(9);
      expect(src().firstError).toBeNull();
    },
  );

  it("dois erros seguidos: a consulta segue, e o data fica", async () => {
    const first = risk(RUN, progress(3));
    riskQueue = [
      ok(first),
      fail(500, "internal_error"),
      fail(429, "too_many_requests"),
      ok(risk(RUN, null)),
    ];
    mount();
    await advance(0);
    const kept = src().data;
    expect(kept).toEqual(first);
    await advance(POLL_INTERVAL_MS);
    await advance(POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(3);
    expect(src().data).toBe(kept);
    await advance(POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(4);
    expect(src().data?.in_progress).toBeNull();
  });

  it("para quando não há mais in_progress", async () => {
    riskQueue = [ok(risk(null, progress(3))), ok(risk(RUN, null))];
    mount();
    await advance(0);
    await advance(POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(2);
    await advance(4 * POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(2);
  });

  it("sem in_progress na primeira leitura, nenhuma consulta", async () => {
    riskQueue = [ok(risk(RUN, null))];
    mount();
    await advance(4 * POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(1);
  });

  it("para ao desmontar", async () => {
    riskQueue = [ok(risk(null, progress(3)))];
    const view = mount();
    await advance(0);
    view.unmount();
    await advance(4 * POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(1);
  });
});

describe("401 e 404 não mantêm o estado", () => {
  it("401 numa releitura chama expired(), e a consulta para", async () => {
    riskQueue = [ok(risk(RUN, progress(3))), fail(401, "not_authenticated")];
    mount();
    await advance(0);
    expect(session?.status).toBe("authenticated");
    await advance(POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(2);
    expect(session?.status).toBe("anonymous");
    expect(session?.status === "anonymous" && session.ended).toBe(true);
    expect(src().attempt).toBe(1);
    await advance(4 * POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(2);
  });

  it("401 na primeira leitura chama expired()", async () => {
    riskQueue = [fail(401, "not_authenticated")];
    mount();
    await advance(0);
    expect(session?.status === "anonymous" && session.ended).toBe(true);
  });

  it("404 numa releitura: notFound, data nulo, o attempt não sobe, e nenhum GET 5 s depois", async () => {
    riskQueue = [ok(risk(RUN, progress(3))), fail(404, "portfolio_not_found")];
    mount();
    await advance(0);
    await advance(POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(2);
    expect(src()).toMatchObject({
      notFound: true,
      data: null,
      loading: false,
      attempt: 1,
    });
    await advance(4 * POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(2);
    expect(session?.status).toBe("authenticated");
  });

  it("404 na primeira leitura: notFound", async () => {
    riskQueue = [fail(404, "portfolio_not_found")];
    mount();
    await advance(0);
    expect(src()).toMatchObject({
      notFound: true,
      data: null,
      loading: false,
      attempt: 0,
    });
  });
});

describe("o 202 e a resposta substituída", () => {
  it("o corpo do 202 com in_progress entra como a leitura, e um GET sai 5 s depois", async () => {
    riskQueue = [ok(risk(null, null)), ok(risk(null, progress(5)))];
    mount();
    await advance(0);
    await advance(2 * POLL_INTERVAL_MS);
    expect(riskCalls()).toBe(1);

    const accepted = risk(null, progress(0));
    act(() => current?.accept(accepted));
    expect(src().data).toBe(accepted);
    expect(src().attempt).toBe(2);
    await advance(POLL_INTERVAL_MS - 1);
    expect(riskCalls()).toBe(1);
    await advance(1);
    expect(riskCalls()).toBe(2);
    expect(src().data?.in_progress?.results_written).toBe(5);
  });

  it("a resposta de um pedido já substituído por reload() é descartada", async () => {
    const old = deferred();
    riskQueue = [old.reply, ok(risk(RUN, null))];
    mount();
    await advance(0);
    act(() => current?.reload());
    await advance(0);
    expect(riskCalls()).toBe(2);
    expect(src().data).toEqual(risk(RUN, null));
    const attempt = src().attempt;

    await act(async () => {
      old.resolve(ok(risk(null, progress(1))) as Awaited<Reply>);
    });
    await advance(0);
    expect(src().data).toEqual(risk(RUN, null));
    expect(src().attempt).toBe(attempt);
  });

  it("um erro de pedido substituído também é descartado", async () => {
    const old = deferred();
    riskQueue = [ok(risk(RUN, null)), old.reply, ok(risk(RUN, null))];
    mount();
    await advance(0);
    act(() => current?.reload());
    act(() => current?.reload());
    await advance(0);
    const attempt = src().attempt;
    await act(async () => {
      old.resolve(fail(404, "portfolio_not_found") as Awaited<Reply>);
    });
    await advance(0);
    expect(src()).toMatchObject({ notFound: false, attempt });
    expect(src().data).toEqual(risk(RUN, null));
  });

  it("a leitura em voo antes do 202 é descartada", async () => {
    const inFlight = deferred();
    riskQueue = [ok(risk(RUN, null)), inFlight.reply];
    mount();
    await advance(0);
    act(() => current?.reload());
    const accepted = risk(RUN, progress(0));
    act(() => current?.accept(accepted));
    await act(async () => {
      inFlight.resolve(ok(risk(RUN, null)) as Awaited<Reply>);
    });
    await advance(0);
    expect(src().data).toBe(accepted);
  });
});
