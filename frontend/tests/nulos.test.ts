/**
 * @vitest-environment node
 *
 * V-06, a metade do frontend (M1.6c): as listas fechadas que a tela traduz são as mesmas de
 * `backend/tests/api/test_valores_fundamentos.py`, cada valor tem frase — salvo `general`; `bank`
 * e `insurance` a mesma —, e a frase de um motivo só aparece nos campos do conjunto dele: um
 * `eps` nulo com `per_share_missing = "no_price"` leva a frase genérica, porque o `no_price` não
 * anula o LPA.
 *
 * As listas estão escritas aqui, e não importadas: valor novo em `nulos.ts` sem o teste reprova.
 */
import { describe, expect, it } from "vitest";

import type { Indicator } from "../src/api/types";
import {
  MARKET_CAP_NULLS,
  MARKET_CAP_REASONS,
  type NullableField,
  nullReason,
  PLAN_NULLS,
  REASON_NULLS,
} from "../src/content/nulos";
import { TEXTOS } from "../src/content/textos";

const ACCOUNT_PLAN = ["general", "bank", "insurance", "unknown"] as const;

const PER_SHARE_MISSING: Record<string, readonly string[]> = {
  unit: ["price_date", "close", "eps", "bvps", "pe", "pb"],
  stale_statement: ["price_date", "close", "eps", "bvps", "pe", "pb"],
  no_share_count: ["eps", "bvps", "pe", "pb"],
  share_scale_unknown: ["eps", "bvps", "pe", "pb"],
  no_price: ["price_date", "close", "pe", "pb"],
};

const MARKET_CAP_MISSING = [
  "stale_statement",
  "no_share_count",
  "share_scale_unknown",
  "ambiguous_class",
  "no_price",
  "missing_class_price",
];

// Os campos que só o plano `general` calcula (o bloco do `account_plan` em `indicators.py`).
const SO_GENERAL = [
  "revenue_ttm",
  "ebit_ttm",
  "net_margin",
  "ebit_margin",
  "gross_debt",
  "cash",
  "net_debt",
  "net_debt_to_equity",
];

// Todo campo numérico do indicador: os dezenove da tela, mais a data do preço e as ações.
const CAMPOS: NullableField[] = [
  "revenue_ttm",
  "ebit_ttm",
  "net_income_ttm",
  "equity_parent",
  "total_assets",
  "gross_debt",
  "cash",
  "net_debt",
  "net_margin",
  "ebit_margin",
  "roe",
  "net_debt_to_equity",
  "price_date",
  "close",
  "shares_total",
  "eps",
  "bvps",
  "pe",
  "pb",
  "market_cap",
];

// A PETR4 de 28/09/2026 (o corpo real de /fundamentals), com o valor de mercado presente:
// cada caso muda só o eixo que testa.
const BASE: Indicator = {
  calculated_at: "2026-09-28T08:02:59.205615-03:00",
  statement: { reference_date: "2026-06-30", source: "itr", scope: "consolidated" },
  account_plan: "general",
  scope: "consolidated",
  revenue_ttm: "548493000000.00",
  ebit_ttm: "185746000000.00",
  net_income_ttm: "133376000000.00",
  equity_parent: "480950000000.00",
  total_assets: "1279019000000.00",
  gross_debt: "366533000000.00",
  cash: "53764000000.00",
  net_debt: "312769000000.00",
  net_margin: "0.2431680988",
  ebit_margin: "0.3386478952",
  roe: "0.2773178085",
  net_debt_to_equity: "0.6503150016",
  price_date: "2026-09-25",
  close: "48.070000",
  shares_total: 12888732761,
  eps: "10.348263",
  bvps: "37.315538",
  pe: "4.645224",
  pb: "1.288203",
  per_share_missing: null,
  market_cap: "626283512000.00",
  market_cap_missing: null,
};

const texto = (chave: string): unknown => (TEXTOS as Record<string, unknown>)[chave];

describe("V-06 — as listas são as do contrato", () => {
  it("REASON_NULLS, inteiro", () => {
    expect(REASON_NULLS).toEqual(PER_SHARE_MISSING);
  });

  it("os valores de market_cap_missing, na ordem de market_cap()", () => {
    expect([...MARKET_CAP_REASONS]).toEqual(MARKET_CAP_MISSING);
  });

  it("os campos que só o general calcula", () => {
    expect([...PLAN_NULLS]).toEqual(SO_GENERAL);
  });

  it("market_cap_missing explica só market_cap", () => {
    expect([...MARKET_CAP_NULLS]).toEqual(["market_cap"]);
  });
});

