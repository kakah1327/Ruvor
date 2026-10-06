/**
 * V-08, a metade da troca de senha (RF-08), e o bloqueio do RF-05 (V-06): os textos aprovados
 * no `senha.html`, lidos de `TEXTOS`; campo vazio e a confirmação diferente sem pedido; os
 * erros da API no campo certo; a troca → a frase das outras sessões, com "Continuar" — na
 * voluntária, `reload()` no 204 e o `next`; na obrigatória, `reload()` só no "Continuar", e a
 * mesma URL passa a mostrar a tela dela; com `must_change_password`, toda rota mostra a troca
 * na URL corrente, menos `/entrar` e `/cadastro`; o 401 → o aviso de sessão terminada, e o
 * `expired()` no clique em "Entrar".
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

import { routes } from "../src/App";
import { TEXTOS } from "../src/content/textos";
import { PasswordScreen } from "../src/screens/PasswordScreen";
import { SessionProvider, useSession } from "../src/session/SessionProvider";
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
const PROVISIONAL: Me = { ...ME, must_change_password: true };

/** A mensagem que a API manda em todo erro destes testes: nunca pode aparecer na tela. */
const API_MESSAGE = "MENSAGEM CRUA DA API";

type Reply = { status: number; body: unknown } | "network" | "not-json" | null;

const ok = (body: unknown): Reply => ({ status: 200, body });
const fail = (status: number, code: string, details: object = {}): Reply => ({
  status,
  body: { error: { code, message: API_MESSAGE, details } },
});
const NO_CONTENT: Reply = { status: 204, body: null };
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

const ME_KEY = "GET /api/v1/auth/me";
const PASSWORD = "POST /api/v1/auth/password";
const passwordCalls = () =>
  calls.filter((c) => c.method === "POST" && c.url === "/api/v1/auth/password");
const meCalls = () =>
  calls.filter((c) => c.method === "GET" && c.url === "/api/v1/auth/me");

/** A sessão, mostrada por um destino qualquer: `status` e, no anônimo, `ended`. */
function SessionView() {
  const session = useSession();
  return (
    <p data-testid="sessao">
      {session.status === "anonymous" ? `anonymous:${session.ended}` : session.status}
    </p>
  );
}

