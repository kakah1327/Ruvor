/**
 * A seção de risco (T11): RF-12 a RF-19 na tela.
 *
 * - V-07: toda perda vem com "em 1 dia" — junto da faixa, ou no cabeçalho da coluna;
 * - V-08: a discordância com "7 de 9", com um modelo só e com nenhum;
 * - V-09: a tabela em MODEL_ORDER, com os resultados na ordem da API e embaralhados; as três
 *   frases dos não rejeitados; `adequate` nulo não conta como reprovado;
 * - V-10: as barras numa escala só (o máximo das dezoito perdas); tags com texto; a linha que
 *   abre com violações × esperadas e os três testes, nos dois níveis; nada de Basileia;
 * - V-11: `data-risk-state` para cada linha da tabela de decisão, mais `RISCO_CARREGANDO` e
 *   `RISCO_ERRO`; as respostas do `POST` (202, 409 com `details`, 429, 422, erro, sem
 *   resposta) e o `X-CSRFToken`;
 * - V-14 da seção; a trilha na coluna lateral e a proveniência no rodapé.
 *
 * O `fetch` é um duplo que responde pela rota e pelo método; o uPlot, um duplo mínimo.
 */
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { routes } from "../src/App";
import {
  type AssetDetail,
  type ComputeRequest,
  type InProgress,
  MODEL_ORDER,
  type ModelName,
  type PriceRow,
  type Prices,
  type Risk,
  type RiskResult,
  type RiskRun,
} from "../src/api/types";
import { traduzirMotivo } from "../src/content/motivos";
import { TEXTOS } from "../src/content/textos";
import { formatPercent } from "../src/format/numbers";
import { lossFromVar } from "../src/format/var";

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
  subsector: null,
  segment: null,
  listing_segment: null,
  last_price: { date: "2026-09-28", close: "38.500000", adj_close: "38.500000" },
};

function priceRows(n: number): PriceRow[] {
  const start = Date.UTC(2016, 0, 4);
  return Array.from({ length: n }, (_, i) => {
    const date = new Date(start + i * 86400000).toISOString().slice(0, 10);
    return {
      date,
      open: "20.0000",
      high: "20.0000",
      low: "20.0000",
      close: "20.0000",
      adj_close: "20.0000",
      volume: 1,
    };
  });
}

const prices = (n: number): Prices => ({
  ticker: "ITUB4",
  from: null,
  to: null,
  results: priceRows(n),
});

/** O VaR de cada modelo a 95%; a 99% é 1,5 vez — menos o EGARCH, o máximo das dezoito. */
const VAR95: Record<ModelName, number> = {
  historical: 0.05,
  parametric: 0.03,
  monte_carlo: 0.02,
  garch_1_1: 0.04,
  egarch: 0.06,
  lstm: 0.01,
  gru: 0.035,
  garchnet: 0.045,
  caviar: 0.025,
};
const EGARCH_99 = 0.2;

type ResultOver = Partial<RiskResult>;

function result(model: ModelName, alpha: "0.0500" | "0.0100", over: ResultOver = {}) {
  const v =
    alpha === "0.0500"
      ? VAR95[model]
      : model === "egarch"
        ? EGARCH_99
        : 1.5 * VAR95[model];
  const base: RiskResult = {
    model_name: model,
    model_category: "traditional",
    alpha,
    hyperparameters: {},
    var_latest: v.toFixed(10),
    var_mean: v.toFixed(10),
    violations: alpha === "0.0500" ? 118 : 25,
    expected_violations: alpha === "0.0500" ? "112.100000" : "22.420000",
    kupiec_passed: true,
    kupiec_p_value: "0.5810000000",
    christoffersen_passed: false,
    christoffersen_p_value: "0.0004000000",
    dq_passed: true,
    dq_p_value: "0.0820000000",
    basel_zone: "zona-basel-verde",
    adequate: false,
    error: "",
    reused_snapshots: null,
    trained_snapshots: null,
  };
  return { ...base, ...over };
}

/** Os dezoito, na ordem da API: `model_name`, e 95% antes de 99% (`views.py`). */
function apiOrder(
  over: (m: ModelName, a: "0.0500" | "0.0100") => ResultOver = () => ({}),
) {
  return [...MODEL_ORDER]
    .sort()
    .flatMap((m) => [
      result(m, "0.0500", over(m, "0.0500")),
      result(m, "0.0100", over(m, "0.0100")),
    ]);
}

