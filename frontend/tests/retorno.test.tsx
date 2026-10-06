/**
 * A seção do retorno (M5.1, T12): RF-16 a RF-22 na tela.
 *
 * - a ordem: o risco, o laboratório (M2.4), o retorno e os Fundamentos;
 * - V-12 (a tela): cada estado do RF-16 com a frase dele; cada combinação do RF-17 — nenhum
 *   bate (a foto real do ITUB4), um bate, os dois, um com `error` —; o `error` distinto do "não
 *   bate"; o acerto sempre ao lado da parcela de alta; o PT nulo com a frase da direção
 *   constante; a previsão dentro da linha do modelo, depois do veredito e do histórico, com a
 *   referência "0,00%" ao lado, na classe aprovada e não na do veredito, sem seta nem cor; a nota
 *   "não mais informativa" em todo modelo que não bate; a previsão ausente, com a frase de estado,
 *   no inativo e com a data passada; nenhum pedido ao trocar o nível;
 * - V-14: o aviso aberto de R3 a R8, nos dois níveis, ausente em R1 e R2; as duas frases que ele
 *   tem de ter; a frase de "nenhum bate" com a das previsões;
 * - V-15: a prova por seção no avançado para cada chave da lista fechada (N = 7).
 *
 * "Hoje" é fixo em 04/10/2026 (só o `Date` é falso): a previsão para 05/10/2026 aparece. O
 * `fetch` é um duplo que responde pela rota; o uPlot, um duplo mínimo.
 */
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { routes } from "../src/App";
import type {
  AssetDetail,
  Lab,
  PriceRow,
  ReturnResult,
  ReturnRun,
  Returns,
  Risk,
} from "../src/api/types";
import { TEXTOS_AVANCADOS } from "../src/content/avancado";
import { TEXTOS } from "../src/content/textos";
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
  last_price: { date: "2026-10-02", close: "38.500000", adj_close: "38.500000" },
};

const RISK: Risk = {
  ticker: "ITUB4",
  covered: false,
  latest: null,
  in_progress: null,
  request: null,
};

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
  risk_engine_version: "0.5.0",
  pending: true,
  latest: null,
  last_failure: null,
};

/** O `ar_1` do ITUB4 na foto da fase A (`docs/mockups/M5.1/returns-ITUB4.js`). */
const AR1: ReturnResult = {
  model_name: "ar_1",
  hyperparameters: { lags: 1, window: "expanding", estimator: "ols", intercept: true },
  mse: "0.0003402168",
  mse_reference: "0.0003403580",
  r2_os: "0.0004148825",
  direction_days: 2217,
  hit_rate: "0.5056382499",
  up_share: "0.5105999098",
  forecast_up_share: "0.7027514659",
  dm_statistic: "0.1049938768",
  dm_p_value: "0.4581903337",
  cw_statistic: "1.6533993320",
  cw_p_value: "0.0491248094",
  pt_statistic: "0.1381045634",
  pt_p_value: "0.4450788896",
  beats_reference: false,
  direction_skill: false,
  next_forecast: "-0.0005241821",
  next_forecast_date: "2026-10-05",
  error: "",
};

/** O `historical_mean` do ITUB4 na foto: o PT nulo, com previsão de alta em todos os dias. */
const MEAN: ReturnResult = {
  model_name: "historical_mean",
  hyperparameters: { window: "expanding", refit_frequency_days: 252 },
  mse: "0.0003404067",
  mse_reference: "0.0003403580",
  r2_os: "-0.0001432235",
  direction_days: 2217,
  hit_rate: "0.5105999098",
  up_share: "0.5105999098",
  forecast_up_share: "1.0000000000",
  dm_statistic: "-0.1009518596",
  dm_p_value: "0.5402056623",
  cw_statistic: "0.7558432239",
  cw_p_value: "0.2248715990",
  pt_statistic: null,
  pt_p_value: null,
  beats_reference: false,
  direction_skill: null,
  next_forecast: "0.0005194783",
  next_forecast_date: "2026-10-05",
  error: "",
};

