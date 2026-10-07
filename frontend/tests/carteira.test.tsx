/**
 * M2.2b (T8), contra o `carteira.html` aprovado: V-05 (o `PATCH`, o `PUT` e o `DELETE` com corpo
 * e CSRF; "nada mudou" pela mesma `version`; "outra pessoa mudou" pela `version` > conhecida + 1;
 * o arquivamento com o diálogo e a volta à lista; a falha de cada escrita mantém o que estava) e
 * a parte do V-01 da página (a sessão; o 404 ao abrir e no meio do uso; o 401 ao abrir e numa
 * escrita, que deixa a página só leitura, sem nenhuma ação de escrita, com um aviso só).
 *
 * O `fetch` é um duplo que responde pelo método e pelo endereço; `null` deixa o pedido pendente.
 * O `<dialog>` é o dublê de `dubles.ts`.
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
import type { Portfolio } from "../src/api/types";
import { TEXTOS } from "../src/content/textos";
import { formatBrlText } from "../src/portfolio/notional";
import type { Me } from "../src/session/types";
import { instalarDublesDeNavegador, restaurarDublesDeNavegador } from "./dubles";

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

const ID = "3f6c2a9e-8d41-4b7a-9c35-1e2f0a7b6d58";

const BASE: Portfolio = {
  id: ID,
  name: "Bancos e energia",
  notional: "250000.00",
  version: 3,
  holdings: [
    { ticker: "BBAS3", name: "BANCO DO BRASIL S.A.", weight: "20.00" },
    { ticker: "ITUB4", name: "ITAU UNIBANCO HOLDING S.A.", weight: "35.00" },
    { ticker: "PETR4", name: "PETROLEO BRASILEIRO S.A. PETROBRAS", weight: "25.00" },
    {
      ticker: "TAEE11",
      name: "TRANSMISSORA ALIANÇA DE ENERGIA ELÉTRICA S.A.",
      weight: "20.00",
    },
  ],
  created_at: "2026-09-29T10:12:00-03:00",
  updated_at: "2026-10-02T16:41:00-03:00",
  // 19:41 em UTC: a tela mostra no fuso da B3, 16:41.
  version_created_at: "2026-10-02T19:41:00Z",
  created_by: { email: ME.email, name: ME.name },
};

/** A composição de `BASE` com outros pesos (a versão nova). */
function withWeights(weights: [string, string, string, string]): Portfolio["holdings"] {
  return BASE.holdings.map((h, i) => ({ ...h, weight: weights[i] }));
}

/** A mensagem que a API manda em todo erro destes testes: nunca pode aparecer na tela. */
const API_MESSAGE = "MENSAGEM CRUA DA API";

type Reply = { status: number; body: unknown } | "network" | null;

const ok = (body: unknown, status = 200): Reply => ({ status, body });
const one = (p: Portfolio): Reply => ok({ portfolio: p });
const fail = (status: number, code: string, details: object = {}): Reply => ({
  status,
  body: { error: { code, message: API_MESSAGE, details } },
});
const NO_CONTENT: Reply = { status: 204, body: undefined };

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
const URL_ONE = `${PORTFOLIOS}/${ID}`;
const GET_ONE = `GET ${URL_ONE}`;
const PATCH_ONE = `PATCH ${URL_ONE}`;
const PUT_ONE = `PUT ${URL_ONE}/holdings`;
const DELETE_ONE = `DELETE ${URL_ONE}`;
const LIST = `GET ${PORTFOLIOS}?limit=50&offset=0`;

const portfolioCalls = () => calls.filter((c) => c.url.startsWith(PORTFOLIOS));
const writes = () => portfolioCalls().filter((c) => c.method !== "GET");

function renderAt(path = `/carteiras/${ID}`) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(<RouterProvider router={router} />);
  return router;
}

async function microtasks(): Promise<void> {
  for (let i = 0; i < 30; i += 1) {
    await Promise.resolve();
  }
}

/** As promessas, e depois as tarefas na fila (o `close` do `<dialog>` chega numa tarefa). */
async function flush(): Promise<void> {
  await act(microtasks);
  await act(async () => {
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
    await microtasks();
  });
}

async function click(element: Element): Promise<void> {
  await act(async () => {
    fireEvent.click(element);
  });
  await flush();
}