/** Um embaralhamento fixo (nem a ordem da API, nem a MODEL_ORDER, nem por valor). */
function shuffled<T>(items: T[]): T[] {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i--) {
    const j = (i * 7 + 3) % (i + 1);
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function run(results: RiskResult[], over: Partial<RiskRun> = {}): RiskRun {
  return {
    id: 63,
    calculated_at: "2026-09-28T19:30:05.120000-03:00",
    finished_at: "2026-09-28T19:32:10.000000-03:00",
    status: "ok",
    engine_version: "0.3.0",
    seed: 42,
    train_window_days: 252,
    as_of_date: "2026-09-25",
    first_price_date: "2016-09-22",
    price_count: 2487,
    train_count: 252,
    test_count: 2235,
    price_run: {
      id: 9,
      source: "yahoo-chart",
      started_at: "2026-09-28T19:00:00-03:00",
      finished_at: "2026-09-28T19:01:00-03:00",
    },
    requested_models: [...MODEL_ORDER],
    full_recompute: false,
    results,
    ...over,
  };
}

const inProgress = (w: number, e = 18): InProgress => ({
  id: 64,
  calculated_at: "2026-09-29T19:30:05-03:00",
  requested_models: [...MODEL_ORDER],
  results_written: w,
  results_expected: e,
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
  ticker: "ITUB4",
  covered: false,
  latest: null,
  in_progress: null,
  request: null,
  ...over,
});

const E1 = risk({ covered: true, latest: run(apiOrder()) });

// ---------------------------------------------------------------- o duplo do fetch

type Route =
  | "asset"
  | "prices"
  | "events"
  | "metrics"
  | "risk"
  | "fundamentals"
  | "disclosures"
  | "post";
type Reply = { status: number; body: unknown } | "network" | "html";

const ok = (body: unknown): Reply => ({ status: 200, body });
const fail = (
  status: number,
  code = "internal_error",
  message = "falhou",
  details = {},
) => ({ status, body: { error: { code, message, details } } }) as Reply;

type Call = {
  url: string;
  route: Route;
  headers: Record<string, string>;
  resolve: (reply: Reply) => void;
};

let calls: Call[] = [];
let replies: Partial<Record<Route, Reply>> = {};

/** A rota do pedido; só `/disclosures` leva parâmetros (a seção Comunicados pede a página). */
function routeOf(url: string, method: string): Route {
  const match =
    /^\/api\/v1\/assets\/[^/?]+(?:\/(prices|events|metrics|risk|fundamentals)|\/(disclosures)\?[^/]*)?$/.exec(
      url,
    );
  if (match === null) throw new Error(`pedido inesperado: ${url}`);
  if (method === "POST") {
    if (match[1] !== "risk") throw new Error(`POST inesperado: ${url}`);
    return "post";
  }
  return (match[1] ?? match[2] ?? "asset") as Route;
}

function stubFetch(): void {
  calls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url: string, init?: RequestInit) =>
        new Promise<Response>((resolve, reject) => {
          const route = routeOf(url, init?.method ?? "GET");
          const call: Call = {
            url,
            route,
            headers: { ...((init?.headers as Record<string, string>) ?? {}) },
            resolve: (r) => {
              if (r === "network") reject(new TypeError("Failed to fetch"));
              else if (r === "html")
                resolve({
                  ok: false,
                  status: 502,
                  json: async () => {
                    throw new SyntaxError("não é JSON");
                  },
                } as unknown as Response);
              else
                resolve({
                  ok: r.status >= 200 && r.status < 300,
                  status: r.status,
                  json: async () => r.body,
                } as unknown as Response);
            },
          };
          calls.push(call);
          const reply = replies[route];
          if (reply !== undefined) call.resolve(reply);
        }),
    ),
  );
}

function allOk(over: Partial<Record<Route, Reply>> = {}): void {
  replies = {
    asset: ok(ASSET),
    prices: ok(prices(40)),
    events: ok({ ticker: "ITUB4", results: [] }),
    metrics: ok({ ticker: "ITUB4", metric: null }),
    risk: ok(E1),
    fundamentals: ok({ ticker: "ITUB4", indicator: null, peers: null }),
    disclosures: ok({
      ticker: "ITUB4",
      company: { code_cvm: "19348", name: "ITAU UNIBANCO HOLDING S.A." },
      count: 0,
      limit: 10,
      offset: 0,
      results: [],
    }),
    ...over,
  };
}

function renderAsset(ticker = "ITUB4") {
  const router = createMemoryRouter(routes, { initialEntries: [`/ativos/${ticker}`] });
  render(<RouterProvider router={router} />);
  return router;
}

function clearCookie(): void {
  // biome-ignore lint/suspicious/noDocumentCookie: o teste do X-CSRFToken lê o cookie de verdade.
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
}

beforeEach(() => {
  allOk();
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  clearCookie();
});

// ---------------------------------------------------------------- as partes

const section = () =>
  document.querySelector<HTMLElement>("[data-risk-state]") as HTMLElement;
const riskState = () => section()?.getAttribute("data-risk-state");
/**
 * O texto no corpo da seção, fora da região viva: o andamento aparece nos dois lugares (RF-01
 * do M1.6d), e o que se confere aqui é o painel visível — exatamente um elemento.
 */
const inBody = (text: string) => {
  const found = within(section())
    .getAllByText(text)
    .filter((el) => el.closest("[aria-live]") === null);
  expect(found).toHaveLength(1);
  return found[0];
};
const level = (alpha: string) =>
  section().querySelector<HTMLElement>(`article[data-alpha="${alpha}"]`) as HTMLElement;
const phrase = (host: HTMLElement, name: string) =>
  host.querySelector(`[data-phrase="${name}"]`)?.textContent;
const table = () => within(section()).getByRole("table");
const row = (model: ModelName) =>
  table().querySelector<HTMLElement>(`tr[data-model="${model}"]`) as HTMLElement;
const cells = (model: ModelName) => [...row(model).querySelectorAll("td")].slice(1);
const rail = () => screen.queryByRole("complementary");
const footer = () => screen.getByRole("contentinfo");

async function settled(state: string): Promise<void> {
  await waitFor(() => expect(riskState()).toBe(state));
}

const loss = (v: number) => formatPercent(lossFromVar(v), 1);

// ---------------------------------------------------------------- V-07