const FAILED_AR1: ReturnResult = {
  ...AR1,
  mse: null,
  mse_reference: null,
  r2_os: null,
  direction_days: null,
  hit_rate: null,
  up_share: null,
  forecast_up_share: null,
  dm_statistic: null,
  dm_p_value: null,
  cw_statistic: null,
  cw_p_value: null,
  pt_statistic: null,
  pt_p_value: null,
  beats_reference: null,
  direction_skill: null,
  next_forecast: null,
  next_forecast_date: null,
  error: "matriz singular no trecho 4",
};

function run(results: ReturnResult[]): ReturnRun {
  return {
    calculated_at: "2026-10-04T10:05:12.724649-03:00",
    engine_version: "0.5.0",
    as_of_date: "2026-10-02",
    first_price_date: "2016-09-22",
    price_count: 2499,
    train_count: 252,
    test_count: 2246,
    train_window_days: 252,
    price_run: {
      id: 20,
      source: "yahoo-chart",
      started_at: "2026-10-02T21:44:53.709597-03:00",
      finished_at: "2026-10-02T21:44:56.619518-03:00",
    },
    results,
  };
}

const returns = (results: ReturnResult[] | null): Returns => ({
  ticker: "ITUB4",
  latest: results === null ? null : run(results),
});

const ITUB4 = returns([AR1, MEAN]);
const ONE_BEATS = returns([
  { ...AR1, dm_p_value: "0.0310000000", beats_reference: true },
  MEAN,
]);
const TWO_BEAT = returns([
  { ...AR1, dm_p_value: "0.0310000000", beats_reference: true },
  { ...MEAN, r2_os: "0.0001000000", dm_p_value: "0.0420000000", beats_reference: true },
]);
const WITH_ERROR = returns([FAILED_AR1, MEAN]);

function priceRows(n: number): PriceRow[] {
  return Array.from({ length: n }, (_, i) => ({
    date: `2016-01-${String((i % 28) + 1).padStart(2, "0")}`,
    open: "30.000000",
    high: "30.000000",
    low: "30.000000",
    close: "30.000000",
    adj_close: "30.000000",
    volume: 1000,
  }));
}

// ---------------------------------------------------------------- o duplo do fetch

type Reply = { status: number; body: unknown } | null;
const ok = (body: unknown): Reply => ({ status: 200, body });
const fail = (status: number): Reply => ({
  status,
  body: { error: { code: "internal_error", message: "falhou", details: {} } },
});

let calls: string[] = [];
let assetReply: Reply;
let pricesReply: Reply;
let returnsReply: Reply;

function bodyOf(url: string): Reply {
  if (url === "/api/v1/auth/me")
    return {
      status: 401,
      body: { error: { code: "not_authenticated", message: "falhou", details: {} } },
    };
  const m = /^\/api\/v1\/assets\/ITUB4(?:\/(\w+))?(\?.*)?$/.exec(url);
  if (m === null) throw new Error(`pedido inesperado: ${url}`);
  switch (m[1]) {
    case undefined:
      return assetReply;
    case "prices":
      return pricesReply;
    case "events":
      return ok({ ticker: "ITUB4", results: [] });
    case "metrics":
      return ok({ ticker: "ITUB4", metric: null });
    case "risk":
      return ok(RISK);
    case "fundamentals":
      return ok({ ticker: "ITUB4", indicator: null, peers: null });
    case "lab":
      return ok(LAB);
    case "returns":
      return returnsReply;
    case "disclosures":
      return ok({
        ticker: "ITUB4",
        company: { code_cvm: "19348", name: "ITAU UNIBANCO HOLDING S.A." },
        count: 0,
        limit: 10,
        offset: 0,
        results: [],
      });
    default:
      throw new Error(`pedido inesperado: ${url}`);
  }
}

function stubFetch(): void {
  calls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url: string) =>
        new Promise<Response>((resolve) => {
          calls.push(url);
          const reply = bodyOf(url);
          if (reply === null) return; // fica pendente
          resolve({
            ok: reply.status >= 200 && reply.status < 300,
            status: reply.status,
            json: async () => structuredClone(reply.body),
          } as unknown as Response);
        }),
    ),
  );
}

