/**
 * V-07 (RF-06) e a parte de `/entrar` do RF-04: a tela de entrada mostra os textos aprovados no
 * `entrada.html`, lidos de `TEXTOS`, e nenhum dos nove itens que saíram do `01-login`; cada
 * `code` vira a frase dele, e a mensagem da API nunca chega à tela; o 429 com e sem
 * `wait_seconds`; o campo vazio fica com `aria-invalid` e `aria-describedby`, sem pedido; o
 * sucesso vai à sessão e ao `next` por substituição; quem já está logado e abre `/entrar` vai
 * ao `next`; os links levam o `next` adiante.
 *
 * O `fetch` é um duplo que responde pelo endereço e pelo método; `null` deixa o pedido pendente.
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

import { App, routes } from "../src/App";
import { TEXTOS } from "../src/content/textos";
import { SignInScreen } from "../src/screens/SignInScreen";
import { SessionProvider, useSession } from "../src/session/SessionProvider";
import type { Me } from "../src/session/types";

// O `App` chega na tela do ativo, que importa o uPlot; o uPlot pede `matchMedia` no import.
vi.mock("uplot", () => ({ default: class {} }));

const ME: Me = {
  email: "ana@exemplo.com",
  name: "Ana",
  role: "member",
  must_change_password: false,
  is_staff: false,
  organization: { name: "Ana", slug: "ana", is_personal: true },
};

/** A mensagem que a API manda em todo erro destes testes: nunca pode aparecer na tela. */
const API_MESSAGE = "MENSAGEM CRUA DA API";

type Reply = { status: number; body: unknown } | "network" | "not-json" | null;

const ok = (body: unknown): Reply => ({ status: 200, body });
const fail = (status: number, code: string, details: object = {}): Reply => ({
  status,
  body: { error: { code, message: API_MESSAGE, details } },
});
const ANON = fail(401, "not_authenticated");

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
      if (r === "not-json") {
        return Promise.resolve({
          ok: false,
          status: 500,
          json: async () => {
            throw new SyntaxError("Unexpected token <");
          },
        } as unknown as Response);
      }
      return Promise.resolve({
        ok: r.status >= 200 && r.status < 300,
        status: r.status,
        json: async () => r.body,
      } as unknown as Response);
    }),
  );
}

const LOGIN = "POST /api/v1/auth/login";
const loginCalls = () =>
  calls.filter((c) => c.method === "POST" && c.url === "/api/v1/auth/login");

/** O estado da sessão, mostrado pela rota de destino dos testes de navegação. */
function Destination() {
  const session = useSession();
  return <p data-testid="destino">{session.status}</p>;
}

/** A entrada e um destino qualquer, sob o provedor de verdade, num roteador de memória. */
function renderAt(path: string, entries: string[] = []) {
  const router = createMemoryRouter(
    [
      {
        element: <SessionProvider />,
        children: [
          { path: "entrar", element: <SignInScreen /> },
          { path: "*", element: <Destination /> },
        ],
      },
    ],
    { initialEntries: [...entries, path], initialIndex: entries.length },
  );
  render(<RouterProvider router={router} />);
  return router;
}

function emailInput(): HTMLInputElement {
  return screen.getByLabelText(TEXTOS["acesso.email.rotulo"]) as HTMLInputElement;
}

function passwordInput(): HTMLInputElement {
  return screen.getByLabelText(TEXTOS["acesso.senha.rotulo"]) as HTMLInputElement;
}

function submitButton(): HTMLButtonElement {
  return document.querySelector('[data-part="botao-entrar"]') as HTMLButtonElement;
}

function fill(email: string, password: string): void {
  fireEvent.change(emailInput(), { target: { value: email } });
  fireEvent.change(passwordInput(), { target: { value: password } });
}

