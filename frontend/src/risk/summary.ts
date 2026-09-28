/**
 * O resumo do risco por nível: a discordância entre os modelos (RF-13) e os modelos que os
 * testes não rejeitaram (RF-14), sem eleger nenhum (D-65).
 */

import { MODEL_ORDER, type ModelName, type RiskResult } from "../api/types";
import { lossFromVar } from "../format/var";

export type Alpha = RiskResult["alpha"];

export type Discordancia = { min: number; max: number; n: number; total: number };

/**
 * A menor e a maior perda (RF-12, já convertida por `lossFromVar`) sobre os resultados do
 * nível com `var_latest` não nulo. `n` é quantos entraram; `total` é sempre o tamanho de
 * MODEL_ORDER — um modelo sem linha, possível numa execução `partial`, conta como não
 * calculado. Nulo quando nenhum entrou.
 */
export function discordancia(
  results: readonly RiskResult[],
  alpha: Alpha,
): Discordancia | null {
  const losses = results
    .filter((r) => r.alpha === alpha && r.var_latest !== null)
    .map((r) => lossFromVar(Number(r.var_latest)));
  if (losses.length === 0) {
    return null;
  }
  return {
    min: Math.min(...losses),
    max: Math.max(...losses),
    n: losses.length,
    total: MODEL_ORDER.length,
  };
}

export type NaoRejeitados = { adequados: ModelName[]; julgados: number };

/**
 * Os modelos com `adequate = true` no nível, na ordem de MODEL_ORDER — nunca na ordem de
 * chegada nem por valor. `julgados` conta os `adequate` não nulos.
 */
export function naoRejeitados(
  results: readonly RiskResult[],
  alpha: Alpha,
): NaoRejeitados {
  const level = results.filter((r) => r.alpha === alpha);
  const adequados = MODEL_ORDER.filter((model) =>
    level.some((r) => r.model_name === model && r.adequate === true),
  );
  const julgados = level.filter((r) => r.adequate !== null).length;
  return { adequados, julgados };
}