/** A troca voluntária e destinos quaisquer, sob o provedor de verdade, num roteador de memória. */
function renderVoluntary(path: string) {
  const router = createMemoryRouter(
    [
      {
        element: <SessionProvider />,
        children: [
          { path: "conta/senha", element: <PasswordScreen mode="voluntary" /> },
          { path: "*", element: <SessionView /> },
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

function input(label: string): HTMLInputElement {
  return screen.getByLabelText(label) as HTMLInputElement;
}

const currentInput = () => input(TEXTOS["senha.atual.rotulo"]);
const newInput = () => input(TEXTOS["senha.nova.rotulo"]);
const confirmationInput = () => input(TEXTOS["senha.confirmacao.rotulo"]);

function submitButton(): HTMLButtonElement {
  return screen.getByRole("button", {
    name: TEXTOS["senha.trocar"],
  }) as HTMLButtonElement;
}

function fill(current: string, next: string, confirmation: string): void {
  fireEvent.change(currentInput(), { target: { value: current } });
  fireEvent.change(newInput(), { target: { value: next } });
  fireEvent.change(confirmationInput(), { target: { value: confirmation } });
}

const fillValid = () =>
  fill("senha-atual-1", "nova-senha-longa-9", "nova-senha-longa-9");

async function submit(): Promise<void> {
  await act(async () => {
    fireEvent.click(submitButton());
  });
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

/** O texto das mensagens de erro ligadas ao campo pelo `aria-describedby` (sem a dica). */
function fieldErrors(field: HTMLInputElement): string[] {
  const ids = (field.getAttribute("aria-describedby") ?? "").split(" ").filter(Boolean);
  return ids
    .map((id) => document.getElementById(id))
    .filter(
      (el): el is HTMLElement => el?.classList.contains("ruvor-field__errors") === true,
    )
    .flatMap((group) =>
      [...group.querySelectorAll(".ruvor-field__error")].map(
        (e) => e.textContent ?? "",
      ),
    );
}

const required = () => document.querySelector('[data-screen="senha-obrigatoria"]');
// A tela do ativo: a barra de abas dela.
const assetScreen = () => document.querySelector(".ruvor-tabs");

beforeEach(() => {
  replies = {};
  reply(ME_KEY, ok(ME));
  // biome-ignore lint/suspicious/noDocumentCookie: a troca manda o token do cookie de verdade.
  document.cookie = "csrftoken=tok; path=/";
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  // biome-ignore lint/suspicious/noDocumentCookie: limpa o cookie gravado no beforeEach.
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("a voluntária: os textos e as marcas (RF-08)", () => {
  const VISIVEIS = [
    "senha.eyebrow",
    "senha.sub",
    "senha.atual.rotulo",
    "senha.nova.rotulo",
    "senha.confirmacao.rotulo",
    "acesso.senha.dica",
    "acesso.senha.requisito.tamanho",
    "acesso.senha.requisito.numeros",
    "acesso.senha.requisito.parecida",
    "acesso.senha.requisito.comum",
  ] as const;

  it.each(VISIVEIS)("%s está na tela, lido de TEXTOS", async (chave) => {
    renderVoluntary("/conta/senha");
    await flush();
    expect(screen.getByText(TEXTOS[chave])).toBeDefined();
  });

  it("o título da página, o botão e o formulário rotulado por ele", async () => {
    renderVoluntary("/conta/senha");
    await flush();
    expect(
      screen.getByRole("heading", { level: 1, name: TEXTOS["senha.titulo"] }),
    ).toBeDefined();
    expect(screen.getByRole("form", { name: TEXTOS["senha.titulo"] })).toBeDefined();
    expect(submitButton().textContent).toBe(TEXTOS["senha.trocar"]);
    expect(screen.queryByText(TEXTOS["senha.obrigatoria.sair"])).toBeNull();
  });

  it("os campos: a dica antes da nova e no aria-describedby dela; o autocomplete", async () => {
    renderVoluntary("/conta/senha");
    await flush();
    const hint = document.querySelector('[data-part="dica-senha"]') as HTMLElement;
    expect(
      hint.compareDocumentPosition(newInput()) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(newInput().getAttribute("aria-describedby")).toBe(hint.id);
    expect(currentInput().getAttribute("autocomplete")).toBe("current-password");
    expect(newInput().getAttribute("autocomplete")).toBe("new-password");
    expect(confirmationInput().getAttribute("autocomplete")).toBe("new-password");
  });

  it("data-screen=senha e os seis data-part, uma vez cada", async () => {
    renderVoluntary("/conta/senha");
    await flush();
    expect(document.querySelectorAll('[data-screen="senha"]')).toHaveLength(1);
    for (const part of [
      "form",
      "campo-atual",
      "campo-nova",
      "campo-confirmacao",
      "dica-senha",
      "botao-trocar",
    ]) {
      expect(document.querySelectorAll(`[data-part="${part}"]`)).toHaveLength(1);
    }
    expect(document.querySelector('[data-part="form-obrigatoria"]')).toBeNull();
  });

  it("em routes, /conta/senha fica no casco", async () => {
    renderRoutes("/conta/senha");
    await flush();
    expect(document.querySelector('[data-screen="senha"]')).not.toBeNull();
    expect(screen.getByRole("banner")).toBeDefined();
  });
});

describe("conferido no navegador, sem pedido (RF-08)", () => {
  it("os três vazios: o erro em cada um, foco na atual, sem pedido", async () => {
    renderVoluntary("/conta/senha");
    await flush();
    await submit();
    expect(fieldErrors(currentInput())).toEqual([TEXTOS["senha.erro.atualVazia"]]);
    expect(fieldErrors(newInput())).toEqual([TEXTOS["senha.erro.novaVazia"]]);
    expect(fieldErrors(confirmationInput())).toEqual([
      TEXTOS["senha.erro.confirmacaoVazia"],
    ]);
    expect(currentInput().getAttribute("aria-invalid")).toBe("true");
    expect(document.activeElement).toBe(currentInput());
    expect(passwordCalls()).toHaveLength(0);
  });

  it("a confirmação diferente: o erro na confirmação, foco nela, sem pedido", async () => {
    renderVoluntary("/conta/senha");
    await flush();
    fill("senha-atual-1", "nova-senha-longa-9", "nova-senha-longa-8");
    await submit();
    expect(fieldErrors(confirmationInput())).toEqual([
      TEXTOS["acesso.erro.confirmacaoDiferente"],
    ]);
    expect(confirmationInput().getAttribute("aria-invalid")).toBe("true");
    expect(document.activeElement).toBe(confirmationInput());
    expect(passwordCalls()).toHaveLength(0);
  });

  it("o erro de um campo some quando a pessoa o edita", async () => {
    renderVoluntary("/conta/senha");
    await flush();
    await submit();
    fireEvent.change(currentInput(), { target: { value: "x" } });
    expect(fieldErrors(currentInput())).toEqual([]);
    expect(fieldErrors(newInput())).toEqual([TEXTOS["senha.erro.novaVazia"]]);
  });
});

describe("o pedido e os erros (RF-08)", () => {
  it("o POST auth/password leva a atual e a nova, sem a confirmação", async () => {
    reply(PASSWORD, null);
    renderVoluntary("/conta/senha");
    await flush();
    fillValid();
    await submit();
    expect(passwordCalls()).toHaveLength(1);
    expect(JSON.parse(passwordCalls()[0].body ?? "null")).toEqual({
      current_password: "senha-atual-1",
      new_password: "nova-senha-longa-9",
    });
    // Enviando: o botão diz "Trocando…", desabilitado e com aria-busy.
    expect(screen.queryByRole("button", { name: TEXTOS["senha.trocar"] })).toBeNull();
    const busy = screen.getByRole("button", { name: TEXTOS["senha.trocando"] });
    expect((busy as HTMLButtonElement).disabled).toBe(true);
    expect(busy.getAttribute("aria-busy")).toBe("true");
  });

  it("invalid_credentials → Senha atual incorreta, no campo da atual, e o foco nele", async () => {
    reply(PASSWORD, fail(400, "invalid_credentials"));
    renderVoluntary("/conta/senha");
    await flush();
    fillValid();
    await submit();
    await flush();
    expect(fieldErrors(currentInput())).toEqual([TEXTOS["senha.erro.atualIncorreta"]]);
    await waitFor(() => expect(document.activeElement).toBe(currentInput()));
    expect(screen.queryByRole("alert")).toBeNull();
    expect(document.body.textContent).not.toContain(API_MESSAGE);
    expect(currentInput().value).toBe("senha-atual-1");
  });

  it("invalid_parameter → a lista de new_password no campo da nova, como chega", async () => {
    const lista = [
      "Esta senha é muito curta. Ela precisa conter pelo menos 10 caracteres.",
      "A nova senha precisa ser diferente da atual.",
    ];
    reply(
      PASSWORD,
      fail(400, "invalid_parameter", { fields: { new_password: lista } }),
    );
    renderVoluntary("/conta/senha");
    await flush();
    fillValid();
    await submit();
    await flush();
    expect(fieldErrors(newInput())).toEqual(lista);
    const ids = (newInput().getAttribute("aria-describedby") ?? "").split(" ");
    expect(ids[0]).toBe(document.querySelector('[data-part="dica-senha"]')?.id);
    await waitFor(() => expect(document.activeElement).toBe(newInput()));
    expect(document.body.textContent).not.toContain(API_MESSAGE);
  });

  it.each([
    [
      "too_many_requests com 42 s",
      fail(429, "too_many_requests", { wait_seconds: 42 }),
      "Muitas tentativas. Tente de novo em 42 s.",
    ],
    [
      "too_many_requests sem wait_seconds",
      fail(429, "too_many_requests"),
      "Muitas tentativas. Aguarde um pouco e tente de novo.",
    ],
    ["csrf_failed", fail(403, "csrf_failed"), TEXTOS["acesso.erro.csrf"]],
    ["outro code", fail(400, "validation_failed"), TEXTOS["senha.erro.outro"]],
    [
      "invalid_parameter de outro campo",
      fail(400, "invalid_parameter", { fields: { current_password: ["x"] } }),
      TEXTOS["senha.erro.outro"],
    ],
    ["erro de rede", "network" as Reply, TEXTOS["acesso.erro.rede"]],
    ["fora do formato", "not-json" as Reply, TEXTOS["acesso.erro.rede"]],
  ])(
    "%s → a frase dele, a mensagem da API fora, o foco no botão",
    async (_n, resposta, frase) => {
      reply(PASSWORD, resposta);
      reply("GET /api/v1/auth/csrf", NO_CONTENT);
      renderVoluntary("/conta/senha");
      await flush();
      fillValid();
      await submit();
      await flush();
      const alert = await screen.findByRole("alert");
      expect(alert.textContent).toBe(frase);
      expect(document.body.textContent).not.toContain(API_MESSAGE);
      expect(newInput().value).toBe("nova-senha-longa-9");
      await waitFor(() => expect(document.activeElement).toBe(submitButton()));
    },
  );
});

describe("o sucesso da voluntária (RF-08)", () => {
  it("204 → reload (um auth/me novo), a frase das outras sessões e o foco no Continuar", async () => {
    reply(PASSWORD, NO_CONTENT);
    renderVoluntary("/conta/senha?next=%2Fativos%2FITUB4");
    await flush();
    expect(meCalls()).toHaveLength(1);
    fillValid();
    await submit();
    await flush();
    expect(meCalls()).toHaveLength(2);
    expect(screen.getByRole("status").textContent).toContain(
      TEXTOS["senha.sucesso.titulo"],
    );
    expect(screen.getByText(TEXTOS["senha.sucesso.texto"])).toBeDefined();
    const go = screen.getByRole("link", { name: TEXTOS["senha.sucesso.continuar"] });
    expect(document.activeElement).toBe(go);
    expect(go.getAttribute("href")).toBe("/ativos/ITUB4");
    expect(document.querySelector('[data-part="form"]')).toBeNull();
  });

  it("Continuar volta ao next", async () => {
    reply(PASSWORD, NO_CONTENT);
    const router = renderVoluntary("/conta/senha?next=%2Fativos%2FITUB4%3Fx%3D1");
    await flush();
    fillValid();
    await submit();
    await flush();
    await click(screen.getByRole("link", { name: TEXTOS["senha.sucesso.continuar"] }));
    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    expect(router.state.location.search).toBe("?x=1");
  });

  it.each([
    ["sem next", "/conta/senha"],
    ["next de fora", "/conta/senha?next=https%3A%2F%2Fevil.com"],
    ["next que aponta para a própria página", "/conta/senha?next=%2Fconta%2Fsenha"],
  ])("%s → Continuar vai a /", async (_n, path) => {
    reply(PASSWORD, NO_CONTENT);
    renderVoluntary(path);
    await flush();
    fillValid();
    await submit();
    await flush();
    expect(
      screen
        .getByRole("link", { name: TEXTOS["senha.sucesso.continuar"] })
        .getAttribute("href"),
    ).toBe("/");
  });
});

describe("o 401 do auth/password (RF-16)", () => {
  it("voluntária: o aviso no lugar do formulário, o foco no Entrar, expired() só no clique", async () => {
    reply(PASSWORD, ANON);
    const router = renderVoluntary("/conta/senha?next=%2Fativos%2FITUB4");
    await flush();
    fillValid();
    await submit();
    await flush();

    const notice = document.querySelector(
      '[data-signin-notice="ended"]',
    ) as HTMLElement;
    expect(notice).not.toBeNull();
    expect(notice.getAttribute("role")).toBe("alert");
    expect(notice.textContent).toContain(TEXTOS["conta.aviso.terminou"]);
    expect(notice.textContent).toContain(TEXTOS["conta.aviso.volta"]);
    expect(document.querySelector('[data-part="form"]')).toBeNull();
    expect(document.body.textContent).not.toContain(API_MESSAGE);
    const enter = screen.getByRole("link", { name: TEXTOS["conta.entrar"] });
    expect(document.activeElement).toBe(enter);
    expect(enter.getAttribute("href")).toBe(
      `/entrar?next=${encodeURIComponent("/conta/senha?next=%2Fativos%2FITUB4")}`,
    );
    // A página fica onde estava.
    expect(router.state.location.pathname).toBe("/conta/senha");

    await click(enter);
    expect(router.state.location.pathname).toBe("/entrar");
    expect(router.state.location.search).toBe(
      `?next=${encodeURIComponent("/conta/senha?next=%2Fativos%2FITUB4")}`,
    );
    // expired(): a sessão vira anonymous com ended: true.
    expect(screen.getByTestId("sessao").textContent).toBe("anonymous:true");
  });

  it("obrigatória: o aviso fica na cena; Entrar → expired() e a entrada com a URL bloqueada", async () => {
    reply(ME_KEY, ok(PROVISIONAL));
    reply(PASSWORD, ANON);
    const router = renderRoutes("/ativos/ITUB4");
    await flush();
    fillValid();
    await submit();
    await flush();
    expect(required()).not.toBeNull();
    expect(document.querySelector('[data-signin-notice="ended"]')).not.toBeNull();
    const enter = screen.getByRole("link", { name: TEXTOS["conta.entrar"] });
    expect(document.activeElement).toBe(enter);
    expect(enter.getAttribute("href")).toBe("/entrar?next=%2Fativos%2FITUB4");

    await click(enter);
    expect(router.state.location.pathname).toBe("/entrar");
    expect(document.querySelector('[data-screen="entrada"]')).not.toBeNull();
    expect(required()).toBeNull();
  });
});

describe("o bloqueio da troca obrigatória (RF-05)", () => {
  it("com must_change_password, /ativos/ITUB4 mostra a troca, fora do casco, e a URL não muda", async () => {
    reply(ME_KEY, ok(PROVISIONAL));
    const router = renderRoutes("/ativos/ITUB4");
    await flush();
    expect(required()).not.toBeNull();
    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    expect(assetScreen()).toBeNull();
    expect(screen.queryByRole("banner")).toBeNull();
  });

  it.each(["/", "/conta/senha", "/qualquer-coisa"])(
    "com must_change_password, %s também mostra a troca",
    async (path) => {
      reply(ME_KEY, ok(PROVISIONAL));
      const router = renderRoutes(path);
      await flush();
      expect(required()).not.toBeNull();
      expect(router.state.location.pathname).toBe(path);
      expect(document.querySelector('[data-screen="senha"]')).toBeNull();
    },
  );

  it("sem must_change_password, /ativos/ITUB4 mostra a tela do ativo", async () => {
    renderRoutes("/ativos/ITUB4");
    await flush();
    expect(required()).toBeNull();
    expect(assetScreen()).not.toBeNull();
  });

  it("os textos da obrigatória, com o e-mail de quem entrou, e as três marcas", async () => {
    reply(ME_KEY, ok(PROVISIONAL));
    renderRoutes("/ativos/ITUB4");
    await flush();
    for (const chave of [
      "senha.obrigatoria.eyebrow",
      "senha.obrigatoria.titulo",
      "senha.obrigatoria.sub",
      "acesso.cena.titulo",
      "senha.atual.rotulo",
      "senha.nova.rotulo",
      "senha.confirmacao.rotulo",
      "acesso.senha.dica",
    ] as const) {
      expect(screen.getByText(TEXTOS[chave])).toBeDefined();
    }
    expect(
      screen.getByText(TEXTOS["senha.obrigatoria.conta"](PROVISIONAL.email)),
    ).toBeDefined();
    expect(
      screen.getByRole("form", { name: TEXTOS["senha.obrigatoria.titulo"] }),
    ).toBeDefined();
    for (const part of ["cena", "form-obrigatoria", "botao-sair"]) {
      expect(document.querySelectorAll(`[data-part="${part}"]`)).toHaveLength(1);
    }
    expect(document.querySelector('[data-part="form"]')).toBeNull();
  });

  it("a troca: 204 → a frase sem reload; Continuar → reload e a mesma URL mostra a tela do ativo", async () => {
    reply(ME_KEY, ok(PROVISIONAL), ok(ME));
    reply(PASSWORD, NO_CONTENT);
    const router = renderRoutes("/ativos/ITUB4");
    await flush();
    fillValid();
    await submit();
    await flush();

    // 204: a frase, ainda na troca, e nenhum auth/me novo.
    expect(required()).not.toBeNull();
    expect(screen.getByText(TEXTOS["senha.sucesso.texto"])).toBeDefined();
    const go = screen.getByRole("button", { name: TEXTOS["senha.sucesso.continuar"] });
    expect(document.activeElement).toBe(go);
    expect(meCalls()).toHaveLength(1);

    await click(go);
    await flush();
    expect(meCalls()).toHaveLength(2);
    expect(required()).toBeNull();
    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    expect(assetScreen()).not.toBeNull();
  });

  it("com must_change_password, /entrar?next=%2Fativos%2FITUB4 monta a entrada, e o sucesso leva a /ativos/ITUB4, que mostra a troca", async () => {
    reply(ME_KEY, fail(401, "not_authenticated"));
    reply("POST /api/v1/auth/login", ok(PROVISIONAL));
    const router = renderRoutes("/entrar?next=%2Fativos%2FITUB4");
    await flush();
    expect(document.querySelector('[data-screen="entrada"]')).not.toBeNull();
    fireEvent.change(screen.getByLabelText(TEXTOS["acesso.email.rotulo"]), {
      target: { value: "ana.souza@exemplo.com" },
    });
    fireEvent.change(screen.getByLabelText(TEXTOS["acesso.senha.rotulo"]), {
      target: { value: "provisoria-1" },
    });
    await click(document.querySelector('[data-part="botao-entrar"]') as Element);
    await flush();
    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    expect(router.state.historyAction).toBe("REPLACE");
    expect(required()).not.toBeNull();
    expect(document.querySelector('[data-screen="entrada"]')).toBeNull();
  });

  it.each([
    ["/entrar?next=%2Fativos%2FITUB4", "entrada"],
    ["/cadastro?next=%2Fativos%2FITUB4", "cadastro"],
  ])(
    "logado com must_change_password em %s: a tela dela monta e leva ao next, que mostra a troca",
    async (path) => {
      reply(ME_KEY, ok(PROVISIONAL));
      const router = renderRoutes(path);
      await waitFor(() => expect(router.state.location.pathname).toBe("/ativos/ITUB4"));
      expect(router.state.historyAction).toBe("REPLACE");
      expect(required()).not.toBeNull();
    },
  );

  it("Sair na obrigatória: signOut e a mesma URL pública, agora anônima", async () => {
    reply(ME_KEY, ok(PROVISIONAL));
    reply("POST /api/v1/auth/logout", NO_CONTENT);
    const router = renderRoutes("/ativos/ITUB4");
    await flush();
    await click(screen.getByRole("button", { name: TEXTOS["senha.obrigatoria.sair"] }));
    await flush();
    expect(
      calls.filter((c) => c.method === "POST" && c.url === "/api/v1/auth/logout"),
    ).toHaveLength(1);
    expect(required()).toBeNull();
    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    expect(assetScreen()).not.toBeNull();
  });

  it("Sair na obrigatória em /conta/senha vai a /", async () => {
    reply(ME_KEY, ok(PROVISIONAL));
    reply("POST /api/v1/auth/logout", NO_CONTENT);
    const router = renderRoutes("/conta/senha");
    await flush();
    await click(screen.getByRole("button", { name: TEXTOS["senha.obrigatoria.sair"] }));
    await flush();
    expect(router.state.location.pathname).toBe("/");
    expect(required()).toBeNull();
  });

  it("o Sair que falha: a sessão fica, e a caixa de erro diz", async () => {
    reply(ME_KEY, ok(PROVISIONAL));
    reply("POST /api/v1/auth/logout", fail(500, "server_error"));
    renderRoutes("/ativos/ITUB4");
    await flush();
    await click(screen.getByRole("button", { name: TEXTOS["senha.obrigatoria.sair"] }));
    await flush();
    expect(required()).not.toBeNull();
    expect(screen.getByRole("alert").textContent).toBe(TEXTOS["conta.menu.sairFalhou"]);
    expect(document.body.textContent).not.toContain(API_MESSAGE);
  });
});
