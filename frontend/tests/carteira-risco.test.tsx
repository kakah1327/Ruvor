/**
 * M2.2b (T9), contra o `risco.html` aprovado: V-06 a V-08 e a parte do V-01 da consulta.
 *
 * - os sete estados do RF-09, na ordem de `portfolio/riskState.ts`, cada um com o seu corpo;
 * - cada resposta do pedido (RF-11): o 202 entra pela fonte; o 409 `portfolio_risk_up_to_date`
 *   relê o `GET` e diz a data; os 429; a rede; o 5xx; o 401, que põe o aviso no lugar do botão;
 *   o 404, que leva a página a "não encontrada";
 * - os três casos do histórico curto (RF-12), com o link só nas ações sem preço;
 * - a perda em reais só com valor, no resumo e por modelo, e a data dos preços (RF-10);
 * - depois de um `PUT` que muda a versão, um `GET .../risk` novo, e o resultado anterior some —
 *   também quando a releitura falha; depois de um `PATCH` do valor, um `GET .../risk` novo;
 * - o cálculo em curso nas frases da composição (RF-07);
 * - a consulta repetida: segue depois de um erro, para no 401 com `expired()`;
 * - as duas leituras: a prova por seção no avançado para as cinco chaves novas, e nenhum pedido
 *   ao trocar o nível.
 *
 * O `fetch` é um duplo que responde pelo método e pelo endereço; `null` deixa o pedido pendente.
 */
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { routes } from "../src/App";
import {
  MODEL_ORDER,
  type ModelName,
  type Portfolio,
  type PortfolioProgress,
  type PortfolioRisk,
  type PortfolioRiskResult,
  type PortfolioRun,
} from "../src/api/types";
import { TEXTOS_AVANCADOS } from "../src/content/avancado";
import { TEXTOS } from "../src/content/textos";
import { formatPercent } from "../src/format/numbers";
import { lossFromVar } from "../src/format/var";
import { formatBrlText } from "../src/portfolio/notional";
import { POLL_INTERVAL_MS } from "../src/risk/usePolling";
import type { Me } from "../src/session/types";
import { instalarDublesDeNavegador, restaurarDublesDeNavegador } from "./dubles";
import { comNivel, limparNivel } from "./nivel";

// O `routes` chega na tela do ativo, que importa o uPlot; o uPlot pede `matchMedia` no import.
vi.mock("uplot", () => ({ default: class {} }));

const ME: Me = {
  email: "ana.souza@exemplo.com",
  name: "Ana Beatriz Souza",
  role: "admin",
  must_change_password: false,
  is_staff: false,
  organization: { name: "Gestora Exemplo", slug: "gestora", is_personal: false },
};

const ID = "5b0e6c1e-0000-4000-8000-000000000000";

const BASE: Portfolio = {
  id: ID,
  name: "Bancos e energia",
  notional: "100000.00",
  version: 2,
  holdings: [
    { ticker: "ITUB4", name: "ITAU UNIBANCO HOLDING S.A.", weight: "60.00" },
    { ticker: "PETR4", name: "PETROLEO BRASILEIRO S.A. PETROBRAS", weight: "40.00" },
  ],
  created_at: "2026-09-29T10:12:00-03:00",
  updated_at: "2026-10-02T16:41:00-03:00",
  version_created_at: "2026-10-02T19:41:00Z",
  created_by: { email: ME.email, name: ME.name },
};

// ---------------------------------------------------------------- o dado (o do `risco.html`)

const CATEGORY: Record<ModelName, PortfolioRiskResult["model_category"]> = {
  historical: "traditional",
  parametric: "traditional",
  monte_carlo: "traditional",
  garch_1_1: "garch",
  egarch: "garch",
  lstm: "ml",
  gru: "ml",
  garchnet: "ml",
  caviar: "ml",
};
const ALPHAS = ["0.0500", "0.0100"] as const;
const VAR: Record<(typeof ALPHAS)[number], number[]> = {
  "0.0500": [0.0181, 0.0203, 0.0205, 0.0219, 0.0198, 0.0214, 0.0236, 0.0192, 0.0221],
  "0.0100": [0.0352, 0.0291, 0.0294, 0.0318, 0.0287, 0.0339, 0.0428, 0.0336, 0.0405],
};
const OK: Record<(typeof ALPHAS)[number], boolean[]> = {
  "0.0500": [false, true, true, true, true, false, true, true, true],
  "0.0100": [false, false, false, true, true, true, false, true, true],
};

/** A perda em reais como a API a calcula na leitura: notional × (1 − e^(−VaR)), ao centavo. */
function brl(notional: string | null, v: number): string | null {
  return notional === null
    ? null
    : (Math.round(Number(notional) * lossFromVar(v) * 100) / 100).toFixed(2);
}

