/**
 * A seção do laboratório (M2.4, T12): RF-13 a RF-17 na tela.
 *
 * - a ordem: a seção de risco, o laboratório, os Fundamentos (RF-13);
 * - V-11 (a tela): cada estado do RF-14 com a frase dele; a grade em `MODEL_ORDER` com a
 *   resposta embaralhada; o veredito com texto, não só cor; o ano não julgado com rótulo
 *   próprio; o modelo com erro com `risco.erroModelo`; a grade de 99% sem veredito por ano; o
 *   "k de N" só a 95%; cada nota do estado pronto e nunca duas; a tabela com cabeçalho de linha
 *   e de coluna; nenhum pedido ao trocar o nível;
 * - V-12: a prova por seção no avançado para cada chave da lista fechada (N = 9) — a avançada
 *   presente e a iniciante ausente, e o contrário na iniciante —; a diferença honesta nas duas
 *   leituras; a trilha e os p-valores recolhidos na iniciante e abertos na avançada.
 *
 * O `fetch` é um duplo que responde pela rota; o uPlot, um duplo mínimo.
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
  type Lab,
  type LabResult,
  type LabRun,
  type LabYear,
  MODEL_ORDER,
  type ModelName,
  type Risk,
} from "../src/api/types";
import { TEXTOS_AVANCADOS } from "../src/content/avancado";
import { TEXTOS } from "../src/content/textos";
import { formatDate, formatDecimal, formatInteger } from "../src/format/numbers";
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

type Alpha = "0.0500" | "0.0100";
/** Os três trechos: dois cheios e o último curto, abaixo do piso de 126 (não julgado). */
const SPANS = [
  ["2017-09-26", "2018-09-24", 252],
  ["2018-09-25", "2019-10-02", 252],
  ["2019-10-03", "2020-03-20", 110],
] as const;

function years(model: number, alpha: Alpha): LabYear[] {
  const a = Number(alpha);
  return SPANS.map(([start, end, n], index) => {
    const judged = alpha === "0.0500" && n >= 126;
    return {
      index,
      start_date: start,
      end_date: end,
      test_count: n,
      violations: alpha === "0.0500" ? 10 + model + index : 1 + ((model + index) % 3),
      expected_violations: (n * a).toFixed(6),
      kupiec_passed: judged ? true : null,
      kupiec_p_value: judged ? "0.4000000000" : null,
      christoffersen_passed: judged ? (model + index) % 2 === 0 : null,
      christoffersen_p_value: judged ? "0.0300000000" : null,
      adequate: judged ? (model + index) % 2 === 0 : null,
    };
  });
}

function result(model: ModelName, alpha: Alpha): LabResult {
  const i = MODEL_ORDER.indexOf(model);
  const ys = years(i, alpha);
  const testCount = ys.reduce((s, y) => s + y.test_count, 0);
  const kupiec = i % 3 !== 0;
  return {
    model_name: model,
    model_category: i < 3 ? "traditional" : i < 5 ? "garch" : "ml",
    alpha,
    test_count: testCount,
    violations: ys.reduce((s, y) => s + y.violations, 0),
    expected_violations: (testCount * Number(alpha)).toFixed(6),
    kupiec_passed: kupiec,
    kupiec_p_value: kupiec ? "0.6000000000" : "0.0004000000",
    christoffersen_passed: true,
    christoffersen_p_value: "0.5000000000",
    dq_passed: false,
    dq_p_value: "0.0010000000",
    adequate: kupiec,
    error: "",
    reused_snapshots: i >= 5 ? 3 : null,
    trained_snapshots: i >= 5 ? 0 : null,
    years: ys,
  };
}

/** Os 18 resultados fora da ordem fixa: o inverso, e os níveis trocados. */
function shuffled(): LabResult[] {
  return [...MODEL_ORDER]
    .reverse()
    .flatMap((m) => [result(m, "0.0100"), result(m, "0.0500")]);
}

