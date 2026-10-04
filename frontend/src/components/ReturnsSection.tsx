import { type ReactNode, useId } from "react";

import type { Load } from "../api/resource";
import type {
  AssetDetail,
  Prices,
  ReturnResult,
  ReturnRun,
  Returns,
} from "../api/types";
import { type ModeloQueBate, TEXTOS } from "../content/textos";
import {
  formatDate,
  formatDecimal,
  formatInstant,
  formatInteger,
  formatPercent,
  formatSignedPercent,
} from "../format/numbers";
import { type Reading, textFor, useReading } from "../reading";
import { forecastView, returnsState } from "../returns/state";
import { MIN_SESSIONS } from "../risk/config";
import type { AssetLoad, PricesLoad } from "../risk/state";
import { Collapsible } from "./Collapsible";
import { Glyph } from "./Glyph";
import { SectionError, SectionSkeleton } from "./SectionStatus";

/**
 * A seção do retorno (M5.1, RF-16 a RF-22), depois do laboratório e antes dos Fundamentos: a
 * validação dos dois modelos de retorno contra a referência de retorno zero, nas duas leituras
 * — o `retorno.html` aprovado. Os estados são os de `returns/state.ts`, na ordem do RF-16; os
 * modelos, na ordem de `model_name` que a API entrega, sem mérito. A previsão do próximo pregão
 * só sai dentro da linha do modelo, depois do veredito e do histórico, e só com
 * `forecastView(...).kind === "show"` (RF-18).
 */

/** Os instantes no fuso da B3, como a trilha do risco. */
const TIME_ZONE = "America/Sao_Paulo";

// ---------------------------------------------------------------- formatação

/** O nulo (o DM e o CW com variância nula, RF-08) sai como "—", nunca como número. */
const NULO = "—";

function formatPValue(value: string | null): string {
  if (value === null) return NULO;
  const p = Number(value);
  return p < 0.001 ? "< 0,001" : formatDecimal(p, 3);
}

/** O erro quadrático em notação científica, com vírgula e o menos tipográfico: "3,402e−4". */
function formatScientific(value: string): string {
  return Number(value).toExponential(3).replace(".", ",").replace(/-/g, "−");
}

/** A previsão (log-retorno de 1 dia) em %, duas casas, com sinal e o menos tipográfico. */
function formatForecast(value: string): string {
  return formatSignedPercent(Number(value), 2);
}

/** O erro relativo em valor absoluto, duas casas: o sinal vai à frase ("menos" ou "mais"). */
function r2Abs(r: ReturnResult): string {
  return formatPercent(Math.abs(Number(r.r2_os)), 2);
}

/** O erro relativo com sinal e o menos tipográfico; o que arredonda a zero, sem sinal (L7). */
function r2Signed(r: ReturnResult): string {
  const abs = r2Abs(r);
  if (abs === formatPercent(0, 2)) return abs;
  return `${Number(r.r2_os) > 0 ? "+" : "−"}${abs}`;
}

function instant(value: string): string {
  const [data = "", hora = ""] = formatInstant(value, TIME_ZONE).split(" ");
  return TEXTOS["risco.trilha.instante"](data, hora);
}

// ---------------------------------------------------------------- leitura dos resultados

const failed = (r: ReturnResult): boolean => r.error !== "";

/** O nome do modelo; o `model_name` fora da lista sai como veio (RF-15: texto livre). */
function modelName(name: string): string {
  const text = (TEXTOS as Record<string, unknown>)[`retorno.modelo.${name}`];
  return typeof text === "string" ? text : name;
}

function sourceName(source: string): string {
  const text = (TEXTOS as Record<string, unknown>)[`risco.trilha.fonte.${source}`];
  return typeof text === "string" ? text : source;
}

// ---------------------------------------------------------------- pedaços

function Note({ phrase, children }: { phrase?: string; children: ReactNode }) {
  return (
    <p className="ruvor-note" data-phrase={phrase}>
      {children}
    </p>
  );
}

