/**
 * O cliente de /api/v1/. Todo erro sai como ApiError:
 *
 * - resposta de erro no formato da D-86 (`{"error": {"code", "message", "details"}}`): o
 *   status e os três campos;
 * - falha de rede (o `fetch` rejeitou): `status` 0 e `code` "network_error";
 * - resposta fora do formato — erro sem o corpo da D-86, ou 2xx sem JSON: o status e
 *   `code` "unexpected_response".
 *
 * A mensagem do ApiError é a da API, para diagnóstico; a tela mostra o texto dela pelo
 * `code`, do módulo de textos.
 *
 * 204 é sucesso sem corpo: devolve `undefined`. Todo método que não é `GET` manda o
 * `X-CSRFToken`, lido do cookie na hora do pedido (o `login()` do Django troca o cookie,
 * e o cliente não guarda cópia). Sem o cookie, pede `GET /api/v1/auth/csrf` antes — e, se
 * esse pedido falha, o erro dele sobe e o pedido não sai. A resposta 403 `csrf_failed`
 * leva a um `auth/csrf` e a **uma** repetição; na segunda falha, o erro sobe (RF-02).
 */

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;

  constructor(
    status: number,
    code: string,
    message: string,
    details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/** Lida a cada pedido, e não no carregamento do módulo: os testes a trocam. */
function baseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? "";
}

/** O valor do cookie `csrftoken`, ou null quando ele não existe. */
function csrfToken(): string | null {
  const cookies = typeof document === "undefined" ? "" : document.cookie;
  for (const part of cookies.split(";")) {
    const [name, ...rest] = part.trim().split("=");
    if (name === "csrftoken") {
      const value = rest.join("=");
      return value === "" ? null : decodeURIComponent(value);
    }
  }
  return null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** O erro no formato da D-86, ou null se o corpo não tiver esse formato. */
function parseError(
  body: unknown,
): { code: string; message: string; details: Record<string, unknown> } | null {
  if (!isRecord(body) || !isRecord(body.error)) {
    return null;
  }
  const { code, message, details } = body.error;
  if (typeof code !== "string" || typeof message !== "string") {
    return null;
  }
  return { code, message, details: isRecord(details) ? details : {} };
}

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

/** A rota que garante o cookie `csrftoken` (M2.1a). */
const CSRF_PATH = "/api/v1/auth/csrf";

/** Um pedido só, sem CSRF prévio nem repetição: o `fetch` e a leitura da resposta. */
async function exchange<T>(method: Method, path: string, body: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const init: RequestInit = { method, headers };
  if (method !== "GET") {
    const token = csrfToken();
    if (token !== null) {
      headers["X-CSRFToken"] = token;
    }
  }
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, init);
  } catch (error) {
    throw new ApiError(
      0,
      "network_error",
      error instanceof Error ? error.message : String(error),
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  let parsed = true;
  let responseBody: unknown;
  try {
    responseBody = await response.json();
  } catch {
    parsed = false;
  }

  if (response.ok) {
    if (!parsed) {
      throw new ApiError(
        response.status,
        "unexpected_response",
        `HTTP ${response.status} sem corpo JSON`,
      );
    }
    return responseBody as T;
  }

  const error = parsed ? parseError(responseBody) : null;
  if (error !== null) {
    throw new ApiError(response.status, error.code, error.message, error.details);
  }
  throw new ApiError(
    response.status,
    "unexpected_response",
    `HTTP ${response.status} fora do formato de erro da API`,
  );
}

/** Pede o cookie `csrftoken`; a falha sobe como o ApiError do `auth/csrf`. */
async function refreshCsrf(): Promise<void> {
  await exchange<undefined>("GET", CSRF_PATH, undefined);
}

/**
 * O pedido com o CSRF do RF-02. `retried` marca a repetição depois de um 403
 * `csrf_failed`: ela não repete de novo — nunca um laço.
 */
async function request<T>(
  method: Method,
  path: string,
  body: unknown,
  retried = false,
): Promise<T> {
  if (method !== "GET" && !retried && csrfToken() === null) {
    await refreshCsrf();
  }
  try {
    return await exchange<T>(method, path, body);
  } catch (error) {
    if (
      method !== "GET" &&
      !retried &&
      error instanceof ApiError &&
      error.status === 403 &&
      error.code === "csrf_failed"
    ) {
      await refreshCsrf();
      return request<T>(method, path, body, true);
    }
    throw error;
  }
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>("GET", path, undefined);
}

/** `body` opcional: sem ele, o pedido sai sem corpo, como as chamadas de antes. */
export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>("POST", path, body);
}

/** A forma do `apiPatch` (M2.2b, RF-15): corpo JSON e `X-CSRFToken`. */
export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>("PUT", path, body);
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return request<T>("PATCH", path, body);
}

export function apiDelete<T = undefined>(path: string): Promise<T> {
  return request<T>("DELETE", path, undefined);
}
