/**
 * V-12 — o acompanhamento (RF-20), com relógio falso: o `/risk` é pedido de novo a cada 5 s
 * enquanto houver `in_progress` ou pedido aberto — inclusive no E3 com `in_progress`, e com
 * `in_progress` presente e pedido nulo; ao terminar, em E1 **e** em E7, a tela recarrega as
 * rotas (o cabeçalho passa de "sem preço" ao último fechamento); para ao sair da tela; a
 * aba oculta não pede, e voltar a ficar visível pede na hora. E o `data-risk-state` estável
 * durante o `reloadAll()`.
 *
 * V-10 do M1.6c (RF-15): o fim do acompanhamento recarrega também as duas seções novas — os
 * fundamentos, e os comunicados de volta à primeira página, com o filtro.
 *
 * M2.4 (T10, RF-18): o `/lab` entra na carga e no `reloadAll()`; no fim do acompanhamento ele é
 * relido, e, com `pending`, de novo a cada `POLL_INTERVAL_MS` até chegar o `latest` — e nunca na
 * montagem. O duplo conta os pedidos que não reconhece, e todo teste exige zero.
 *
 * M5.1 (T10): o `/returns` entra na carga e no `reloadAll()`, como as outras rotas.
 *
 * M2.3 (T10): a tabela dos nove nasce recolhida na iniciante; o teste que confere a tabela à
 * vista durante o `reloadAll()` declara a leitura avançada, em que ela nasce aberta.
 */
import { act, cleanup, fireEvent, render, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { routes } from "../src/App";
import {
  type AssetDetail,
  type ComputeRequest,
  type DisclosureItem,
  type Disclosures,
  type Fundamentals,
  type Indicator,
  type InProgress,
  type Lab,
  type LabRun,
  MODEL_ORDER,
  type Risk,
  type RiskResult,
  type RiskRun,
} from "../src/api/types";
import { TEXTOS } from "../src/content/textos";
import { formatCurrency } from "../src/format/numbers";
import { POLL_INTERVAL_MS } from "../src/risk/usePolling";
import { comNivel, limparNivel } from "./nivel";

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

/** O `/lab` (M2.4): antes do risco, devido (pending) e já gravado. */
function lab(over: Partial<Lab> = {}): Lab {
  return {
    ticker: "AALR3",
    active: true,
    decade: {
      first_price_date: "2016-09-22",
      end_date: "2026-09-22",
      last_price_date: "2026-10-02",
      complete: true,
      sessions: 2491,
    },
    risk_engine_version: "0.4.0",
    pending: false,
    latest: null,
    last_failure: null,
    ...over,
  };
}
const LAB_RUN: LabRun = {
  id: 1,
  calculated_at: "2026-10-04T04:41:41-03:00",
  finished_at: "2026-10-04T04:41:45-03:00",
  status: "ok",
  origin: "risk_close",
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
    id: 6,
    source: "yahoo-chart",
    started_at: "2026-09-25T19:30:00-03:00",
    finished_at: null,
  },
  price_fingerprint: "ac1d93ec7b42b24cc4cb777ff58df44d16543ba1530ddb11e969c2ef723d52ef",
  results: [],
};
const LAB_NO_RISK = lab({ risk_engine_version: null });
const LAB_PENDING = lab({ pending: true });
const LAB_READY = lab({ latest: LAB_RUN });

/** Um indicador calculado, só com o que a seção precisa para sair do vazio. */
const INDICATOR: Indicator = {
  calculated_at: "2026-09-29T20:00:00-03:00",
  statement: { reference_date: "2026-06-30", source: "itr", scope: "consolidated" },
  account_plan: "general",
  scope: "consolidated",
  revenue_ttm: null,
  ebit_ttm: null,
  net_income_ttm: null,
  equity_parent: null,
  total_assets: null,
  gross_debt: null,
  cash: null,
  net_debt: null,
  net_margin: null,
  ebit_margin: null,
  roe: null,
  net_debt_to_equity: null,
  price_date: null,
  close: null,
  shares_total: null,
  eps: null,
  bvps: null,
  pe: null,
  pb: null,
  per_share_missing: null,
  market_cap: null,
  market_cap_missing: null,
};

/** A página de `/disclosures` que o pedido quer: 25 documentos, dez por página, por categoria. */
function disclosuresPage(url: URL): Disclosures {
  const offset = Number(url.searchParams.get("offset"));
  const category = url.searchParams.get("category") ?? "comunicado";
  const results: DisclosureItem[] = [];
  for (let n = offset; n < Math.min(offset + 10, 25); n += 1) {
    results.push({
      delivered_on: "2026-09-25",
      reference_date: "2026-09-25",
      category: category as DisclosureItem["category"],
      kind: "Outros",
      species: "",
      title: `Documento ${category} ${n}`,
      link: `https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?c=${category}&n=${n}`,
    });
  }
  return {
    ticker: "AALR3",
    company: { code_cvm: "25011", name: "ALLIANÇA SAÚDE E PARTICIPAÇÕES S.A." },
    count: 25,
    limit: 10,
    offset,
    results,
  };
}