function VerdictTag({ result }: { result: ReturnResult }) {
  if (failed(result)) {
    return (
      <span className="ruvor-tag ruvor-tag--review" data-verdict="error">
        {TEXTOS["retorno.tag.erro"]}
      </span>
    );
  }
  // O veredito que bate é a tag --evidence, nunca a --validated (portão da T9, D-192).
  return result.beats_reference === true ? (
    <span className="ruvor-tag ruvor-tag--evidence" data-verdict="beats">
      {TEXTOS["retorno.tag.bate"]}
    </span>
  ) : (
    <span className="ruvor-tag ruvor-tag--neutral" data-verdict="not_beats">
      {TEXTOS["retorno.tag.naoBate"]}
    </span>
  );
}

/** O painel de estado, como o do risco e o do laboratório: o sinal, o título, a frase, a ação. */
function StatePanel({
  tone = "evidence",
  title,
  text,
  actions,
}: {
  tone?: "evidence" | "review";
  title: string;
  text: string;
  actions?: ReactNode;
}) {
  return (
    <div className="ruvor-panel">
      <div className="ruvor-panel__body ruvor-state">
        <span className={`ruvor-icon ruvor-icon--${tone}`}>
          <Glyph name={tone === "review" ? "warning" : "info"} weight="duotone" />
        </span>
        <div className="ruvor-state__body">
          <p className="ruvor-state__title">{title}</p>
          <p className="ruvor-state__text">{text}</p>
          {actions !== undefined && (
            <div className="ruvor-state__actions">{actions}</div>
          )}
        </div>
      </div>
    </div>
  );
}

function RetryButton({ onRetry }: { onRetry: () => void }) {
  return (
    <button className="ruvor-btn" type="button" onClick={onRetry}>
      <Glyph name="arrows-clockwise" />
      <span>{TEXTOS["ativo.tentarDeNovo"]}</span>
    </button>
  );
}

/** O aviso do RF-19: sempre aberto, nas duas leituras, de R3 a R8. */
function Aviso() {
  return (
    <div className="ruvor-callout ruvor-returns-callout" data-aviso="retorno">
      <Glyph name="info" />
      <p>{TEXTOS["retorno.aviso"]}</p>
    </div>
  );
}

function TestRow({
  label,
  value,
  phrase,
  phraseKey,
}: {
  label: string;
  value: string;
  phrase?: string;
  phraseKey?: string;
}) {
  return (
    <div className="ruvor-test">
      <dt>{label}</dt>
      <dd>
        <span className="ruvor-num">{value}</span>
      </dd>
      {phrase !== undefined && <Note phrase={phraseKey}>{phrase}</Note>}
    </div>
  );
}

// ---------------------------------------------------------------- a previsão (RF-18)

function Forecast({
  result,
  asset,
  today,
  reading,
}: {
  result: ReturnResult;
  asset: AssetLoad;
  today: string;
  reading: Reading;
}) {
  const view = forecastView(asset, result, today);
  if (view.kind === "none" || view.kind === "pending_identity") return null;
  if (view.kind === "inactive") {
    return (
      <div className="ruvor-returns-forecast" data-forecast="inactive">
        <Note>{TEXTOS["retorno.previsao.inativo"]}</Note>
      </div>
    );
  }
  if (view.kind === "past") {
    return (
      <div className="ruvor-returns-forecast" data-forecast="past">
        <Note>{TEXTOS["retorno.previsao.passada"](formatDate(view.date))}</Note>
      </div>
    );
  }
  // `show`: o `forecastView` já garantiu o número e a data.
  const data = formatDate(result.next_forecast_date ?? "");
  const valor = formatForecast(result.next_forecast ?? "0");
  return (
    <div className="ruvor-returns-forecast" data-forecast="show">
      <p className="ruvor-returns-forecast__line">
        <span>{TEXTOS["retorno.previsao.rotulo"](data)}</span>
        <span className="ruvor-num" data-value="forecast">
          {valor}
        </span>
        <span>{TEXTOS["retorno.previsao.referencia"]}</span>
      </p>
      <Note phrase="previsao">
        {textFor("retorno.previsao", reading)(
          valor,
          data,
          result.beats_reference === true,
        )}
      </Note>
    </div>
  );
}

