import logoReverse from "@brand/ruvor-logo-reverse.svg";
import {
  type FormEvent,
  type ReactNode,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router";

import { ApiError, apiPost } from "../api/client";
import { Glyph } from "../components/Glyph";
import { TEXTOS } from "../content/textos";
import { safeNext, signInHref } from "../session/next";
import { useSession } from "../session/SessionProvider";
import { apiFieldLists, FieldErrorList, PasswordHint } from "./SignUpScreen";

const PASSWORD_PATH = "/api/v1/auth/password";

/** Os campos do formulário, na ordem da tela — a ordem em que o foco procura o primeiro erro. */
const FIELDS = ["current", "next", "confirmation"] as const;
type Field = (typeof FIELDS)[number];
type FieldErrors = Partial<Record<Field, string[]>>;

/** O `name` de cada campo: os dois do `PasswordIn` e a confirmação, que não vai à API. */
const NAMES: Record<Field, string> = {
  current: "current_password",
  next: "new_password",
  confirmation: "confirmation",
};

/** A página da troca voluntária: o `next` que aponta para ela mesma não volta a ela. */
const OWN_PATH = "/conta/senha";

/**
 * O texto do erro geral da troca, pelo `code` — nunca a mensagem da API. O 429, o
 * `csrf_failed` e a rede usam as frases da entrada (RF-08: "como no RF-06").
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
      return TEXTOS["senha.erro.outro"];
  }
}

/** O erro da API que vai a um campo: `invalid_credentials` na atual, `new_password` na nova. */
function fieldErrorsOf(caught: unknown): FieldErrors | null {
  if (!(caught instanceof ApiError)) return null;
  if (caught.code === "invalid_credentials") {
    return { current: [TEXTOS["senha.erro.atualIncorreta"]] };
  }
  if (caught.code === "invalid_parameter") {
    const lists = apiFieldLists(caught.details, ["new_password"] as const);
    return lists?.new_password === undefined ? null : { next: lists.new_password };
  }
  return null;
}

/**
 * Trocar a senha (RF-08), em dois modos, com o mesmo formulário — a senha atual, a nova, a
 * confirmação e a dica dos requisitos —, como o `senha.html` aprovado, só com classes do kit:
 *
 * - **voluntária** (`/conta/senha?next=`), no casco: 204 → `reload()` e a frase das outras
 *   sessões; "Continuar" vai a `safeNext(next)` (o `next` que aponta para esta página, a `/`);
 * - **obrigatória** (RF-05), na cena, no lugar de qualquer rota — quem a monta é o provedor da
 *   sessão: 204 → a frase, **sem** `reload()`, que tiraria a tela antes de a frase ser lida;
 *   "Continuar" → `reload()`, e o provedor volta ao `<Outlet>` na mesma URL. "Sair" chama
 *   `signOut()`; se ele falha, a sessão fica e a caixa de erro diz.
 *
 * Campo vazio e a confirmação diferente não mandam pedido. O 401 mostra o aviso de sessão
 * terminada no lugar do formulário, e a tela chama `expired()` só no clique em "Entrar", antes
 * de navegar à entrada com a URL corrente: chamar no 401 tiraria a obrigatória de cena, e
 * navegar com a sessão ainda logada faria a entrada devolver aqui.
 */
export function PasswordScreen({ mode }: { mode: "voluntary" | "required" }) {
  const session = useSession();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const here = location.pathname + location.search;
  const voluntary = mode === "voluntary";

  const destination = safeNext(params.get("next"));
  const continueTo =
    new URL(destination, window.location.origin).pathname === OWN_PATH
      ? "/"
      : destination;

  const [values, setValues] = useState<Record<Field, string>>({
    current: "",
    next: "",
    confirmation: "",
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [outcome, setOutcome] = useState<"form" | "done" | "ended">("form");

  const refs = {
    current: useRef<HTMLInputElement>(null),
    next: useRef<HTMLInputElement>(null),
    confirmation: useRef<HTMLInputElement>(null),
  };
  const submitRef = useRef<HTMLButtonElement>(null);
  // O "Continuar" do sucesso e o "Entrar" do aviso recebem o foco ao aparecer.
  const linkRef = useRef<HTMLAnchorElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const focusAfter = useRef<Field | "submit" | null>(null);

  const id = useId();
  const titleId = `${id}-titulo`;
  const ids = (field: Field) => ({
    input: `${id}-${field}`,
    errors: `${id}-${field}-erro`,
  });
  const hintId = `${id}-nova-dica`;

  useEffect(() => {
    if (outcome !== "form") (linkRef.current ?? buttonRef.current)?.focus();
  }, [outcome]);

  useEffect(() => {
    if (busy || focusAfter.current === null) return;
    const target = focusAfter.current;
    focusAfter.current = null;
    (target === "submit" ? submitRef : refs[target]).current?.focus();
  });

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const found: FieldErrors = {};
    if (values.current === "") found.current = [TEXTOS["senha.erro.atualVazia"]];
    if (values.next === "") found.next = [TEXTOS["senha.erro.novaVazia"]];
    if (values.confirmation === "") {
      found.confirmation = [TEXTOS["senha.erro.confirmacaoVazia"]];
    } else if (values.next !== "" && values.confirmation !== values.next) {
      found.confirmation = [TEXTOS["acesso.erro.confirmacaoDiferente"]];
    }
    setError(null);
    setErrors(found);
    const first = FIELDS.find((field) => found[field] !== undefined);
    if (first !== undefined) {
      refs[first].current?.focus();
      return;
    }

    setBusy(true);
    try {
      await apiPost<undefined>(PASSWORD_PATH, {
        current_password: values.current,
        new_password: values.next,
      });
      // A voluntária relê o `me` já; a obrigatória só no "Continuar" (o bloqueio cairia agora).
      if (voluntary) void session.reload();
      setOutcome("done");
    } catch (caught) {
      if (caught instanceof ApiError && caught.code === "not_authenticated") {
        setOutcome("ended");
      } else {
        const fromApi = fieldErrorsOf(caught);
        if (fromApi !== null) {
          setErrors(fromApi);
          focusAfter.current =
            FIELDS.find((field) => fromApi[field] !== undefined) ?? null;
        } else {
          setError(generalError(caught));
          focusAfter.current = "submit";
        }
      }
    }
    setBusy(false);
  }

  /** "Sair" da obrigatória (RF-10): fica na página pública; de `/conta/*` e `/organizacao/*`, `/`. */
  async function onSignOut() {
    if (leaving) return;
    setLeaving(true);
    setError(null);
    try {
      await session.signOut();
      if (
        location.pathname.startsWith("/conta/") ||
        location.pathname.startsWith("/organizacao/")
      ) {
        void navigate("/");
      }
    } catch {
      setError(TEXTOS["conta.menu.sairFalhou"]);
      setLeaving(false);
    }
  }

  function change(field: Field, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => {
      if (current[field] === undefined) return current;
      const { [field]: _gone, ...rest } = current;
      return rest;
    });
  }

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

  function field(
    key: Field,
    label: string,
    autoComplete: string,
    part: string | undefined,
    hint: ReactNode = null,
  ) {
    return (
      <div className="ruvor-field" data-part={part}>
        <label className="ruvor-label" htmlFor={ids(key).input}>
          {label}
        </label>
        {hint}
        <input
          ref={refs[key]}
          className="ruvor-input"
          id={ids(key).input}
          name={NAMES[key]}
          type="password"
          autoComplete={autoComplete}
          value={values[key]}
          onChange={(event) => change(key, event.target.value)}
          {...described(key, hint === null ? null : hintId)}
        />
        <FieldErrorList id={ids(key).errors} lines={errors[key] ?? []} />
      </div>
    );
  }

  const me = session.status === "authenticated" ? session.me : null;

  const form = (
    <form
      className="ruvor-auth"
      noValidate
      aria-labelledby={titleId}
      aria-busy={busy ? true : undefined}
      data-part={voluntary ? "form" : "form-obrigatoria"}
      onSubmit={(event) => void onSubmit(event)}
    >
      {!voluntary && (
        <div className="ruvor-auth__head">
          <p className="ruvor-eyebrow">{TEXTOS["senha.obrigatoria.eyebrow"]}</p>
          <h2 className="ruvor-h2 ruvor-auth__title" id={titleId}>
            {TEXTOS["senha.obrigatoria.titulo"]}
          </h2>
          <p className="ruvor-sub">{TEXTOS["senha.obrigatoria.sub"]}</p>
          {me !== null && (
            <p className="ruvor-note">{TEXTOS["senha.obrigatoria.conta"](me.email)}</p>
          )}
        </div>
      )}

      {field(
        "current",
        TEXTOS["senha.atual.rotulo"],
        "current-password",
        voluntary ? "campo-atual" : undefined,
      )}
      {field(
        "next",
        TEXTOS["senha.nova.rotulo"],
        "new-password",
        voluntary ? "campo-nova" : undefined,
        <PasswordHint id={hintId} part={voluntary ? "dica-senha" : undefined} />,
      )}
      {field(
        "confirmation",
        TEXTOS["senha.confirmacao.rotulo"],
        "new-password",
        voluntary ? "campo-confirmacao" : undefined,
      )}

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
        data-part={voluntary ? "botao-trocar" : undefined}
      >
        {busy && <Glyph name="spinner-gap" className="ruvor-spin" />}
        <span>{busy ? TEXTOS["senha.trocando"] : TEXTOS["senha.trocar"]}</span>
      </button>

      {!voluntary && (
        <button
          className="ruvor-btn ruvor-btn--ghost ruvor-btn--block"
          type="button"
          disabled={leaving}
          data-part="botao-sair"
          onClick={() => void onSignOut()}
        >
          <Glyph name="sign-out" />
          <span>{TEXTOS["senha.obrigatoria.sair"]}</span>
        </button>
      )}
    </form>
  );

  const done = (
    <div className="ruvor-state" role="status">
      <span className="ruvor-icon ruvor-icon--validated">
        <Glyph name="check-circle" weight="duotone" />
      </span>
      <div className="ruvor-state__body">
        <p className="ruvor-state__title">{TEXTOS["senha.sucesso.titulo"]}</p>
        <p className="ruvor-state__text">{TEXTOS["senha.sucesso.texto"]}</p>
        <div className="ruvor-state__actions">
          {voluntary ? (
            <Link
              ref={linkRef}
              className="ruvor-btn ruvor-btn--primary"
              to={continueTo}
            >
              {TEXTOS["senha.sucesso.continuar"]}
            </Link>
          ) : (
            <button
              ref={buttonRef}
              className="ruvor-btn ruvor-btn--primary"
              type="button"
              onClick={() => void session.reload()}
            >
              {TEXTOS["senha.sucesso.continuar"]}
            </button>
          )}
        </div>
      </div>
    </div>
  );

  // O aviso de sessão terminada (RF-16), no lugar do formulário.
  const ended = (
    <div
      className="ruvor-state ruvor-state--notice ruvor-state--signin"
      data-signin-notice="ended"
      role="alert"
    >
      <span className="ruvor-icon ruvor-icon--evidence">
        <Glyph name="info" weight="duotone" />
      </span>
      <div className="ruvor-state__body">
        <p className="ruvor-state__title">{TEXTOS["conta.aviso.terminou"]}</p>
        <p className="ruvor-note">{TEXTOS["conta.aviso.volta"]}</p>
        <Link
          ref={linkRef}
          className="ruvor-btn ruvor-btn--primary"
          to={signInHref(here)}
          onClick={() => session.expired()}
        >
          {TEXTOS["conta.entrar"]}
        </Link>
      </div>
    </div>
  );

  if (voluntary) {
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="senha">
        <div className="ruvor-page-head">
          <div>
            <p className="ruvor-eyebrow">{TEXTOS["senha.eyebrow"]}</p>
            <h1 className="ruvor-display" id={titleId}>
              {TEXTOS["senha.titulo"]}
            </h1>
            <p className="ruvor-sub">{TEXTOS["senha.sub"]}</p>
          </div>
        </div>
        {outcome === "ended" ? (
          <div className="ruvor-panel--narrow">{ended}</div>
        ) : (
          <section className="ruvor-panel ruvor-panel--narrow">
            <div className="ruvor-panel__body">{outcome === "done" ? done : form}</div>
          </section>
        )}
      </div>
    );
  }

  // Fora do casco, a tela leva a base `.ruvor-app` dela, como o `<body>` do mockup.
  return (
    <div className="ruvor-app">
      <main className="ruvor-access" data-screen="senha-obrigatoria">
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
          {outcome === "form" ? (
            form
          ) : (
            <div className="ruvor-auth">{outcome === "done" ? done : ended}</div>
          )}
        </section>
      </main>
    </div>
  );
}
