import { useId } from "react";

import { SearchBox } from "../components/SearchBox";
import { TEXTOS } from "../content/textos";

/** A página inicial (RF-05): o campo grande, com a lista inteira na página. */
export function SearchScreen() {
  const titleId = useId();

  return (
    <section className="ruvor-home" aria-labelledby={titleId}>
      <p className="ruvor-eyebrow">{TEXTOS["busca.eyebrow"]}</p>
      <h1 className="ruvor-display" id={titleId}>
        {TEXTOS["busca.titulo"]}
      </h1>
      <p className="ruvor-sub">{TEXTOS["busca.sub"]}</p>
      <SearchBox variant="page" />
    </section>
  );
}
