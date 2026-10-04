/**
 * V-09 (RF-09, RF-10) e a parte de página do V-11 (RF-16), contra o `conta.html` aprovado: o
 * lugar da conta na barra nos três estados, sempre o mesmo elemento e por último, depois da
 * chave de tema; as iniciais; o menu — `aria-expanded`, `aria-controls`, o nome, o e-mail, a
 * organização ou "Conta pessoal", "Trocar a senha" com o `next`, e "Usuários da organização" só
 * com `admin` numa organização que não é pessoal (os quatro casos) —; o teclado, o `Esc` com o
 * foco devolvido, o clique fora, o clique num item e o `Tab` que sai; Sair — na página pública
 * fica, em `/conta/` e `/organizacao/` vai a `/`, o 401 é sair sem erro, e a falha mantém a
 * sessão, o menu aberto e o mesmo Sair, só com a linha de alerta —; os dois avisos do RF-16, e
 * `/conta/senha` aberto por quem não entrou, ou com a sessão carregando.
 *
 * O `fetch` é um duplo que responde pelo endereço e pelo método; `null` deixa o pedido pendente.
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
import { initials } from "../src/components/AccountMenu";
import { Shell } from "../src/components/Shell";
import { SignInNotice } from "../src/components/SignInNotice";
import { TEXTOS } from "../src/content/textos";
import { PasswordScreen } from "../src/screens/PasswordScreen";
import { SessionProvider } from "../src/session/SessionProvider";
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
  organization: { name: "Ana Beatriz Souza", slug: "ana", is_personal: true },
};
const MEMBER: Me = { ...ME, role: "member" };

/** A mensagem que a API manda em todo erro destes testes: nunca pode aparecer na tela. */
const API_MESSAGE = "MENSAGEM CRUA DA API";

type Reply = { status: number; body: unknown } | "network" | null;

const ok = (body: unknown): Reply => ({ status: 200, body });
const fail = (status: number, code: string): Reply => ({
  status,
  body: { error: { code, message: API_MESSAGE, details: {} } },
});
const NO_CONTENT: Reply = { status: 204, body: null };
const ANON = fail(401, "not_authenticated");

type Call = { url: string; method: string };

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
      calls.push({ url, method });
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
const LOGOUT = "POST /api/v1/auth/logout";
const logoutCalls = () =>
  calls.filter((c) => c.method === "POST" && c.url === "/api/v1/auth/logout");

/** O casco sob o provedor de verdade, com destinos quaisquer e a troca voluntária da senha. */
function renderShell(path: string) {
  const router = createMemoryRouter(
    [
      {
        element: <SessionProvider />,
        children: [
          {
            element: <Shell />,
            children: [
              { index: true, element: <p data-testid="destino">inicio</p> },
              { path: "conta/senha", element: <PasswordScreen mode="voluntary" /> },
              { path: "*", element: <p data-testid="destino">outra</p> },
            ],
          },
        ],
      },
    ],
    { initialEntries: [path] },
  );
  render(<RouterProvider router={router} />);
  return router;
}

/** O aplicativo inteiro (`routes`), num roteador de memória. */
function renderRoutes(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(<RouterProvider router={router} />);
  return router;
}

async function click(element: Element): Promise<void> {
  await act(async () => {
    fireEvent.click(element);
  });
}

/** Esvazia as promessas pendentes — a cadeia fetch → json → estado — dentro do `act`. */
async function flush(): Promise<void> {
  await act(async () => {
    for (let i = 0; i < 20; i += 1) {
      await Promise.resolve();
    }
  });
}

const slot = () => document.querySelector(".ruvor-topbar__account") as HTMLElement;
const accountButton = () =>
  document.querySelector('[data-part="conta"]') as HTMLElement;
const menu = () => document.querySelector('[data-part="menu"]') as HTMLElement;
const sairButton = () =>
  within(menu()).getByRole("button", { name: TEXTOS["conta.menu.sair"] });
const isOpen = () =>
  accountButton().getAttribute("aria-expanded") === "true" && !menu().hidden;

