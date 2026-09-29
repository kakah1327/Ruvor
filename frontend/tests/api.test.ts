/**
 * V-04 (parte do cliente) e o X-CSRFToken do V-11: com `fetch` substituído, o formato de
 * erro da D-86 vira ApiError com o `code`; a falha de rede vira `network_error`; o `POST`
 * manda o X-CSRFToken só quando o cookie existe.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiGet, apiPost } from "../src/api/client";

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

  it("não manda o X-CSRFToken quando o cookie não existe", async () => {
    stubCookie("outro=1");
    const fetchMock = stubFetch(202, { ticker: "ABCD3" });
    await apiPost("/api/v1/assets/ABCD3/risk");
    const [, init] = fetchMock.mock.calls[0] as FetchArgs;
    expect(new Headers(init.headers).has("X-CSRFToken")).toBe(false);
  });

  it("o GET nunca manda o X-CSRFToken", async () => {
    stubCookie("csrftoken=abc123");
    const fetchMock = stubFetch(200, {});
    await apiGet("/api/v1/assets");
    const [, init] = fetchMock.mock.calls[0] as FetchArgs;
    expect(new Headers(init.headers).has("X-CSRFToken")).toBe(false);
  });

  it("409 asset_already_covered leva os detalhes", async () => {
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
