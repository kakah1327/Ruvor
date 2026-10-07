/**
 * V-04 (parte do cliente) e o X-CSRFToken do V-11: com `fetch` substituído, o formato de
 * erro da D-86 vira ApiError com o `code`; a falha de rede vira `network_error`; o `POST`
 * manda o X-CSRFToken lido do cookie.
 *
 * M2.1b, V-04 (RF-02): corpo JSON e `Content-Type`; `PATCH` e `DELETE`; 204 → `undefined`;
 * o `X-CSRFToken` em todo método que não é `GET`; sem cookie, um `auth/csrf` antes, e a
 * falha dele sobe sem o pedido; 403 `csrf_failed` → um `auth/csrf` e uma repetição só.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  apiDelete,
  apiGet,
  apiPatch,
  apiPost,
  apiPut,
} from "../src/api/client";

type FetchArgs = [string, RequestInit];

function stubFetch(status: number, body: unknown): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn(
    async (_url: string, _init: RequestInit) =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** O `document.cookie` lido pelo cliente, sem gravar cookie de verdade. */
function stubCookie(value: string): void {
  vi.spyOn(document, "cookie", "get").mockReturnValue(value);
}

/** Um `document.cookie` (espiado) que o duplo do servidor pode mudar, como o `auth/csrf`. */
function cookieJar(initial: string): { set(value: string): void } {
  let value = initial;
  vi.spyOn(document, "cookie", "get").mockImplementation(() => value);
  return {
    set(next: string) {
      value = next;
    },
  };
}

type Call = {
  url: string;
  method: string;
  headers: RequestInit["headers"];
  body: RequestInit["body"];
};

const CSRF = "/api/v1/auth/csrf";

/** O `fetch` falso que responde por URL e método, e guarda cada pedido na ordem. */
function stubServer(
  handle: (url: string, method: string) => Response | Promise<Response>,
): Call[] {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: RequestInit = {}) => {
      const method = init.method ?? "GET";
      calls.push({ url, method, headers: init.headers, body: init.body });
      return handle(url, method);
    }),
  );
  return calls;
}

const jsonReply = (status: number, body: unknown): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const noContent = (): Response => new Response(null, { status: 204 });

const apiErrorReply = (status: number, code: string): Response =>
  jsonReply(status, { error: { code, message: `falhou: ${code}`, details: {} } });

/** Os cabeçalhos de um pedido como objeto simples (o contrato: nunca `Headers`). */
function plainHeaders(call: Call | undefined): Record<string, string> {
  const headers = call?.headers;
  expect(headers).toBeDefined();
  expect(headers instanceof Headers).toBe(false);
  expect(Array.isArray(headers)).toBe(false);
  expect(Object.getPrototypeOf(headers)).toBe(Object.prototype);
  return headers as Record<string, string>;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
});

async function caught(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof ApiError) {
      return error;
    }
    throw error;
  }
  throw new Error("a promessa não rejeitou");
}

describe("apiGet", () => {
  it("devolve o corpo de uma resposta 2xx", async () => {
    const fetchMock = stubFetch(200, { ticker: "ITUB4", metric: null });
    const body = await apiGet<{ ticker: string }>("/api/v1/assets/ITUB4/metrics");
    expect(body).toEqual({ ticker: "ITUB4", metric: null });
    const [url, init] = fetchMock.mock.calls[0] as FetchArgs;
    expect(url).toBe("/api/v1/assets/ITUB4/metrics");
    expect(init.method).toBe("GET");
  });

  it("prefixa o caminho com VITE_API_BASE_URL", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://api.exemplo");
    const fetchMock = stubFetch(200, {});
    await apiGet("/api/v1/assets");
    const [url] = fetchMock.mock.calls[0] as FetchArgs;
    expect(url).toBe("http://api.exemplo/api/v1/assets");
  });

  it("404 asset_not_found vira ApiError com o code, a mensagem e os detalhes", async () => {
    stubFetch(404, {
      error: {
        code: "asset_not_found",
        message: "Ativo XPTO3 não existe.",
        details: { ticker: "XPTO3" },
      },
    });
    const error = await caught(apiGet("/api/v1/assets/XPTO3"));
    expect(error.status).toBe(404);
    expect(error.code).toBe("asset_not_found");
    expect(error.message).toBe("Ativo XPTO3 não existe.");
    expect(error.details).toEqual({ ticker: "XPTO3" });
  });

  it("erro de rede vira network_error com status 0", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );
    const error = await caught(apiGet("/api/v1/assets"));
    expect(error.status).toBe(0);
    expect(error.code).toBe("network_error");
  });

  it("erro fora do formato da D-86 vira unexpected_response com o status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("<html>Bad Gateway</html>", { status: 502 })),
    );
    const error = await caught(apiGet("/api/v1/assets"));
    expect(error.status).toBe(502);
    expect(error.code).toBe("unexpected_response");
  });
});

