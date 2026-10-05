/**
 * A tela do ativo (T10): o cabeçalho, o preço, os proventos e o comportamento.
 *
 * - V-04 na parte de tela (RF-06): as rotas pedidas juntas — sete desde o M1.6c, com
 *   `/fundamentals` e `/disclosures` (V-10 do M1.6c) —; `404 asset_not_found` na identidade vira
 *   "ativo não encontrado"; qualquer outro erro fica na seção da rota, com "tentar de novo", e o
 *   resto da tela renderiza;
 * - V-06 (RF-10): cada campo formatado em pt-BR; o nulo mostra "—" e o porquê, **nunca** zero;
 *   o índice com beta nulo diz que é a referência; `metric: null`;
 * - V-14 das seções desta tarefa (RF-21): a frase de cada número está junto dele;
 * - `data-ready` e o `reloadAll()` que a T11 usa; as duas seções do M1.6c depois do risco, fora
 *   do `data-ready`;
 * - M2.4 (T10, RF-18): o `/lab` na carga e no `reloadAll()`, fora do `data-ready` — a tela fica
 *   pronta com o `/lab` ainda carregando ou em erro;
 * - M5.1 (T10): o `/returns` na carga e no `reloadAll()`, também fora do `data-ready`;
 * - V-09 do M1.7 (RF-10): a busca da barra não pede a sugestão — **todo teste** confere, no
 *   `afterEach`, que a rota `suggestion` recebeu `suggestionsExpected` pedidos (0, menos na tela
 *   "ativo não encontrado", que monta a caixa de página e pede exatamente 1).
 *
 * - M2.3 (T4): o cabeçalho e o preço nos dois níveis — a prova por seção no avançado (V-04), o
 *   valor igual nos dois, e a troca pelo alternador sem pedido à API com o risco em E1 (V-08).
 * - M2.3 (T7): o comportamento nos dois níveis — a prova por seção das 22 chaves no avançado
 *   (V-04), os números iguais nos dois níveis, e a assimetria e a curtose recolhidas na iniciante,
 *   com o histograma aberto (V-05). Os testes do M1.6b que leem a assimetria e a curtose abrem o
 *   controle (`openMoments`): na iniciante, elas nascem recolhidas.
 *
 * O `fetch` é um duplo que responde pela rota; o uPlot, um duplo mínimo (o jsdom não tem
 * `<canvas>` nem `matchMedia`) — o que ele recebe é dos testes dos gráficos.
 */
import {
  act,
  cleanup,
  fireEvent,
  render,
  renderHook,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { routes } from "../src/App";
import {
  type AssetDetail,
  type AssetItem,
  type AssetPage,
  type Disclosures,
  type EventRow,
  type Events,
  type Fundamentals,
  type HistogramBin,
  type Lab,
  type Metric,
  type Metrics,
  MODEL_ORDER,
  type PriceRow,
  type Prices,
  type Returns,
  type Risk,
  type RiskResult,
  type RiskRun,
} from "../src/api/types";
import { TEXTOS_AVANCADOS } from "../src/content/avancado";
import { TEXTOS } from "../src/content/textos";
import { formatCurrency, formatCurrencyPrecise } from "../src/format/numbers";
import { useAssetData } from "../src/screens/AssetScreen";
import { comNivel, limparNivel } from "./nivel";

// ---------------------------------------------------------------- o duplo do uPlot

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

const ASSET: AssetDetail = {
  ticker: "ITUB4",
  name: "ITAU UNIBANCO HOLDING S.A.",
  trading_name: "ITAUUNIBANCO",
  kind: "stock",
  sector: "Financeiro",
  status: "active",
  has_prices: true,
  subsector: "Intermediários Financeiros",
  segment: "Bancos",
  listing_segment: "N1",
  last_price: { date: "2026-09-28", close: "38.500000", adj_close: "38.500000" },
};

function priceRows(n: number): PriceRow[] {
  const start = Date.UTC(2016, 0, 4);
  return Array.from({ length: n }, (_, i) => {
    const date = new Date(start + i * 86400000).toISOString().slice(0, 10);
    const close = (20 + i / 10).toFixed(4);
    return {
      date,
      open: close,
      high: close,
      low: close,
      close,
      adj_close: close,
      volume: 1,
    };
  });
}

const PRICES: Prices = {
  ticker: "ITUB4",
  from: null,
  to: null,
  results: priceRows(40),
};

const EVENTS: Events = {
  ticker: "ITUB4",
  results: [
    // fora da janela de 12 meses até 28/09/2026 (a janela exclui o início)
    {
      date: "2025-09-28",
      kind: "dividend",
      amount: "0.500000",
      numerator: null,
      denominator: null,
    },
    {
      date: "2024-03-18",
      kind: "split",
      amount: null,
      numerator: "11.0000",
      denominator: "10.0000",
    },
    // dentro dela, fora de ordem
    {
      date: "2026-08-01",
      kind: "dividend",
      amount: "0.021700",
      numerator: null,
      denominator: null,
    },
    {
      date: "2026-09-01",
      kind: "dividend",
      amount: "0.021700",
      numerator: null,
      denominator: null,
    },
    {
      date: "2026-03-20",
      kind: "split",
      amount: null,
      numerator: "12.0000",
      denominator: "10.0000",
    },
  ] satisfies EventRow[],
};

function bins(counts: (i: number) => number): HistogramBin[] {
  return Array.from({ length: 42 }, (_, i) => ({
    bin_index: i,
    lower_bound: i === 0 ? null : (-0.1 + (i - 1) * 0.005).toFixed(10),
    upper_bound: i === 41 ? null : (-0.1 + i * 0.005).toFixed(10),
    count: counts(i),
  }));
}

const METRIC: Metric = {
  calculated_at: "2026-09-28T19:30:02-03:00",
  as_of_date: "2026-09-28",
  first_price_date: "2016-09-22",
  price_count: 2487,
  return_1m: "0.0200000000",
  return_3m: "-0.0500000000",
  return_6m: "0.1000000000",
  return_12m: "0.2581292498",
  return_36m: "0.5000000000",
  return_60m: "0.6616825124",
  return_120m: "2.0829423310",
  return_ytd: "0.1357090768",
  volatility_12m: "0.1753240687",
  volatility_60m: "0.2500000000",
  max_drawdown: "-0.4681580885",
  max_drawdown_peak_date: "2020-01-23",
  max_drawdown_trough_date: "2020-03-23",
  max_drawdown_recovery_date: "2021-01-06",
  max_drawdown_recovery_sessions: 195,
  beta_60m: "0.8512000000",
  correlation_60m: "-0.1234000000",
  benchmark_observations: 1230,
  skewness: "-0.0470730429",
  excess_kurtosis: "1.0654291607",
  statistical_observations: 1247,
  dividends_12m: "3.456700",
  dividend_payments_12m: 14,
  dividend_yield_12m: "0.0812345678",
  avg_volume_21d: "25432100.00",
  avg_volume_252d: "21000000.00",
  histogram: bins((i) => (i === 20 ? 300 : i % 5)),
  // Os momentos de estresse (M3.3) são de `estresse.test.tsx`; aqui, a linha sem episódios.
  stress: [],
};

/** A série curta: as janelas longas nulas, a queda sem volta, a distribuição sem dado. */
const METRIC_SHORT: Metric = {
  ...METRIC,
  first_price_date: "2025-01-02",
  price_count: 430,
  return_36m: null,
  return_60m: null,
  return_120m: null,
  volatility_60m: null,
  max_drawdown_recovery_date: null,
  max_drawdown_recovery_sessions: null,
  beta_60m: null,
  correlation_60m: null,
  benchmark_observations: null,
  skewness: null,
  excess_kurtosis: null,
  statistical_observations: null,
  avg_volume_252d: null,
  histogram: bins(() => 0),
};

const RISK: Risk = {
  ticker: "ITUB4",
  covered: false,
  latest: null,
  in_progress: null,
  request: null,
};

/** Sem indicador calculado: a seção Fundamentos fica no vazio, sem alerta. */
const FUNDAMENTALS: Fundamentals = { ticker: "ITUB4", indicator: null, peers: null };
/** O `/lab` (M2.4): a década completa, sem experimento ainda. A seção chega na T12. */
const LAB: Lab = {
  ticker: "ITUB4",
  active: true,
  decade: {
    first_price_date: "2016-09-22",
    end_date: "2026-09-22",
    last_price_date: "2026-10-02",
    complete: true,
    sessions: 2491,
  },
  risk_engine_version: "0.4.0",
  pending: true,
  latest: null,
  last_failure: null,
};

/** O `/returns` (M5.1): sem validação ainda. A seção chega na T12. */
const RETURNS: Returns = { ticker: "ITUB4", latest: null };

const DISCLOSURES: Disclosures = {
  ticker: "ITUB4",
  company: { code_cvm: "19348", name: "ITAU UNIBANCO HOLDING S.A." },
  count: 1,
  limit: 10,
  offset: 0,
  results: [
    {
      delivered_on: "2026-09-25",
      reference_date: "2026-09-25",
      category: "fato_relevante",
      kind: "Fato Relevante",
      species: "",
      title: "Título do fato relevante",
      link: "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo=1",
    },
  ],
};

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
  | "disclosures"
  | "suggestion"
  | "me";
type Reply = { status: number; body: unknown };

const ok = (body: unknown): Reply => ({ status: 200, body });
const fail = (status: number, code = "internal_error"): Reply => ({
  status,
  body: { error: { code, message: "falhou", details: {} } },
});

type Call = { url: string; route: Route; resolve: (reply: Reply) => void };

let calls: Call[] = [];
/** A resposta de cada rota; `undefined` deixa o pedido pendente até o teste responder. */
let replies: Partial<Record<Route, Reply>> = {};

/** O pedido da sugestão (M1.7, RF-10), literal: só ele casa com a rota `suggestion`. */
const SUGGESTION_URL = "/api/v1/assets?has_risk=true&limit=8";

/**
 * O `auth/me` da rota de layout da sessão (M2.1b, RF-03), a rota `me`: responde na hora —
 * `replies.me` ou, sem ela, 401 (anônimo) — e fica fora de `calls`.
 */
const ME_URL = "/api/v1/auth/me";
const ANON: Reply = fail(401, "not_authenticated");

/**
 * A rota do pedido; só `/disclosures` leva parâmetros (a seção Comunicados pede a página). A
 * sugestão é a rota própria `suggestion`, casada só pelo endereço exato; qualquer outro pedido
 * continua lançando.
 */
function routeOf(url: string): Route {
  if (url === SUGGESTION_URL) return "suggestion";
  if (url === ME_URL) return "me";
  const match =
    /^\/api\/v1\/assets\/[^/?]+(?:\/(prices|events|metrics|risk|fundamentals|lab|returns)|\/(disclosures)\?[^/]*)?$/.exec(
      url,
    );
  if (match === null) throw new Error(`pedido inesperado: ${url}`);
  return (match[1] ?? match[2] ?? "asset") as Route;
}

function fakeResponse({ status, body }: Reply): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as unknown as Response;
}

