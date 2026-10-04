/**
 * V-12 do M5.1 (estados e visibilidade): a tabela de `returnsState`, uma linha por estado e pelo
 * R1 intermediário, com as fronteiras da série em 0, 1, 502 e 503 — a ordem das perguntas é o
 * contrato (RF-16) —; e a de `forecastView` (RF-18), cada `kind`, com a data igual a hoje
 * (`show`) e a de ontem (`past`).
 */
import { describe, expect, it } from "vitest";
import { ApiError } from "../src/api/client";
import type { Load } from "../src/api/resource";
import type { ReturnResult, ReturnRun, Returns } from "../src/api/types";
import { forecastView, returnsState } from "../src/returns/state";
import { MIN_SESSIONS } from "../src/risk/config";
import type { AssetLoad, PricesLoad } from "../src/risk/state";

// ---------------------------------------------------------------- os dados

/** O `ar_1` do ITUB4 na foto da fase A (`docs/mockups/M5.1/returns-ITUB4.js`). */
function result(over: Partial<ReturnResult> = {}): ReturnResult {
  return {
    model_name: "ar_1",
    hyperparameters: {
      lags: 1,
      window: "expanding",
      estimator: "ols",
      intercept: true,
    },
    mse: "0.0003402168",
    mse_reference: "0.0003403580",
    r2_os: "0.0004148825",
    direction_days: 2217,
    hit_rate: "0.5056382499",
    up_share: "0.5105999098",
    forecast_up_share: "0.7027514659",
    dm_statistic: "0.1049938768",
    dm_p_value: "0.4581903337",
    cw_statistic: "1.6533993320",
    cw_p_value: "0.0491248094",
    pt_statistic: "0.1381045634",
    pt_p_value: "0.4450788896",
    beats_reference: false,
    direction_skill: false,
    next_forecast: "-0.0005241821",
    next_forecast_date: "2026-10-05",
    error: "",
    ...over,
  };
}

/** O resultado com `error`: todo número, a data e os dois booleanos nulos. */
const FAILED = result({
  mse: null,
  mse_reference: null,
  r2_os: null,
  direction_days: null,
  hit_rate: null,
  up_share: null,
  forecast_up_share: null,
  dm_statistic: null,
  dm_p_value: null,
  cw_statistic: null,
  cw_p_value: null,
  pt_statistic: null,
  pt_p_value: null,
  beats_reference: null,
  direction_skill: null,
  next_forecast: null,
  next_forecast_date: null,
  error: "matriz singular no trecho 4",
});

const RUN: ReturnRun = {
  calculated_at: "2026-10-04T10:05:12.724649-03:00",
  engine_version: "0.5.0",
  as_of_date: "2026-10-02",
  first_price_date: "2016-09-22",
  price_count: 2499,
  train_count: 252,
  test_count: 2246,
  train_window_days: 252,
  price_run: {
    id: 20,
    source: "yahoo-chart",
    started_at: "2026-10-02T21:44:53.709597-03:00",
    finished_at: "2026-10-02T21:44:56.619518-03:00",
  },
  results: [result()],
};

const LOADING: Load<Returns> = { state: "loading" };
const ERROR: Load<Returns> = {
  state: "error",
  error: new ApiError(500, "internal_error", "falhou"),
};
const WITH_LATEST: Load<Returns> = {
  state: "ok",
  data: { ticker: "ITUB4", latest: RUN },
};
const NO_LATEST: Load<Returns> = {
  state: "ok",
  data: { ticker: "ITUB4", latest: null },
};

const ACTIVE: AssetLoad = { state: "ok", status: "active" };
const INACTIVE: AssetLoad = { state: "ok", status: "inactive" };
const ASSET_LOADING: AssetLoad = { state: "loading" };
const ASSET_ERROR: AssetLoad = { state: "error" };

const count = (n: number): PricesLoad => ({ state: "ok", count: n });
const PRICES_LOADING: PricesLoad = { state: "loading" };
const PRICES_ERROR: PricesLoad = { state: "error" };

// ---------------------------------------------------------------- returnsState