describe("apiPost", () => {
  it("manda o X-CSRFToken quando o cookie csrftoken existe", async () => {
    stubCookie("outro=1; csrftoken=abc123");
    const fetchMock = stubFetch(202, { ticker: "ABCD3" });
    await apiPost("/api/v1/assets/ABCD3/risk");
    const [, init] = fetchMock.mock.calls[0] as FetchArgs;
    expect(init.method).toBe("POST");
    expect(new Headers(init.headers).get("X-CSRFToken")).toBe("abc123");
  });

  it("sem cookie, pede `auth/csrf` antes e manda o token que o cookie passa a ter", async () => {
    const jar = cookieJar("outro=1");
    const calls = stubServer((url, method) => {
      if (url === CSRF && method === "GET") {
        jar.set("outro=1; csrftoken=tok");
        return noContent();
      }
      return jsonReply(202, { ticker: "ABCD3" });
    });
    await apiPost("/api/v1/assets/ABCD3/risk");
    const csrfAt = calls.findIndex((c) => c.url === CSRF && c.method === "GET");
    const postAt = calls.findIndex(
      (c) => c.url === "/api/v1/assets/ABCD3/risk" && c.method === "POST",
    );
    expect(csrfAt).toBeGreaterThanOrEqual(0);
    expect(postAt).toBeGreaterThan(csrfAt);
    expect(calls.filter((c) => c.url === CSRF)).toHaveLength(1);
    expect(calls).toHaveLength(2);
    expect(plainHeaders(calls[postAt])["X-CSRFToken"]).toBe("tok");
    expect(plainHeaders(calls[csrfAt])).not.toHaveProperty("X-CSRFToken");
  });

  it("com o cookie, não pede `auth/csrf`", async () => {
    cookieJar("csrftoken=abc123");
    const calls = stubServer(() => jsonReply(202, { ticker: "ABCD3" }));
    await apiPost("/api/v1/assets/ABCD3/risk");
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([
      "POST /api/v1/assets/ABCD3/risk",
    ]);
  });

  it("o GET nunca manda o X-CSRFToken", async () => {
    stubCookie("csrftoken=abc123");
    const fetchMock = stubFetch(200, {});
    await apiGet("/api/v1/assets");
    const [, init] = fetchMock.mock.calls[0] as FetchArgs;
    expect(new Headers(init.headers).has("X-CSRFToken")).toBe(false);
  });

  it("409 asset_already_covered leva os detalhes", async () => {
    stubCookie("csrftoken=abc123");
    stubFetch(409, {
      error: {
        code: "asset_already_covered",
        message: "Ativo ITUB4 já tem risco calculado.",
        details: { ticker: "ITUB4", covered: true },
      },
    });
    const error = await caught(apiPost("/api/v1/assets/ITUB4/risk"));
    expect(error.status).toBe(409);
    expect(error.code).toBe("asset_already_covered");
    expect(error.details).toEqual({ ticker: "ITUB4", covered: true });
  });
});