beforeEach(() => {
  replies = {};
  reply(ME_KEY, ok(ME));
  // biome-ignore lint/suspicious/noDocumentCookie: o logout manda o token do cookie de verdade.
  document.cookie = "csrftoken=tok; path=/";
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  // biome-ignore lint/suspicious/noDocumentCookie: limpa o cookie gravado no beforeEach.
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("a barra nos três estados (RF-09)", () => {
  it("o lugar da conta é o último de .ruvor-topbar__prefs, depois da chave de tema", async () => {
    renderShell("/");
    await flush();
    const prefs = document.querySelector(".ruvor-topbar__prefs") as HTMLElement;
    const theme = screen.getByRole("group", { name: TEXTOS["casco.tema.rotulo"] });
    expect(prefs.lastElementChild).toBe(slot());
    expect(theme.nextElementSibling).toBe(slot());
    expect(document.querySelector('[data-part="barra"]')).toBe(
      screen.getByRole("banner"),
    );
  });

  it("carregando: o lugar vazio, sem Entrar nem nome", async () => {
    reply(ME_KEY, null);
    renderShell("/ativos/ITUB4");
    await flush();
    expect(slot().getAttribute("data-account")).toBe("loading");
    expect(slot().childElementCount).toBe(0);
    expect(slot().textContent).toBe("");
  });

  it("anônimo: o link Entrar, para /entrar?next=<página atual>", async () => {
    reply(ME_KEY, ANON);
    renderShell("/ativos/ITUB4?x=1");
    await flush();
    expect(slot().getAttribute("data-account")).toBe("anonymous");
    const enter = within(slot()).getByRole("link", { name: TEXTOS["conta.entrar"] });
    expect(enter.getAttribute("href")).toBe("/entrar?next=%2Fativos%2FITUB4%3Fx%3D1");
    expect(enter.getAttribute("data-part")).toBe("entrar");
    expect(accountButton()).toBeNull();
    expect(menu()).toBeNull();
  });

  it("logado: o botão de conta com o nome, as iniciais e o rótulo; o menu fechado", async () => {
    renderShell("/");
    await flush();
    expect(slot().getAttribute("data-account")).toBe("authenticated");
    const button = within(slot()).getByRole("button", {
      name: TEXTOS["conta.menu.rotulo"](ME.name),
    });
    expect(button).toBe(accountButton());
    expect(button.tagName).toBe("BUTTON");
    expect(button.getAttribute("type")).toBe("button");
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(button.getAttribute("aria-controls")).toBe(menu().id);
    expect(menu().id).not.toBe("");
    expect(menu().hidden).toBe(true);
    expect(button.querySelector(".ruvor-account__name")?.textContent).toBe(ME.name);
    const avatar = button.querySelector('[data-part="avatar"]') as HTMLElement;
    expect(avatar.textContent).toBe("AS");
    expect(avatar.getAttribute("aria-hidden")).toBe("true");
    expect(
      within(slot()).queryByRole("link", { name: TEXTOS["conta.entrar"] }),
    ).toBeNull();
  });

  it("do carregando ao logado, o lugar é o mesmo elemento (sem salto)", async () => {
    let resolveMe: (r: Response) => void = () => {};
    vi.mocked(fetch).mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          resolveMe = resolve;
        }),
    );
    renderShell("/");
    await flush();
    const before = slot();
    expect(before.getAttribute("data-account")).toBe("loading");
    await act(async () => {
      resolveMe({ ok: true, status: 200, json: async () => ME } as unknown as Response);
    });
    await flush();
    expect(slot()).toBe(before);
    expect(before.getAttribute("data-account")).toBe("authenticated");
  });
});

describe("as iniciais (o conta.html)", () => {
  it.each([
    ["Ana Beatriz Souza", "ana@exemplo.com", "AS"],
    ["ana", "ana@exemplo.com", "A"],
    ["  maria   da silva ", "m@exemplo.com", "MS"],
    ["   ", "zeca@exemplo.com", "Z"],
    ["", " bia@exemplo.com", "B"],
  ])("%j, %j → %j", (name, email, expected) => {
    expect(initials(name, email)).toBe(expected);
  });
});