async function type(input: HTMLInputElement, value: string): Promise<void> {
  await act(async () => {
    fireEvent.change(input, { target: { value } });
  });
}

async function submit(element: Element): Promise<void> {
  await act(async () => {
    fireEvent.submit(element);
  });
  await flush();
}

async function key(element: Element, name: string): Promise<void> {
  await act(async () => {
    fireEvent.keyDown(element, { key: name });
  });
  await flush();
}

async function openPage(p: Portfolio = BASE): Promise<void> {
  reply(GET_ONE, one(p));
  renderAt();
  await flush();
}

const root = () => document.querySelector('[data-screen="carteira"]') as HTMLElement;
const part = (name: string) =>
  document.querySelector(`[data-part="${name}"]`) as HTMLElement | null;
const button = (name: string) =>
  screen.queryByRole("button", { name }) as HTMLButtonElement | null;
const dialogEl = () => document.querySelector("dialog") as HTMLDialogElement;
const isDialogOpen = () => dialogEl()?.hasAttribute("open") === true;
const inDialog = () => within(dialogEl());
const notices = () => [...document.querySelectorAll("[data-signin-notice]")];
const navLink = () => {
  const bar = screen.queryByRole("banner");
  return bar === null
    ? null
    : within(bar).queryByRole("link", { name: TEXTOS["carteiras.nav"] });
};
const weightInput = (ticker: string) =>
  screen.getByLabelText(TEXTOS["carteiras.peso.rotulo"](ticker)) as HTMLInputElement;
const readRows = () =>
  [...(part("composicao")?.querySelectorAll("tbody tr") ?? [])].map((tr) =>
    [...tr.querySelectorAll("td")].map((td) => td.textContent),
  );
const failures = () =>
  [...document.querySelectorAll('[data-part="falha"]')].map((e) => e.textContent);
const reply1 = () => part("resposta");

/** Os botões de escrita da página (fora do diálogo). */
const WRITE_LABELS: readonly string[] = [
  TEXTOS["carteira.nome.mudar"],
  TEXTOS["carteira.arquivar"],
  TEXTOS["carteira.valor.mudar"],
  TEXTOS["carteira.valor.informar"],
  TEXTOS["carteira.valor.tirar"],
  TEXTOS["carteira.composicao.editar"],
  TEXTOS["carteira.composicao.salvar"],
  TEXTOS["carteira.salvar"],
  TEXTOS["carteiras.cancelar"],
];
const pageWriteButtons = () =>
  [...root().querySelectorAll("button")]
    .filter((b) => !b.closest("dialog"))
    .map((b) => b.textContent ?? "")
    .filter((t) => WRITE_LABELS.includes(t));

beforeEach(() => {
  replies = {};
  reply(ME_KEY, ok(ME));
  reply(LIST, ok({ count: 0, limit: 50, offset: 0, results: [] }));
  // biome-ignore lint/suspicious/noDocumentCookie: os pedidos mandam o token do cookie de verdade.
  document.cookie = "csrftoken=tok; path=/";
  stubFetch();
  instalarDublesDeNavegador();
});