describe("V-07 — a perda em percentual simples, sempre com o horizonte", () => {
  it('"0.0500000000" mostra 4,9%', async () => {
    renderAsset();
    await settled("E1");
    const cell = cells("historical")[0];
    expect(cell.querySelector(".ruvor-loss")?.textContent).toBe("4,9%");
  });

  it('toda perda da seção vem com "em 1 dia": junto da faixa, ou no cabeçalho da coluna', async () => {
    renderAsset();
    await settled("E1");
    const ranges = section().querySelectorAll(".ruvor-range");
    expect(ranges).toHaveLength(2);
    for (const range of ranges) {
      expect(range.textContent).toContain(TEXTOS["risco.horizonte"]);
    }
    const headers = [...table().querySelectorAll("thead th")];
    const losses = table().querySelectorAll(".ruvor-loss");
    expect(losses).toHaveLength(18);
    for (const lossEl of losses) {
      const cell = lossEl.closest("td") as HTMLTableCellElement;
      const header = headers[cell.cellIndex];
      expect(header.textContent).toContain(TEXTOS["risco.horizonte"]);
    }
  });
});

// ---------------------------------------------------------------- V-08

describe("V-08 — a discordância", () => {
  it('"7 de 9" com dois modelos falhos, e a faixa sobre os sete', async () => {
    const failed = new Set<ModelName>(["lstm", "egarch"]);
    const results = apiOrder((m, a) =>
      a === "0.0500" && failed.has(m)
        ? {
            var_latest: null,
            var_mean: null,
            adequate: null,
            kupiec_passed: null,
            error: "falhou",
          }
        : {},
    );
    allOk({ risk: ok(risk({ latest: run(results, { status: "partial" }) })) });
    stubFetch();
    renderAsset();
    await settled("E1");

    const text = phrase(level("0.0500"), "discordancia") ?? "";
    expect(text).toContain("7 de 9");
    // o mínimo e o máximo dos sete que calcularam: o Monte Carlo e o histórico
    const min = loss(VAR95.monte_carlo);
    const max = loss(VAR95.historical);
    expect(text).toBe(TEXTOS["risco.discordancia"](min, max, 7, 9, 20, min));
    expect(level("0.0500").querySelector(".ruvor-range b")?.textContent).toBe(
      TEXTOS["risco.faixa"](min, max),
    );
    // o outro nível tem os nove
    expect(phrase(level("0.0100"), "discordancia")).toContain("Os nove modelos");
  });

  it("um modelo só: o número dele, sem faixa", async () => {
    const results = apiOrder((m, a) =>
      a === "0.0100" && m !== "garch_1_1"
        ? {
            var_latest: null,
            var_mean: null,
            adequate: null,
            kupiec_passed: null,
            error: "x",
          }
        : {},
    );
    allOk({ risk: ok(risk({ latest: run(results, { status: "partial" }) })) });
    stubFetch();
    renderAsset();
    await settled("E1");
    const only = loss(1.5 * VAR95.garch_1_1);
    expect(level("0.0100").querySelector(".ruvor-range b")?.textContent).toBe(only);
    expect(phrase(level("0.0100"), "discordancia")).toBe(
      TEXTOS["risco.discordancia"](only, only, 1, 9, 100, only),
    );
  });

  it("nenhum: '—' e a frase de que o cálculo falhou em todos", async () => {
    const results = apiOrder((_m, a) =>
      a === "0.0100"
        ? {
            var_latest: null,
            var_mean: null,
            adequate: null,
            kupiec_passed: null,
            error: "x",
          }
        : {},
    );
    allOk({ risk: ok(risk({ latest: run(results, { status: "partial" }) })) });
    stubFetch();
    renderAsset();
    await settled("E1");
    expect(level("0.0100").querySelector(".ruvor-range b")?.textContent).toBe("—");
    expect(phrase(level("0.0100"), "discordancia")).toBe(
      TEXTOS["risco.discordancia"](null, null, 0, 9, 100, null),
    );
  });
});

// ---------------------------------------------------------------- V-09

