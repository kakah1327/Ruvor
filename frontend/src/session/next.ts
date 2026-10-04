/**
 * O `next` das telas de entrada (RF-04): só caminho interno, conferido pelo `URL` do
 * navegador e nunca por prefixo de texto. O destino é `pathname + search` normalizado pelo
 * `URL` — nunca a cadeia recebida. `next` ausente, inválido, de outra origem, ou que volta à
 * própria entrada (`/entrar`, `/cadastro`), vale `/`.
 */
export function safeNext(next: string | null, origin = window.location.origin): string {
  if (!next) return "/";
  let u: URL;
  try {
    u = new URL(next, origin);
  } catch {
    return "/";
  }
  if (u.origin !== origin) return "/";
  if (u.pathname === "/entrar" || u.pathname === "/cadastro") return "/";
  return u.pathname + u.search;
}

/** O link para a entrada, com o caminho e a busca de onde a pessoa sai: todo link passa por aqui. */
export function signInHref(pathAndSearch: string): string {
  return `/entrar?next=${encodeURIComponent(pathAndSearch)}`;
}