function result(
  model: ModelName,
  alpha: (typeof ALPHAS)[number],
  notional: string | null,
  failed: boolean,
): PortfolioRiskResult {
  const i = MODEL_ORDER.indexOf(model);
  const v = VAR[alpha][i] as number;
  const ok = OK[alpha][i] as boolean;
  if (failed) {
    return {
      model_name: model,
      model_category: CATEGORY[model],
      alpha,
      hyperparameters: {},
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
      error: "falha fictícia do treino",
      loss_brl: null,
    };
  }
  return {
    model_name: model,
    model_category: CATEGORY[model],
    alpha,
    hyperparameters: {},
    var_latest: v.toFixed(10),
    var_mean: (v * 0.97).toFixed(10),
    violations: 110,
    expected_violations: (2227 * Number(alpha)).toFixed(6),
    kupiec_passed: ok,
    kupiec_p_value: ok ? "0.4120000000" : "0.0004000000",
    christoffersen_passed: true,
    christoffersen_p_value: "0.5530000000",
    dq_passed: ok,
    dq_p_value: ok ? "0.1870000000" : "0.0000000000",
    adequate: ok,
    error: "",
    loss_brl: brl(notional, v),
  };
}

function run(
  status: PortfolioRun["status"],
  notional: string | null,
  { version = 2, asOf = "2026-10-02" }: { version?: number; asOf?: string } = {},
): PortfolioRun {
  const failedModels: ModelName[] = status === "partial" ? ["lstm", "gru"] : [];
  const results =
    status === "failed"
      ? []
      : ALPHAS.flatMap((a) =>
          MODEL_ORDER.map((m) => result(m, a, notional, failedModels.includes(m))),
        );
  return {
    id: 31,
    version,
    status,
    calculated_at: "2026-10-03T12:40:00Z",
    finished_at: "2026-10-03T12:42:31Z",
    engine_version: "0.5.0",
    seed: 42,
    train_window_days: 252,
    first_date: "2016-10-03",
    as_of_date: asOf,
    session_count: 2480,
    train_count: 252,
    test_count: 2227,
    requested_models: [...MODEL_ORDER],
    series_sha256: "9f2c4e8a1b7d3f60c5a2e9d84b1f7c3a6e0d2b9f4c8a1e7d3b5f9c2a6e4d8b1f",
    price_run_id: 412,
    requested_by: { email: ME.email, name: ME.name },
    results,
    summary: ALPHAS.map((alpha) => {
      const vs = results
        .filter((r) => r.alpha === alpha && r.var_latest !== null)
        .map((r) => Number(r.var_latest));
      const min = vs.length ? Math.min(...vs) : null;
      const max = vs.length ? Math.max(...vs) : null;
      return {
        alpha,
        computed: [],
        var_min: min === null ? null : min.toFixed(10),
        var_max: max === null ? null : max.toFixed(10),
        loss_brl_min: min === null ? null : brl(notional, min),
        loss_brl_max: max === null ? null : brl(notional, max),
        not_rejected: [],
      };
    }),
  };
}

const progress = (written: number, version = 2): PortfolioProgress => ({
  id: 32,
  version,
  calculated_at: "2026-10-03T13:05:00Z",
  requested_models: [...MODEL_ORDER],
  results_written: written,
  results_expected: 18,
});

function risk(
  latest: PortfolioRun | null,
  inProgress: PortfolioProgress | null,
  {
    version = 2,
    notional = BASE.notional,
  }: { version?: number; notional?: string | null } = {},
): { portfolio_risk: PortfolioRisk } {
  return {
    portfolio_risk: {
      portfolio_id: ID,
      version,
      notional,
      latest,
      in_progress: inProgress,
    },
  };
}

// ---------------------------------------------------------------- o duplo do `fetch`

const API_MESSAGE = "MENSAGEM CRUA DA API";

type Reply = { status: number; body: unknown } | "network" | null;

const ok = (body: unknown, status = 200): Reply => ({ status, body });
const one = (p: Portfolio): Reply => ok({ portfolio: p });
const fail = (status: number, code: string, details: object = {}): Reply => ({
  status,
  body: { error: { code, message: API_MESSAGE, details } },
});

type Call = { url: string; method: string; body: string | undefined };

let calls: Call[] = [];
let replies: Record<string, Reply[]> = {};

/** As respostas por "MÉTODO endereço", em fila; a última se repete. */
function reply(key: string, ...queue: Reply[]): void {
  replies[key] = queue;
}

function stubFetch(): void {
  calls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      calls.push({ url, method, body: init?.body as string | undefined });
      const queue = replies[`${method} ${url}`] ?? [null];
      const r = queue.length > 1 ? (queue.shift() as Reply) : queue[0];
      if (r === null) return new Promise<Response>(() => {});
      if (r === "network") return Promise.reject(new TypeError("Failed to fetch"));
      return Promise.resolve({
        ok: r.status >= 200 && r.status < 300,
        status: r.status,
        json: async () => r.body,
      } as unknown as Response);
    }),
  );
}