describe("V-09 — a ordem fixa e os não rejeitados, sem eleger", () => {
  it.each([
    ["na ordem da API", apiOrder()],
    ["embaralhados", shuffled(apiOrder())],
  ])("a tabela sai na MODEL_ORDER com os resultados %s", async (_caso, results) => {
    allOk({ risk: ok(risk({ latest: run(results) })) });
    stubFetch();
    renderAsset();
    await settled("E1");
    const order = [...table().querySelectorAll("tbody tr[data-model]")].map((tr) =>
      tr.getAttribute("data-model"),
    );
    expect(order).toEqual([...MODEL_ORDER]);
    // os valores não estão na ordem fixa: ordenar por perda daria outra ordem
    const byLoss = [...MODEL_ORDER].sort((a, b) => VAR95[a] - VAR95[b]);
    expect(byLoss).not.toEqual([...MODEL_ORDER]);
    // cada linha mostra os números do seu modelo
    for (const model of MODEL_ORDER) {
      expect(cells(model)[0].querySelector(".ruvor-loss")?.textContent).toBe(
        loss(VAR95[model]),
      );
    }
  });

  it("alguns adequados: a lista na ordem fixa, e a frase", async () => {
    const adequate = new Set<ModelName>(["caviar", "historical", "egarch"]);
    const results = shuffled(
      apiOrder((m, a) => ({ adequate: a === "0.0500" && adequate.has(m) })),
    );
    allOk({ risk: ok(risk({ latest: run(results) })) });
    stubFetch();
    renderAsset();
    await settled("E1");
    const items = [...level("0.0500").querySelectorAll(".ruvor-tag-list li")].map(
      (li) => li.textContent,
    );
    expect(items).toEqual([
      TEXTOS["risco.modelo.historical"],
      TEXTOS["risco.modelo.egarch"],
      TEXTOS["risco.modelo.caviar"],
    ]);
    expect(phrase(level("0.0500"), "naoRejeitados")).toBe(
      TEXTOS["risco.naoRejeitados"](3, 9, 9),
    );
    // no outro nível, nenhum entre os nove julgados: sem lista
    expect(level("0.0100").querySelector(".ruvor-tag-list")).toBeNull();
    expect(phrase(level("0.0100"), "naoRejeitados")).toBe(
      TEXTOS["risco.naoRejeitados"](0, 9, 9),
    );
  });

  it("nenhum adequado entre os julgados, com '7 de 9 julgados'; o nulo é 'não julgado', não reprovado", async () => {
    const failed = new Set<ModelName>(["gru", "caviar"]);
    const results = apiOrder((m, a) =>
      a === "0.0500" && failed.has(m)
        ? {
            var_latest: null,
            var_mean: null,
            adequate: null,
            kupiec_passed: null,
            error: "x",
          }
        : { adequate: false },
    );
    allOk({ risk: ok(risk({ latest: run(results, { status: "partial" }) })) });
    stubFetch();
    renderAsset();
    await settled("E1");
    const text = phrase(level("0.0500"), "naoRejeitados") ?? "";
    expect(text).toBe(TEXTOS["risco.naoRejeitados"](0, 7, 9));
    expect(text).toContain("7 de 9 julgados");
    expect(text).toContain("2 modelos não puderam ser julgados");

    const tags95 = MODEL_ORDER.map(
      (m) => cells(m)[0].querySelector(".ruvor-tag")?.textContent,
    );
    expect(tags95.filter((t) => t === TEXTOS["risco.tag.naoAdequado"])).toHaveLength(7);
    expect(tags95.filter((t) => t === TEXTOS["risco.tag.naoJulgado"])).toHaveLength(2);
  });

  it("nenhum julgado: a frase de que não foi possível julgar", async () => {
    const results = apiOrder((_m, a) =>
      a === "0.0100"
        ? {
            var_latest: null,
            var_mean: null,
            adequate: null,
            kupiec_passed: null,
            error: "x",
          }
        : {},
    );
    allOk({ risk: ok(risk({ latest: run(results, { status: "partial" }) })) });
    stubFetch();
    renderAsset();
    await settled("E1");
    expect(phrase(level("0.0100"), "naoRejeitados")).toBe(
      TEXTOS["risco.naoRejeitados"](0, 0, 9),
    );
  });
});

// ---------------------------------------------------------------- V-10

describe("V-10 — a tabela", () => {
  it("as barras numa escala só: o máximo das dezoito perdas", async () => {
    renderAsset();
    await settled("E1");
    const max = lossFromVar(EGARCH_99);
    for (const model of MODEL_ORDER) {
      const [c95, c99] = cells(model);
      const v99 = model === "egarch" ? EGARCH_99 : 1.5 * VAR95[model];
      for (const [cell, v] of [
        [c95, VAR95[model]],
        [c99, v99],
      ] as const) {
        const fill = cell.querySelector<HTMLElement>(".ruvor-bar__fill");
        // o jsdom normaliza "100.0%" para "100%": compara o número
        expect(fill?.style.width.endsWith("%")).toBe(true);
        expect(Number.parseFloat(fill?.style.width ?? "")).toBeCloseTo(
          (100 * lossFromVar(v)) / max,
          1,
        );
      }
    }
  });

  it("nenhum texto de Basileia na seção", async () => {
    renderAsset();
    await settled("E1");
    fireEvent.click(
      within(row("historical")).getByRole("button", {
        name: TEXTOS["risco.tabela.abrir"](TEXTOS["risco.modelo.historical"]),
      }),
    );
    expect(section().textContent).not.toMatch(/basel|basileia/i);
  });

  it("cada tag tem texto", async () => {
    renderAsset();
    await settled("E1");
    const tags = section().querySelectorAll(".ruvor-tag");
    expect(tags.length).toBeGreaterThan(18);
    for (const tag of tags) expect(tag.textContent?.trim()).not.toBe("");
  });

  it("abrir a linha mostra violações × esperadas e os três testes, com p-valor e se passou, nos dois níveis", async () => {
    renderAsset();
    await settled("E1");
    const toggle = within(row("garch_1_1")).getByRole("button", {
      name: TEXTOS["risco.tabela.abrir"](TEXTOS["risco.modelo.garch_1_1"]),
    });
    const detail = document.getElementById(
      toggle.getAttribute("aria-controls") as string,
    ) as HTMLElement;
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(detail.hidden).toBe(true);

    fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    expect(detail.hidden).toBe(false);

    for (const [alpha, v, e, cadaN] of [
      ["0.0500", "118", "112,1", 20],
      ["0.0100", "25", "22,4", 100],
    ] as const) {
      const part = detail.querySelector<HTMLElement>(
        `[data-alpha="${alpha}"]`,
      ) as HTMLElement;
      expect(part.textContent).toContain(TEXTOS[`risco.nivel.${alpha}`]);
      const viol = part.querySelector<HTMLElement>(
        '[data-test="violacoes"]',
      ) as HTMLElement;
      expect(viol.querySelector("dd")?.textContent).toBe(`${v} × ${e}`);
      expect(viol.querySelector(".ruvor-note")?.textContent).toBe(
        TEXTOS["risco.violacoes"](v, e, cadaN, true),
      );
      const test = (name: string) =>
        part.querySelector<HTMLElement>(`[data-test="${name}"]`) as HTMLElement;
      expect(test("kupiec").querySelector("dd")?.textContent).toBe(
        `0,581${TEXTOS["risco.teste.passou"]}`,
      );
      expect(test("kupiec").querySelector(".ruvor-note")?.textContent).toBe(
        TEXTOS["risco.kupiec"]("0,581", true),
      );
      expect(test("christoffersen").querySelector("dd")?.textContent).toBe(
        `< 0,001${TEXTOS["risco.teste.naoPassou"]}`,
      );
      expect(test("christoffersen").querySelector(".ruvor-note")?.textContent).toBe(
        TEXTOS["risco.christoffersen"]("< 0,001", false),
      );
      expect(test("dq").querySelector("dd")?.textContent).toBe(
        `0,082${TEXTOS["risco.teste.passou"]}`,
      );
      expect(test("dq").querySelector(".ruvor-note")?.textContent).toBe(
        TEXTOS["risco.dq"]("0,082", true),
      );
    }

    fireEvent.click(toggle);
    expect(detail.hidden).toBe(true);
  });

  it("o modelo que falhou num nível mostra o erro, não a frase das violações", async () => {
    const results = apiOrder((m, a) =>
      m === "lstm" && a === "0.0100"
        ? {
            var_latest: null,
            var_mean: null,
            violations: null,
            expected_violations: null,
            kupiec_passed: null,
            kupiec_p_value: null,
            christoffersen_passed: null,
            christoffersen_p_value: null,
            dq_passed: null,
            dq_p_value: null,
            adequate: null,
            error: "treino divergiu",
          }
        : {},
    );
    allOk({ risk: ok(risk({ latest: run(results, { status: "partial" }) })) });
    stubFetch();
    renderAsset();
    await settled("E1");
    const [, c99] = cells("lstm");
    expect(c99.querySelector(".ruvor-loss")?.textContent).toBe("—");
    expect(c99.querySelector(".ruvor-bar")).toBeNull();
    expect(c99.querySelector(".ruvor-tag")?.textContent).toBe(
      TEXTOS["risco.tag.naoJulgado"],
    );
    fireEvent.click(within(row("lstm")).getByRole("button"));
    const detail = row("lstm").nextElementSibling as HTMLElement;
    const part = detail.querySelector<HTMLElement>(
      '[data-alpha="0.0100"]',
    ) as HTMLElement;
    expect(part.querySelector('[data-phrase="erroModelo"]')?.textContent).toBe(
      TEXTOS["risco.erroModelo"]("treino divergiu"),
    );
    expect(part.querySelector('[data-test="violacoes"]')).toBeNull();
    // o outro nível segue com os testes
    expect(
      detail.querySelector('[data-alpha="0.0500"] [data-test="kupiec"]'),
    ).not.toBeNull();
  });
});

