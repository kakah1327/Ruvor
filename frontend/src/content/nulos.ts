/**
 * A atribuição dos nulos dos fundamentos (M1.6c, RF-07): por que um número da seção
 * Fundamentos está vazio, quando o cálculo gravou o porquê.
 *
 * O bloco abaixo é a cópia literal das regras da `fundamentos` — `REASON_NULLS` de
 * `backend/apps/fundamentals/indicators.py`, os campos que só o plano `general` calcula e o
 * único campo que `market_cap_missing` explica. Mudança numa delas é mudança de contrato
 * entre frentes (D-99): `backend/tests/api/test_valores_fundamentos.py` e
 * `frontend/tests/nulos.test.ts` fixam as listas.
 */

import type { Indicator } from "../api/types";
import { TEXTOS } from "./textos";

export const REASON_NULLS = {
  unit: ["price_date", "close", "eps", "bvps", "pe", "pb"],
  stale_statement: ["price_date", "close", "eps", "bvps", "pe", "pb"],
  no_share_count: ["eps", "bvps", "pe", "pb"],
  share_scale_unknown: ["eps", "bvps", "pe", "pb"],
  no_price: ["price_date", "close", "pe", "pb"],
} as const;
export const PLAN_NULLS = [
  "revenue_ttm",
  "ebit_ttm",
  "net_margin",
  "ebit_margin",
  "gross_debt",
  "cash",
  "net_debt",
  "net_debt_to_equity",
] as const; // bank, insurance, unknown
export const MARKET_CAP_NULLS = ["market_cap"] as const;

/**
 * Os valores de `market_cap_missing`: os literais dos `return` de `market_cap()` em
 * `indicators.py`, na ordem do código — a lista que o teste de contrato do backend lê por
 * `ast`.
 */
export const MARKET_CAP_REASONS = [
  "stale_statement",
  "no_share_count",
  "share_scale_unknown",
  "ambiguous_class",
  "no_price",
  "missing_class_price",
] as const;

type PerShareReason = keyof typeof REASON_NULLS;
type MarketCapReason = (typeof MARKET_CAP_REASONS)[number];

/** Um campo numérico do indicador que a seção mostra (ou usa na frase). */
export type NullableField = Exclude<
  keyof Indicator,
  | "calculated_at"
  | "statement"
  | "account_plan"
  | "scope"
  | "per_share_missing"
  | "market_cap_missing"
>;

/** A marca do porquê (`data-null-reason`) e a frase. */
export type NullReason = { code: string; text: string };

function isPerShareReason(value: string): value is PerShareReason {
  return Object.hasOwn(REASON_NULLS, value);
}

function isMarketCapReason(value: string): value is MarketCapReason {
  return (MARKET_CAP_REASONS as readonly string[]).includes(value);
}

/**
 * O porquê de um campo nulo, na ordem do plano: (1) o plano de contas, se não é `general` e o
 * campo é um dos que só o `general` calcula; (2) `per_share_missing`, se o campo está no
 * conjunto que aquele motivo anula; (3) `market_cap_missing`, só para `market_cap`; (4) a
 * frase genérica — os nulos sem motivo gravado, e o valor desconhecido de qualquer lista.
 */
export function nullReason(indicator: Indicator, field: NullableField): NullReason {
  const plan = indicator.account_plan;
  if (plan !== "general" && (PLAN_NULLS as readonly string[]).includes(field)) {
    if (plan === "bank" || plan === "insurance") {
      return { code: `plan:${plan}`, text: TEXTOS["fundamentos.nulo.planoFinanceiro"] };
    }
    if (plan === "unknown") {
      return {
        code: "plan:unknown",
        text: TEXTOS["fundamentos.nulo.planoDesconhecido"],
      };
    }
  }

  const perShare = indicator.per_share_missing;
  if (
    perShare !== null &&
    isPerShareReason(perShare) &&
    (REASON_NULLS[perShare] as readonly string[]).includes(field)
  ) {
    return {
      code: `per_share:${perShare}`,
      text: TEXTOS[`fundamentos.nulo.porAcao.${perShare}`],
    };
  }

  const marketCap = indicator.market_cap_missing;
  if (
    (MARKET_CAP_NULLS as readonly string[]).includes(field) &&
    marketCap !== null &&
    isMarketCapReason(marketCap)
  ) {
    return {
      code: `market_cap:${marketCap}`,
      text: TEXTOS[`fundamentos.nulo.valorMercado.${marketCap}`],
    };
  }

  return { code: "generic", text: TEXTOS["fundamentos.nulo.generico"] };
}
