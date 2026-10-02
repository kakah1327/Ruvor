import { Fragment, useId, useState } from "react";

import { MODEL_ORDER, type ModelName, type RiskResult } from "../api/types";
import { BLOCOS_AVANCADOS } from "../content/avancado";
import { TEXTOS } from "../content/textos";
import { formatDecimal, formatInteger } from "../format/numbers";
import { formatLoss, lossFromVar } from "../format/var";
import { type Reading, textFor, useReading } from "../reading";
import type { Alpha } from "../risk/summary";
import { Glyph } from "./Glyph";
import { ALPHAS, CADA_N } from "./LossSummary";

/** A família de cada modelo (RF-15): a linha de baixo do nome. */
const CATEGORY: Record<ModelName, RiskResult["model_category"]> = {
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

/** O p-valor com três casas; abaixo de 0,001, "< 0,001", como no mockup. */
function formatPValue(value: string): string {
  const p = Number(value);
  return p < 0.001 ? "< 0,001" : formatDecimal(p, 3);
}

/** O veredito em tag, com texto (RF-15): adequado, não adequado, ou não julgado. */
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

function PassTag({ ok }: { ok: boolean }) {
  return (
    <span
      className={ok ? "ruvor-tag ruvor-tag--validated" : "ruvor-tag ruvor-tag--review"}
    >
      {ok ? TEXTOS["risco.teste.passou"] : TEXTOS["risco.teste.naoPassou"]}
    </span>
  );
}

/**
 * A célula de um nível: a perda (RF-12), a barra na escala comum às dezoito células e a
 * tag. Sem perda — o modelo falhou, ou não tem linha —, "—" e a tag, sem barra.
 */
function LossCell({ result, scale }: { result: RiskResult | null; scale: number }) {
  if (result === null || result.var_latest === null) {
    return (
      <td>
        <div className="ruvor-cell-stack">
          <span className="ruvor-loss">
            <b className="ruvor-num">—</b>
          </span>
          <VerdictTag adequate={result?.adequate ?? null} />
        </div>
      </td>
    );
  }
  const loss = lossFromVar(Number(result.var_latest));
  return (
    <td>
      <div className="ruvor-cell-stack">
        <span className="ruvor-loss">
          <b className="ruvor-num">{formatLoss(result.var_latest)}</b>
        </span>
        <span className="ruvor-bar ruvor-bar--evidence" aria-hidden="true">
          <span
            className="ruvor-bar__fill"
            style={{ width: `${((100 * loss) / scale).toFixed(1)}%` }}
          />
        </span>
        <VerdictTag adequate={result.adequate} />
      </div>
    </td>
  );
}

type TestKey = "kupiec" | "christoffersen" | "dq";

/** Um teste: o p-valor, se passou, e a frase. Sem o dado, "—", sem tag nem frase. */
function TestRow({
  test,
  pValue,
  passed,
}: {
  test: TestKey;
  pValue: string | null;
  passed: boolean | null;
}) {
  const reading = useReading();
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

/**
 * Os testes de um modelo num nível (RF-15): violações × esperadas, Kupiec, Christoffersen e
 * DQ. O modelo que falhou — sem linha, com erro, ou com o Kupiec nulo — mostra o erro.
 */
function LevelTests({ result, alpha }: { result: RiskResult | null; alpha: Alpha }) {
  const reading = useReading();
  const title = <p className="ruvor-eyebrow">{TEXTOS[`risco.nivel.${alpha}`]}</p>;
  if (
    result === null ||
    result.error !== "" ||
    result.kupiec_passed === null ||
    result.violations === null ||
    result.expected_violations === null
  ) {
    return (
      <div data-alpha={alpha}>
        {title}
        <p className="ruvor-note" data-phrase="erroModelo">
          {TEXTOS["risco.erroModelo"](result?.error || "—")}
        </p>
      </div>
    );
  }
  const violations = formatInteger(result.violations);
  const expected = formatDecimal(Number(result.expected_violations), 1);
  return (
    <div data-alpha={alpha}>
      {title}
      <dl className="ruvor-tests">
        <div className="ruvor-test" data-test="violacoes">
          <dt>{TEXTOS["risco.rotulo.violacoes"]}</dt>
          <dd className="ruvor-num">{`${violations} × ${expected}`}</dd>
          <p className="ruvor-note">
            {textFor("risco.violacoes", reading)(
              violations,
              expected,
              CADA_N[alpha],
              result.kupiec_passed,
            )}
          </p>
        </div>
        <TestRow
          test="kupiec"
          pValue={result.kupiec_p_value}
          passed={result.kupiec_passed}
        />
        <TestRow
          test="christoffersen"
          pValue={result.christoffersen_p_value}
          passed={result.christoffersen_passed}
        />
        <TestRow test="dq" pValue={result.dq_p_value} passed={result.dq_passed} />
      </dl>
    </div>
  );
}

/**
 * As linhas de teste abertas no padrão de cada nível (RF-06, RF-07 do M2.3): nenhuma na
 * iniciante, as nove na avançada.
 */
function openFor(reading: Reading): ReadonlySet<ModelName> {
  return new Set(reading === "advanced" ? MODEL_ORDER : []);
}

/**
 * A tabela dos nove (RF-15), **em MODEL_ORDER** — nunca na ordem de chegada nem por valor.
 * As barras usam uma escala só: o máximo das dezoito perdas não nulas. A linha abre os
 * testes dos dois níveis. A zona de Basileia não aparece.
 *
 * As linhas de teste (M2.3): fechadas na iniciante e abertas na avançada; trocar o nível
 * reaplica o padrão — o estado guarda o nível em que foi decidido, como o `Collapsible` —, e
 * cada linha expansível leva `data-collapsible="tests"` e o seu `data-open`.
 */
export function ModelTable({ results }: { results: readonly RiskResult[] }) {
  const reading = useReading();
  const baseId = useId();
  const titleId = `${baseId}-titulo`;
  const [state, setState] = useState<{
    reading: Reading;
    open: ReadonlySet<ModelName>;
  }>(() => ({ reading, open: openFor(reading) }));

  let open = state.open;
  if (state.reading !== reading) {
    // O nível mudou: o padrão dele vale de novo, ainda no desenho (o molde do `Collapsible`).
    open = openFor(reading);
    setState({ reading, open });
  }

  const at = (model: ModelName, alpha: Alpha): RiskResult | null =>
    results.find((r) => r.model_name === model && r.alpha === alpha) ?? null;

  const losses = results
    .filter((r) => r.var_latest !== null)
    .map((r) => lossFromVar(Number(r.var_latest)));
  const scale = Math.max(0, ...losses) || 1;

  const toggle = (model: ModelName) => {
    setState((current) => {
      const next = new Set(current.open);
      if (next.has(model)) next.delete(model);
      else next.add(model);
      return { reading: current.reading, open: next };
    });
  };

  return (
    <section className="ruvor-panel" aria-labelledby={titleId}>
      <div className="ruvor-panel__head">
        <Glyph name="scales" />
        <h3 className="ruvor-h3" id={titleId}>
          {TEXTOS["risco.tabela.titulo"]}
        </h3>
      </div>
      <div className="ruvor-panel__body">
        <div className="ruvor-stack">
          <p className="ruvor-note" data-phrase="intro">
            {reading === "advanced"
              ? BLOCOS_AVANCADOS["risco.tabela.intro"]
              : TEXTOS["risco.tabela.intro"]}
          </p>
          <div className="ruvor-legend">
            <VerdictTag adequate={true} />
            <VerdictTag adequate={false} />
            <VerdictTag adequate={null} />
          </div>
          <p className="ruvor-note" data-phrase="veredito">
            {textFor("risco.veredito", reading)}
          </p>
        </div>
      </div>
      <table className="ruvor-table ruvor-table--models">
        <colgroup>
          <col className="ruvor-table__col--lead" />
          <col />
          <col />
        </colgroup>
        <thead>
          <tr>
            <th scope="col">{TEXTOS["risco.tabela.col.modelo"]}</th>
            {ALPHAS.map((alpha) => (
              <th scope="col" key={alpha} data-alpha={alpha}>
                {TEXTOS[`risco.tabela.col.${alpha}`]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {MODEL_ORDER.map((model) => {
            const name = TEXTOS[`risco.modelo.${model}`];
            const detailId = `${baseId}-${model}`;
            const expanded = open.has(model);
            return (
              <Fragment key={model}>
                <tr
                  className="ruvor-table__row--expandable"
                  data-model={model}
                  data-collapsible="tests"
                  data-open={expanded}
                >
                  <td>
                    <button
                      className="ruvor-table__toggle"
                      type="button"
                      aria-expanded={expanded}
                      aria-controls={detailId}
                      aria-label={TEXTOS["risco.tabela.abrir"](name)}
                      onClick={() => toggle(model)}
                    >
                      <Glyph name="caret-right" />
                      <span>{name}</span>
                    </button>
                    <span className="ruvor-table__sub">
                      {TEXTOS[`risco.categoria.${CATEGORY[model]}`]}
                    </span>
                  </td>
                  {ALPHAS.map((alpha) => (
                    <LossCell key={alpha} result={at(model, alpha)} scale={scale} />
                  ))}
                </tr>
                <tr className="ruvor-table__detail" id={detailId} hidden={!expanded}>
                  <td colSpan={3}>
                    <div className="ruvor-table__detail-grid">
                      {ALPHAS.map((alpha) => (
                        <LevelTests
                          key={alpha}
                          result={at(model, alpha)}
                          alpha={alpha}
                        />
                      ))}
                    </div>
                  </td>
                </tr>
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