describe("o menu aberto (RF-09)", () => {
  it("abre pelo botão: o nome, o e-mail, a organização, Trocar a senha com o next, Sair", async () => {
    renderShell("/ativos/ITUB4?x=1");
    await flush();
    await click(accountButton());
    expect(isOpen()).toBe(true);
    expect(within(menu()).getByText(ME.email)).toBeDefined();
    expect(menu().querySelector('[data-part="menu-nome"]')?.textContent).toBe(ME.name);
    const org = menu().querySelector('[data-part="menu-organizacao"]') as HTMLElement;
    expect(org.textContent).toBe(
      `${TEXTOS["conta.menu.organizacao"]}${ME.organization.name}`,
    );
    const password = within(menu()).getByRole("link", {
      name: TEXTOS["conta.menu.senha"],
    });
    expect(password.getAttribute("href")).toBe(
      `/conta/senha?next=${encodeURIComponent("/ativos/ITUB4?x=1")}`,
    );
    expect(sairButton().getAttribute("data-part")).toBe("menu-sair");
    for (const part of ["menu", "menu-nome", "menu-organizacao", "menu-sair"]) {
      expect(document.querySelectorAll(`[data-part="${part}"]`)).toHaveLength(1);
    }
    expect(within(menu()).queryByRole("alert")).toBeNull();
  });

  it("o botão de novo fecha", async () => {
    renderShell("/");
    await flush();
    await click(accountButton());
    await click(accountButton());
    expect(isOpen()).toBe(false);
  });

  it.each([
    ["admin, organização real", true, ME],
    ["admin, conta pessoal", false, PERSONAL],
    ["membro, organização real", false, MEMBER],
    ["membro, conta pessoal", false, { ...PERSONAL, role: "member" as const }],
  ])("Usuários da organização — %s → mostra: %s", async (_n, shown, me) => {
    reply(ME_KEY, ok(me));
    renderShell("/");
    await flush();
    await click(accountButton());
    const link = within(menu()).queryByRole("link", {
      name: TEXTOS["conta.menu.usuarios"],
    });
    if (shown) {
      expect(link?.getAttribute("href")).toBe("/organizacao/usuarios");
    } else {
      expect(link).toBeNull();
      expect(menu().textContent).not.toContain(TEXTOS["conta.menu.usuarios"]);
    }
  });

  it("a conta pessoal mostra 'Conta pessoal' no lugar do nome da organização", async () => {
    reply(ME_KEY, ok(PERSONAL));
    renderShell("/");
    await flush();
    await click(accountButton());
    const org = menu().querySelector('[data-part="menu-organizacao"]') as HTMLElement;
    expect(org.textContent).toBe(
      `${TEXTOS["conta.menu.organizacao"]}${TEXTOS["conta.menu.pessoal"]}`,
    );
  });
});

describe("o teclado, o Esc, o clique fora e o foco (RF-09)", () => {
  it("Esc fecha e devolve o foco ao botão de conta", async () => {
    renderShell("/");
    await flush();
    accountButton().focus();
    await click(accountButton());
    sairButton().focus();
    expect(document.activeElement).toBe(sairButton());
    await act(async () => {
      fireEvent.keyDown(document.activeElement as Element, { key: "Escape" });
    });
    expect(isOpen()).toBe(false);
    expect(document.activeElement).toBe(accountButton());
  });

  it("outra tecla não fecha", async () => {
    renderShell("/");
    await flush();
    await click(accountButton());
    await act(async () => {
      fireEvent.keyDown(document.body, { key: "Enter" });
    });
    expect(isOpen()).toBe(true);
  });

  it("o clique fora fecha; o clique dentro do menu, não", async () => {
    renderShell("/");
    await flush();
    await click(accountButton());
    await click(menu().querySelector('[data-part="menu-nome"]') as Element);
    expect(isOpen()).toBe(true);
    await click(screen.getByTestId("destino"));
    expect(isOpen()).toBe(false);
  });

  it("o clique num item fecha o menu e navega", async () => {
    const router = renderShell("/ativos/ITUB4");
    await flush();
    await click(accountButton());
    await click(within(menu()).getByRole("link", { name: TEXTOS["conta.menu.senha"] }));
    expect(router.state.location.pathname).toBe("/conta/senha");
    expect(router.state.location.search).toBe("?next=%2Fativos%2FITUB4");
    expect(isOpen()).toBe(false);
  });

  it("o Tab que sai do último item fecha; o foco que anda dentro do menu, não", async () => {
    renderShell("/");
    await flush();
    await click(accountButton());
    const password = within(menu()).getByRole("link", {
      name: TEXTOS["conta.menu.senha"],
    });
    await act(async () => {
      fireEvent.focusOut(password, { relatedTarget: sairButton() });
    });
    expect(isOpen()).toBe(true);
    const brand = screen.getByRole("link", { name: TEXTOS["casco.marca.rotulo"] });
    await act(async () => {
      fireEvent.focusOut(sairButton(), { relatedTarget: brand });
    });
    expect(isOpen()).toBe(false);
  });
});

