/**
 * V-11 (parte pura): a tabela de decisão dos estados do risco, linha a linha, e o
 * `shouldPoll` (RF-20).
 */
import { describe, expect, it } from "vitest";

import type { ComputeRequest, InProgress, Risk, RiskRun } from "../src/api/types";
import { MIN_SESSIONS } from "../src/risk/config";
import {
  type AssetLoad,
  type PricesLoad,
  riskState,
  shouldPoll,
} from "../src/risk/state";

function run(status: RiskRun["status"]): RiskRun {
  return {
    id: 1,
    calculated_at: "2026-09-28T10:00:00-03:00",
    finished_at: "2026-09-28T10:02:00-03:00",
    status,
    engine_version: "0.3.0",
    seed: 42,
    train_window_days: 504,
    as_of_date: "2026-09-25",
    first_price_date: "2016-09-26",
    price_count: 2480,
    train_count: 504,
    test_count: 1976,
    price_run: {
      id: 7,
      source: "yahoo",
      started_at: "2026-09-28T09:00:00-03:00",
      finished_at: "2026-09-28T09:01:00-03:00",
    },
    requested_models: ["historical"],
    full_recompute: false,
    results: [],
  };
}

const IN_PROGRESS: InProgress = {
  id: 2,
  calculated_at: "2026-09-28T11:00:00-03:00",
  requested_models: ["historical", "parametric"],
  results_written: 1,
  results_expected: 4,
};

function req(status: ComputeRequest["status"], reason = ""): ComputeRequest {
  return {
    id: 3,
    status,
    requested_at: "2026-09-28T11:00:00-03:00",
    finished_at: null,
    reason,
    error: "",
    risk_run_id: null,
  };
}

function risk(parts: Partial<Omit<Risk, "ticker" | "covered">> = {}): Risk {
  return {
    ticker: "ABCD3",
    covered: false,
    latest: null,
    in_progress: null,
    request: null,
    ...parts,
  };
}

const ACTIVE: AssetLoad = { state: "ok", status: "active" };
const INACTIVE: AssetLoad = { state: "ok", status: "inactive" };
const ASSET_LOADING: AssetLoad = { state: "loading" };
const ASSET_ERROR: AssetLoad = { state: "error" };
const prices = (count: number): PricesLoad => ({ state: "ok", count });
const PRICES_LOADING: PricesLoad = { state: "loading" };
const PRICES_ERROR: PricesLoad = { state: "error" };

