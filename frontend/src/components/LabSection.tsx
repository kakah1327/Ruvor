import { type ReactNode, useId } from "react";

import type { Load } from "../api/resource";
import {
  type Lab,
  type LabResult,
  type LabRun,
  type LabYear,
  MODEL_ORDER,
  type ModelName,
} from "../api/types";
import { TEXTOS } from "../content/textos";
import {
  formatDate,
  formatDecimal,
  formatInstant,
  formatInteger,
} from "../format/numbers";
import { labState, promisesRetry, readyNote } from "../lab/state";
import { type Reading, textFor, useReading } from "../reading";
import { MIN_SESSIONS } from "../risk/config";
import { Collapsible } from "./Collapsible";
import { Glyph } from "./Glyph";
import { SectionError, SectionSkeleton } from "./SectionStatus";

/**
 * A seção do laboratório (M2.4, RF-13 a RF-17), logo depois da seção de risco: o experimento
 * fixo da década, para todo visitante, nas duas leituras — o `laboratorio.html` aprovado. Os
 * estados são os de `lab/state.ts`, na ordem do RF-14; os modelos, sempre em `MODEL_ORDER`,
 * sem ordenar, destacar nem eleger nenhum.
 */

type Alpha = "0.0500" | "0.0100";
const ALPHAS: readonly Alpha[] = ["0.0500", "0.0100"];
const CADA_N: Record<Alpha, number> = { "0.0500": 20, "0.0100": 100 };
/** O trecho com menos retornos que isto não é julgado (`LAB_YEAR_MIN_JUDGED` do backend). */
const MIN_JUDGED = 126;
/** O tamanho de um trecho cheio (`LAB_YEAR_DAYS` do backend). */
const YEAR_DAYS = 252;
/** Os instantes no fuso da B3, como a trilha do risco. */
const TIME_ZONE = "America/Sao_Paulo";

/** A família de cada modelo: a linha de baixo do nome, como na tabela do risco. */
const CATEGORY: Record<ModelName, LabResult["model_category"]> = {
  historical: "traditional",
  parametric: "traditional",
  monte_carlo: "traditional",
  garch_1_1: "garch",
  egarch: "garch",
  lstm: "ml",
  gru: "ml",
  garchnet: "ml",
  caviar: "ml",
};

// ---------------------------------------------------------------- formatação

function formatPValue(value: string): string {
  const p = Number(value);
  return p < 0.001 ? "< 0,001" : formatDecimal(p, 3);
}

const monthFormat = new Intl.DateTimeFormat("pt-BR", {
  month: "short",
  timeZone: "UTC",
});

/** "2017-09-26" → "set/2017": o mês abreviado do pt-BR, sem o ponto, e o ano. */
function formatMonthYear(value: string): string {
  const [year = "", month = "1"] = value.split("-");
  const name = monthFormat.format(Date.UTC(Number(year), Number(month) - 1, 1));
  return `${name.replace(".", "")}/${year}`;
}

function instantDate(value: string): string {
  return formatInstant(value, TIME_ZONE).split(" ")[0] ?? "";
}

function instant(value: string): string {
  const [data = "", hora = ""] = formatInstant(value, TIME_ZONE).split(" ");
  return TEXTOS["risco.trilha.instante"](data, hora);
}

// ---------------------------------------------------------------- leitura dos resultados

const failed = (r: LabResult | null): boolean =>
  r === null || r.error !== "" || r.violations === null;
const judged = (y: LabYear): boolean =>
  y.kupiec_passed !== null && y.christoffersen_passed !== null;

function resultOf(run: LabRun, model: ModelName, alpha: Alpha): LabResult | null {
  return run.results.find((r) => r.model_name === model && r.alpha === alpha) ?? null;
}

/** Os modelos com erro em ao menos um nível (ou sem resultado, num `partial`). */
function modelsWithError(run: LabRun): number {
  return MODEL_ORDER.filter((m) => ALPHAS.some((a) => failed(resultOf(run, m, a))))
    .length;
}

// ---------------------------------------------------------------- pedaços