describe("Sair (RF-10)", () => {
  it.each([
    ["204", NO_CONTENT],
    ["401 (a sessão já tinha acabado)", ANON],
  ])("%s numa página pública: anônimo, na mesma página, sem erro", async (_n, r) => {
    reply(LOGOUT, r);
    const router = renderShell("/ativos/ITUB4");
    await flush();
    await click(accountButton());
    await click(sairButton());
    await flush();
    expect(logoutCalls()).toHaveLength(1);
    expect(slot().getAttribute("data-account")).toBe("anonymous");
    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    expect(screen.queryByRole("alert")).toBeNull();
    expect(document.body.textContent).not.toContain(API_MESSAGE);
  });

  it("na busca (/) fica na busca", async () => {
    reply(LOGOUT, NO_CONTENT);
    const router = renderShell("/");
    await flush();
    await click(accountButton());
    await click(sairButton());
    await flush();
    expect(router.state.location.pathname).toBe("/");
    expect(slot().getAttribute("data-account")).toBe("anonymous");
  });

  it.each(["/conta/senha", "/organizacao/usuarios"])("em %s vai a /", async (path) => {
    reply(LOGOUT, NO_CONTENT);
    const router = renderShell(path);
    await flush();
    await click(accountButton());
    await click(sairButton());
    await flush();
    expect(router.state.location.pathname).toBe("/");
    expect(slot().getAttribute("data-account")).toBe("anonymous");
  });

  it.each([
    ["500", fail(500, "server_error")],
    ["403 csrf_failed", fail(403, "csrf_failed")],
    ["rede", "network" as Reply],
  ])(
    "o Sair que falha (%s): a sessão fica, o menu aberto, a linha de alerta e o mesmo Sair",
    async (_n, r) => {
      reply(LOGOUT, r);
      reply("GET /api/v1/auth/csrf", NO_CONTENT);
      const router = renderShell("/conta/senha");
      await flush();
      await click(accountButton());
      const sair = sairButton();
      const password = within(menu()).getByRole("link", {
        name: TEXTOS["conta.menu.senha"],
      });
      await click(sair);
      await flush();
      expect(slot().getAttribute("data-account")).toBe("authenticated");
      expect(isOpen()).toBe(true);
      expect(within(menu()).getByRole("alert").textContent).toBe(
        TEXTOS["conta.menu.sairFalhou"],
      );
      // Só acrescenta a linha: o Sair e os outros itens são os mesmos elementos.
      expect(sairButton()).toBe(sair);
      expect(
        within(menu()).getByRole("link", { name: TEXTOS["conta.menu.senha"] }),
      ).toBe(password);
      expect(router.state.location.pathname).toBe("/conta/senha");
      expect(document.body.textContent).not.toContain(API_MESSAGE);
    },
  );

  it("depois da falha, o Sair de novo sai", async () => {
    reply(LOGOUT, fail(500, "server_error"), NO_CONTENT);
    renderShell("/ativos/ITUB4");
    await flush();
    await click(accountButton());
    await click(sairButton());
    await flush();
    expect(within(menu()).getByRole("alert")).toBeDefined();
    await click(sairButton());
    await flush();
    expect(logoutCalls()).toHaveLength(2);
    expect(slot().getAttribute("data-account")).toBe("anonymous");
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("os dois avisos (RF-16)", () => {
  function renderNotice(ended: boolean, path = "/ativos/ITUB4?x=1") {
    const router = createMemoryRouter(
      [{ path: "*", element: <SignInNotice ended={ended} /> }],
      { initialEntries: [path] },
    );
    render(<RouterProvider router={router} />);
  }

  it("ended: 'a sua sessão terminou', com role=alert e o Entrar com a página atual", () => {
    renderNotice(true);
    const notice = document.querySelector("[data-signin-notice]") as HTMLElement;
    expect(notice.getAttribute("data-signin-notice")).toBe("ended");
    expect(notice.getAttribute("role")).toBe("alert");
    expect(notice.textContent).toContain(TEXTOS["conta.aviso.terminou"]);
    expect(notice.textContent).not.toContain(TEXTOS["conta.aviso.paraQuemEntrou"]);
    expect(notice.textContent).toContain(TEXTOS["conta.aviso.volta"]);
    expect(
      screen.getByRole("link", { name: TEXTOS["conta.entrar"] }).getAttribute("href"),
    ).toBe("/entrar?next=%2Fativos%2FITUB4%3Fx%3D1");
  });

  it("sem ended: 'esta página é para quem entrou', sem role=alert", () => {
    renderNotice(false, "/conta/senha");
    const notice = document.querySelector("[data-signin-notice]") as HTMLElement;
    expect(notice.getAttribute("data-signin-notice")).toBe("required");
    expect(notice.hasAttribute("role")).toBe(false);
    expect(notice.textContent).toContain(TEXTOS["conta.aviso.paraQuemEntrou"]);
    expect(notice.textContent).not.toContain(TEXTOS["conta.aviso.terminou"]);
    expect(
      screen.getByRole("link", { name: TEXTOS["conta.entrar"] }).getAttribute("href"),
    ).toBe("/entrar?next=%2Fconta%2Fsenha");
  });
});

describe("/conta/senha sem conta (RF-04, RF-16)", () => {
  it("anônimo desde a carga: o aviso 'para quem entrou', não o de sessão terminada, e nada do formulário", async () => {
    reply(ME_KEY, ANON);
    const router = renderRoutes("/conta/senha?next=%2Fativos%2FITUB4");
    await flush();
    const page = document.querySelector('[data-screen="senha"]') as HTMLElement;
    expect(page).not.toBeNull();
    expect(page.querySelector('[data-signin-notice="required"]')).not.toBeNull();
    expect(document.querySelector('[data-signin-notice="ended"]')).toBeNull();
    expect(page.textContent).toContain(TEXTOS["conta.aviso.paraQuemEntrou"]);
    expect(page.textContent).not.toContain(TEXTOS["conta.aviso.terminou"]);
    expect(within(page).queryByRole("alert")).toBeNull();
    expect(document.querySelector('[data-part="form"]')).toBeNull();
    expect(screen.queryByLabelText(TEXTOS["senha.atual.rotulo"])).toBeNull();
    expect(
      within(page)
        .getByRole("link", { name: TEXTOS["conta.entrar"] })
        .getAttribute("href"),
    ).toBe(`/entrar?next=${encodeURIComponent("/conta/senha?next=%2Fativos%2FITUB4")}`);
    // A barra mostra "Entrar"; a página fica onde estava; só o auth/me foi pedido.
    expect(slot().getAttribute("data-account")).toBe("anonymous");
    expect(router.state.location.pathname).toBe("/conta/senha");
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([ME_KEY]);
  });

  it("com a sessão carregando: o esqueleto, sem formulário, sem aviso, sem pedido", async () => {
    reply(ME_KEY, null);
    renderRoutes("/conta/senha");
    await flush();
    const page = document.querySelector('[data-screen="senha"]') as HTMLElement;
    expect(page.getAttribute("aria-busy")).toBe("true");
    expect(page.querySelector(".ruvor-skeleton")).not.toBeNull();
    expect(document.querySelector("[data-signin-notice]")).toBeNull();
    expect(document.querySelector('[data-part="form"]')).toBeNull();
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([ME_KEY]);
  });

  it("logado: o formulário, sem aviso", async () => {
    renderRoutes("/conta/senha");
    await flush();
    expect(document.querySelector('[data-part="form"]')).not.toBeNull();
    expect(document.querySelector("[data-signin-notice]")).toBeNull();
  });
});
