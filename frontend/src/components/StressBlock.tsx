import type { ReactNode } from "react";

import type { StressEpisode } from "../api/types";
import { TEXTOS } from "../content/textos";
import {
  formatCurrency,
  formatDate,
  formatInteger,
  formatPercent,
  formatSignedPercent,
  toNumber,
  typographicMinus,
} from "../format/numbers";
import { type Reading, textFor, useReading } from "../reading";

const NULL = "—";

/** As seis medidas, cada uma com rótulo e frase (RF-12): três do ativo e três do índice. */
type Measure =
  | "period_return"
  | "drawdown"
  | "recovery_sessions"
  | "benchmark_period_return"
  | "benchmark_drawdown"
  | "benchmark_recovery_sessions";

/** O número com o rótulo e a frase, como o `.ruvor-stat` do resto da seção. */
function Cell({
  measure,
  label = TEXTOS[`comportamento.estresse.rotulo.${measure}`],
  value,
  phrase,
  className = "ruvor-stat",
  benchmarkNone = false,
}: {
  measure: Measure;
  label?: string;
  value: string;
  phrase: string;
  className?: string;
  benchmarkNone?: boolean;
}) {
  return (
    <div
      className={className}
      data-field={measure}
      data-benchmark={benchmarkNone ? "none" : undefined}
    >
      <span className="ruvor-stat__label">{label}</span>
      <span className="ruvor-stat__value ruvor-num">{value}</span>
      <p className="ruvor-note">{phrase}</p>
    </div>
  );
}

const hundred = (r: number) => formatCurrency(100 * (1 + r));

/** O lado do ativo: os três números, ou uma célula só com o motivo, nas três linhas (RF-05). */
function assetCells(e: StressEpisode, reading: Reading): ReactNode[] {
  const r = toNumber(e.period_return);
  const d = toNumber(e.drawdown);
  if (
    e.missing !== null ||
    r === null ||
    d === null ||
    e.window_start_date === null ||
    e.window_end_date === null
  ) {
    return [
      <Cell
        key="asset"
        measure="period_return"
        label={TEXTOS["comportamento.estresse.semDado.rotulo"]}
        value={NULL}
        phrase={
          e.missing === null
            ? TEXTOS["comportamento.estresse.naoCalculado"]
            : TEXTOS[`comportamento.estresse.semDado.${e.missing}`]
        }
        className="ruvor-stat ruvor-pair__span"
      />,
    ];
  }
  const ret = (
    <Cell
      key="period_return"
      measure="period_return"
      value={formatSignedPercent(r, 1)}
      phrase={textFor("comportamento.estresse.period_return", reading)(
        hundred(r),
        formatDate(e.window_start_date),
        formatDate(e.window_end_date),
      )}
    />
  );
  // A queda zero (RF-04): o topo e o fundo em P0, e nada a recuperar.
  if (d === 0) {
    return [
      ret,
      <Cell
        key="drawdown"
        measure="drawdown"
        value={formatPercent(0, 1)}
        phrase={TEXTOS["comportamento.estresse.semQueda"]}
      />,
      <Cell
        key="recovery_sessions"
        measure="recovery_sessions"
        value={NULL}
        phrase={TEXTOS["comportamento.estresse.nadaARecuperar"]}
      />,
    ];
  }
  // A queda que começa no primeiro pregão da janela e termina no último coincide com o retorno.
  const whole =
    e.drawdown_peak_date === e.window_start_date &&
    e.drawdown_trough_date === e.window_end_date;
  return [
    ret,
    <Cell
      key="drawdown"
      measure="drawdown"
      value={typographicMinus(formatPercent(d, 1))}
      phrase={textFor("comportamento.estresse.drawdown", reading)(
        formatPercent(Math.abs(d), 1),
        e.drawdown_peak_date === null ? NULL : formatDate(e.drawdown_peak_date),
        e.drawdown_trough_date === null ? NULL : formatDate(e.drawdown_trough_date),
        whole,
      )}
    />,
    e.recovery_sessions === null || e.recovery_date === null ? (
      <Cell
        key="recovery_sessions"
        measure="recovery_sessions"
        value={NULL}
        phrase={TEXTOS["comportamento.nulo.naoRecuperou"]}
      />
    ) : (
      <Cell
        key="recovery_sessions"
        measure="recovery_sessions"
        value={formatInteger(e.recovery_sessions)}
        phrase={textFor(
          "comportamento.estresse.recovery_sessions",
          reading,
        )(formatDate(e.recovery_date))}
      />
    ),
  ];
}

/**
 * O lado do índice: os três números no mesmo recorte, mostrados também com o ativo sem dado
 * (RF-05); nulo, uma célula só — no próprio IBOV, a referência.
 */