describe("o corpo, os métodos e o 204 (RF-02)", () => {
  it("com corpo: Content-Type application/json e o corpo serializado", async () => {
    cookieJar("csrftoken=abc123");
    const calls = stubServer(() => jsonReply(201, { email: "a@exemplo.com" }));
    const reply = await apiPost<{ email: string }>("/api/v1/auth/signup", {
      email: "a@exemplo.com",
      password: "s3nh@ longa",
    });
    expect(reply).toEqual({ email: "a@exemplo.com" });
    expect(calls).toHaveLength(1);
    expect(calls[0]?.method).toBe("POST");
    const headers = plainHeaders(calls[0]);
    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers["X-CSRFToken"]).toBe("abc123");
    expect(calls[0]?.body).toBe(
      JSON.stringify({ email: "a@exemplo.com", password: "s3nh@ longa" }),
    );
  });

  it("sem corpo: nem Content-Type nem corpo", async () => {
    cookieJar("csrftoken=abc123");
    const calls = stubServer(() => jsonReply(202, {}));
    await apiPost("/api/v1/assets/ABCD3/risk");
    expect(plainHeaders(calls[0])).not.toHaveProperty("Content-Type");
    expect(calls[0]?.body).toBeUndefined();
  });

  it("PATCH: o método, o corpo, o Content-Type e o X-CSRFToken", async () => {
    cookieJar("csrftoken=abc123");
    const calls = stubServer(() => jsonReply(200, { role: "admin" }));
    const reply = await apiPatch<{ role: string }>(
      "/api/v1/organization/users/b%40exemplo.com",
      { role: "admin" },
    );
    expect(reply).toEqual({ role: "admin" });
    expect(calls).toHaveLength(1);
    expect(calls[0]?.url).toBe("/api/v1/organization/users/b%40exemplo.com");
    expect(calls[0]?.method).toBe("PATCH");
    const headers = plainHeaders(calls[0]);
    expect(headers["X-CSRFToken"]).toBe("abc123");
    expect(headers["Content-Type"]).toBe("application/json");
    expect(calls[0]?.body).toBe(JSON.stringify({ role: "admin" }));
  });

  it("DELETE: o método, o X-CSRFToken, sem corpo, e o 204 vira undefined", async () => {
    cookieJar("csrftoken=abc123");
    const calls = stubServer(() => noContent());
    const reply = await apiDelete("/api/v1/organization/users/b%40exemplo.com");
    expect(reply).toBeUndefined();
    expect(calls).toHaveLength(1);
    expect(calls[0]?.method).toBe("DELETE");
    expect(plainHeaders(calls[0])["X-CSRFToken"]).toBe("abc123");
    expect(plainHeaders(calls[0])).not.toHaveProperty("Content-Type");
    expect(calls[0]?.body).toBeUndefined();
  });

  it("204 devolve undefined sem ler o corpo", async () => {
    cookieJar("csrftoken=abc123");
    const json = vi.fn(async () => {
      throw new SyntaxError("sem corpo");
    });
    stubServer(() => ({ ok: true, status: 204, json }) as unknown as Response);
    await expect(apiPost("/api/v1/auth/logout")).resolves.toBeUndefined();
    expect(json).not.toHaveBeenCalled();
  });

  it("2xx com corpo que não é JSON segue unexpected_response", async () => {
    stubServer(() => new Response("<html>ok</html>", { status: 200 }));
    const error = await caught(apiGet("/api/v1/auth/me"));
    expect(error.status).toBe(200);
    expect(error.code).toBe("unexpected_response");
  });

  it("os cabeçalhos são um objeto simples, no GET e no POST", async () => {
    cookieJar("csrftoken=abc123");
    const calls = stubServer(() => jsonReply(200, {}));
    await apiGet("/api/v1/assets");
    await apiPost("/api/v1/assets/ABCD3/risk", { a: 1 });
    expect(calls).toHaveLength(2);
    expect(plainHeaders(calls[0])).not.toHaveProperty("X-CSRFToken");
    expect(plainHeaders(calls[1])["X-CSRFToken"]).toBe("abc123");
  });

  it("o GET sem cookie não pede `auth/csrf`", async () => {
    cookieJar("");
    const calls = stubServer(() => jsonReply(200, {}));
    await apiGet("/api/v1/assets");
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual(["GET /api/v1/assets"]);
  });
});

describe("o `auth/csrf` prévio que falha (RF-02)", () => {
  it.each([
    ["PATCH", () => apiPatch("/api/v1/organization/users/b%40exemplo.com", { a: 1 })],
    ["DELETE", () => apiDelete("/api/v1/organization/users/b%40exemplo.com")],
    ["POST", () => apiPost("/api/v1/auth/login", { email: "a", password: "b" })],
  ])(
    "%s: 500 no `auth/csrf` → rejeita com o erro dele, e o pedido não sai",
    async (_m, call) => {
      cookieJar("");
      const calls = stubServer((url) =>
        url === CSRF ? apiErrorReply(500, "internal_error") : jsonReply(200, {}),
      );
      const error = await caught(call());
      expect(error.status).toBe(500);
      expect(error.code).toBe("internal_error");
      expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([`GET ${CSRF}`]);
    },
  );

  it("falha de rede no `auth/csrf` → network_error, e o pedido não sai", async () => {
    cookieJar("");
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init: RequestInit = {}) => {
        calls.push(`${init.method ?? "GET"} ${url}`);
        if (url === CSRF) throw new TypeError("Failed to fetch");
        return jsonReply(200, {});
      }),
    );
    const error = await caught(apiPost("/api/v1/assets/ABCD3/risk"));
    expect(error.status).toBe(0);
    expect(error.code).toBe("network_error");
    expect(calls).toEqual([`GET ${CSRF}`]);
  });
});