function VerdictTag({ adequate }: { adequate: boolean | null }) {
  if (adequate === null) {
    return (
      <span className="ruvor-tag ruvor-tag--neutral">
        {TEXTOS["risco.tag.naoJulgado"]}
      </span>
    );
  }
  return adequate ? (
    <span className="ruvor-tag ruvor-tag--validated">
      {TEXTOS["risco.tag.adequado"]}
    </span>
  ) : (
    <span className="ruvor-tag ruvor-tag--review">
      {TEXTOS["risco.tag.naoAdequado"]}
    </span>
  );
}

function ShortTag() {
  return (
    <span className="ruvor-tag ruvor-tag--neutral" data-tag="ano-curto">
      {TEXTOS["laboratorio.tag.anoCurto"]}
    </span>
  );
}

function PassTag({ ok }: { ok: boolean }) {
  return (
    <span
      className={ok ? "ruvor-tag ruvor-tag--validated" : "ruvor-tag ruvor-tag--review"}
    >
      {ok ? TEXTOS["risco.teste.passou"] : TEXTOS["risco.teste.naoPassou"]}
    </span>
  );
}

function Note({ phrase, children }: { phrase: string; children: ReactNode }) {
  return (
    <p className="ruvor-note" data-phrase={phrase}>
      {children}
    </p>
  );
}

/** O painel de estado, como o do risco: o sinal, o título, a frase e as notas. */
function StatePanel({
  tone = "evidence",
  title,
  text,
  notes = [],
  notice = false,
}: {
  tone?: "evidence" | "review";
  title: string;
  text?: string;
  notes?: string[];
  notice?: boolean;
}) {
  const inner = (
    <>
      <span className={`ruvor-icon ruvor-icon--${tone}`}>
        <Glyph name={tone === "review" ? "warning" : "info"} weight="duotone" />
      </span>
      <div className="ruvor-state__body">
        <p className="ruvor-state__title">{title}</p>
        {text !== undefined && <p className="ruvor-state__text">{text}</p>}
        {notes.map((note) => (
          <p className="ruvor-note" key={note}>
            {note}
          </p>
        ))}
      </div>
    </>
  );
  return notice ? (
    <div className="ruvor-state ruvor-state--notice" data-note-panel="true">
      {inner}
    </div>
  ) : (
    <div className="ruvor-panel">
      <div className="ruvor-panel__body ruvor-state">{inner}</div>
    </div>
  );
}

// ---------------------------------------------------------------- a grade de um nível

