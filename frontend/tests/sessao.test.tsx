/**
 * V-05 (RF-03), o provedor da sessão: um `auth/me` ao montar; 200 com a forma do `me` →
 * logado; forma errada, 401, 500 e erro de rede → anônimo; `loading` enquanto não volta; as
 * ações `setMe`, `reload`, `signOut` e `expired`; fora do provedor, o anônimo do padrão; e o
 * provedor na rota de layout de `routes`, que `createMemoryRouter(routes)` recebe sem nada extra.
 * E o bloqueio do RF-05 (V-06): com `must_change_password`, a troca obrigatória no lugar do
 * `<Outlet>`, na mesma URL, menos em `/entrar` e `/cadastro`.
 *
 * O `fetch` é um duplo que responde pelo endereço e pelo método; `null` deixa o pedido pendente.
 */
import { act, cleanup, render, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { routes } from "../src/App";
import { Shell } from "../src/components/Shell";
import {
  type SessionApi,
  SessionProvider,
  useSession,
} from "../src/session/SessionProvider";
import type { Me } from "../src/session/types";

// O `App` chega na tela do ativo, que importa o uPlot; o uPlot pede `matchMedia` no import.
vi.mock("uplot", () => ({ default: class {} }));

const ME: Me = {
  email: "ana@exemplo.com",
  name: "Ana",
  role: "admin",
  must_change_password: false,
  is_staff: false,
  organization: { name: "Ruvor", slug: "ruvor", is_personal: false },
};

type Reply = { status: number; body: unknown } | "network" | null;

const ok = (body: unknown): Reply => ({ status: 200, body });
const fail = (status: number, code: string): Reply => ({
  status,
  body: { error: { code, message: "falhou", details: {} } },
});
const NO_CONTENT: Reply = { status: 204, body: null };
const ANON = fail(401, "not_authenticated");

type Call = { url: string; method: string; headers: Record<string, string> };

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
      calls.push({
        url,
        method,
        headers: { ...((init?.headers as Record<string, string>) ?? {}) },
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

const meCalls = () =>
  calls.filter((c) => c.method === "GET" && c.url === "/api/v1/auth/me");

/** A sessão vista pelo componente de dentro, a cada desenho. */
let api: SessionApi;

function Probe() {
  api = useSession();
  return null;
}

function renderProvider() {
  const router = createMemoryRouter(
    [{ element: <SessionProvider />, children: [{ index: true, element: <Probe /> }] }],
    { initialEntries: ["/"] },
  );
  return render(<RouterProvider router={router} />);
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
  // biome-ignore lint/suspicious/noDocumentCookie: o `signOut` manda o token do cookie de verdade.
  document.cookie = "csrftoken=tok; path=/";
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  // biome-ignore lint/suspicious/noDocumentCookie: limpa o cookie gravado no beforeEach.
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("a leitura ao montar", () => {
  it("um auth/me só, e loading enquanto não volta", async () => {
    renderProvider();
    await flush();
    expect(meCalls()).toHaveLength(1);
    expect(calls).toHaveLength(1);
    expect(api.status).toBe("loading");
  });

  it("200 com a forma do me → authenticated, com o me", async () => {
    reply("GET /api/v1/auth/me", ok(ME));
    renderProvider();
    await waitFor(() => expect(api.status).toBe("authenticated"));
    expect(api.status === "authenticated" && api.me).toEqual(ME);
    expect(meCalls()).toHaveLength(1);
  });

  it.each([
    ["sem a organização", { ...ME, organization: undefined }],
    ["papel fora da lista", { ...ME, role: "owner" }],
    ["must_change_password em texto", { ...ME, must_change_password: "false" }],
    [
      "organização sem is_personal",
      { ...ME, organization: { name: "Ruvor", slug: "ruvor" } },
    ],
    ["uma lista", [ME]],
  ])("200 com a forma errada (%s) → anonymous", async (_nome, body) => {
    reply("GET /api/v1/auth/me", ok(body));
    renderProvider();
    await waitFor(() => expect(api.status).toBe("anonymous"));
    expect(api.status === "anonymous" && api.ended).toBe(false);
  });

  it.each([
    ["401", ANON],
    ["500", fail(500, "internal_error")],
    ["erro de rede", "network" as Reply],
  ])("%s → anonymous, sem tentar de novo", async (_nome, r) => {
    reply("GET /api/v1/auth/me", r);
    renderProvider();
    await waitFor(() => expect(api.status).toBe("anonymous"));
    expect(api.status === "anonymous" && api.ended).toBe(false);
    await flush();
    expect(meCalls()).toHaveLength(1);
  });
});

describe("as ações", () => {
  it("setMe → authenticated com o me dado", async () => {
    reply("GET /api/v1/auth/me", ANON);
    renderProvider();
    await waitFor(() => expect(api.status).toBe("anonymous"));
    act(() => api.setMe(ME));
    expect(api.status === "authenticated" && api.me).toEqual(ME);
  });

  it("a leitura do auth/me que volta depois do setMe não o desfaz", async () => {
    let answer: (r: Response) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn(
        () =>
          new Promise<Response>((resolve) => {
            answer = resolve;
          }),
      ),
    );
    renderProvider();
    await flush();
    expect(api.status).toBe("loading");
    act(() => api.setMe(ME));
    expect(api.status).toBe("authenticated");
    // a leitura de montagem ainda estava pendente; agora volta 401 — e chegou tarde.
    answer({
      ok: false,
      status: 401,
      json: async () => ({
        error: { code: "not_authenticated", message: "falhou", details: {} },
      }),
    } as unknown as Response);
    await flush();
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1);
    expect(api.status).toBe("authenticated");
  });

  it("reload relê o auth/me e aplica a resposta", async () => {
    reply(
      "GET /api/v1/auth/me",
      ANON,
      ok(ME),
      ok({ ...ME, must_change_password: true }),
    );
    renderProvider();
    await waitFor(() => expect(api.status).toBe("anonymous"));
    await act(() => api.reload());
    expect(api.status === "authenticated" && api.me).toEqual(ME);
    await act(() => api.reload());
    // Com a marca, o bloqueio do RF-05 tira o Outlet (e o Probe): a troca aparece no lugar.
    expect(document.querySelector('[data-screen="senha-obrigatoria"]')).not.toBeNull();
    expect(meCalls()).toHaveLength(3);
  });

  it("reload com o auth/me em 401 → anonymous", async () => {
    reply("GET /api/v1/auth/me", ok(ME), ANON);
    renderProvider();
    await waitFor(() => expect(api.status).toBe("authenticated"));
    await act(() => api.reload());
    expect(api.status).toBe("anonymous");
  });

  it.each([
    ["204", NO_CONTENT],
    ["401", ANON],
  ])(
    "signOut com %s → anonymous, sem erro, pelo POST auth/logout com o token",
    async (_n, r) => {
      reply("GET /api/v1/auth/me", ok(ME));
      reply("POST /api/v1/auth/logout", r);
      renderProvider();
      await waitFor(() => expect(api.status).toBe("authenticated"));
      await act(() => api.signOut());
      expect(api.status).toBe("anonymous");
      expect(api.status === "anonymous" && api.ended).toBe(false);
      const logout = calls.filter(
        (c) => c.method === "POST" && c.url === "/api/v1/auth/logout",
      );
      expect(logout).toHaveLength(1);
      expect(logout[0]?.headers["X-CSRFToken"]).toBe("tok");
    },
  );

  it("signOut com outro erro sobe, e a sessão fica", async () => {
    reply("GET /api/v1/auth/me", ok(ME));
    reply("POST /api/v1/auth/logout", fail(500, "internal_error"));
    renderProvider();
    await waitFor(() => expect(api.status).toBe("authenticated"));
    await act(async () => {
      await expect(api.signOut()).rejects.toMatchObject({ status: 500 });
    });
    expect(api.status).toBe("authenticated");
  });

  it("expired → anonymous com ended: true", async () => {
    reply("GET /api/v1/auth/me", ok(ME));
    renderProvider();
    await waitFor(() => expect(api.status).toBe("authenticated"));
    act(() => api.expired());
    expect(api.status).toBe("anonymous");
    expect(api.status === "anonymous" && api.ended).toBe(true);
  });
});

describe("o bloqueio do RF-05", () => {
  /** O provedor num roteador, com a troca isenta em /entrar e /cadastro e um filho em `*`. */
  function renderAt(path: string) {
    const router = createMemoryRouter(
      [
        {
          element: <SessionProvider />,
          children: [
            { path: "entrar", element: <Probe /> },
            { path: "cadastro", element: <Probe /> },
            { path: "*", element: <Probe /> },
          ],
        },
      ],
      { initialEntries: [path] },
    );
    render(<RouterProvider router={router} />);
    return router;
  }

  const required = () => document.querySelector('[data-screen="senha-obrigatoria"]');

  it.each(["/", "/ativos/ITUB4", "/conta/senha"])(
    "com must_change_password, %s mostra a troca obrigatória no lugar do Outlet, na mesma URL",
    async (path) => {
      reply("GET /api/v1/auth/me", ok({ ...ME, must_change_password: true }));
      const router = renderAt(path);
      await waitFor(() => expect(required()).not.toBeNull());
      expect(router.state.location.pathname).toBe(path);
      // o Outlet não desenhou: o Probe só viu o carregando.
      expect(api.status).toBe("loading");
    },
  );

  it.each(["/entrar", "/cadastro"])(
    "com must_change_password, %s monta a tela dela, não a troca",
    async (path) => {
      reply("GET /api/v1/auth/me", ok({ ...ME, must_change_password: true }));
      renderAt(path);
      await waitFor(() => expect(api.status).toBe("authenticated"));
      expect(required()).toBeNull();
    },
  );

  it("sem must_change_password, o Outlet de pé e nenhuma troca", async () => {
    reply("GET /api/v1/auth/me", ok(ME));
    renderAt("/ativos/ITUB4");
    await waitFor(() => expect(api.status).toBe("authenticated"));
    expect(required()).toBeNull();
  });

  it("anônimo e carregando: nenhuma troca", async () => {
    renderAt("/ativos/ITUB4");
    await flush();
    expect(api.status).toBe("loading");
    expect(required()).toBeNull();
  });

  it("fora de um roteador, com filhos: sem URL para isentar, o bloqueio não se aplica", async () => {
    reply("GET /api/v1/auth/me", ok({ ...ME, must_change_password: true }));
    render(
      <SessionProvider>
        <Probe />
      </SessionProvider>,
    );
    await waitFor(() => expect(api.status).toBe("authenticated"));
    expect(required()).toBeNull();
  });
});

describe("fora do provedor e com filhos", () => {
  it("fora do provedor: o anônimo do padrão, e as ações inertes", async () => {
    render(<Probe />);
    expect(api.status).toBe("anonymous");
    expect(api.status === "anonymous" && api.ended).toBe(false);
    act(() => api.setMe(ME));
    act(() => api.expired());
    await act(() => api.reload());
    await act(() => api.signOut());
    expect(api.status).toBe("anonymous");
    expect(api.status === "anonymous" && api.ended).toBe(false);
    expect(calls).toHaveLength(0);
  });

  it("com filhos, o provedor os renderiza no lugar do Outlet, sem roteador", async () => {
    reply("GET /api/v1/auth/me", ok(ME));
    render(
      <SessionProvider>
        <Probe />
      </SessionProvider>,
    );
    await waitFor(() => expect(api.status).toBe("authenticated"));
  });
});

describe("o provedor em routes", () => {
  it("a raiz de routes é a rota de layout da sessão, pai do casco", () => {
    expect(routes).toHaveLength(1);
    const root = routes[0];
    expect(root?.path).toBeUndefined();
    expect((root?.element as { type?: unknown } | undefined)?.type).toBe(
      SessionProvider,
    );
    const shell = root?.children?.[0];
    expect((shell?.element as { type?: unknown } | undefined)?.type).toBe(Shell);
  });

  it("montado por createMemoryRouter(routes), sem nada extra, o provedor pede o auth/me", async () => {
    reply("GET /api/v1/auth/me", ANON);
    const router = createMemoryRouter(routes, { initialEntries: ["/qualquer-coisa"] });
    render(<RouterProvider router={router} />);
    await flush();
    expect(meCalls()).toHaveLength(1);
  });
});