const ME_KEY = "GET /api/v1/auth/me";
const URL_ONE = `/api/v1/portfolios/${ID}`;
const URL_RISK = `${URL_ONE}/risk`;
const GET_ONE = `GET ${URL_ONE}`;
const GET_RISK = `GET ${URL_RISK}`;
const POST_RISK = `POST ${URL_RISK}`;
const PUT_ONE = `PUT ${URL_ONE}/holdings`;
const PATCH_ONE = `PATCH ${URL_ONE}`;

const riskGets = () => calls.filter((c) => c.method === "GET" && c.url === URL_RISK);

async function microtasks(): Promise<void> {
  for (let i = 0; i < 30; i += 1) {
    await Promise.resolve();
  }
}

/** As promessas (os pedidos respondem na hora). */
async function flush(): Promise<void> {
  await act(microtasks);
  await act(microtasks);
}

async function click(element: Element): Promise<void> {
  await act(async () => {
    fireEvent.click(element);
  });
  await flush();
}

async function openPage(riskReply: Reply, p: Portfolio = BASE): Promise<void> {
  reply(GET_ONE, one(p));
  reply(GET_RISK, riskReply);
  const router = createMemoryRouter(routes, { initialEntries: [`/carteiras/${ID}`] });
  render(<RouterProvider router={router} />);
  await flush();
}

const section = () => document.querySelector('[data-part="risco"]') as HTMLElement;
const stateOf = () => section()?.getAttribute("data-risk-state");
const part = (name: string, root: ParentNode = document) =>
  root.querySelector(`[data-part="${name}"]`) as HTMLElement | null;
const phrase = (name: string) =>
  section().querySelector(`[data-phrase="${name}"]`)?.textContent ?? null;
const requestButton = () => part("pedido", section()) as HTMLButtonElement | null;
const rail = () => document.querySelector("aside.ruvor-rail") as HTMLElement | null;
const has = (text: string) => (document.body.textContent ?? "").includes(text);
const readingButton = (key: "casco.leitura.iniciante" | "casco.leitura.avancada") =>
  within(screen.getByRole("group", { name: TEXTOS["casco.leitura.rotulo"] })).getByRole(
    "button",
    { name: TEXTOS[key] },
  );

/** Abre todo recolhido da seção e da trilha (a iniciante os fecha). */
async function openAll(): Promise<void> {
  for (const root of [section(), rail()]) {
    if (root === null) continue;
    for (const b of [
      ...root.querySelectorAll<HTMLButtonElement>(
        '.ruvor-collapsible__toggle[aria-expanded="false"]',
      ),
    ]) {
      await click(b);
    }
  }
}

beforeEach(() => {
  replies = {};
  reply(ME_KEY, ok(ME));
  // biome-ignore lint/suspicious/noDocumentCookie: os pedidos mandam o token do cookie de verdade.
  document.cookie = "csrftoken=tok; path=/";
  stubFetch();
  instalarDublesDeNavegador();
});