async function submit(): Promise<void> {
  await act(async () => {
    fireEvent.click(submitButton());
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

beforeEach(() => {
  replies = {};
  reply("GET /api/v1/auth/me", ANON);
  // biome-ignore lint/suspicious/noDocumentCookie: o login manda o token do cookie de verdade.
  document.cookie = "csrftoken=tok; path=/";
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  // biome-ignore lint/suspicious/noDocumentCookie: limpa o cookie gravado no beforeEach.
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
  window.history.replaceState(null, "", "/");
});

describe("os textos aprovados (V-07)", () => {
  const VISIVEIS = [
    "acesso.cena.eyebrow",
    "acesso.cena.titulo",
    "acesso.cena.texto",
    "acesso.eyebrow",
    "acesso.titulo",
    "acesso.sub",
    "acesso.email.rotulo",
    "acesso.senha.rotulo",
    "acesso.senha.nota",
    "acesso.entrar",
    "acesso.semConta",
    "acesso.criarConta",
    "acesso.continuar",
  ] as const;

  it.each(VISIVEIS)("%s está na tela, lido de TEXTOS", async (chave) => {
    renderAt("/entrar");
    await flush();
    expect(screen.getByText(TEXTOS[chave])).toBeDefined();
  });

  it("o exemplo do e-mail, o texto alternativo da marca e os títulos", async () => {
    renderAt("/entrar");
    await flush();
    expect(emailInput().placeholder).toBe(TEXTOS["acesso.email.placeholder"]);
    expect(passwordInput().placeholder).toBe("");
    expect(screen.getByAltText(TEXTOS["acesso.cena.marca"])).toBeDefined();
    expect(
      screen.getByRole("heading", { level: 1, name: TEXTOS["acesso.cena.titulo"] }),
    ).toBeDefined();
    expect(screen.getByRole("form", { name: TEXTOS["acesso.titulo"] })).toBeDefined();
  });

  it("nenhum dos nove itens que saíram do 01-login", async () => {
    renderAt("/entrar");
    await flush();
    const html = document.body.innerHTML;
    for (const fora of [
      "Workspace",
      "workspace",
      "SSO",
      "Esqueci",
      "corporativo",
      "Estado previsto",
      "Suporte",
      "Privacidade",
      "segregados",
      "times de risco",
      "Verifique o workspace",
      "nome@empresa.com",
    ]) {
      expect(html).not.toContain(fora);
    }
  });

  it("as marcas para o navegador: data-screen e os nove data-part, uma vez cada", async () => {
    renderAt("/entrar");
    await flush();
    expect(document.querySelectorAll('[data-screen="entrada"]')).toHaveLength(1);
    for (const part of [
      "cena",
      "form",
      "titulo",
      "campo-email",
      "campo-senha",
      "nota-senha",
      "botao-entrar",
      "link-cadastro",
      "link-continuar",
    ]) {
      expect(document.querySelectorAll(`[data-part="${part}"]`)).toHaveLength(1);
    }
  });

  it("fica fora do casco: sem a barra superior", async () => {
    renderAt("/entrar");
    await flush();
    expect(screen.queryByRole("banner")).toBeNull();
  });
});

describe("o campo vazio (RF-06)", () => {
  it("os dois vazios: aria-invalid e aria-describedby nos dois, foco no e-mail, sem pedido", async () => {
    renderAt("/entrar");
    await flush();
    await submit();

    const email = emailInput();
    const password = passwordInput();
    expect(email.getAttribute("aria-invalid")).toBe("true");
    expect(password.getAttribute("aria-invalid")).toBe("true");

    const emailIds = (email.getAttribute("aria-describedby") ?? "").split(" ");
    expect(emailIds).toHaveLength(1);
    expect(document.getElementById(emailIds[0])?.textContent).toBe(
      TEXTOS["acesso.erro.emailVazio"],
    );

    const passwordIds = (password.getAttribute("aria-describedby") ?? "").split(" ");
    expect(passwordIds).toHaveLength(2);
    expect(document.getElementById(passwordIds[0])?.textContent).toBe(
      TEXTOS["acesso.erro.senhaVazia"],
    );
    expect(document.getElementById(passwordIds[1])?.textContent).toBe(
      TEXTOS["acesso.senha.nota"],
    );

    expect(document.activeElement).toBe(email);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(loginCalls()).toHaveLength(0);
  });

  it("só a senha vazia: o erro nela, foco nela, o e-mail sem erro, sem pedido", async () => {
    renderAt("/entrar");
    await flush();
    fill("ana@exemplo.com", "");
    await submit();

    expect(emailInput().getAttribute("aria-invalid")).toBeNull();
    expect(emailInput().getAttribute("aria-describedby")).toBeNull();
    expect(passwordInput().getAttribute("aria-invalid")).toBe("true");
    expect(document.activeElement).toBe(passwordInput());
    expect(screen.getByText(TEXTOS["acesso.erro.senhaVazia"])).toBeDefined();
    expect(screen.queryByText(TEXTOS["acesso.erro.emailVazio"])).toBeNull();
    expect(loginCalls()).toHaveLength(0);
  });

  it("o e-mail só de espaços conta como vazio", async () => {
    renderAt("/entrar");
    await flush();
    fill("   ", "segredo");
    await submit();
    expect(emailInput().getAttribute("aria-invalid")).toBe("true");
    expect(loginCalls()).toHaveLength(0);
  });

  it("sem erro, a senha descreve-se só pela nota", async () => {
    renderAt("/entrar");
    await flush();
    const ids = (passwordInput().getAttribute("aria-describedby") ?? "").split(" ");
    expect(ids).toHaveLength(1);
    expect(document.getElementById(ids[0])?.textContent).toBe(
      TEXTOS["acesso.senha.nota"],
    );
    expect(passwordInput().getAttribute("aria-invalid")).toBeNull();
  });
});

describe("o pedido e os erros gerais (RF-06)", () => {
  it("o POST auth/login leva o e-mail e a senha em JSON", async () => {
    reply(LOGIN, null);
    renderAt("/entrar");
    await flush();
    fill("ana@exemplo.com", "segredo");
    await submit();
    expect(loginCalls()).toHaveLength(1);
    expect(JSON.parse(loginCalls()[0].body ?? "null")).toEqual({
      email: "ana@exemplo.com",
      password: "segredo",
    });
  });

  it("enviando: o botão diz Entrando…, desabilitado e aria-busy", async () => {
    reply(LOGIN, null);
    renderAt("/entrar");
    await flush();
    fill("ana@exemplo.com", "segredo");
    await submit();
    const button = submitButton();
    expect(button.disabled).toBe(true);
    expect(button.getAttribute("aria-busy")).toBe("true");
    expect(button.textContent).toBe(TEXTOS["acesso.entrando"]);
  });

  it.each([
    [
      "invalid_credentials",
      fail(400, "invalid_credentials"),
      TEXTOS["acesso.erro.credenciais"],
    ],
    [
      "too_many_requests com 42 s",
      fail(429, "too_many_requests", { wait_seconds: 42 }),
      "Muitas tentativas. Tente de novo em 42 s.",
    ],
    [
      "too_many_requests com 900 s (o bloqueio)",
      fail(429, "too_many_requests", { wait_seconds: 900 }),
      "Muitas tentativas. Tente de novo em 15 min.",
    ],
    [
      "too_many_requests sem wait_seconds",
      fail(429, "too_many_requests"),
      "Muitas tentativas. Aguarde um pouco e tente de novo.",
    ],
    ["csrf_failed", fail(403, "csrf_failed"), TEXTOS["acesso.erro.csrf"]],
    ["outro code", fail(400, "validation_failed"), TEXTOS["acesso.erro.outro"]],
    ["outro code (500 da API)", fail(500, "server_error"), TEXTOS["acesso.erro.outro"]],
    ["erro de rede", "network" as Reply, TEXTOS["acesso.erro.rede"]],
    ["fora do formato", "not-json" as Reply, TEXTOS["acesso.erro.rede"]],
    ["200 sem a forma do me", ok({ ok: true }), TEXTOS["acesso.erro.rede"]],
  ])(
    "%s → a frase dele, e a mensagem da API fora da tela",
    async (_nome, resposta, frase) => {
      reply(LOGIN, resposta);
      reply("GET /api/v1/auth/csrf", { status: 204, body: null });
      const router = renderAt("/entrar");
      await flush();
      fill("ana@exemplo.com", "segredo");
      await submit();
      await flush();

      const alert = await screen.findByRole("alert");
      expect(alert.textContent).toBe(frase);
      expect(document.body.textContent).not.toContain(API_MESSAGE);
      // Os dois campos seguem preenchidos, a tela fica, e o foco volta ao "Entrar".
      expect(emailInput().value).toBe("ana@exemplo.com");
      expect(passwordInput().value).toBe("segredo");
      expect(router.state.location.pathname).toBe("/entrar");
      await waitFor(() => expect(document.activeElement).toBe(submitButton()));
      expect(submitButton().disabled).toBe(false);
      expect(submitButton().textContent).toBe(TEXTOS["acesso.entrar"]);
    },
  );

  it("csrf_failed: a frase só depois da repetição do cliente (um auth/csrf e dois POST)", async () => {
    reply(LOGIN, fail(403, "csrf_failed"));
    reply("GET /api/v1/auth/csrf", { status: 204, body: null });
    renderAt("/entrar");
    await flush();
    fill("ana@exemplo.com", "segredo");
    await submit();
    await screen.findByRole("alert");
    expect(loginCalls()).toHaveLength(2);
    expect(calls.filter((c) => c.url === "/api/v1/auth/csrf")).toHaveLength(1);
  });

  it("o erro geral some ao enviar de novo, e o de campo não aparece junto", async () => {
    reply(LOGIN, fail(400, "invalid_credentials"), null);
    renderAt("/entrar");
    await flush();
    fill("ana@exemplo.com", "segredo");
    await submit();
    await screen.findByRole("alert");

    fill("ana@exemplo.com", "");
    await submit();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByText(TEXTOS["acesso.erro.senhaVazia"])).toBeDefined();
  });
});

describe("o sucesso e o next (RF-04, RF-06)", () => {
  it("200 me → a sessão logada e o next, por substituição", async () => {
    reply(LOGIN, ok(ME));
    const router = renderAt("/entrar?next=%2Fativos%2FITUB4%3Fx%3D1", ["/"]);
    await flush();
    fill("ana@exemplo.com", "segredo");
    await submit();
    await flush();

    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    expect(router.state.location.search).toBe("?x=1");
    expect(router.state.historyAction).toBe("REPLACE");
    expect(screen.getByTestId("destino").textContent).toBe("authenticated");
    // Um só auth/me, o da montagem: a sessão veio da resposta do login.
    expect(calls.filter((c) => c.url === "/api/v1/auth/me")).toHaveLength(1);

    // A entrada saiu do histórico: voltar leva a quem estava antes dela.
    await act(async () => {
      await router.navigate(-1);
    });
    expect(router.state.location.pathname).toBe("/");
  });

  it("o tamanho do histórico do navegador não cresce", async () => {
    reply(LOGIN, ok(ME));
    window.history.pushState(null, "", "/entrar?next=%2Fativos%2FITUB4");
    const before = window.history.length;
    render(<App />);
    await flush();
    fill("ana@exemplo.com", "segredo");
    await submit();
    await flush();

    expect(window.location.pathname).toBe("/ativos/ITUB4");
    expect(window.history.length).toBe(before);
  });

  it.each([
    ["sem next", "/entrar", "/"],
    ["next de outra origem", "/entrar?next=https%3A%2F%2Fevil.com", "/"],
    ["next que volta à entrada", "/entrar?next=%2Fentrar", "/"],
  ])("%s → a busca", async (_nome, path, destino) => {
    reply(LOGIN, ok(ME));
    const router = renderAt(path);
    await flush();
    fill("ana@exemplo.com", "segredo");
    await submit();
    await flush();
    expect(router.state.location.pathname).toBe(destino);
    expect(router.state.historyAction).toBe("REPLACE");
  });

  it("logado que abre /entrar vai ao next, por substituição, sem pedir login", async () => {
    reply("GET /api/v1/auth/me", ok(ME));
    const router = renderAt("/entrar?next=%2Fativos%2FITUB4", ["/"]);
    await waitFor(() => expect(router.state.location.pathname).toBe("/ativos/ITUB4"));
    expect(router.state.historyAction).toBe("REPLACE");
    expect(loginCalls()).toHaveLength(0);
  });

  it("logado que abre /entrar sem next vai a /", async () => {
    reply("GET /api/v1/auth/me", ok(ME));
    const router = renderAt("/entrar", ["/ativos/ITUB4"]);
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
    expect(router.state.historyAction).toBe("REPLACE");
  });

  it("anônimo fica na entrada", async () => {
    const router = renderAt("/entrar?next=%2Fativos%2FITUB4");
    await flush();
    expect(router.state.location.pathname).toBe("/entrar");
    expect(document.querySelector('[data-screen="entrada"]')).not.toBeNull();
  });
});

describe("os links (RF-06)", () => {
  it("Criar conta leva o mesmo next, codificado; Continuar sem entrar vai ao next", async () => {
    renderAt("/entrar?next=%2Fativos%2FITUB4%3Fx%3D1%26y%3D2");
    await flush();
    const signUp = screen.getByRole("link", { name: TEXTOS["acesso.criarConta"] });
    expect(signUp.getAttribute("href")).toBe(
      "/cadastro?next=%2Fativos%2FITUB4%3Fx%3D1%26y%3D2",
    );
    const skip = screen.getByRole("link", { name: TEXTOS["acesso.continuar"] });
    expect(skip.getAttribute("href")).toBe("/ativos/ITUB4?x=1&y=2");
  });

  it("sem next: /cadastro e /", async () => {
    renderAt("/entrar");
    await flush();
    expect(
      screen
        .getByRole("link", { name: TEXTOS["acesso.criarConta"] })
        .getAttribute("href"),
    ).toBe("/cadastro");
    expect(
      screen
        .getByRole("link", { name: TEXTOS["acesso.continuar"] })
        .getAttribute("href"),
    ).toBe("/");
  });

  it("Continuar sem entrar com next de fora vai a /", async () => {
    renderAt("/entrar?next=%2F%2Fevil.com");
    await flush();
    expect(
      screen
        .getByRole("link", { name: TEXTOS["acesso.continuar"] })
        .getAttribute("href"),
    ).toBe("/");
  });
});

describe("a rota /entrar em routes (RF-04)", () => {
  it("createMemoryRouter(routes) monta a entrada em /entrar, fora do casco", async () => {
    render(
      <RouterProvider
        router={createMemoryRouter(routes, { initialEntries: ["/entrar"] })}
      />,
    );
    await flush();
    expect(document.querySelector('[data-screen="entrada"]')).not.toBeNull();
    expect(screen.queryByRole("banner")).toBeNull();
  });
});