function run(over: Partial<LabRun> = {}): LabRun {
  return {
    id: 3,
    calculated_at: "2026-10-04T04:43:02-03:00",
    finished_at: "2026-10-04T04:43:07-03:00",
    status: "ok",
    origin: "command",
    engine_version: "0.4.0",
    seed: 42,
    train_window_days: 252,
    first_price_date: "2016-09-22",
    decade_end: "2026-09-22",
    as_of_date: "2026-09-22",
    price_count: 868,
    train_count: 252,
    test_count: 614,
    year_count: 3,
    price_run: {
      id: 18,
      source: "yahoo-chart",
      started_at: "2026-10-01T22:26:25-03:00",
      finished_at: "2026-10-01T22:26:28-03:00",
    },
    price_fingerprint:
      "d2a0cec292f30a823ef94e74ce31da3d72a992fb349b48ccd54e8f4fb9710a44",
    results: shuffled(),
    ...over,
  };
}

const COMPLETE = {
  first_price_date: "2016-09-22",
  end_date: "2026-09-22",
  last_price_date: "2026-10-02",
  complete: true,
  sessions: 2491,
};

function lab(over: Partial<Lab> = {}): Lab {
  return {
    ticker: "ITUB4",
    active: true,
    decade: COMPLETE,
    risk_engine_version: "0.4.0",
    pending: false,
    latest: run(),
    last_failure: null,
    ...over,
  };
}

const FAILURE = {
  id: 9,
  calculated_at: "2026-10-05T19:42:10-03:00",
  engine_version: "0.4.0",
  error: "série mudou durante o cálculo",
};

/** O `partial` do mesmo motor: o GRU a 99% com erro. */
function partial(): LabRun {
  const results = shuffled().map((r) =>
    r.model_name === "gru" && r.alpha === "0.0100"
      ? {
          ...r,
          test_count: null,
          violations: null,
          expected_violations: null,
          kupiec_passed: null,
          kupiec_p_value: null,
          christoffersen_passed: null,
          christoffersen_p_value: null,
          dq_passed: null,
          dq_p_value: null,
          adequate: null,
          error: "o treino não convergiu",
          reused_snapshots: null,
          trained_snapshots: null,
          years: [],
        }
      : r,
  );
  return run({ status: "partial", results });
}

// ---------------------------------------------------------------- o duplo do fetch

type Reply = { status: number; body: unknown } | null;
let labReply: Reply = { status: 200, body: lab() };
let calls: string[] = [];

const ok = (body: unknown): Reply => ({ status: 200, body });

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
      return ok(ASSET);
    case "prices":
      return ok({ ticker: "ITUB4", from: null, to: null, results: [] });
    case "events":
      return ok({ ticker: "ITUB4", results: [] });
    case "metrics":
      return ok({ ticker: "ITUB4", metric: null });
    case "risk":
      return ok(RISK);
    case "fundamentals":
      return ok({ ticker: "ITUB4", indicator: null, peers: null });
    case "disclosures":
      return ok({
        ticker: "ITUB4",
        company: { code_cvm: "19348", name: "ITAU UNIBANCO HOLDING S.A." },
        count: 0,
        limit: 10,
        offset: 0,
        results: [],
      });
    case "lab":
      return labReply;
    case "returns":
      return ok({ ticker: "ITUB4", latest: null });
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
    initialEntries: ["/ativos/ITUB4/laboratorio"],
  });
  render(<RouterProvider router={router} />);
}

beforeEach(() => {
  labReply = ok(lab());
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  limparNivel();
});

// ---------------------------------------------------------------- as partes

const section = () =>
  document.querySelector<HTMLElement>('[data-section="lab"]') as HTMLElement;
const labState = () => section().getAttribute("data-lab-state");
const grid = (alpha: Alpha) =>
  section().querySelector<HTMLElement>(`section[data-alpha="${alpha}"]`) as HTMLElement;
const sectionHas = (text: string) => (section().textContent ?? "").includes(text);
const labCalls = () => calls.filter((u) => u.endsWith("/lab")).length;

async function settled(state: string): Promise<void> {
  await waitFor(() => expect(section()).not.toBeNull());
  await waitFor(() => expect(labState()).toBe(state));
}