afterEach(() => {
  cleanup();
  limparNivel();
  restaurarDublesDeNavegador();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  // biome-ignore lint/suspicious/noDocumentCookie: limpa o cookie gravado no beforeEach.
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

// ---------------------------------------------------------------- V-06: os sete estados

describe("V-06 — os sete estados, na ordem do RF-09", () => {
  it("1 carregando: o esqueleto, com a trilha também carregando", async () => {
    await openPage(null);
    expect(stateOf()).toBe("loading");
    expect(within(section()).getByRole("status").getAttribute("aria-busy")).toBe(
      "true",
    );
    expect(has(TEXTOS["carteira.risco.carregando"])).toBe(true);
    expect(rail()?.querySelector('[aria-busy="true"]')).not.toBeNull();
  });

  it("2 erro da primeira leitura: a mensagem com 'Tentar de novo', que pede de novo", async () => {
    await openPage(fail(500, "internal_error"));
    expect(stateOf()).toBe("error");
    expect(has(TEXTOS["ativo.erroSecao"])).toBe(true);
    expect(rail()).toBeNull();
    reply(GET_RISK, ok(risk(null, null)));
    await click(
      within(section()).getByRole("button", { name: TEXTOS["ativo.tentarDeNovo"] }),
    );
    expect(stateOf()).toBe("never");
    expect(riskGets()).toHaveLength(2);
  });

  it("3 resultado + recalculando: o resultado anterior com o andamento por cima, sem botão", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), progress(7))));
    expect(stateOf()).toBe("result_recalculating");
    expect(has(TEXTOS["risco.estado.recalculando"](7, 18))).toBe(true);
    expect(has(TEXTOS["risco.estado.recalculando.nota"])).toBe(true);
    expect(section().querySelectorAll("[data-alpha]").length).toBeGreaterThan(0);
    expect(requestButton()).toBeNull();
    expect(section().querySelector('[aria-live="polite"]')?.textContent).toBe(
      TEXTOS["risco.estado.recalculando"](7, 18),
    );
  });

  it("4 calculando: o andamento, sem resultado e sem botão", async () => {
    await openPage(ok(risk(null, progress(7))));
    expect(stateOf()).toBe("calculating");
    const bar = within(section()).getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("7");
    expect(bar.getAttribute("aria-valuemax")).toBe("18");
    expect(has(TEXTOS["risco.estado.E4.nota"])).toBe(true);
    expect(requestButton()).toBeNull();
    expect(rail()).toBeNull();
  });

  it("4 calculando com o anterior falho: o recálculo com a nota da falha e o painel dela", async () => {
    await openPage(ok(risk(run("failed", BASE.notional), progress(4))));
    expect(stateOf()).toBe("calculating");
    expect(has(TEXTOS["risco.estado.recalculando.notaFalha"])).toBe(true);
    expect(has(TEXTOS["risco.estado.E3.titulo"])).toBe(true);
    expect(has(TEXTOS["carteira.risco.estado.falhou"])).toBe(true);
    expect(requestButton()).toBeNull();
  });

  it("5 pronto: o resultado, a data dos preços e 'Calcular de novo', com a frase sem rotina", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    expect(stateOf()).toBe("ready");
    expect(phrase("asOf")).toBe(TEXTOS["carteira.risco.asOf"]("02/10/2026"));
    expect(requestButton()?.textContent).toBe(TEXTOS["risco.pedido.deNovo"]);
    expect(has(TEXTOS["carteira.risco.semRotina"])).toBe(true);
    expect(part("parcial")).toBeNull();
    // A trilha da carteira, na coluna lateral.
    expect(rail()?.textContent).toContain(TEXTOS["risco.trilha.titulo"]);
  });

  it("5 pronto, parcial: quantos modelos ficaram sem resultado", async () => {
    await openPage(ok(risk(run("partial", BASE.notional), null)));
    expect(stateOf()).toBe("ready");
    expect(part("parcial")?.textContent).toBe(
      TEXTOS["carteira.risco.estado.parcial"](2),
    );
  });

  it("6 falhou: a falha com 'Calcular de novo'", async () => {
    await openPage(ok(risk(run("failed", BASE.notional), null)));
    expect(stateOf()).toBe("failed");
    expect(has(TEXTOS["carteira.risco.estado.falhou"])).toBe(true);
    expect(requestButton()?.textContent).toBe(TEXTOS["risco.pedido.deNovo"]);
  });

  it("7 nunca calculado: o convite com 'Calcular o risco'", async () => {
    await openPage(ok(risk(null, null)));
    expect(stateOf()).toBe("never");
    expect(has(TEXTOS["carteira.risco.estado.nunca.titulo"])).toBe(true);
    expect(has(TEXTOS["carteira.risco.estado.nunca"])).toBe(true);
    expect(requestButton()?.textContent).toBe(TEXTOS["risco.pedido.calcular"]);
    expect(rail()).toBeNull();
  });
});

// ---------------------------------------------------------------- RF-10: o resultado

describe("RF-10 — a perda em reais só com valor, e a data dos preços", () => {
  it("com valor: a faixa em reais de cada nível, a frase dela e a perda de cada modelo", async () => {
    comNivel("advanced");
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    const levels = section().querySelectorAll('[data-part="perda-reais"]');
    const lo = brl(BASE.notional, 0.0181) as string;
    const hi = brl(BASE.notional, 0.0236) as string;
    const first = section().querySelector(
      'article[data-alpha="0.0500"] [data-part="perda-reais"]',
    );
    expect(first?.textContent).toBe(
      `${TEXTOS["risco.faixa"](formatBrlText(lo), formatBrlText(hi))}${TEXTOS["risco.horizonte"]}`,
    );
    expect(first?.classList.contains("ruvor-range--brl")).toBe(true);
    expect(phrase("perdaReais")).toBe(
      TEXTOS_AVANCADOS["carteira.risco.perdaReais"](formatBrlText("100000.00"), 20),
    );
    expect(phrase("valorAgora")).toBe(TEXTOS_AVANCADOS["carteira.risco.valorAgora"]);
    // A tabela (aberta na avançada): a perda em reais de cada modelo, ao lado da %.
    const table = section().querySelector('[data-collapsible="models"]') as HTMLElement;
    const row = table.querySelector('tr[data-model="historical"]') as HTMLElement;
    expect(row.querySelector('[data-part="perda-reais"]')?.textContent).toBe(
      formatBrlText(brl(BASE.notional, 0.0181) as string),
    );
    expect(levels.length).toBeGreaterThan(2);
  });

  it("sem valor: nenhum real, nem no resumo nem na tabela, e a frase de só em %", async () => {
    comNivel("advanced");
    const p = { ...BASE, notional: null };
    await openPage(ok(risk(run("ok", null), null, { notional: null })), p);
    expect(section().querySelector('[data-part="perda-reais"]')).toBeNull();
    expect(phrase("perdaReais")).toBeNull();
    expect(phrase("valorAgora")).toBeNull();
    expect(part("sem-valor")?.textContent).toBe(TEXTOS["carteira.risco.semValor"]);
    expect(section().textContent).toContain(formatPercent(lossFromVar(0.0181), 1));
  });

  it("a trilha da carteira: a versão, os pregões em comum, quem pediu e o SHA-256", async () => {
    comNivel("advanced");
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    const trail = rail()?.querySelector(".ruvor-trail") as HTMLElement;
    const items = [...trail.querySelectorAll("div")].map((d) => [
      d.querySelector("dt")?.textContent,
      d.querySelector("dd")?.textContent,
    ]);
    expect(items).toContainEqual([TEXTOS["carteira.risco.trilha.versao"], "2"]);
    expect(items).toContainEqual([TEXTOS["carteira.risco.trilha.sessoes"], "2.480"]);
    expect(items).toContainEqual([TEXTOS["carteira.risco.trilha.pedidoPor"], ME.name]);
    expect(items).toContainEqual([
      TEXTOS["carteira.risco.trilha.sha"],
      run("ok", null).series_sha256,
    ]);
    expect(trail.querySelector(".ruvor-trail__hash")).not.toBeNull();
  });
});

