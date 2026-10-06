/**
 * Os estados da seção do laboratório (M2.4, RF-14): a tabela do plano, como função pura.
 * **A ordem das perguntas é o contrato** — a primeira que casa decide.
 */

import type { Load } from "../api/resource";
import type { Lab } from "../api/types";
import { MIN_SESSIONS } from "../risk/config";

export type LabState =
  | "LOADING"
  | "ERROR"
  | "READY"
  | "FAILED"
  | "PENDING"
  | "INACTIVE"
  | "NO_DECADE"
  | "SHORT"
  | "NO_RISK";

export function labState(load: Load<Lab>): LabState {
  if (load.state === "loading") return "LOADING";
  if (load.state === "error") return "ERROR";
  const lab = load.data;
  if (lab.latest !== null) return "READY";
  if (lab.last_failure !== null) return "FAILED";
  if (lab.pending) return "PENDING";
  if (!lab.active) return "INACTIVE";
  if (lab.decade.first_price_date !== null && !lab.decade.complete) return "NO_DECADE";
  if (lab.decade.complete && lab.decade.sessions < MIN_SESSIONS) return "SHORT";
  return "NO_RISK";
}

/** A nota do estado READY: no máximo uma, nesta ordem (RF-14, linha 3). */
export function readyNote(lab: Lab): "failure" | "engine" | "partial" | null {
  const latest = lab.latest;
  if (latest === null) return null; // fora do READY, não há nota
  if (lab.last_failure !== null) return "failure"; // a rota só o devolve se posterior ao latest
  if (
    lab.active &&
    lab.risk_engine_version !== null &&
    latest.engine_version !== lab.risk_engine_version
  )
    return "engine"; // promete o experimento novo: só com o ativo `active`
  if (latest.status === "partial") return "partial";
  return null;
}

/**
 * A promessa de nova tentativa (estado FAILED e notas `failure`/`partial`): só com `lab.active`
 * — o inativo não passa pelo fecho do risco. A nota do motor, que promete o experimento novo,
 * nem aparece no inativo (`readyNote`).
 */
export function promisesRetry(lab: Lab): boolean {
  return lab.active;
}