function stubFetch(): void {
  calls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url: string) =>
        new Promise<Response>((resolve) => {
          const route = routeOf(url);
          if (route === "me") {
            resolve(fakeResponse(replies.me ?? ANON));
            return;
          }
          const call: Call = { url, route, resolve: (r) => resolve(fakeResponse(r)) };
          calls.push(call);
          const reply = replies[route];
          if (reply !== undefined) call.resolve(reply);
        }),
    ),
  );
}

/** Quantos pedidos a rota recebeu neste teste, por qualquer duplo do `fetch` em vigor. */
function count(route: Route): number {
  return vi
    .mocked(globalThis.fetch)
    .mock.calls.filter(([url]) => routeOf(String(url)) === route).length;
}

/** Quantos pedidos de sugestão o teste espera: 0 na tela do ativo (a barra não pede). */
let suggestionsExpected = 0;

const SUGGESTED: AssetItem = {
  ticker: "PETR4",
  name: "PETROLEO BRASILEIRO S.A. PETROBRAS",
  trading_name: "PETROBRAS",
  kind: "stock",
  sector: "Petróleo, Gás e Biocombustíveis",
  status: "active",
  has_prices: true,
  has_risk: true,
};
const SUGGESTION: AssetPage = {
  count: 2,
  limit: 8,
  offset: 0,
  results: [
    {
      ...SUGGESTED,
      ticker: "ITUB4",
      name: "ITAU UNIBANCO HOLDING S.A.",
      trading_name: "ITAUUNIBANCO",
      sector: "Financeiro",
    },
    SUGGESTED,
  ],
};

function allOk(over: Partial<Record<Route, Reply>> = {}): void {
  replies = {
    asset: ok(ASSET),
    prices: ok(PRICES),
    events: ok(EVENTS),
    metrics: ok({ ticker: "ITUB4", metric: METRIC } satisfies Metrics),
    risk: ok(RISK),
    fundamentals: ok(FUNDAMENTALS),
    lab: ok(LAB),
    returns: ok(RETURNS),
    disclosures: ok(DISCLOSURES),
    suggestion: ok(SUGGESTION),
    me: ANON,
    ...over,
  };
}

function renderAsset(ticker = "ITUB4", tab = "") {
  const path = tab === "" ? `/ativos/${ticker}` : `/ativos/${ticker}/${tab}`;
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(<RouterProvider router={router} />);
  return router;
}

beforeEach(() => {
  suggestionsExpected = 0;
  allOk();
  stubFetch();
});

afterEach(() => {
  // RF-10: a barra não pede a sugestão; só a caixa de página do "ativo não encontrado" pede.
  // Conta antes de desfazer o duplo, e confere depois de limpar: a falha não deixa a tela
  // montada para o teste seguinte.
  const suggestions = count("suggestion");
  cleanup();
  vi.unstubAllGlobals();
  limparNivel();
  expect(suggestions).toBe(suggestionsExpected);
});

// ---------------------------------------------------------------- as partes da tela

const main = () => screen.getByRole("main");
const header = () =>
  main().querySelector<HTMLElement>(".ruvor-asset-head") as HTMLElement;
const panel = (title: string) =>
  screen.getByRole("heading", { name: title }).closest("section") as HTMLElement;
const pricePanel = () => panel(TEXTOS["ativo.preco.titulo"]);
const eventsPanel = () => panel(TEXTOS["ativo.eventos.titulo"]);
const behavior = () => panel(TEXTOS["comportamento.titulo"]);
const fundamentalsSection = () =>
  main().querySelector<HTMLElement>('[data-section="fundamentals"]') as HTMLElement;
const disclosuresSection = () =>
  main().querySelector<HTMLElement>('[data-section="disclosures"]') as HTMLElement;
const block = (title: string) =>
  within(behavior())
    .getByRole("heading", { name: title })
    .closest("section") as HTMLElement;
const stat = (field: string) =>
  behavior().querySelector<HTMLElement>(`[data-field="${field}"]`) as HTMLElement;
const statValue = (field: string) =>
  stat(field).querySelector(".ruvor-stat__value")?.textContent;
const statPhrase = (field: string) =>
  stat(field).querySelector(".ruvor-note")?.textContent;

/** O `data-ready`: o cabeçalho e o risco terminados, em qualquer aba. */
async function ready(): Promise<void> {
  await waitFor(() =>
    expect(main().querySelector("[data-ready]")?.getAttribute("data-ready")).toBe(
      "true",
    ),
  );
}

/** A visão geral pronta: o `data-ready` e o comportamento fora do carregando. */
async function loaded(): Promise<void> {
  await ready();
  await waitFor(() => expect(behavior().querySelector("[aria-busy]")).toBeNull());
}

/** O controle da assimetria e da curtose (M2.3), na seção Comportamento. */
const momentsToggle = () =>
  within(behavior()).getByRole("button", {
    name: TEXTOS["comportamento.momentos.abrir"],
  });

/** Abre a assimetria e a curtose, se estiverem recolhidas — na iniciante, nascem recolhidas. */
function openMoments(): void {
  if (momentsToggle().getAttribute("aria-expanded") === "false") {
    fireEvent.click(momentsToggle());
  }
}

// ---------------------------------------------------------------- RF-06

