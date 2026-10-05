import { NavLink } from "react-router";

import { TEXTOS } from "../content/textos";
import { Glyph } from "./Glyph";

/**
 * As abas da tela do ativo: cada uma é um caminho debaixo de `/ativos/{ticker}`, e a visão
 * geral é o próprio `/ativos/{ticker}`, sem segmento. O `slug` é o segmento da URL.
 */
export const ASSET_TABS = [
  { slug: "", label: TEXTOS["ativo.aba.visaoGeral"] },
  { slug: "risco", label: TEXTOS["ativo.aba.risco"] },
  { slug: "laboratorio", label: TEXTOS["ativo.aba.laboratorio"] },
  { slug: "retorno", label: TEXTOS["ativo.aba.retorno"] },
  { slug: "fundamentos", label: TEXTOS["ativo.aba.fundamentos"] },
  { slug: "comunicados", label: TEXTOS["ativo.aba.comunicados"] },
] as const;

export type AssetTab = (typeof ASSET_TABS)[number]["slug"];

/** O segmento da URL como aba; `null` quando não é nenhuma delas. */
export function tabFromSlug(slug: string | undefined): AssetTab | null {
  const value = slug ?? "";
  return ASSET_TABS.find((tab) => tab.slug === value)?.slug ?? null;
}

/** O endereço de uma aba do ativo. */
export function assetTabPath(ticker: string, tab: AssetTab): string {
  const base = `/ativos/${encodeURIComponent(ticker)}`;
  return tab === "" ? base : `${base}/${tab}`;
}

type Props = {
  ticker: string;
  /** Se as explicações estão à vista, e a troca (`src/explain.ts`). */
  explain: boolean;
  onToggleExplain: () => void;
};

/**
 * A barra de abas, logo abaixo do cabeçalho; o `NavLink` marca a corrente com `aria-current`.
 * No fim da barra, o botão que mostra e esconde as explicações, com `aria-pressed`.
 */
export function AssetTabs({ ticker, explain, onToggleExplain }: Props) {
  return (
    <div className="ruvor-tabs-bar">
      <nav className="ruvor-tabs" aria-label={TEXTOS["ativo.abas.rotulo"]}>
        <ul className="ruvor-tabs__list">
          {ASSET_TABS.map((tab) => (
            <li key={tab.slug}>
              <NavLink
                className="ruvor-tabs__link"
                to={assetTabPath(ticker, tab.slug)}
                end
                preventScrollReset
              >
                {tab.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <button
        className="ruvor-tabs__explain"
        type="button"
        aria-pressed={explain}
        onClick={onToggleExplain}
      >
        <Glyph name="info" />
        <span>{TEXTOS["ativo.explicacoes"]}</span>
      </button>
    </div>
  );
}