describe("V-06 — cada valor tem frase", () => {
  it.each(Object.keys(PER_SHARE_MISSING))("per_share_missing %s", (motivo) => {
    const frase = texto(`fundamentos.nulo.porAcao.${motivo}`);
    expect(typeof frase).toBe("string");
    expect((frase as string).trim()).not.toBe("");
  });

  it.each(MARKET_CAP_MISSING)("market_cap_missing %s", (motivo) => {
    const frase = texto(`fundamentos.nulo.valorMercado.${motivo}`);
    expect(typeof frase).toBe("string");
    expect((frase as string).trim()).not.toBe("");
  });

  it("account_plan: general sem frase; bank e insurance a mesma; unknown a sua", () => {
    const frase = (plano: (typeof ACCOUNT_PLAN)[number]) =>
      nullReason({ ...BASE, account_plan: plano, revenue_ttm: null }, "revenue_ttm");
    expect(frase("general")).toEqual({
      code: "generic",
      text: TEXTOS["fundamentos.nulo.generico"],
    });
    expect(frase("bank")).toEqual({
      code: "plan:bank",
      text: TEXTOS["fundamentos.nulo.planoFinanceiro"],
    });
    expect(frase("insurance")).toEqual({
      code: "plan:insurance",
      text: TEXTOS["fundamentos.nulo.planoFinanceiro"],
    });
    expect(frase("unknown")).toEqual({
      code: "plan:unknown",
      text: TEXTOS["fundamentos.nulo.planoDesconhecido"],
    });
    expect(TEXTOS["fundamentos.nulo.planoDesconhecido"]).not.toBe(
      TEXTOS["fundamentos.nulo.planoFinanceiro"],
    );
  });
});

describe("V-06 — a frase do motivo só no conjunto dele", () => {
  const casos = Object.entries(PER_SHARE_MISSING).flatMap(([motivo, conjunto]) =>
    CAMPOS.map((campo) => [motivo, campo, conjunto.includes(campo)] as const),
  );

  it.each(casos)(
    "per_share_missing %s, %s nulo: do motivo = %s",
    (motivo, campo, dele) => {
      const r = nullReason(
        { ...BASE, per_share_missing: motivo, [campo]: null },
        campo,
      );
      expect(r.code).toBe(dele ? `per_share:${motivo}` : "generic");
      expect(r.text).toBe(
        dele
          ? texto(`fundamentos.nulo.porAcao.${motivo}`)
          : TEXTOS["fundamentos.nulo.generico"],
      );
    },
  );

  it("no_price num eps nulo: a genérica, não a do motivo", () => {
    const r = nullReason({ ...BASE, per_share_missing: "no_price", eps: null }, "eps");
    expect(r).toEqual({ code: "generic", text: TEXTOS["fundamentos.nulo.generico"] });
    expect(r.text).not.toBe(TEXTOS["fundamentos.nulo.porAcao.no_price"]);
  });

  const casosMercado = MARKET_CAP_MISSING.flatMap((motivo) =>
    CAMPOS.map((campo) => [motivo, campo] as const),
  );

  it.each(casosMercado)("market_cap_missing %s, %s nulo", (motivo, campo) => {
    const r = nullReason({ ...BASE, market_cap_missing: motivo, [campo]: null }, campo);
    expect(r.code).toBe(campo === "market_cap" ? `market_cap:${motivo}` : "generic");
  });

  it.each(ACCOUNT_PLAN.filter((p) => p !== "general"))(
    "account_plan %s: a frase do plano só nos campos que só o general calcula",
    (plano) => {
      for (const campo of CAMPOS) {
        const r = nullReason({ ...BASE, account_plan: plano, [campo]: null }, campo);
        expect(r.code).toBe(SO_GENERAL.includes(campo) ? `plan:${plano}` : "generic");
      }
    },
  );

  it("valor desconhecido de qualquer lista cai na genérica", () => {
    const desconhecido = {
      ...BASE,
      per_share_missing: "novo_motivo",
      market_cap_missing: "novo_motivo",
      eps: null,
      market_cap: null,
    };
    expect(nullReason(desconhecido, "eps").code).toBe("generic");
    expect(nullReason(desconhecido, "market_cap").code).toBe("generic");
  });
});