// ---------------------------------------------------------------- V-14 da seção

describe("V-14 — cada número do risco com a frase junto", () => {
  it("a perda, a discordância e os não rejeitados em cada nível; o veredito junto da tabela", async () => {
    renderAsset();
    await settled("E1");
    for (const [alpha, key] of [
      ["0.0500", "risco.perda95"],
      ["0.0100", "risco.perda99"],
    ] as const) {
      const panel = level(alpha);
      expect(panel.querySelector(".ruvor-range b")?.textContent).not.toBe("");
      expect(phrase(panel, "perda")).toBe(TEXTOS[key]);
      expect(phrase(panel, "discordancia")).not.toBe("");
      expect(phrase(panel, "naoRejeitados")).not.toBe("");
    }
    const tablePanel = table().closest("section") as HTMLElement;
    expect(tablePanel.querySelector('[data-phrase="veredito"]')?.textContent).toBe(
      TEXTOS["risco.veredito"],
    );
  });
});

// ---------------------------------------------------------------- a trilha e a proveniência

describe("RF-16 — a trilha na coluna lateral, e a proveniência no rodapé", () => {
  it("E1: a trilha no aside do casco, com o que entrou no cálculo", async () => {
    renderAsset();
    await settled("E1");
    const aside = await waitFor(() => {
      const found = rail();
      expect(found?.querySelector(".ruvor-trail")).not.toBeNull();
      return found as HTMLElement;
    });
    expect(within(aside).getByText(TEXTOS["risco.trilha.titulo"])).toBeDefined();
    expect(within(aside).getByText(TEXTOS["risco.trilha"])).toBeDefined();
    const value = (label: string) =>
      within(aside).getByText(label).closest("div")?.querySelector("dd")?.textContent;
    expect(value(TEXTOS["risco.trilha.asOf"])).toBe("25/09/2026");
    expect(value(TEXTOS["risco.trilha.firstPrice"])).toBe("22/09/2016");
    expect(value(TEXTOS["risco.trilha.priceCount"])).toBe("2.487");
    expect(value(TEXTOS["risco.trilha.test"])).toBe(
      TEXTOS["risco.trilha.pregoes"]("2.235"),
    );
    expect(value(TEXTOS["risco.trilha.engine"])).toBe("0.3.0");
    expect(value(TEXTOS["risco.trilha.seed"])).toBe("42");
    expect(value(TEXTOS["risco.trilha.calculatedAt"])).toBe("28/09/2026 às 19:30");
    expect(value(TEXTOS["risco.trilha.priceRun"])).toBe(
      TEXTOS["risco.trilha.coleta"]("Yahoo Finance", "28/09/2026 às 19:01"),
    );
    expect(value(TEXTOS["risco.trilha.status"])).toBe(TEXTOS["risco.trilha.status.ok"]);
    // a trilha fica fora da seção
    expect(section().contains(aside)).toBe(false);
  });

  it("partial: quantos modelos falharam", async () => {
    const results = apiOrder((m) =>
      m === "gru" || m === "lstm"
        ? { var_latest: null, adequate: null, kupiec_passed: null, error: "x" }
        : {},
    );
    allOk({ risk: ok(risk({ latest: run(results, { status: "partial" }) })) });
    stubFetch();
    renderAsset();
    await settled("E1");
    await waitFor(() =>
      expect(
        within(rail() as HTMLElement).getByText(
          TEXTOS["risco.trilha.status.partial"](2),
        ),
      ).toBeDefined(),
    );
  });

  it("o rodapé mostra o último pregão e o instante do cálculo", async () => {
    renderAsset();
    await settled("E1");
    await waitFor(() =>
      expect(
        footer().querySelector('[data-provenance="as-of-date"]')?.textContent,
      ).toBe(TEXTOS["rodape.ultimoPregao"]("25/09/2026")),
    );
    expect(
      footer().querySelector('[data-provenance="calculated-at"]')?.textContent,
    ).toBe(TEXTOS["rodape.calculadoEm"]("28/09/2026", "19:30"));
  });

  it("sem cálculo (E8): sem trilha e sem proveniência", async () => {
    allOk({ risk: ok(risk()), prices: ok(prices(0)) });
    stubFetch();
    renderAsset();
    await settled("E8");
    await waitFor(() => expect(rail()).toBeNull());
    expect(footer().querySelector("[data-provenance]")).toBeNull();
  });

  it("E3: a trilha, sem a tabela dos modelos, e sem proveniência", async () => {
    allOk({ risk: ok(risk({ latest: run([], { status: "failed" }) })) });
    stubFetch();
    renderAsset();
    await settled("E3");
    expect(within(section()).queryByRole("table")).toBeNull();
    expect(within(section()).getByText(TEXTOS["risco.estado.E3.titulo"])).toBeDefined();
    expect(within(section()).queryByRole("button", { name: /calcular/i })).toBeNull();
    await waitFor(() =>
      expect(
        within(rail() as HTMLElement).getByText(TEXTOS["risco.trilha.status.failed"]),
      ).toBeDefined(),
    );
    expect(footer().querySelector("[data-provenance]")).toBeNull();
  });
});

