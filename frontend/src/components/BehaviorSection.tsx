import { type ReactNode, useId } from "react";

import type { Load } from "../api/resource";
import type { Metric, Metrics } from "../api/types";
import { TEXTOS } from "../content/textos";
import {
  formatCurrency,
  formatDate,
  formatDecimal,
  formatInteger,
  formatPercent,
  formatSignedPercent,
  toNumber,
  typographicMinus,
} from "../format/numbers";
import { textFor, useReading } from "../reading";
import { Collapsible } from "./Collapsible";
import { Glyph } from "./Glyph";
import { ReturnsHistogram } from "./ReturnsHistogram";
import { SectionError, SectionSkeleton } from "./SectionStatus";

/**
 * O índice de referência do beta e da correlação — `IBOV_TICKER` em
 * `backend/apps/analytics/metrics.py`. Nele, os dois são nulos por identidade, não por falta
 * (RF-10; RF-08 do M1.3).
 */
const BENCHMARK_TICKER = "IBOV";

/** Os retornos por janela, na ordem do bloco; `null` é o do ano, que não tem janela fixa. */
const RETURNS = [
  ["return_1m", 1],
  ["return_3m", 3],
  ["return_6m", 6],
  ["return_12m", 12],
  ["return_36m", 36],
  ["return_60m", 60],
  ["return_120m", 120],
  ["return_ytd", null],
] as const;

/** Os campos com rótulo, os que viram número em destaque (RF-10). */
type StatField =
  | (typeof RETURNS)[number][0]
  | "volatility_12m"
  | "volatility_60m"
  | "max_drawdown"
  | "max_drawdown_recovery_sessions"
  | "beta_60m"
  | "correlation_60m"
  | "skewness"
  | "excess_kurtosis"
  | "dividends_12m"
  | "dividend_payments_12m"
  | "dividend_yield_12m"
  | "avg_volume_21d"
  | "avg_volume_252d";

/** Os campos decimais (string na API); as duas contagens de pregões e pagamentos são número. */
type DecField = Exclude<
  StatField,
  "max_drawdown_recovery_sessions" | "dividend_payments_12m"
>;

/** O número e a frase junto dele (RF-21). Nulo mostra "—" e, quando se sabe, o porquê. */
function Stat({
  field,
  value,
  phrase,
}: {
  field: StatField;
  value: string;
  phrase: string | null;
}) {
  return (
    <div className="ruvor-stat" data-field={field}>
      <span className="ruvor-stat__label">
        {TEXTOS[`comportamento.rotulo.${field}`]}
      </span>
      <span className="ruvor-stat__value ruvor-num">{value}</span>
      {phrase !== null && phrase !== "" && <p className="ruvor-note">{phrase}</p>}
    </div>
  );
}

function Block({
  title,
  note = null,
  wide = false,
  children,
}: {
  title: string;
  note?: string | null;
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <section className={wide ? "ruvor-panel ruvor-blocks__wide" : "ruvor-panel"}>
      <div className="ruvor-panel__head">
        <h3 className="ruvor-h3">{title}</h3>
      </div>
      <div className="ruvor-panel__body">
        {children}
        {note !== null && <p className="ruvor-note ruvor-panel__note">{note}</p>}
      </div>
    </section>
  );
}

const NULL = "—";

/** Um valor sem unidade, com o menos tipográfico: −0,05. */
function signedDecimal(value: number): string {
  return typographicMinus(formatDecimal(value, 2));
}

