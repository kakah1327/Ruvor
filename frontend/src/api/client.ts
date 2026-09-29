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

async function request<T>(method: "GET" | "POST", path: string): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (method === "POST") {
    const token = csrfToken();
    if (token !== null) {
      headers["X-CSRFToken"] = token;
    }
  }

  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, { method, headers });
  } catch (error) {
    throw new ApiError(
      0,
      "network_error",
      error instanceof Error ? error.message : String(error),
    );
  }

  let body: unknown;
  let parsed = true;
  try {
    body = await response.json();
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
    return body as T;
  }

  const error = parsed ? parseError(body) : null;
  if (error !== null) {
    throw new ApiError(response.status, error.code, error.message, error.details);
  }
  throw new ApiError(
    response.status,
    "unexpected_response",
    `HTTP ${response.status} fora do formato de erro da API`,
  );
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>("GET", path);
}

export function apiPost<T>(path: string): Promise<T> {
  return request<T>("POST", path);
}
