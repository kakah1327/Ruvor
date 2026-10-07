/**
 * M2.2b (T5), V-06 (a ordem): a tabela de decisão de `portfolioRiskState` (RF-09), uma linha por
 * estado — a ordem das perguntas é o contrato, e cada linha monta o caso em que só a pergunta
 * testada decide (o resultado + recalculando tem `latest` `ok` **e** `in_progress`, o que também
 * casaria "calculando" e "pronto") —, a regra da versão (nunca o resultado da versão anterior ao
 * lado da composição nova) e `shouldPollPortfolio`.
 */
import { describe, expect, it } from "vitest";

import { ApiError } from "../src/api/client";
import type { PortfolioProgress, PortfolioRisk, PortfolioRun } from "../src/api/types";
import { portfolioRiskState, shouldPollPortfolio } from "../src/portfolio/riskState";
import type { RiskSource } from "../src/portfolio/useRiskSource";

// ---------------------------------------------------------------- os dados

const VERSION = 2;

function run(
  status: PortfolioRun["status"],
  over: Partial<PortfolioRun> = {},
): PortfolioRun {
  return {
    id: 31,
    version: VERSION,
    status,
    calculated_at: "2026-10-02T18:00:00-03:00",
    finished_at: "2026-10-02T18:02:30-03:00",
    engine_version: "0.5.0",
    seed: 42,
    train_window_days: 252,
    first_date: "2016-10-03",
    as_of_date: "2026-10-02",
    session_count: 2470,
    train_count: 252,
    test_count: 2218,
    requested_models: [],
    series_sha256: "a".repeat(64),
    price_run_id: 7,
    requested_by: { email: "ana@exemplo.com", name: "Ana" },
    results: [],
    summary: [],
    ...over,
  };
}

const PROGRESS: PortfolioProgress = {
  id: 32,
  version: VERSION,
  calculated_at: "2026-10-03T10:00:00-03:00",
  requested_models: ["historical"],
  results_written: 7,
  results_expected: 18,
};

function body(
  latest: PortfolioRun | null,
  inProgress: PortfolioProgress | null,
  version = VERSION,
): PortfolioRisk {
  return {
    portfolio_id: "5b0e6c1e-0000-4000-8000-000000000000",
    version,
    notional: null,
    latest,
    in_progress: inProgress,
  };
}

function source(over: Partial<RiskSource> = {}): RiskSource {
  return {
    data: null,
    firstError: null,
    notFound: false,
    loading: false,
    attempt: 1,
    ...over,
  };
}

const ERROR = new ApiError(503, "unexpected_response", "HTTP 503");

// ---------------------------------------------------------------- a tabela

describe("portfolioRiskState: os sete estados, na ordem do RF-09", () => {
  const OK = run("ok");
  const PARTIAL = run("partial");
  const FAILED = run("failed");

  const rows: [string, RiskSource, string][] = [
    [
      "1 carregando: a primeira leitura não voltou",
      source({ loading: true, attempt: 0 }),
      "loading",
    ],
    [
      "2 erro: sem corpo e com o erro da primeira leitura",
      source({ firstError: ERROR }),
      "error",
    ],
    [
      "3 resultado + recalculando: ok e in_progress",
      source({ data: body(OK, PROGRESS) }),
      "result_recalculating",
    ],
    [
      "3 resultado + recalculando: partial e in_progress",
      source({ data: body(PARTIAL, PROGRESS) }),
      "result_recalculating",
    ],
    [
      "4 calculando: in_progress sem latest",
      source({ data: body(null, PROGRESS) }),
      "calculating",
    ],
    [
      "4 calculando: in_progress com latest failed",
      source({ data: body(FAILED, PROGRESS) }),
      "calculating",
    ],
    ["5 pronto: ok", source({ data: body(OK, null) }), "ready"],
    ["5 pronto: partial", source({ data: body(PARTIAL, null) }), "ready"],
    ["6 falhou: failed", source({ data: body(FAILED, null) }), "failed"],
    ["7 nunca calculado", source({ data: body(null, null) }), "never"],
  ];

  it.each(rows)("%s", (_name, src, kind) => {
    expect(portfolioRiskState(src, VERSION).kind).toBe(kind);
  });

  it("o resultado + recalculando leva o resultado e o andamento", () => {
    expect(portfolioRiskState(source({ data: body(OK, PROGRESS) }), VERSION)).toEqual({
      kind: "result_recalculating",
      latest: OK,
      progress: PROGRESS,
    });
  });

  it("o calculando leva o andamento e a falha anterior, quando há", () => {
    expect(
      portfolioRiskState(source({ data: body(FAILED, PROGRESS) }), VERSION),
    ).toEqual({
      kind: "calculating",
      progress: PROGRESS,
      failed: FAILED,
    });
    expect(portfolioRiskState(source({ data: body(null, PROGRESS) }), VERSION)).toEqual(
      {
        kind: "calculating",
        progress: PROGRESS,
        failed: null,
      },
    );
  });

  it("o erro leva o ApiError", () => {
    expect(portfolioRiskState(source({ firstError: ERROR }), VERSION)).toEqual({
      kind: "error",
      error: ERROR,
    });
  });

  it("pronto e falhou levam o latest", () => {
    expect(portfolioRiskState(source({ data: body(OK, null) }), VERSION)).toEqual({
      kind: "ready",
      latest: OK,
    });
    expect(portfolioRiskState(source({ data: body(FAILED, null) }), VERSION)).toEqual({
      kind: "failed",
      latest: FAILED,
    });
  });

  it("com o corpo da versão corrente, um erro de releitura não muda o estado", () => {
    // O erro de uma consulta repetida mantém o que se mostrava (RF-09).
    expect(
      portfolioRiskState(
        source({ data: body(OK, PROGRESS), firstError: ERROR }),
        VERSION,
      ).kind,
    ).toBe("result_recalculating");
    expect(
      portfolioRiskState(source({ data: body(OK, null), firstError: ERROR }), VERSION)
        .kind,
    ).toBe("ready");
  });
});

describe("a regra da versão: nunca o resultado da versão anterior", () => {
  const OLD = body(run("ok", { version: 1 }), null, 1);

  it("o corpo da versão anterior, sem erro: carregando (a releitura depois do PUT não voltou)", () => {
    expect(portfolioRiskState(source({ data: OLD }), VERSION).kind).toBe("loading");
  });

  it("o corpo da versão anterior com a releitura em erro: o erro", () => {
    expect(
      portfolioRiskState(source({ data: OLD, firstError: ERROR }), VERSION),
    ).toEqual({
      kind: "error",
      error: ERROR,
    });
  });

  it("o mesmo corpo, lido com a versão dele, é o resultado", () => {
    expect(portfolioRiskState(source({ data: OLD }), 1).kind).toBe("ready");
  });

  it("depois do 404 (sem corpo e sem erro): carregando, nunca um estado com resultado", () => {
    expect(portfolioRiskState(source({ notFound: true }), VERSION).kind).toBe(
      "loading",
    );
  });
});

describe("shouldPollPortfolio: só enquanto há in_progress (D-182)", () => {
  it.each([
    ["in_progress sem latest", body(null, PROGRESS), true],
    ["in_progress com resultado", body(run("ok"), PROGRESS), true],
    ["pronto", body(run("ok"), null), false],
    ["falhou", body(run("failed"), null), false],
    ["nunca calculado", body(null, null), false],
  ])("%s → %s", (_name, risk, expected) => {
    expect(shouldPollPortfolio(risk)).toBe(expected);
  });
});