describe("RF-06 e RF-15 do M1.6c — as nove rotas, cada seção sozinha", () => {
  it("pede as oito juntas, antes de qualquer resposta — com o /lab do M2.4 e o /returns do M5.1; os comunicados, só na aba deles", () => {
    replies = {};
    renderAsset();
    expect(count("suggestion")).toBe(0);
    expect(calls.map((c) => c.url).sort()).toEqual(
      [
        "/api/v1/assets/ITUB4",
        "/api/v1/assets/ITUB4/events",
        "/api/v1/assets/ITUB4/metrics",
        "/api/v1/assets/ITUB4/prices",
        "/api/v1/assets/ITUB4/risk",
        "/api/v1/assets/ITUB4/fundamentals",
        "/api/v1/assets/ITUB4/lab",
        "/api/v1/assets/ITUB4/returns",
      ].sort(),
    );
  });

  it("na aba dos comunicados, as oito e o /disclosures", () => {
    replies = {};
    renderAsset("ITUB4", "comunicados");
    expect(calls.map((c) => c.url)).toContain(
      "/api/v1/assets/ITUB4/disclosures?limit=10&offset=0",
    );
    expect(calls).toHaveLength(9);
  });

  it("as abas, na ordem: visão geral, risco, laboratório, retorno, fundamentos e comunicados", async () => {
    renderAsset();
    await loaded();
    const nav = screen.getByRole("navigation", { name: TEXTOS["ativo.abas.rotulo"] });
    expect(
      within(nav)
        .getAllByRole("link")
        .map((a) => a.textContent),
    ).toEqual([
      TEXTOS["ativo.aba.visaoGeral"],
      TEXTOS["ativo.aba.risco"],
      TEXTOS["ativo.aba.laboratorio"],
      TEXTOS["ativo.aba.retorno"],
      TEXTOS["ativo.aba.fundamentos"],
      TEXTOS["ativo.aba.comunicados"],
    ]);
    expect(
      within(nav)
        .getAllByRole("link")
        .map((a) => a.getAttribute("href")),
    ).toEqual([
      "/ativos/ITUB4",
      "/ativos/ITUB4/risco",
      "/ativos/ITUB4/laboratorio",
      "/ativos/ITUB4/retorno",
      "/ativos/ITUB4/fundamentos",
      "/ativos/ITUB4/comunicados",
    ]);
    const current = within(nav).getByRole("link", { current: "page" });
    expect(current.textContent).toBe(TEXTOS["ativo.aba.visaoGeral"]);
  });

  it("a visão geral: o preço, os proventos e o comportamento, sem as outras seções", async () => {
    renderAsset();
    await loaded();
    expect(within(pricePanel()).getByRole("img")).toBeDefined();
    expect(behavior()).not.toBeNull();
    expect(main().querySelector("[data-risk-state]")).toBeNull();
    expect(main().querySelector('[data-section="fundamentals"]')).toBeNull();
    expect(main().querySelector('[data-section="disclosures"]')).toBeNull();
  });

  it("trocar de aba mostra a seção dela e não pede as rotas de novo", async () => {
    renderAsset();
    await loaded();
    const before = calls.length;
    const nav = screen.getByRole("navigation", { name: TEXTOS["ativo.abas.rotulo"] });
    fireEvent.click(
      within(nav).getByRole("link", { name: TEXTOS["ativo.aba.fundamentos"] }),
    );
    await waitFor(() =>
      expect(fundamentalsSection().getAttribute("data-state")).toBe("empty"),
    );
    expect(main().querySelector("[data-risk-state]")).toBeNull();
    expect(calls.length).toBe(before);
  });

  it("a aba dos comunicados: a seção da companhia", async () => {
    renderAsset("ITUB4", "comunicados");
    await ready();
    await waitFor(() =>
      expect(disclosuresSection().getAttribute("data-state")).toBe("ready"),
    );
    expect(disclosuresSection().getAttribute("data-company")).toBe("19348");
  });

  it("as explicações: escondidas por padrão; o botão as mostra, e a escolha é lembrada", async () => {
    window.localStorage.removeItem("ruvor-explain");
    renderAsset();
    await loaded();
    const root = () => main().querySelector("[data-explain]") as HTMLElement;
    const button = () =>
      screen.getByRole("button", { name: TEXTOS["ativo.explicacoes"] });
    expect(root().getAttribute("data-explain")).toBe("off");
    expect(button().getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(button());
    expect(root().getAttribute("data-explain")).toBe("on");
    expect(button().getAttribute("aria-pressed")).toBe("true");
    expect(window.localStorage.getItem("ruvor-explain")).toBe("on");
    window.localStorage.removeItem("ruvor-explain");
  });

  it("a aba desconhecida vira a visão geral, sem entrada nova no histórico", async () => {
    const router = renderAsset("ITUB4", "xpto");
    await waitFor(() => expect(router.state.location.pathname).toBe("/ativos/ITUB4"));
    expect(router.state.historyAction).toBe("REPLACE");
  });

  it("a lenta não segura a rápida: o comportamento chega com a identidade pendente", async () => {
    allOk({ asset: undefined });
    stubFetch();
    renderAsset();
    await waitFor(() => expect(stat("return_12m")).not.toBeNull());
    expect(header().getAttribute("aria-busy")).toBe("true");
    expect(within(pricePanel()).getByRole("img")).toBeDefined();
  });

  it("404 asset_not_found na identidade: a tela inteira vira 'ativo não encontrado', com a busca", async () => {
    suggestionsExpected = 1;
    allOk({ asset: fail(404, "asset_not_found") });
    stubFetch();
    renderAsset("XPTO3");
    const title = await screen.findByRole("heading", {
      name: TEXTOS["ativo.naoEncontrado.titulo"],
    });
    const page = title.closest("section") as HTMLElement;
    expect(
      within(page).getByText(TEXTOS["ativo.naoEncontrado"]("XPTO3")),
    ).toBeDefined();
    expect(within(page).getByText(TEXTOS["ativo.naoEncontrado.dica"])).toBeDefined();
    expect(within(page).getByRole("combobox")).toBeDefined();
    expect(
      screen.queryByRole("heading", { name: TEXTOS["comportamento.titulo"] }),
    ).toBeNull();
    expect(page.getAttribute("data-ready")).toBe("true");

    // M1.7, RF-10: a caixa de página pede a sugestão exatamente uma vez e mostra a resposta.
    // O pedido sai no efeito de montagem, que pode correr depois de o título aparecer: espera
    // por ele; o `afterEach` confere de novo, com tudo assentado, que foi exatamente 1.
    const suggest = within(page).getByRole("region", {
      name: TEXTOS["busca.sugestaoTitulo"],
    });
    await waitFor(() =>
      expect(
        within(suggest)
          .getAllByRole("link")
          .map((link) => link.textContent),
      ).toEqual(["ITUB4", "PETR4"]),
    );
    expect(count("suggestion")).toBe(1);
  });

  it("identidade com 500: o erro no cabeçalho, com tentar de novo, e o comportamento renderiza", async () => {
    allOk({ asset: fail(500) });
    stubFetch();
    renderAsset();
    await loaded();

    const alert = within(header()).getByRole("alert");
    expect(alert.textContent).toContain(TEXTOS["ativo.erroSecao"]);
    // o resto da tela continua
    expect(
      screen.queryByRole("heading", { name: TEXTOS["ativo.naoEncontrado.titulo"] }),
    ).toBeNull();
    expect(statValue("return_12m")).toBe("+25,8%");
    expect(within(pricePanel()).getByRole("img")).toBeDefined();
    expect(within(eventsPanel()).getByRole("table")).toBeDefined();
    expect(screen.getAllByRole("alert")).toHaveLength(1);

    // tentar de novo pede só a identidade
    replies.asset = ok(ASSET);
    const before = calls.length;
    fireEvent.click(
      within(alert).getByRole("button", { name: TEXTOS["ativo.tentarDeNovo"] }),
    );
    await waitFor(() =>
      expect(within(header()).getByRole("heading", { level: 1 }).textContent).toBe(
        "ITUB4",
      ),
    );
    expect(calls.slice(before).map((c) => c.route)).toEqual(["asset"]);
  });

  it.each([
    ["prices", () => pricePanel()],
    ["events", () => eventsPanel()],
    ["metrics", () => behavior()],
  ] as const)(
    "%s com 500: o erro só na seção dela, e as outras renderizam",
    async (route, section) => {
      allOk({ [route]: fail(500) });
      stubFetch();
      renderAsset();
      await waitFor(() => expect(within(section()).getByRole("alert")).toBeDefined());
      await waitFor(() =>
        expect(main().querySelector("[data-ready]")?.getAttribute("data-ready")).toBe(
          "true",
        ),
      );
      expect(screen.getAllByRole("alert")).toHaveLength(1);
      expect(within(header()).getByRole("heading", { level: 1 }).textContent).toBe(
        "ITUB4",
      );
      if (route !== "prices")
        expect(within(pricePanel()).getByRole("img")).toBeDefined();
      if (route !== "events") {
        await waitFor(() =>
          expect(within(eventsPanel()).getByRole("table")).toBeDefined(),
        );
      }
      if (route !== "metrics") {
        await waitFor(() => expect(statValue("return_12m")).toBe("+25,8%"));
      }

      // tentar de novo pede só a rota da seção
      replies[route] = allOkReply(route);
      const before = calls.length;
      fireEvent.click(
        within(section()).getByRole("button", { name: TEXTOS["ativo.tentarDeNovo"] }),
      );
      await waitFor(() => expect(within(section()).queryByRole("alert")).toBeNull());
      expect(calls.slice(before).map((c) => c.route)).toEqual([route]);
    },
  );

  it.each([
    ["fundamentals", "fundamentos", () => fundamentalsSection()],
    ["disclosures", "comunicados", () => disclosuresSection()],
  ] as const)(
    "%s com 500, na aba dela: o erro só na seção, e tentar de novo pede só a rota dela",
    async (route, tab, section) => {
      allOk({ [route]: fail(500) });
      stubFetch();
      renderAsset("ITUB4", tab);
      await waitFor(() => expect(within(section()).getByRole("alert")).toBeDefined());
      await waitFor(() =>
        expect(main().querySelector("[data-ready]")?.getAttribute("data-ready")).toBe(
          "true",
        ),
      );
      expect(screen.getAllByRole("alert")).toHaveLength(1);
      expect(within(header()).getByRole("heading", { level: 1 }).textContent).toBe(
        "ITUB4",
      );

      replies[route] = allOkReply(route);
      const before = calls.length;
      fireEvent.click(
        within(section()).getByRole("button", { name: TEXTOS["ativo.tentarDeNovo"] }),
      );
      await waitFor(() => expect(within(section()).queryByRole("alert")).toBeNull());
      expect(calls.slice(before).map((c) => c.route)).toEqual([route]);
    },
  );

  it("erro de rede (network_error) também fica na seção", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (routeOf(url) === "prices") throw new TypeError("Failed to fetch");
        return fakeResponse(allOkReply(routeOf(url)));
      }),
    );
    renderAsset();
    await waitFor(() => expect(within(pricePanel()).getByRole("alert")).toBeDefined());
    await waitFor(() => expect(statValue("return_12m")).toBe("+25,8%"));
  });
});

