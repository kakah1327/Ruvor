import logoReverse from "@brand/ruvor-logo-reverse.svg";
import {
  type FormEvent,
  type ReactNode,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import { Link, useNavigate, useSearchParams } from "react-router";

import { ApiError, apiPost } from "../api/client";
import { Glyph } from "../components/Glyph";
import { TEXTOS } from "../content/textos";
import { safeNext } from "../session/next";
import { useSession } from "../session/SessionProvider";
import { isMe } from "../session/types";

const SIGNUP_PATH = "/api/v1/auth/signup";

/** Os campos do formulário, na ordem da tela — a ordem em que o foco procura o primeiro erro. */
const FIELDS = ["name", "email", "password", "confirmation"] as const;
type Field = (typeof FIELDS)[number];

/** As linhas de erro de cada campo: texto da tela, mensagem da API como chega, ou o `email_taken`. */
type FieldErrors = Partial<Record<Field, ReactNode[]>>;

/** Os campos que a API devolve em `details.fields` e que a tela conhece (RF-07). */
const API_FIELDS: readonly Field[] = ["name", "email", "password"];

/**
 * As listas de `details.fields` de um `invalid_parameter`, como chegam. Devolve `null` quando
 * não há lista que a tela saiba pôr num campo — sem `fields`, sem lista de texto, ou com um
 * campo que a tela não conhece: aí vale o erro geral, e erro de campo e erro geral não
 * aparecem juntos.
 */
export function apiFieldLists<K extends string>(
  details: Record<string, unknown>,
  known: readonly K[],
): Partial<Record<K, string[]>> | null {
  const fields = details.fields;
  if (typeof fields !== "object" || fields === null || Array.isArray(fields)) {
    return null;
  }
  const lists: Partial<Record<K, string[]>> = {};
  let any = false;
  for (const [key, value] of Object.entries(fields)) {
    if (!(known as readonly string[]).includes(key)) return null;
    if (!Array.isArray(value)) return null;
    const messages = value.filter((m): m is string => typeof m === "string");
    if (messages.length === 0) return null;
    lists[key as K] = messages;
    any = true;
  }
  return any ? lists : null;
}

/**
 * O texto do erro geral do cadastro, pelo `code` — nunca a mensagem da API. O 429, o
 * `csrf_failed` e a rede usam as frases da entrada (RF-07: "como no RF-06").
 */
function generalError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return TEXTOS["acesso.erro.rede"];
  }
  switch (error.code) {
    case "too_many_requests": {
      const wait = error.details.wait_seconds;
      return TEXTOS["acesso.erro.tentativas"](typeof wait === "number" ? wait : null);
    }
    case "csrf_failed":
      return TEXTOS["acesso.erro.csrf"];
    case "network_error":
    case "unexpected_response":
      return TEXTOS["acesso.erro.rede"];
    default:
      return TEXTOS["cadastro.erro.outro"];
  }
}

/**
 * A dica dos requisitos da senha (RF-07, RF-08), compartilhada pelo cadastro e pelas duas
 * trocas: o ícone, a frase e a lista, antes do campo, ligada a ele por `aria-describedby`.
 */
export function PasswordHint({ id, part }: { id: string; part?: string }) {
  return (
    <div className="ruvor-hint ruvor-hint--top" id={id} data-part={part}>
      <Glyph name="info" className="ruvor-glyph--sm" />
      <div>
        <span>{TEXTOS["acesso.senha.dica"]}</span>
        <ul className="ruvor-hint__list">
          <li>{TEXTOS["acesso.senha.requisito.tamanho"]}</li>
          <li>{TEXTOS["acesso.senha.requisito.numeros"]}</li>
          <li>{TEXTOS["acesso.senha.requisito.parecida"]}</li>
          <li>{TEXTOS["acesso.senha.requisito.comum"]}</li>
        </ul>
      </div>
    </div>
  );
}