// ---------------------------------------------------------------- V-07: o pedido

describe("V-07 — as respostas do pedido (RF-11)", () => {
  it("enviando: o botão desabilitado, com aria-busy, e 'Enviando o pedido…'", async () => {
    await openPage(ok(risk(null, null)));
    reply(POST_RISK, null);
    await click(requestButton() as HTMLButtonElement);
    expect(requestButton()?.disabled).toBe(true);
    expect(requestButton()?.getAttribute("aria-busy")).toBe("true");
    expect(has(TEXTOS["risco.pedido.enviando"])).toBe(true);
  });

  it("202: o corpo entra pela fonte (sem outro GET), e o estado é o dele", async () => {
    await openPage(ok(risk(null, null)));
    reply(POST_RISK, ok(risk(null, progress(0)), 202));
    await click(requestButton() as HTMLButtonElement);
    expect(stateOf()).toBe("calculating");
    expect(riskGets()).toHaveLength(1);
    expect(calls.filter((c) => c.method === "POST")).toHaveLength(1);
  });

  it("202 com a fila recusando: a failed nova é o latest, mesmo com um ok antes", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    reply(POST_RISK, ok(risk(run("failed", BASE.notional), null), 202));
    await click(requestButton() as HTMLButtonElement);
    expect(stateOf()).toBe("failed");
  });

  it("409 portfolio_risk_up_to_date: relê o GET e diz a data do latest relido", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    reply(POST_RISK, fail(409, "portfolio_risk_up_to_date", { run_id: 31 }));
    reply(GET_RISK, ok(risk(run("ok", BASE.notional, { asOf: "2026-10-03" }), null)));
    await click(requestButton() as HTMLButtonElement);
    expect(riskGets()).toHaveLength(2);
    expect(part("atualizado")?.textContent).toBe(
      TEXTOS["carteira.risco.pedido.atualizado"]("03/10/2026"),
    );
    expect(has(API_MESSAGE)).toBe(false);
  });

  it.each([
    [fail(429, "portfolio_compute_busy"), TEXTOS["carteira.risco.pedido.ocupada"]],
    [
      fail(429, "portfolio_queue_full"),
      TEXTOS["carteira.risco.pedido.servicoOcupado"](null),
    ],
    [
      fail(429, "too_many_requests", { wait_seconds: 30 }),
      TEXTOS["carteira.risco.pedido.servicoOcupado"]("30"),
    ],
    [
      fail(429, "too_many_requests"),
      TEXTOS["carteira.risco.pedido.servicoOcupado"](null),
    ],
    ["network" as Reply, TEXTOS["risco.pedido.semResposta"]],
  ])("%# junto do botão, que segue disponível", async (answer, text) => {
    await openPage(ok(risk(null, null)));
    reply(POST_RISK, answer);
    await click(requestButton() as HTMLButtonElement);
    expect(part("resposta-pedido")?.textContent).toBe(text);
    expect(requestButton()?.disabled).toBe(false);
    expect(stateOf()).toBe("never");
  });

  it("5xx: a mensagem da D-86 dentro da frase do pedido não aceito", async () => {
    await openPage(ok(risk(null, null)));
    reply(POST_RISK, fail(500, "internal_error"));
    await click(requestButton() as HTMLButtonElement);
    expect(part("resposta-pedido")?.textContent).toBe(
      TEXTOS["risco.pedido.erro"](API_MESSAGE),
    );
  });

  it("401: o aviso de sessão terminada no lugar do botão; a página só leitura", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    reply(POST_RISK, fail(401, "not_authenticated"));
    await click(requestButton() as HTMLButtonElement);
    expect(requestButton()).toBeNull();
    const notices = document.querySelectorAll('[data-signin-notice="ended"]');
    expect(notices).toHaveLength(1);
    expect(section().contains(notices[0] as Node)).toBe(true);
    expect(document.activeElement).toBe(notices[0]?.querySelector("a"));
    expect(
      screen.queryByRole("button", { name: TEXTOS["carteira.composicao.editar"] }),
    ).toBeNull();
    // A carteira segue à vista.
    expect(screen.getByRole("heading", { level: 1, name: BASE.name })).toBeDefined();
  });

  it("404: a página inteira vai a 'não encontrada'", async () => {
    await openPage(ok(risk(null, null)));
    reply(POST_RISK, fail(404, "portfolio_not_found"));
    await click(requestButton() as HTMLButtonElement);
    expect(has(TEXTOS["carteira.naoEncontrada.titulo"])).toBe(true);
    expect(section()).toBeNull();
  });
});

