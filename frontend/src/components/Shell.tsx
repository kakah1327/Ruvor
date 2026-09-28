import markReverse from "@brand/ruvor-mark-reverse.svg";
import { useCallback, useState } from "react";
import { Link, Outlet, useLocation, useOutletContext } from "react-router";

import { TEXTOS } from "../content/textos";
import { formatDate, formatInstant } from "../format/numbers";
import { Glyph } from "./Glyph";
import { SearchBox } from "./SearchBox";
import { ThemeSwitch } from "./ThemeSwitch";

/** A proveniência da tela do ativo, no rodapé (RF-04, RF-16): a T11 a preenche. */
export type Provenance = {
  /** O último pregão usado, `AAAA-MM-DD`. */
  asOfDate: string;
  /** O instante do cálculo, ISO com deslocamento. */
  calculatedAt: string;
};

/** O que o casco passa às telas pelo `<Outlet>`. */
export type ShellContext = {
  setProvenance: (provenance: Provenance | null) => void;
};

/** Para a tela, dentro do casco: `const { setProvenance } = useShellContext()`. */
export function useShellContext(): ShellContext {
  return useOutletContext<ShellContext>();
}

/** O instante no fuso da B3, como no `ativo.html` aprovado. */
const PROVENANCE_TIME_ZONE = "America/Sao_Paulo";

/**
 * O casco (RF-01 a RF-04): a barra superior, a área da tela e o rodapé, em toda rota.
 *
 * A proveniência fica guardada junto do endereço em que a tela a deu: ao sair dele, o
 * rodapé deixa de mostrá-la sem depender de a tela limpar.
 */
export function Shell() {
  const { pathname } = useLocation();
  const [stored, setStored] = useState<{
    pathname: string;
    provenance: Provenance;
  } | null>(null);

  const setProvenance = useCallback(
    (provenance: Provenance | null) => {
      setStored(provenance === null ? null : { pathname, provenance });
    },
    [pathname],
  );

  const provenance =
    stored !== null && stored.pathname === pathname ? stored.provenance : null;
  const context: ShellContext = { setProvenance };

  return (
    <div className="ruvor-app">
      <header className="ruvor-topbar">
        <Link className="ruvor-brand" to="/" aria-label={TEXTOS["casco.marca.rotulo"]}>
          <img src={markReverse} alt="" />
          <b>{TEXTOS["casco.marca"]}</b>
        </Link>

        {/* RF-02: na página de busca, a barra não tem campo — o grande basta. */}
        {pathname === "/" ? (
          <div className="ruvor-topbar__spacer" aria-hidden="true" />
        ) : (
          <SearchBox variant="bar" />
        )}

        <ThemeSwitch />
      </header>

      <div className="ruvor-workspace ruvor-workspace--full ruvor-workspace--footer">
        <main className="ruvor-content">
          <Outlet context={context} />
        </main>

        <footer className="ruvor-footer">
          <p>
            <Glyph name="info" />
            <span>{TEXTOS["rodape.ressalva"]}</span>
          </p>
          <p>
            <Glyph name="database" />
            <span>
              {TEXTOS["rodape.fonte"]}
              {provenance !== null && (
                <>
                  {" "}
                  <span data-provenance="as-of-date">
                    {TEXTOS["rodape.ultimoPregao"](formatDate(provenance.asOfDate))}
                  </span>{" "}
                  <span data-provenance="calculated-at">
                    {calculatedAtText(provenance.calculatedAt)}
                  </span>
                </>
              )}
            </span>
          </p>
        </footer>
      </div>
    </div>
  );
}

function calculatedAtText(calculatedAt: string): string {
  // `formatInstant` devolve "dd/mm/aaaa hh:mm"; a frase separa a data da hora.
  const [date, time] = formatInstant(calculatedAt, PROVENANCE_TIME_ZONE).split(" ");
  return TEXTOS["rodape.calculadoEm"](date ?? "", time ?? "");
}