// ---------------------------------------------------------------- V-11 — os estados

type Case = {
  name: string;
  risk?: Reply | undefined;
  asset?: Reply | undefined;
  prices?: Reply | undefined;
  state: string;
  shows?: string[];
  /** O texto da região viva (V-01 do M1.6d); sem ele, a região está vazia. */
  live?: string;
};

const inactive: AssetDetail = { ...ASSET, status: "inactive" };

const CASES: Case[] = [
  { name: "1: latest ok, sem in_progress", state: "E1", live: "" },
  {
    name: "1: latest partial",
    risk: ok(risk({ latest: run(apiOrder(), { status: "partial" }) })),
    state: "E1",
  },
  {
    name: "1: latest ok com in_progress → E2",
    risk: ok(risk({ latest: run(apiOrder()), in_progress: inProgress(12) })),
    state: "E2",
    shows: [
      TEXTOS["risco.estado.recalculando"](12, 18),
      TEXTOS["risco.estado.recalculando.nota"],
    ],
    live: TEXTOS["risco.estado.recalculando"](12, 18),
  },
  {
    name: "2: latest failed",
    risk: ok(risk({ latest: run([], { status: "failed" }) })),
    state: "E3",
    shows: [TEXTOS["risco.estado.E3.titulo"], TEXTOS["risco.estado.E3"]],
  },
  {
    name: "2: latest failed com in_progress — o recálculo",
    risk: ok(
      risk({ latest: run([], { status: "failed" }), in_progress: inProgress(3) }),
    ),
    state: "E3",
    shows: [
      TEXTOS["risco.estado.recalculando"](3, 18),
      TEXTOS["risco.estado.recalculando.notaFalha"],
      TEXTOS["risco.estado.E3.titulo"],
    ],
    live: TEXTOS["risco.estado.recalculando"](3, 18),
  },
  {
    name: "3: in_progress sem latest",
    risk: ok(
      risk({ in_progress: inProgress(7), request: request({ status: "running" }) }),
    ),
    state: "E4",
    shows: [TEXTOS["risco.estado.E4"](7, 18), TEXTOS["risco.estado.E4.nota"]],
    live: TEXTOS["risco.estado.E4"](7, 18),
  },
  {
    name: "4: pedido queued",
    risk: ok(risk({ request: request({ status: "queued" }) })),
    state: "E5",
    shows: [TEXTOS["risco.estado.E5.fila"], TEXTOS["risco.estado.E5.fila.nota"]],
    live: TEXTOS["risco.estado.E5.fila"],
  },
  {
    name: "4: pedido running",
    risk: ok(risk({ request: request({ status: "running" }) })),
    state: "E5",
    shows: [
      TEXTOS["risco.estado.E5.coletando"],
      TEXTOS["risco.estado.E5.coletando.nota"],
    ],
    live: TEXTOS["risco.estado.E5.coletando"],
  },
  {
    name: "5: done com série curta",
    risk: ok(
      risk({
        request: request({
          status: "done",
          reason: "serie curta (312 pregoes, minimo 503)",
        }),
      }),
    ),
    state: "E6",
    shows: [
      TEXTOS["risco.estado.serieCurta.titulo"],
      traduzirMotivo("serie curta (312 pregoes, minimo 503)"),
    ],
  },
  {
    name: "6: failed",
    risk: ok(
      risk({ request: request({ status: "failed", reason: "falhou na coleta" }) }),
    ),
    state: "E7",
    shows: [TEXTOS["risco.estado.E7.titulo"], TEXTOS["motivos.falhouColeta"]],
  },
  {
    name: "6: expired",
    risk: ok(
      risk({ request: request({ status: "expired", reason: "expirado (30 min)" }) }),
    ),
    state: "E7",
    shows: [traduzirMotivo("expirado (30 min)")],
  },
  {
    name: "7: done 'calculado' com latest nulo — a reserva",
    risk: ok(risk({ request: request({ status: "done", reason: "calculado" }) })),
    state: "E8",
  },
  {
    name: "7a: identidade carregando",
    risk: ok(risk()),
    asset: undefined,
    state: "CARREGANDO",
  },
  {
    name: "7b: inativo com série curta → E9",
    risk: ok(risk()),
    asset: ok(inactive),
    prices: ok(prices(100)),
    state: "E9",
    shows: [TEXTOS["risco.estado.E9.titulo"], TEXTOS["risco.estado.E9"]],
  },
  {
    name: "identidade em erro segue adiante (série curta → E6b)",
    risk: ok(risk()),
    asset: fail(500),
    prices: ok(prices(40)),
    state: "E6b",
  },
  {
    name: "8: série carregando",
    risk: ok(risk()),
    prices: undefined,
    state: "CARREGANDO",
  },
  { name: "9: série em erro", risk: ok(risk()), prices: fail(500), state: "E8" },
  {
    name: "10: 502 pregões",
    risk: ok(risk()),
    prices: ok(prices(502)),
    state: "E6b",
    shows: [TEXTOS["motivos.serieCurta"]("502", "503")],
  },
  { name: "11: 503 pregões", risk: ok(risk()), prices: ok(prices(503)), state: "E8" },
  {
    name: "11: 0 pregões",
    risk: ok(risk()),
    prices: ok(prices(0)),
    state: "E8",
    shows: [TEXTOS["risco.estado.E8.titulo"], TEXTOS["risco.estado.E8"]],
  },
  { name: "o /risk carregando", risk: undefined, state: "RISCO_CARREGANDO" },
  { name: "o /risk em erro", risk: fail(500), state: "RISCO_ERRO" },
];

