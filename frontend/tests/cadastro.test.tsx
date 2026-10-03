/**
 * V-08, a metade do cadastro (RF-07) e a parte de `/cadastro` do RF-04: a tela mostra os
 * textos aprovados no `cadastro.html`, lidos de `TEXTOS`; campo vazio e a confirmação
 * diferente não mandam pedido; `details.fields` vai ao campo certo, como chega, e campo
 * desconhecido cai no erro geral; `email_taken` no e-mail, com o link "Entrar"; cada `code`
 * com a frase dele, e a mensagem da API nunca na tela; 201 → a sessão e o `next`, por
 * substituição; quem já está logado e abre `/cadastro` vai ao `next`.
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
import { SignUpScreen } from "../src/screens/SignUpScreen";
import { SessionProvider, useSession } from "../src/session/SessionProvider";
import type { Me } from "../src/session/types";

// O `routes` chega na tela do ativo, que importa o uPlot; o uPlot pede `matchMedia` no import.
vi.mock("uplot", () => ({ default: class {} }));

const ME: Me = {
  email: "ana.souza@exemplo.com",
  name: "Ana Souza",
  role: "admin",
  must_change_password: false,
  is_staff: false,
  organization: { name: "Ana Souza", slug: "ana-souza", is_personal: true },
};

/** A mensagem que a API manda em todo erro destes testes: nunca pode aparecer na tela. */
const API_MESSAGE = "MENSAGEM CRUA DA API";

type Reply = { status: number; body: unknown } | "network" | "not-json" | null;

const created = (body: unknown): Reply => ({ status: 201, body });
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

const SIGNUP = "POST /api/v1/auth/signup";
const signupCalls = () =>
  calls.filter((c) => c.method === "POST" && c.url === "/api/v1/auth/signup");

/** O estado da sessão, mostrado pela rota de destino dos testes de navegação. */
function Destination() {
  const session = useSession();
  return <p data-testid="destino">{session.status}</p>;
}

/** O cadastro e um destino qualquer, sob o provedor de verdade, num roteador de memória. */
function renderAt(path: string, entries: string[] = []) {
  const router = createMemoryRouter(
    [
      {
        element: <SessionProvider />,
        children: [
          { path: "cadastro", element: <SignUpScreen /> },
          { path: "*", element: <Destination /> },
        ],
      },
    ],
    { initialEntries: [...entries, path], initialIndex: entries.length },
  );
  render(<RouterProvider router={router} />);
  return router;
}

function input(label: string): HTMLInputElement {
  return screen.getByLabelText(label) as HTMLInputElement;
}

const nameInput = () => input(TEXTOS["cadastro.nome.rotulo"]);
const emailInput = () => input(TEXTOS["acesso.email.rotulo"]);
const passwordInput = () => input(TEXTOS["acesso.senha.rotulo"]);
const confirmationInput = () => input(TEXTOS["cadastro.confirmacao.rotulo"]);

function submitButton(): HTMLButtonElement {
  return document.querySelector('[data-part="botao-criar"]') as HTMLButtonElement;
}

function fill(
  name: string,
  email: string,
  password: string,
  confirmation: string,
): void {
  fireEvent.change(nameInput(), { target: { value: name } });
  fireEvent.change(emailInput(), { target: { value: email } });
  fireEvent.change(passwordInput(), { target: { value: password } });
  fireEvent.change(confirmationInput(), { target: { value: confirmation } });
}

const fillValid = () =>
  fill("Ana Souza", "ana.souza@exemplo.com", "sol-de-inverno-42", "sol-de-inverno-42");

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