/** Os erros de um campo, agrupados num `id` só, uma linha por mensagem. Sem linhas, nada. */
export function FieldErrorList({ id, lines }: { id: string; lines: ReactNode[] }) {
  if (lines.length === 0) return null;
  return (
    <div className="ruvor-field__errors" id={id}>
      {lines.map((line, index) => (
        // A lista é fixa enquanto aparece: muda inteira a cada envio.
        // biome-ignore lint/suspicious/noArrayIndexKey: a mesma mensagem pode vir duas vezes.
        <span className="ruvor-field__error" key={index}>
          <Glyph name="x-circle" className="ruvor-glyph--sm" />
          <span>{line}</span>
        </span>
      ))}
    </div>
  );
}

/**
 * Criar conta (`/cadastro?next=`, RF-07), fora do casco, na cena da entrada, como o
 * `cadastro.html` aprovado, só com classes do kit.
 *
 * Nome, e-mail, senha e a confirmação — conferida no navegador, que a API não recebe. Campo
 * vazio (o nome e o e-mail aparados; a senha e a confirmação só `""`) e a confirmação diferente
 * não mandam pedido. `invalid_parameter` põe cada lista de `details.fields` no campo dela, como
 * chega; campo que a tela não conhece cai no erro geral. `email_taken` fica no e-mail, com o
 * link "Entrar". O foco vai ao primeiro campo com erro; com erro geral, fica no botão.
 *
 * Sucesso: 201 `me`, já logado → `setMe` e `safeNext(next)` por substituição; quem já está
 * logado e abre a tela vai ao mesmo lugar. "Entrar" leva o mesmo `next` adiante.
 */