function Grid({
  run,
  alpha,
  reading,
}: {
  run: LabRun;
  alpha: Alpha;
  reading: Reading;
}) {
  const captionId = useId();
  const is95 = alpha === "0.0500";
  const ref = MODEL_ORDER.map((m) => resultOf(run, m, alpha)).find(
    (r): r is LabResult => !failed(r),
  );
  const years = ref?.years ?? [];
  const cols = 1 + years.length + 1 + (is95 ? 1 : 0);
  const last = years.at(-1);
  const short =
    last !== undefined && last.test_count < MIN_JUDGED ? last.test_count : null;
  const celulas = MODEL_ORDER.map((m) => resultOf(run, m, alpha))
    .filter((r): r is LabResult => !failed(r))
    .reduce((n, r) => n + r.years.filter(judged).length, 0);

  // As colunas da década e dos anos não rejeitados, em duas cópias: logo depois do nome (até
  // 720 px) e no fim (larguras largas) — o ajuste do portão; o kit mostra uma.
  const decadeHead = (where: "narrow" | "wide") => (
    <>
      <th
        scope="col"
        className={`ruvor-lab-grid__decade ruvor-lab-grid__${where}${where === "narrow" && !is95 ? " ruvor-lab-grid__lead-end" : ""}`}
      >
        {TEXTOS["laboratorio.grade.col.decada"]}
        {ref !== undefined && ref.expected_violations !== null && (
          <span className="ruvor-lab-grid__sub">
            {TEXTOS["laboratorio.grade.esperadas"](
              formatDecimal(Number(ref.expected_violations), 1),
            )}
          </span>
        )}
      </th>
      {is95 && (
        <th
          scope="col"
          className={`ruvor-lab-grid__${where}${where === "narrow" ? " ruvor-lab-grid__lead-end" : ""}`}
        >
          {TEXTOS["laboratorio.grade.col.anos"]}
        </th>
      )}
    </>
  );

  const decadeCells = (r: LabResult, where: "narrow" | "wide") => {
    const julgados = r.years.filter(judged);
    return (
      <>
        <td
          className={`ruvor-lab-grid__decade ruvor-lab-grid__${where}${where === "narrow" && !is95 ? " ruvor-lab-grid__lead-end" : ""}`}
          data-decade="true"
        >
          <div className="ruvor-cell-stack">
            <span className="ruvor-num">
              {`${formatInteger(r.violations ?? 0)} × ${formatDecimal(Number(r.expected_violations), 1)}`}
            </span>
            <VerdictTag adequate={r.adequate} />
          </div>
        </td>
        {is95 && (
          <td
            className={`ruvor-lab-grid__${where}${where === "narrow" ? " ruvor-lab-grid__lead-end" : ""}`}
            data-years-not-rejected="true"
          >
            <span className="ruvor-num">
              {TEXTOS["laboratorio.grade.kDeN"](
                julgados.filter((y) => y.adequate === true).length,
                julgados.length,
              )}
            </span>
          </td>
        )}
      </>
    );
  };

  const notes = (
    <div className="ruvor-stack">
      <Note phrase="violacoesAno">
        {textFor("laboratorio.violacoesAno", reading)(
          formatDecimal(YEAR_DAYS * Number(alpha), 1),
          CADA_N[alpha],
        )}
      </Note>
      {is95 ? (
        <Note phrase="vereditoAno">
          {textFor("laboratorio.vereditoAno", reading)(celulas)}
        </Note>
      ) : (
        <Note phrase="semVereditoAno99">
          {textFor("laboratorio.semVereditoAno99", reading)}
        </Note>
      )}
      {short !== null && (
        <Note phrase="anoNaoJulgado">
          {textFor("laboratorio.anoNaoJulgado", reading)(short)}
        </Note>
      )}
      <Note phrase="vereditoDecada">
        {textFor("laboratorio.vereditoDecada", reading)}
      </Note>
      {is95 && (
        <Note phrase="anosNaoRejeitados">
          {textFor("laboratorio.anosNaoRejeitados", reading)}
        </Note>
      )}
    </div>
  );

  const legend = (
    <div className="ruvor-legend">
      <VerdictTag adequate={true} />
      <VerdictTag adequate={false} />
      {is95 && short !== null && <ShortTag />}
      <VerdictTag adequate={null} />
    </div>
  );

  return (
    <section className="ruvor-panel" data-alpha={alpha} aria-labelledby={captionId}>
      <div className="ruvor-panel__head">
        <Glyph name="calendar-blank" />
        <div>
          <p className="ruvor-eyebrow">{TEXTOS[`risco.nivel.${alpha}`]}</p>
          <h3 className="ruvor-h3" id={captionId}>
            {TEXTOS[`laboratorio.grade.titulo.${alpha}`]}
          </h3>
        </div>
      </div>
      {/* Na avançada, as notas antes da tabela; na iniciante, a grade primeiro (portão). */}
      {reading === "advanced" ? (
        <div className="ruvor-panel__body">
          <div className="ruvor-stack">
            {notes}
            {legend}
          </div>
        </div>
      ) : (
        <div className="ruvor-panel__body">{legend}</div>
      )}
      {/* O contêiner rolável: uma região com nome (a `section` com `aria-labelledby`), que recebe
          o foco pelo teclado para rolar a grade nas larguras estreitas (RF-19). */}
      <section
        className="ruvor-lab-scroll"
        // biome-ignore lint/a11y/noNoninteractiveTabindex: a região rolável precisa do foco pelo teclado para rolar (RF-19); sem ele, quem não usa mouse não alcança as colunas escondidas.
        tabIndex={0}
        aria-labelledby={captionId}
      >
        <table className="ruvor-table ruvor-lab-grid">
          <thead>
            <tr>
              <th scope="col">{TEXTOS["risco.tabela.col.modelo"]}</th>
              {decadeHead("narrow")}
              {years.map((y) => (
                <th scope="col" key={y.index}>
                  {TEXTOS["laboratorio.grade.ano"](y.index + 1)}
                  <span className="ruvor-lab-grid__sub">
                    {TEXTOS["laboratorio.grade.periodo"](
                      formatMonthYear(y.start_date),
                      formatMonthYear(y.end_date),
                    )}
                  </span>
                  <span className="ruvor-lab-grid__sub">
                    {TEXTOS["laboratorio.grade.esperadas"](
                      formatDecimal(Number(y.expected_violations), 1),
                    )}
                  </span>
                </th>
              ))}
              {decadeHead("wide")}
            </tr>
          </thead>
          <tbody>
            {MODEL_ORDER.map((m) => {
              const r = resultOf(run, m, alpha);
              const head = (
                <th scope="row">
                  {TEXTOS[`risco.modelo.${m}`]}
                  <span className="ruvor-table__sub">
                    {TEXTOS[`risco.categoria.${CATEGORY[m]}`]}
                  </span>
                </th>
              );
              if (r === null || failed(r)) {
                return (
                  <tr key={m} data-model={m} data-error="true">
                    {head}
                    <td colSpan={cols - 1}>
                      <p className="ruvor-note ruvor-keep" data-phrase="erroModelo">
                        {TEXTOS["risco.erroModelo"](r?.error || "—")}
                      </p>
                    </td>
                  </tr>
                );
              }
              return (
                <tr key={m} data-model={m}>
                  {head}
                  {decadeCells(r, "narrow")}
                  {years.map((_, i) => {
                    const y = r.years[i];
                    if (y === undefined) return <td key={`vazio-${String(i)}`}>—</td>;
                    return (
                      <td
                        className="ruvor-lab-grid__year"
                        key={y.index}
                        data-year={y.index}
                      >
                        <div className="ruvor-cell-stack">
                          <span className="ruvor-num">
                            {formatInteger(y.violations)}
                          </span>
                          {is95 &&
                            (judged(y) ? (
                              <VerdictTag adequate={y.adequate} />
                            ) : (
                              <ShortTag />
                            ))}
                        </div>
                      </td>
                    );
                  })}
                  {decadeCells(r, "wide")}
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
      {reading !== "advanced" && <div className="ruvor-panel__body">{notes}</div>}
    </section>
  );
}

// ---------------------------------------------------------------- os testes de cada modelo

function TestRow({
  test,
  pValue,
  passed,
  reading,
}: {
  test: "kupiec" | "christoffersen" | "dq";
  pValue: string | null;
  passed: boolean | null;
  reading: Reading;
}) {
  const known = pValue !== null && passed !== null;
  return (
    <div className="ruvor-test" data-test={test}>
      <dt>{TEXTOS[`risco.rotulo.${test}`]}</dt>
      <dd>
        <span className="ruvor-num">{known ? formatPValue(pValue) : "—"}</span>
        {known && <PassTag ok={passed} />}
      </dd>
      {known && (
        <p className="ruvor-note">
          {textFor(`risco.${test}`, reading)(formatPValue(pValue), passed)}
        </p>
      )}
    </div>
  );
}

function LevelTests({
  result,
  alpha,
  reading,
}: {
  result: LabResult | null;
  alpha: Alpha;
  reading: Reading;
}) {
  const title = <p className="ruvor-eyebrow">{TEXTOS[`risco.nivel.${alpha}`]}</p>;
  if (result === null || failed(result)) {
    return (
      <div data-alpha={alpha}>
        {title}
        <p className="ruvor-note ruvor-keep" data-phrase="erroModelo">
          {TEXTOS["risco.erroModelo"](result?.error || "—")}
        </p>
      </div>
    );
  }
  const v = formatInteger(result.violations ?? 0);
  const e = formatDecimal(Number(result.expected_violations), 1);
  return (
    <div data-alpha={alpha}>
      {title}
      <dl className="ruvor-tests">
        <div className="ruvor-test" data-test="violacoes">
          <dt>{TEXTOS["risco.rotulo.violacoes"]}</dt>
          <dd className="ruvor-num">{`${v} × ${e}`}</dd>
          <p className="ruvor-note" data-phrase="violacoesDecada">
            {textFor("laboratorio.violacoesDecada", reading)(
              v,
              e,
              CADA_N[alpha],
              result.kupiec_passed === true,
            )}
          </p>
        </div>
        <TestRow
          test="kupiec"
          pValue={result.kupiec_p_value}
          passed={result.kupiec_passed}
          reading={reading}
        />
        <TestRow
          test="christoffersen"
          pValue={result.christoffersen_p_value}
          passed={result.christoffersen_passed}
          reading={reading}
        />
        <TestRow
          test="dq"
          pValue={result.dq_p_value}
          passed={result.dq_passed}
          reading={reading}
        />
      </dl>
      {alpha === "0.0500" && (
        <section
          className="ruvor-lab-years ruvor-lab-scroll"
          // biome-ignore lint/a11y/noNoninteractiveTabindex: a região rolável precisa do foco pelo teclado para rolar (RF-19).
          tabIndex={0}
          aria-label={TEXTOS["laboratorio.testes.porAno"]}
        >
          <table className="ruvor-table">
            <caption>{TEXTOS["laboratorio.testes.porAno"]}</caption>
            <thead>
              <tr>
                <th scope="col">{TEXTOS["laboratorio.testes.col.ano"]}</th>
                <th scope="col">{TEXTOS["risco.rotulo.kupiec"]}</th>
                <th scope="col">{TEXTOS["risco.rotulo.christoffersen"]}</th>
                <th scope="col">{TEXTOS["laboratorio.testes.col.veredito"]}</th>
              </tr>
            </thead>
            <tbody>
              {result.years.map((y) => (
                <tr key={y.index}>
                  <th scope="row">{TEXTOS["laboratorio.grade.ano"](y.index + 1)}</th>
                  {judged(y) &&
                  y.kupiec_p_value !== null &&
                  y.christoffersen_p_value !== null ? (
                    <>
                      <td>
                        <span className="ruvor-num">
                          {formatPValue(y.kupiec_p_value)}
                        </span>{" "}
                        <PassTag ok={y.kupiec_passed === true} />
                      </td>
                      <td>
                        <span className="ruvor-num">
                          {formatPValue(y.christoffersen_p_value)}
                        </span>{" "}
                        <PassTag ok={y.christoffersen_passed === true} />
                      </td>
                      <td>
                        <VerdictTag adequate={y.adequate} />
                      </td>
                    </>
                  ) : (
                    <>
                      <td>—</td>
                      <td>—</td>
                      <td>
                        <ShortTag />
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

function ModelTests({ run, reading }: { run: LabRun; reading: Reading }) {
  return (
    <div className="ruvor-lab-models">
      {MODEL_ORDER.map((m) => (
        <section
          className="ruvor-lab-model"
          data-model={m}
          key={m}
          aria-label={TEXTOS[`risco.modelo.${m}`]}
        >
          <h4 className="ruvor-h3">{TEXTOS[`risco.modelo.${m}`]}</h4>
          <div className="ruvor-lab-levels">
            {ALPHAS.map((a) => (
              <LevelTests
                key={a}
                result={resultOf(run, m, a)}
                alpha={a}
                reading={reading}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- a trilha

function sourceName(source: string): string {
  const text = (TEXTOS as Record<string, unknown>)[`risco.trilha.fonte.${source}`];
  return typeof text === "string" ? text : source;
}

function Item({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function LabTrail({ run }: { run: LabRun }) {
  const pregoes = (n: number) => TEXTOS["risco.trilha.pregoes"](formatInteger(n));
  const reused = run.results.reduce((n, r) => n + (r.reused_snapshots ?? 0), 0);
  const trained = run.results.reduce((n, r) => n + (r.trained_snapshots ?? 0), 0);
  const status =
    run.status === "ok"
      ? TEXTOS["risco.trilha.status.ok"]
      : TEXTOS["risco.trilha.status.partial"](modelsWithError(run));
  return (
    <>
      <p className="ruvor-eyebrow">{TEXTOS["laboratorio.trilha.titulo"]}</p>
      <p className="ruvor-note">{TEXTOS["laboratorio.trilha"]}</p>
      <dl className="ruvor-trail">
        <Item label={TEXTOS["risco.trilha.firstPrice"]}>
          {formatDate(run.first_price_date)}
        </Item>
        <Item label={TEXTOS["risco.trilha.asOf"]}>{formatDate(run.as_of_date)}</Item>
        <Item label={TEXTOS["laboratorio.trilha.decadeEnd"]}>
          {formatDate(run.decade_end)}
        </Item>
        <Item label={TEXTOS["risco.trilha.priceCount"]}>
          {formatInteger(run.price_count)}
        </Item>
        <Item label={TEXTOS["risco.trilha.train"]}>{pregoes(run.train_count)}</Item>
        <Item label={TEXTOS["risco.trilha.test"]}>{pregoes(run.test_count)}</Item>
        <Item label={TEXTOS["laboratorio.trilha.years"]}>
          {formatInteger(run.year_count)}
        </Item>
        <Item label={TEXTOS["risco.trilha.window"]}>
          {pregoes(run.train_window_days)}
        </Item>
        <Item label={TEXTOS["risco.trilha.seed"]}>{String(run.seed)}</Item>
        <Item label={TEXTOS["risco.trilha.engine"]}>{run.engine_version}</Item>
        <Item label={TEXTOS["risco.trilha.calculatedAt"]}>
          {instant(run.calculated_at)}
        </Item>
        <Item label={TEXTOS["risco.trilha.finishedAt"]}>
          {instant(run.finished_at)}
        </Item>
        <Item label={TEXTOS["laboratorio.trilha.origin"]}>
          {TEXTOS[`laboratorio.trilha.origin.${run.origin}`]}
        </Item>
        <Item label={TEXTOS["risco.trilha.priceRun"]}>
          {TEXTOS["risco.trilha.coleta"](
            sourceName(run.price_run.source),
            instant(run.price_run.finished_at ?? run.price_run.started_at),
          )}
        </Item>
        <Item label={TEXTOS["laboratorio.trilha.snapshots"]}>
          {TEXTOS["laboratorio.trilha.retratos"](
            formatInteger(reused),
            formatInteger(trained),
          )}
        </Item>
        <Item label={TEXTOS["risco.trilha.status"]}>{status}</Item>
        <div>
          <dt>{TEXTOS["laboratorio.trilha.fingerprint"]}</dt>
          <dd className="ruvor-num ruvor-lab-hash">{run.price_fingerprint}</dd>
        </div>
      </dl>
    </>
  );
}

// ---------------------------------------------------------------- o estado pronto

function Ready({ lab, reading }: { lab: Lab; reading: Reading }) {
  const run = lab.latest as LabRun;
  const note = readyNote(lab);
  const promise = promisesRetry(lab);
  const lastYear = run.results.find((r) => !failed(r))?.years.at(-1);
  return (
    <div className="ruvor-stack" data-note={note ?? "none"}>
      {note === "failure" && lab.last_failure !== null && (
        <StatePanel
          notice
          tone="review"
          title={TEXTOS["laboratorio.nota.falha"](
            instantDate(lab.last_failure.calculated_at),
          )}
          notes={promise ? [TEXTOS["laboratorio.estado.tentaDeNovo"]] : []}
        />
      )}
      {note === "engine" && lab.risk_engine_version !== null && (
        <StatePanel
          notice
          title={TEXTOS["laboratorio.nota.motor"](
            run.engine_version,
            lab.risk_engine_version,
          )}
        />
      )}
      {note === "partial" && (
        <StatePanel
          notice
          tone="review"
          title={TEXTOS["laboratorio.nota.parcial"](modelsWithError(run))}
          notes={promise ? [TEXTOS["laboratorio.nota.refeito"]] : []}
        />
      )}
      <p className="ruvor-note" data-phrase="decada">
        {textFor("laboratorio.decada", reading)(
          formatDate(run.first_price_date),
          formatDate(run.as_of_date),
          run.year_count,
          lastYear?.test_count ?? YEAR_DAYS,
        )}
      </p>
      <div className="ruvor-callout ruvor-lab-honest" data-phrase="diferenca">
        <Glyph name="scales" />
        <p>
          {textFor("laboratorio.diferenca", reading)(
            run.engine_version,
            formatDate(run.as_of_date),
          )}
        </p>
      </div>
      {ALPHAS.map((a) => (
        <Grid key={a} run={run} alpha={a} reading={reading} />
      ))}
      <Collapsible name="lab-tests" label={TEXTOS["laboratorio.testes.abrir"]}>
        <ModelTests run={run} reading={reading} />
      </Collapsible>
      <Collapsible name="lab-trail" label={TEXTOS["laboratorio.trilha.abrir"]}>
        <LabTrail run={run} />
      </Collapsible>
    </div>
  );
}

// ---------------------------------------------------------------- a seção

function Body({
  load,
  onRetry,
  reading,
}: {
  load: Load<Lab>;
  onRetry: () => void;
  reading: Reading;
}) {
  const state = labState(load);
  if (load.state === "loading") {
    return (
      <>
        <p className="ruvor-sr-only">{TEXTOS["laboratorio.carregando"]}</p>
        <SectionSkeleton />
      </>
    );
  }
  if (load.state === "error") return <SectionError onRetry={onRetry} />;
  const lab = load.data;
  switch (state) {
    case "READY":
      return <Ready lab={lab} reading={reading} />;
    case "FAILED":
      return (
        <StatePanel
          tone="review"
          title={TEXTOS["laboratorio.estado.falhou.titulo"]}
          text={TEXTOS["laboratorio.estado.falhou"](
            instantDate(lab.last_failure?.calculated_at ?? ""),
          )}
          notes={promisesRetry(lab) ? [TEXTOS["laboratorio.estado.tentaDeNovo"]] : []}
        />
      );
    case "PENDING":
      return (
        <StatePanel
          title={TEXTOS["laboratorio.estado.aCalcular.titulo"]}
          text={TEXTOS["laboratorio.estado.aCalcular"]}
        />
      );
    case "INACTIVE":
      return (
        <StatePanel
          title={TEXTOS["laboratorio.estado.inativo.titulo"]}
          text={TEXTOS["laboratorio.estado.inativo"]}
        />
      );
    case "NO_DECADE":
      return (
        <StatePanel
          title={TEXTOS["laboratorio.estado.semDecada.titulo"]}
          text={TEXTOS["laboratorio.estado.semDecada"](
            formatDate(lab.decade.first_price_date ?? ""),
            formatDate(lab.decade.end_date ?? ""),
          )}
        />
      );
    case "SHORT":
      return (
        <StatePanel
          title={TEXTOS["laboratorio.estado.serieCurta.titulo"]}
          text={TEXTOS["laboratorio.estado.serieCurta"](
            formatInteger(lab.decade.sessions),
            formatInteger(MIN_SESSIONS),
          )}
        />
      );
    default:
      return (
        <StatePanel
          title={TEXTOS["laboratorio.estado.semRisco.titulo"]}
          text={TEXTOS["laboratorio.estado.semRisco"]}
        />
      );
  }
}

export function LabSection({
  load,
  onRetry,
}: {
  load: Load<Lab>;
  onRetry: () => void;
}) {
  const titleId = useId();
  const reading = useReading();
  const state = labState(load);
  return (
    <section
      className="ruvor-stack"
      aria-labelledby={titleId}
      data-section="lab"
      data-lab-state={state}
    >
      <div className="ruvor-section-head">
        <div>
          <p className="ruvor-eyebrow">{TEXTOS["laboratorio.sobrancelha"]}</p>
          <h2 className="ruvor-h2" id={titleId}>
            {TEXTOS["laboratorio.titulo"]}
          </h2>
        </div>
      </div>
      <p className="ruvor-sub">{TEXTOS["laboratorio.intro"]}</p>
      <div data-body="true" aria-busy={state === "LOADING" ? true : undefined}>
        <Body load={load} onRetry={onRetry} reading={reading} />
      </div>
    </section>
  );
}
