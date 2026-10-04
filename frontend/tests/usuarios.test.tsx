/**
 * V-10 (RF-11 a RF-14) e a parte do diálogo do V-12, contra o `usuarios.html` aprovado (o papel
 * `admin` como "Administração"): a lista paginada — 50 por página, "Mostrar mais" sem repetir
 * e-mail —, a própria linha marcada "você" e **sem** "Desativar" nem "Nova senha provisória";
 * os casos do RF-12 pelo `me` antes do pedido e pelo `code` depois; criar → o diálogo com a
 * senha, copiar pelo `navigator.clipboard`, a senha fora do DOM depois de fechar e **a primeira
 * página relida**; cada ação com a confirmação e o `PATCH`/`POST` certo, com o e-mail
 * codificado; `last_admin`, `user_not_found`; rebaixar a si mesma → `auth/me` relido e o caso
 * "membro"; o 401 no lugar da ação; e **o foco devolvido explicitamente** ao fechar o diálogo.
 *
 * O `fetch` é um duplo que responde pelo endereço e pelo método; `null` deixa o pedido pendente.
 * O `<dialog>` e a área de transferência são os dublês de `dubles.ts`.
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
import { TEXTOS } from "../src/content/textos";
import type { Me, OrgUser } from "../src/session/types";
import {
  areaDeTransferencia,
  instalarDublesDeNavegador,
  restaurarDublesDeNavegador,
} from "./dubles";

// O `routes` chega na tela do ativo, que importa o uPlot; o uPlot pede `matchMedia` no import.
vi.mock("uplot", () => ({ default: class {} }));

const ME: Me = {
  email: "carla.mendes@exemplo.com",
  name: "Carla Mendes",
  role: "admin",
  must_change_password: false,
  is_staff: false,
  organization: { name: "Gestora Exemplo", slug: "gestora", is_personal: false },
};
const MEMBER: Me = { ...ME, role: "member" };
const PERSONAL: Me = {
  ...ME,
  organization: { name: "Carla Mendes", slug: "pessoal-1", is_personal: true },
};

function user(over: Partial<OrgUser> & Pick<OrgUser, "email" | "name">): OrgUser {
  return {
    role: "member",
    is_active: true,
    must_change_password: false,
    created_at: "2026-09-01T12:00:00Z",
    last_login: "2026-10-01T19:20:00Z",
    ...over,
  };
}

const ANA = user({
  email: "ana+x@exemplo.com",
  name: "Ana Lima",
  must_change_password: true,
  last_login: null,
});
const BRUNO = user({
  email: "bruno.costa@exemplo.com",
  name: "Bruno Costa",
  role: "admin",
  last_login: "2026-09-29T21:02:00Z",
});
const CARLA = user({ email: ME.email, name: ME.name, role: "admin" });
const DIEGO = user({
  email: "diego.alves@exemplo.com",
  name: "Diego Alves",
  is_active: false,
});
const GABRIELA = user({
  email: "gabriela.rocha@exemplo.com",
  name: "Gabriela Rocha",
  role: "admin",
  must_change_password: true,
  last_login: null,
});

const PASSWORD = "k7Qm2vXa9RtB4nLp";

/** A mensagem que a API manda em todo erro destes testes: nunca pode aparecer na tela. */
const API_MESSAGE = "MENSAGEM CRUA DA API";

type Reply = { status: number; body: unknown } | "network" | null;

const ok = (body: unknown, status = 200): Reply => ({ status, body });
const fail = (status: number, code: string, details: object = {}): Reply => ({
  status,
  body: { error: { code, message: API_MESSAGE, details } },
});
const page = (results: OrgUser[], count = results.length, offset = 0): Reply =>
  ok({ count, limit: 50, offset, results });

type Call = { url: string; method: string; body: string | undefined };

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
const USERS = "/api/v1/organization/users";
const FIRST = `GET ${USERS}?limit=50&offset=0`;
const ANA_PATH = `${USERS}/ana%2Bx%40exemplo.com`;

const callsTo = (method: string, url: string) =>
  calls.filter((c) => c.method === method && c.url === url);
const usersCalls = () => calls.filter((c) => c.url.startsWith(USERS));
const meCalls = () => callsTo("GET", "/api/v1/auth/me");

function renderUsers(path = "/organizacao/usuarios") {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(<RouterProvider router={router} />);
  return router;
}

async function microtasks(): Promise<void> {
  for (let i = 0; i < 20; i += 1) {
    await Promise.resolve();
  }
}

/**
 * Esvazia as promessas pendentes — a cadeia fetch → json → estado — dentro do `act`, e depois
 * deixa correr as tarefas já na fila, num `act` à parte: o `close` do `<dialog>` chega numa
 * tarefa (`dubles.ts`), **depois** da renderização que o primeiro `act` descarrega — a ordem do
 * navegador.
 */
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

const screenRoot = () =>
  document.querySelector('[data-screen="usuarios"]') as HTMLElement;
const dialogEl = () => document.querySelector("dialog") as HTMLDialogElement;
const isDialogOpen = () => dialogEl()?.hasAttribute("open") === true;
const rowOf = (email: string) =>
  document.querySelector(`tr[data-email="${email}"]`) as HTMLElement;
const rowButtons = (email: string) =>
  [...rowOf(email).querySelectorAll("button")].map((b) => b.textContent);
const rowButton = (email: string, label: string) =>
  within(rowOf(email)).getByRole("button", { name: label });
const listPanel = () => document.querySelector('[data-part="lista"]') as HTMLElement;
const submitButton = () =>
  document.querySelector('[data-part="botao-criar"]') as HTMLButtonElement;
const nameInput = () =>
  screen.getByLabelText(TEXTOS["usuarios.campo.nome"]) as HTMLInputElement;
const emailInput = () =>
  screen.getByLabelText(TEXTOS["usuarios.campo.email"]) as HTMLInputElement;