function allOkReply(route: Route): Reply {
  const saved = replies;
  allOk();
  const reply = replies[route] as Reply;
  replies = saved;
  return reply;
}

// ---------------------------------------------------------------- data-ready e reloadAll

describe("data-ready e reloadAll()", () => {
  const readyAttr = () =>
    main().querySelector("[data-ready]")?.getAttribute("data-ready");

  it("só com o cabeçalho e o risco terminados", async () => {
    replies = {};
    renderAsset();
    expect(main().querySelector("[data-ready]")).toBeNull();
    const reply = (route: Route, r: Reply) =>
      act(async () => {
        for (const c of calls.filter((x) => x.route === route)) c.resolve(r);
      });

    await reply("asset", ok(ASSET));
    await reply("prices", ok(PRICES));
    await reply("metrics", ok({ ticker: "ITUB4", metric: METRIC }));
    await reply("events", ok(EVENTS));
    expect(main().querySelector("[data-ready]")).toBeNull();

    await reply("risk", ok(RISK));
    expect(readyAttr()).toBe("true");
    // o /lab (M2.4) e o /returns (M5.1) foram pedidos e seguem sem resposta: o data-ready não os espera
    expect(calls.filter((c) => c.route === "lab")).toHaveLength(1);
    expect(calls.filter((c) => c.route === "returns")).toHaveLength(1);
    // o /fundamentals segue sem resposta: o data-ready não o espera
    expect(calls.filter((c) => c.route === "fundamentals")).toHaveLength(1);
  });

  it("os comunicados terminados não bastam: o risco pendente segura", async () => {
    allOk({ risk: undefined });
    stubFetch();
    renderAsset("ITUB4", "comunicados");
    await waitFor(() =>
      expect(disclosuresSection().getAttribute("data-state")).toBe("ready"),
    );
    expect(main().querySelector("[data-ready]")).toBeNull();
  });

  it.each([
    ["pendente", undefined],
    ["em erro", fail(500)],
  ])("o /lab %s não segura o data-ready (M2.4, RF-13)", async (_caso, labReply) => {
    allOk({ lab: labReply });
    stubFetch();
    renderAsset();
    await waitFor(() => expect(readyAttr()).toBe("true"));
    expect(calls.filter((c) => c.route === "lab")).toHaveLength(1);
  });

  it.each([
    ["pendente", undefined],
    ["em erro", fail(500)],
  ])("o /returns %s não segura o data-ready (M5.1)", async (_caso, returnsReply) => {
    allOk({ returns: returnsReply });
    stubFetch();
    renderAsset();
    await waitFor(() => expect(readyAttr()).toBe("true"));
    expect(calls.filter((c) => c.route === "returns")).toHaveLength(1);
  });

  it("o risco em erro também termina", async () => {
    allOk({ risk: fail(500) });
    stubFetch();
    renderAsset();
    await waitFor(() => expect(readyAttr()).toBe("true"));
  });

  it("o cabeçalho pendente segura, mesmo com o risco pronto", async () => {
    allOk({ asset: undefined });
    stubFetch();
    renderAsset();
    await waitFor(() => expect(stat("return_12m")).not.toBeNull());
    expect(main().querySelector("[data-ready]")).toBeNull();
  });

  it("reloadAll pede as oito de novo — com o /lab do M2.4 e o /returns do M5.1 — sem apagar o que já chegou, incrementa o reloadToken, e troca quando o novo chega", async () => {
    const { result } = renderHook(() => useAssetData("ITUB4"));
    await waitFor(() => expect(result.current.risk.state).toBe("ok"));
    await waitFor(() => expect(result.current.asset.state).toBe("ok"));
    await waitFor(() => expect(result.current.fundamentals.state).toBe("ok"));
    await waitFor(() => expect(result.current.lab.state).toBe("ok"));
    await waitFor(() => expect(result.current.returns.state).toBe("ok"));
    // o hook não pede /disclosures: é a seção Comunicados que pede
    expect(calls.some((c) => c.route === "disclosures")).toBe(false);
    const token = result.current.reloadToken;

    replies = {};
    const before = calls.length;
    act(() => result.current.reloadAll());
    expect(
      calls
        .slice(before)
        .map((c) => c.route)
        .sort(),
    ).toEqual([
      "asset",
      "events",
      "fundamentals",
      "lab",
      "metrics",
      "prices",
      "returns",
      "risk",
    ]);
    expect(result.current.reloadToken).toBe(token + 1);
    // enquanto recarrega, o dado anterior fica
    for (const key of [
      "asset",
      "prices",
      "events",
      "metrics",
      "risk",
      "fundamentals",
      "lab",
      "returns",
    ] as const) {
      expect(result.current[key].state).toBe("ok");
    }

    const withPrice: AssetDetail = {
      ...ASSET,
      last_price: { date: "2026-09-29", close: "39.000000", adj_close: "39.000000" },
    };
    await act(async () => {
      for (const c of calls.slice(before))
        c.resolve(c.route === "asset" ? ok(withPrice) : allOkReply(c.route));
    });
    expect(result.current.asset).toEqual({ state: "ok", data: withPrice });
  });

  it("a resposta de um pedido já substituído é descartada", async () => {
    replies = {};
    const { result } = renderHook(() => useAssetData("ITUB4"));
    const first = calls.find((c) => c.route === "asset") as Call;
    act(() => result.current.reload.asset());
    const second = calls.filter((c) => c.route === "asset").at(-1) as Call;
    expect(second).not.toBe(first);

    const newer: AssetDetail = { ...ASSET, name: "NOVO" };
    await act(async () => second.resolve(ok(newer)));
    await act(async () => first.resolve(ok(ASSET)));
    expect(result.current.asset).toEqual({ state: "ok", data: newer });
  });
});

// ---------------------------------------------------------------- RF-07

