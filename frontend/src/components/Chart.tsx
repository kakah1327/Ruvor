import { useEffect, useRef } from "react";
import uPlot from "uplot";

import { onThemeChange } from "../theme";

/**
 * O invólucro do uPlot (RF-22). O uPlot desenha em `<canvas>`, que não lê variável de CSS:
 * cada cor é lida do token, **pelo nome**, em `getComputedStyle(document.documentElement)`,
 * na hora de montar — e a cada troca de tema (`onThemeChange`) o gráfico é destruído e
 * recriado com as cores do tema novo. A seleção e as linhas do cursor, que o uPlot desenha
 * em HTML, ganham cor pelo `app.css`.
 */

/** As cores e a fonte do gráfico, lidas dos tokens. */
export type ChartColors = {
  /** `--ruvor-evidence`: a série do preço e as barras dos dias de alta. */
  evidence: string;
  /** `--ruvor-critical`: as barras dos dias de queda. */
  critical: string;
  /** `--ruvor-surface`: o miolo dos pontos. */
  surface: string;
  /** `--ruvor-ink`: o contorno do ponto do cursor. */
  ink: string;
  /** `--ruvor-text-muted`: os rótulos dos eixos. */
  textMuted: string;
  /** `--ruvor-table-rule`: a grade e as marcas dos eixos. */
  tableRule: string;
  /** `--ruvor-type-micro-size` e `--ruvor-font-sans`: a fonte dos eixos. */
  font: string;
};

function token(styles: CSSStyleDeclaration, name: string): string {
  return styles.getPropertyValue(`--ruvor-${name}`).trim();
}

/** Lê as cores do tema corrente, pelo nome de cada token. */
export function readChartColors(): ChartColors {
  const styles = getComputedStyle(document.documentElement);
  return {
    evidence: token(styles, "evidence"),
    critical: token(styles, "critical"),
    surface: token(styles, "surface"),
    ink: token(styles, "ink"),
    textMuted: token(styles, "text-muted"),
    tableRule: token(styles, "table-rule"),
    font: `${token(styles, "type-micro-size")} ${token(styles, "font-sans")}`,
  };
}

/** Um eixo nas cores do tema: rótulos em `text-muted`, grade e marcas em `table-rule`. */
export function chartAxis(colors: ChartColors, extra: uPlot.Axis = {}): uPlot.Axis {
  return {
    stroke: colors.textMuted,
    grid: { stroke: colors.tableRule, width: 1 },
    ticks: { stroke: colors.tableRule, width: 1 },
    font: colors.font,
    ...extra,
  };
}

/** O ponto do cursor: contorno em `ink`, miolo em `surface`. */
export function cursorPoints(colors: ChartColors, size: number): uPlot.Cursor.Points {
  return { stroke: colors.ink, fill: colors.surface, size };
}

/** O que um gráfico entrega ao invólucro: as opções (sem o tamanho), o dado, e o que fazer
 * com o gráfico recém-criado. */
export type ChartSpec = {
  options: Omit<uPlot.Options, "width" | "height">;
  data: uPlot.AlignedData;
  init?: (chart: uPlot) => void;
};

type ChartProps = {
  /** Altura do gráfico em pixels; a largura é a do contêiner. */
  height: number;
  /** A alternativa em texto: o resumo, vindo de `TEXTOS`. */
  label: string;
  /**
   * Monta as opções a partir das cores. O gráfico é recriado quando a função muda — quem
   * usa a memoriza sobre o dado —, e a cada troca de tema.
   */
  build: (colors: ChartColors) => ChartSpec;
};

/** A área do gráfico: cria o uPlot, acompanha a largura e o recria na troca de tema. */
export function Chart({ height, label, build }: ChartProps) {
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const target = box.current;
    if (target === null) return;
    let chart: uPlot | null = null;

    const create = (): void => {
      chart?.destroy();
      target.replaceChildren();
      const { options, data, init } = build(readChartColors());
      chart = new uPlot(
        { ...options, width: target.clientWidth, height },
        data,
        target,
      );
      init?.(chart);
    };

    create();
    const stopTheme = onThemeChange(create);
    const resize =
      typeof ResizeObserver === "function"
        ? new ResizeObserver(() =>
            chart?.setSize({ width: target.clientWidth, height }),
          )
        : null;
    resize?.observe(target);

    return () => {
      stopTheme();
      resize?.disconnect();
      chart?.destroy();
      chart = null;
    };
  }, [build, height]);

  return <div ref={box} className="ruvor-chart" role="img" aria-label={label} />;
}