function readingButton(key: "casco.leitura.iniciante" | "casco.leitura.avancada") {
  return screen.getByRole("button", { name: TEXTOS[key] });
}

// ---------------------------------------------------------------- a ordem

describe("RF-13 — a ordem das seções", () => {
  it("a aba do laboratório: só a seção dele, sem o risco nem os Fundamentos", async () => {
    renderAsset();
    await settled("READY");
    expect(section()).not.toBeNull();
    expect(document.querySelector("[data-risk-state]")).toBeNull();
    expect(document.querySelector('[data-section="fundamentals"]')).toBeNull();
    const current = document.querySelector('.ruvor-tabs [aria-current="page"]');
    expect(current?.textContent).toBe(TEXTOS["ativo.aba.laboratorio"]);
  });
});

// ---------------------------------------------------------------- os estados

describe("V-11 — cada estado com a frase dele", () => {
  it("carregando: o esqueleto e a frase para leitor de tela", async () => {
    labReply = null;
    stubFetch();
    renderAsset();
    await settled("LOADING");
    expect(sectionHas(TEXTOS["laboratorio.carregando"])).toBe(true);
    expect(section().querySelector("[aria-busy='true']")).not.toBeNull();
  });

  it("erro da leitura: a mensagem e o tentar de novo, que pede só o /lab", async () => {
    labReply = {
      status: 500,
      body: { error: { code: "internal_error", message: "x", details: {} } },
    };
    stubFetch();
    renderAsset();
    await settled("ERROR");
    expect(within(section()).getByRole("alert").textContent).toContain(
      TEXTOS["ativo.erroSecao"],
    );
    labReply = ok(lab());
    const before = calls.length;
    fireEvent.click(
      within(section()).getByRole("button", { name: TEXTOS["ativo.tentarDeNovo"] }),
    );
    await settled("READY");
    expect(calls.slice(before)).toEqual(["/api/v1/assets/ITUB4/lab"]);
  });

  it.each([
    [
      "falhou, ativo: a falha e a promessa",
      lab({ latest: null, last_failure: FAILURE }),
      "FAILED",
      [
        TEXTOS["laboratorio.estado.falhou.titulo"],
        TEXTOS["laboratorio.estado.falhou"]("05/10/2026"),
        TEXTOS["laboratorio.estado.tentaDeNovo"],
      ],
      [],
    ],
    [
      "falhou, inativo: sem a promessa",
      lab({ latest: null, last_failure: FAILURE, active: false }),
      "FAILED",
      [TEXTOS["laboratorio.estado.falhou"]("05/10/2026")],
      [TEXTOS["laboratorio.estado.tentaDeNovo"]],
    ],
    [
      "a calcular",
      lab({ latest: null, pending: true }),
      "PENDING",
      [
        TEXTOS["laboratorio.estado.aCalcular.titulo"],
        TEXTOS["laboratorio.estado.aCalcular"],
      ],
      [],
    ],
    [
      "inativo",
      lab({ latest: null, active: false }),
      "INACTIVE",
      [
        TEXTOS["laboratorio.estado.inativo.titulo"],
        TEXTOS["laboratorio.estado.inativo"],
      ],
      [],
    ],
    [
      "sem a década",
      lab({
        latest: null,
        decade: {
          ...COMPLETE,
          first_price_date: "2016-10-28",
          end_date: "2026-10-28",
          complete: false,
        },
      }),
      "NO_DECADE",
      [TEXTOS["laboratorio.estado.semDecada"]("28/10/2016", "28/10/2026")],
      [],
    ],
    [
      "série curta",
      lab({ latest: null, decade: { ...COMPLETE, sessions: 480 } }),
      "SHORT",
      [TEXTOS["laboratorio.estado.serieCurta"]("480", "503")],
      [],
    ],
    [
      "sem risco: sem botão",
      lab({ latest: null, risk_engine_version: null }),
      "NO_RISK",
      [
        TEXTOS["laboratorio.estado.semRisco.titulo"],
        TEXTOS["laboratorio.estado.semRisco"],
      ],
      [],
    ],
  ])("%s", async (_caso, body, state, present, absent) => {
    labReply = ok(body);
    stubFetch();
    renderAsset();
    await settled(state);
    for (const text of present) expect(sectionHas(text), text).toBe(true);
    for (const text of absent) expect(sectionHas(text), text).toBe(false);
    expect(within(section()).queryByRole("button")).toBeNull();
  });
});

