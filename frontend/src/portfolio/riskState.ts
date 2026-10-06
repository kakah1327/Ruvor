/**
 * Os sete estados do risco da carteira (M2.2b, RF-09). **A ordem das perguntas é o contrato**:
 * a primeira que casa decide, como a seção de risco do ativo (`risk/state.ts`).
 *
 * 1. carregando — a primeira leitura não voltou, ou o corpo é de outra versão sem erro (a
 *    releitura depois de um `PUT` ainda não voltou);
 * 2. erro — sem corpo e com o erro da primeira leitura, ou o corpo de outra versão com a
 *    releitura em erro: **nunca o resultado da versão anterior** ao lado da composição nova;
 * 3. resultado + recalculando — `latest` `ok`/`partial` **e** `in_progress`;
 * 4. calculando — `in_progress` (com `latest` nulo ou `failed`);
 * 5. pronto — `latest` `ok`/`partial`;
 * 6. falhou — `latest` `failed`;
 * 7. nunca calculado.
 */

import type { ApiError } from "../api/client";
import type { PortfolioProgress, PortfolioRisk, PortfolioRun } from "../api/types";
import type { RiskSource } from "./useRiskSource";

export type PortfolioRiskState =
  | { kind: "loading" }
  | { kind: "error"; error: ApiError } // só a primeira leitura
  | { kind: "result_recalculating"; latest: PortfolioRun; progress: PortfolioProgress }
  | { kind: "calculating"; progress: PortfolioProgress; failed: PortfolioRun | null }
  | { kind: "ready"; latest: PortfolioRun } // ok ou partial
  | { kind: "failed"; latest: PortfolioRun }
  | { kind: "never" };

/** A execução com resultado: `ok` ou `partial`. */
function hasResult(run: PortfolioRun): boolean {
  return run.status === "ok" || run.status === "partial";
}

/** O estado da seção para a carteira na versão `version` (a do corpo `portfolio`). */
export function portfolioRiskState(
  source: RiskSource,
  version: number,
): PortfolioRiskState {
  const { data, firstError } = source;
  const current = data !== null && data.version === version ? data : null;

  if (source.loading) {
    return { kind: "loading" };
  }
  if (current === null) {
    // Sem corpo da versão corrente: com erro, o erro; sem erro, a leitura ainda não voltou (sem
    // corpo nenhum e sem erro fora do carregando, só depois de um 404 — e a página já foi a
    // "não encontrada").
    return firstError === null
      ? { kind: "loading" }
      : { kind: "error", error: firstError };
  }
  const { latest, in_progress: progress } = current;
  if (latest !== null && hasResult(latest) && progress !== null) {
    return { kind: "result_recalculating", latest, progress };
  }
  if (progress !== null) {
    return {
      kind: "calculating",
      progress,
      failed: latest !== null && latest.status === "failed" ? latest : null,
    };
  }
  if (latest !== null && hasResult(latest)) {
    return { kind: "ready", latest };
  }
  if (latest !== null && latest.status === "failed") {
    return { kind: "failed", latest };
  }
  return { kind: "never" };
}

/** A consulta repetida da carteira (D-182): só enquanto há cálculo em andamento. */
export function shouldPollPortfolio(risk: PortfolioRisk): boolean {
  return risk.in_progress !== null;
}
