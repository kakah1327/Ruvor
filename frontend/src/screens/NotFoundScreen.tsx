import { useId } from "react";
import { Link, useLocation } from "react-router";

import { Glyph } from "../components/Glyph";
import { TEXTOS } from "../content/textos";

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
        <Glyph name="arrow-left" />
        <span>{TEXTOS["casco.irParaBusca"]}</span>
      </Link>
    </section>
  );
}
