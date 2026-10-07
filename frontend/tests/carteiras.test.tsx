/**
 * M2.2b (T7), contra o `lista.html` aprovado: V-01 (o item "Carteiras" só logado com a conta
 * pronta; o anônimo com o aviso sem `ended` e o `next`; **nenhum pedido antes da sessão
 * resolver**), V-02 (a lista nos estados; "mostrar mais" pede o `offset` seguinte), V-03 (a
 * criação com o editor: o texto do campo preservado, a soma, as conferências do cliente, cada
 * `reason` da API na linha certa pelo `index`) e V-04 (o seletor: só ação ativa escolhível).
 *
 * O `fetch` é um duplo que responde pelo método e pelo endereço; `null` deixa o pedido
 * pendente. Só o `setTimeout` é falso (a pausa do seletor); as promessas correm de verdade.
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
import type { AssetItem, Portfolio } from "../src/api/types";
import { TEXTOS } from "../src/content/textos";
import { formatInstant } from "../src/format/numbers";
import type { Me } from "../src/session/types";

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
const PERSONAL: Me = {
  ...ME,
  organization: { name: "Ana Beatriz Souza", slug: "pessoal-1", is_personal: true },
};

function portfolio(n: number, over: Partial<Portfolio> = {}): Portfolio {
  return {
    id: `6f1c2d3e-0000-4000-8000-${String(n).padStart(12, "0")}`,
    name: `Carteira ${n}`,
    notional: null,
    version: 1,
    holdings: [
      { ticker: "ITUB4", name: "ITAU UNIBANCO HOLDING S.A.", weight: "50.00" },
      { ticker: "PETR4", name: "PETROLEO BRASILEIRO S.A. PETROBRAS", weight: "50.00" },
    ],
    created_at: "2026-09-29T10:00:00-03:00",
    updated_at: "2026-09-29T10:00:00-03:00",
    version_created_at: "2026-10-02T14:31:00-03:00",
    created_by: { email: ME.email, name: ME.name },
    ...over,
  };
}

const BANCOS = portfolio(1, {
  name: "Bancos e energia",
  notional: "50000.00",
  version: 3,
  holdings: [
    { ticker: "BBDC4", name: "BANCO BRADESCO S.A.", weight: "25.00" },
    { ticker: "EQTL3", name: "EQUATORIAL S.A.", weight: "25.00" },
    { ticker: "ITUB4", name: "ITAU UNIBANCO HOLDING S.A.", weight: "25.00" },
    { ticker: "PETR4", name: "PETROLEO BRASILEIRO S.A. PETROBRAS", weight: "25.00" },
  ],
});
const EXPORTADORAS = portfolio(2, {
  name: "Exportadoras",
  version_created_at: "2026-09-30T09:12:00-03:00",
});

function asset(ticker: string, over: Partial<AssetItem> = {}): AssetItem {
  return {
    ticker,
    name: `${ticker} S.A.`,
    trading_name: ticker,
    kind: "stock",
    sector: "Bancos",
    status: "active",
    has_prices: true,
    has_risk: false,
    ...over,
  };
}

const IBOV = asset("IBOV", {
  name: "ÍNDICE BOVESPA",
  trading_name: "IBOVESPA",
  kind: "index",
  sector: null,
});
const BIDI4 = asset("BIDI4", { trading_name: "BANCO INTER", status: "inactive" });
const BBAS3 = asset("BBAS3", { name: "BANCO DO BRASIL S.A.", trading_name: "BRASIL" });
const BBDC4 = asset("BBDC4", { name: "BANCO BRADESCO S.A.", trading_name: "BRADESCO" });
const ITUB4 = asset("ITUB4", { name: "ITAU UNIBANCO HOLDING S.A." });
const PETR4 = asset("PETR4", { name: "PETROLEO BRASILEIRO S.A. PETROBRAS" });
const VALE3 = asset("VALE3", { name: "VALE S.A." });

/** A mensagem que a API manda em todo erro destes testes: nunca pode aparecer na tela. */
const API_MESSAGE = "MENSAGEM CRUA DA API";

type Reply = { status: number; body: unknown } | "network" | null;

const ok = (body: unknown, status = 200): Reply => ({ status, body });
const fail = (status: number, code: string, details: object = {}): Reply => ({
  status,
  body: { error: { code, message: API_MESSAGE, details } },
});
const list = (results: Portfolio[], count = results.length, offset = 0): Reply =>
  ok({ count, limit: 50, offset, results });
const search = (results: AssetItem[], count = results.length): Reply =>
  ok({ count, limit: 20, offset: 0, results });

type Call = { url: string; method: string; body: string | undefined; csrf?: string };