// ---------------------------------------------------------------- um bloco por modelo

function ModelBlock({
  result,
  asset,
  today,
  reading,
}: {
  result: ReturnResult;
  asset: AssetLoad;
  today: string;
  reading: Reading;
}) {
  const head = (
    <div className="ruvor-returns-model__head">
      <h3 className="ruvor-h3">{modelName(result.model_name)}</h3>
      <VerdictTag result={result} />
    </div>
  );
  if (failed(result)) {
    return (
      <section
        className="ruvor-returns-model"
        data-model={result.model_name}
        data-error="true"
      >
        {head}
        <Note phrase="erroModelo">{TEXTOS["retorno.erroModelo"](result.error)}</Note>
      </section>
    );
  }
  const menos = Number(result.r2_os) > 0;
  const acerto =
    result.hit_rate === null ? NULO : formatPercent(Number(result.hit_rate), 1);
  const alta =
    result.up_share === null ? NULO : formatPercent(Number(result.up_share), 1);
  const dm = formatPValue(result.dm_p_value);
  return (
    <section className="ruvor-returns-model" data-model={result.model_name}>
      {head}
      <dl className="ruvor-tests">
        <TestRow
          label={TEXTOS["retorno.rotulo.r2"]}
          value={r2Signed(result)}
          phrase={textFor("retorno.r2_os", reading)(r2Abs(result), menos)}
          phraseKey="r2_os"
        />
        <TestRow
          label={TEXTOS["retorno.rotulo.acerto"]}
          value={TEXTOS["retorno.acerto.valor"](acerto, alta)}
          phrase={textFor("retorno.acerto", reading)(acerto, alta)}
          phraseKey="acerto"
        />
        <TestRow
          label={TEXTOS["retorno.rotulo.dm"]}
          value={dm}
          phrase={textFor("retorno.dm", reading)(dm, result.beats_reference === true)}
          phraseKey="dm"
        />
      </dl>
      <Forecast result={result} asset={asset} today={today} reading={reading} />
    </section>
  );
}

// ---------------------------------------------------------------- recolhidos na iniciante

/** Os dois erros quadráticos, o CW e o PT de cada modelo (RF-17). */
function Details({ run, reading }: { run: ReturnRun; reading: Reading }) {
  return (
    <div className="ruvor-returns-models">
      {run.results.map((r) => {
        const head = <h4 className="ruvor-h3">{modelName(r.model_name)}</h4>;
        if (failed(r)) {
          return (
            <section
              className="ruvor-returns-model"
              data-model={r.model_name}
              key={r.model_name}
            >
              {head}
              <Note>{TEXTOS["retorno.erroModelo"](r.error)}</Note>
            </section>
          );
        }
        const pt = r.pt_p_value === null ? null : formatPValue(r.pt_p_value);
        const todosAlta = pt === null ? Number(r.forecast_up_share) === 1 : null;
        const cw = formatPValue(r.cw_p_value);
        return (
          <section
            className="ruvor-returns-model"
            data-model={r.model_name}
            key={r.model_name}
          >
            {head}
            <dl className="ruvor-tests">
              <TestRow
                label={TEXTOS["retorno.rotulo.mse"]}
                value={formatScientific(r.mse ?? "0")}
              />
              <TestRow
                label={TEXTOS["retorno.rotulo.mseRef"]}
                value={formatScientific(r.mse_reference ?? "0")}
              />
              <TestRow
                label={TEXTOS["retorno.rotulo.cw"]}
                value={cw}
                phrase={textFor("retorno.cw", reading)(cw)}
                phraseKey="cw"
              />
              <TestRow
                label={TEXTOS["retorno.rotulo.pt"]}
                value={pt ?? TEXTOS["retorno.semPt"]}
                phrase={textFor("retorno.pt", reading)(pt, todosAlta)}
                phraseKey="pt"
              />
            </dl>
          </section>
        );
      })}
    </div>
  );
}

