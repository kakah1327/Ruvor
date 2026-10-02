import type { ModelName, RiskResult } from "../api/types";
import { MODEL_ORDER } from "../api/types";
import { TEXTOS } from "../content/textos";
import { formatPercent } from "../format/numbers";
import { textFor, useReading } from "../reading";
import { type Alpha, discordancia, naoRejeitados } from "../risk/summary";
import { Glyph } from "./Glyph";

/** Os dois níveis, na ordem da tela. */
export const ALPHAS = ["0.0500", "0.0100"] as const satisfies readonly Alpha[];

/** "1 dia a cada N": o N de cada nível. */
export const CADA_N: Record<Alpha, number> = { "0.0500": 20, "0.0100": 100 };

/**
 * A perda que `discordancia` já converteu (RF-12, por `lossFromVar`), com uma casa — a mesma
 * formatação de `formatLoss`, sem converter duas vezes.
 */
function formatConvertedLoss(loss: number): string {
  return formatPercent(loss, 1);
}

/**
 * Um nível (RF-13, RF-14): a faixa entre os modelos que calcularam, com o horizonte "em 1
 * dia", a frase da perda e a da discordância; e os não rejeitados, na ordem fixa, com a frase.
 * As três frases são as do nível de leitura (RF-05 do M2.3); o painel fica aberto nos dois
 * níveis, fora de qualquer recolhível (RF-06).
 */
function LevelPanel({
  results,
  alpha,
}: {
  results: readonly RiskResult[];
  alpha: Alpha;
}) {
  const reading = useReading();
  const range = discordancia(results, alpha);
  const accepted = naoRejeitados(results, alpha);
  const min = range === null ? null : formatConvertedLoss(range.min);
  const max = range === null ? null : formatConvertedLoss(range.max);

  let shown = "—";
  if (range !== null && min !== null && max !== null) {
    shown = range.n === 1 ? min : TEXTOS["risco.faixa"](min, max);
  }

  return (
    <article className="ruvor-panel" data-alpha={alpha}>
      <div className="ruvor-panel__body ruvor-level">
        <p className="ruvor-eyebrow">{TEXTOS[`risco.nivel.${alpha}`]}</p>
        <p className="ruvor-range">
          <b className="ruvor-num">{shown}</b>
          <small>{TEXTOS["risco.horizonte"]}</small>
        </p>
        <p className="ruvor-note" data-phrase="perda">
          {alpha === "0.0500"
            ? textFor("risco.perda95", reading)
            : textFor("risco.perda99", reading)}
        </p>
        <p className="ruvor-note" data-phrase="discordancia">
          {textFor("risco.discordancia", reading)(
            min,
            max,
            range?.n ?? 0,
            MODEL_ORDER.length,
            CADA_N[alpha],
            min,
          )}
        </p>
        <div className="ruvor-divider" />
        <p className="ruvor-level__title">{TEXTOS["risco.naoRejeitados.titulo"]}</p>
        {accepted.adequados.length > 0 && (
          <ul className="ruvor-tag-list">
            {accepted.adequados.map((model: ModelName) => (
              <li key={model}>
                <span className="ruvor-tag ruvor-tag--validated">
                  <Glyph name="check-circle" className="ruvor-glyph--sm" />
                  {TEXTOS[`risco.modelo.${model}`]}
                </span>
              </li>
            ))}
          </ul>
        )}
        <p className="ruvor-note" data-phrase="naoRejeitados">
          {textFor("risco.naoRejeitados", reading)(
            accepted.adequados.length,
            accepted.julgados,
            MODEL_ORDER.length,
          )}
        </p>
      </div>
    </article>
  );
}

/** Os dois níveis lado a lado (a quebra em uma coluna é do kit). */
export function LossSummary({ results }: { results: readonly RiskResult[] }) {
  return (
    <div className="ruvor-levels">
      {ALPHAS.map((alpha) => (
        <LevelPanel key={alpha} results={results} alpha={alpha} />
      ))}
    </div>
  );
}