// ---------------------------------------------------------------- a grade

describe("V-11 — as duas grades", () => {
  it("as linhas em MODEL_ORDER, com a resposta embaralhada, nos dois níveis", async () => {
    renderAsset();
    await settled("READY");
    for (const alpha of ["0.0500", "0.0100"] as const) {
      const rows = [...grid(alpha).querySelectorAll("tbody tr")].map((r) =>
        r.getAttribute("data-model"),
      );
      expect(rows).toEqual([...MODEL_ORDER]);
    }
  });

  it("tabela de verdade: cabeçalho de coluna para os anos e de linha para os modelos", async () => {
    renderAsset();
    await settled("READY");
    // pelo seletor, não pela consulta de papel (lenta no jsdom numa tabela deste tamanho):
    // `th` com `scope` é o cabeçalho de coluna e de linha da tabela de verdade
    const table = grid("0.0500").querySelector("table") as HTMLElement;
    expect(
      table.querySelectorAll('thead th[scope="col"]').length,
    ).toBeGreaterThanOrEqual(4);
    expect(table.querySelectorAll('tbody th[scope="row"]')).toHaveLength(9);
    expect(table.querySelectorAll("td th, th th")).toHaveLength(0);
  });

  it("a 95%: o veredito de cada ano com texto, e o ano curto com o rótulo próprio", async () => {
    renderAsset();
    await settled("READY");
    const row = grid("0.0500").querySelector(
      'tr[data-model="historical"]',
    ) as HTMLElement;
    const tags = [...row.querySelectorAll("td[data-year] .ruvor-tag")].map(
      (t) => t.textContent,
    );
    // o histórico (posição 0): o ano 1 adequado, o 2 não, o 3 curto
    expect(tags).toEqual([
      TEXTOS["risco.tag.adequado"],
      TEXTOS["risco.tag.naoAdequado"],
      TEXTOS["laboratorio.tag.anoCurto"],
    ]);
    for (const tag of grid("0.0500").querySelectorAll(".ruvor-tag")) {
      expect((tag.textContent ?? "").trim()).not.toBe("");
    }
  });

  it("a 99%: as violações por ano, sem veredito por ano; a década com o veredito", async () => {
    renderAsset();
    await settled("READY");
    expect(grid("0.0100").querySelectorAll("td[data-year] .ruvor-tag")).toHaveLength(0);
    expect(grid("0.0100").querySelectorAll("td[data-year]").length).toBe(27);
    expect(
      grid("0.0100").querySelectorAll("td[data-decade] .ruvor-tag").length,
    ).toBeGreaterThan(0);
  });

  it("o 'k de N' só a 95%", async () => {
    renderAsset();
    await settled("READY");
    const kn = grid("0.0500").querySelector(
      'tr[data-model="historical"] .ruvor-lab-grid__wide[data-years-not-rejected]',
    );
    expect(kn?.textContent).toBe(TEXTOS["laboratorio.grade.kDeN"](1, 2));
    expect(grid("0.0100").querySelectorAll("[data-years-not-rejected]")).toHaveLength(
      0,
    );
  });

  it("o modelo com erro: a frase de risco.erroModelo, sem números", async () => {
    labReply = ok(lab({ latest: partial() }));
    stubFetch();
    renderAsset();
    await settled("READY");
    const row = grid("0.0100").querySelector('tr[data-model="gru"]') as HTMLElement;
    expect(row.getAttribute("data-error")).toBe("true");
    expect(row.textContent).toContain(
      TEXTOS["risco.erroModelo"]("o treino não convergiu"),
    );
    expect(row.querySelectorAll("td[data-year]")).toHaveLength(0);
  });
});

// ---------------------------------------------------------------- as notas