function renderAsset() {
  const router = createMemoryRouter(routes, {
    initialEntries: ["/ativos/ITUB4/retorno"],
  });
  render(<RouterProvider router={router} />);
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 9, 4, 12, 0, 0));
  assetReply = ok(ASSET);
  pricesReply = ok({ ticker: "ITUB4", from: null, to: null, results: priceRows(2499) });
  returnsReply = ok(ITUB4);
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  limparNivel();
});

// ---------------------------------------------------------------- as partes

const section = () =>
  document.querySelector<HTMLElement>('[data-section="returns"]') as HTMLElement;
const state = () => section().getAttribute("data-returns-state");
const text = () => section().textContent ?? "";
const has = (t: string) => text().includes(t);
const model = (name: string) =>
  section().querySelector<HTMLElement>(
    `.ruvor-returns-models [data-model="${name}"]`,
  ) as HTMLElement;
const aviso = () => section().querySelector('[data-aviso="retorno"]');
const follows = (a: Node, b: Node) =>
  Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);

async function settled(expected: string): Promise<void> {
  await waitFor(() => expect(section()).not.toBeNull());
  await waitFor(() => expect(state()).toBe(expected));
}

function openAll(): void {
  for (const toggle of section().querySelectorAll<HTMLElement>(
    ".ruvor-collapsible__toggle[aria-expanded='false']",
  )) {
    fireEvent.click(toggle);
  }
}

function readingButton(key: "casco.leitura.iniciante" | "casco.leitura.avancada") {
  return screen.getByRole("button", { name: TEXTOS[key] });
}

// ---------------------------------------------------------------- a ordem

describe("a ordem das seções", () => {
  it("a aba do retorno: só a seção dele, sem o risco, o laboratório nem os Fundamentos", async () => {
    renderAsset();
    await settled("R3");
    expect(section()).not.toBeNull();
    expect(document.querySelector("[data-risk-state]")).toBeNull();
    expect(document.querySelector('[data-section="lab"]')).toBeNull();
    expect(document.querySelector('[data-section="fundamentals"]')).toBeNull();
    const current = document.querySelector('.ruvor-tabs [aria-current="page"]');
    expect(current?.textContent).toBe(TEXTOS["ativo.aba.retorno"]);
  });
});

// ---------------------------------------------------------------- os estados