const inDialog = () => within(dialogEl());
const slot = () => document.querySelector(".ruvor-topbar__account") as HTMLElement;

/** O texto das mensagens de erro ligadas ao campo pelo `aria-describedby`. */
function fieldErrors(field: HTMLInputElement): string[] {
  const id = field.getAttribute("aria-describedby");
  if (id === null) return [];
  const group = document.getElementById(id);
  return [...(group?.querySelectorAll(".ruvor-field__error") ?? [])].map(
    (e) => e.textContent ?? "",
  );
}

async function fillAndCreate(name: string, email: string): Promise<void> {
  fireEvent.change(nameInput(), { target: { value: name } });
  fireEvent.change(emailInput(), { target: { value: email } });
  await click(submitButton());
}

beforeEach(() => {
  replies = {};
  reply(ME_KEY, ok(ME));
  reply(FIRST, page([ANA, BRUNO, CARLA, DIEGO]));
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

describe("a página e as marcas (RF-11)", () => {
  it("no casco: o sobretítulo, o título e a frase com a organização", async () => {
    renderUsers();
    await flush();
    expect(screen.getByRole("banner")).toBeDefined();
    expect(document.querySelectorAll('[data-screen="usuarios"]')).toHaveLength(1);
    expect(within(screenRoot()).getByText(TEXTOS["usuarios.eyebrow"])).toBeDefined();
    expect(
      screen.getByRole("heading", { level: 1, name: TEXTOS["usuarios.titulo"] }),
    ).toBeDefined();
    expect(
      screen.getByText(TEXTOS["usuarios.sub"](ME.organization.name)),
    ).toBeDefined();
  });

  it("os cinco data-part, uma vez cada; 'linha' é a primeira que não é a própria", async () => {
    renderUsers();
    await flush();
    for (const part of ["lista", "linha", "linha-voce", "form-criar", "botao-criar"]) {
      expect(document.querySelectorAll(`[data-part="${part}"]`)).toHaveLength(1);
    }
    expect(document.querySelector('[data-part="linha"]')).toBe(rowOf(ANA.email));
    expect(document.querySelector('[data-part="linha-voce"]')).toBe(rowOf(CARLA.email));
  });

  it("um GET organization/users?limit=50&offset=0 ao montar", async () => {
    renderUsers();
    await flush();
    expect(usersCalls()).toEqual([
      { url: `${USERS}?limit=50&offset=0`, method: "GET", body: undefined },
    ]);
  });

  it("o formulário: os textos aprovados, o papel em .ruvor-segmented--surface com Membro marcado", async () => {
    renderUsers();
    await flush();
    for (const key of [
      "usuarios.criar.titulo",
      "usuarios.criar.texto",
      "usuarios.campo.papel",
      "usuarios.campo.papel.dica",
    ] as const) {
      const form = document.querySelector('[data-part="form-criar"]') as HTMLElement;
      expect(within(form).getByText(TEXTOS[key])).toBeDefined();
    }
    expect(emailInput().getAttribute("placeholder")).toBe(
      TEXTOS["usuarios.campo.email.exemplo"],
    );
    const group = document.querySelector(".ruvor-segmented--surface") as HTMLElement;
    const member = within(group).getByRole("button", {
      name: TEXTOS["usuarios.papel.member"],
    });
    const admin = within(group).getByRole("button", {
      name: TEXTOS["usuarios.papel.admin"],
    });
    expect(member.getAttribute("aria-pressed")).toBe("true");
    expect(admin.getAttribute("aria-pressed")).toBe("false");
    expect(submitButton().textContent).toBe(TEXTOS["usuarios.criar.botao"]);
  });
});

describe("a lista (RF-11)", () => {
  it("a contagem, as colunas e o 'Mostrando'", async () => {
    renderUsers();
    await flush();
    const panel = listPanel();
    expect(within(panel).getByText(TEXTOS["usuarios.lista.titulo"])).toBeDefined();
    expect(within(panel).getByText(TEXTOS["usuarios.lista.contagem"](4))).toBeDefined();
    for (const key of [
      "usuarios.col.nome",
      "usuarios.col.email",
      "usuarios.col.papel",
      "usuarios.col.situacao",
      "usuarios.col.ultimoAcesso",
      "usuarios.col.acoes",
    ] as const) {
      expect(
        within(panel).getByRole("columnheader", { name: TEXTOS[key] }),
      ).toBeDefined();
    }
    expect(within(panel).getByText(TEXTOS["usuarios.mostrando"](4, 4))).toBeDefined();
    expect(within(panel).queryByText(TEXTOS["usuarios.mostrarMais"])).toBeNull();
  });

  it("cada linha: o papel como 'Administração' ou 'Membro', a situação, a senha provisória e o último acesso", async () => {
    renderUsers();
    await flush();
    const ana = within(rowOf(ANA.email));
    expect(ana.getByText(ANA.name)).toBeDefined();
    expect(ana.getByText(ANA.email)).toBeDefined();
    expect(ana.getByText(TEXTOS["usuarios.papel.member"])).toBeDefined();
    expect(ana.getByText(TEXTOS["usuarios.situacao.ativa"])).toBeDefined();
    expect(ana.getByText(TEXTOS["usuarios.provisoria"])).toBeDefined();
    expect(ana.getByText(TEXTOS["usuarios.nuncaEntrou"])).toBeDefined();
    const bruno = within(rowOf(BRUNO.email));
    expect(bruno.getByText(TEXTOS["usuarios.papel.admin"])).toBeDefined();
    // 21:02 UTC é 18:02 no fuso da B3.
    expect(
      bruno.getByText(TEXTOS["usuarios.ultimoAcesso"]("29/09/2026", "18:02")),
    ).toBeDefined();
    expect(bruno.queryByText(TEXTOS["usuarios.provisoria"])).toBeNull();
    expect(
      within(rowOf(DIEGO.email)).getByText(TEXTOS["usuarios.situacao.desativada"]),
    ).toBeDefined();
  });

  it("'você' só na própria linha", async () => {
    renderUsers();
    await flush();
    expect(screen.getAllByText(TEXTOS["usuarios.voce"])).toHaveLength(1);
    expect(within(rowOf(CARLA.email)).getByText(TEXTOS["usuarios.voce"])).toBeDefined();
  });

  it("a própria linha só muda o papel: sem Desativar nem Nova senha provisória (RF-14)", async () => {
    renderUsers();
    await flush();
    expect(rowButtons(CARLA.email)).toEqual([TEXTOS["usuarios.acao.member"]]);
  });

  it("as ações das outras linhas, pelo papel e pela situação", async () => {
    renderUsers();
    await flush();
    expect(rowButtons(ANA.email)).toEqual([
      TEXTOS["usuarios.acao.admin"],
      TEXTOS["usuarios.acao.desativar"],
      TEXTOS["usuarios.acao.senha"],
    ]);
    expect(rowButtons(BRUNO.email)).toEqual([
      TEXTOS["usuarios.acao.member"],
      TEXTOS["usuarios.acao.desativar"],
      TEXTOS["usuarios.acao.senha"],
    ]);
    expect(rowButtons(DIEGO.email)).toEqual([
      TEXTOS["usuarios.acao.admin"],
      TEXTOS["usuarios.acao.reativar"],
      TEXTOS["usuarios.acao.senha"],
    ]);
    expect(
      screen.getByRole("group", { name: TEXTOS["usuarios.acoes.rotulo"](ANA.name) }),
    ).toBeDefined();
  });

  it("Mostrar mais pede a página seguinte pelo offset e não repete e-mail", async () => {
    reply(FIRST, page([ANA, BRUNO, CARLA], 4));
    reply(`GET ${USERS}?limit=50&offset=3`, page([CARLA, DIEGO], 4, 3));
    renderUsers();
    await flush();
    expect(screen.getByText(TEXTOS["usuarios.mostrando"](3, 4))).toBeDefined();
    await click(screen.getByRole("button", { name: TEXTOS["usuarios.mostrarMais"] }));
    expect(callsTo("GET", `${USERS}?limit=50&offset=3`)).toHaveLength(1);
    const emails = [...document.querySelectorAll("tr[data-email]")].map((tr) =>
      tr.getAttribute("data-email"),
    );
    expect(emails).toEqual([ANA.email, BRUNO.email, CARLA.email, DIEGO.email]);
    expect(screen.getByText(TEXTOS["usuarios.mostrando"](4, 4))).toBeDefined();
    expect(
      screen.queryByRole("button", { name: TEXTOS["usuarios.mostrarMais"] }),
    ).toBeNull();
  });

  it("Mostrar mais que falha: as linhas ficam, e o erro tem 'Tentar de novo'", async () => {
    reply(FIRST, page([ANA, BRUNO, CARLA], 4));
    reply(`GET ${USERS}?limit=50&offset=3`, "network", page([DIEGO], 4, 3));
    renderUsers();
    await flush();
    await click(screen.getByRole("button", { name: TEXTOS["usuarios.mostrarMais"] }));
    expect(screen.getByRole("alert").textContent).toContain(
      TEXTOS["usuarios.erroMais"],
    );
    expect(document.querySelectorAll("tr[data-email]")).toHaveLength(3);
    await click(screen.getByRole("button", { name: TEXTOS["usuarios.tentarDeNovo"] }));
    expect(document.querySelectorAll("tr[data-email]")).toHaveLength(4);
  });

  it("a primeira página que não vem: o erro e 'Tentar de novo', que pede de novo", async () => {
    reply(FIRST, fail(500, "server_error"), page([ANA, CARLA]));
    renderUsers();
    await flush();
    expect(screen.getByRole("alert").textContent).toContain(
      TEXTOS["usuarios.erroLista"],
    );
    expect(document.body.textContent).not.toContain(API_MESSAGE);
    await click(screen.getByRole("button", { name: TEXTOS["usuarios.tentarDeNovo"] }));
    expect(callsTo("GET", `${USERS}?limit=50&offset=0`)).toHaveLength(2);
    expect(document.querySelectorAll("tr[data-email]")).toHaveLength(2);
  });

  it("carregando: o esqueleto, com aria-busy", async () => {
    reply(FIRST, null);
    renderUsers();
    await flush();
    const body = listPanel().querySelector(".ruvor-panel__body") as HTMLElement;
    expect(body.getAttribute("aria-busy")).toBe("true");
    expect(body.querySelector(".ruvor-skeleton")).not.toBeNull();
  });
});

describe("quem não pode gerir (RF-12)", () => {
  it.each([
    [
      "membro",
      MEMBER,
      "usuarios.membro.titulo",
      TEXTOS["usuarios.membro.texto"]("Gestora Exemplo"),
    ],
    [
      "organização pessoal",
      PERSONAL,
      "usuarios.pessoal.titulo",
      TEXTOS["usuarios.pessoal.texto"],
    ],
  ] as const)(
    "%s, pelo me: o porquê, sem pedir a lista",
    async (_n, me, title, text) => {
      reply(ME_KEY, ok(me));
      renderUsers();
      await flush();
      expect(screen.getByText(TEXTOS[title])).toBeDefined();
      expect(screen.getByText(text)).toBeDefined();
      expect(usersCalls()).toHaveLength(0);
      expect(document.querySelector('[data-part="form-criar"]')).toBeNull();
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
        TEXTOS["usuarios.titulo"],
      );
      expect(
        screen.queryByText(TEXTOS["usuarios.sub"](me.organization.name)),
      ).toBeNull();
    },
  );

  it("anônimo desde a carga: o aviso 'para quem entrou', sem pedir a lista", async () => {
    reply(ME_KEY, fail(401, "not_authenticated"));
    renderUsers();
    await flush();
    const notice = document.querySelector("[data-signin-notice]") as HTMLElement;
    expect(notice.getAttribute("data-signin-notice")).toBe("required");
    expect(
      within(notice)
        .getByRole("link", { name: TEXTOS["conta.entrar"] })
        .getAttribute("href"),
    ).toBe("/entrar?next=%2Forganizacao%2Fusuarios");
    expect(usersCalls()).toHaveLength(0);
  });

  it("com a sessão carregando: o esqueleto, sem pedir a lista", async () => {
    reply(ME_KEY, null);
    renderUsers();
    await flush();
    expect(screenRoot().getAttribute("aria-busy")).toBe("true");
    expect(usersCalls()).toHaveLength(0);
    expect(document.querySelector("[data-signin-notice]")).toBeNull();
  });

  it.each([
    ["403 permission_denied", fail(403, "permission_denied"), "usuarios.membro.titulo"],
    [
      "409 personal_organization",
      fail(409, "personal_organization"),
      "usuarios.pessoal.titulo",
    ],
  ] as const)("%s na lista: o caso dele, pelo code", async (_n, r, title) => {
    reply(FIRST, r);
    renderUsers();
    await flush();
    expect(screen.getByText(TEXTOS[title])).toBeDefined();
    expect(document.querySelector('[data-part="lista"]')).toBeNull();
    expect(document.body.textContent).not.toContain(API_MESSAGE);
  });

  it("password_change_required na lista: relê o auth/me, e a troca obrigatória assume", async () => {
    reply(ME_KEY, ok(ME), ok({ ...ME, must_change_password: true }));
    reply(FIRST, fail(403, "password_change_required"));
    const router = renderUsers();
    await flush();
    expect(meCalls()).toHaveLength(2);
    expect(document.querySelector('[data-screen="senha-obrigatoria"]')).not.toBeNull();
    expect(router.state.location.pathname).toBe("/organizacao/usuarios");
  });

  it("401 na lista: o aviso de sessão terminada no lugar da lista; o resto da página fica", async () => {
    reply(FIRST, fail(401, "not_authenticated"));
    const router = renderUsers();
    await flush();
    const notice = listPanel().querySelector("[data-signin-notice]") as HTMLElement;
    expect(notice.getAttribute("data-signin-notice")).toBe("ended");
    expect(notice.getAttribute("role")).toBe("alert");
    expect(document.querySelector('[data-part="form-criar"]')).not.toBeNull();
    expect(slot().getAttribute("data-account")).toBe("anonymous");
    expect(router.state.location.pathname).toBe("/organizacao/usuarios");
  });
});

describe("criar (RF-13)", () => {
  it("os vazios: o erro em cada campo, ligado a ele, e o foco no nome, sem pedido", async () => {
    renderUsers();
    await flush();
    fireEvent.change(nameInput(), { target: { value: "   " } });
    await click(submitButton());
    expect(nameInput().getAttribute("aria-invalid")).toBe("true");
    expect(fieldErrors(nameInput())).toEqual([TEXTOS["usuarios.erro.nomeVazio"]]);
    expect(fieldErrors(emailInput())).toEqual([TEXTOS["usuarios.erro.emailVazio"]]);
    expect(document.activeElement).toBe(nameInput());
    expect(callsTo("POST", USERS)).toHaveLength(0);
  });

  it("o POST leva o nome e o e-mail aparados e o papel escolhido", async () => {
    reply(`POST ${USERS}`, null);
    renderUsers();
    await flush();
    await click(screen.getByRole("button", { name: TEXTOS["usuarios.papel.admin"] }));
    await fillAndCreate("  Gabriela Rocha ", " gabriela.rocha@exemplo.com ");
    const posts = callsTo("POST", USERS);
    expect(posts).toHaveLength(1);
    expect(JSON.parse(posts[0].body ?? "")).toEqual({
      email: "gabriela.rocha@exemplo.com",
      name: "Gabriela Rocha",
      role: "admin",
    });
    expect(submitButton().disabled).toBe(true);
    expect(submitButton().textContent).toBe(TEXTOS["usuarios.criar.enviando"]);
  });

  it("201: o diálogo com a senha, uma vez, e a lista relida da primeira página", async () => {
    reply(`POST ${USERS}`, ok({ user: GABRIELA, temporary_password: PASSWORD }, 201));
    reply(
      FIRST,
      page([ANA, BRUNO, CARLA, DIEGO]),
      page([ANA, BRUNO, CARLA, DIEGO, GABRIELA]),
    );
    renderUsers();
    await flush();
    await fillAndCreate(GABRIELA.name, GABRIELA.email);
    expect(isDialogOpen()).toBe(true);
    expect(dialogEl().getAttribute("data-dialog")).toBe("senha-provisoria");
    const dialog = inDialog();
    expect(dialog.getByText(TEXTOS["usuarios.senha.criado.titulo"])).toBeDefined();
    expect(
      dialog.getByText(
        TEXTOS["usuarios.senha.criado.texto"](GABRIELA.name, GABRIELA.email),
      ),
    ).toBeDefined();
    expect(dialog.getByDisplayValue(PASSWORD)).toBeDefined();
    for (const key of [
      "usuarios.senha.umaVez",
      "usuarios.senha.trocar",
      "usuarios.senha.entrega",
    ] as const) {
      expect(dialog.getByText(TEXTOS[key])).toBeDefined();
    }
    // A lista relida da API, não a linha inserida à mão: dois GET com offset=0, e o count novo.
    expect(callsTo("GET", `${USERS}?limit=50&offset=0`)).toHaveLength(2);
    expect(screen.getByText(TEXTOS["usuarios.lista.contagem"](5))).toBeDefined();
    expect(rowOf(GABRIELA.email)).not.toBeNull();
    // O formulário volta vazio, com Membro.
    expect(nameInput().value).toBe("");
    expect(emailInput().value).toBe("");
    expect(
      screen
        .getAllByRole("button", { name: TEXTOS["usuarios.papel.member"] })[0]
        .getAttribute("aria-pressed"),
    ).toBe("true");
  });

  it("Copiar: o texto vai à área de transferência, e a confirmação aparece", async () => {
    reply(`POST ${USERS}`, ok({ user: GABRIELA, temporary_password: PASSWORD }, 201));
    renderUsers();
    await flush();
    await fillAndCreate(GABRIELA.name, GABRIELA.email);
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.senha.copiar"] }),
    );
    expect(areaDeTransferencia.textos).toEqual([PASSWORD]);
    expect(inDialog().getByRole("status").textContent).toBe(
      TEXTOS["usuarios.senha.copiadaAviso"],
    );
    expect(inDialog().getByText(TEXTOS["usuarios.senha.copiada"])).toBeDefined();
  });

  it("a cópia negada: a frase de copiar com o teclado, e nada na área de transferência", async () => {
    reply(`POST ${USERS}`, ok({ user: GABRIELA, temporary_password: PASSWORD }, 201));
    renderUsers();
    await flush();
    await fillAndCreate(GABRIELA.name, GABRIELA.email);
    areaDeTransferencia.falhar = true;
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.senha.copiar"] }),
    );
    expect(areaDeTransferencia.textos).toEqual([]);
    expect(inDialog().getByRole("status").textContent).toBe(
      TEXTOS["usuarios.senha.copiaFalhou"],
    );
  });

  it("Fechar: a senha sai do DOM, e o foco volta a 'Criar usuário'", async () => {
    reply(`POST ${USERS}`, ok({ user: GABRIELA, temporary_password: PASSWORD }, 201));
    renderUsers();
    await flush();
    await fillAndCreate(GABRIELA.name, GABRIELA.email);
    // Ao abrir, o foco vai ao primeiro controle do diálogo.
    expect(dialogEl().contains(document.activeElement)).toBe(true);
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.senha.fechar"] }),
    );
    expect(isDialogOpen()).toBe(false);
    expect(screen.queryByDisplayValue(PASSWORD)).toBeNull();
    expect(document.body.innerHTML).not.toContain(PASSWORD);
    expect(document.activeElement).toBe(submitButton());
  });

  it("email_taken: no campo do e-mail, com o foco nele", async () => {
    reply(`POST ${USERS}`, fail(409, "email_taken"));
    renderUsers();
    await flush();
    await fillAndCreate("Elisa Prado", "elisa.prado@exemplo.com");
    expect(fieldErrors(emailInput())).toEqual([TEXTOS["usuarios.erro.emailTaken"]]);
    expect(document.activeElement).toBe(emailInput());
    expect(isDialogOpen()).toBe(false);
    expect(document.body.textContent).not.toContain(API_MESSAGE);
  });

  it("invalid_parameter: a lista de details.fields no campo dela, como chega", async () => {
    const message = "Informe um nome de 1 a 120 caracteres.";
    reply(
      `POST ${USERS}`,
      fail(400, "invalid_parameter", { fields: { name: [message] } }),
    );
    renderUsers();
    await flush();
    await fillAndCreate("Ana", "ana@exemplo.com");
    expect(fieldErrors(nameInput())).toEqual([message]);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it.each([
    [
      "429 com wait_seconds",
      fail(429, "too_many_requests", { wait_seconds: 12 }),
      TEXTOS["usuarios.erro.muitos"](12),
    ],
    [
      "429 sem wait_seconds",
      fail(429, "too_many_requests"),
      TEXTOS["usuarios.erro.muitosSemTempo"],
    ],
    ["csrf_failed", fail(403, "csrf_failed"), TEXTOS["usuarios.erro.csrf"]],
    ["rede", "network" as Reply, TEXTOS["usuarios.erro.rede"]],
    [
      "outro code",
      fail(400, "invalid_parameter", { fields: { role: ["x"] } }),
      TEXTOS["usuarios.erro.outro"],
    ],
  ])(
    "%s: a frase dele na caixa do formulário, e o foco no botão",
    async (_n, r, text) => {
      reply(`POST ${USERS}`, r);
      reply("GET /api/v1/auth/csrf", { status: 204, body: null });
      renderUsers();
      await flush();
      await fillAndCreate("Ana", "ana@exemplo.com");
      const form = document.querySelector('[data-part="form-criar"]') as HTMLElement;
      expect(within(form).getByRole("alert").textContent).toBe(text);
      expect(document.activeElement).toBe(submitButton());
      expect(document.body.textContent).not.toContain(API_MESSAGE);
    },
  );

  it("401: o aviso de sessão terminada no lugar do formulário; a lista fica", async () => {
    reply(`POST ${USERS}`, fail(401, "not_authenticated"));
    renderUsers();
    await flush();
    await fillAndCreate("Ana", "ana@exemplo.com");
    expect(document.querySelector('[data-part="form-criar"]')).toBeNull();
    expect(
      document.querySelector('[data-signin-notice="ended"]')?.closest(".ruvor-panel"),
    ).not.toBe(listPanel());
    expect(rowOf(ANA.email)).not.toBeNull();
    expect(slot().getAttribute("data-account")).toBe("anonymous");
  });
});

