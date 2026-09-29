/**
 * V-12 — o acompanhamento (RF-20), com relógio falso: o `/risk` é pedido de novo a cada 5 s
 * enquanto houver `in_progress` ou pedido aberto — inclusive no E3 com `in_progress`, e com
 * `in_progress` presente e pedido nulo; ao terminar, em E1 **e** em E7, a tela recarrega as
 * cinco rotas (o cabeçalho passa de "sem preço" ao último fechamento); para ao sair da tela; a
 * aba oculta não pede, e voltar a ficar visível pede na hora. E o `data-risk-state` estável
 * durante o `reloadAll()`.
 */
import { act, cleanup, render, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { routes } from "../src/App";
import {
  type AssetDetail,
  type ComputeRequest,
  type InProgress,
  MODEL_ORDER,
  type Risk,
  type RiskResult,
  type RiskRun,
} from "../src/api/types";
import { TEXTOS } from "../src/content/textos";
import { formatCurrency } from "../src/format/numbers";

vi.mock("uplot", () => {
  class FakeUPlot {
    static paths = { bars: () => ({}) };
    static tzDate = (date: Date) => date;
    over = document.createElement("div");
    setScale() {}
    setSize() {}
    destroy() {}
  }
  return { default: FakeUPlot };
});

// ---------------------------------------------------------------- os dados

const NO_PRICE: AssetDetail = {
  ticker: "AALR3",
  name: "ALLIANÇA SAÚDE E PARTICIPAÇÕES S.A.",
  trading_name: "ALLIAR",
  kind: "stock",
  sector: "Saúde",
  status: "active",
  has_prices: false,
  subsector: null,
  segment: null,
  listing_segment: null,
  last_price: null,
};

const WITH_PRICE: AssetDetail = {
  ...NO_PRICE,
  has_prices: true,
  last_price: { date: "2026-09-29", close: "12.340000", adj_close: "12.340000" },
};

function result(model: string, alpha: "0.0500" | "0.0100"): RiskResult {
  return {
    model_name: model as RiskResult["model_name"],
    model_category: "traditional",
    alpha,
    hyperparameters: {},
    var_latest: "0.0300000000",
    var_mean: "0.0300000000",
    violations: 10,
    expected_violations: "11.000000",
    kupiec_passed: true,
    kupiec_p_value: "0.5000000000",
    christoffersen_passed: true,
    christoffersen_p_value: "0.5000000000",
    dq_passed: true,
    dq_p_value: "0.5000000000",
    basel_zone: null,
    adequate: true,
    error: "",
    reused_snapshots: null,
    trained_snapshots: null,
  };
}

function run(status: RiskRun["status"]): RiskRun {
  return {
    id: 70,
    calculated_at: "2026-09-29T14:03:00-03:00",
    finished_at: "2026-09-29T14:05:00-03:00",
    status,
    engine_version: "0.3.0",
    seed: 42,
    train_window_days: 252,
    as_of_date: "2026-09-29",
    first_price_date: "2016-09-22",
    price_count: 2487,
    train_count: 252,
    test_count: 2235,
    price_run: {
      id: 9,
      source: "yahoo-chart",
      started_at: "2026-09-29T14:02:00-03:00",
      finished_at: "2026-09-29T14:02:30-03:00",
    },
    requested_models: [...MODEL_ORDER],
    full_recompute: false,
    results:
      status === "failed"
        ? []
        : MODEL_ORDER.flatMap((m) => [result(m, "0.0500"), result(m, "0.0100")]),
  };
}

const inProgress = (w: number): InProgress => ({
  id: 70,
  calculated_at: "2026-09-29T14:03:00-03:00",
  requested_models: [...MODEL_ORDER],
  results_written: w,
  results_expected: 18,
});

const request = (over: Partial<ComputeRequest>): ComputeRequest => ({
  id: 41,
  status: "queued",
  requested_at: "2026-09-29T14:02:11-03:00",
  finished_at: null,
  reason: "",
  error: "",
  risk_run_id: null,
  ...over,
});

const risk = (over: Partial<Risk> = {}): Risk => ({
  ticker: "AALR3",
  covered: false,
  latest: null,
  in_progress: null,
  request: null,
  ...over,
});

/** Calculando, com `in_progress` presente e **pedido nulo**. */
const E4_NO_REQUEST = risk({ in_progress: inProgress(4) });
const E5_QUEUED = risk({ request: request({ status: "queued" }) });
const E3_RECALC = risk({ latest: run("failed"), in_progress: inProgress(2) });
const E1 = risk({ covered: true, latest: run("ok") });
const E7 = risk({ request: request({ status: "failed", reason: "falhou na coleta" }) });

// ---------------------------------------------------------------- o duplo do fetch

type Route = "asset" | "prices" | "events" | "metrics" | "risk";
type Call = { route: Route; resolve: (body: unknown) => void };

let calls: Call[] = [];
/** As respostas do `/risk`, em ordem; `null` deixa o pedido pendente. A última se repete. */
let riskQueue: (Risk | null)[] = [];
let assetBody: AssetDetail = NO_PRICE;

function routeOf(url: string): Route {
  const match = /^\/api\/v1\/assets\/[^/]+(?:\/(prices|events|metrics|risk))?$/.exec(
    url,
  );
  if (match === null) throw new Error(`pedido inesperado: ${url}`);
  return (match[1] as Route | undefined) ?? "asset";
}

function bodyOf(route: Route): unknown | null {
  switch (route) {
    case "asset":
      return assetBody;
    case "prices":
      return { ticker: "AALR3", from: null, to: null, results: [] };
    case "events":
      return { ticker: "AALR3", results: [] };
    case "metrics":
      return { ticker: "AALR3", metric: null };
    case "risk":
      return riskQueue.length > 1 ? riskQueue.shift() : riskQueue[0];
  }
}

function stubFetch(): void {
  calls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url: string) =>
        new Promise<Response>((resolve) => {
          const route = routeOf(url);
          // Como o `response.json()` de verdade, cada resposta é um objeto novo.
          const call: Call = {
            route,
            resolve: (body) =>
              resolve({
                ok: true,
                status: 200,
                json: async () => structuredClone(body),
              } as Response),
          };
          calls.push(call);
          const body = bodyOf(route);
          if (body !== null) call.resolve(body);
        }),
    ),
  );
}