/** O botão do pedido, por estado: só o E7 e o E8 o têm. */
const BUTTON: Record<string, string | null> = {
  E7: TEXTOS["risco.pedido.deNovo"],
  E8: TEXTOS["risco.pedido.calcular"],
};

describe("V-11 — data-risk-state para cada linha da tabela de decisão", () => {
  it.each(CASES)("$name → $state", async (c) => {
    const over: Partial<Record<Route, Reply>> = {};
    if ("risk" in c) over.risk = c.risk;
    if ("asset" in c) over.asset = c.asset;
    if ("prices" in c) over.prices = c.prices;
    allOk(over);
    replies = { ...replies, ...over };
    stubFetch();
    renderAsset();
    await settled(c.state);
    // a seção fica no estado (nada mais chega)
    await act(async () => {});
    expect(riskState()).toBe(c.state);

    for (const text of c.shows ?? []) {
      expect(inBody(text)).toBeDefined();
    }
    const label = BUTTON[c.state] ?? null;
    const buttons = within(section())
      .queryAllByRole("button")
      .filter((b) => !b.classList.contains("ruvor-table__toggle"));
    if (label === null) {
      expect(buttons.map((b) => b.textContent)).not.toContain(
        TEXTOS["risco.pedido.calcular"],
      );
      expect(buttons.map((b) => b.textContent)).not.toContain(
        TEXTOS["risco.pedido.deNovo"],
      );
    } else {
      expect(within(section()).getByRole("button", { name: label })).toBeDefined();
    }
    if (c.state === "CARREGANDO" || c.state === "RISCO_CARREGANDO") {
      const status = within(section()).getByRole("status");
      expect(status.getAttribute("aria-busy")).toBe("true");
      expect(status.textContent).toBe(TEXTOS["risco.carregando"]);
      expect(section().querySelector(".ruvor-skeleton")).not.toBeNull();
    }
    if (c.state === "RISCO_ERRO") {
      expect(within(section()).getByRole("alert").textContent).toContain(
        TEXTOS["ativo.erroSecao"],
      );
    }

    // V-01 do M1.6d: uma região viva só, invisível, com o andamento e sem o corpo; o embrulho
    // do corpo não tem aria-live. Fora da tabela do RF-01, a região está vazia.
    const esperado = c.live ?? "";
    const vivas = section().querySelectorAll("[aria-live]");
    expect(vivas).toHaveLength(1);
    const viva = vivas[0];
    expect(viva.classList.contains("ruvor-sr-only")).toBe(true);
    expect(viva.querySelector("table, .ruvor-panel")).toBeNull();
    expect(viva.textContent).toBe(esperado);
  });

  it("E4 com a barra de progresso", async () => {
    allOk({ risk: ok(risk({ in_progress: inProgress(7) })) });
    stubFetch();
    renderAsset();
    await settled("E4");
    const bar = within(section()).getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("7");
    expect(bar.getAttribute("aria-valuemax")).toBe("18");
    expect(bar.querySelector<HTMLElement>(".ruvor-progress__fill")?.style.width).toBe(
      "38.9%",
    );
  });

  it("RISCO_ERRO: tentar de novo pede o /risk, e a seção sai do erro", async () => {
    allOk({ risk: fail(500) });
    stubFetch();
    renderAsset();
    await settled("RISCO_ERRO");
    replies.risk = ok(E1);
    fireEvent.click(
      within(section()).getByRole("button", { name: TEXTOS["ativo.tentarDeNovo"] }),
    );
    await settled("E1");
  });

  it("data-ready só quando a seção sai do carregando", async () => {
    allOk({ prices: undefined, risk: ok(risk()) });
    stubFetch();
    renderAsset();
    await settled("CARREGANDO");
    expect(document.querySelector("[data-ready]")).toBeNull();
    await act(async () => {
      for (const c of calls.filter((x) => x.route === "prices"))
        c.resolve(ok(prices(0)));
    });
    await settled("E8");
    expect(document.querySelector("[data-ready]")?.getAttribute("data-ready")).toBe(
      "true",
    );
  });
});