function Blocks({ metric, ticker }: { metric: Metric; ticker: string }) {
  // A frase de cada número da lista fechada pelo nível (RF-05 do M2.3): a avançada substitui a
  // iniciante, com os mesmos argumentos. O nulo, o rótulo e a unidade não mudam com o nível.
  const reading = useReading();
  // Nulo continua nulo: `toNumber`, nunca `Number`, que faria do nulo um zero.
  const num = (field: DecField): number | null => toNumber(metric[field]);
  const isBenchmark = ticker === BENCHMARK_TICKER;
  const hundred = (r: number) => formatCurrency(100 * (1 + r));

  const returns = RETURNS.map(([field, months]) => {
    const r = num(field);
    return r === null ? (
      <Stat
        key={field}
        field={field}
        value={NULL}
        phrase={months === null ? null : TEXTOS["comportamento.nulo.janela"](months)}
      />
    ) : (
      <Stat
        key={field}
        field={field}
        value={formatSignedPercent(r, 1)}
        phrase={textFor(`comportamento.${field}`, reading)(hundred(r))}
      />
    );
  });

  const volatility = (["volatility_12m", "volatility_60m"] as const).map((field) => {
    const v = num(field);
    return (
      <Stat
        key={field}
        field={field}
        value={v === null ? NULL : formatPercent(v, 1)}
        phrase={
          v === null
            ? TEXTOS["comportamento.nulo.janela"](field === "volatility_12m" ? 12 : 60)
            : textFor(`comportamento.${field}`, reading)(formatPercent(v, 1))
        }
      />
    );
  });

  // A maior queda: as datas e a volta entram na frase (RF-21).
  const drawdown = num("max_drawdown");
  const peak = metric.max_drawdown_peak_date;
  const trough = metric.max_drawdown_trough_date;
  const recovery = metric.max_drawdown_recovery_date;
  const sessions = metric.max_drawdown_recovery_sessions;
  const drawdownPhrase =
    drawdown === null || peak === null || trough === null
      ? null
      : textFor("comportamento.max_drawdown", reading)(
          formatPercent(Math.abs(drawdown), 1),
          formatDate(peak),
          formatDate(trough),
          formatDate(metric.first_price_date),
          recovery === null ? null : formatDate(recovery),
        );
  const sessionsPhrase =
    sessions !== null
      ? textFor(
          "comportamento.max_drawdown_recovery_sessions",
          reading,
        )(formatDecimal(sessions / 252, 1))
      : drawdown !== null
        ? TEXTOS["comportamento.nulo.naoRecuperou"]
        : null;

  // O beta e a correlação: no próprio Ibovespa, o nulo é identidade.
  const beta = num("beta_60m");
  const correlation = num("correlation_60m");
  const benchmarkNull = isBenchmark
    ? TEXTOS["comportamento.nulo.referencia"]
    : TEXTOS["comportamento.nulo.janela"](60);

  const skewness = num("skewness");
  const kurtosis = num("excess_kurtosis");

  const dividends = num("dividends_12m");
  const yieldValue = num("dividend_yield_12m");

  const volume = (["avg_volume_21d", "avg_volume_252d"] as const).map((field) => {
    const v = num(field);
    return (
      <Stat
        key={field}
        field={field}
        value={
          v === null
            ? NULL
            : TEXTOS["comportamento.unidade.volume"](formatDecimal(v / 1e6, 1))
        }
        phrase={
          v === null
            ? TEXTOS["comportamento.nulo.pregoes"](
                field === "avg_volume_21d" ? 21 : 252,
              )
            : textFor(`comportamento.${field}`, reading)
        }
      />
    );
  });

  const observations = metric.statistical_observations;

  return (
    <div className="ruvor-blocks">
      <Block
        title={TEXTOS["comportamento.bloco.retornos"]}
        note={TEXTOS["comportamento.nota.retornos"]}
        wide
      >
        <div className="ruvor-stats">{returns}</div>
      </Block>

      <Block title={TEXTOS["comportamento.bloco.volatilidade"]}>
        <div className="ruvor-stats">{volatility}</div>
      </Block>

      <Block title={TEXTOS["comportamento.bloco.queda"]}>
        <div className="ruvor-stats">
          <Stat
            field="max_drawdown"
            value={
              drawdown === null ? NULL : typographicMinus(formatPercent(drawdown, 1))
            }
            phrase={drawdownPhrase}
          />
          <Stat
            field="max_drawdown_recovery_sessions"
            value={sessions === null ? NULL : formatInteger(sessions)}
            phrase={sessionsPhrase}
          />
        </div>
      </Block>

      <Block
        title={TEXTOS["comportamento.bloco.ibov"]}
        note={
          metric.benchmark_observations === null
            ? null
            : TEXTOS["comportamento.nota.ibov"](
                formatInteger(metric.benchmark_observations),
              )
        }
      >
        <div className="ruvor-stats">
          <Stat
            field="beta_60m"
            value={beta === null ? NULL : signedDecimal(beta)}
            phrase={
              beta === null
                ? benchmarkNull
                : textFor("comportamento.beta_60m", reading)(
                    `${formatDecimal(Math.abs(beta), 2)}%`,
                    beta < 0,
                  )
            }
          />
          <Stat
            field="correlation_60m"
            value={correlation === null ? NULL : signedDecimal(correlation)}
            phrase={
              correlation === null
                ? benchmarkNull
                : textFor(
                    "comportamento.correlation_60m",
                    reading,
                  )(signedDecimal(correlation))
            }
          />
        </div>
      </Block>

      <Block title={TEXTOS["comportamento.bloco.proventos"]}>
        <div className="ruvor-stats">
          <Stat
            field="dividends_12m"
            value={dividends === null ? NULL : formatCurrency(dividends)}
            phrase={textFor("comportamento.dividends_12m", reading)}
          />
          <Stat
            field="dividend_payments_12m"
            value={formatInteger(metric.dividend_payments_12m)}
            phrase={textFor("comportamento.dividend_payments_12m", reading)}
          />
          <Stat
            field="dividend_yield_12m"
            value={yieldValue === null ? NULL : formatPercent(yieldValue, 1)}
            phrase={
              yieldValue === null
                ? null
                : textFor("comportamento.dividend_yield_12m", reading)(
                    formatDate(metric.as_of_date),
                    formatCurrency(100 * yieldValue),
                  )
            }
          />
        </div>
      </Block>

      <Block
        title={TEXTOS["comportamento.bloco.distribuicao"]}
        note={
          observations === null
            ? null
            : TEXTOS["comportamento.nota.distribuicao"](formatInteger(observations))
        }
        wide
      >
        <div className="ruvor-stack">
          {observations !== null && (
            <p className="ruvor-note">{textFor("comportamento.histograma", reading)}</p>
          )}
          <div>
            <ReturnsHistogram bins={metric.histogram} observations={observations} />
          </div>
          {/* A assimetria e a curtose, recolhidas na iniciante (RF-06); o histograma fica
              aberto nos dois níveis. Com a série curta, o recolhível continua, com os nulos. */}
          <Collapsible name="moments" label={TEXTOS["comportamento.momentos.abrir"]}>
            <div className="ruvor-stats">
              <Stat
                field="skewness"
                value={skewness === null ? NULL : signedDecimal(skewness)}
                phrase={
                  skewness === null
                    ? TEXTOS["comportamento.nulo.janela"](60)
                    : textFor("comportamento.skewness", reading)(
                        signedDecimal(skewness),
                        Math.sign(skewness),
                      )
                }
              />
              <Stat
                field="excess_kurtosis"
                value={kurtosis === null ? NULL : signedDecimal(kurtosis)}
                phrase={
                  kurtosis === null
                    ? TEXTOS["comportamento.nulo.janela"](60)
                    : textFor("comportamento.excess_kurtosis", reading)(
                        signedDecimal(kurtosis),
                        Math.sign(kurtosis),
                      )
                }
              />
            </div>
          </Collapsible>
        </div>
      </Block>

      <Block title={TEXTOS["comportamento.bloco.volume"]} wide>
        <div className="ruvor-stats">{volume}</div>
      </Block>
    </div>
  );
}

