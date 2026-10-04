import logoReverse from "@brand/ruvor-logo-reverse.svg";
import { type FormEvent, useEffect, useId, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";

import { ApiError, apiPost } from "../api/client";
import { Glyph } from "../components/Glyph";
import { TEXTOS } from "../content/textos";
import { safeNext } from "../session/next";
import { useSession } from "../session/SessionProvider";
import { isMe } from "../session/types";

const LOGIN_PATH = "/api/v1/auth/login";

/**
 * O texto do erro geral, pelo `code` (RF-06) — nunca a mensagem da API. Rede e resposta fora
 * do formato (inclusive o 200 que não tem a forma do `me`) têm a mesma frase.
 */
function generalError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return TEXTOS["acesso.erro.rede"];
  }
  switch (error.code) {
    case "invalid_credentials":
      return TEXTOS["acesso.erro.credenciais"];
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
      return TEXTOS["acesso.erro.outro"];
  }
}

/**
 * A tela de entrada (`/entrar?next=`, RF-06 e RF-04), fora do casco, em tela cheia: a cena à
 * esquerda e o formulário à direita, como o `entrada.html` aprovado, só com classes do kit.
 *
 * O campo vazio não manda pedido: fica com `aria-invalid` e o erro em `aria-describedby`, e o
 * foco vai ao primeiro vazio. O erro geral fica na caixa com `role="alert"`, os dois campos
 * continuam preenchidos e o foco fica no "Entrar". Com sucesso, o `me` vai à sessão e a tela
 * navega a `safeNext(next)` por substituição; quem já está logado e abre a tela vai ao mesmo
 * lugar. "Criar conta" leva o mesmo `next` adiante; "Continuar sem entrar" vai ao destino.
 */
export function SignInScreen() {
  const session = useSession();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next");
  const destination = safeNext(next);
  const signUpHref =
    next === null ? "/cadastro" : `/cadastro?next=${encodeURIComponent(next)}`;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailEmpty, setEmailEmpty] = useState(false);
  const [passwordEmpty, setPasswordEmpty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const submitRef = useRef<HTMLButtonElement>(null);
  // Depois de um erro geral, o foco volta ao "Entrar" quando ele deixa de estar desabilitado.
  const focusSubmit = useRef(false);
  // A navegação é uma só: a do sucesso, ou a de quem já chegou logado.
  const navigated = useRef(false);

  const id = useId();
  const titleId = `${id}-titulo`;
  const emailId = `${id}-email`;
  const emailErrorId = `${id}-email-erro`;
  const passwordId = `${id}-senha`;
  const passwordErrorId = `${id}-senha-erro`;
  const noteId = `${id}-senha-nota`;

  const authenticated = session.status === "authenticated";
  useEffect(() => {
    if (authenticated && !navigated.current) {
      navigated.current = true;
      void navigate(destination, { replace: true });
    }
  }, [authenticated, destination, navigate]);

  useEffect(() => {
    if (!busy && focusSubmit.current) {
      focusSubmit.current = false;
      submitRef.current?.focus();
    }
  }, [busy]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const noEmail = email.trim() === "";
    const noPassword = password === "";
    setEmailEmpty(noEmail);
    setPasswordEmpty(noPassword);
    setError(null);
    if (noEmail || noPassword) {
      (noEmail ? emailRef : passwordRef).current?.focus();
      return;
    }

    setBusy(true);
    try {
      const body = await apiPost<unknown>(LOGIN_PATH, {
        email: email.trim(),
        password,
      });
      if (!isMe(body)) {
        throw new ApiError(200, "unexpected_response", "auth/login sem a forma do me");
      }
      navigated.current = true;
      session.setMe(body);
      void navigate(destination, { replace: true });
    } catch (caught) {
      setError(generalError(caught));
      focusSubmit.current = true;
      setBusy(false);
    }
  }

  // Fora do casco, a tela leva a base `.ruvor-app` dela, como o `<body>` do mockup.
  return (
    <div className="ruvor-app">
      <main className="ruvor-access" data-screen="entrada">
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
              <h2
                className="ruvor-h2 ruvor-auth__title"
                id={titleId}
                data-part="titulo"
              >
                {TEXTOS["acesso.titulo"]}
              </h2>
              <p className="ruvor-sub">{TEXTOS["acesso.sub"]}</p>
            </div>

            <div className="ruvor-field" data-part="campo-email">
              <label className="ruvor-label" htmlFor={emailId}>
                {TEXTOS["acesso.email.rotulo"]}
              </label>
              <input
                ref={emailRef}
                className="ruvor-input"
                id={emailId}
                name="email"
                type="email"
                autoComplete="username"
                spellCheck={false}
                placeholder={TEXTOS["acesso.email.placeholder"]}
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setEmailEmpty(false);
                }}
                aria-invalid={emailEmpty ? true : undefined}
                aria-describedby={emailEmpty ? emailErrorId : undefined}
              />
              {emailEmpty && (
                <span className="ruvor-field__error" id={emailErrorId}>
                  <Glyph name="x-circle" className="ruvor-glyph--sm" />
                  <span>{TEXTOS["acesso.erro.emailVazio"]}</span>
                </span>
              )}
            </div>

            <div className="ruvor-field" data-part="campo-senha">
              <label className="ruvor-label" htmlFor={passwordId}>
                {TEXTOS["acesso.senha.rotulo"]}
              </label>
              <input
                ref={passwordRef}
                className="ruvor-input"
                id={passwordId}
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setPasswordEmpty(false);
                }}
                aria-invalid={passwordEmpty ? true : undefined}
                aria-describedby={
                  passwordEmpty ? `${passwordErrorId} ${noteId}` : noteId
                }
              />
              {passwordEmpty && (
                <span className="ruvor-field__error" id={passwordErrorId}>
                  <Glyph name="x-circle" className="ruvor-glyph--sm" />
                  <span>{TEXTOS["acesso.erro.senhaVazia"]}</span>
                </span>
              )}
              <span
                className="ruvor-hint ruvor-hint--top"
                id={noteId}
                data-part="nota-senha"
              >
                <Glyph name="info" className="ruvor-glyph--sm" />
                <span>{TEXTOS["acesso.senha.nota"]}</span>
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
              data-part="botao-entrar"
            >
              {busy && <Glyph name="spinner-gap" className="ruvor-spin" />}
              <span>{busy ? TEXTOS["acesso.entrando"] : TEXTOS["acesso.entrar"]}</span>
            </button>

            <p className="ruvor-auth__alt">
              <span>{TEXTOS["acesso.semConta"]}</span>{" "}
              <Link className="ruvor-link" to={signUpHref} data-part="link-cadastro">
                {TEXTOS["acesso.criarConta"]}
              </Link>
            </p>

            <Link
              className="ruvor-btn ruvor-btn--ghost ruvor-btn--block"
              to={destination}
              data-part="link-continuar"
            >
              {TEXTOS["acesso.continuar"]}
            </Link>
          </form>
        </section>
      </main>
    </div>
  );
}