// ---------------------------------------------------------------- V-11 — o pedido

describe("V-11 — as respostas do POST (RF-19)", () => {
  function startE8(post?: Reply) {
    allOk({ risk: ok(risk()), prices: ok(prices(0)), post });
    stubFetch();
    renderAsset();
  }
  const calcular = () =>
    within(section()).getByRole("button", { name: TEXTOS["risco.pedido.calcular"] });

  it("enquanto não volta: aria-busy, desabilitado, e 'enviando'", async () => {
    startE8(undefined);
    await settled("E8");
    fireEvent.click(calcular());
    await waitFor(() => expect(calls.some((c) => c.route === "post")).toBe(true));
    const button = calcular();
    expect(button.getAttribute("aria-busy")).toBe("true");
    expect((button as HTMLButtonElement).disabled).toBe(true);
    expect(within(section()).getByRole("status").textContent).toBe(
      TEXTOS["risco.pedido.enviando"],
    );
    expect(calls.find((c) => c.route === "post")?.url).toBe(
      "/api/v1/assets/ITUB4/risk",
    );
  });

  it("202: a seção passa ao estado do corpo", async () => {
    startE8({ status: 202, body: risk({ request: request({ status: "queued" }) }) });
    await settled("E8");
    fireEvent.click(calcular());
    await settled("E5");
    expect(inBody(TEXTOS["risco.estado.E5.fila"])).toBeDefined();
  });

  it("409 asset_already_covered: o /risk do details, e o risco aparece", async () => {
    startE8(fail(409, "asset_already_covered", "Ativo ITUB4 já tem risco", E1));
    await settled("E8");
    fireEvent.click(calcular());
    await settled("E1");
    expect(within(section()).getByRole("table")).toBeDefined();
  });

  it("429 on_demand_queue_full: a frase, e o botão de volta", async () => {
    startE8(fail(429, "on_demand_queue_full", "A fila está cheia", { max: 3 }));
    await settled("E8");
    fireEvent.click(calcular());
    const alert = await within(section()).findByRole("alert");
    expect(alert.textContent).toBe(TEXTOS["risco.pedido.filaCheia"]);
    expect((calcular() as HTMLButtonElement).disabled).toBe(false);
    expect(calcular().hasAttribute("aria-busy")).toBe(false);
    expect(riskState()).toBe("E8");
  });

  it("422 asset_inactive: E9", async () => {
    startE8(fail(422, "asset_inactive", "Ativo ITUB4 está inativo."));
    await settled("E8");
    fireEvent.click(calcular());
    await settled("E9");
    expect(within(section()).getByText(TEXTOS["risco.estado.E9.titulo"])).toBeDefined();
  });

  it("outro erro: a mensagem da D-86 dentro da frase, e o botão de volta", async () => {
    startE8(fail(500, "internal_error", "Erro interno. Tente de novo mais tarde."));
    await settled("E8");
    fireEvent.click(calcular());
    const alert = await within(section()).findByRole("alert");
    expect(alert.textContent).toBe(
      TEXTOS["risco.pedido.erro"]("Erro interno. Tente de novo mais tarde."),
    );
    expect((calcular() as HTMLButtonElement).disabled).toBe(false);
  });

  it.each([
    ["network_error", "network" as const],
    ["unexpected_response", "html" as const],
  ])("%s: a frase fixa de sem resposta", async (_code, reply) => {
    startE8(reply);
    await settled("E8");
    fireEvent.click(calcular());
    const alert = await within(section()).findByRole("alert");
    expect(alert.textContent).toBe(TEXTOS["risco.pedido.semResposta"]);
  });

  it("E7: calcular de novo também pede, e recebe a fila cheia", async () => {
    allOk({
      risk: ok(
        risk({ request: request({ status: "failed", reason: "falhou na coleta" }) }),
      ),
      post: fail(429, "on_demand_queue_full", "cheia"),
    });
    stubFetch();
    renderAsset();
    await settled("E7");
    fireEvent.click(
      within(section()).getByRole("button", { name: TEXTOS["risco.pedido.deNovo"] }),
    );
    expect((await within(section()).findByRole("alert")).textContent).toBe(
      TEXTOS["risco.pedido.filaCheia"],
    );
  });

  it("o X-CSRFToken vai quando o cookie existe", async () => {
    // biome-ignore lint/suspicious/noDocumentCookie: o cliente lê o cookie de verdade.
    document.cookie = "csrftoken=tok123; path=/";
    startE8({ status: 202, body: risk({ request: request({ status: "queued" }) }) });
    await settled("E8");
    fireEvent.click(calcular());
    await settled("E5");
    expect(calls.find((c) => c.route === "post")?.headers["X-CSRFToken"]).toBe(
      "tok123",
    );
  });

  it("e não vai quando o cookie não existe", async () => {
    startE8({ status: 202, body: risk({ request: request({ status: "queued" }) }) });
    await settled("E8");
    fireEvent.click(calcular());
    await settled("E5");
    expect(calls.find((c) => c.route === "post")?.headers).not.toHaveProperty(
      "X-CSRFToken",
    );
  });
});
