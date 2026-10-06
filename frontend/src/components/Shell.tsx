import markReverse from "@brand/ruvor-mark-reverse.svg";
import { useCallback, useState } from "react";
import { Link, Outlet, useLocation, useOutletContext } from "react-router";

import { TEXTOS } from "../content/textos";
import { formatDate, formatInstant } from "../format/numbers";
import { AccountMenu } from "./AccountMenu";
import { Glyph } from "./Glyph";
import { ReadingSwitch } from "./ReadingSwitch";
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
  /**
   * Liga ou desliga a coluna lateral (a trilha do cálculo, RF-16). Ligada, o casco desenha
   * a área em duas colunas, como o `ativo.html`, com a coluna vazia; a tela põe o conteúdo
   * nela por `createPortal`, em `railElement`.
   */
  setRail: (on: boolean) => void;
  /** O `<aside>` da coluna lateral, quando ela está ligada e montada; senão, `null`. */
  railElement: HTMLElement | null;
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
 * rodapé deixa de mostrá-la sem depender de a tela limpar. A coluna lateral, também.
 *
 * O `<main>` fica sempre no mesmo lugar da árvore, com a coluna ligada ou não: trocar o
 * pai dele desmontaria a tela.
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

  // O endereço em que a tela ligou a coluna lateral; em outro, ela está desligada.
  const [railPathname, setRailPathname] = useState<string | null>(null);
  const setRail = useCallback(
    (on: boolean) => {
      setRailPathname(on ? pathname : null);
    },
    [pathname],
  );
  const railOn = railPathname === pathname;
  const [railElement, setRailElement] = useState<HTMLElement | null>(null);

  const context: ShellContext = {
    setProvenance,
    setRail,
    railElement: railOn ? railElement : null,
  };

  return (
    <div className="ruvor-app">
      <header className="ruvor-topbar" data-part="barra">
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

        {/* As duas chaves, a de leitura antes da de tema (RF-01 e RF-11 do M2.3): o arranjo
            em 1440 e em 360 px é o do casco-e-preco.html, em .ruvor-topbar__prefs. O lugar da
            conta por último, depois da chave de tema (RF-09 do M2.1b, o conta.html aprovado). */}
        <div className="ruvor-topbar__prefs">
          <ReadingSwitch />
          <ThemeSwitch />
          <AccountMenu />
        </div>
      </header>

      <div className="ruvor-workspace ruvor-workspace--full ruvor-workspace--footer">
        {/* Com a coluna lateral, a área em duas colunas (.ruvor-workspace), e o rodapé embaixo
            das duas, como no ativo.html; sem ela, um invólucro neutro. */}
        <div className={railOn ? "ruvor-workspace" : undefined}>
          <main className="ruvor-content">
            <Outlet context={context} />
          </main>
          {railOn && (
            <aside className="ruvor-rail ruvor-rail--stack" ref={setRailElement} />
          )}
        </div>

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