describe("V-11 — as notas do estado pronto: no máximo uma", () => {
  const panels = () => section().querySelectorAll("[data-note-panel]");

  it.each([
    [
      "a falha, com a promessa (ativo)",
      lab({ last_failure: FAILURE, risk_engine_version: "0.5.0", latest: partial() }),
      TEXTOS["laboratorio.nota.falha"]("05/10/2026"),
      [TEXTOS["laboratorio.estado.tentaDeNovo"]],
      [],
    ],
    [
      "a falha, sem a promessa (inativo)",
      lab({ last_failure: FAILURE, active: false }),
      TEXTOS["laboratorio.nota.falha"]("05/10/2026"),
      [],
      [TEXTOS["laboratorio.estado.tentaDeNovo"]],
    ],
    [
      "o motor, num partial de outro motor: só a do motor",
      lab({ risk_engine_version: "0.5.0", latest: partial() }),
      TEXTOS["laboratorio.nota.motor"]("0.4.0", "0.5.0"),
      [],
      [TEXTOS["laboratorio.nota.parcial"](1)],
    ],
    [
      "o partial do mesmo motor, com o refazer",
      lab({ latest: partial() }),
      TEXTOS["laboratorio.nota.parcial"](1),
      [TEXTOS["laboratorio.nota.refeito"]],
      [],
    ],
    [
      "o partial no inativo: sem o refazer",
      lab({ latest: partial(), active: false }),
      TEXTOS["laboratorio.nota.parcial"](1),
      [],
      [TEXTOS["laboratorio.nota.refeito"]],
    ],
  ])("%s", async (_caso, body, title, present, absent) => {
    labReply = ok(body);
    stubFetch();
    renderAsset();
    await settled("READY");
    expect(panels()).toHaveLength(1);
    expect(panels()[0]?.textContent).toContain(title);
    for (const text of present) expect(sectionHas(text), text).toBe(true);
    for (const text of absent) expect(sectionHas(text), text).toBe(false);
  });

  it("o ok do mesmo motor: nenhuma nota", async () => {
    renderAsset();
    await settled("READY");
    expect(panels()).toHaveLength(0);
  });

  it("o motor diferente no ativo inativo: nenhuma nota", async () => {
    labReply = ok(lab({ risk_engine_version: "0.5.0", active: false }));
    stubFetch();
    renderAsset();
    await settled("READY");
    expect(panels()).toHaveLength(0);
  });
});

// ---------------------------------------------------------------- as duas leituras

/** As nove chaves da lista fechada, com os argumentos que a seção do `lab()` produz. */
function closedKeys(): Array<[string, unknown[]]> {
  const r = result("historical", "0.0500");
  return [
    [
      "laboratorio.decada",
      [formatDate("2016-09-22"), formatDate("2026-09-22"), 3, 110],
    ],
    ["laboratorio.diferenca", ["0.4.0", formatDate("2026-09-22")]],
    ["laboratorio.violacoesAno", ["12,6", 20]],
    ["laboratorio.vereditoAno", [18]],
    ["laboratorio.anoNaoJulgado", [110]],
    ["laboratorio.semVereditoAno99", []],
    [
      "laboratorio.violacoesDecada",
      [
        formatInteger(r.violations ?? 0),
        formatDecimal(Number(r.expected_violations), 1),
        20,
        r.kupiec_passed === true,
      ],
    ],
    ["laboratorio.vereditoDecada", []],
    ["laboratorio.anosNaoRejeitados", []],
  ];
}

function phraseOf(registro: object, key: string, args: unknown[]): string {
  const v = (registro as Record<string, unknown>)[key];
  return typeof v === "function"
    ? (v as (...a: unknown[]) => string)(...args)
    : String(v);
}

function openAll(): void {
  for (const toggle of section().querySelectorAll<HTMLElement>(
    ".ruvor-collapsible__toggle[aria-expanded='false']",
  )) {
    fireEvent.click(toggle);
  }
}

