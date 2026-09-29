import { useCallback, useMemo, useRef, useState } from "react";
import uPlot from "uplot";

import type { PriceRow } from "../api/types";
import { TEXTOS } from "../content/textos";
import { formatCurrency, formatCurrencyWhole, formatDate } from "../format/numbers";
import {
  Chart,
  type ChartColors,
  type ChartSpec,
  chartAxis,
  cursorPoints,
} from "./Chart";

const HEIGHT = 260;
const DAY = 86400;
const YEAR = 365.25 * DAY;

/** Os atalhos de período (RF-08); `custom` é a janela escolhida por arrasto. */
type Range = "1" | "5" | "all" | "custom";

const SHORTCUTS = [
  { range: "1", label: "grafico.atalho.1a" },
  { range: "5", label: "grafico.atalho.5a" },
  { range: "all", label: "grafico.atalho.tudo" },
] as const satisfies ReadonlyArray<{ range: Range; label: keyof typeof TEXTOS }>;

/** A data da API como instante UTC em segundos, a unidade do eixo de tempo do uPlot. */
function toSeconds(date: string): number {
  return Date.parse(`${date}T00:00:00Z`) / 1000;
}

/** O rótulo do eixo de tempo: o ano na janela longa, mês e ano na curta. */
function timeLabels(self: uPlot, splits: number[]): string[] {
  const { min = 0, max = 0 } = self.scales.x;
  const long = (max - min) / DAY > 3 * 365;
  return splits.map((s) => {
    const d = new Date(s * 1000);
    const year = String(d.getUTCFullYear());
    return long ? year : `${String(d.getUTCMonth() + 1).padStart(2, "0")}/${year}`;
  });
}

/**
 * O preço ajustado (RF-08): a linha no uPlot, os atalhos 1 ano, 5 anos e tudo, a seleção
 * por arrasto (duplo clique volta a tudo), a leitura de data e preço sob o cursor e o resumo
 * em texto. Sem preço, a área vazia com a frase.
 */
export function PriceChart({ rows }: { rows: PriceRow[] }) {
  const xs = useMemo(() => rows.map((r) => toSeconds(r.date)), [rows]);
  const ys = useMemo(() => rows.map((r) => Number(r.adj_close)), [rows]);
  const last = rows.length - 1;

  const [range, setRange] = useState<Range>("all");
  const [cursor, setCursor] = useState<number | null>(null);
  // O gráfico vivo e o período: os ganchos do uPlot os leem sem recriar o gráfico.
  const chart = useRef<uPlot | null>(null);
  const rangeRef = useRef<Range>("all");
  const customRef = useRef<{ min: number; max: number } | null>(null);

  const choose = useCallback(
    (next: Range) => {
      rangeRef.current = next;
      setRange(next);
      const u = chart.current;
      if (u === null || last < 0) return;
      if (next === "all") u.setScale("x", { min: xs[0], max: xs[last] });
      else if (next !== "custom")
        u.setScale("x", { min: xs[last] - Number(next) * YEAR, max: xs[last] });
    },
    [xs, last],
  );

  const build = useCallback(
    (colors: ChartColors): ChartSpec => ({
      options: {
        legend: { show: false },
        tzDate: (ts) => uPlot.tzDate(new Date(ts * 1000), "Etc/UTC"),
        cursor: { points: cursorPoints(colors, 8), drag: { x: true, y: false } },
        scales: { x: { time: true } },
        axes: [
          chartAxis(colors, { values: timeLabels }),
          chartAxis(colors, {
            size: 64,
            values: (_, splits) => splits.map((v) => formatCurrencyWhole(v)),
          }),
        ],
        series: [
          {},
          {
            stroke: colors.evidence,
            fill: undefined,
            width: 1.5,
            points: { stroke: colors.evidence, fill: colors.surface },
          },
        ],
        hooks: {
          setCursor: [(self) => setCursor(self.cursor.idx ?? null)],
          setSelect: [
            (self) => {
              const { left, width } = self.select;
              if (width <= 0) return;
              customRef.current = {
                min: self.posToVal(left, "x"),
                max: self.posToVal(left + width, "x"),
              };
              rangeRef.current = "custom";
              setRange("custom");
            },
          ],
        },
      },
      data: [xs, ys],
      init: (u) => {
        chart.current = u;
        // Recriado (tema), o gráfico volta ao período que estava.
        const custom = customRef.current;
        if (rangeRef.current === "custom" && custom !== null) u.setScale("x", custom);
        else choose(rangeRef.current);
        u.over.addEventListener("dblclick", () => {
          rangeRef.current = "all";
          setRange("all");
        });
      },
    }),
    [xs, ys, choose],
  );

  if (last < 0) {
    return (
      <div className="ruvor-chart__empty">
        <div>
          <p>{TEXTOS["ativo.preco.vazio"]}</p>
          <p className="ruvor-note">{TEXTOS["ativo.preco.vazio.nota"]}</p>
        </div>
      </div>
    );
  }

  let iMin = 0;
  let iMax = 0;
  ys.forEach((v, i) => {
    if (v < ys[iMin]) iMin = i;
    if (v > ys[iMax]) iMax = i;
  });
  const summary = TEXTOS["grafico.resumoPreco"](
    formatDate(rows[0].date),
    formatDate(rows[last].date),
    formatCurrency(ys[iMin]),
    formatDate(rows[iMin].date),
    formatCurrency(ys[iMax]),
    formatDate(rows[iMax].date),
    formatCurrency(ys[last]),
  );
  const shown = cursor !== null && cursor <= last ? cursor : last;

  return (
    <>
      <div className="ruvor-chart__bar">
        {/* biome-ignore lint/a11y/useSemanticElements: os atalhos são a .ruvor-btn-group do kit, um div com role="group" como no ativo.html aprovado; um fieldset traria margem e largura mínima do navegador que a classe não zera. */}
        <div
          className="ruvor-btn-group"
          role="group"
          aria-label={TEXTOS["grafico.atalhos"]}
        >
          {SHORTCUTS.map(({ range: r, label }) => (
            <button
              key={r}
              className="ruvor-btn"
              type="button"
              aria-pressed={range === r}
              onClick={() => choose(r)}
            >
              {TEXTOS[label]}
            </button>
          ))}
        </div>
        <span className="ruvor-chart__readout ruvor-num" aria-hidden="true">
          {TEXTOS["grafico.dicaPreco"](
            formatDate(rows[shown].date),
            formatCurrency(ys[shown]),
          )}
        </span>
      </div>
      <Chart height={HEIGHT} label={summary} build={build} />
      <p className="ruvor-note ruvor-chart__summary" aria-hidden="true">
        {summary}
      </p>
      <p className="ruvor-note">{TEXTOS["grafico.arrasto"]}</p>
    </>
  );
}