describe("riskState: a tabela de decisão", () => {
  it("1: latest ok ou partial sem in_progress → E1", () => {
    expect(riskState(ACTIVE, risk({ latest: run("ok") }), prices(2480))).toBe("E1");
    expect(riskState(ACTIVE, risk({ latest: run("partial") }), prices(2480))).toBe(
      "E1",
    );
  });

  it("1: latest ok ou partial com in_progress → E2", () => {
    const body = risk({ latest: run("ok"), in_progress: IN_PROGRESS });
    expect(riskState(ACTIVE, body, prices(2480))).toBe("E2");
    const partial = risk({ latest: run("partial"), in_progress: IN_PROGRESS });
    expect(riskState(ACTIVE, partial, prices(2480))).toBe("E2");
  });

  it("1 vem antes do resto: E1 com ativo inativo, pedido falho e preços carregando", () => {
    const body = risk({
      latest: run("ok"),
      request: req("failed", "falhou na coleta"),
    });
    expect(riskState(INACTIVE, body, PRICES_LOADING)).toBe("E1");
  });

  it("2: latest failed → E3, com e sem in_progress", () => {
    expect(riskState(ACTIVE, risk({ latest: run("failed") }), prices(2480))).toBe("E3");
    const recalc = risk({ latest: run("failed"), in_progress: IN_PROGRESS });
    expect(riskState(ACTIVE, recalc, prices(2480))).toBe("E3");
  });

  it("3: in_progress sem latest → E4, mesmo com pedido na fila", () => {
    expect(riskState(ACTIVE, risk({ in_progress: IN_PROGRESS }), prices(0))).toBe("E4");
    const body = risk({ in_progress: IN_PROGRESS, request: req("running") });
    expect(riskState(ACTIVE, body, prices(0))).toBe("E4");
  });

  it("4: pedido queued ou running → E5", () => {
    expect(riskState(ACTIVE, risk({ request: req("queued") }), prices(0))).toBe("E5");
    expect(riskState(ACTIVE, risk({ request: req("running") }), prices(0))).toBe("E5");
  });

  it("4 vem antes da identidade e da série: E5 com ativo e preços carregando", () => {
    const body = risk({ request: req("queued") });
    expect(riskState(ASSET_LOADING, body, PRICES_LOADING)).toBe("E5");
  });

  it('5: pedido done com motivo "serie curta" → E6', () => {
    const body = risk({ request: req("done", "serie curta (12 pregoes, minimo 503)") });
    expect(riskState(ACTIVE, body, prices(12))).toBe("E6");
  });

  it("6: pedido failed ou expired → E7", () => {
    const failed = risk({ request: req("failed", "falhou na coleta") });
    expect(riskState(ACTIVE, failed, prices(0))).toBe("E7");
    const expired = risk({ request: req("expired", "expirado (30 min)") });
    expect(riskState(ACTIVE, expired, prices(0))).toBe("E7");
  });

  it('7: a reserva — done "calculado" com latest nulo → E8, mesmo com 100 pregões', () => {
    const body = risk({ request: req("done", "calculado") });
    expect(riskState(ACTIVE, body, prices(100))).toBe("E8");
    expect(riskState(ACTIVE, body, prices(2480))).toBe("E8");
  });

  it("7a: sem pedido e identidade carregando → CARREGANDO", () => {
    expect(riskState(ASSET_LOADING, risk(), prices(2480))).toBe("CARREGANDO");
    expect(riskState(ASSET_LOADING, risk(), PRICES_LOADING)).toBe("CARREGANDO");
  });

  it("7b: sem pedido e ativo inativo → E9, inclusive com série curta", () => {
    expect(riskState(INACTIVE, risk(), prices(0))).toBe("E9");
    expect(riskState(INACTIVE, risk(), prices(12))).toBe("E9");
    expect(riskState(INACTIVE, risk(), prices(2480))).toBe("E9");
  });

  it("8: sem pedido e preços carregando → CARREGANDO", () => {
    expect(riskState(ACTIVE, risk(), PRICES_LOADING)).toBe("CARREGANDO");
  });

  it("9: sem pedido e preços com erro → E8", () => {
    expect(riskState(ACTIVE, risk(), PRICES_ERROR)).toBe("E8");
  });

  it("10: 1 a MIN_SESSIONS − 1 pregões → E6b", () => {
    expect(MIN_SESSIONS).toBe(503);
    expect(riskState(ACTIVE, risk(), prices(1))).toBe("E6b");
    expect(riskState(ACTIVE, risk(), prices(502))).toBe("E6b");
  });

  it("11: 0 pregões ou MIN_SESSIONS ou mais → E8", () => {
    expect(riskState(ACTIVE, risk(), prices(0))).toBe("E8");
    expect(riskState(ACTIVE, risk(), prices(503))).toBe("E8");
    expect(riskState(ACTIVE, risk(), prices(2480))).toBe("E8");
  });

  it("identidade com erro segue adiante: 600 pregões → E8, 12 → E6b", () => {
    expect(riskState(ASSET_ERROR, risk(), prices(600))).toBe("E8");
    expect(riskState(ASSET_ERROR, risk(), prices(12))).toBe("E6b");
    expect(riskState(ASSET_ERROR, risk(), PRICES_LOADING)).toBe("CARREGANDO");
  });
});

describe("shouldPoll", () => {
  it("verdadeiro com in_progress ou pedido aberto", () => {
    expect(shouldPoll(risk({ in_progress: IN_PROGRESS }))).toBe(true);
    expect(shouldPoll(risk({ latest: run("ok"), in_progress: IN_PROGRESS }))).toBe(
      true,
    );
    expect(shouldPoll(risk({ request: req("queued") }))).toBe(true);
    expect(shouldPoll(risk({ request: req("running") }))).toBe(true);
  });

  it("falso sem in_progress e com pedido fechado ou nulo", () => {
    expect(shouldPoll(risk())).toBe(false);
    expect(shouldPoll(risk({ latest: run("ok") }))).toBe(false);
    expect(shouldPoll(risk({ request: req("done", "calculado") }))).toBe(false);
    expect(shouldPoll(risk({ request: req("failed", "falhou na coleta") }))).toBe(
      false,
    );
    expect(shouldPoll(risk({ request: req("expired", "expirado (30 min)") }))).toBe(
      false,
    );
  });
});