function benchmarkCells(
  e: StressEpisode,
  isBenchmark: boolean,
  reading: Reading,
): ReactNode[] {
  const r = toNumber(e.benchmark_period_return);
  const d = toNumber(e.benchmark_drawdown);
  if (r === null || d === null) {
    return [
      <Cell
        key="benchmark"
        measure="benchmark_period_return"
        value={NULL}
        phrase={
          isBenchmark
            ? TEXTOS["comportamento.nulo.referencia"]
            : TEXTOS["comportamento.estresse.semIbov"]
        }
        className="ruvor-stat ruvor-pair__span ruvor-pair__span--bench"
        benchmarkNone
      />,
    ];
  }
  const ret = (
    <Cell
      key="benchmark_period_return"
      measure="benchmark_period_return"
      value={formatSignedPercent(r, 1)}
      phrase={textFor(
        "comportamento.estresse.benchmark_period_return",
        reading,
      )(hundred(r))}
    />
  );
  if (d === 0) {
    return [
      ret,
      <Cell
        key="benchmark_drawdown"
        measure="benchmark_drawdown"
        value={formatPercent(0, 1)}
        phrase={TEXTOS["comportamento.estresse.semQueda"]}
      />,
      <Cell
        key="benchmark_recovery_sessions"
        measure="benchmark_recovery_sessions"
        value={NULL}
        phrase={TEXTOS["comportamento.estresse.nadaARecuperar"]}
      />,
    ];
  }
  const sessions = e.benchmark_recovery_sessions;
  return [
    ret,
    <Cell
      key="benchmark_drawdown"
      measure="benchmark_drawdown"
      value={typographicMinus(formatPercent(d, 1))}
      phrase={textFor("comportamento.estresse.benchmark_drawdown", reading)(
        formatPercent(Math.abs(d), 1),
        r === d,
      )}
    />,
    sessions === null ? (
      <Cell
        key="benchmark_recovery_sessions"
        measure="benchmark_recovery_sessions"
        value={NULL}
        phrase={TEXTOS["comportamento.nulo.naoRecuperou"]}
      />
    ) : (
      <Cell
        key="benchmark_recovery_sessions"
        measure="benchmark_recovery_sessions"
        value={formatInteger(sessions)}
        phrase={textFor(
          "comportamento.estresse.benchmark_recovery_sessions",
          reading,
        )(TEXTOS["comportamento.estresse.pregoes"](formatInteger(sessions)))}
      />
    ),
  ];
}

/**
 * Na grade de duas colunas, a ordem é ativo, índice, ativo, índice — em uma coluna, cada
 * medida do ativo vem seguida da do índice. Com um lado numa célula só, ele vai primeiro.
 */
function interleave(asset: ReactNode[], benchmark: ReactNode[]): ReactNode[] {
  if (asset.length === 1 || benchmark.length === 1) return [...asset, ...benchmark];
  return asset.flatMap((cell, i) => [cell, benchmark[i]]);
}

function Episode({
  episode,
  isBenchmark,
  reading,
}: {
  episode: StressEpisode;
  isBenchmark: boolean;
  reading: Reading;
}) {
  const dates = TEXTOS["comportamento.estresse.recorte"](
    formatDate(episode.start_date),
    formatDate(episode.end_date),
  );
  // As datas de P0 e Pn só quando diferem do recorte de calendário (RF-12).
  const differ =
    episode.window_start_date !== null &&
    episode.window_end_date !== null &&
    (episode.window_start_date !== episode.start_date ||
      episode.window_end_date !== episode.end_date);
  const window =
    differ && episode.window_start_date !== null && episode.window_end_date !== null
      ? TEXTOS["comportamento.estresse.janela"](
          formatDate(episode.window_start_date),
          formatDate(episode.window_end_date),
        )
      : null;
  return (
    <article
      className="ruvor-episode"
      data-episode={episode.episode}
      data-missing={episode.missing ?? undefined}
    >
      <div className="ruvor-episode__head">
        <h4 className="ruvor-episode__name">
          {TEXTOS[`comportamento.estresse.episodio.${episode.episode}`]}
        </h4>
        <p className="ruvor-episode__dates">
          {window === null ? dates : `${dates} · ${window}`}
        </p>
      </div>
      <div className="ruvor-pair">
        {interleave(
          assetCells(episode, reading),
          benchmarkCells(episode, isBenchmark, reading),
        )}
      </div>
    </article>
  );
}

type Props = {
  stress: StressEpisode[];
  /** O ativo é o próprio índice: o lado do índice nulo é a referência, não falta. */
  isBenchmark: boolean;
};

/**
 * Os momentos de estresse (RF-12 a RF-15 do M3.3): o bloco da seção Comportamento, logo depois
 * de "Maior queda", com cada episódio da D-147 — o ativo e o Ibovespa lado a lado, medida a
 * medida. `stress: []` é a linha de métrica gravada antes do bloco: diz que entra no próximo
 * cálculo, sem nota.
 */
export function StressBlock({ stress, isBenchmark }: Props) {
  const reading = useReading();
  return (
    <section className="ruvor-panel ruvor-blocks__wide" data-block="stress">
      <div className="ruvor-panel__head">
        <h3 className="ruvor-h3">{TEXTOS["comportamento.bloco.estresse"]}</h3>
      </div>
      <div className="ruvor-panel__body">
        {stress.length === 0 ? (
          <p className="ruvor-muted">{TEXTOS["comportamento.estresse.naoCalculado"]}</p>
        ) : (
          <>
            <div className="ruvor-episodes">
              {stress.map((episode) => (
                <Episode
                  key={episode.episode}
                  episode={episode}
                  isBenchmark={isBenchmark}
                  reading={reading}
                />
              ))}
            </div>
            <p className="ruvor-note ruvor-panel__note">
              {TEXTOS["comportamento.nota.estresse"]}
            </p>
          </>
        )}
      </div>
    </section>
  );
}