describe("403 csrf_failed: um `auth/csrf` e uma repetição (RF-02)", () => {
  /** 403 `csrf_failed` nas `failures` primeiras escritas; depois, 200. */
  function rejectingCsrf(failures: number): Call[] {
    let failed = 0;
    return stubServer((url, method) => {
      if (url === CSRF && method === "GET") return noContent();
      if (failed < failures) {
        failed += 1;
        return apiErrorReply(403, "csrf_failed");
      }
      return jsonReply(200, { ok: true });
    });
  }

  it("a repetição que passa devolve o corpo: três pedidos", async () => {
    cookieJar("csrftoken=velho");
    const calls = rejectingCsrf(1);
    await expect(apiPost("/api/v1/auth/login", { email: "a" })).resolves.toEqual({
      ok: true,
    });
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([
      "POST /api/v1/auth/login",
      `GET ${CSRF}`,
      "POST /api/v1/auth/login",
    ]);
  });

  it("a segunda falha sobe: três pedidos no total, não mais", async () => {
    cookieJar("csrftoken=velho");
    const calls = rejectingCsrf(10);
    const error = await caught(apiPatch("/api/v1/auth/me", { name: "A" }));
    expect(error.status).toBe(403);
    expect(error.code).toBe("csrf_failed");
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([
      "PATCH /api/v1/auth/me",
      `GET ${CSRF}`,
      "PATCH /api/v1/auth/me",
    ]);
  });

  it("a repetição manda o token novo, lido do cookie na hora", async () => {
    const jar = cookieJar("csrftoken=velho");
    let failed = false;
    const calls = stubServer((url, method) => {
      if (url === CSRF && method === "GET") {
        jar.set("csrftoken=novo");
        return noContent();
      }
      if (!failed) {
        failed = true;
        return apiErrorReply(403, "csrf_failed");
      }
      return noContent();
    });
    await apiDelete("/api/v1/organization/users/b%40exemplo.com");
    const writes = calls.filter((c) => c.method === "DELETE");
    expect(writes.map((c) => plainHeaders(c)["X-CSRFToken"])).toEqual([
      "velho",
      "novo",
    ]);
  });

  it("403 com outro código não repete", async () => {
    cookieJar("csrftoken=abc123");
    const calls = stubServer(() => apiErrorReply(403, "password_change_required"));
    const error = await caught(apiPost("/api/v1/assets/ABCD3/risk"));
    expect(error.code).toBe("password_change_required");
    expect(calls).toHaveLength(1);
  });
});

describe("PUT (M2.2b, RF-15): a forma do PATCH", () => {
  const PATH = "/api/v1/portfolios/5b0e6c1e-0000-4000-8000-000000000000/holdings";
  const BODY = { holdings: [{ ticker: "ITUB4", weight: "60.00" }] };

  it("o método, o corpo JSON, o Content-Type e o X-CSRFToken", async () => {
    cookieJar("csrftoken=abc123");
    const calls = stubServer(() => jsonReply(200, { portfolio: { version: 2 } }));
    const reply = await apiPut<{ portfolio: { version: number } }>(PATH, BODY);
    expect(reply).toEqual({ portfolio: { version: 2 } });
    expect(calls).toHaveLength(1);
    expect(calls[0]?.url).toBe(PATH);
    expect(calls[0]?.method).toBe("PUT");
    const headers = plainHeaders(calls[0]);
    expect(headers["X-CSRFToken"]).toBe("abc123");
    expect(headers["Content-Type"]).toBe("application/json");
    expect(calls[0]?.body).toBe(JSON.stringify(BODY));
  });

  it("sem cookie, pede `auth/csrf` antes e manda o token que o cookie passa a ter", async () => {
    const jar = cookieJar("");
    const calls = stubServer((url) => {
      if (url === CSRF) {
        jar.set("csrftoken=novo");
        return noContent();
      }
      return jsonReply(200, {});
    });
    await apiPut(PATH, BODY);
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([
      `GET ${CSRF}`,
      `PUT ${PATH}`,
    ]);
    expect(plainHeaders(calls[1])["X-CSRFToken"]).toBe("novo");
  });

  it("403 csrf_failed: um `auth/csrf` e uma repetição", async () => {
    cookieJar("csrftoken=velho");
    let failed = false;
    const calls = stubServer((url, method) => {
      if (url === CSRF && method === "GET") return noContent();
      if (!failed) {
        failed = true;
        return apiErrorReply(403, "csrf_failed");
      }
      return jsonReply(200, { ok: true });
    });
    await expect(apiPut(PATH, BODY)).resolves.toEqual({ ok: true });
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([
      `PUT ${PATH}`,
      `GET ${CSRF}`,
      `PUT ${PATH}`,
    ]);
  });

  it("o erro da API sobe como ApiError, com os detalhes", async () => {
    cookieJar("csrftoken=abc123");
    stubServer(() =>
      jsonReply(400, {
        error: {
          code: "invalid_holdings",
          message: "Composição inválida.",
          details: { reason: "weights_sum", sum: "99.99" },
        },
      }),
    );
    const error = await caught(apiPut(PATH, BODY));
    expect(error.status).toBe(400);
    expect(error.code).toBe("invalid_holdings");
    expect(error.details).toEqual({ reason: "weights_sum", sum: "99.99" });
  });
});
