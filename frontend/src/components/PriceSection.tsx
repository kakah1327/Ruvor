import { useId } from "react";

import type { Load } from "../api/resource";
import type { Prices } from "../api/types";
import { TEXTOS } from "../content/textos";
import { textFor, useReading } from "../reading";
import { Glyph } from "./Glyph";
import { PriceChart } from "./PriceChart";
import { SectionError, SectionSkeleton } from "./SectionStatus";

type Props = {
  load: Load<Prices>;
  onRetry: () => void;
};

/**
 * O preço ajustado (RF-08): o painel com a frase do preço ajustado (RF-21) e o gráfico da
 * série inteira — os atalhos, o arrasto e a leitura são do `PriceChart`. Sem preço, a frase e
 * a área vazia, como no `ativo-estados.html`.
 */
export function PriceSection({ load, onRetry }: Props) {
  const titleId = useId();
  // O nível muda só a frase do preço ajustado, nunca o gráfico (D-152, V-04).
  const reading = useReading();
  return (
    <section className="ruvor-panel" aria-labelledby={titleId}>
      <div className="ruvor-panel__head">
        <Glyph name="chart-line" />
        <h2 className="ruvor-h3" id={titleId}>
          {TEXTOS["ativo.preco.titulo"]}
        </h2>
      </div>
      <div
        className="ruvor-panel__body"
        aria-busy={load.state === "loading" || undefined}
      >
        {load.state === "loading" && <SectionSkeleton />}
        {load.state === "error" && <SectionError onRetry={onRetry} />}
        {load.state === "ok" && (
          // A frase e o gráfico numa pilha do kit: o espaço entre eles é o da pilha.
          <div className="ruvor-stack">
            <p className="ruvor-note">{textFor("ativo.precoAjustado", reading)}</p>
            <div>
              <PriceChart rows={load.data.results} />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
