import markReverse from "@brand/ruvor-mark-reverse.svg";
import { useCallback, useState } from "react";
import { Link, Outlet, useLocation, useOutletContext } from "react-router";

import { TEXTOS } from "../content/textos";
import { formatDate, formatInstant } from "../format/numbers";
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

// Os ícones de brand/ruvor/icons/regular/ (D-93), o `d` copiado do arquivo oficial.
const INFO_PATH =
  "M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm16-40a8,8,0,0,1-8,8,16,16,0,0,1-16-16V128a8,8,0,0,1,0-16,16,16,0,0,1,16,16v40A8,8,0,0,1,144,176ZM112,84a12,12,0,1,1,12,12A12,12,0,0,1,112,84Z";
const DATABASE_PATH =
  "M128,24C74.17,24,32,48.6,32,80v96c0,31.4,42.17,56,96,56s96-24.6,96-56V80C224,48.6,181.83,24,128,24Zm80,104c0,9.62-7.88,19.43-21.61,26.92C170.93,163.35,150.19,168,128,168s-42.93-4.65-58.39-13.08C55.88,147.43,48,137.62,48,128V111.36c17.06,15,46.23,24.64,80,24.64s62.94-9.68,80-24.64ZM69.61,53.08C85.07,44.65,105.81,40,128,40s42.93,4.65,58.39,13.08C200.12,60.57,208,70.38,208,80s-7.88,19.43-21.61,26.92C170.93,115.35,150.19,120,128,120s-42.93-4.65-58.39-13.08C55.88,99.43,48,89.62,48,80S55.88,60.57,69.61,53.08ZM186.39,202.92C170.93,211.35,150.19,216,128,216s-42.93-4.65-58.39-13.08C55.88,195.43,48,185.62,48,176V159.36c17.06,15,46.23,24.64,80,24.64s62.94-9.68,80-24.64V176C208,185.62,200.12,195.43,186.39,202.92Z";

function Glyph({ path }: { path: string }) {
  return (
    <svg
      className="ruvor-glyph"
      viewBox="0 0 256 256"
      aria-hidden="true"
      focusable="false"
    >
      <path d={path} />
    </svg>
  );
}

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

        {/* O lugar da busca na barra: a T7 o preenche. */}
        <div className="ruvor-topbar__spacer" aria-hidden="true" />

        <ThemeSwitch />
      </header>

      <div className="ruvor-workspace ruvor-workspace--full ruvor-workspace--footer">
        <main className="ruvor-content">
          <Outlet context={context} />
        </main>

        <footer className="ruvor-footer">
          <p>
            <Glyph path={INFO_PATH} />
            <span>{TEXTOS["rodape.ressalva"]}</span>
          </p>
          <p>
            <Glyph path={DATABASE_PATH} />
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