describe("V-12 — cada estado com a frase dele", () => {
  it("R1: o esqueleto e a frase para leitor de tela, sem o aviso", async () => {
    returnsReply = null;
    stubFetch();
    renderAsset();
    await settled("R1");
    expect(has(TEXTOS["retorno.carregando"])).toBe(true);
    expect(section().querySelector("[aria-busy='true']")).not.toBeNull();
    expect(aviso()).toBeNull();
  });

  it("R2: a mensagem e o tentar de novo, que pede só o /returns, sem o aviso", async () => {
    returnsReply = fail(500);
    stubFetch();
    renderAsset();
    await settled("R2");
    expect(aviso()).toBeNull();
    const before = calls.length;
    await act(async () =>
      fireEvent.click(section().querySelector(".ruvor-btn") as HTMLElement),
    );
    expect(calls.slice(before)).toEqual(["/api/v1/assets/ITUB4/returns"]);
  });

  it.each([
    [
      "R4",
      () => {
        assetReply = ok({ ...ASSET, status: "inactive" });
        returnsReply = ok(returns(null));
      },
      "retorno.estado.inativo.titulo",
      "retorno.estado.inativo",
    ],
    [
      "R5",
      () => {
        pricesReply = fail(500);
        returnsReply = ok(returns(null));
      },
      "retorno.estado.semSerie.titulo",
      "retorno.estado.semSerie",
    ],
    [
      "R6",
      () => {
        pricesReply = ok({ ticker: "ITUB4", from: null, to: null, results: [] });
        returnsReply = ok(returns(null));
      },
      "retorno.estado.naoCoberto.titulo",
      "retorno.estado.naoCoberto",
    ],
    [
      "R8",
      () => {
        returnsReply = ok(returns(null));
      },
      "retorno.estado.naoCalculado.titulo",
      "retorno.estado.naoCalculado",
    ],
  ] as const)("%s: o título, a frase e o aviso", async (st, setup, title, phrase) => {
    setup();
    stubFetch();
    renderAsset();
    await settled(st);
    expect(has(TEXTOS[title])).toBe(true);
    expect(has(TEXTOS[phrase])).toBe(true);
    expect(aviso()).not.toBeNull();
  });

  it("R5: o tentar de novo pede só o /prices", async () => {
    pricesReply = fail(500);
    returnsReply = ok(returns(null));
    stubFetch();
    renderAsset();
    await settled("R5");
    const before = calls.length;
    await act(async () =>
      fireEvent.click(
        section().querySelector(".ruvor-state .ruvor-btn") as HTMLElement,
      ),
    );
    expect(calls.slice(before)).toEqual(["/api/v1/assets/ITUB4/prices"]);
  });

  it("R7: a série curta, com a contagem e o piso", async () => {
    pricesReply = ok({
      ticker: "ITUB4",
      from: null,
      to: null,
      results: priceRows(312),
    });
    returnsReply = ok(returns(null));
    stubFetch();
    renderAsset();
    await settled("R7");
    expect(has(TEXTOS["retorno.estado.serieCurta.titulo"])).toBe(true);
    expect(has(TEXTOS["retorno.estado.serieCurta"]("312", "503"))).toBe(true);
    expect(aviso()).not.toBeNull();
  });
});

// ---------------------------------------------------------------- as combinações (RF-17)

describe("V-12 — as combinações do RF-17", () => {
  it("nenhum bate (a foto real do ITUB4): as duas tags 'não bate' e a frase das previsões", async () => {
    renderAsset();
    await settled("R3");
    for (const name of ["ar_1", "historical_mean"]) {
      const tag = model(name).querySelector("[data-verdict]") as HTMLElement;
      expect(tag.getAttribute("data-verdict")).toBe("not_beats");
      expect(tag.textContent).toBe(TEXTOS["retorno.tag.naoBate"]);
      expect(tag.className).toContain("ruvor-tag--neutral");
    }
    const verdict = section().querySelector('[data-phrase="veredito"]') as HTMLElement;
    expect(verdict.textContent).toContain(
      "as previsões abaixo não são mais informativas",
    );
  });

  it("um bate: a tag --evidence, nunca a --validated", async () => {
    returnsReply = ok(ONE_BEATS);
    stubFetch();
    renderAsset();
    await settled("R3");
    const tag = model("ar_1").querySelector("[data-verdict]") as HTMLElement;
    expect(tag.getAttribute("data-verdict")).toBe("beats");
    expect(tag.textContent).toBe(TEXTOS["retorno.tag.bate"]);
    expect(tag.className).toContain("ruvor-tag--evidence");
    expect(section().querySelector(".ruvor-tag--validated")).toBeNull();
    const verdict = section().querySelector('[data-phrase="veredito"]') as HTMLElement;
    expect(verdict.textContent).toBe(
      TEXTOS["retorno.veredito"](
        "ITUB4",
        "2.246",
        "02/10/2026",
        [["AR(1)", "0,04%"]],
        ["Média histórica"],
        0,
      ),
    );
  });

  it("os dois batem", async () => {
    returnsReply = ok(TWO_BEAT);
    stubFetch();
    renderAsset();
    await settled("R3");
    expect(section().querySelectorAll('[data-verdict="beats"]')).toHaveLength(2);
    expect(
      (section().querySelector('[data-phrase="veredito"]') as HTMLElement).textContent,
    ).toContain("Os dois modelos erraram menos");
  });

  it("um com error: 'não deu para calcular', distinto de 'não bate', sem números e sem previsão", async () => {
    returnsReply = ok(WITH_ERROR);
    stubFetch();
    renderAsset();
    await settled("R3");
    const failedBlock = model("ar_1");
    expect(failedBlock.getAttribute("data-error")).toBe("true");
    const tag = failedBlock.querySelector("[data-verdict]") as HTMLElement;
    expect(tag.getAttribute("data-verdict")).toBe("error");
    expect(tag.textContent).toBe(TEXTOS["retorno.tag.erro"]);
    expect(tag.textContent).not.toBe(TEXTOS["retorno.tag.naoBate"]);
    expect(failedBlock.querySelector(".ruvor-tests")).toBeNull();
    expect(failedBlock.querySelector("[data-forecast]")).toBeNull();
    expect(failedBlock.textContent).toContain(
      TEXTOS["retorno.erroModelo"]("matriz singular no trecho 4"),
    );
    expect(
      (section().querySelector('[data-phrase="veredito"]') as HTMLElement).textContent,
    ).toContain("O cálculo de um dos modelos falhou");
  });

  it("o acerto sempre ao lado da parcela de alta", async () => {
    renderAsset();
    await settled("R3");
    expect(model("ar_1").textContent).toContain(
      TEXTOS["retorno.acerto.valor"]("50,6%", "51,1%"),
    );
    expect(model("historical_mean").textContent).toContain(
      TEXTOS["retorno.acerto.valor"]("51,1%", "51,1%"),
    );
  });

  it("o PT nulo: 'sem teste' e a frase da direção constante, nos detalhes", async () => {
    renderAsset();
    await settled("R3");
    openAll();
    expect(has(TEXTOS["retorno.semPt"])).toBe(true);
    expect(has(TEXTOS["retorno.pt"](null, true))).toBe(true);
  });
});