// ---------------------------------------------------------------- o duplo do fetch

type Route =
  | "asset"
  | "prices"
  | "events"
  | "metrics"
  | "risk"
  | "fundamentals"
  | "lab"
  | "returns"
  | "disclosures";
type Call = { route: Route; url: URL; resolve: (body: unknown) => void };

let calls: Call[] = [];
/** As respostas do `/risk`, em ordem; `null` deixa o pedido pendente. A última se repete. */
let riskQueue: (Risk | null)[] = [];
let assetBody: AssetDetail = NO_PRICE;
let fundamentalsBody: Fundamentals = { ticker: "AALR3", indicator: null, peers: null };
/** As respostas do `/lab`, em ordem; a última se repete (M2.4). */
let labQueue: Lab[] = [];
/** Os pedidos que o duplo não reconhece: `routeOf` lança dentro da promessa, que rejeita em silêncio. */
let unexpected: string[] = [];

/** A rota do pedido; só `/disclosures` leva parâmetros (a seção Comunicados pede a página). */
function routeOf(url: string): Route {
  const match =
    /^\/api\/v1\/assets\/[^/?]+(?:\/(prices|events|metrics|risk|fundamentals|lab|returns)|\/(disclosures)\?[^/]*)?$/.exec(
      url,
    );
  if (match === null) {
    unexpected.push(url);
    throw new Error(`pedido inesperado: ${url}`);
  }
  return (match[1] ?? match[2] ?? "asset") as Route;
}

function bodyOf(route: Route, url: URL): unknown | null {
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
    case "fundamentals":
      return fundamentalsBody;
    case "lab":
      return labQueue.length > 1 ? labQueue.shift() : labQueue[0];
    case "returns":
      return { ticker: "AALR3", latest: null };
    case "disclosures":
      return disclosuresPage(url);
  }
}

/**
 * O `auth/me` da rota de layout da sessão (M2.1b, RF-03): responde 401 (anônimo) na hora e
 * fica fora de `calls`.
 */
const ME_URL = "/api/v1/auth/me";