afterEach(() => {
  cleanup();
  restaurarDublesDeNavegador();
  vi.unstubAllGlobals();
  // biome-ignore lint/suspicious/noDocumentCookie: limpa o cookie gravado no beforeEach.
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("V-01 — a sessão e os estados da página", () => {
  it("sessão carregando: o esqueleto, sem pedido às carteiras", async () => {
    reply(ME_KEY, null);
    renderAt();
    await flush();
    expect(root().querySelector('[aria-busy="true"]')).not.toBeNull();
    expect(within(root()).getByText(TEXTOS["carteira.carregando"])).toBeDefined();
    expect(portfolioCalls()).toEqual([]);
  });

  it("anônimo: o aviso para quem entrou, sem ended, com o next, sem pedido", async () => {
    reply(ME_KEY, fail(401, "not_authenticated"));
    renderAt();
    await flush();
    const n = notices();
    expect(n).toHaveLength(1);
    expect(n[0].getAttribute("data-signin-notice")).toBe("required");
    expect(
      within(n[0] as HTMLElement)
        .getByRole("link")
        .getAttribute("href"),
    ).toBe(`/entrar?next=${encodeURIComponent(`/carteiras/${ID}`)}`);
    expect(portfolioCalls()).toEqual([]);
    expect(navLink()).toBeNull();
  });

  it("a carteira: os fatos, a composição na ordem da API e nenhum pedido ao risco", async () => {
    await openPage();
    expect(
      screen.getByRole("heading", { level: 1, name: BASE.name }).dataset.part,
    ).toBe("nome");
    expect(part("valor")?.textContent).toBe(formatBrlText("250000.00"));
    expect(within(root()).getByText(TEXTOS["carteira.valor.nota.com"])).toBeDefined();
    expect(part("versao")?.textContent).toBe("3");
    expect(part("mudou-em")?.textContent).toBe(
      TEXTOS["carteira.mudouEm"]("02/10/2026", "16:41"),
    );
    const creator = within(root()).getByText(ME.name);
    expect(creator.getAttribute("title")).toBe(ME.email);
    expect(readRows()).toEqual([
      ["BBAS3BANCO DO BRASIL S.A.", "20,00%"],
      ["ITUB4ITAU UNIBANCO HOLDING S.A.", "35,00%"],
      ["PETR4PETROLEO BRASILEIRO S.A. PETROBRAS", "25,00%"],
      ["TAEE11TRANSMISSORA ALIANÇA DE ENERGIA ELÉTRICA S.A.", "20,00%"],
    ]);
    expect(part("composicao")?.querySelector("tfoot")?.textContent).toBe(
      `${TEXTOS["carteira.composicao.total"]}100,00%`,
    );
    expect(navLink()?.getAttribute("aria-current")).toBe("page");
    expect(portfolioCalls().map((c) => `${c.method} ${c.url}`)).toEqual([GET_ONE]);
    expect(calls.some((c) => c.url.includes("/risk"))).toBe(false);
  });

  it("sem valor: 'sem valor', a frase de só em %, e 'Informar um valor' sem 'Tirar'", async () => {
    await openPage({ ...BASE, notional: null });
    expect(part("valor")?.textContent).toBe(TEXTOS["carteiras.semValor"]);
    expect(within(root()).getByText(TEXTOS["carteira.valor.nota.sem"])).toBeDefined();
    expect(button(TEXTOS["carteira.valor.informar"])).not.toBeNull();
    expect(button(TEXTOS["carteira.valor.tirar"])).toBeNull();
  });

  it("o 404 ao abrir: 'Carteira não encontrada.', com o caminho de volta à lista", async () => {
    reply(GET_ONE, fail(404, "portfolio_not_found"));
    renderAt();
    await flush();
    const section = part("nao-encontrada") as HTMLElement;
    expect(
      within(section).getByRole("heading", {
        level: 1,
        name: TEXTOS["carteira.naoEncontrada.titulo"],
      }),
    ).toBeDefined();
    expect(
      within(section)
        .getByRole("link", { name: TEXTOS["carteira.naoEncontrada.voltar"] })
        .getAttribute("href"),
    ).toBe("/carteiras");
  });

  it("o 401 ao abrir: o aviso de sessão terminada no lugar da página", async () => {
    reply(GET_ONE, fail(401, "not_authenticated"));
    renderAt();
    await flush();
    const n = notices();
    expect(n).toHaveLength(1);
    expect(n[0].getAttribute("data-signin-notice")).toBe("ended");
    expect(screen.queryByRole("heading", { level: 1 })).toBeNull();
    expect(navLink()).toBeNull();
  });

  it("o erro ao abrir: a mensagem com 'Tentar de novo', que pede de novo", async () => {
    reply(GET_ONE, fail(500, "internal_error"), one(BASE));
    renderAt();
    await flush();
    expect(within(root()).getByText(TEXTOS["carteira.erro.titulo"])).toBeDefined();
    expect(root().textContent).not.toContain(API_MESSAGE);
    await click(button(TEXTOS["carteiras.tentarDeNovo"]) as HTMLButtonElement);
    expect(screen.getByRole("heading", { level: 1, name: BASE.name })).toBeDefined();
    expect(portfolioCalls().filter((c) => c.method === "GET")).toHaveLength(2);
  });

  it("o id que não é de uma carteira vai no caminho codificado, e o 404 decide", async () => {
    reply(`GET ${PORTFOLIOS}/x%2Fy`, fail(404, "portfolio_not_found"));
    renderAt("/carteiras/x%2Fy");
    await flush();
    expect(part("nao-encontrada")).not.toBeNull();
  });
});

describe("RF-08 — o nome no lugar (PATCH)", () => {
  async function openName(): Promise<HTMLInputElement> {
    await click(button(TEXTOS["carteira.nome.mudar"]) as HTMLButtonElement);
    return screen.getByLabelText(TEXTOS["carteira.nome.campo"]) as HTMLInputElement;
  }

  it("o PATCH com o nome aparado e o CSRF; o título passa a ser o da resposta", async () => {
    await openPage();
    const input = await openName();
    expect(input.value).toBe(BASE.name);
    expect(document.activeElement).toBe(input);
    reply(PATCH_ONE, one({ ...BASE, name: "Bancos, energia e transmissão" }));
    await type(input, "  Bancos, energia e transmissão  ");
    await submit(input.form as HTMLFormElement);
    expect(writes()).toEqual([
      {
        url: URL_ONE,
        method: "PATCH",
        body: JSON.stringify({ name: "Bancos, energia e transmissão" }),
        csrf: "tok",
      },
    ]);
    expect(
      screen.getByRole("heading", { level: 1, name: "Bancos, energia e transmissão" }),
    ).toBeDefined();
    expect(document.activeElement).toBe(button(TEXTOS["carteira.nome.mudar"]));
  });

  it("vazio: a mensagem no campo, sem pedido", async () => {
    await openPage();
    const input = await openName();
    await type(input, "   ");
    await submit(input.form as HTMLFormElement);
    expect(writes()).toEqual([]);
    expect(
      within(input.form as HTMLElement).getByText(TEXTOS["carteiras.erro.nome"]),
    ).toBeDefined();
    expect(input.getAttribute("aria-invalid")).toBe("true");
  });

  it("a falha (rede): a mensagem, o que foi digitado fica, e o nome de antes também", async () => {
    await openPage();
    const input = await openName();
    reply(PATCH_ONE, "network");
    await type(input, "Outro nome");
    await submit(input.form as HTMLFormElement);
    expect(failures()).toEqual([
      `${TEXTOS["carteira.erro.rede"]} ${TEXTOS["carteira.erro.mantido"]}`,
    ]);
    expect(input.value).toBe("Outro nome");
    await click(button(TEXTOS["carteiras.cancelar"]) as HTMLButtonElement);
    expect(screen.getByRole("heading", { level: 1, name: BASE.name })).toBeDefined();
  });

  it("o invalid_parameter com details.fields.name: a mensagem do campo, como chega", async () => {
    await openPage();
    const input = await openName();
    reply(
      PATCH_ONE,
      fail(400, "invalid_parameter", {
        fields: {
          name: ["Certifique-se de que este campo não tenha mais de 100 caracteres."],
        },
      }),
    );
    await type(input, "Outro nome");
    await submit(input.form as HTMLFormElement);
    expect(
      within(input.form as HTMLElement).getByText(
        "Certifique-se de que este campo não tenha mais de 100 caracteres.",
      ),
    ).toBeDefined();
    expect(failures()).toEqual([]);
  });

  it("o Esc cancela sem pedido e devolve o foco a 'Mudar o nome'", async () => {
    await openPage();
    const input = await openName();
    await type(input, "Outro");
    await key(input, "Escape");
    expect(screen.queryByLabelText(TEXTOS["carteira.nome.campo"])).toBeNull();
    expect(screen.getByRole("heading", { level: 1, name: BASE.name })).toBeDefined();
    expect(document.activeElement).toBe(button(TEXTOS["carteira.nome.mudar"]));
    expect(writes()).toEqual([]);
  });

  it("o 401: só leitura, com o digitado, nenhuma ação de escrita, um aviso só; o Esc não traz de volta", async () => {
    await openPage();
    const input = await openName();
    reply(PATCH_ONE, fail(401, "not_authenticated"));
    await type(input, "Outro nome");
    await submit(input.form as HTMLFormElement);
    expect(input.value).toBe("Outro nome");
    expect(input.readOnly).toBe(true);
    const n = notices();
    expect(n).toHaveLength(1);
    expect(n[0].getAttribute("data-signin-notice")).toBe("ended");
    expect((input.form as HTMLElement).contains(n[0])).toBe(true);
    expect(document.activeElement).toBe(within(n[0] as HTMLElement).getByRole("link"));
    expect(pageWriteButtons()).toEqual([]);
    await key(input, "Escape");
    expect(screen.getByLabelText(TEXTOS["carteira.nome.campo"])).toBe(input);
    expect(pageWriteButtons()).toEqual([]);
    expect(navLink()).toBeNull();
  });

  it("o 404: a página inteira vai a 'não encontrada'", async () => {
    await openPage();
    const input = await openName();
    reply(PATCH_ONE, fail(404, "portfolio_not_found"));
    await type(input, "Outro nome");
    await submit(input.form as HTMLFormElement);
    expect(part("nao-encontrada")).not.toBeNull();
  });
});

describe("RF-08 — o valor no lugar (PATCH)", () => {
  async function openValue(label: string = TEXTOS["carteira.valor.mudar"]) {
    await click(button(label) as HTMLButtonElement);
    return screen.getByLabelText(TEXTOS["carteira.valor.campo"]) as HTMLInputElement;
  }

  it("abre com o valor de agora; o PATCH leva o texto com ponto", async () => {
    await openPage();
    const input = await openValue();
    expect(input.value).toBe("250000,00");
    reply(PATCH_ONE, one({ ...BASE, notional: "300000.00" }));
    await type(input, "300.000,00");
    await submit(input.form as HTMLFormElement);
    expect(writes()).toEqual([
      {
        url: URL_ONE,
        method: "PATCH",
        body: JSON.stringify({ notional: "300000.00" }),
        csrf: "tok",
      },
    ]);
    expect(part("valor")?.textContent).toBe(formatBrlText("300000.00"));
  });

  it("fora da regra: a mensagem, sem pedido", async () => {
    await openPage();
    const input = await openValue();
    await type(input, "300000,555");
    await submit(input.form as HTMLFormElement);
    expect(writes()).toEqual([]);
    expect(
      within(input.form as HTMLElement).getByText(TEXTOS["carteiras.erro.valor"]),
    ).toBeDefined();
  });

  it("'Informar um valor' sem valor abre o campo vazio", async () => {
    await openPage({ ...BASE, notional: null });
    const input = await openValue(TEXTOS["carteira.valor.informar"]);
    expect(input.value).toBe("");
  });

  it("a falha do PATCH (429 com espera): a mensagem; o campo com o digitado", async () => {
    await openPage();
    const input = await openValue();
    reply(PATCH_ONE, fail(429, "too_many_requests", { wait_seconds: 12 }));
    await type(input, "300000");
    await submit(input.form as HTMLFormElement);
    expect(failures()).toEqual([
      `${TEXTOS["carteira.erro.muitos"](12)} ${TEXTOS["carteira.erro.mantido"]}`,
    ]);
    expect(input.value).toBe("300000");
  });

  it("o 401 no PATCH do valor: o campo só leitura com o digitado, o aviso nele, nenhuma escrita", async () => {
    await openPage();
    const input = await openValue();
    reply(PATCH_ONE, fail(401, "not_authenticated"));
    await type(input, "300000");
    await submit(input.form as HTMLFormElement);
    expect(input.value).toBe("300000");
    expect(input.readOnly).toBe(true);
    const n = notices();
    expect(n).toHaveLength(1);
    expect((input.form as HTMLElement).contains(n[0])).toBe(true);
    expect(pageWriteButtons()).toEqual([]);
    await key(input, "Escape");
    expect(screen.getByLabelText(TEXTOS["carteira.valor.campo"])).toBe(input);
  });

  it("'Tirar o valor': o PATCH com notional null, sem confirmação; o fato vira 'sem valor'", async () => {
    await openPage();
    reply(PATCH_ONE, one({ ...BASE, notional: null }));
    await click(button(TEXTOS["carteira.valor.tirar"]) as HTMLButtonElement);
    expect(writes()).toEqual([
      {
        url: URL_ONE,
        method: "PATCH",
        body: JSON.stringify({ notional: null }),
        csrf: "tok",
      },
    ]);
    expect(isDialogOpen()).toBe(false);
    expect(part("valor")?.textContent).toBe(TEXTOS["carteiras.semValor"]);
    expect(button(TEXTOS["carteira.valor.tirar"])).toBeNull();
  });

  it("'Tirar o valor' que falha (csrf_failed): o valor de antes fica, com a mensagem", async () => {
    await openPage();
    reply(PATCH_ONE, fail(403, "csrf_failed"));
    reply("GET /api/v1/auth/csrf", ok({}));
    await click(button(TEXTOS["carteira.valor.tirar"]) as HTMLButtonElement);
    expect(failures()).toEqual([
      `${TEXTOS["carteira.erro.csrf"]} ${TEXTOS["carteira.erro.mantido"]}`,
    ]);
    expect(part("valor")?.textContent).toBe(formatBrlText("250000.00"));
  });

  it("'Tirar o valor' com 401: o aviso no lugar das ações do fato, e nenhuma ação de escrita", async () => {
    await openPage();
    reply(PATCH_ONE, fail(401, "not_authenticated"));
    await click(button(TEXTOS["carteira.valor.tirar"]) as HTMLButtonElement);
    const n = notices();
    expect(n).toHaveLength(1);
    expect(n[0].closest("dd")).not.toBeNull();
    expect(pageWriteButtons()).toEqual([]);
    expect(part("valor")?.textContent).toBe(formatBrlText("250000.00"));
  });
});

describe("RF-07 — a composição no lugar (PUT)", () => {
  async function openEditor(): Promise<void> {
    await click(button(TEXTOS["carteira.composicao.editar"]) as HTMLButtonElement);
  }

  async function save(): Promise<void> {
    await submit(part("form-composicao") as HTMLElement);
  }

  it("abre com a composição corrente, cada peso como texto; o foco no primeiro peso", async () => {
    await openPage();
    await openEditor();
    expect(weightInput("BBAS3").value).toBe("20,00");
    expect(weightInput("TAEE11").value).toBe("20,00");
    expect(document.activeElement).toBe(weightInput("BBAS3"));
    expect(part("composicao")).toBeNull();
  });

  it("o PUT com os pesos em texto com ponto e o CSRF; a versão seguinte é 'salva'", async () => {
    await openPage();
    await openEditor();
    await type(weightInput("ITUB4"), "35,5");
    await type(weightInput("PETR4"), "24,50");
    expect(weightInput("ITUB4").value).toBe("35,5");
    const after = {
      ...BASE,
      version: 4,
      holdings: withWeights(["20.00", "35.50", "24.50", "20.00"]),
      version_created_at: "2026-10-03T14:05:00Z",
    };
    reply(PUT_ONE, one(after));
    await save();
    expect(writes()).toEqual([
      {
        url: `${URL_ONE}/holdings`,
        method: "PUT",
        body: JSON.stringify({
          holdings: [
            { ticker: "BBAS3", weight: "20.00" },
            { ticker: "ITUB4", weight: "35.50" },
            { ticker: "PETR4", weight: "24.50" },
            { ticker: "TAEE11", weight: "20.00" },
          ],
        }),
        csrf: "tok",
      },
    ]);
    expect(reply1()?.textContent).toBe(TEXTOS["carteira.composicao.salva"](4));
    expect(reply1()?.getAttribute("role")).toBe("status");
    expect(part("versao")?.textContent).toBe("4");
    expect(part("mudou-em")?.textContent).toBe(
      TEXTOS["carteira.mudouEm"]("03/10/2026", "11:05"),
    );
    expect(readRows()[1]).toEqual(["ITUB4ITAU UNIBANCO HOLDING S.A.", "35,50%"]);
    expect(document.activeElement).toBe(button(TEXTOS["carteira.composicao.editar"]));
  });

  it("a mesma version na resposta: 'nada mudou'", async () => {
    await openPage();
    await openEditor();
    await type(weightInput("ITUB4"), "35");
    reply(PUT_ONE, one(BASE));
    await save();
    expect(reply1()?.textContent).toBe(TEXTOS["carteira.composicao.nadaMudou"](3));
    expect(part("versao")?.textContent).toBe("3");
  });

  it("version > conhecida + 1: 'outra pessoa mudou', com a composição que ficou", async () => {
    await openPage();
    await openEditor();
    await type(weightInput("ITUB4"), "35,5");
    await type(weightInput("PETR4"), "24,5");
    const other = {
      ...BASE,
      version: 5,
      holdings: withWeights(["10.00", "45.00", "25.00", "20.00"]),
    };
    reply(PUT_ONE, one(other));
    await save();
    expect(reply1()?.textContent).toBe(TEXTOS["carteira.composicao.outraPessoa"](5));
    expect(reply1()?.getAttribute("role")).toBe("alert");
    expect(part("versao")?.textContent).toBe("5");
    expect(readRows()[0]).toEqual(["BBAS3BANCO DO BRASIL S.A.", "10,00%"]);
  });

  it("a mesma composição enviada, mas a version veio + 2: é 'outra pessoa', não 'nada mudou'", async () => {
    await openPage();
    await openEditor();
    reply(PUT_ONE, one({ ...BASE, version: 5 }));
    await save();
    expect(reply1()?.textContent).toBe(TEXTOS["carteira.composicao.outraPessoa"](5));
  });

  it("a conferência do cliente: a soma fora de 100,00 dá o motivo no total, sem pedido", async () => {
    await openPage();
    await openEditor();
    await type(weightInput("ITUB4"), "34");
    await save();
    expect(writes()).toEqual([]);
    expect(
      [
        ...document.querySelectorAll('[data-part="soma-erros"] .ruvor-field__error'),
      ].map((e) => e.textContent),
    ).toEqual([TEXTOS["carteiras.erro.soma"]("99,00")]);
  });

  it("o invalid_holdings com items: a mensagem na linha do index (inactive sob o código)", async () => {
    await openPage();
    await openEditor();
    reply(
      PUT_ONE,
      fail(400, "invalid_holdings", {
        reason: "items",
        items: [{ index: 3, ticker: "TAEE11", reason: "inactive" }],
      }),
    );
    await save();
    const row = document.querySelector(
      '[data-part="editor"] tr[data-ticker="TAEE11"]',
    ) as HTMLElement;
    expect(row.querySelector("td")?.textContent).toContain(
      TEXTOS["carteiras.erro.inativa"],
    );
    expect(failures()).toEqual([]);
  });

  it("o invalid_parameter de forma: a mensagem geral da página", async () => {
    await openPage();
    await openEditor();
    reply(PUT_ONE, fail(400, "invalid_parameter", { fields: { holdings: ["x"] } }));
    await save();
    expect(failures()).toEqual([
      `${TEXTOS["carteira.erro.forma"]} ${TEXTOS["carteira.erro.mantido"]}`,
    ]);
  });

  it("a falha (5xx): o editor aberto com o digitado; cancelando, a composição de antes", async () => {
    await openPage();
    await openEditor();
    await type(weightInput("ITUB4"), "35,5");
    await type(weightInput("PETR4"), "24,5");
    reply(PUT_ONE, fail(503, "internal_error"));
    await save();
    expect(failures()).toEqual([
      `${TEXTOS["carteira.erro.rede"]} ${TEXTOS["carteira.erro.mantido"]}`,
    ]);
    expect(weightInput("ITUB4").value).toBe("35,5");
    expect(part("versao")?.textContent).toBe("3");
    await click(button(TEXTOS["carteiras.cancelar"]) as HTMLButtonElement);
    expect(readRows()[1]).toEqual(["ITUB4ITAU UNIBANCO HOLDING S.A.", "35,00%"]);
    expect(document.activeElement).toBe(button(TEXTOS["carteira.composicao.editar"]));
  });

  it("'Cancelar' descarta, sem pedido", async () => {
    await openPage();
    await openEditor();
    await type(weightInput("ITUB4"), "99");
    await click(button(TEXTOS["carteiras.cancelar"]) as HTMLButtonElement);
    expect(writes()).toEqual([]);
    expect(readRows()[1]).toEqual(["ITUB4ITAU UNIBANCO HOLDING S.A.", "35,00%"]);
  });

  it("o 404 no meio do uso (outra pessoa arquivou): 'não encontrada'", async () => {
    await openPage();
    await openEditor();
    reply(PUT_ONE, fail(404, "portfolio_not_found"));
    await save();
    expect(part("nao-encontrada")).not.toBeNull();
    expect(part("form-composicao")).toBeNull();
  });

  it("o 401: o editor à vista, travado, com o digitado; o aviso no lugar das ações; nenhuma escrita", async () => {
    await openPage();
    await openEditor();
    await type(weightInput("ITUB4"), "35,5");
    await type(weightInput("PETR4"), "24,5");
    reply(PUT_ONE, fail(401, "not_authenticated"));
    await save();
    expect(weightInput("ITUB4").value).toBe("35,5");
    expect(weightInput("ITUB4").disabled).toBe(true);
    const n = notices();
    expect(n).toHaveLength(1);
    expect((part("form-composicao") as HTMLElement).contains(n[0])).toBe(true);
    expect(pageWriteButtons()).toEqual([]);
    expect(navLink()).toBeNull();
  });
});

describe("RF-08 — o arquivamento (DELETE)", () => {
  async function openArchive(): Promise<void> {
    await click(button(TEXTOS["carteira.arquivar"]) as HTMLButtonElement);
  }
  const confirm = () =>
    inDialog().getByRole("button", { name: TEXTOS["carteira.arquivar.confirmar"] });

  it("'Arquivar' abre o diálogo com o efeito dito, sem pedido; 'Cancelar' fecha sem pedido", async () => {
    await openPage();
    await openArchive();
    expect(isDialogOpen()).toBe(true);
    expect(
      inDialog().getByRole("heading", {
        name: TEXTOS["carteira.arquivar.titulo"](BASE.name),
      }),
    ).toBeDefined();
    expect(inDialog().getByText(TEXTOS["carteira.arquivar.texto"])).toBeDefined();
    expect(inDialog().getByText(TEXTOS["carteira.arquivar.semVolta"])).toBeDefined();
    expect(writes()).toEqual([]);
    await click(inDialog().getByRole("button", { name: TEXTOS["carteiras.cancelar"] }));
    expect(isDialogOpen()).toBe(false);
    expect(writes()).toEqual([]);
    expect(document.activeElement).toBe(button(TEXTOS["carteira.arquivar"]));
  });

  it("confirmado: o DELETE com o CSRF, e a volta à lista dizendo que foi arquivada", async () => {
    await openPage();
    await openArchive();
    reply(DELETE_ONE, NO_CONTENT);
    await click(confirm());
    expect(writes()).toEqual([
      { url: URL_ONE, method: "DELETE", body: undefined, csrf: "tok" },
    ]);
    const archived = part("arquivada") as HTMLElement;
    expect(archived.textContent).toBe(TEXTOS["carteiras.arquivada"](BASE.name));
    expect(document.querySelector('[data-screen="carteiras"]')).not.toBeNull();
  });

  it("a falha (rede): o diálogo continua, com a mensagem, e a carteira também", async () => {
    await openPage();
    await openArchive();
    reply(DELETE_ONE, "network");
    await click(confirm());
    expect(isDialogOpen()).toBe(true);
    expect(
      [...dialogEl().querySelectorAll('[data-part="falha"]')].map((e) => e.textContent),
    ).toEqual([`${TEXTOS["carteira.erro.rede"]} ${TEXTOS["carteira.erro.mantido"]}`]);
    expect(confirm()).toBeDefined();
    expect(screen.getByRole("heading", { level: 1, name: BASE.name })).toBeDefined();
  });

  it("o 404 (outra pessoa já arquivou): o diálogo some e a página vai a 'não encontrada'", async () => {
    await openPage();
    await openArchive();
    reply(DELETE_ONE, fail(404, "portfolio_not_found"));
    await click(confirm());
    expect(part("nao-encontrada")).not.toBeNull();
    expect(document.querySelector("dialog")).toBeNull();
  });

  it("o 401: o aviso no diálogo e 'Fechar'; fechado, o aviso no lugar de 'Arquivar' e nenhuma escrita", async () => {
    await openPage();
    await openArchive();
    reply(DELETE_ONE, fail(401, "not_authenticated"));
    await click(confirm());
    expect(isDialogOpen()).toBe(true);
    expect(
      dialogEl()
        .querySelector("[data-signin-notice]")
        ?.getAttribute("data-signin-notice"),
    ).toBe("ended");
    expect(
      inDialog().queryByRole("button", { name: TEXTOS["carteiras.cancelar"] }),
    ).toBeNull();
    expect(inDialog().queryByText(TEXTOS["carteira.arquivar.texto"])).toBeNull();
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.confirmar.fechar"] }),
    );
    expect(isDialogOpen()).toBe(false);
    const n = notices();
    expect(n).toHaveLength(1);
    expect(n[0].closest(".ruvor-portfolio-top__actions")).not.toBeNull();
    expect(document.activeElement).toBe(within(n[0] as HTMLElement).getByRole("link"));
    expect(pageWriteButtons()).toEqual([]);
    expect(writes()).toHaveLength(1);
  });
});
