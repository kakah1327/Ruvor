import type { Ref } from "react";
import { Link, useLocation } from "react-router";

import { TEXTOS } from "../content/textos";
import { signInHref } from "../session/next";
import { Glyph } from "./Glyph";

/**
 * O aviso para entrar (RF-16), como no `conta.html` aprovado: o mesmo componente, com dois
 * títulos, escolhidos por `ended`.
 *
 * - `ended`: **"A sua sessão terminou."** — no lugar da ação que recebeu 401 de quem estava
 *   logado (o botão de calcular, o formulário da troca de senha), com `role="alert"`;
 * - sem `ended`: **"Esta página é para quem entrou na conta."** — no corpo de uma página que
 *   exige conta, aberta por quem não entrou (anônimo desde a carga).
 *
 * O que os distingue é o estado de sessão antes da resposta, e quem o sabe é a tela: o aviso
 * não lê a sessão. O link "Entrar" leva a `/entrar?next=<página atual>`, por `signInHref`.
 * `linkRef` deixa a tela pôr o foco nele; `onSignIn` roda no clique, antes da navegação.
 */
export function SignInNotice({
  ended,
  linkRef,
  onSignIn,
}: {
  ended: boolean;
  linkRef?: Ref<HTMLAnchorElement>;
  onSignIn?: () => void;
}) {
  const location = useLocation();
  return (
    <div
      className="ruvor-state ruvor-state--notice ruvor-state--signin"
      data-signin-notice={ended ? "ended" : "required"}
      role={ended ? "alert" : undefined}
    >
      <span className="ruvor-icon ruvor-icon--evidence">
        <Glyph name="info" weight="duotone" />
      </span>
      <div className="ruvor-state__body">
        <p className="ruvor-state__title">
          {ended
            ? TEXTOS["conta.aviso.terminou"]
            : TEXTOS["conta.aviso.paraQuemEntrou"]}
        </p>
        <p className="ruvor-note ruvor-keep">{TEXTOS["conta.aviso.volta"]}</p>
        <Link
          ref={linkRef}
          className="ruvor-btn ruvor-btn--primary"
          to={signInHref(location.pathname + location.search)}
          onClick={onSignIn}
        >
          {TEXTOS["conta.entrar"]}
        </Link>
      </div>
    </div>
  );
}