function stubFetch(): void {
  calls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url: string) =>
        new Promise<Response>((resolve) => {
          if (url === ME_URL) {
            resolve({
              ok: false,
              status: 401,
              json: async () => ({
                error: { code: "not_authenticated", message: "falhou", details: {} },
              }),
            } as unknown as Response);
            return;
          }
          const route = routeOf(url);
          const parsed = new URL(url, "http://localhost");
          // Como o `response.json()` de verdade, cada resposta é um objeto novo.
          const call: Call = {
            route,
            url: parsed,
            resolve: (body) =>
              resolve({
                ok: true,
                status: 200,
                json: async () => structuredClone(body),
              } as Response),
          };
          calls.push(call);
          const body = bodyOf(route, parsed);
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
const disclosures = () =>
  document.querySelector('[data-section="disclosures"]') as HTMLElement;

/** Deixa as promessas e os efeitos correrem, e avança o relógio falso `ms`. */
async function advance(ms: number): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

function renderAsset(path = "/ativos/AALR3/risco") {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  return render(<RouterProvider router={router} />);
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  visibility = "visible";
  vi.spyOn(document, "visibilityState", "get").mockImplementation(() => visibility);
  assetBody = NO_PRICE;
  fundamentalsBody = { ticker: "AALR3", indicator: null, peers: null };
  labQueue = [LAB_NO_RISK];
  unexpected = [];
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  limparNivel();
  expect(unexpected).toEqual([]);
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

describe("V-12 — ao terminar, recarrega as rotas", () => {
  it.each([
    ["E1", E1],
    ["E7", E7],
  ])(
    "chegando em %s: as rotas de novo, e o cabeçalho sai de 'sem preço'",
    async (state, end) => {
      riskQueue = [E4_NO_REQUEST, end];
      renderAsset();
      await advance(0);
      expect(riskState()).toBe("E4");
      expect(within(header()).getByText(TEXTOS["ativo.semPreco"])).toBeDefined();

      assetBody = WITH_PRICE; // a cadeia sob demanda coletou os preços
      await advance(5000);
      expect(riskState()).toBe(state);
      for (const route of [
        "asset",
        "prices",
        "events",
        "metrics",
        "fundamentals",
        "returns",
      ] as const) {
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
    // A tabela à vista no E1: na leitura avançada, ela nasce aberta (M2.3).
    comNivel("advanced");
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

describe("V-10 do M1.6c — o acompanhamento recarrega as duas seções", () => {
  it.each([
    ["E1", E1],
    ["E7", E7],
  ])(
    "chegando em %s na aba dos comunicados: os fundamentos de novo, e os comunicados na primeira página com o filtro",
    async (_state, end) => {
      // O acompanhamento corre em qualquer aba: aqui, a dos comunicados, sem a seção do risco.
      riskQueue = [E4_NO_REQUEST, end];
      renderAsset("/ativos/AALR3/comunicados");
      await advance(0);
      expect(count("risk")).toBe(1);
      expect(disclosures().getAttribute("data-state")).toBe("ready");

      // o filtro em "Fatos relevantes", e a segunda página somada
      const factButton = () =>
        within(
          within(disclosures()).getByRole("group", {
            name: TEXTOS["comunicados.filtro.rotulo"],
          }),
        ).getByRole("button", { name: TEXTOS["comunicados.filtro.fato_relevante"] });
      await act(async () => fireEvent.click(factButton()));
      await advance(0);
      await act(async () =>
        fireEvent.click(
          within(disclosures()).getByRole("button", {
            name: TEXTOS["comunicados.mostrarMais"],
          }),
        ),
      );
      await advance(0);
      const links = () => disclosures().querySelectorAll("[data-disclosure-link]");
      expect(links()).toHaveLength(20);
      const before = count("disclosures");

      // a rotina semanal calculou os fundamentos no meio do acompanhamento
      fundamentalsBody = { ticker: "AALR3", indicator: INDICATOR, peers: null };
      await advance(5000);
      expect(count("risk")).toBe(3); // o do início, o do acompanhamento e o do reloadAll

      expect(count("fundamentals")).toBe(2);

      expect(count("disclosures")).toBe(before + 1);
      const last = calls.filter((c) => c.route === "disclosures").at(-1) as Call;
      expect(last.url.searchParams.get("offset")).toBe("0");
      expect(last.url.searchParams.get("category")).toBe("fato_relevante");
      expect(factButton().getAttribute("aria-pressed")).toBe("true");
      expect(links()).toHaveLength(10);
      expect(disclosures().getAttribute("data-state")).toBe("ready");

      // terminou: não recarrega mais
      await advance(30000);
      expect(count("fundamentals")).toBe(2);
      expect(count("disclosures")).toBe(before + 1);
    },
  );
});

describe("RF-18 do M2.4 — o /lab relido no fim do acompanhamento, por até 2 minutos", () => {
  it("na montagem, com pending, não relê", async () => {
    riskQueue = [E1];
    labQueue = [LAB_PENDING];
    renderAsset();
    await advance(0);
    expect(count("lab")).toBe(1);
    await advance(60_000);
    expect(count("lab")).toBe(1);
  });

  it("no fim do acompanhamento: o /lab de novo e, com pending, a cada POLL_INTERVAL_MS até o latest", async () => {
    riskQueue = [E4_NO_REQUEST, E1];
    // o da carga (antes do risco), o do reloadAll e o da primeira releitura devidos, e então o experimento
    labQueue = [LAB_NO_RISK, LAB_PENDING, LAB_PENDING, LAB_READY];
    renderAsset();
    await advance(0);
    expect(riskState()).toBe("E4");
    expect(count("lab")).toBe(1);

    await advance(POLL_INTERVAL_MS); // o /risk chega em E1: o reloadAll
    expect(riskState()).toBe("E1");
    expect(count("lab")).toBe(2);

    await advance(POLL_INTERVAL_MS - 1);
    expect(count("lab")).toBe(2);
    await advance(1);
    expect(count("lab")).toBe(3);
    await advance(POLL_INTERVAL_MS);
    expect(count("lab")).toBe(4); // este traz o latest

    // chegou: não relê mais
    await advance(120_000);
    expect(count("lab")).toBe(4);
    expect(count("risk")).toBe(3);
  });

  it("sem pending depois do reloadAll, relê uma vez só (a do reloadAll)", async () => {
    riskQueue = [E4_NO_REQUEST, E1];
    labQueue = [LAB_NO_RISK, LAB_READY];
    renderAsset();
    await advance(0);
    await advance(POLL_INTERVAL_MS);
    expect(count("lab")).toBe(2);
    await advance(120_000);
    expect(count("lab")).toBe(2);
  });

  it("com pending para sempre, para em 2 minutos", async () => {
    riskQueue = [E4_NO_REQUEST, E1];
    labQueue = [LAB_NO_RISK, LAB_PENDING];
    renderAsset();
    await advance(0);
    await advance(POLL_INTERVAL_MS);
    const opened = count("lab");
    // de 5 em 5 s: cada resposta agenda o próximo quando o `act` do passo termina
    for (let t = 0; t < 120_000; t += POLL_INTERVAL_MS) await advance(POLL_INTERVAL_MS);
    const atEnd = count("lab");
    expect(atEnd - opened).toBeGreaterThanOrEqual(120_000 / POLL_INTERVAL_MS - 1);
    expect(atEnd - opened).toBeLessThanOrEqual(120_000 / POLL_INTERVAL_MS);
    for (let t = 0; t < 60_000; t += POLL_INTERVAL_MS) await advance(POLL_INTERVAL_MS);
    expect(count("lab")).toBe(atEnd);
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
