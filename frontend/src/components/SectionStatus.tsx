import { TEXTOS } from "../content/textos";
import { Glyph } from "./Glyph";

/**
 * O erro de uma seção da tela do ativo (RF-06): a frase e o "tentar de novo" na mesma linha,
 * como no `ativo.html` e no `ativo-estados.html` aprovados. O resto da tela continua.
 */
export function SectionError({ onRetry }: { onRetry: () => void }) {
  return (
    <div
      className="ruvor-callout ruvor-callout--critical ruvor-callout--row"
      role="alert"
    >
      <span>{TEXTOS["ativo.erroSecao"]}</span>
      <button className="ruvor-btn" type="button" onClick={onRetry}>
        <Glyph name="arrows-clockwise" />
        <span>{TEXTOS["ativo.tentarDeNovo"]}</span>
      </button>
    </div>
  );
}

/**
 * O carregando de uma seção: o esqueleto do tamanho dela, decorativo — quem o contém leva
 * `aria-busy="true"`, como no `ativo.html`.
 */
export function SectionSkeleton({ short = false }: { short?: boolean }) {
  return (
    <div
      className={
        short
          ? "ruvor-skeleton ruvor-skeleton--block ruvor-skeleton--short"
          : "ruvor-skeleton ruvor-skeleton--block"
      }
      aria-hidden="true"
    />
  );
}