describe("as ações da linha (RF-14)", () => {
  it("Desativar: a confirmação diz o efeito; o PATCH vai com o e-mail codificado; a linha mostra o devolvido", async () => {
    reply(`PATCH ${ANA_PATH}`, ok({ ...ANA, is_active: false }));
    renderUsers();
    await flush();
    await click(rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]));
    expect(isDialogOpen()).toBe(true);
    expect(dialogEl().getAttribute("data-dialog")).toBe("confirmar-desativar");
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.desativar.titulo"](ANA.name)),
    ).toBeDefined();
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.desativar.texto"]),
    ).toBeDefined();
    expect(callsTo("PATCH", ANA_PATH)).toHaveLength(0);
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.desativar"] }),
    );
    const patches = callsTo("PATCH", ANA_PATH);
    expect(patches).toHaveLength(1);
    expect(patches[0].url).toBe("/api/v1/organization/users/ana%2Bx%40exemplo.com");
    expect(JSON.parse(patches[0].body ?? "")).toEqual({ is_active: false });
    expect(isDialogOpen()).toBe(false);
    expect(
      within(rowOf(ANA.email)).getByText(TEXTOS["usuarios.situacao.desativada"]),
    ).toBeDefined();
    expect(rowButtons(ANA.email)[1]).toBe(TEXTOS["usuarios.acao.reativar"]);
    // O foco volta ao botão da mesma posição na linha.
    expect(document.activeElement).toBe(
      rowButton(ANA.email, TEXTOS["usuarios.acao.reativar"]),
    );
  });

  it("Cancelar: nada é pedido, e o foco volta ao botão que abriu", async () => {
    renderUsers();
    await flush();
    const opener = rowButton(BRUNO.email, TEXTOS["usuarios.acao.desativar"]);
    await click(opener);
    const cancel = inDialog().getByRole("button", {
      name: TEXTOS["usuarios.confirmar.cancelar"],
    });
    cancel.focus();
    expect(document.activeElement).toBe(cancel);
    await click(cancel);
    expect(isDialogOpen()).toBe(false);
    expect(calls.filter((c) => c.method === "PATCH")).toHaveLength(0);
    expect(document.activeElement).toBe(opener);
  });

  it("o Esc (o close do navegador) também devolve o foco", async () => {
    renderUsers();
    await flush();
    const opener = rowButton(BRUNO.email, TEXTOS["usuarios.acao.member"]);
    await click(opener);
    await act(async () => {
      dialogEl().close();
    });
    await flush();
    expect(document.activeElement).toBe(opener);
  });

  it("Mudar para administração: PATCH com role admin, e a linha passa a 'Administração'", async () => {
    reply(`PATCH ${ANA_PATH}`, ok({ ...ANA, role: "admin" }));
    renderUsers();
    await flush();
    await click(rowButton(ANA.email, TEXTOS["usuarios.acao.admin"]));
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.admin.titulo"](ANA.name)),
    ).toBeDefined();
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.admin.texto"]),
    ).toBeDefined();
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.admin"] }),
    );
    expect(JSON.parse(callsTo("PATCH", ANA_PATH)[0].body ?? "")).toEqual({
      role: "admin",
    });
    expect(
      within(rowOf(ANA.email)).getByText(TEXTOS["usuarios.papel.admin"]),
    ).toBeDefined();
  });

  it("Mudar para membro (outra pessoa): a confirmação dela e o PATCH com role member", async () => {
    const path = `${USERS}/bruno.costa%40exemplo.com`;
    reply(`PATCH ${path}`, ok({ ...BRUNO, role: "member" }));
    renderUsers();
    await flush();
    await click(rowButton(BRUNO.email, TEXTOS["usuarios.acao.member"]));
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.member.titulo"](BRUNO.name)),
    ).toBeDefined();
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.member.texto"]),
    ).toBeDefined();
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.member"] }),
    );
    expect(JSON.parse(callsTo("PATCH", path)[0].body ?? "")).toEqual({
      role: "member",
    });
    expect(meCalls()).toHaveLength(1);
  });

  it("Reativar: PATCH com is_active true; na linha desativada, a mudança de papel diz quando vale", async () => {
    const path = `${USERS}/diego.alves%40exemplo.com`;
    reply(`PATCH ${path}`, ok({ ...DIEGO, is_active: true }));
    renderUsers();
    await flush();
    await click(rowButton(DIEGO.email, TEXTOS["usuarios.acao.admin"]));
    expect(inDialog().getByText(TEXTOS["usuarios.confirmar.desativada"])).toBeDefined();
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.confirmar.cancelar"] }),
    );
    await click(rowButton(DIEGO.email, TEXTOS["usuarios.acao.reativar"]));
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.reativar.texto"]),
    ).toBeDefined();
    expect(inDialog().queryByText(TEXTOS["usuarios.confirmar.desativada"])).toBeNull();
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.reativar"] }),
    );
    expect(JSON.parse(callsTo("PATCH", path)[0].body ?? "")).toEqual({
      is_active: true,
    });
    expect(
      within(rowOf(DIEGO.email)).getByText(TEXTOS["usuarios.situacao.ativa"]),
    ).toBeDefined();
  });

  it("Nova senha provisória: o POST, o diálogo troca para a senha, e o foco vai ao primeiro controle", async () => {
    const path = `${ANA_PATH}/temporary-password`;
    const fresh = "pL4nBtR9aXv2mQ7k";
    reply(
      `POST ${path}`,
      ok({ user: { ...ANA, must_change_password: true }, temporary_password: fresh }),
    );
    renderUsers();
    await flush();
    const opener = rowButton(ANA.email, TEXTOS["usuarios.acao.senha"]);
    await click(opener);
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.senha.titulo"](ANA.name)),
    ).toBeDefined();
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.senha.texto"]),
    ).toBeDefined();
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.senha"] }),
    );
    expect(callsTo("POST", path)).toHaveLength(1);
    expect(dialogEl().getAttribute("data-dialog")).toBe("senha-provisoria");
    expect(inDialog().getByText(TEXTOS["usuarios.senha.nova.titulo"])).toBeDefined();
    expect(
      inDialog().getByText(TEXTOS["usuarios.senha.nova.texto"](ANA.name, ANA.email)),
    ).toBeDefined();
    expect(document.activeElement).toBe(inDialog().getByDisplayValue(fresh));
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.senha.fechar"] }),
    );
    expect(document.body.innerHTML).not.toContain(fresh);
    expect(document.activeElement).toBe(opener);
  });

  it("rebaixar a si mesma: a confirmação própria, o PATCH, o auth/me relido e o caso 'membro' com o foco", async () => {
    const path = `${USERS}/carla.mendes%40exemplo.com`;
    reply(`PATCH ${path}`, ok({ ...CARLA, role: "member" }));
    reply(ME_KEY, ok(ME), ok(MEMBER));
    renderUsers();
    await flush();
    await click(rowButton(CARLA.email, TEXTOS["usuarios.acao.member"]));
    expect(dialogEl().getAttribute("data-dialog")).toBe("confirmar-rebaixar-si");
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.rebaixarSi.titulo"]),
    ).toBeDefined();
    expect(
      inDialog().getByText(TEXTOS["usuarios.confirmar.rebaixarSi.texto"]),
    ).toBeDefined();
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.member"] }),
    );
    await flush();
    expect(JSON.parse(callsTo("PATCH", path)[0].body ?? "")).toEqual({
      role: "member",
    });
    expect(meCalls()).toHaveLength(2);
    const title = screen.getByText(TEXTOS["usuarios.membro.titulo"]);
    expect(document.activeElement).toBe(title.closest(".ruvor-state"));
    expect(document.querySelector("dialog")).toBeNull();
  });

  it("last_admin: a frase dele no diálogo, que continua com a confirmação", async () => {
    const path = `${USERS}/carla.mendes%40exemplo.com`;
    reply(`PATCH ${path}`, fail(409, "last_admin"));
    renderUsers();
    await flush();
    await click(rowButton(CARLA.email, TEXTOS["usuarios.acao.member"]));
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.member"] }),
    );
    expect(inDialog().getByRole("alert").textContent).toBe(
      TEXTOS["usuarios.erro.lastAdmin"],
    );
    expect(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.member"] }),
    ).toBeDefined();
    expect(meCalls()).toHaveLength(1);
    expect(document.body.textContent).not.toContain(API_MESSAGE);
  });

  it("user_not_found: só o título, a frase e Fechar; a lista é relida", async () => {
    reply(`PATCH ${ANA_PATH}`, fail(404, "user_not_found"));
    reply(FIRST, page([ANA, BRUNO, CARLA, DIEGO]), page([BRUNO, CARLA, DIEGO]));
    renderUsers();
    await flush();
    await click(rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]));
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.desativar"] }),
    );
    expect(inDialog().getByRole("alert").textContent).toBe(
      TEXTOS["usuarios.erro.naoEncontrado"],
    );
    expect(
      inDialog().queryByText(TEXTOS["usuarios.confirmar.desativar.texto"]),
    ).toBeNull();
    expect(
      inDialog()
        .getAllByRole("button")
        .map((b) => b.textContent),
    ).toEqual([TEXTOS["usuarios.confirmar.fechar"]]);
    expect(callsTo("GET", `${USERS}?limit=50&offset=0`)).toHaveLength(2);
    expect(rowOf(ANA.email)).toBeNull();
  });

  it("401 numa ação: o aviso de sessão terminada dentro do diálogo, com Fechar; a página fica", async () => {
    reply(`PATCH ${ANA_PATH}`, fail(401, "not_authenticated"));
    const router = renderUsers();
    await flush();
    await click(rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]));
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.desativar"] }),
    );
    const notice = dialogEl().querySelector("[data-signin-notice]") as HTMLElement;
    expect(notice.getAttribute("data-signin-notice")).toBe("ended");
    expect(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.confirmar.fechar"] }),
    ).toBeDefined();
    expect(slot().getAttribute("data-account")).toBe("anonymous");
    expect(rowOf(ANA.email)).not.toBeNull();
    expect(router.state.location.pathname).toBe("/organizacao/usuarios");
  });

  it("permission_denied numa ação: a tela passa ao caso 'membro'", async () => {
    reply(`PATCH ${ANA_PATH}`, fail(403, "permission_denied"));
    renderUsers();
    await flush();
    await click(rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]));
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.desativar"] }),
    );
    expect(screen.getByText(TEXTOS["usuarios.membro.titulo"])).toBeDefined();
    expect(document.querySelector("dialog")).toBeNull();
  });

  it("password_change_required numa ação: relê o auth/me", async () => {
    reply(`PATCH ${ANA_PATH}`, fail(403, "password_change_required"));
    reply(ME_KEY, ok(ME), ok({ ...ME, must_change_password: true }));
    renderUsers();
    await flush();
    await click(rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]));
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.desativar"] }),
    );
    expect(meCalls()).toHaveLength(2);
    expect(document.querySelector('[data-screen="senha-obrigatoria"]')).not.toBeNull();
  });

  it("enviando: os dois botões travados e a espera; a rede que falha → a frase dela", async () => {
    reply(`PATCH ${ANA_PATH}`, null);
    renderUsers();
    await flush();
    await click(rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]));
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.desativar"] }),
    );
    const buttons = inDialog().getAllByRole("button") as HTMLButtonElement[];
    expect(buttons.every((b) => b.disabled)).toBe(true);
    expect(dialogEl().textContent).toContain(TEXTOS["usuarios.confirmar.enviando"]);
    cleanup();
    reply(`PATCH ${ANA_PATH}`, "network");
    renderUsers();
    await flush();
    await click(rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]));
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.desativar"] }),
    );
    expect(inDialog().getByRole("alert").textContent).toBe(
      TEXTOS["usuarios.erro.rede"],
    );
  });
});

