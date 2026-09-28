/**
 * Os estados da seção de risco (RF-17): a tabela de decisão do plano, como função pura.
 * **A ordem das perguntas é o contrato** — a primeira que casa decide.
 *
 * O `404 asset_not_found` da identidade não chega aqui: a tela inteira vira "ativo não
 * encontrado" (RF-06).
 */

import type { Risk } from "../api/types";
import { MIN_SESSIONS } from "../content/sugestoes";

/** A situação da identidade do ativo (`GET /api/v1/assets/{ticker}`). */
export type AssetLoad =
  | { state: "loading" }
  | { state: "error" }
  | { state: "ok"; status: "active" | "inactive" };

/** A situação da série de preços (`GET /api/v1/assets/{ticker}/prices`). */
export type PricesLoad =
  | { state: "loading" }
  | { state: "error" }
  | { state: "ok"; count: number };

/**
 * O estado decidido. "CARREGANDO" é o skeleton, sem botão (linhas 7a e 8). O E3 com
 * recálculo é o E3 com `risk.in_progress` presente.
 */
export type RiskState =
  | "E1"
  | "E2"
  | "E3"
  | "E4"
  | "E5"
  | "E6"
  | "E6b"
  | "E7"
  | "E8"
  | "E9"
  | "CARREGANDO";

const SHORT_SERIES_PREFIX = "serie curta";

export function riskState(asset: AssetLoad, risk: Risk, prices: PricesLoad): RiskState {
  const { latest, in_progress: inProgress, request } = risk;

  // 1 e 2: há execução fechada.
  if (latest !== null && (latest.status === "ok" || latest.status === "partial")) {
    return inProgress !== null ? "E2" : "E1";
  }
  if (latest !== null && latest.status === "failed") {
    return "E3";
  }
  // 3: calculando.
  if (inProgress !== null) {
    return "E4";
  }
  // 4 a 7: há pedido.
  if (request !== null) {
    if (request.status === "queued" || request.status === "running") {
      return "E5";
    }
    if (request.status === "done" && request.reason.startsWith(SHORT_SERIES_PREFIX)) {
      return "E6";
    }
    if (request.status === "failed" || request.status === "expired") {
      return "E7";
    }
    // 7: `done` "calculado" com `latest` nulo — a reserva do RF-17.
    return "E8";
  }
  // Daqui para baixo, pedido nulo.
  // 7a e 7b: a identidade.
  if (asset.state === "loading") {
    return "CARREGANDO";
  }
  if (asset.state === "ok" && asset.status === "inactive") {
    return "E9";
  }
  // 8 a 11: a série.
  if (prices.state === "loading") {
    return "CARREGANDO";
  }
  if (prices.state === "error") {
    return "E8";
  }
  if (prices.count >= 1 && prices.count <= MIN_SESSIONS - 1) {
    return "E6b";
  }
  return "E8";
}

/** O acompanhamento (RF-20) continua enquanto há execução em andamento ou pedido aberto. */
export function shouldPoll(risk: Risk): boolean {
  return (
    risk.in_progress !== null ||
    risk.request?.status === "queued" ||
    risk.request?.status === "running"
  );
}
