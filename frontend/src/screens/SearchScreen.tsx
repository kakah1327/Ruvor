import { useId } from "react";

import { Glyph } from "../components/Glyph";
import { SearchBox } from "../components/SearchBox";
import { TEXTOS } from "../content/textos";

/** O ícone de cada bloco de "o que a página do ativo mostra", na ordem de `busca.pagina`. */
const PAGINA_ICONES = ["chart-line", "shield-check", "scales", "buildings"] as const;

/**
 * A página inicial (RF-05): o campo grande, com a lista inteira na página; abaixo dele, os
 * números do método e o que a página do ativo mostra.
 */
export function SearchScreen() {
  const titleId = useId();
  const metodoId = useId();
  const paginaId = useId();

  return (
    <div className="ruvor-home-page">
      <section className="ruvor-home" aria-labelledby={titleId}>
        <p className="ruvor-eyebrow">{TEXTOS["busca.eyebrow"]}</p>
        <h1 className="ruvor-display" id={titleId}>
          {TEXTOS["busca.titulo"]}
        </h1>
        <p className="ruvor-sub">{TEXTOS["busca.sub"]}</p>
        <SearchBox variant="page" />
      </section>

      <section className="ruvor-home-facts" aria-labelledby={metodoId}>
        <h2 className="ruvor-eyebrow" id={metodoId}>
          {TEXTOS["busca.metodoTitulo"]}
        </h2>
        <dl className="ruvor-home-facts__list">
          {TEXTOS["busca.metodo"].map((item) => (
            <div className="ruvor-home-facts__item" key={item.rotulo}>
              <dt className="ruvor-home-facts__value">{item.valor}</dt>
              <dd className="ruvor-home-facts__label">{item.rotulo}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="ruvor-home-tour" aria-labelledby={paginaId}>
        <h2 className="ruvor-eyebrow" id={paginaId}>
          {TEXTOS["busca.paginaTitulo"]}
        </h2>
        <ul className="ruvor-home-tour__list">
          {TEXTOS["busca.pagina"].map((item, i) => (
            <li className="ruvor-panel ruvor-home-tour__item" key={item.titulo}>
              <span className="ruvor-home-tour__icon">
                <Glyph name={PAGINA_ICONES[i] ?? "info"} className="ruvor-glyph--lg" />
              </span>
              <h3 className="ruvor-h3">{item.titulo}</h3>
              <p className="ruvor-note">{item.texto}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