let visibility: DocumentVisibilityState = "visible";

function setVisibility(state: DocumentVisibilityState): void {
  visibility = state;
  document.dispatchEvent(new Event("visibilitychange"));
}

const count = (route: Route) => calls.filter((c) => c.route === route).length;
const riskState = () =>
  document.querySelector("[data-risk-state]")?.getAttribute("data-risk-state");
const header = () => document.querySelector(".ruvor-asset-head") as HTMLElement;

/** Deixa as promessas e os efeitos correrem, e avança o relógio falso `ms`. */
async function advance(ms: number): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

function renderAsset() {
  const router = createMemoryRouter(routes, { initialEntries: ["/ativos/AALR3"] });
  return render(<RouterProvider router={router} />);
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  visibility = "visible";
  vi.spyOn(document, "visibilityState", "get").mockImplementation(() => visibility);
  assetBody = NO_PRICE;
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------- V-12

describe("V-12 — o /risk de novo a cada 5 s, enquanto há o que acompanhar", () => {
  it.each([
    ["in_progress presente e pedido nulo (E4)", E4_NO_REQUEST, "E4"],
    ["pedido aberto e in_progress nulo (E5)", E5_QUEUED, "E5"],
    ["E3 com in_progress (o recálculo)", E3_RECALC, "E3"],
  ])("%s", async (_caso, body, state) => {
    riskQueue = [body];
    renderAsset();
    await advance(0);
    expect(riskState()).toBe(state);
    expect(count("risk")).toBe(1);

    await advance(4999);
    expect(count("risk")).toBe(1);
    await advance(1);
    expect(count("risk")).toBe(2);
    await advance(5000);
    expect(count("risk")).toBe(3);
    // só o /risk: as outras rotas não se repetem enquanto acompanha
    expect(count("asset")).toBe(1);
  });

  it("sem nada a acompanhar (E1), não pede de novo", async () => {
    riskQueue = [E1];
    renderAsset();
    await advance(0);
    expect(riskState()).toBe("E1");
    await advance(30000);
    expect(count("risk")).toBe(1);
  });
});

describe("V-12 — ao terminar, recarrega as cinco rotas", () => {
  it.each([
    ["E1", E1],
    ["E7", E7],
  ])(
    "chegando em %s: as cinco de novo, e o cabeçalho sai de 'sem preço'",
    async (state, end) => {
      riskQueue = [E4_NO_REQUEST, end];
      renderAsset();
      await advance(0);
      expect(riskState()).toBe("E4");
      expect(within(header()).getByText(TEXTOS["ativo.semPreco"])).toBeDefined();

      assetBody = WITH_PRICE; // a cadeia sob demanda coletou os preços
      await advance(5000);
      expect(riskState()).toBe(state);
      for (const route of ["asset", "prices", "events", "metrics"] as const) {
        expect(count(route)).toBe(2);
      }
      expect(count("risk")).toBe(3); // o do início, o do acompanhamento e o do reloadAll
      expect(header().querySelector("[data-value='last-close']")?.textContent).toBe(
        formatCurrency(12.34),
      );
      expect(within(header()).queryByText(TEXTOS["ativo.semPreco"])).toBeNull();

      // terminou: não pede mais
      await advance(30000);
      expect(count("risk")).toBe(3);
      expect(count("asset")).toBe(2);
    },
  );

  it("o data-risk-state fica no último /risk recebido enquanto o reloadAll recarrega", async () => {
    riskQueue = [E4_NO_REQUEST, E1, null];
    renderAsset();
    await advance(0);
    await advance(5000);
    expect(riskState()).toBe("E1");
    // o /risk do reloadAll está pendente; a seção não volta ao carregando
    const pending = calls.filter((c) => c.route === "risk").at(-1) as Call;
    expect(count("risk")).toBe(3);
    await advance(1000);
    expect(riskState()).toBe("E1");
    expect(document.querySelector("[data-risk-state] table")).not.toBeNull();

    await act(async () => pending.resolve(E1));
    expect(riskState()).toBe("E1");
  });
});

describe("V-12 — para ao sair, e respeita a aba oculta", () => {
  it("desmontar a tela cancela", async () => {
    riskQueue = [E4_NO_REQUEST];
    const { unmount } = renderAsset();
    await advance(0);
    await advance(2000);
    unmount();
    await advance(30000);
    expect(count("risk")).toBe(1);
  });

  it("com a aba oculta não pede; ao voltar, pede na hora", async () => {
    visibility = "hidden";
    riskQueue = [E4_NO_REQUEST];
    renderAsset();
    await advance(0);
    await advance(30000);
    expect(count("risk")).toBe(1);

    await act(async () => setVisibility("visible"));
    await advance(0);
    expect(count("risk")).toBe(2);
    await advance(5000);
    expect(count("risk")).toBe(3);
  });

  it("ocultar com um pedido agendado o cancela", async () => {
    riskQueue = [E5_QUEUED];
    renderAsset();
    await advance(0);
    await advance(2000);
    await act(async () => setVisibility("hidden"));
    await advance(30000);
    expect(count("risk")).toBe(1);
  });
});