describe("o diálogo fecha de vez, com o close numa tarefa (o defeito achado na T16)", () => {
  /** Fechado, vazio e assim continua depois de mais uma volta de tarefas. */
  async function expectClosedForGood(): Promise<void> {
    expect(isDialogOpen()).toBe(false);
    expect(dialogEl().childElementCount).toBe(0);
    expect(dialogEl().hasAttribute("data-dialog")).toBe(false);
    await flush();
    expect(isDialogOpen()).toBe(false);
    expect(document.querySelectorAll("dialog[open]")).toHaveLength(0);
  }

  const DIEGO_PATH = `${USERS}/diego.alves%40exemplo.com`;
  const BRUNO_PATH = `${USERS}/bruno.costa%40exemplo.com`;

  it.each([
    // [o caso, o e-mail da linha, o botão que abre, o PATCH, a resposta, o botão que recebe o foco]
    [
      "Desativar",
      ANA.email,
      "usuarios.acao.desativar",
      ANA_PATH,
      { ...ANA, is_active: false },
      "usuarios.acao.reativar",
    ],
    [
      "Reativar",
      DIEGO.email,
      "usuarios.acao.reativar",
      DIEGO_PATH,
      { ...DIEGO, is_active: true },
      "usuarios.acao.desativar",
    ],
    [
      "Mudar para administração",
      ANA.email,
      "usuarios.acao.admin",
      ANA_PATH,
      { ...ANA, role: "admin" },
      "usuarios.acao.member",
    ],
    [
      "Mudar para membro",
      BRUNO.email,
      "usuarios.acao.member",
      BRUNO_PATH,
      { ...BRUNO, role: "member" },
      "usuarios.acao.admin",
    ],
  ] as const)(
    "%s confirmado: o <dialog> não reabre, e o foco volta à mesma posição na linha",
    async (_n, email, action, path, body, focused) => {
      reply(`PATCH ${path}`, ok(body));
      renderUsers();
      await flush();
      await click(rowButton(email, TEXTOS[action]));
      expect(isDialogOpen()).toBe(true);
      await click(inDialog().getByRole("button", { name: TEXTOS[action] }));
      expect(callsTo("PATCH", path)).toHaveLength(1);
      await expectClosedForGood();
      expect(document.activeElement).toBe(rowButton(email, TEXTOS[focused]));
    },
  );

  it("Cancelar: o <dialog> não reabre, e o foco volta a quem abriu", async () => {
    renderUsers();
    await flush();
    const opener = rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]);
    await click(opener);
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.confirmar.cancelar"] }),
    );
    await expectClosedForGood();
    expect(document.activeElement).toBe(opener);
  });

  it("Fechar a senha de quem foi criado: o <dialog> não reabre, e o foco volta a 'Criar usuário'", async () => {
    reply(`POST ${USERS}`, ok({ user: GABRIELA, temporary_password: PASSWORD }, 201));
    renderUsers();
    await flush();
    await fillAndCreate(GABRIELA.name, GABRIELA.email);
    expect(isDialogOpen()).toBe(true);
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.senha.fechar"] }),
    );
    await expectClosedForGood();
    expect(document.activeElement).toBe(submitButton());
  });

  it("Fechar a nova senha provisória: o <dialog> não reabre, e o foco volta a quem abriu", async () => {
    const path = `${ANA_PATH}/temporary-password`;
    reply(`POST ${path}`, ok({ user: ANA, temporary_password: PASSWORD }));
    renderUsers();
    await flush();
    const opener = rowButton(ANA.email, TEXTOS["usuarios.acao.senha"]);
    await click(opener);
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.senha"] }),
    );
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.senha.fechar"] }),
    );
    await expectClosedForGood();
    expect(document.activeElement).toBe(opener);
  });

  it("Fechar depois de user_not_found: o <dialog> não reabre", async () => {
    reply(`PATCH ${ANA_PATH}`, fail(404, "user_not_found"));
    reply(FIRST, page([ANA, BRUNO, CARLA, DIEGO]), page([BRUNO, CARLA, DIEGO]));
    renderUsers();
    await flush();
    await click(rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]));
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.desativar"] }),
    );
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.confirmar.fechar"] }),
    );
    await expectClosedForGood();
  });

  it("Fechar depois do 401: o <dialog> não reabre, e o foco volta a quem abriu", async () => {
    reply(`PATCH ${ANA_PATH}`, fail(401, "not_authenticated"));
    renderUsers();
    await flush();
    const opener = rowButton(ANA.email, TEXTOS["usuarios.acao.desativar"]);
    await click(opener);
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.acao.desativar"] }),
    );
    await click(
      inDialog().getByRole("button", { name: TEXTOS["usuarios.confirmar.fechar"] }),
    );
    await expectClosedForGood();
    expect(document.activeElement).toBe(opener);
  });

  it.each([
    [
      "rebaixar a si mesma",
      `${USERS}/carla.mendes%40exemplo.com`,
      CARLA.email,
      "usuarios.acao.member",
      ok({ ...CARLA, role: "member" }),
    ],
    [
      "permission_denied",
      ANA_PATH,
      ANA.email,
      "usuarios.acao.desativar",
      fail(403, "permission_denied"),
    ],
  ] as const)(
    "%s (o dismissDialog): nenhum <dialog> aberto fica, e o foco vai ao caso 'membro'",
    async (_n, path, email, action, r) => {
      reply(`PATCH ${path}`, r);
      reply(ME_KEY, ok(ME), ok(MEMBER));
      renderUsers();
      await flush();
      await click(rowButton(email, TEXTOS[action]));
      await click(inDialog().getByRole("button", { name: TEXTOS[action] }));
      await flush();
      expect(document.querySelectorAll("dialog[open]")).toHaveLength(0);
      const title = screen.getByText(TEXTOS["usuarios.membro.titulo"]);
      expect(document.activeElement).toBe(title.closest(".ruvor-state"));
    },
  );
});

describe("a rota (RF-04)", () => {
  it("o menu de conta leva a /organizacao/usuarios, que mostra a gestão", async () => {
    const router = renderUsers("/");
    await flush();
    await click(document.querySelector('[data-part="conta"]') as HTMLElement);
    await click(screen.getByRole("link", { name: TEXTOS["conta.menu.usuarios"] }));
    expect(router.state.location.pathname).toBe("/organizacao/usuarios");
    expect(screenRoot()).not.toBeNull();
    expect(screen.queryByText(TEXTOS["casco.naoEncontrada.titulo"])).toBeNull();
  });
});