// ---------------------------------------------------------------- a previsão (RF-18)

describe("V-12 — a previsão do próximo pregão", () => {
  it("a identidade carregando, com latest: a linha sem a previsão e sem frase de estado", async () => {
    assetReply = null;
    stubFetch();
    renderAsset();
    await settled("R3");
    expect(section().querySelector("[data-forecast]")).toBeNull();
    expect(section().querySelector('[data-value="forecast"]')).toBeNull();
    expect(model("ar_1").querySelector(".ruvor-tests")).not.toBeNull();
  });

  it("o p do DM nulo (variância nula) sai como '—', nunca como número", async () => {
    returnsReply = ok(
      returns([{ ...AR1, dm_statistic: null, dm_p_value: null }, MEAN]),
    );
    stubFetch();
    renderAsset();
    await settled("R3");
    const dm = [...model("ar_1").querySelectorAll(".ruvor-test")][2] as HTMLElement;
    expect(dm.querySelector(".ruvor-num")?.textContent).toBe("—");
  });

  it("nenhum bate: a nota 'não mais informativa' nos dois modelos", async () => {
    renderAsset();
    await settled("R3");
    for (const name of ["ar_1", "historical_mean"]) {
      expect(
        (model(name).querySelector('[data-phrase="previsao"]') as HTMLElement)
          .textContent,
      ).toContain("não é mais informativo que supor retorno zero");
    }
  });

  it("dentro da linha do modelo, depois do veredito e do histórico, com a referência ao lado", async () => {
    renderAsset();
    await settled("R3");
    for (const name of ["ar_1", "historical_mean"]) {
      const block = model(name);
      const tag = block.querySelector("[data-verdict]") as HTMLElement;
      const tests = block.querySelector(".ruvor-tests") as HTMLElement;
      const forecast = block.querySelector('[data-forecast="show"]') as HTMLElement;
      expect(forecast).not.toBeNull();
      expect(follows(tag, tests)).toBe(true);
      expect(follows(tests, forecast)).toBe(true);
      const line = forecast.querySelector(
        ".ruvor-returns-forecast__line",
      ) as HTMLElement;
      expect(line.textContent).toContain(TEXTOS["retorno.previsao.referencia"]);
      expect(line.textContent).toContain(
        TEXTOS["retorno.previsao.rotulo"]("05/10/2026"),
      );
      // sem seta nem cor de direção: nenhum ícone, nenhuma tag na linha
      expect(forecast.querySelector("svg")).toBeNull();
      expect(forecast.querySelector(".ruvor-tag")).toBeNull();
      expect(forecast.closest(".ruvor-tag")).toBeNull();
    }
    expect(
      (model("ar_1").querySelector('[data-value="forecast"]') as HTMLElement)
        .textContent,
    ).toBe("−0,05%");
    expect(
      (model("historical_mean").querySelector('[data-value="forecast"]') as HTMLElement)
        .textContent,
    ).toBe("+0,05%");
  });

  it("a previsão não sai no título da seção nem na frase do veredito", async () => {
    renderAsset();
    await settled("R3");
    const head = section().querySelector(".ruvor-section-head") as HTMLElement;
    const verdict = section().querySelector('[data-phrase="veredito"]') as HTMLElement;
    for (const node of [head, verdict]) {
      expect(node.textContent).not.toContain("−0,05%");
      expect(node.textContent).not.toContain("+0,05%");
    }
    expect(section().querySelectorAll('[data-value="forecast"]')).toHaveLength(2);
  });

  it("a nota 'não mais informativa' em todo modelo que não bate; no que bate, a outra", async () => {
    returnsReply = ok(ONE_BEATS);
    stubFetch();
    renderAsset();
    await settled("R3");
    const noteOf = (name: string) =>
      (model(name).querySelector('[data-phrase="previsao"]') as HTMLElement)
        .textContent;
    expect(noteOf("historical_mean")).toBe(
      TEXTOS["retorno.previsao"]("+0,05%", "05/10/2026", false),
    );
    expect(noteOf("ar_1")).toBe(
      TEXTOS["retorno.previsao"]("−0,05%", "05/10/2026", true),
    );
  });

  it("o ativo inativo: a frase, sem o número", async () => {
    assetReply = ok({ ...ASSET, status: "inactive" });
    stubFetch();
    renderAsset();
    await settled("R3");
    expect(section().querySelectorAll('[data-forecast="inactive"]')).toHaveLength(2);
    expect(section().querySelector('[data-value="forecast"]')).toBeNull();
    expect(has(TEXTOS["retorno.previsao.inativo"])).toBe(true);
  });

  it("a data já passou: a frase com a data, sem o número", async () => {
    returnsReply = ok(
      returns([
        { ...AR1, next_forecast_date: "2026-09-28" },
        { ...MEAN, next_forecast_date: "2026-09-28" },
      ]),
    );
    stubFetch();
    renderAsset();
    await settled("R3");
    expect(section().querySelectorAll('[data-forecast="past"]')).toHaveLength(2);
    expect(section().querySelector('[data-value="forecast"]')).toBeNull();
    expect(has(TEXTOS["retorno.previsao.passada"]("28/09/2026"))).toBe(true);
  });
});