// ---------------------------------------------------------------- RF-12: o histórico curto

describe("RF-12 — o histórico curto, nos três casos", () => {
  async function short(details: object): Promise<HTMLElement> {
    await openPage(ok(risk(null, null)));
    reply(POST_RISK, fail(409, "insufficient_history", details));
    await click(requestButton() as HTMLButtonElement);
    return part("historico-curto") as HTMLElement;
  }
  const groups = (panel: HTMLElement) =>
    [...panel.querySelectorAll("[data-group]")].map((g) =>
      g.getAttribute("data-group"),
    );

  it("1 e 2 juntos: a sem preço com o link para a página dela; a curta sem link", async () => {
    const panel = await short({
      sessions: 0,
      minimum: 503,
      assets: [
        { ticker: "ABCB4", first_date: null, sessions: 0 },
        { ticker: "ITUB4", first_date: "2016-10-03", sessions: 2480 },
        { ticker: "CURT3", first_date: "2025-03-12", sessions: 410 },
      ],
    });
    expect(groups(panel)).toEqual(["sem-preco", "curtas"]);
    expect(panel.textContent).toContain(TEXTOS["carteira.risco.curta"]("0", "503"));
    const links = [...panel.querySelectorAll("a")];
    expect(links.map((a) => a.textContent)).toEqual([
      TEXTOS["carteira.risco.curta.irPara"]("ABCB4"),
    ]);
    expect(links[0]?.getAttribute("href")).toBe("/ativos/ABCB4/risco");
    const curtas = panel.querySelector('[data-group="curtas"]') as HTMLElement;
    expect(curtas.textContent).toContain(TEXTOS["carteira.risco.curta.curtas"](1));
    expect(curtas.textContent).toContain(
      TEXTOS["carteira.risco.curta.item"]("410", "12/03/2025"),
    );
    expect(curtas.textContent).not.toContain("ITUB4");
    expect(has(API_MESSAGE)).toBe(false);
  });

  it("só o caso 1, no plural", async () => {
    const panel = await short({
      sessions: 0,
      minimum: 503,
      assets: [
        { ticker: "ABCB4", first_date: null, sessions: 0 },
        { ticker: "ABEV3", first_date: null, sessions: 0 },
        { ticker: "PETR4", first_date: "2016-10-03", sessions: 2480 },
      ],
    });
    expect(groups(panel)).toEqual(["sem-preco"]);
    expect(panel.textContent).toContain(TEXTOS["carteira.risco.curta.semPreco"](2));
    expect(panel.querySelectorAll("a")).toHaveLength(2);
  });

  it("3 a sobreposição curta: cada ação com o mínimo, as datas de começo, nenhum link", async () => {
    const panel = await short({
      sessions: 120,
      minimum: 503,
      assets: [
        { ticker: "ANTG3", first_date: "2016-10-03", sessions: 640 },
        { ticker: "NOVA3", first_date: "2018-09-14", sessions: 1950 },
      ],
    });
    expect(groups(panel)).toEqual(["sobreposicao"]);
    expect(panel.textContent).toContain(TEXTOS["carteira.risco.curta"]("120", "503"));
    expect(panel.textContent).toContain(
      TEXTOS["carteira.risco.curta.item"]("1.950", "14/09/2018"),
    );
    expect(panel.querySelectorAll("a")).toHaveLength(0);
  });
});

// ---------------------------------------------------------------- RF-07: a versão e o valor

