import { useId } from "react";
import { Link, useLocation } from "react-router";

import { TEXTOS } from "../content/textos";

// brand/ruvor/icons/regular/arrow-left.svg (D-93), o `d` copiado do arquivo oficial.
const ARROW_LEFT_PATH =
  "M224,128a8,8,0,0,1-8,8H59.31l58.35,58.34a8,8,0,0,1-11.32,11.32l-72-72a8,8,0,0,1,0-11.32l72-72a8,8,0,0,1,11.32,11.32L59.31,120H216A8,8,0,0,1,224,128Z";

/** "Página não encontrada" (RF-01), dentro do casco, com o endereço digitado e o caminho para a busca. */
export function NotFoundScreen() {
  const { pathname } = useLocation();
  const titleId = useId();

  return (
    <section className="ruvor-notfound" aria-labelledby={titleId}>
      <p className="ruvor-eyebrow">{TEXTOS["casco.naoEncontrada.eyebrow"]}</p>
      <h1 className="ruvor-display" id={titleId}>
        {TEXTOS["casco.naoEncontrada.titulo"]}
      </h1>
      <p className="ruvor-sub">
        {TEXTOS["casco.naoEncontrada.antes"]}
        <span className="ruvor-path">{pathname}</span>
        {TEXTOS["casco.naoEncontrada.depois"]}
      </p>
      <p className="ruvor-sub">{TEXTOS["casco.naoEncontrada.dica"]}</p>
      <Link className="ruvor-btn ruvor-btn--primary" to="/">
        <svg
          className="ruvor-glyph"
          viewBox="0 0 256 256"
          aria-hidden="true"
          focusable="false"
        >
          <path d={ARROW_LEFT_PATH} />
        </svg>
        <span>{TEXTOS["casco.irParaBusca"]}</span>
      </Link>
    </section>
  );
}