export function SignUpScreen() {
  const session = useSession();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next");
  const destination = safeNext(next);
  const signInHref =
    next === null ? "/entrar" : `/entrar?next=${encodeURIComponent(next)}`;

  const [values, setValues] = useState<Record<Field, string>>({
    name: "",
    email: "",
    password: "",
    confirmation: "",
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refs = {
    name: useRef<HTMLInputElement>(null),
    email: useRef<HTMLInputElement>(null),
    password: useRef<HTMLInputElement>(null),
    confirmation: useRef<HTMLInputElement>(null),
  };
  const submitRef = useRef<HTMLButtonElement>(null);
  // Depois do envio, o foco vai aonde o resultado pede, quando o botão deixa de estar desabilitado.
  const focusAfter = useRef<Field | "submit" | null>(null);
  // A navegação é uma só: a do sucesso, ou a de quem já chegou logado.
  const navigated = useRef(false);

  const id = useId();
  const titleId = `${id}-titulo`;
  const ids = (field: Field) => ({
    input: `${id}-${field}`,
    errors: `${id}-${field}-erro`,
  });
  const hintId = `${id}-senha-dica`;

  const authenticated = session.status === "authenticated";
  useEffect(() => {
    if (authenticated && !navigated.current) {
      navigated.current = true;
      void navigate(destination, { replace: true });
    }
  }, [authenticated, destination, navigate]);

  useEffect(() => {
    if (busy || focusAfter.current === null) return;
    const target = focusAfter.current;
    focusAfter.current = null;
    (target === "submit" ? submitRef : refs[target]).current?.focus();
  });

  function firstWithError(found: FieldErrors): Field | null {
    return FIELDS.find((field) => (found[field]?.length ?? 0) > 0) ?? null;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const found: FieldErrors = {};
    if (values.name.trim() === "") found.name = [TEXTOS["cadastro.erro.nomeVazio"]];
    if (values.email.trim() === "") found.email = [TEXTOS["acesso.erro.emailVazio"]];
    if (values.password === "") found.password = [TEXTOS["acesso.erro.senhaVazia"]];
    if (values.confirmation === "") {
      found.confirmation = [TEXTOS["cadastro.erro.confirmacaoVazia"]];
    } else if (values.password !== "" && values.confirmation !== values.password) {
      found.confirmation = [TEXTOS["acesso.erro.confirmacaoDiferente"]];
    }
    setError(null);
    setErrors(found);
    const first = firstWithError(found);
    if (first !== null) {
      refs[first].current?.focus();
      return;
    }

    setBusy(true);
    try {
      const body = await apiPost<unknown>(SIGNUP_PATH, {
        email: values.email.trim(),
        name: values.name.trim(),
        password: values.password,
      });
      if (!isMe(body)) {
        throw new ApiError(201, "unexpected_response", "auth/signup sem a forma do me");
      }
      navigated.current = true;
      session.setMe(body);
      void navigate(destination, { replace: true });
    } catch (caught) {
      const fromApi = fieldErrorsOf(caught);
      if (fromApi !== null) {
        setErrors(fromApi);
        focusAfter.current = firstWithError(fromApi);
      } else {
        setError(generalError(caught));
        focusAfter.current = "submit";
      }
      setBusy(false);
    }
  }

  /** O erro da API que vai a um campo: `invalid_parameter` conhecido, ou `email_taken`. */
  function fieldErrorsOf(caught: unknown): FieldErrors | null {
    if (!(caught instanceof ApiError)) return null;
    if (caught.code === "email_taken") {
      return {
        email: [
          <>
            {TEXTOS["cadastro.erro.emailTaken"]}{" "}
            <Link className="ruvor-link" to={signInHref}>
              {TEXTOS["cadastro.erro.emailTakenLink"]}
            </Link>
          </>,
        ],
      };
    }
    if (caught.code === "invalid_parameter") {
      return apiFieldLists(caught.details, API_FIELDS);
    }
    return null;
  }

  function change(field: Field, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    // O erro de um campo some quando a pessoa edita aquele campo.
    setErrors((current) => {
      if (current[field] === undefined) return current;
      const { [field]: _gone, ...rest } = current;
      return rest;
    });
  }

  /** As propriedades de acessibilidade de um campo: o erro e, na senha, a dica. */
  function described(field: Field, base: string | null = null) {
    const lines = errors[field] ?? [];
    const describedBy = [base, lines.length > 0 ? ids(field).errors : null]
      .filter((value) => value !== null)
      .join(" ");
    return {
      "aria-invalid": lines.length > 0 ? true : undefined,
      "aria-describedby": describedBy === "" ? undefined : describedBy,
    };
  }

  // Fora do casco, a tela leva a base `.ruvor-app` dela, como o `<body>` do mockup.
  return (
    <div className="ruvor-app">
      <main className="ruvor-access" data-screen="cadastro">
        <section className="ruvor-scene" data-part="cena">
          <img
            className="ruvor-scene__logo"
            src={logoReverse}
            alt={TEXTOS["acesso.cena.marca"]}
          />
          <div className="ruvor-scene__copy">
            <p className="ruvor-eyebrow">{TEXTOS["acesso.cena.eyebrow"]}</p>
            <h1 className="ruvor-display ruvor-scene__title">
              {TEXTOS["acesso.cena.titulo"]}
            </h1>
            <p className="ruvor-scene__text">{TEXTOS["acesso.cena.texto"]}</p>
          </div>
        </section>

        <section className="ruvor-access__side">
          <form
            className="ruvor-auth"
            noValidate
            aria-labelledby={titleId}
            aria-busy={busy ? true : undefined}
            data-part="form"
            onSubmit={(event) => void onSubmit(event)}
          >
            <div className="ruvor-auth__head">
              <p className="ruvor-eyebrow">{TEXTOS["acesso.eyebrow"]}</p>
              <h2 className="ruvor-h2 ruvor-auth__title" id={titleId}>
                {TEXTOS["cadastro.titulo"]}
              </h2>
              <p className="ruvor-sub">{TEXTOS["cadastro.sub"]}</p>
            </div>

            <div className="ruvor-field" data-part="campo-nome">
              <label className="ruvor-label" htmlFor={ids("name").input}>
                {TEXTOS["cadastro.nome.rotulo"]}
              </label>
              <input
                ref={refs.name}
                className="ruvor-input"
                id={ids("name").input}
                name="name"
                type="text"
                autoComplete="name"
                value={values.name}
                onChange={(event) => change("name", event.target.value)}
                {...described("name")}
              />
              <FieldErrorList id={ids("name").errors} lines={errors.name ?? []} />
            </div>

            <div className="ruvor-field" data-part="campo-email">
              <label className="ruvor-label" htmlFor={ids("email").input}>
                {TEXTOS["acesso.email.rotulo"]}
              </label>
              <input
                ref={refs.email}
                className="ruvor-input"
                id={ids("email").input}
                name="email"
                type="email"
                autoComplete="username"
                spellCheck={false}
                placeholder={TEXTOS["acesso.email.placeholder"]}
                value={values.email}
                onChange={(event) => change("email", event.target.value)}
                {...described("email")}
              />
              <FieldErrorList id={ids("email").errors} lines={errors.email ?? []} />
            </div>

            <div className="ruvor-field" data-part="campo-senha">
              <label className="ruvor-label" htmlFor={ids("password").input}>
                {TEXTOS["acesso.senha.rotulo"]}
              </label>
              {/* A dica vem ANTES do campo (RF-07): quem lê, lê antes de digitar. */}
              <PasswordHint id={hintId} part="dica-senha" />
              <input
                ref={refs.password}
                className="ruvor-input"
                id={ids("password").input}
                name="password"
                type="password"
                autoComplete="new-password"
                value={values.password}
                onChange={(event) => change("password", event.target.value)}
                {...described("password", hintId)}
              />
              <FieldErrorList
                id={ids("password").errors}
                lines={errors.password ?? []}
              />
            </div>

            <div className="ruvor-field" data-part="campo-confirmacao">
              <label className="ruvor-label" htmlFor={ids("confirmation").input}>
                {TEXTOS["cadastro.confirmacao.rotulo"]}
              </label>
              <input
                ref={refs.confirmation}
                className="ruvor-input"
                id={ids("confirmation").input}
                name="password_confirmation"
                type="password"
                autoComplete="new-password"
                value={values.confirmation}
                onChange={(event) => change("confirmation", event.target.value)}
                {...described("confirmation")}
              />
              <FieldErrorList
                id={ids("confirmation").errors}
                lines={errors.confirmation ?? []}
              />
            </div>

            {/* A frase da conta pessoal (RF-07, D-101). */}
            <div className="ruvor-hint ruvor-hint--top">
              <Glyph name="info" className="ruvor-glyph--sm" />
              <span>
                <span>{TEXTOS["cadastro.pessoal"]}</span>{" "}
                <span>{TEXTOS["cadastro.pessoal.organizacao"]}</span>
              </span>
            </div>

            {error !== null && (
              <div
                className="ruvor-callout ruvor-callout--critical ruvor-form-error"
                role="alert"
              >
                <Glyph name="warning" />
                <span>{error}</span>
              </div>
            )}

            <button
              ref={submitRef}
              className="ruvor-btn ruvor-btn--primary ruvor-btn--block"
              type="submit"
              disabled={busy}
              aria-busy={busy ? true : undefined}
              data-part="botao-criar"
            >
              {busy && <Glyph name="spinner-gap" className="ruvor-spin" />}
              <span>
                {busy ? TEXTOS["cadastro.criando"] : TEXTOS["cadastro.criar"]}
              </span>
            </button>

            <p className="ruvor-auth__alt">
              <span>{TEXTOS["cadastro.temConta"]}</span>{" "}
              <Link className="ruvor-link" to={signInHref}>
                {TEXTOS["acesso.entrar"]}
              </Link>
            </p>

            <Link
              className="ruvor-btn ruvor-btn--ghost ruvor-btn--block"
              to={destination}
            >
              {TEXTOS["acesso.continuar"]}
            </Link>
          </form>
        </section>
      </main>
    </div>
  );
}