beforeEach(() => {
  replies = {};
  reply("GET /api/v1/auth/me", ANON);
  // biome-ignore lint/suspicious/noDocumentCookie: o signup manda o token do cookie de verdade.
  document.cookie = "csrftoken=tok; path=/";
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  // biome-ignore lint/suspicious/noDocumentCookie: limpa o cookie gravado no beforeEach.
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("os textos aprovados (RF-07)", () => {
  const VISIVEIS = [
    "acesso.cena.eyebrow",
    "acesso.cena.titulo",
    "acesso.cena.texto",
    "acesso.eyebrow",
    "cadastro.titulo",
    "cadastro.sub",
    "cadastro.nome.rotulo",
    "acesso.email.rotulo",
    "acesso.senha.rotulo",
    "acesso.senha.dica",
    "acesso.senha.requisito.tamanho",
    "acesso.senha.requisito.numeros",
    "acesso.senha.requisito.parecida",
    "acesso.senha.requisito.comum",
    "cadastro.confirmacao.rotulo",
    "cadastro.pessoal",
    "cadastro.pessoal.organizacao",
    "cadastro.criar",
    "cadastro.temConta",
    "acesso.entrar",
    "acesso.continuar",
  ] as const;

  it.each(VISIVEIS)("%s está na tela, lido de TEXTOS", async (chave) => {
    renderAt("/cadastro");
    await flush();
    expect(screen.getByText(TEXTOS[chave])).toBeDefined();
  });

  it("o exemplo do e-mail, a marca, o título do formulário e fora do casco", async () => {
    renderAt("/cadastro");
    await flush();
    expect(emailInput().placeholder).toBe(TEXTOS["acesso.email.placeholder"]);
    expect(screen.getByAltText(TEXTOS["acesso.cena.marca"])).toBeDefined();
    expect(screen.getByRole("form", { name: TEXTOS["cadastro.titulo"] })).toBeDefined();
    expect(screen.queryByRole("banner")).toBeNull();
  });

  it("a dica vem antes do campo da senha, e o campo a cita no aria-describedby", async () => {
    renderAt("/cadastro");
    await flush();
    const hint = document.querySelector('[data-part="dica-senha"]') as HTMLElement;
    expect(
      hint.compareDocumentPosition(passwordInput()) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(passwordInput().getAttribute("aria-describedby")).toBe(hint.id);
    expect(hint.querySelectorAll("li")).toHaveLength(4);
  });

  it("as marcas: data-screen e os oito data-part, uma vez cada", async () => {
    renderAt("/cadastro");
    await flush();
    expect(document.querySelectorAll('[data-screen="cadastro"]')).toHaveLength(1);
    for (const part of [
      "cena",
      "form",
      "campo-nome",
      "campo-email",
      "campo-senha",
      "campo-confirmacao",
      "dica-senha",
      "botao-criar",
    ]) {
      expect(document.querySelectorAll(`[data-part="${part}"]`)).toHaveLength(1);
    }
    expect(
      document.querySelector('[data-part="campo-senha"] [data-part="dica-senha"]'),
    ).not.toBeNull();
  });
});

describe("conferido no navegador, sem pedido (RF-07)", () => {
  it("os quatro vazios: o erro em cada um, foco no nome, sem pedido", async () => {
    renderAt("/cadastro");
    await flush();
    await submit();
    expect(fieldErrors(nameInput())).toEqual([TEXTOS["cadastro.erro.nomeVazio"]]);
    expect(fieldErrors(emailInput())).toEqual([TEXTOS["acesso.erro.emailVazio"]]);
    expect(fieldErrors(passwordInput())).toEqual([TEXTOS["acesso.erro.senhaVazia"]]);
    expect(fieldErrors(confirmationInput())).toEqual([
      TEXTOS["cadastro.erro.confirmacaoVazia"],
    ]);
    for (const field of [
      nameInput(),
      emailInput(),
      passwordInput(),
      confirmationInput(),
    ]) {
      expect(field.getAttribute("aria-invalid")).toBe("true");
    }
    expect(document.activeElement).toBe(nameInput());
    expect(screen.queryByRole("alert")).toBeNull();
    expect(signupCalls()).toHaveLength(0);
  });

  it("o nome e o e-mail só de espaços contam como vazios", async () => {
    renderAt("/cadastro");
    await flush();
    fill("   ", "  ", "sol-de-inverno-42", "sol-de-inverno-42");
    await submit();
    expect(fieldErrors(nameInput())).toEqual([TEXTOS["cadastro.erro.nomeVazio"]]);
    expect(fieldErrors(emailInput())).toEqual([TEXTOS["acesso.erro.emailVazio"]]);
    expect(signupCalls()).toHaveLength(0);
  });

  it("a senha de espaços não é vazia: vai à API como está", async () => {
    reply(SIGNUP, null);
    renderAt("/cadastro");
    await flush();
    fill("Ana", "ana@exemplo.com", "   ", "   ");
    await submit();
    expect(signupCalls()).toHaveLength(1);
    expect(JSON.parse(signupCalls()[0].body ?? "null").password).toBe("   ");
  });

  it("a confirmação diferente: o erro na confirmação, foco nela, sem pedido", async () => {
    renderAt("/cadastro");
    await flush();
    fill(
      "Ana Souza",
      "ana.souza@exemplo.com",
      "sol-de-inverno-42",
      "sol-de-inverno-24",
    );
    await submit();
    expect(fieldErrors(confirmationInput())).toEqual([
      TEXTOS["acesso.erro.confirmacaoDiferente"],
    ]);
    expect(confirmationInput().getAttribute("aria-invalid")).toBe("true");
    expect(fieldErrors(passwordInput())).toEqual([]);
    expect(document.activeElement).toBe(confirmationInput());
    expect(signupCalls()).toHaveLength(0);
  });

  it("o erro de um campo some quando a pessoa edita aquele campo, e só ele", async () => {
    renderAt("/cadastro");
    await flush();
    await submit();
    fireEvent.change(nameInput(), { target: { value: "A" } });
    expect(fieldErrors(nameInput())).toEqual([]);
    expect(nameInput().getAttribute("aria-invalid")).toBeNull();
    expect(fieldErrors(emailInput())).toEqual([TEXTOS["acesso.erro.emailVazio"]]);
  });
});

describe("o pedido e as respostas da API (RF-07)", () => {
  it("o POST auth/signup leva o e-mail e o nome aparados e a senha, em JSON", async () => {
    reply(SIGNUP, null);
    renderAt("/cadastro");
    await flush();
    fill(
      "  Ana Souza ",
      " ana.souza@exemplo.com ",
      "sol-de-inverno-42",
      "sol-de-inverno-42",
    );
    await submit();
    expect(signupCalls()).toHaveLength(1);
    expect(JSON.parse(signupCalls()[0].body ?? "null")).toEqual({
      email: "ana.souza@exemplo.com",
      name: "Ana Souza",
      password: "sol-de-inverno-42",
    });
  });

  it("enviando: o botão diz Criando a conta…, desabilitado e aria-busy", async () => {
    reply(SIGNUP, null);
    renderAt("/cadastro");
    await flush();
    fillValid();
    await submit();
    expect(submitButton().disabled).toBe(true);
    expect(submitButton().getAttribute("aria-busy")).toBe("true");
    expect(submitButton().textContent).toBe(TEXTOS["cadastro.criando"]);
  });

  it("invalid_parameter: cada lista no campo dela, como chega, e o foco no primeiro", async () => {
    reply(
      SIGNUP,
      fail(400, "invalid_parameter", {
        fields: {
          email: ["Informe um e-mail válido."],
          password: [
            "Esta senha é muito curta. Ela precisa conter pelo menos 10 caracteres.",
            "Esta senha é muito comum.",
            "A senha é muito parecida com name",
          ],
        },
      }),
    );
    renderAt("/cadastro");
    await flush();
    fillValid();
    await submit();
    await flush();
    expect(fieldErrors(emailInput())).toEqual(["Informe um e-mail válido."]);
    expect(fieldErrors(passwordInput())).toEqual([
      "Esta senha é muito curta. Ela precisa conter pelo menos 10 caracteres.",
      "Esta senha é muito comum.",
      "A senha é muito parecida com name",
    ]);
    expect(fieldErrors(nameInput())).toEqual([]);
    expect(fieldErrors(confirmationInput())).toEqual([]);
    // A senha segue descrita pela dica, antes das mensagens.
    const ids = (passwordInput().getAttribute("aria-describedby") ?? "").split(" ");
    expect(ids[0]).toBe(document.querySelector('[data-part="dica-senha"]')?.id);
    await waitFor(() => expect(document.activeElement).toBe(emailInput()));
    expect(screen.queryByRole("alert")).toBeNull();
    expect(document.body.textContent).not.toContain(API_MESSAGE);
    // Os campos seguem preenchidos — as duas senhas inclusive.
    expect(passwordInput().value).toBe("sol-de-inverno-42");
    expect(confirmationInput().value).toBe("sol-de-inverno-42");
  });

  it("invalid_parameter no nome: a mensagem no nome, e o foco nele", async () => {
    reply(
      SIGNUP,
      fail(400, "invalid_parameter", {
        fields: { name: ["Informe um nome de 1 a 120 caracteres."] },
      }),
    );
    renderAt("/cadastro");
    await flush();
    fillValid();
    await submit();
    await flush();
    expect(fieldErrors(nameInput())).toEqual([
      "Informe um nome de 1 a 120 caracteres.",
    ]);
    await waitFor(() => expect(document.activeElement).toBe(nameInput()));
  });

  it.each([
    ["um campo que a tela não conhece", { fields: { non_field_errors: ["x"] } }],
    [
      "um conhecido e um desconhecido",
      { fields: { email: ["Informe um e-mail válido."], role: ["x"] } },
    ],
    ["sem fields", {}],
    ["fields que não é lista", { fields: { email: "Informe um e-mail válido." } }],
  ])(
    "invalid_parameter com %s → o erro geral do cadastro, sem erro de campo",
    async (_n, details) => {
      reply(SIGNUP, fail(400, "invalid_parameter", details));
      renderAt("/cadastro");
      await flush();
      fillValid();
      await submit();
      const alert = await screen.findByRole("alert");
      expect(alert.textContent).toBe(TEXTOS["cadastro.erro.outro"]);
      for (const field of [
        nameInput(),
        emailInput(),
        passwordInput(),
        confirmationInput(),
      ]) {
        expect(fieldErrors(field)).toEqual([]);
      }
      expect(document.body.textContent).not.toContain("non_field_errors");
    },
  );

  it("email_taken: no campo do e-mail, com o link Entrar e o mesmo next", async () => {
    reply(SIGNUP, fail(409, "email_taken"));
    renderAt("/cadastro?next=%2Fativos%2FITUB4");
    await flush();
    fillValid();
    await submit();
    await flush();
    const errors = fieldErrors(emailInput());
    expect(errors).toEqual([
      `${TEXTOS["cadastro.erro.emailTaken"]} ${TEXTOS["cadastro.erro.emailTakenLink"]}`,
    ]);
    const group = document.getElementById(
      (emailInput().getAttribute("aria-describedby") ?? "").split(" ")[0],
    ) as HTMLElement;
    const link = group.querySelector("a") as HTMLAnchorElement;
    expect(link.textContent).toBe(TEXTOS["cadastro.erro.emailTakenLink"]);
    expect(link.getAttribute("href")).toBe("/entrar?next=%2Fativos%2FITUB4");
    await waitFor(() => expect(document.activeElement).toBe(emailInput()));
    expect(screen.queryByRole("alert")).toBeNull();
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
    ["outro code", fail(400, "validation_failed"), TEXTOS["cadastro.erro.outro"]],
    ["500 da API", fail(500, "server_error"), TEXTOS["cadastro.erro.outro"]],
    ["erro de rede", "network" as Reply, TEXTOS["acesso.erro.rede"]],
    ["fora do formato", "not-json" as Reply, TEXTOS["acesso.erro.rede"]],
    ["201 sem a forma do me", created({ ok: true }), TEXTOS["acesso.erro.rede"]],
  ])(
    "%s → a frase dele, a mensagem da API fora, o foco no botão",
    async (_n, resposta, frase) => {
      reply(SIGNUP, resposta);
      reply("GET /api/v1/auth/csrf", { status: 204, body: null });
      const router = renderAt("/cadastro");
      await flush();
      fillValid();
      await submit();
      await flush();
      const alert = await screen.findByRole("alert");
      expect(alert.textContent).toBe(frase);
      expect(document.body.textContent).not.toContain(API_MESSAGE);
      expect(router.state.location.pathname).toBe("/cadastro");
      expect(nameInput().value).toBe("Ana Souza");
      expect(passwordInput().value).toBe("sol-de-inverno-42");
      await waitFor(() => expect(document.activeElement).toBe(submitButton()));
      expect(submitButton().textContent).toBe(TEXTOS["cadastro.criar"]);
    },
  );
});

describe("o sucesso e o next (RF-04, RF-07)", () => {
  it("201 me → a sessão logada e o next, por substituição", async () => {
    reply(SIGNUP, created(ME));
    const router = renderAt("/cadastro?next=%2Fativos%2FITUB4%3Fx%3D1", ["/"]);
    await flush();
    fillValid();
    await submit();
    await flush();
    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    expect(router.state.location.search).toBe("?x=1");
    expect(router.state.historyAction).toBe("REPLACE");
    expect(screen.getByTestId("destino").textContent).toBe("authenticated");
    expect(calls.filter((c) => c.url === "/api/v1/auth/me")).toHaveLength(1);
    await act(async () => {
      await router.navigate(-1);
    });
    expect(router.state.location.pathname).toBe("/");
  });

  it("sem next, ou com next de fora, → /", async () => {
    reply(SIGNUP, created(ME));
    const router = renderAt("/cadastro?next=%2F%2Fevil.com");
    await flush();
    fillValid();
    await submit();
    await flush();
    expect(router.state.location.pathname).toBe("/");
    expect(router.state.historyAction).toBe("REPLACE");
  });

  it("logado (sem senha provisória) em /cadastro?next=%2Fativos%2FITUB4 → /ativos/ITUB4, por substituição", async () => {
    reply("GET /api/v1/auth/me", ok(ME));
    const router = renderAt("/cadastro?next=%2Fativos%2FITUB4", ["/"]);
    await waitFor(() => expect(router.state.location.pathname).toBe("/ativos/ITUB4"));
    expect(router.state.historyAction).toBe("REPLACE");
    expect(signupCalls()).toHaveLength(0);
  });

  it("anônimo fica no cadastro", async () => {
    const router = renderAt("/cadastro?next=%2Fativos%2FITUB4");
    await flush();
    expect(router.state.location.pathname).toBe("/cadastro");
    expect(document.querySelector('[data-screen="cadastro"]')).not.toBeNull();
  });
});

describe("os links (RF-07)", () => {
  it("Entrar leva o mesmo next, codificado; Continuar sem entrar vai ao next", async () => {
    renderAt("/cadastro?next=%2Fativos%2FITUB4%3Fx%3D1%26y%3D2");
    await flush();
    expect(
      screen.getByRole("link", { name: TEXTOS["acesso.entrar"] }).getAttribute("href"),
    ).toBe("/entrar?next=%2Fativos%2FITUB4%3Fx%3D1%26y%3D2");
    expect(
      screen
        .getByRole("link", { name: TEXTOS["acesso.continuar"] })
        .getAttribute("href"),
    ).toBe("/ativos/ITUB4?x=1&y=2");
  });

  it("sem next: /entrar e /", async () => {
    renderAt("/cadastro");
    await flush();
    expect(
      screen.getByRole("link", { name: TEXTOS["acesso.entrar"] }).getAttribute("href"),
    ).toBe("/entrar");
    expect(
      screen
        .getByRole("link", { name: TEXTOS["acesso.continuar"] })
        .getAttribute("href"),
    ).toBe("/");
  });
});

describe("a rota /cadastro em routes (RF-04)", () => {
  it("createMemoryRouter(routes) monta o cadastro em /cadastro, fora do casco", async () => {
    render(
      <RouterProvider
        router={createMemoryRouter(routes, { initialEntries: ["/cadastro"] })}
      />,
    );
    await flush();
    expect(document.querySelector('[data-screen="cadastro"]')).not.toBeNull();
    expect(screen.queryByRole("banner")).toBeNull();
  });
});
