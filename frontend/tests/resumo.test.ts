/**
 * V-08 (a discordância) e V-09 na parte de função (os não rejeitados, na ordem fixa).
 */
import { describe, expect, it } from "vitest";

import { MODEL_ORDER, type ModelName, type RiskResult } from "../src/api/types";
import { lossFromVar } from "../src/format/var";
import { discordancia, naoRejeitados } from "../src/risk/summary";

// MODEL_ORDER e ModelName são o mesmo conjunto: cada lado cabe no outro.
type OrderName = (typeof MODEL_ORDER)[number];
const _orderInName: ModelName[] = [...MODEL_ORDER];
const _nameInOrder = (m: ModelName): OrderName => m;
void _orderInName;
void _nameInOrder;

const CATEGORY: Record<ModelName, RiskResult["model_category"]> = {
  historical: "traditional",
  parametric: "traditional",
  monte_carlo: "traditional",
  garch_1_1: "garch",
  egarch: "garch",
  lstm: "ml",
  gru: "ml",
  garchnet: "ml",
  caviar: "ml",
};

function result(
  model_name: ModelName,
  alpha: RiskResult["alpha"],
  var_latest: string | null,
  adequate: boolean | null,
): RiskResult {
  return {
    model_name,
    model_category: CATEGORY[model_name],
    alpha,
    hyperparameters: {},
    var_latest,
    var_mean: var_latest,
    violations: var_latest === null ? null : 10,
    expected_violations: var_latest === null ? null : "10.000000",
    kupiec_passed: adequate,
    kupiec_p_value: null,
    christoffersen_passed: adequate,
    christoffersen_p_value: null,
    dq_passed: adequate,
    dq_p_value: null,
    basel_zone: null,
    adequate,
    error: var_latest === null ? "falhou" : "",
    reused_snapshots: null,
    trained_snapshots: null,
  };
}

// Os nove modelos nos dois níveis, com VaR crescente na MODEL_ORDER a 95%.
function fullRun(): RiskResult[] {
  return MODEL_ORDER.flatMap((model, i) => [
    result(model, "0.0500", (0.02 + i * 0.001).toFixed(10), i % 2 === 0),
    result(model, "0.0100", (0.04 + i * 0.001).toFixed(10), i % 3 === 0),
  ]);
}

// A ordem da API: `model_name` alfabético, depois `-alpha` (backend/apps/api/views.py).
function apiOrder(results: RiskResult[]): RiskResult[] {
  return [...results].sort((a, b) =>
    a.model_name === b.model_name
      ? Number(b.alpha) - Number(a.alpha)
      : a.model_name < b.model_name
        ? -1
        : 1,
  );
}

// Embaralhamento determinístico: um gerador congruencial com semente fixa.
function shuffled<T>(items: readonly T[], seed: number): T[] {
  const out = [...items];
  let state = seed;
  for (let i = out.length - 1; i > 0; i--) {
    state = (state * 1103515245 + 12345) % 2147483648;
    const j = state % (i + 1);
    [out[i], out[j]] = [out[j] as T, out[i] as T];
  }
  return out;
}

describe("discordancia (V-08)", () => {
  it("a faixa sobre os nove, já convertida", () => {
    const d = discordancia(fullRun(), "0.0500");
    expect(d).toEqual({
      min: lossFromVar(0.02),
      max: lossFromVar(0.028),
      n: 9,
      total: 9,
    });
  });

  it("com um var_latest nulo no meio, n é 8 e o mínimo não é 0", () => {
    const results = fullRun().map((r) =>
      r.model_name === "garch_1_1" && r.alpha === "0.0500"
        ? result("garch_1_1", "0.0500", null, null)
        : r,
    );
    const d = discordancia(results, "0.0500");
    expect(d?.n).toBe(8);
    expect(d?.total).toBe(9);
    expect(d?.min).toBe(lossFromVar(0.02));
    expect(d?.min).not.toBe(0);
  });

  it("dois falhos: 7 de 9", () => {
    const results = fullRun().map((r) =>
      (r.model_name === "lstm" || r.model_name === "gru") && r.alpha === "0.0100"
        ? result(r.model_name, "0.0100", null, null)
        : r,
    );
    const d = discordancia(results, "0.0100");
    expect(d?.n).toBe(7);
    expect(d?.total).toBe(9);
  });

  it("com um modelo sem linha (execução partial), total continua 9", () => {
    const results = fullRun().filter((r) => r.model_name !== "caviar");
    const d = discordancia(results, "0.0500");
    expect(d?.n).toBe(8);
    expect(d?.total).toBe(9);
  });

  it("um modelo só: mínimo igual ao máximo", () => {
    const d = discordancia(
      [result("historical", "0.0100", "0.0500000000", true)],
      "0.0100",
    );
    expect(d).toEqual({
      min: lossFromVar(0.05),
      max: lossFromVar(0.05),
      n: 1,
      total: 9,
    });
  });

  it("nenhum não nulo: nulo", () => {
    const results = MODEL_ORDER.map((m) => result(m, "0.0500", null, null));
    expect(discordancia(results, "0.0500")).toBeNull();
    expect(discordancia([], "0.0500")).toBeNull();
  });

  it("só olha o nível pedido", () => {
    const d95 = discordancia(fullRun(), "0.0500");
    const d99 = discordancia(fullRun(), "0.0100");
    expect(d99?.min).toBe(lossFromVar(0.04));
    expect(d95?.max).toBeLessThan(d99?.min ?? 0);
  });
});

describe("naoRejeitados (V-09)", () => {
  const expected95: ModelName[] = [
    "historical",
    "monte_carlo",
    "egarch",
    "gru",
    "caviar",
  ];
  const expected99: ModelName[] = ["historical", "garch_1_1", "gru"];

  it("na MODEL_ORDER, com a entrada na ordem da API", () => {
    const input = apiOrder(fullRun());
    expect(input[0]?.model_name).toBe("caviar");
    expect(naoRejeitados(input, "0.0500")).toEqual({
      adequados: expected95,
      julgados: 9,
    });
    expect(naoRejeitados(input, "0.0100")).toEqual({
      adequados: expected99,
      julgados: 9,
    });
  });

  it("na MODEL_ORDER, com a entrada embaralhada", () => {
    for (const seed of [1, 7, 42, 2026]) {
      const input = shuffled(fullRun(), seed);
      expect(naoRejeitados(input, "0.0500").adequados).toEqual(expected95);
      expect(naoRejeitados(input, "0.0100").adequados).toEqual(expected99);
    }
  });

  it("a ordem não muda quando os valores mudam", () => {
    const reversed = fullRun().map((r) =>
      result(
        r.model_name,
        r.alpha,
        (0.09 - MODEL_ORDER.indexOf(r.model_name) * 0.005).toFixed(10),
        r.adequate,
      ),
    );
    expect(naoRejeitados(reversed, "0.0500").adequados).toEqual(expected95);
  });

  it("adequate nulo não é julgado e não conta como reprovado", () => {
    const results = fullRun().map((r) =>
      r.alpha === "0.0500" && (r.model_name === "historical" || r.model_name === "lstm")
        ? { ...r, adequate: null }
        : r,
    );
    const out = naoRejeitados(results, "0.0500");
    expect(out.julgados).toBe(7);
    expect(out.adequados).toEqual(["monte_carlo", "egarch", "gru", "caviar"]);
  });

  it("nenhum adequado: lista vazia", () => {
    const results = MODEL_ORDER.map((m) => result(m, "0.0100", "0.03", false));
    expect(naoRejeitados(results, "0.0100")).toEqual({ adequados: [], julgados: 9 });
  });
});
