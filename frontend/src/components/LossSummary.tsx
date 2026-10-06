import type { ModelName, RiskResultBase } from "../api/types";
import { MODEL_ORDER } from "../api/types";
import type { LeituraKey } from "../content/avancado";
import { TEXTOS } from "../content/textos";
import { formatPercent } from "../format/numbers";
import { formatBrlText } from "../portfolio/notional";
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
 * A chave da frase dos não rejeitados: a do ativo ou a da carteira, cuja iniciante não diz
 * "este ativo" (a conferência da T1 do M2.2b). As duas têm a mesma assinatura.
 */
export type NotRejectedKey = "risco.naoRejeitados" | "carteira.risco.naoRejeitados";

/**
 * A faixa em reais de cada nível (a carteira com valor, M2.2b RF-10), por `alpha`: o
 * `loss_brl_min` e o `loss_brl_max` do `summary`, decimais da API; nulo, sem faixa.
 */
export type BrlRange = Readonly<Record<string, readonly [string, string] | null>>;

/**
 * Um nível (RF-13, RF-14): a faixa entre os modelos que calcularam, com o horizonte "em 1
 * dia", a frase da perda e a da discordância; e os não rejeitados, na ordem fixa, com a frase.
 * As três frases são as do nível de leitura (RF-05 do M2.3); o painel fica aberto nos dois
 * níveis, fora de qualquer recolhível (RF-06).
 *
 * Com `brl` (a carteira com valor), a faixa em reais logo abaixo da faixa em %, com o mesmo
 * horizonte, escrita pelo texto.
 */
function LevelPanel({
  results,
  alpha,
  brl,
  notRejectedKey,
}: {
  results: readonly RiskResultBase[];
  alpha: Alpha;
  brl: readonly [string, string] | null;
  notRejectedKey: NotRejectedKey;
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

  let shownBrl: string | null = null;
  if (brl !== null) {
    const [low, high] = brl.map(formatBrlText);
    if (low !== undefined && high !== undefined) {
      shownBrl = low === high ? low : TEXTOS["risco.faixa"](low, high);
    }
  }

  // `carteira.risco.naoRejeitados` nasce em `textos.ts` e `avancado.ts` na T9 do M2.2b; até lá,
  // o `Extract` deixa só a chave que já existe, e a do ativo é a única passada.
  const notRejected = textFor(
    notRejectedKey as Extract<NotRejectedKey, LeituraKey>,
    reading,
  );

  return (
    <article className="ruvor-panel" data-alpha={alpha}>
      <div className="ruvor-panel__body ruvor-level">
        <p className="ruvor-eyebrow">{TEXTOS[`risco.nivel.${alpha}`]}</p>
        <p className="ruvor-range">
          <b className="ruvor-num">{shown}</b>
          <small>{TEXTOS["risco.horizonte"]}</small>
        </p>
        {shownBrl !== null && (
          <p className="ruvor-range" data-part="perda-reais">
            <b className="ruvor-num">{shownBrl}</b>
            <small>{TEXTOS["risco.horizonte"]}</small>
          </p>
        )}
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
          {notRejected(
            accepted.adequados.length,
            accepted.julgados,
            MODEL_ORDER.length,
          )}
        </p>
      </div>
    </article>
  );
}

/**
 * Os dois níveis lado a lado (a quebra em uma coluna é do kit). Serve ao ativo e à carteira
 * (M2.2b, RF-16); as props opcionais ficam ausentes no ativo: `brlRange` dá a faixa em reais
 * por `alpha`, e `notRejectedKey` troca a frase dos não rejeitados (o padrão é a do ativo).
 */
export function LossSummary<R extends RiskResultBase>({
  results,
  brlRange,
  notRejectedKey = "risco.naoRejeitados",
}: {
  results: readonly R[];
  brlRange?: BrlRange;
  notRejectedKey?: NotRejectedKey;
}) {
  return (
    <div className="ruvor-levels">
      {ALPHAS.map((alpha) => (
        <LevelPanel
          key={alpha}
          results={results}
          alpha={alpha}
          brl={brlRange?.[alpha] ?? null}
          notRejectedKey={notRejectedKey}
        />
      ))}
    </div>
  );
}