describe("RF-07 — o cabeçalho", () => {
  it("código, nomes, tags, classificação e o último fechamento com a data e a frase", async () => {
    renderAsset();
    await loaded();
    const head = header();
    expect(within(head).getByRole("heading", { level: 1 }).textContent).toBe("ITUB4");
    expect(within(head).getByText("ITAUUNIBANCO")).toBeDefined();
    expect(within(head).getByText("ITAU UNIBANCO HOLDING S.A.")).toBeDefined();
    expect(within(head).getByText(TEXTOS["ativo.tipo.stock"])).toBeDefined();
    expect(within(head).getByText(TEXTOS["ativo.situacao.active"])).toBeDefined();
    expect(within(head).getByText(TEXTOS["ativo.listagem"]("N1"))).toBeDefined();
    const crumbs = within(head).getByRole("list", {
      name: TEXTOS["ativo.classificacao"],
    });
    expect([...crumbs.querySelectorAll("li")].map((li) => li.textContent)).toEqual([
      "Financeiro",
      "Intermediários Financeiros",
      "Bancos",
    ]);
    const last = head.querySelector(".ruvor-asset-head__last") as HTMLElement;
    expect(last.querySelector("[data-value='last-close']")?.textContent).toBe(
      formatCurrency(38.5),
    );
    expect(
      within(last).getByText(TEXTOS["ativo.ultimoFechamento"]("28/09/2026")),
    ).toBeDefined();
  });

  it("o nulo da classificação sai sem traço; sem listagem, sem a tag; inativo e índice", async () => {
    allOk({
      asset: ok({
        ...ASSET,
        kind: "index",
        status: "inactive",
        subsector: null,
        listing_segment: null,
      } satisfies AssetDetail),
    });
    stubFetch();
    renderAsset();
    await loaded();
    const head = header();
    const crumbs = within(head).getByRole("list", {
      name: TEXTOS["ativo.classificacao"],
    });
    expect([...crumbs.querySelectorAll("li")].map((li) => li.textContent)).toEqual([
      "Financeiro",
      "Bancos",
    ]);
    expect(within(head).queryByText(/segmento de listagem/)).toBeNull();
    expect(within(head).getByText(TEXTOS["ativo.tipo.index"])).toBeDefined();
    expect(
      within(head).getByText(TEXTOS["ativo.situacao.inactive"]).className,
    ).toContain("ruvor-tag--review");
  });

  it("sem classificação nenhuma, sem a lista", async () => {
    allOk({ asset: ok({ ...ASSET, sector: null, subsector: null, segment: null }) });
    stubFetch();
    renderAsset();
    await loaded();
    expect(within(header()).queryByRole("list")).toBeNull();
  });

  it("sem preço: '—' e 'sem preço coletado ainda' — nunca R$ 0,00", async () => {
    allOk({ asset: ok({ ...ASSET, has_prices: false, last_price: null }) });
    stubFetch();
    renderAsset();
    await loaded();
    const last = header().querySelector(".ruvor-asset-head__last") as HTMLElement;
    expect(last.querySelector("[data-value='last-close']")?.textContent).toBe("—");
    expect(within(last).getByText(TEXTOS["ativo.semPreco"])).toBeDefined();
  });
});

// ---------------------------------------------------------------- RF-08

describe("RF-08 — o preço", () => {
  it("a frase do preço ajustado junto do gráfico", async () => {
    renderAsset();
    await loaded();
    const p = pricePanel();
    expect(within(p).getByText(TEXTOS["ativo.precoAjustado"])).toBeDefined();
    expect(within(p).getByRole("img")).toBeDefined();
    expect(
      within(p).getByRole("group", { name: TEXTOS["grafico.atalhos"] }),
    ).toBeDefined();
  });

  it("sem preço: a frase e a área vazia", async () => {
    allOk({ prices: ok({ ...PRICES, results: [] }) });
    stubFetch();
    renderAsset();
    await loaded();
    const p = pricePanel();
    expect(within(p).getByText(TEXTOS["ativo.precoAjustado"])).toBeDefined();
    expect(within(p).getByText(TEXTOS["ativo.preco.vazio"])).toBeDefined();
    expect(within(p).queryByRole("img")).toBeNull();
  });
});

// ---------------------------------------------------------------- M2.3: os dois níveis

/** Um resultado de modelo, o mínimo para a seção de risco sair em E1. */
function riskResult(
  model: RiskResult["model_name"],
  alpha: RiskResult["alpha"],
): RiskResult {
  return {
    model_name: model,
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

const RUN_OK: RiskRun = {
  id: 70,
  calculated_at: "2026-09-28T19:40:00-03:00",
  finished_at: "2026-09-28T19:45:00-03:00",
  status: "ok",
  engine_version: "0.3.0",
  seed: 42,
  train_window_days: 252,
  as_of_date: "2026-09-28",
  first_price_date: "2016-09-22",
  price_count: 2487,
  train_count: 252,
  test_count: 2235,
  price_run: {
    id: 9,
    source: "yahoo-chart",
    started_at: "2026-09-28T19:00:00-03:00",
    finished_at: "2026-09-28T19:00:30-03:00",
  },
  requested_models: [...MODEL_ORDER],
  full_recompute: false,
  results: MODEL_ORDER.flatMap((m) => [
    riskResult(m, "0.0500"),
    riskResult(m, "0.0100"),
  ]),
};

/** E1: resultado pronto, sem cálculo em curso nem pedido — o acompanhamento não consulta. */
const RISK_E1: Risk = {
  ticker: "ITUB4",
  covered: true,
  latest: RUN_OK,
  in_progress: null,
  request: null,
};

const lastBox = () => header().querySelector(".ruvor-asset-head__last") as HTMLElement;
const readingGroup = () =>
  screen.getByRole("group", { name: TEXTOS["casco.leitura.rotulo"] });

describe("M2.3 — o cabeçalho e o preço nos dois níveis (V-04)", () => {
  // A data do último fechamento da fixture, como a tela a formata.
  const DATA = "28/09/2026";

  it("no iniciante: as iniciantes, e nenhuma avançada", async () => {
    comNivel("beginner");
    renderAsset();
    await loaded();
    expect(
      within(lastBox()).getByText(TEXTOS["ativo.ultimoFechamento"](DATA)),
    ).toBeDefined();
    expect(
      within(lastBox()).queryByText(TEXTOS_AVANCADOS["ativo.ultimoFechamento"](DATA)),
    ).toBeNull();
    expect(within(pricePanel()).getByText(TEXTOS["ativo.precoAjustado"])).toBeDefined();
    expect(
      within(pricePanel()).queryByText(TEXTOS_AVANCADOS["ativo.precoAjustado"]),
    ).toBeNull();
  });

  it("a prova por seção no avançado: cada chave do cabeçalho e do preço na avançada, nunca na iniciante", async () => {
    comNivel("advanced");
    renderAsset();
    await loaded();
    // Chave de função: a saída da avançada com os argumentos da fixture, e não a da iniciante.
    expect(
      within(lastBox()).getByText(TEXTOS_AVANCADOS["ativo.ultimoFechamento"](DATA)),
    ).toBeDefined();
    expect(
      within(main()).queryByText(TEXTOS["ativo.ultimoFechamento"](DATA)),
    ).toBeNull();
    // Chave de texto: a avançada presente, a iniciante ausente.
    expect(
      within(pricePanel()).getByText(TEXTOS_AVANCADOS["ativo.precoAjustado"]),
    ).toBeDefined();
    expect(within(main()).queryByText(TEXTOS["ativo.precoAjustado"])).toBeNull();
  });

  it("a prova por seção no avançado, sem preço: a frase do preço ajustado na avançada, junto da área vazia", async () => {
    // Sem série, só a frase do preço ajustado muda; o último fechamento é do caso acima.
    allOk({ prices: ok({ ...PRICES, results: [] }) });
    stubFetch();
    comNivel("advanced");
    renderAsset();
    await loaded();
    expect(
      within(pricePanel()).getByText(TEXTOS_AVANCADOS["ativo.precoAjustado"]),
    ).toBeDefined();
    expect(within(pricePanel()).queryByText(TEXTOS["ativo.precoAjustado"])).toBeNull();
    expect(within(pricePanel()).getByText(TEXTOS["ativo.preco.vazio"])).toBeDefined();
  });

  it("o valor exibido é o mesmo nos dois níveis: o fechamento e o resumo do gráfico", async () => {
    comNivel("beginner");
    renderAsset();
    await loaded();
    const valor = () =>
      lastBox().querySelector("[data-value='last-close']")?.textContent;
    const resumo = () =>
      within(pricePanel()).getByRole("img").getAttribute("aria-label");
    const antes = { valor: valor(), resumo: resumo() };
    expect(antes.valor).toBe(formatCurrency(38.5));

    fireEvent.click(
      within(readingGroup()).getByRole("button", {
        name: TEXTOS["casco.leitura.avancada"],
      }),
    );
    expect(
      within(lastBox()).getByText(TEXTOS_AVANCADOS["ativo.ultimoFechamento"](DATA)),
    ).toBeDefined();
    expect({ valor: valor(), resumo: resumo() }).toEqual(antes);
  });
});

describe("M2.3 — V-08: trocar o nível não pede nada à API", () => {
  it("com o risco em E1, a troca pelo alternador não chama o fetch, nos dois sentidos", async () => {
    allOk({ risk: ok(RISK_E1) });
    stubFetch();
    // Na visão geral: o /risk em E1 não abre acompanhamento, em aba nenhuma.
    renderAsset();
    await loaded();
    const fetchSpy = vi.mocked(fetch);
    const antes = fetchSpy.mock.calls.length;
    // Um respiro depois da troca, para qualquer efeito disparado por ela chegar ao fetch.
    const respiro = () =>
      act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 50));
      });

    const group = readingGroup();
    expect(group.closest("[aria-live]")).toBeNull();
    fireEvent.click(
      within(group).getByRole("button", { name: TEXTOS["casco.leitura.avancada"] }),
    );
    await respiro();
    expect(fetchSpy.mock.calls.length).toBe(antes);
    expect(
      within(pricePanel()).getByText(TEXTOS_AVANCADOS["ativo.precoAjustado"]),
    ).toBeDefined();

    fireEvent.click(
      within(readingGroup()).getByRole("button", {
        name: TEXTOS["casco.leitura.iniciante"],
      }),
    );
    await respiro();
    expect(fetchSpy.mock.calls.length).toBe(antes);
    expect(within(pricePanel()).getByText(TEXTOS["ativo.precoAjustado"])).toBeDefined();
  });
});

