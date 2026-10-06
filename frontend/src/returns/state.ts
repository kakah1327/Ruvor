/**
 * Os estados da seção do retorno (M5.1, RF-16) e a visibilidade da previsão do próximo pregão
 * (RF-18): a tabela do plano, como funções puras. **A ordem das perguntas é o contrato** — a
 * primeira que casa decide.
 */

import type { Load } from "../api/resource";
import type { ReturnResult, Returns } from "../api/types";
import { MIN_SESSIONS } from "../risk/config";
import type { AssetLoad, PricesLoad } from "../risk/state";

export type ReturnsState =
  | "R1" // carregando (inclusive o intermediário)
  | "R2" // erro do /returns
  | "R3" // resultado
  | "R4" // inativo, sem latest
  | "R5" // /prices em erro, sem latest
  | "R6" // não coberto: 0 pregões
  | "R7" // série curta: 1..MIN_SESSIONS-1
  | "R8"; // ainda não calculado: >= MIN_SESSIONS

export function returnsState(
  asset: AssetLoad,
  returns: Load<Returns>,
  prices: PricesLoad,
): ReturnsState {
  if (returns.state === "loading") return "R1";
  if (returns.state === "error") return "R2";
  if (returns.data.latest !== null) return "R3";
  if (asset.state === "loading" || prices.state === "loading") return "R1"; // o intermediário, antes do R4 (spec)
  if (asset.state === "ok" && asset.status === "inactive") return "R4";
  if (prices.state === "error") return "R5";
  if (prices.count === 0) return "R6";
  if (prices.count <= MIN_SESSIONS - 1) return "R7";
  return "R8";
}

export type ForecastView =
  | { kind: "show" } // o número, a referência, a data
  | { kind: "inactive" } // ativo inativo
  | { kind: "pending_identity" } // identidade carregando ou em erro: sem o número, sem frase de estado
  | { kind: "past"; date: string } // a data já passou
  | { kind: "none" }; // error no resultado: sem previsão

/**
 * `today` é o `AAAA-MM-DD` de hoje no fuso do navegador, que a tela passa; a função não lê
 * relógio. A comparação é de texto ISO, que ordena como data.
 */
export function forecastView(
  asset: AssetLoad,
  result: ReturnResult,
  today: string,
): ForecastView {
  if (
    result.error !== "" ||
    result.next_forecast === null ||
    result.next_forecast_date === null
  )
    return { kind: "none" };
  if (asset.state !== "ok") return { kind: "pending_identity" };
  if (asset.status === "inactive") return { kind: "inactive" };
  if (result.next_forecast_date < today)
    return { kind: "past", date: result.next_forecast_date };
  return { kind: "show" };
}