describe("V-12 — returnsState, na ordem do RF-16", () => {
  it("o piso da série é o do risco", () => {
    expect(MIN_SESSIONS).toBe(503);
  });

  it.each<[string, AssetLoad, Load<Returns>, PricesLoad, string]>([
    ["o /returns carregando", ACTIVE, LOADING, count(2499), "R1"],
    [
      "o /returns carregando, com o resto em erro",
      ASSET_ERROR,
      LOADING,
      PRICES_ERROR,
      "R1",
    ],
    ["o /returns em erro", ACTIVE, ERROR, count(2499), "R2"],
    ["o /returns em erro, no inativo", INACTIVE, ERROR, count(0), "R2"],
    ["com latest", ACTIVE, WITH_LATEST, count(2499), "R3"],
    ["com latest, no inativo", INACTIVE, WITH_LATEST, count(2499), "R3"],
    ["com latest, com o /prices em erro", ACTIVE, WITH_LATEST, PRICES_ERROR, "R3"],
    [
      "com latest, com a identidade carregando",
      ASSET_LOADING,
      WITH_LATEST,
      count(0),
      "R3",
    ],
    [
      "o intermediário: sem latest, a identidade carregando",
      ASSET_LOADING,
      NO_LATEST,
      count(2499),
      "R1",
    ],
    [
      "o intermediário: sem latest, o /prices carregando",
      ACTIVE,
      NO_LATEST,
      PRICES_LOADING,
      "R1",
    ],
    ["o intermediário vem antes do inativo", INACTIVE, NO_LATEST, PRICES_LOADING, "R1"],
    ["inativo, sem latest", INACTIVE, NO_LATEST, count(2499), "R4"],
    ["inativo, sem latest, sem preço", INACTIVE, NO_LATEST, count(0), "R4"],
    ["inativo, sem latest, o /prices em erro", INACTIVE, NO_LATEST, PRICES_ERROR, "R4"],
    ["o /prices em erro, sem latest", ACTIVE, NO_LATEST, PRICES_ERROR, "R5"],
    [
      "o /prices em erro, a identidade em erro",
      ASSET_ERROR,
      NO_LATEST,
      PRICES_ERROR,
      "R5",
    ],
    ["0 pregões", ACTIVE, NO_LATEST, count(0), "R6"],
    ["0 pregões, a identidade em erro", ASSET_ERROR, NO_LATEST, count(0), "R6"],
    ["1 pregão", ACTIVE, NO_LATEST, count(1), "R7"],
    ["502 pregões", ACTIVE, NO_LATEST, count(MIN_SESSIONS - 1), "R7"],
    ["503 pregões", ACTIVE, NO_LATEST, count(MIN_SESSIONS), "R8"],
    ["2.499 pregões", ACTIVE, NO_LATEST, count(2499), "R8"],
  ])("%s", (_caso, asset, returns, prices, expected) => {
    expect(returnsState(asset, returns, prices)).toBe(expected);
  });
});

// ---------------------------------------------------------------- forecastView

describe("V-12 — forecastView (RF-18)", () => {
  const TODAY = "2026-10-05";

  it("a data igual a hoje: mostra", () => {
    expect(forecastView(ACTIVE, result(), TODAY)).toEqual({ kind: "show" });
  });

  it("a data depois de hoje: mostra", () => {
    expect(forecastView(ACTIVE, result(), "2026-10-04")).toEqual({ kind: "show" });
  });

  it("a data de ontem: passou, com a data", () => {
    expect(forecastView(ACTIVE, result(), "2026-10-06")).toEqual({
      kind: "past",
      date: "2026-10-05",
    });
  });

  it("o ativo inativo: sem o número, com a data futura ou passada", () => {
    expect(forecastView(INACTIVE, result(), TODAY)).toEqual({ kind: "inactive" });
    expect(forecastView(INACTIVE, result(), "2026-10-06")).toEqual({
      kind: "inactive",
    });
  });

  it.each<[string, AssetLoad]>([
    ["carregando", ASSET_LOADING],
    ["em erro", ASSET_ERROR],
  ])("a identidade %s: pendente, sem frase de estado", (_caso, asset) => {
    expect(forecastView(asset, result(), TODAY)).toEqual({ kind: "pending_identity" });
  });

  it("o resultado com error: nenhuma, nem no inativo nem com a identidade pendente", () => {
    expect(forecastView(ACTIVE, FAILED, TODAY)).toEqual({ kind: "none" });
    expect(forecastView(INACTIVE, FAILED, TODAY)).toEqual({ kind: "none" });
    expect(forecastView(ASSET_LOADING, FAILED, TODAY)).toEqual({ kind: "none" });
  });

  it("sem número ou sem data, mesmo sem error: nenhuma", () => {
    expect(forecastView(ACTIVE, result({ next_forecast: null }), TODAY)).toEqual({
      kind: "none",
    });
    expect(forecastView(ACTIVE, result({ next_forecast_date: null }), TODAY)).toEqual({
      kind: "none",
    });
  });
});