function Item({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function Trail({ run }: { run: ReturnRun }) {
  const pregoes = (n: number) => TEXTOS["risco.trilha.pregoes"](formatInteger(n));
  return (
    <>
      <p className="ruvor-eyebrow">{TEXTOS["retorno.trilha.titulo"]}</p>
      <Note>{TEXTOS["retorno.trilha"]}</Note>
      <dl className="ruvor-trail">
        <Item label={TEXTOS["risco.trilha.firstPrice"]}>
          {formatDate(run.first_price_date)}
        </Item>
        <Item label={TEXTOS["risco.trilha.asOf"]}>{formatDate(run.as_of_date)}</Item>
        <Item label={TEXTOS["risco.trilha.priceCount"]}>
          {formatInteger(run.price_count)}
        </Item>
        <Item label={TEXTOS["risco.trilha.train"]}>{pregoes(run.train_count)}</Item>
        <Item label={TEXTOS["risco.trilha.test"]}>{pregoes(run.test_count)}</Item>
        <Item label={TEXTOS["risco.trilha.window"]}>
          {pregoes(run.train_window_days)}
        </Item>
        <Item label={TEXTOS["retorno.trilha.refit"]}>
          {TEXTOS["retorno.trilha.refitValor"]}
        </Item>
        <Item label={TEXTOS["retorno.trilha.referencia"]}>
          {TEXTOS["retorno.trilha.referenciaValor"]}
        </Item>
        <Item label={TEXTOS["risco.trilha.engine"]}>{run.engine_version}</Item>
        <Item label={TEXTOS["risco.trilha.calculatedAt"]}>
          {instant(run.calculated_at)}
        </Item>
        <Item label={TEXTOS["risco.trilha.priceRun"]}>
          {TEXTOS["risco.trilha.coleta"](
            sourceName(run.price_run.source),
            instant(run.price_run.finished_at ?? run.price_run.started_at),
          )}
        </Item>
      </dl>
    </>
  );
}

// ---------------------------------------------------------------- o resultado (R3)

function verdictPhrase(returns: Returns, run: ReturnRun, reading: Reading): string {
  const ok = run.results.filter((r) => !failed(r));
  const batem: ModeloQueBate[] = ok
    .filter((r) => r.beats_reference === true)
    .map((r) => [modelName(r.model_name), r2Abs(r)] as const);
  const naoBatem = ok
    .filter((r) => r.beats_reference !== true)
    .map((r) => modelName(r.model_name));
  return textFor("retorno.veredito", reading)(
    returns.ticker,
    formatInteger(run.test_count),
    formatDate(run.as_of_date),
    batem,
    naoBatem,
    run.results.length - ok.length,
  );
}

function Result({
  returns,
  asset,
  today,
  reading,
  titleId,
}: {
  returns: Returns;
  asset: AssetLoad;
  today: string;
  reading: Reading;
  titleId: string;
}) {
  const run = returns.latest as ReturnRun;
  return (
    <div className="ruvor-stack">
      <Aviso />
      <div className="ruvor-callout ruvor-returns-callout" data-phrase="veredito">
        <Glyph name="scales" />
        <p>{verdictPhrase(returns, run, reading)}</p>
      </div>
      <section className="ruvor-panel" aria-labelledby={`${titleId}-modelos`}>
        <div className="ruvor-panel__body">
          <h3 className="ruvor-sr-only" id={`${titleId}-modelos`}>
            {TEXTOS["retorno.titulo"]}
          </h3>
          <div className="ruvor-returns-models">
            {run.results.map((r) => (
              <ModelBlock
                key={r.model_name}
                result={r}
                asset={asset}
                today={today}
                reading={reading}
              />
            ))}
          </div>
        </div>
      </section>
      <Collapsible name="returns-details" label={TEXTOS["retorno.detalhes.abrir"]}>
        <Details run={run} reading={reading} />
      </Collapsible>
      <Collapsible name="returns-trail" label={TEXTOS["retorno.trilha.abrir"]}>
        <Trail run={run} />
      </Collapsible>
    </div>
  );
}

// ---------------------------------------------------------------- a seção

function assetLoadOf(asset: Load<AssetDetail>): AssetLoad {
  return asset.state === "ok"
    ? { state: "ok", status: asset.data.status }
    : { state: asset.state };
}

function pricesLoadOf(prices: Load<Prices>): PricesLoad {
  return prices.state === "ok"
    ? { state: "ok", count: prices.data.results.length }
    : { state: prices.state };
}

export function ReturnsSection({
  load,
  asset,
  prices,
  today,
  onRetry,
  onRetryPrices,
}: {
  load: Load<Returns>;
  asset: Load<AssetDetail>;
  prices: Load<Prices>;
  /** Hoje no fuso do navegador, `AAAA-MM-DD` (a `today()` da tela): a data da previsão. */
  today: string;
  onRetry: () => void;
  onRetryPrices: () => void;
}) {
  const titleId = useId();
  const reading = useReading();
  const assetLoad = assetLoadOf(asset);
  const pricesLoad = pricesLoadOf(prices);
  const state = returnsState(assetLoad, load, pricesLoad);

  let body: ReactNode;
  if (state === "R1") {
    body = (
      <>
        <p className="ruvor-sr-only">{TEXTOS["retorno.carregando"]}</p>
        <SectionSkeleton />
      </>
    );
  } else if (state === "R2") {
    body = <SectionError onRetry={onRetry} />;
  } else if (state === "R3" && load.state === "ok") {
    body = (
      <Result
        returns={load.data}
        asset={assetLoad}
        today={today}
        reading={reading}
        titleId={titleId}
      />
    );
  } else {
    let panel: ReactNode;
    if (state === "R4") {
      panel = (
        <StatePanel
          title={TEXTOS["retorno.estado.inativo.titulo"]}
          text={TEXTOS["retorno.estado.inativo"]}
        />
      );
    } else if (state === "R5") {
      panel = (
        <StatePanel
          tone="review"
          title={TEXTOS["retorno.estado.semSerie.titulo"]}
          text={TEXTOS["retorno.estado.semSerie"]}
          actions={<RetryButton onRetry={onRetryPrices} />}
        />
      );
    } else if (state === "R6") {
      panel = (
        <StatePanel
          title={TEXTOS["retorno.estado.naoCoberto.titulo"]}
          text={TEXTOS["retorno.estado.naoCoberto"]}
        />
      );
    } else if (state === "R7") {
      panel = (
        <StatePanel
          title={TEXTOS["retorno.estado.serieCurta.titulo"]}
          text={TEXTOS["retorno.estado.serieCurta"](
            formatInteger(pricesLoad.state === "ok" ? pricesLoad.count : 0),
            formatInteger(MIN_SESSIONS),
          )}
        />
      );
    } else {
      panel = (
        <StatePanel
          title={TEXTOS["retorno.estado.naoCalculado.titulo"]}
          text={TEXTOS["retorno.estado.naoCalculado"]}
        />
      );
    }
    body = (
      <div className="ruvor-stack">
        <Aviso />
        {panel}
      </div>
    );
  }

  return (
    <section
      className="ruvor-stack"
      aria-labelledby={titleId}
      data-section="returns"
      data-returns-state={state}
    >
      <div className="ruvor-section-head">
        <div>
          <p className="ruvor-eyebrow">{TEXTOS["retorno.sobrancelha"]}</p>
          <h2 className="ruvor-h2" id={titleId}>
            {TEXTOS["retorno.titulo"]}
          </h2>
        </div>
      </div>
      <p className="ruvor-sub">{TEXTOS["retorno.intro"]}</p>
      <div data-body="true" aria-busy={state === "R1" ? true : undefined}>
        {body}
      </div>
    </section>
  );
}