type Props = {
  load: Load<Metrics>;
  ticker: string;
  onRetry: () => void;
};

/**
 * O comportamento (RF-10, RF-11; camada 2): a última linha de `/metrics` em blocos, cada
 * número com a sua frase; o nulo é "—" com o porquê, nunca zero. `metric: null` aponta para
 * a seção de risco, onde está o convite — a cadeia sob demanda calcula as métricas junto.
 */
export function BehaviorSection({ load, ticker, onRetry }: Props) {
  const titleId = useId();
  const metric = load.state === "ok" ? load.data.metric : null;

  let body: ReactNode;
  if (load.state === "loading") {
    body = <SectionSkeleton />;
  } else if (load.state === "error") {
    body = <SectionError onRetry={onRetry} />;
  } else if (metric === null) {
    body = (
      <div className="ruvor-panel">
        <div className="ruvor-panel__body ruvor-state">
          <span className="ruvor-icon ruvor-icon--evidence">
            <Glyph name="info" weight="duotone" />
          </span>
          <div className="ruvor-state__body">
            <p className="ruvor-state__title">{TEXTOS["comportamento.naoCalculado"]}</p>
            <p className="ruvor-state__text">
              {TEXTOS["comportamento.naoCalculado.nota"]}
            </p>
            <div className="ruvor-state__actions">
              <a className="ruvor-btn" href="#risco">
                <Glyph name="chart-line" />
                <span>{TEXTOS["comportamento.irParaRisco"]}</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  } else {
    body = <Blocks metric={metric} ticker={ticker} />;
  }

  return (
    <section className="ruvor-stack" aria-labelledby={titleId}>
      <div className="ruvor-section-head">
        <div>
          <p className="ruvor-eyebrow">{TEXTOS["comportamento.sobrancelha"]}</p>
          <h2 className="ruvor-h2" id={titleId}>
            {TEXTOS["comportamento.titulo"]}
          </h2>
        </div>
        {metric !== null && (
          <span className="ruvor-tag ruvor-tag--evidence">
            {TEXTOS["comportamento.ate"](formatDate(metric.as_of_date))}
          </span>
        )}
      </div>
      <p className="ruvor-sub">{TEXTOS["comportamento.intro"]}</p>
      <div aria-busy={load.state === "loading" || undefined}>{body}</div>
    </section>
  );
}
