/**
 * A conversão do VaR (RF-12). O `var_latest` é a magnitude positiva do quantil do retorno
 * logarítmico de 1 dia; a tela mostra a perda em percentual simples, `1 − e^(−VaR)`, com
 * uma casa. A discordância e a tabela usam estas funções; nenhum componente formata VaR
 * por conta própria.
 */

import type { Dec } from "../api/types";
import { formatPercent } from "./numbers";

export const lossFromVar = (v: number): number => 1 - Math.exp(-v);

/** O VaR da API como perda em percentual simples: "0.0500000000" → "4,9%". */
export function formatLoss(value: Dec | number): string {
  return formatPercent(lossFromVar(Number(value)), 1);
}