describe("RF-07 e RF-10 — a releitura depois do PUT e do PATCH", () => {
  async function saveComposition(next: Portfolio): Promise<void> {
    await click(
      screen.getByRole("button", { name: TEXTOS["carteira.composicao.editar"] }),
    );
    reply(PUT_ONE, one(next));
    await act(async () => {
      fireEvent.submit(part("form-composicao") as HTMLElement);
    });
    await flush();
  }

  it("o PUT que muda a versão: um GET novo, e o resultado anterior some até ele voltar", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    expect(stateOf()).toBe("ready");
    reply(GET_RISK, null);
    await saveComposition({ ...BASE, version: 3 });
    expect(riskGets()).toHaveLength(2);
    expect(stateOf()).toBe("loading");
    expect(section().querySelector("[data-alpha]")).toBeNull();
  });

  it("a releitura depois do PUT falha: o erro, nunca o resultado da versão anterior", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    reply(GET_RISK, fail(500, "internal_error"));
    await saveComposition({ ...BASE, version: 3 });
    expect(stateOf()).toBe("error");
    expect(section().querySelector("[data-alpha]")).toBeNull();
  });

  it("o PUT sem mudança (nada mudou): nenhum GET novo", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    await saveComposition(BASE);
    expect(riskGets()).toHaveLength(1);
    expect(stateOf()).toBe("ready");
  });

  it("o PATCH do valor: um GET novo, e os reais do valor de agora", async () => {
    comNivel("advanced");
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    await click(screen.getByRole("button", { name: TEXTOS["carteira.valor.mudar"] }));
    const input = screen.getByLabelText(
      TEXTOS["carteira.valor.campo"],
    ) as HTMLInputElement;
    await act(async () => {
      fireEvent.change(input, { target: { value: "200000" } });
    });
    reply(PATCH_ONE, one({ ...BASE, notional: "200000.00" }));
    reply(GET_RISK, ok(risk(run("ok", "200000.00"), null, { notional: "200000.00" })));
    await act(async () => {
      fireEvent.submit(part("form-valor") as HTMLElement);
    });
    await flush();
    expect(riskGets()).toHaveLength(2);
    expect(phrase("perdaReais")).toBe(
      TEXTOS_AVANCADOS["carteira.risco.perdaReais"](formatBrlText("200000.00"), 20),
    );
  });

  it("o PATCH do nome: nenhum GET novo", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    await click(screen.getByRole("button", { name: TEXTOS["carteira.nome.mudar"] }));
    reply(PATCH_ONE, one({ ...BASE, name: "Outro nome" }));
    await act(async () => {
      fireEvent.submit(part("form-nome") as HTMLElement);
    });
    await flush();
    expect(riskGets()).toHaveLength(1);
  });
});

describe("RF-07 — o cálculo em curso nas frases da composição", () => {
  async function edit(): Promise<void> {
    await click(
      screen.getByRole("button", { name: TEXTOS["carteira.composicao.editar"] }),
    );
  }

  it("no editor, o aviso antes de salvar; sem cálculo em curso, nenhum", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), progress(7))));
    await edit();
    expect(part("em-curso")?.textContent).toBe(
      TEXTOS["carteira.composicao.emCurso"](2),
    );
    cleanup();
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    await edit();
    expect(part("em-curso")).toBeNull();
  });

  it("salvo como a versão seguinte: a frase da versão nova com o cálculo da anterior", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), progress(7))));
    await edit();
    reply(PUT_ONE, one({ ...BASE, version: 3 }));
    reply(GET_RISK, ok(risk(null, null, { version: 3 })));
    await act(async () => {
      fireEvent.submit(part("form-composicao") as HTMLElement);
    });
    await flush();
    expect(part("resposta")?.textContent).toBe(
      TEXTOS["carteira.composicao.salvaEmCurso"](3, 2),
    );
    expect(stateOf()).toBe("never");
  });

  it("outra pessoa mudou no meio: as duas frases", async () => {
    await openPage(ok(risk(run("ok", BASE.notional), progress(7))));
    await edit();
    reply(PUT_ONE, one({ ...BASE, version: 4 }));
    await act(async () => {
      fireEvent.submit(part("form-composicao") as HTMLElement);
    });
    await flush();
    expect(part("resposta")?.textContent).toBe(
      TEXTOS["carteira.composicao.outraPessoa"](4),
    );
    expect(part("resposta-em-curso")?.textContent).toBe(
      TEXTOS["carteira.composicao.riscoEmCurso"](2, 4),
    );
  });
});

// ---------------------------------------------------------------- V-01: a consulta repetida