describe("V-12 — as duas leituras", () => {
  it("a lista cobre as nove chaves, todas com avançada", () => {
    expect(new Set(closedKeys().map(([k]) => k)).size).toBe(9);
    for (const [key] of closedKeys()) {
      expect(Object.hasOwn(TEXTOS_AVANCADOS, key), key).toBe(true);
    }
  });

  it("a prova por seção no avançado: cada chave na avançada, nunca na iniciante", async () => {
    comNivel("advanced");
    renderAsset();
    await settled("READY");
    const ausentes: string[] = [];
    const presentes: string[] = [];
    for (const [key, args] of closedKeys()) {
      if (!sectionHas(phraseOf(TEXTOS_AVANCADOS, key, args))) ausentes.push(key);
      if (sectionHas(phraseOf(TEXTOS, key, args))) presentes.push(key);
    }
    expect(ausentes, "avançada ausente").toEqual([]);
    expect(presentes, "iniciante presente").toEqual([]);
  });

  it("na iniciante, abertos os recolhidos: as iniciantes, e nenhuma avançada", async () => {
    comNivel("beginner");
    renderAsset();
    await settled("READY");
    openAll();
    const ausentes: string[] = [];
    const presentes: string[] = [];
    for (const [key, args] of closedKeys()) {
      if (!sectionHas(phraseOf(TEXTOS, key, args))) ausentes.push(key);
      if (sectionHas(phraseOf(TEXTOS_AVANCADOS, key, args))) presentes.push(key);
    }
    expect(ausentes, "iniciante ausente").toEqual([]);
    expect(presentes, "avançada presente").toEqual([]);
  });

  it.each(["beginner", "advanced"] as const)(
    "a diferença honesta está presente na leitura %s",
    async (reading) => {
      comNivel(reading);
      renderAsset();
      await settled("READY");
      const honest = section().querySelector('[data-phrase="diferenca"]');
      const registro = reading === "advanced" ? TEXTOS_AVANCADOS : TEXTOS;
      expect(honest?.textContent).toBe(
        phraseOf(registro, "laboratorio.diferenca", [
          "0.4.0",
          formatDate("2026-09-22"),
        ]),
      );
    },
  );

  it("na iniciante, a trilha e os p-valores recolhidos; a grade aberta, com as notas depois da tabela", async () => {
    comNivel("beginner");
    renderAsset();
    await settled("READY");
    for (const name of ["lab-tests", "lab-trail"]) {
      expect(
        section()
          .querySelector(`[data-collapsible="${name}"]`)
          ?.getAttribute("data-open"),
      ).toBe("false");
    }
    expect(section().querySelectorAll('[data-test="kupiec"]')).toHaveLength(0);
    expect(section().querySelector(".ruvor-trail")).toBeNull();
    const panel = grid("0.0500");
    const table = panel.querySelector("table") as HTMLElement;
    const note = panel.querySelector('[data-phrase="violacoesAno"]') as HTMLElement;
    expect(
      table.compareDocumentPosition(note) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("na avançada, a trilha e os p-valores abertos, e as notas antes da tabela", async () => {
    comNivel("advanced");
    renderAsset();
    await settled("READY");
    for (const name of ["lab-tests", "lab-trail"]) {
      expect(
        section()
          .querySelector(`[data-collapsible="${name}"]`)
          ?.getAttribute("data-open"),
      ).toBe("true");
    }
    expect(section().querySelectorAll('[data-test="kupiec"]').length).toBe(18);
    expect(section().querySelector(".ruvor-trail")).not.toBeNull();
    const panel = grid("0.0500");
    const table = panel.querySelector("table") as HTMLElement;
    const note = panel.querySelector('[data-phrase="violacoesAno"]') as HTMLElement;
    expect(
      note.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("trocar o nível não pede nada à API", async () => {
    comNivel("beginner");
    renderAsset();
    await settled("READY");
    const before = calls.length;
    const lab0 = labCalls();
    await act(async () => fireEvent.click(readingButton("casco.leitura.avancada")));
    expect(
      sectionHas(phraseOf(TEXTOS_AVANCADOS, "laboratorio.vereditoDecada", [])),
    ).toBe(true);
    await act(async () => fireEvent.click(readingButton("casco.leitura.iniciante")));
    expect(calls.length).toBe(before);
    expect(labCalls()).toBe(lab0);
  });
});