// ---------------------------------------------------------------- o aviso (RF-19)

describe("V-14 — o aviso", () => {
  it("tem as duas frases que o portão exige", () => {
    expect(TEXTOS["retorno.aviso"]).toMatch(/não é recomendação de investimento/i);
    expect(TEXTOS["retorno.aviso"]).toContain("não uma expectativa nem uma indicação");
  });

  it.each(["beginner", "advanced"] as const)(
    "aberto em R3 na leitura %s, fora de recolhido",
    async (reading) => {
      comNivel(reading);
      renderAsset();
      await settled("R3");
      const node = aviso() as HTMLElement;
      expect(node.textContent).toContain(TEXTOS["retorno.aviso"]);
      expect(node.closest(".ruvor-collapsible")).toBeNull();
    },
  );

  it.each(["beginner", "advanced"] as const)(
    "aberto em R6 na leitura %s",
    async (reading) => {
      comNivel(reading);
      pricesReply = ok({ ticker: "ITUB4", from: null, to: null, results: [] });
      returnsReply = ok(returns(null));
      stubFetch();
      renderAsset();
      await settled("R6");
      expect(aviso()).not.toBeNull();
    },
  );
});

// ---------------------------------------------------------------- as duas leituras (V-15)

/** Cada chave da lista fechada com os argumentos que a tela usa para a foto do ITUB4. */
function closedKeys(): Array<[keyof typeof TEXTOS_AVANCADOS, unknown[]]> {
  return [
    [
      "retorno.veredito",
      ["ITUB4", "2.246", "02/10/2026", [], ["AR(1)", "Média histórica"], 0],
    ],
    ["retorno.r2_os", ["0,04%", true]],
    ["retorno.acerto", ["50,6%", "51,1%"]],
    ["retorno.dm", ["0,458", false]],
    ["retorno.cw", ["0,049"]],
    ["retorno.pt", ["0,445", null]],
    ["retorno.previsao", ["−0,05%", "05/10/2026", false]],
  ];
}