describe("V-01 — a consulta repetida (D-182)", () => {
  it("segue enquanto há in_progress; um erro mantém o estado e a próxima tenta de novo", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    await openPage(ok(risk(run("ok", BASE.notional), progress(7))));
    expect(stateOf()).toBe("result_recalculating");
    reply(
      GET_RISK,
      fail(503, "internal_error"),
      ok(risk(run("ok", BASE.notional), progress(12))),
    );
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    await flush();
    expect(riskGets()).toHaveLength(2);
    expect(stateOf()).toBe("result_recalculating");
    expect(has(TEXTOS["risco.estado.recalculando"](7, 18))).toBe(true);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    await flush();
    expect(riskGets()).toHaveLength(3);
    expect(has(TEXTOS["risco.estado.recalculando"](12, 18))).toBe(true);
  });

  it("para quando o cálculo fecha", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    await openPage(ok(risk(null, progress(7))));
    reply(GET_RISK, ok(risk(run("ok", BASE.notional), null)));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    await flush();
    expect(stateOf()).toBe("ready");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3 * POLL_INTERVAL_MS);
    });
    expect(riskGets()).toHaveLength(2);
  });

  it("o 401 numa consulta repetida: expired(), o aviso de sessão terminada, e a consulta para", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    await openPage(ok(risk(null, progress(7))));
    reply(GET_RISK, fail(401, "not_authenticated"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    await flush();
    expect(document.querySelectorAll('[data-signin-notice="ended"]')).toHaveLength(1);
    expect(document.querySelector('[data-signin-notice="required"]')).toBeNull();
    // A barra passa a "Entrar": a sessão terminou.
    expect(
      within(screen.getByRole("banner")).queryByRole("link", {
        name: TEXTOS["conta.entrar"],
      }),
    ).not.toBeNull();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3 * POLL_INTERVAL_MS);
    });
    expect(riskGets()).toHaveLength(2);
  });

  it("o 404 numa consulta: a página vai a 'não encontrada'", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    await openPage(ok(risk(null, progress(7))));
    reply(GET_RISK, fail(404, "portfolio_not_found"));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    await flush();
    expect(has(TEXTOS["carteira.naoEncontrada.titulo"])).toBe(true);
    expect(rail()).toBeNull();
  });
});

// ---------------------------------------------------------------- V-08: as duas leituras

/** Cada chave nova da lista fechada com os argumentos que a tela usa para o dado do teste. */
function newKeys(): Array<[keyof typeof TEXTOS_AVANCADOS, unknown[]]> {
  return [
    ["carteira.risco.perdaReais", [formatBrlText("100000.00"), 20]],
    ["carteira.risco.valorAgora", []],
    ["carteira.risco.serie", []],
    ["carteira.risco.asOf", ["02/10/2026"]],
    ["carteira.risco.naoRejeitados", [7, 9, 9]],
  ];
}

function phraseOf(registro: object, key: string, args: unknown[]): string {
  const v = (registro as Record<string, unknown>)[key];
  return typeof v === "function"
    ? (v as (...a: unknown[]) => string)(...args)
    : String(v);
}

describe("V-08 — as duas leituras", () => {
  it("a prova por seção no avançado: cada chave nova na avançada, nunca na iniciante", async () => {
    comNivel("advanced");
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    const ausentes: string[] = [];
    const presentes: string[] = [];
    for (const [key, args] of newKeys()) {
      if (!has(phraseOf(TEXTOS_AVANCADOS, key, args))) ausentes.push(key);
      if (has(phraseOf(TEXTOS, key, args))) presentes.push(key);
    }
    expect(ausentes, "avançada ausente").toEqual([]);
    expect(presentes, "iniciante presente").toEqual([]);
  });

  it("na iniciante, abertos os recolhidos: as iniciantes, e nenhuma avançada", async () => {
    comNivel("beginner");
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    await openAll();
    const ausentes: string[] = [];
    const presentes: string[] = [];
    for (const [key, args] of newKeys()) {
      if (!has(phraseOf(TEXTOS, key, args))) ausentes.push(key);
      if (has(phraseOf(TEXTOS_AVANCADOS, key, args))) presentes.push(key);
    }
    expect(ausentes, "iniciante ausente").toEqual([]);
    expect(presentes, "avançada presente").toEqual([]);
  });

  it("o ramo k = 0 da iniciante fala da carteira, não do ativo", async () => {
    comNivel("beginner");
    const r = run("ok", BASE.notional);
    const none = { ...r, results: r.results.map((x) => ({ ...x, adequate: false })) };
    await openPage(ok(risk(none, null)));
    expect(has(TEXTOS["carteira.risco.naoRejeitados"](0, 9, 9))).toBe(true);
    expect(has(TEXTOS["risco.naoRejeitados"](0, 9, 9))).toBe(false);
  });

  it("na iniciante, a tabela e a trilha recolhidas; na avançada, abertas", async () => {
    comNivel("beginner");
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    const openOf = (root: ParentNode | null, name: string) =>
      root?.querySelector(`[data-collapsible="${name}"]`)?.getAttribute("data-open");
    expect(openOf(section(), "models")).toBe("false");
    expect(openOf(rail(), "trail")).toBe("false");
    await act(async () => fireEvent.click(readingButton("casco.leitura.avancada")));
    expect(openOf(section(), "models")).toBe("true");
    expect(openOf(rail(), "trail")).toBe("true");
  });

  it("trocar o nível não pede nada à API", async () => {
    comNivel("beginner");
    await openPage(ok(risk(run("ok", BASE.notional), null)));
    const before = calls.length;
    await act(async () => fireEvent.click(readingButton("casco.leitura.avancada")));
    expect(phrase("asOf")).toBe(TEXTOS_AVANCADOS["carteira.risco.asOf"]("02/10/2026"));
    await act(async () => fireEvent.click(readingButton("casco.leitura.iniciante")));
    expect(calls.length).toBe(before);
  });
});