let calls: Call[] = [];
/** As respostas por "MÉTODO endereço", em fila; a última se repete. */
let replies: Record<string, Reply[]> = {};

function reply(key: string, ...queue: Reply[]): void {
  replies[key] = queue;
}

function stubFetch(): void {
  calls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      const headers = (init?.headers ?? {}) as Record<string, string>;
      calls.push({
        url,
        method,
        body: init?.body as string | undefined,
        csrf: headers["X-CSRFToken"],
      });
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
const PORTFOLIOS = "/api/v1/portfolios";
const FIRST = `GET ${PORTFOLIOS}?limit=50&offset=0`;
const SECOND = `GET ${PORTFOLIOS}?limit=50&offset=50`;
const searchKey = (q: string) =>
  `GET /api/v1/assets?q=${encodeURIComponent(q)}&limit=20&offset=0`;

const portfolioCalls = () => calls.filter((c) => c.url.startsWith(PORTFOLIOS));

function renderAt(path = "/carteiras", state?: unknown) {
  const router = createMemoryRouter(routes, {
    initialEntries: [state === undefined ? path : { pathname: path, state }],
  });
  render(<RouterProvider router={router} />);
  return router;
}

async function flush(): Promise<void> {
  await act(async () => {
    for (let i = 0; i < 30; i += 1) await Promise.resolve();
  });
}

async function wait(ms: number): Promise<void> {
  await act(async () => {
    vi.advanceTimersByTime(ms);
  });
  await flush();
}

async function click(element: Element): Promise<void> {
  await act(async () => {
    fireEvent.click(element);
  });
  await flush();
}

const screenRoot = () =>
  document.querySelector('[data-screen="carteiras"]') as HTMLElement;
const banner = () => screen.getByRole("banner");
const navLink = () => {
  const bar = screen.queryByRole("banner");
  return bar === null
    ? null
    : within(bar).queryByRole("link", { name: TEXTOS["carteiras.nav"] });
};
const notice = () => document.querySelector("[data-signin-notice]");
const creation = () => document.querySelector('[data-part="criacao"]') as HTMLElement;
const nameInput = () =>
  within(creation()).getByLabelText(TEXTOS["carteiras.campo.nome"]) as HTMLInputElement;
const notionalInput = () =>
  within(creation()).getByLabelText(
    TEXTOS["carteiras.campo.valor"],
  ) as HTMLInputElement;
const pickerInput = () =>
  screen.getByRole("combobox", {
    name: TEXTOS["carteiras.seletor.rotulo"],
  }) as HTMLInputElement;
const weightInput = (ticker: string) =>
  screen.getByLabelText(TEXTOS["carteiras.peso.rotulo"](ticker)) as HTMLInputElement;
const editorRow = (ticker: string) =>
  document.querySelector(
    `[data-part="editor"] tr[data-ticker="${ticker}"]`,
  ) as HTMLElement;
const sum = () => document.querySelector('[data-part="soma"]') as HTMLElement;
const totalErrors = () =>
  [...document.querySelectorAll('[data-part="soma-erros"] .ruvor-field__error')].map(
    (e) => e.textContent,
  );
const option = (ticker: string) =>
  document.querySelector(`[role="option"][data-ticker="${ticker}"]`) as HTMLElement;
const submit = () => document.querySelector('[data-part="criar"]') as HTMLButtonElement;

/** As mensagens de erro de uma linha do editor: embaixo do nome e embaixo do peso. */
function rowMessages(ticker: string): { ticker: string[]; weight: string[] } {
  const [tickerCell, weightCell] = editorRow(ticker).querySelectorAll("td");
  const texts = (cell: Element) =>
    [...cell.querySelectorAll(".ruvor-field__error")].map((e) => e.textContent ?? "");
  return { ticker: texts(tickerCell), weight: texts(weightCell) };
}

async function openCreation(): Promise<void> {
  await click(screen.getByRole("button", { name: TEXTOS["carteiras.nova"] }));
}

/** Busca no seletor e escolhe o item pelo código. */
async function add(q: string, results: AssetItem[], ticker: string): Promise<void> {
  reply(searchKey(q), search(results));
  fireEvent.change(pickerInput(), { target: { value: q } });
  await wait(200);
  await click(option(ticker));
}

async function type(input: HTMLInputElement, value: string): Promise<void> {
  await act(async () => {
    fireEvent.change(input, { target: { value } });
  });
}

/** Abre a criação com o nome, o valor e três linhas com os pesos digitados. */
async function fillThree(
  weights: [string, string, string],
  name = "Bancos e energia",
  notional = "50.000,00",
): Promise<void> {
  await openCreation();
  await type(nameInput(), name);
  await type(notionalInput(), notional);
  await add("itub", [ITUB4], "ITUB4");
  await add("bbdc", [BBDC4], "BBDC4");
  await add("vale", [VALE3], "VALE3");
  await type(weightInput("ITUB4"), weights[0]);
  await type(weightInput("BBDC4"), weights[1]);
  await type(weightInput("VALE3"), weights[2]);
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  replies = {};
  reply(ME_KEY, ok(ME));
  reply(FIRST, list([BANCOS, EXPORTADORAS]));
  // biome-ignore lint/suspicious/noDocumentCookie: os pedidos mandam o token do cookie de verdade.
  document.cookie = "csrftoken=tok; path=/";
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  // biome-ignore lint/suspicious/noDocumentCookie: limpa o cookie gravado no beforeEach.
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("V-01 — a sessão e o item da barra", () => {
  it("carregando: o esqueleto, sem item na barra e sem nenhum pedido às carteiras", async () => {
    reply(ME_KEY, null);
    renderAt();
    await flush();
    expect(screenRoot().querySelector('[aria-busy="true"]')).not.toBeNull();
    expect(navLink()).toBeNull();
    expect(notice()).toBeNull();
    expect(portfolioCalls()).toEqual([]);
  });

  it("anônimo: o aviso 'para quem entrou', sem ended, com o next; nenhum pedido; sem item", async () => {
    reply(ME_KEY, fail(401, "not_authenticated"));
    renderAt();
    await flush();
    expect(notice()?.getAttribute("data-signin-notice")).toBe("required");
    expect(screen.getByText(TEXTOS["conta.aviso.paraQuemEntrou"])).toBeDefined();
    expect(screen.queryByText(TEXTOS["conta.aviso.terminou"])).toBeNull();
    const entrar = within(notice() as HTMLElement).getByRole("link", {
      name: TEXTOS["conta.entrar"],
    });
    expect(entrar.getAttribute("href")).toBe("/entrar?next=%2Fcarteiras");
    expect(portfolioCalls()).toEqual([]);
    expect(navLink()).toBeNull();
    expect(banner().querySelector("nav")).toBeNull();
  });

  it("logado: 'Carteiras' logo depois da marca, corrente em /carteiras; a conta segue por último", async () => {
    renderAt();
    await flush();
    const link = navLink() as HTMLElement;
    expect(link.getAttribute("href")).toBe("/carteiras");
    expect(link.getAttribute("aria-current")).toBe("page");
    expect(link.classList.contains("ruvor-nav__link--on")).toBe(true);
    const nav = link.closest("nav") as HTMLElement;
    expect(nav.className).toBe("ruvor-nav ruvor-nav--account");
    expect(nav.getAttribute("aria-label")).toBe(TEXTOS["carteiras.nav.rotulo"]);
    const children = [...banner().children];
    expect(children[0].classList.contains("ruvor-brand")).toBe(true);
    expect(children[1]).toBe(nav);
    expect(children[2].classList.contains("ruvor-topbar__search")).toBe(true);
    const prefs = banner().querySelector(".ruvor-topbar__prefs") as HTMLElement;
    expect(prefs.lastElementChild?.classList.contains("ruvor-topbar__account")).toBe(
      true,
    );
  });

  it("logado fora das carteiras: o item, sem a marca de corrente", async () => {
    reply("GET /api/v1/assets?has_risk=true&limit=8", search([]));
    renderAt("/");
    await flush();
    const link = navLink() as HTMLElement;
    expect(link.getAttribute("aria-current")).toBeNull();
    expect(link.classList.contains("ruvor-nav__link--on")).toBe(false);
  });

  it("com a senha provisória por trocar: a troca obrigatória, sem item e sem pedido", async () => {
    reply(ME_KEY, ok({ ...ME, must_change_password: true }));
    renderAt();
    await flush();
    expect(document.querySelector("header")).toBeNull();
    expect(navLink()).toBeNull();
    expect(portfolioCalls()).toEqual([]);
  });

  it("a frase da organização só na que não é pessoal", async () => {
    renderAt();
    await flush();
    expect(
      screen.getByText(TEXTOS["carteiras.sub.organizacao"](ME.organization.name)),
    ).toBeDefined();
    cleanup();
    reply(ME_KEY, ok(PERSONAL));
    renderAt();
    await flush();
    expect(document.querySelector(".ruvor-portfolios-head__org")).toBeNull();
  });
});

describe("V-02 — a lista", () => {
  it("um GET portfolios?limit=50&offset=0; as linhas na ordem da API, com cada coluna", async () => {
    renderAt();
    await flush();
    expect(portfolioCalls()).toEqual([
      { url: `${PORTFOLIOS}?limit=50&offset=0`, method: "GET", body: undefined },
    ]);
    const rows = [...document.querySelectorAll('[data-part="lista"] tbody tr')];
    expect(rows.map((r) => r.getAttribute("data-id"))).toEqual([
      BANCOS.id,
      EXPORTADORAS.id,
    ]);
    const cells = (r: Element) =>
      [...r.querySelectorAll("td")].map((td) => td.textContent);
    expect(cells(rows[0])).toEqual([
      "Bancos e energia",
      TEXTOS["carteiras.acoes"](4),
      "3",
      "R$ 50.000,00",
      formatInstant(BANCOS.version_created_at),
    ]);
    expect(cells(rows[1])[3]).toBe(TEXTOS["carteiras.semValor"]);
    expect(
      within(rows[0] as HTMLElement)
        .getByRole("link", { name: "Bancos e energia" })
        .getAttribute("href"),
    ).toBe(`/carteiras/${BANCOS.id}`);
    expect(screen.getByText(TEXTOS["carteiras.lista.contagem"](2))).toBeDefined();
    expect(document.querySelector('[data-part="mais"]')).toBeNull();
    expect(
      screen.getByRole("button", { name: TEXTOS["carteiras.nova"] }),
    ).toBeDefined();
  });

  it("carregando: o esqueleto da lista, sem 'Nova carteira'", async () => {
    reply(FIRST, null);
    renderAt();
    await flush();
    const panel = document.querySelector('[data-part="lista"]') as HTMLElement;
    expect(panel.getAttribute("aria-busy")).toBe("true");
    expect(panel.querySelectorAll(".ruvor-portfolios__skel")).toHaveLength(3);
    expect(screen.queryByRole("button", { name: TEXTOS["carteiras.nova"] })).toBeNull();
  });

  it("vazia: o convite a criar a primeira, que abre a criação", async () => {
    reply(FIRST, list([]));
    renderAt();
    await flush();
    expect(screen.getByText(TEXTOS["carteiras.lista.vazia.titulo"])).toBeDefined();
    expect(screen.queryByRole("button", { name: TEXTOS["carteiras.nova"] })).toBeNull();
    await click(
      screen.getByRole("button", { name: TEXTOS["carteiras.lista.vazia.criar"] }),
    );
    expect(creation()).not.toBeNull();
    expect(document.activeElement).toBe(nameInput());
    expect(
      screen.queryByRole("button", { name: TEXTOS["carteiras.lista.vazia.criar"] }),
    ).toBeNull();
  });

  it("erro: a mensagem com 'Tentar de novo', que pede de novo", async () => {
    reply(FIRST, fail(500, "internal_error"), list([BANCOS]));
    renderAt();
    await flush();
    const alert = document.querySelector('[data-part="lista-erro"]') as HTMLElement;
    expect(alert.getAttribute("role")).toBe("alert");
    expect(
      within(alert).getByText(TEXTOS["carteiras.lista.erro.titulo"]),
    ).toBeDefined();
    expect(screen.queryByText(API_MESSAGE)).toBeNull();
    await click(
      within(alert).getByRole("button", { name: TEXTOS["carteiras.tentarDeNovo"] }),
    );
    expect(portfolioCalls()).toHaveLength(2);
    expect(document.querySelectorAll('[data-part="lista"] tbody tr')).toHaveLength(1);
  });

  it("'Mostrar mais' pede o offset seguinte e acrescenta", async () => {
    const first = Array.from({ length: 50 }, (_, i) => portfolio(i + 1));
    const rest = Array.from({ length: 7 }, (_, i) => portfolio(i + 51));
    reply(FIRST, list(first, 57));
    reply(SECOND, list(rest, 57, 50));
    renderAt();
    await flush();
    const more = document.querySelector('[data-part="mais"]') as HTMLElement;
    expect(within(more).getByText(TEXTOS["carteiras.mostrando"](50, 57))).toBeDefined();
    await click(
      within(more).getByRole("button", { name: TEXTOS["carteiras.mostrarMais"] }),
    );
    expect(portfolioCalls().map((c) => c.url)).toEqual([
      `${PORTFOLIOS}?limit=50&offset=0`,
      `${PORTFOLIOS}?limit=50&offset=50`,
    ]);
    expect(document.querySelectorAll('[data-part="lista"] tbody tr')).toHaveLength(57);
    expect(document.querySelector('[data-part="mais"]')).toBeNull();
  });

  it("'Mostrar mais' que falha: as carregadas ficam, e 'Tentar de novo' pede o mesmo offset", async () => {
    const first = Array.from({ length: 50 }, (_, i) => portfolio(i + 1));
    reply(FIRST, list(first, 57));
    reply(SECOND, fail(503, "service_unavailable"), list([portfolio(51)], 57, 50));
    renderAt();
    await flush();
    await click(screen.getByRole("button", { name: TEXTOS["carteiras.mostrarMais"] }));
    expect(document.querySelectorAll('[data-part="lista"] tbody tr')).toHaveLength(50);
    expect(screen.getByRole("alert").textContent).toBe(TEXTOS["carteiras.maisErro"]);
    await click(screen.getByRole("button", { name: TEXTOS["carteiras.tentarDeNovo"] }));
    expect(
      portfolioCalls()
        .map((c) => c.url)
        .slice(1),
    ).toEqual([`${PORTFOLIOS}?limit=50&offset=50`, `${PORTFOLIOS}?limit=50&offset=50`]);
    expect(document.querySelectorAll('[data-part="lista"] tbody tr')).toHaveLength(51);
  });

  it("401 na lista: a sessão termina, o aviso no lugar da lista, e a barra perde o item", async () => {
    reply(FIRST, fail(401, "not_authenticated"));
    renderAt();
    await flush();
    expect(notice()?.getAttribute("data-signin-notice")).toBe("ended");
    expect(navLink()).toBeNull();
    expect(
      within(banner()).getByRole("link", { name: TEXTOS["conta.entrar"] }),
    ).toBeDefined();
  });

  it("depois de arquivar: a mensagem do RF-08 no topo", async () => {
    renderAt("/carteiras", { archived: "Exportadoras" });
    await flush();
    const status = document.querySelector('[data-part="arquivada"]') as HTMLElement;
    expect(status.getAttribute("role")).toBe("status");
    expect(status.textContent).toBe(TEXTOS["carteiras.arquivada"]("Exportadoras"));
  });
});

describe("V-04 — o seletor de ação", () => {
  it("busca no catálogo depois da pausa, e só a ação ativa fora da composição é escolhível", async () => {
    renderAt();
    await flush();
    await openCreation();
    await add("itub", [ITUB4], "ITUB4");
    reply(searchKey("b"), search([BBAS3, BIDI4, IBOV, ITUB4], 31));
    fireEvent.change(pickerInput(), { target: { value: "b" } });
    await wait(199);
    expect(calls.filter((c) => c.url.includes("q=b&"))).toHaveLength(0);
    await wait(1);
    expect(calls.filter((c) => c.url.includes("q=b&"))).toHaveLength(1);

    const reasons = (ticker: string) => ({
      disabled: option(ticker).getAttribute("aria-disabled"),
      why: option(ticker).querySelector(".ruvor-pick__why")?.textContent ?? null,
    });
    expect(reasons("BBAS3")).toEqual({ disabled: null, why: null });
    expect(reasons("BIDI4")).toEqual({
      disabled: "true",
      why: TEXTOS["carteiras.seletor.motivo.inativa"],
    });
    expect(reasons("IBOV")).toEqual({
      disabled: "true",
      why: TEXTOS["carteiras.seletor.motivo.indice"],
    });
    expect(reasons("ITUB4")).toEqual({
      disabled: "true",
      why: TEXTOS["carteiras.seletor.motivo.naComposicao"],
    });
    expect(screen.getByText(TEXTOS["busca.suspensaRodape"](4, 31))).toBeDefined();
    expect(document.querySelector('[data-part="nenhuma-serve"]')).toBeNull();

    // O clique num desabilitado não faz nada; num escolhível, acrescenta no fim.
    await click(option("IBOV"));
    await click(option("BIDI4"));
    expect(editorRow("IBOV")).toBeNull();
    expect(editorRow("BIDI4")).toBeNull();
    await click(option("BBAS3"));
    const tickers = [...document.querySelectorAll('[data-part="editor"] tbody tr')].map(
      (r) => r.getAttribute("data-ticker"),
    );
    expect(tickers).toEqual(["ITUB4", "BBAS3"]);
    expect(pickerInput().value).toBe("");
    expect(document.querySelector('[role="listbox"]')).toBeNull();
    expect(document.activeElement).toBe(weightInput("BBAS3"));
  });

  it("pelo teclado: as setas passam pelos desabilitados, e o Enter neles não faz nada", async () => {
    renderAt();
    await flush();
    await openCreation();
    reply(searchKey("b"), search([IBOV, BBAS3]));
    fireEvent.change(pickerInput(), { target: { value: "b" } });
    await wait(200);
    // Sem destaque, o Enter tenta o primeiro: o índice, que não entra.
    await act(async () => {
      fireEvent.keyDown(pickerInput(), { key: "Enter" });
    });
    expect(editorRow("IBOV")).toBeNull();
    await act(async () => {
      fireEvent.keyDown(pickerInput(), { key: "ArrowDown" });
    });
    expect(pickerInput().getAttribute("aria-activedescendant")).toBe(option("IBOV").id);
    await act(async () => {
      fireEvent.keyDown(pickerInput(), { key: "Enter" });
    });
    expect(editorRow("IBOV")).toBeNull();
    await act(async () => {
      fireEvent.keyDown(pickerInput(), { key: "ArrowDown" });
    });
    await act(async () => {
      fireEvent.keyDown(pickerInput(), { key: "Enter" });
    });
    expect(editorRow("BBAS3")).not.toBeNull();
  });

  it("a página só com o que não serve diz isso e pede um termo mais preciso", async () => {
    renderAt();
    await flush();
    await openCreation();
    reply(searchKey("IBOV"), search([IBOV, BIDI4]));
    fireEvent.change(pickerInput(), { target: { value: "IBOV" } });
    await wait(200);
    const msg = document.querySelector('[data-part="nenhuma-serve"]') as HTMLElement;
    expect(msg.textContent).toBe(
      TEXTOS["carteiras.seletor.nenhumaServe"]("IBOV") +
        TEXTOS["carteiras.seletor.nenhumaServeDica"],
    );
  });
});

describe("V-03 — a criação com o editor", () => {
  it("a soma ao vivo em centésimos: 0,01 + 65,40 + 34,59 fecha em 100,00", async () => {
    renderAt();
    await flush();
    await fillThree(["0,01", "65,40", "34,59"]);
    expect(sum().querySelector(".ruvor-weight-sum__value")?.textContent).toBe(
      "100,00%",
    );
    expect(sum().textContent).toContain(TEXTOS["carteiras.soma.exata"]);
  });

  it("abaixo e acima, e o peso que ainda não é número fica fora da soma", async () => {
    renderAt();
    await flush();
    await fillThree(["33,33", "33,33", "33,33"]);
    expect(sum().textContent).toContain(TEXTOS["carteiras.soma.abaixo"]("0,01"));
    await type(weightInput("VALE3"), "33,84");
    expect(sum().textContent).toContain(TEXTOS["carteiras.soma.acima"]("0,50"));
    await type(weightInput("VALE3"), "abc");
    expect(sum().querySelector(".ruvor-weight-sum__value")?.textContent).toBe("66,66%");
    expect(sum().textContent).toContain(TEXTOS["carteiras.soma.foraDaSoma"](1));
  });

  it("o campo guarda o texto como foi digitado — ao digitar, ao sair e ao enviar", async () => {
    reply(`POST ${PORTFOLIOS}`, null);
    renderAt();
    await flush();
    await fillThree(["5,", "33.4", " 61,6 "]);
    for (const ticker of ["ITUB4", "BBDC4", "VALE3"]) {
      await act(async () => {
        fireEvent.blur(weightInput(ticker));
      });
    }
    expect(weightInput("ITUB4").value).toBe("5,");
    expect(weightInput("BBDC4").value).toBe("33.4");
    expect(weightInput("VALE3").value).toBe(" 61,6 ");
    expect(sum().textContent).toContain(TEXTOS["carteiras.soma.exata"]);
    await click(submit());
    expect(weightInput("ITUB4").value).toBe("5,");
    expect(weightInput("BBDC4").value).toBe("33.4");
    expect(weightInput("VALE3").value).toBe(" 61,6 ");
    const post = calls.find((c) => c.method === "POST") as Call;
    expect(JSON.parse(post.body as string).holdings).toEqual([
      { ticker: "ITUB4", weight: "5.00" },
      { ticker: "BBDC4", weight: "33.40" },
      { ticker: "VALE3", weight: "61.60" },
    ]);
  });

  it("o POST com o corpo e o CSRF; o 201 vai à página da carteira nova", async () => {
    const created = portfolio(9, { name: "Bancos e energia" });
    reply(`POST ${PORTFOLIOS}`, ok({ portfolio: created }, 201));
    const router = renderAt();
    await flush();
    await fillThree(["0,01", "65,40", "34,59"], "  Bancos e energia  ");
    await click(submit());
    const posts = calls.filter((c) => c.method === "POST");
    expect(posts).toHaveLength(1);
    expect(posts[0].url).toBe(PORTFOLIOS);
    expect(posts[0].csrf).toBe("tok");
    expect(JSON.parse(posts[0].body as string)).toEqual({
      name: "Bancos e energia",
      notional: "50000.00",
      holdings: [
        { ticker: "ITUB4", weight: "0.01" },
        { ticker: "BBDC4", weight: "65.40" },
        { ticker: "VALE3", weight: "34.59" },
      ],
    });
    expect(router.state.location.pathname).toBe(`/carteiras/${created.id}`);
  });

  it("sem valor: notional nulo", async () => {
    reply(`POST ${PORTFOLIOS}`, null);
    renderAt();
    await flush();
    await fillThree(["50", "25", "25"], "Sem valor", "");
    await click(submit());
    const post = calls.find((c) => c.method === "POST") as Call;
    expect(JSON.parse(post.body as string).notional).toBeNull();
  });

  it("as conferências do cliente: o nome, o valor, os pesos — sem pedido, e o foco no primeiro", async () => {
    renderAt();
    await flush();
    await openCreation();
    await type(nameInput(), "   ");
    await type(notionalInput(), "10.000,999");
    await add("petr", [PETR4], "PETR4");
    await add("vale", [VALE3], "VALE3");
    await add("itub", [ITUB4], "ITUB4");
    await type(weightInput("PETR4"), "12,345");
    await type(weightInput("VALE3"), "0");
    await type(weightInput("ITUB4"), "150");
    await click(submit());
    expect(calls.filter((c) => c.method === "POST")).toHaveLength(0);
    const errorOf = (input: HTMLInputElement) =>
      document.getElementById(
        (input.getAttribute("aria-describedby") ?? "").split(" ").pop() ?? "",
      )?.textContent;
    expect(nameInput().getAttribute("aria-invalid")).toBe("true");
    expect(errorOf(nameInput())).toBe(TEXTOS["carteiras.erro.nome"]);
    expect(errorOf(notionalInput())).toBe(TEXTOS["carteiras.erro.valor"]);
    expect(rowMessages("PETR4").weight).toEqual([TEXTOS["carteiras.erro.pesoFormato"]]);
    expect(rowMessages("VALE3").weight).toEqual([TEXTOS["carteiras.erro.peso"]]);
    expect(rowMessages("ITUB4").weight).toEqual([TEXTOS["carteiras.erro.peso"]]);
    // A soma só se confere com todos os pesos números.
    expect(totalErrors()).toEqual([]);
    expect(document.activeElement).toBe(nameInput());
    expect(weightInput("PETR4").value).toBe("12,345");
  });

  it("uma ação só e a soma fora de 100,00: na linha da soma", async () => {
    renderAt();
    await flush();
    await openCreation();
    await type(nameInput(), "Uma ação");
    await add("petr", [PETR4], "PETR4");
    await type(weightInput("PETR4"), "99,99");
    await click(submit());
    expect(totalErrors()).toEqual([
      TEXTOS["carteiras.erro.contagem"](1),
      TEXTOS["carteiras.erro.soma"]("99,99"),
    ]);
    expect(calls.filter((c) => c.method === "POST")).toHaveLength(0);
  });

  it("o formato do peso aparece ao sair do campo", async () => {
    renderAt();
    await flush();
    await openCreation();
    await add("petr", [PETR4], "PETR4");
    await type(weightInput("PETR4"), "1,234");
    await act(async () => {
      fireEvent.blur(weightInput("PETR4"));
    });
    expect(rowMessages("PETR4").weight).toEqual([TEXTOS["carteiras.erro.pesoFormato"]]);
    await type(weightInput("PETR4"), "1,23");
    await act(async () => {
      fireEvent.blur(weightInput("PETR4"));
    });
    expect(rowMessages("PETR4").weight).toEqual([]);
  });

  it("cada reason de items na linha do seu index: os da ação embaixo do nome, o do peso embaixo do peso", async () => {
    reply(
      `POST ${PORTFOLIOS}`,
      fail(400, "invalid_holdings", {
        reason: "items",
        items: [
          { index: 0, ticker: "ITUB4", reason: "not_a_stock" },
          { index: 1, ticker: "BBDC4", reason: "inactive" },
          { index: 2, ticker: "VALE3", reason: "weight_out_of_range" },
        ],
      }),
    );
    renderAt();
    await flush();
    await fillThree(["0,01", "65,40", "34,59"]);
    await click(submit());
    expect(rowMessages("ITUB4")).toEqual({
      ticker: [TEXTOS["carteiras.erro.naoAcao"]],
      weight: [],
    });
    expect(rowMessages("BBDC4")).toEqual({
      ticker: [TEXTOS["carteiras.erro.inativa"]],
      weight: [],
    });
    expect(rowMessages("VALE3")).toEqual({
      ticker: [],
      weight: [TEXTOS["carteiras.erro.peso"]],
    });
    expect(screen.queryByText(API_MESSAGE)).toBeNull();
    expect(nameInput().value).toBe("Bancos e energia");
  });

  it.each([
    ["duplicate", "carteiras.erro.repetida"],
    ["unknown_ticker", "carteiras.erro.desconhecida"],
  ] as const)("items %s: embaixo do nome da linha", async (reason, key) => {
    reply(
      `POST ${PORTFOLIOS}`,
      fail(400, "invalid_holdings", {
        reason: "items",
        items: [{ index: 1, ticker: "BBDC4", reason }],
      }),
    );
    renderAt();
    await flush();
    await fillThree(["0,01", "65,40", "34,59"]);
    await click(submit());
    expect(rowMessages("BBDC4").ticker).toEqual([TEXTOS[key]]);
    expect(rowMessages("ITUB4")).toEqual({ ticker: [], weight: [] });
  });

  it("count_out_of_range e weights_sum: na linha da soma, pelo details", async () => {
    reply(
      `POST ${PORTFOLIOS}`,
      fail(400, "invalid_holdings", { reason: "count_out_of_range", count: 21 }),
      fail(400, "invalid_holdings", { reason: "weights_sum", sum: "99.99" }),
    );
    renderAt();
    await flush();
    await fillThree(["0,01", "65,40", "34,59"]);
    await click(submit());
    expect(totalErrors()).toEqual([TEXTOS["carteiras.erro.contagem"](21)]);
    await click(submit());
    expect(totalErrors()).toEqual([TEXTOS["carteiras.erro.soma"]("99,99")]);
  });

  it.each([
    [
      "invalid_parameter",
      fail(400, "invalid_parameter", { fields: { holdings: ["x"] } }),
    ],
    [
      "reason fora da lista",
      fail(400, "invalid_holdings", { reason: "algo_novo", items: [] }),
    ],
    [
      "index fora da composição",
      fail(400, "invalid_holdings", {
        reason: "items",
        items: [{ index: 7, ticker: "X", reason: "duplicate" }],
      }),
    ],
  ])("%s: a mensagem geral da forma", async (_rotulo, response) => {
    reply(`POST ${PORTFOLIOS}`, response);
    renderAt();
    await flush();
    await fillThree(["0,01", "65,40", "34,59"]);
    await click(submit());
    expect(screen.getByRole("alert").textContent).toBe(TEXTOS["carteiras.erro.forma"]);
  });

  it.each([
    ["rede", "network" as Reply],
    ["5xx", fail(500, "internal_error")],
    ["429", fail(429, "too_many_requests", { wait_seconds: 3 })],
    ["csrf_failed", fail(403, "csrf_failed")],
  ])(
    "%s: a mensagem de envio no formulário, e o que foi digitado fica",
    async (_r, response) => {
      reply(`POST ${PORTFOLIOS}`, response);
      reply("GET /api/v1/auth/csrf", ok({}));
      renderAt();
      await flush();
      await fillThree(["0,01", "65,40", "34,59"]);
      await click(submit());
      expect(screen.getByRole("alert").textContent).toBe(
        TEXTOS["carteiras.erro.envio"],
      );
      expect(nameInput().value).toBe("Bancos e energia");
      expect(notionalInput().value).toBe("50.000,00");
      expect(weightInput("ITUB4").value).toBe("0,01");
      expect(submit().disabled).toBe(false);
    },
  );

  it("401 no envio: o aviso de sessão terminada no lugar dos botões; o formulário fica", async () => {
    reply(`POST ${PORTFOLIOS}`, fail(401, "not_authenticated"));
    renderAt();
    await flush();
    await fillThree(["0,01", "65,40", "34,59"]);
    await click(submit());
    expect(notice()?.getAttribute("data-signin-notice")).toBe("ended");
    expect(submit()).toBeNull();
    expect(nameInput().value).toBe("Bancos e energia");
    expect(weightInput("BBDC4").value).toBe("65,40");
    expect(navLink()).toBeNull();
    expect(document.querySelectorAll('[data-part="lista"] tbody tr')).toHaveLength(2);
  });

  it("'Cancelar' fecha e descarta", async () => {
    renderAt();
    await flush();
    await fillThree(["0,01", "65,40", "34,59"]);
    await click(screen.getByRole("button", { name: TEXTOS["carteiras.cancelar"] }));
    expect(creation()).toBeNull();
    await openCreation();
    expect(nameInput().value).toBe("");
    expect(editorRow("ITUB4")).toBeNull();
    expect(screen.getByText(TEXTOS["carteiras.editor.vazio"])).toBeDefined();
  });

  it("remover tira a linha, e a soma acompanha", async () => {
    renderAt();
    await flush();
    await fillThree(["0,01", "65,40", "34,59"]);
    await click(
      screen.getByRole("button", { name: TEXTOS["carteiras.remover"]("BBDC4") }),
    );
    expect(editorRow("BBDC4")).toBeNull();
    expect(sum().querySelector(".ruvor-weight-sum__value")?.textContent).toBe("34,60%");
  });
});