function phraseOf(registro: object, key: string, args: unknown[]): string {
  const v = (registro as Record<string, unknown>)[key];
  return typeof v === "function"
    ? (v as (...a: unknown[]) => string)(...args)
    : String(v);
}

describe("V-15 — as duas leituras", () => {
  it("a lista cobre as sete chaves, todas com avançada", () => {
    expect(new Set(closedKeys().map(([k]) => k)).size).toBe(7);
    for (const [key] of closedKeys()) {
      expect(Object.hasOwn(TEXTOS_AVANCADOS, key), key).toBe(true);
    }
  });

  it("a prova por seção no avançado: cada chave na avançada, nunca na iniciante", async () => {
    comNivel("advanced");
    renderAsset();
    await settled("R3");
    const ausentes: string[] = [];
    const presentes: string[] = [];
    for (const [key, args] of closedKeys()) {
      if (!has(phraseOf(TEXTOS_AVANCADOS, key, args))) ausentes.push(key);
      if (has(phraseOf(TEXTOS, key, args))) presentes.push(key);
    }
    expect(ausentes, "avançada ausente").toEqual([]);
    expect(presentes, "iniciante presente").toEqual([]);
  });

  it("na iniciante, abertos os recolhidos: as iniciantes, e nenhuma avançada", async () => {
    comNivel("beginner");
    renderAsset();
    await settled("R3");
    openAll();
    const ausentes: string[] = [];
    const presentes: string[] = [];
    for (const [key, args] of closedKeys()) {
      if (!has(phraseOf(TEXTOS, key, args))) ausentes.push(key);
      if (has(phraseOf(TEXTOS_AVANCADOS, key, args))) presentes.push(key);
    }
    expect(ausentes, "iniciante ausente").toEqual([]);
    expect(presentes, "avançada presente").toEqual([]);
  });

  it("na iniciante, os detalhes e a trilha recolhidos; na avançada, abertos", async () => {
    comNivel("beginner");
    renderAsset();
    await settled("R3");
    for (const name of ["returns-details", "returns-trail"]) {
      expect(
        section()
          .querySelector(`[data-collapsible="${name}"]`)
          ?.getAttribute("data-open"),
      ).toBe("false");
    }
    await act(async () => fireEvent.click(readingButton("casco.leitura.avancada")));
    for (const name of ["returns-details", "returns-trail"]) {
      expect(
        section()
          .querySelector(`[data-collapsible="${name}"]`)
          ?.getAttribute("data-open"),
      ).toBe("true");
    }
    expect(section().querySelector(".ruvor-trail")).not.toBeNull();
  });

  it("trocar o nível não pede nada à API", async () => {
    comNivel("beginner");
    renderAsset();
    await settled("R3");
    const before = calls.length;
    await act(async () => fireEvent.click(readingButton("casco.leitura.avancada")));
    expect(has(phraseOf(TEXTOS_AVANCADOS, "retorno.cw", ["0,049"]))).toBe(true);
    await act(async () => fireEvent.click(readingButton("casco.leitura.iniciante")));
    expect(calls.length).toBe(before);
  });
});
