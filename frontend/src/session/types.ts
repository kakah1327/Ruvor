/**
 * Os corpos das rotas de conta do M2.1a: o `me` (`services.me_body`) e o usuário da gestão
 * (`services.user_body`), como a API os entrega.
 */

export type Me = {
  email: string;
  name: string;
  role: "admin" | "member";
  must_change_password: boolean;
  is_staff: boolean;
  organization: { name: string; slug: string; is_personal: boolean };
};

export type OrgUser = {
  email: string;
  name: string;
  role: "admin" | "member";
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
  last_login: string | null;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Confere a forma do `me`: cada chave de `Me`, com o tipo dela. */
export function isMe(value: unknown): value is Me {
  if (!isRecord(value) || !isRecord(value.organization)) {
    return false;
  }
  const org = value.organization;
  return (
    typeof value.email === "string" &&
    typeof value.name === "string" &&
    (value.role === "admin" || value.role === "member") &&
    typeof value.must_change_password === "boolean" &&
    typeof value.is_staff === "boolean" &&
    typeof org.name === "string" &&
    typeof org.slug === "string" &&
    typeof org.is_personal === "boolean"
  );
}