// ---------------------------------------------------------------- RF-09

describe("RF-09 — proventos e desdobramentos", () => {
  const rows = () =>
    [...within(eventsPanel()).getAllByRole("row")]
      .slice(1)
      .map((tr) => [...tr.querySelectorAll("td")].map((td) => td.textContent));

  it("os dos 12 meses até o último fechamento, do mais novo ao mais antigo; e ver todos", async () => {
    renderAsset();
    await loaded();
    await waitFor(() => expect(within(eventsPanel()).getByRole("table")).toBeDefined());
    expect(
      within(eventsPanel()).getByText(TEXTOS["ativo.eventos.periodo"]("28/09/2026")),
    ).toBeDefined();
    const amount = TEXTOS["ativo.eventos.valor"](formatCurrencyPrecise(0.0217));
    expect(rows()).toEqual([
      ["01/09/2026", TEXTOS["ativo.eventos.dividend"], amount],
      ["01/08/2026", TEXTOS["ativo.eventos.dividend"], amount],
      [
        "20/03/2026",
        TEXTOS["ativo.eventos.split"],
        TEXTOS["ativo.eventos.proporcao"]("12", "10"),
      ],
    ]);

    const more = within(eventsPanel()).getByRole("button", {
      name: TEXTOS["ativo.eventos.verTodos"]("5"),
    });
    expect(more.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(more);
    expect(rows()).toHaveLength(5);
    expect(rows()[4]).toEqual([
      "18/03/2024",
      TEXTOS["ativo.eventos.split"],
      TEXTOS["ativo.eventos.proporcao"]("11", "10"),
    ]);
    fireEvent.click(
      within(eventsPanel()).getByRole("button", {
        name: TEXTOS["ativo.eventos.verMenos"],
      }),
    );
    expect(rows()).toHaveLength(3);
  });

  it("sem eventos no período: a frase, e ver todos se houver antigos", async () => {
    allOk({ events: ok({ ticker: "ITUB4", results: EVENTS.results.slice(0, 2) }) });
    stubFetch();
    renderAsset();
    await loaded();
    await waitFor(() =>
      expect(
        within(eventsPanel()).getByText(TEXTOS["ativo.eventos.nenhum"]),
      ).toBeDefined(),
    );
    expect(within(eventsPanel()).queryByRole("table")).toBeNull();
    expect(
      within(eventsPanel()).getByRole("button", {
        name: TEXTOS["ativo.eventos.verTodos"]("2"),
      }),
    ).toBeDefined();
  });

  it("sem evento nenhum: a frase, sem ver todos", async () => {
    allOk({ events: ok({ ticker: "IBOV", results: [] }) });
    stubFetch();
    renderAsset();
    await loaded();
    await waitFor(() =>
      expect(
        within(eventsPanel()).getByText(TEXTOS["ativo.eventos.nenhum"]),
      ).toBeDefined(),
    );
    expect(within(eventsPanel()).queryByRole("button")).toBeNull();
  });
});

// ---------------------------------------------------------------- RF-10, RF-11 e V-14

/** Cada campo com frase (a lista fechada do RF-21), o valor e a frase esperados. */
const EXPECTED: Array<[field: string, value: string, phrase: string]> = [
  ["return_1m", "+2,0%", TEXTOS["comportamento.return_1m"](formatCurrency(102))],
  ["return_3m", "−5,0%", TEXTOS["comportamento.return_3m"](formatCurrency(95))],
  ["return_6m", "+10,0%", TEXTOS["comportamento.return_6m"](formatCurrency(110))],
  ["return_12m", "+25,8%", TEXTOS["comportamento.return_12m"](formatCurrency(125.81))],
  ["return_36m", "+50,0%", TEXTOS["comportamento.return_36m"](formatCurrency(150))],
  ["return_60m", "+66,2%", TEXTOS["comportamento.return_60m"](formatCurrency(166.17))],
  [
    "return_120m",
    "+208,3%",
    TEXTOS["comportamento.return_120m"](formatCurrency(308.29)),
  ],
  ["return_ytd", "+13,6%", TEXTOS["comportamento.return_ytd"](formatCurrency(113.57))],
  ["volatility_12m", "17,5%", TEXTOS["comportamento.volatility_12m"]("17,5%")],
  ["volatility_60m", "25,0%", TEXTOS["comportamento.volatility_60m"]("25,0%")],
  [
    "max_drawdown",
    "−46,8%",
    TEXTOS["comportamento.max_drawdown"](
      "46,8%",
      "23/01/2020",
      "23/03/2020",
      "22/09/2016",
      "06/01/2021",
    ),
  ],
  [
    "max_drawdown_recovery_sessions",
    "195",
    TEXTOS["comportamento.max_drawdown_recovery_sessions"]("0,8"),
  ],
  ["beta_60m", "0,85", TEXTOS["comportamento.beta_60m"]("0,85%", false)],
  ["correlation_60m", "−0,12", TEXTOS["comportamento.correlation_60m"]("−0,12")],
  ["skewness", "−0,05", TEXTOS["comportamento.skewness"]("−0,05", -1)],
  ["excess_kurtosis", "1,07", TEXTOS["comportamento.excess_kurtosis"]("1,07", 1)],
  ["dividends_12m", formatCurrency(3.4567), TEXTOS["comportamento.dividends_12m"]],
  ["dividend_payments_12m", "14", TEXTOS["comportamento.dividend_payments_12m"]],
  [
    "dividend_yield_12m",
    "8,1%",
    TEXTOS["comportamento.dividend_yield_12m"]("28/09/2026", formatCurrency(8.12)),
  ],
  [
    "avg_volume_21d",
    TEXTOS["comportamento.unidade.volume"]("25,4"),
    TEXTOS["comportamento.avg_volume_21d"],
  ],
  [
    "avg_volume_252d",
    TEXTOS["comportamento.unidade.volume"]("21,0"),
    TEXTOS["comportamento.avg_volume_252d"],
  ],
];

describe("RF-10 — o comportamento, formatado em pt-BR, e V-14: a frase junto do número", () => {
  it("a lista cobre os 19 campos com frase e as duas medidas da distribuição", () => {
    expect(EXPECTED).toHaveLength(21);
  });

  it("o retorno no ano: a iniciante emendada no portão da T6 do M2.3, literal", () => {
    // Segunda exceção ao "Fora" da spec do M2.3: o cálculo parte do fechamento do último
    // pregão antes do ano corrente, não do primeiro pregão do ano.
    expect(TEXTOS["comportamento.return_ytd"]("R$ 114,98")).toBe(
      "Desde o fechamento do último pregão do ano passado, com os proventos: R$ 100 viraram R$ 114,98.",
    );
  });

  it.each(EXPECTED)("%s: %s, com a frase", async (field, value, phrase) => {
    renderAsset();
    await loaded();
    openMoments();
    expect(statValue(field)).toBe(value);
    expect(statPhrase(field)).toBe(phrase);
  });

  it("o cabeçalho do bloco diz até quando, e as notas dizem sobre quantos pregões", async () => {
    renderAsset();
    await loaded();
    expect(
      within(behavior()).getByText(TEXTOS["comportamento.ate"]("28/09/2026")),
    ).toBeDefined();
    expect(
      within(block(TEXTOS["comportamento.bloco.ibov"])).getByText(
        TEXTOS["comportamento.nota.ibov"]("1.230"),
      ),
    ).toBeDefined();
    expect(
      within(block(TEXTOS["comportamento.bloco.distribuicao"])).getByText(
        TEXTOS["comportamento.nota.distribuicao"]("1.247"),
      ),
    ).toBeDefined();
    expect(
      within(block(TEXTOS["comportamento.bloco.retornos"])).getByText(
        TEXTOS["comportamento.nota.retornos"],
      ),
    ).toBeDefined();
  });

  it("RF-11: o histograma com a frase dele, no bloco da distribuição", async () => {
    renderAsset();
    await loaded();
    const dist = block(TEXTOS["comportamento.bloco.distribuicao"]);
    expect(within(dist).getByText(TEXTOS["comportamento.histograma"])).toBeDefined();
    expect(within(dist).getByRole("img")).toBeDefined();
    expect(
      within(dist).queryByText(TEXTOS["comportamento.histogramaCurto"]),
    ).toBeNull();
  });
});

describe("V-06 — nulo não é zero", () => {
  /** Cada campo nulo da série curta: "—" e o porquê. */
  const NULLS: Array<[field: string, phrase: string | null]> = [
    ["return_36m", TEXTOS["comportamento.nulo.janela"](36)],
    ["return_60m", TEXTOS["comportamento.nulo.janela"](60)],
    ["return_120m", TEXTOS["comportamento.nulo.janela"](120)],
    ["volatility_60m", TEXTOS["comportamento.nulo.janela"](60)],
    ["max_drawdown_recovery_sessions", TEXTOS["comportamento.nulo.naoRecuperou"]],
    ["beta_60m", TEXTOS["comportamento.nulo.janela"](60)],
    ["correlation_60m", TEXTOS["comportamento.nulo.janela"](60)],
    ["skewness", TEXTOS["comportamento.nulo.janela"](60)],
    ["excess_kurtosis", TEXTOS["comportamento.nulo.janela"](60)],
    ["avg_volume_252d", TEXTOS["comportamento.nulo.pregoes"](252)],
  ];

  beforeEach(() => {
    allOk({ metrics: ok({ ticker: "ITUB4", metric: METRIC_SHORT }) });
    stubFetch();
  });

  it.each(NULLS)("%s nulo mostra '—' e o porquê", async (field, phrase) => {
    renderAsset();
    await loaded();
    openMoments();
    expect(statValue(field)).toBe("—");
    expect(statPhrase(field)).toBe(phrase);
  });

  it("a queda sem volta diz que ainda não voltou; o que não é nulo segue formatado", async () => {
    renderAsset();
    await loaded();
    expect(statPhrase("max_drawdown")).toBe(
      TEXTOS["comportamento.max_drawdown"](
        "46,8%",
        "23/01/2020",
        "23/03/2020",
        "02/01/2025",
        null,
      ),
    );
    expect(statValue("return_12m")).toBe("+25,8%");
  });

  it("a série curta: a frase no lugar do histograma, sem a nota de pregões", async () => {
    renderAsset();
    await loaded();
    const dist = block(TEXTOS["comportamento.bloco.distribuicao"]);
    expect(
      within(dist).getByText(TEXTOS["comportamento.histogramaCurto"]),
    ).toBeDefined();
    expect(within(dist).queryByRole("img")).toBeNull();
    expect(within(dist).queryByText(TEXTOS["comportamento.histograma"])).toBeNull();
    expect(dist.querySelector(".ruvor-panel__note")).toBeNull();
    expect(
      block(TEXTOS["comportamento.bloco.ibov"]).querySelector(".ruvor-panel__note"),
    ).toBeNull();
  });

  it("nenhum número em destaque de campo nulo é zero", async () => {
    renderAsset();
    await loaded();
    openMoments();
    for (const [field] of NULLS) {
      expect(statValue(field)).not.toMatch(/\d/);
    }
  });

  it("no índice, o beta e a correlação nulos dizem que ele é a própria referência", async () => {
    allOk({
      asset: ok({ ...ASSET, ticker: "IBOV", kind: "index" }),
      metrics: ok({ ticker: "IBOV", metric: METRIC_SHORT }),
    });
    stubFetch();
    renderAsset("IBOV");
    await loaded();
    for (const field of ["beta_60m", "correlation_60m"]) {
      expect(statValue(field)).toBe("—");
      expect(statPhrase(field)).toBe(TEXTOS["comportamento.nulo.referencia"]);
    }
  });

  it("metric: null — ainda não calculado, apontando para o risco", async () => {
    allOk({ metrics: ok({ ticker: "AALR3", metric: null } satisfies Metrics) });
    stubFetch();
    renderAsset();
    await loaded();
    const section = behavior();
    expect(
      within(section).getByText(TEXTOS["comportamento.naoCalculado"]),
    ).toBeDefined();
    expect(
      within(section).getByText(TEXTOS["comportamento.naoCalculado.nota"]),
    ).toBeDefined();
    const link = within(section).getByRole("link", {
      name: TEXTOS["comportamento.irParaRisco"],
    });
    expect(link.getAttribute("href")).toBe("/ativos/ITUB4/risco");
    expect(section.querySelector("[data-field]")).toBeNull();
    expect(within(section).queryByText(/^até /)).toBeNull();
  });
});

// ---------------------------------------------------------------- M2.3: o comportamento nos dois níveis

type PhraseSource = Readonly<Record<string, unknown>>;

/** A frase de uma chave num dos dois módulos, com os argumentos (chave de texto: sem argumento). */
function phraseOf(source: PhraseSource, key: string, args: readonly unknown[]): string {
  const entry = source[key];
  if (typeof entry === "function")
    return (entry as (...a: unknown[]) => string)(...args);
  if (typeof entry === "string") return entry;
  throw new Error(`sem entrada: ${key}`);
}

/**
 * As 22 chaves `comportamento.*` da lista do RF-04, com os argumentos que a fixture `METRIC`
 * produz — os mesmos de `EXPECTED`. A fixture exercita todas as 22; o ramo que ela não tem (a
 * queda sem volta) vem de `METRIC_SHORT`, no caso próprio abaixo.
 */
const BEHAVIOR_KEYS: Array<[key: string, args: readonly unknown[]]> = [
  ["comportamento.return_1m", [formatCurrency(102)]],
  ["comportamento.return_3m", [formatCurrency(95)]],
  ["comportamento.return_6m", [formatCurrency(110)]],
  ["comportamento.return_12m", [formatCurrency(125.81)]],
  ["comportamento.return_36m", [formatCurrency(150)]],
  ["comportamento.return_60m", [formatCurrency(166.17)]],
  ["comportamento.return_120m", [formatCurrency(308.29)]],
  ["comportamento.return_ytd", [formatCurrency(113.57)]],
  ["comportamento.volatility_12m", ["17,5%"]],
  ["comportamento.volatility_60m", ["25,0%"]],
  [
    "comportamento.max_drawdown",
    ["46,8%", "23/01/2020", "23/03/2020", "22/09/2016", "06/01/2021"],
  ],
  ["comportamento.max_drawdown_recovery_sessions", ["0,8"]],
  ["comportamento.beta_60m", ["0,85%", false]],
  ["comportamento.correlation_60m", ["−0,12"]],
  ["comportamento.histograma", []],
  ["comportamento.skewness", ["−0,05", -1]],
  ["comportamento.excess_kurtosis", ["1,07", 1]],
  ["comportamento.dividends_12m", []],
  ["comportamento.dividend_payments_12m", []],
  ["comportamento.dividend_yield_12m", ["28/09/2026", formatCurrency(8.12)]],
  ["comportamento.avg_volume_21d", []],
  ["comportamento.avg_volume_252d", []],
];

const distribution = () => block(TEXTOS["comportamento.bloco.distribuicao"]);
const momentsRoot = () =>
  behavior().querySelector<HTMLElement>('[data-collapsible="moments"]') as HTMLElement;
/** Os números em destaque da seção, na ordem da tela. */
const statValues = () =>
  [...behavior().querySelectorAll(".ruvor-stat__value")].map((el) => el.textContent);
/**
 * Se a frase está na seção, exata, num parágrafo: compara o `textContent` cru — o `getByText`
 * normaliza o espaço fino do "R$" na tela, mas não no texto procurado.
 */
const behaviorHas = (phrase: string) =>
  [...behavior().querySelectorAll("p")].some((el) => el.textContent === phrase);

describe("M2.3 — o comportamento nos dois níveis (V-04)", () => {
  it("a lista cobre as 22 chaves comportamento.* do RF-04, todas com avançada", () => {
    expect(new Set(BEHAVIOR_KEYS.map(([key]) => key)).size).toBe(22);
    for (const [key] of BEHAVIOR_KEYS) {
      expect(Object.hasOwn(TEXTOS_AVANCADOS, key), key).toBe(true);
    }
  });

  it("a prova por seção no avançado: cada chave na avançada, nunca na iniciante", async () => {
    comNivel("advanced");
    renderAsset();
    await loaded();
    const ausentes: string[] = [];
    const presentes: string[] = [];
    for (const [key, args] of BEHAVIOR_KEYS) {
      const avancada = phraseOf(TEXTOS_AVANCADOS, key, args);
      const iniciante = phraseOf(TEXTOS, key, args);
      if (!behaviorHas(avancada)) ausentes.push(key);
      if (behaviorHas(iniciante)) presentes.push(key);
    }
    expect(ausentes, "avançada ausente").toEqual([]);
    expect(presentes, "iniciante presente").toEqual([]);
  });

  it("no iniciante, aberta a assimetria e a curtose: as iniciantes, e nenhuma avançada", async () => {
    comNivel("beginner");
    renderAsset();
    await loaded();
    openMoments();
    const ausentes: string[] = [];
    const presentes: string[] = [];
    for (const [key, args] of BEHAVIOR_KEYS) {
      const avancada = phraseOf(TEXTOS_AVANCADOS, key, args);
      const iniciante = phraseOf(TEXTOS, key, args);
      if (!behaviorHas(iniciante)) ausentes.push(key);
      if (behaviorHas(avancada)) presentes.push(key);
    }
    expect(ausentes, "iniciante ausente").toEqual([]);
    expect(presentes, "avançada presente").toEqual([]);
  });

  it("o ramo da queda sem volta, no avançado (a série curta)", async () => {
    allOk({ metrics: ok({ ticker: "ITUB4", metric: METRIC_SHORT }) });
    stubFetch();
    comNivel("advanced");
    renderAsset();
    await loaded();
    const args = ["46,8%", "23/01/2020", "23/03/2020", "02/01/2025", null] as const;
    expect(statPhrase("max_drawdown")).toBe(
      TEXTOS_AVANCADOS["comportamento.max_drawdown"](...args),
    );
  });

  it("o valor exibido é o mesmo nos dois níveis, e a troca pelo alternador só muda a frase", async () => {
    comNivel("beginner");
    renderAsset();
    await loaded();
    openMoments();
    const antes = statValues();
    expect(antes).toHaveLength(21);
    expect(statPhrase("volatility_12m")).toBe(
      TEXTOS["comportamento.volatility_12m"]("17,5%"),
    );

    fireEvent.click(
      within(readingGroup()).getByRole("button", {
        name: TEXTOS["casco.leitura.avancada"],
      }),
    );
    expect(statPhrase("volatility_12m")).toBe(
      TEXTOS_AVANCADOS["comportamento.volatility_12m"]("17,5%"),
    );
    expect(statValues()).toEqual(antes);
  });
});

describe("M2.3 — a assimetria e a curtose recolhidas na iniciante (V-05)", () => {
  it("na iniciante: o botão fechado, e a assimetria e a curtose fora da árvore", async () => {
    comNivel("beginner");
    renderAsset();
    await loaded();
    expect(momentsToggle().getAttribute("aria-expanded")).toBe("false");
    expect(momentsRoot().getAttribute("data-open")).toBe("false");
    expect(stat("skewness")).toBeNull();
    expect(stat("excess_kurtosis")).toBeNull();
    expect(
      within(behavior()).queryByText(TEXTOS["comportamento.rotulo.skewness"]),
    ).toBeNull();
    const controls = momentsToggle().getAttribute("aria-controls") as string;
    expect(document.getElementById(controls)).toBeNull();
  });

  it("abrir na iniciante mostra os mesmos números do avançado, com as frases iniciantes", async () => {
    comNivel("beginner");
    renderAsset();
    await loaded();
    fireEvent.click(momentsToggle());
    expect(momentsToggle().getAttribute("aria-expanded")).toBe("true");
    expect(statValue("skewness")).toBe("−0,05");
    expect(statValue("excess_kurtosis")).toBe("1,07");
    expect(statPhrase("skewness")).toBe(TEXTOS["comportamento.skewness"]("−0,05", -1));
    const controls = momentsToggle().getAttribute("aria-controls") as string;
    expect(document.getElementById(controls)?.contains(stat("skewness"))).toBe(true);
  });

  it("na avançada: aberto por padrão, com os mesmos números", async () => {
    comNivel("advanced");
    renderAsset();
    await loaded();
    expect(momentsToggle().getAttribute("aria-expanded")).toBe("true");
    expect(momentsRoot().getAttribute("data-open")).toBe("true");
    expect(statValue("skewness")).toBe("−0,05");
    expect(statValue("excess_kurtosis")).toBe("1,07");
  });

  it("trocar o nível pelo alternador reaplica o padrão: o aberto à mão fecha ao voltar à iniciante", async () => {
    comNivel("beginner");
    renderAsset();
    await loaded();
    fireEvent.click(momentsToggle());
    const button = (key: "casco.leitura.avancada" | "casco.leitura.iniciante") =>
      within(readingGroup()).getByRole("button", { name: TEXTOS[key] });
    fireEvent.click(button("casco.leitura.avancada"));
    expect(momentsToggle().getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(momentsToggle());
    expect(stat("skewness")).toBeNull();
    fireEvent.click(button("casco.leitura.iniciante"));
    expect(momentsToggle().getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(button("casco.leitura.avancada"));
    expect(momentsToggle().getAttribute("aria-expanded")).toBe("true");
    expect(statValue("skewness")).toBe("−0,05");
  });

  it("o histograma fica aberto nos dois níveis, fora do recolhível", async () => {
    for (const reading of ["beginner", "advanced"] as const) {
      comNivel(reading);
      renderAsset();
      await loaded();
      const chart = within(distribution()).getByRole("img");
      expect(chart.closest("[data-collapsible]"), reading).toBeNull();
      const phrase = within(distribution()).getByText(
        reading === "advanced"
          ? TEXTOS_AVANCADOS["comportamento.histograma"]
          : TEXTOS["comportamento.histograma"],
      );
      expect(phrase.closest("[data-collapsible]"), reading).toBeNull();
      cleanup();
    }
  });

  it("o resto da seção nunca tem controle: o único recolhível é o da assimetria e da curtose", async () => {
    for (const reading of ["beginner", "advanced"] as const) {
      comNivel(reading);
      renderAsset();
      await loaded();
      expect(behavior().querySelectorAll("[data-collapsible]")).toHaveLength(1);
      expect(behavior().querySelectorAll("[aria-expanded]")).toHaveLength(1);
      for (const field of [
        "return_12m",
        "volatility_12m",
        "max_drawdown",
        "beta_60m",
      ]) {
        expect(stat(field).closest("[data-collapsible]"), field).toBeNull();
      }
      cleanup();
    }
  });

  it("nem o recolhível nem o alternador ficam dentro de região viva", async () => {
    comNivel("advanced");
    renderAsset();
    await loaded();
    for (const el of document.querySelectorAll("[data-collapsible]")) {
      expect(el.closest("[aria-live]")).toBeNull();
      expect(el.querySelector("[aria-live]")).toBeNull();
    }
    expect(readingGroup().closest("[aria-live]")).toBeNull();
    expect(behavior().closest("[aria-live]")).toBeNull();
  });

  it("a série curta: a frase no lugar do histograma, e o recolhível continua, com os nulos dentro", async () => {
    allOk({ metrics: ok({ ticker: "ITUB4", metric: METRIC_SHORT }) });
    stubFetch();
    comNivel("beginner");
    renderAsset();
    await loaded();
    const short = within(distribution()).getByText(
      TEXTOS["comportamento.histogramaCurto"],
    );
    expect(short.closest("[data-collapsible]")).toBeNull();
    expect(momentsToggle().getAttribute("aria-expanded")).toBe("false");
    expect(stat("skewness")).toBeNull();
    fireEvent.click(momentsToggle());
    expect(statValue("skewness")).toBe("—");
    expect(statPhrase("skewness")).toBe(TEXTOS["comportamento.nulo.janela"](60));
    expect(statValue("excess_kurtosis")).toBe("—");
  });
});
