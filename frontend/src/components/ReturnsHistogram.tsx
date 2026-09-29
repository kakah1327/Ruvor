import { useCallback, useMemo } from "react";
import uPlot from "uplot";

import type { HistogramBin } from "../api/types";
import { TEXTOS } from "../content/textos";
import {
  formatInteger,
  formatPercent,
  formatSignedPercent,
  typographicMinus,
} from "../format/numbers";
import {
  Chart,
  type ChartColors,
  type ChartSpec,
  chartAxis,
  cursorPoints,
} from "./Chart";

const HEIGHT = 220;

// As marcas do eixo: as bordas de −10%, −5%, 0, +5% e +10% entre os 42 baldes — o 0 e o 41
// são as pontas abertas, e cada um dos 40 do meio tem 0,5 ponto.
const TICKS = [0.5, 10.5, 20.5, 30.5, 40.5];
const TICK_VALUES = [-0.1, -0.05, 0, 0.05, 0.1];

/** A faixa de um balde, em texto: a ponta aberta pelo nome, o resto "de x a y". */
export function binRange(bin: HistogramBin): string {
  if (bin.lower_bound === null) return TEXTOS["grafico.pontaInferior"];
  if (bin.upper_bound === null) return TEXTOS["grafico.pontaSuperior"];
  return TEXTOS["grafico.faixa"](
    typographicMinus(formatPercent(Number(bin.lower_bound), 1)),
    typographicMinus(formatPercent(Number(bin.upper_bound), 1)),
  );
}

/** O balde dos dias de queda: o limite de cima não passa de zero. */
function isNegative(bin: HistogramBin): boolean {
  return bin.upper_bound !== null && Number(bin.upper_bound) <= 0;
}

type Props = {
  bins: HistogramBin[];
  /** `statistical_observations` da métrica: nulo quando a série é curta demais. */
  observations: number | null;
};

/**
 * O histograma dos retornos diários (RF-11): os 42 baldes, as pontas abertas, os dias de
 * queda em `critical` — duas séries de barras, a negativa e a positiva —, a dica por barra
 * com a faixa e a contagem, a legenda e o resumo em texto. Com a série curta, a frase no
 * lugar do gráfico.
 */
export function ReturnsHistogram({ bins, observations }: Props) {
  const short = observations === null || bins.length === 0;

  const build = useCallback(
    (colors: ChartColors): ChartSpec => {
      const xs = bins.map((b) => b.bin_index);
      const negative = bins.map((b) => (isNegative(b) ? b.count : null));
      const positive = bins.map((b) => (isNegative(b) ? null : b.count));
      const bars = uPlot.paths.bars?.({
        size: [0.86, Number.POSITIVE_INFINITY],
        gap: 1,
      });
      const tip = document.createElement("div");
      tip.className = "ruvor-chart__tip";
      tip.hidden = true;
      tip.setAttribute("aria-hidden", "true");
      return {
        options: {
          legend: { show: false },
          cursor: { points: cursorPoints(colors, 7), drag: { x: false, y: false } },
          scales: {
            x: { time: false, range: [-0.5, bins.length - 0.5] },
            y: { range: (_, __, max) => [0, max * 1.08] },
          },
          axes: [
            chartAxis(colors, {
              splits: () => TICKS,
              values: () => TICK_VALUES.map((v) => formatSignedPercent(v, 0)),
            }),
            chartAxis(colors, {
              size: 48,
              values: (_, splits) => splits.map((v) => formatInteger(v)),
            }),
          ],
          series: [
            {},
            {
              stroke: colors.critical,
              fill: colors.critical,
              paths: bars,
              points: { show: false, stroke: colors.critical, fill: colors.surface },
            },
            {
              stroke: colors.evidence,
              fill: colors.evidence,
              paths: bars,
              points: { show: false, stroke: colors.evidence, fill: colors.surface },
            },
          ],
          hooks: {
            setCursor: [
              (self) => {
                const i = self.cursor.idx;
                const left = self.cursor.left ?? -1;
                if (
                  i === null ||
                  i === undefined ||
                  left < 0 ||
                  bins[i] === undefined
                ) {
                  tip.hidden = true;
                  return;
                }
                tip.textContent = TEXTOS["grafico.dicaBarra"](
                  binRange(bins[i]),
                  bins[i].count,
                );
                tip.style.left = `${self.valToPos(i, "x")}px`;
                tip.style.top = `${self.valToPos(bins[i].count, "y")}px`;
                tip.hidden = false;
              },
            ],
          },
        },
        data: [xs, negative, positive],
        init: (u) => {
          u.over.appendChild(tip);
        },
      };
    },
    [bins],
  );

  const summary = useMemo(() => {
    if (short) return "";
    let top = bins[0];
    for (const b of bins) if (b.count > top.count) top = b;
    return TEXTOS["grafico.resumoHistograma"](
      binRange(top),
      formatInteger(top.count),
      bins[0].count,
      bins[bins.length - 1].count,
    );
  }, [bins, short]);

  if (short) {
    return <p className="ruvor-muted">{TEXTOS["comportamento.histogramaCurto"]}</p>;
  }

  return (
    <>
      <div className="ruvor-chart__bar">
        <div className="ruvor-legend" aria-hidden="true">
          <span>
            <i className="ruvor-legend__swatch ruvor-legend__swatch--critical" />
            {TEXTOS["grafico.legendaQueda"]}
          </span>
          <span>
            <i className="ruvor-legend__swatch ruvor-legend__swatch--evidence" />
            {TEXTOS["grafico.legendaAlta"]}
          </span>
        </div>
      </div>
      <Chart height={HEIGHT} label={summary} build={build} />
      <div className="ruvor-chart__ends" aria-hidden="true">
        <span>← {TEXTOS["grafico.pontaInferior"]}</span>
        <span>{TEXTOS["grafico.pontaSuperior"]} →</span>
      </div>
      <p className="ruvor-note ruvor-chart__summary" aria-hidden="true">
        {summary}
      </p>
    </>
  );
}
