/**
 * M2.2b (T5), RF-16: a tabela dos nove e o resumo da perda servem ao ativo e à carteira, pelo
 * tipo base `RiskResultBase`. As props opcionais novas — `lossBrl` na tabela, `brlRange` e
 * `notRejectedKey` no resumo — ficam ausentes no ativo, que segue igual (as suítes da tela do
 * ativo, sem mudança); presentes, a perda em reais aparece pelo texto, ao lado da %.
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  MODEL_ORDER,
  type ModelName,
  type PortfolioRiskResult,
  type RiskResult,
} from "../src/api/types";
import { LossSummary } from "../src/components/LossSummary";
import { ModelTable } from "../src/components/ModelTable";
import { TEXTOS } from "../src/content/textos";
import { formatBrlText } from "../src/portfolio/notional";

function base(model: ModelName, alpha: "0.0500" | "0.0100", index: number) {
  return {
    model_name: model,
    model_category: "traditional" as const,
    alpha,
    hyperparameters: {},
    var_latest: (0.01 + index / 1000).toFixed(10),
    var_mean: "0.0200000000",
    violations: 120,
    expected_violations: "110.900000",
    kupiec_passed: true,
    kupiec_p_value: "0.3000000000",
    christoffersen_passed: true,
    christoffersen_p_value: "0.4000000000",
    dq_passed: true,
    dq_p_value: "0.5000000000",
    adequate: true,
    error: "",
  };
}

const ALPHAS = ["0.0500", "0.0100"] as const;

const PORTFOLIO: PortfolioRiskResult[] = ALPHAS.flatMap((alpha) =>
  MODEL_ORDER.map((model, i) => ({
    ...base(model, alpha, i),
    loss_brl: `${1000 + i}.5`,
  })),
);

const ASSET: RiskResult[] = ALPHAS.flatMap((alpha) =>
  MODEL_ORDER.map((model, i) => ({
    ...base(model, alpha, i),
    basel_zone: "green",
    reused_snapshots: null,
    trained_snapshots: null,
  })),
);

const brlCells = () => [...document.querySelectorAll('[data-part="perda-reais"]')];

afterEach(() => {
  cleanup();
});

describe("ModelTable: lossBrl", () => {
  it("sem lossBrl (o ativo), nenhuma perda em reais", () => {
    render(<ModelTable results={ASSET} />);
    expect(brlCells()).toHaveLength(0);
  });

  it("com lossBrl, a perda em reais de cada célula, pelo texto, no <small> de .ruvor-loss", () => {
    render(<ModelTable results={PORTFOLIO} lossBrl={(r) => r.loss_brl} />);
    const cells = brlCells();
    expect(cells).toHaveLength(18);
    for (const cell of cells) {
      expect(cell.tagName).toBe("SMALL");
      expect(cell.parentElement?.classList.contains("ruvor-loss")).toBe(true);
    }
    const historical = document.querySelector('[data-model="historical"]');
    expect(historical?.querySelector('[data-part="perda-reais"]')?.textContent).toBe(
      formatBrlText("1000.5"),
    );
  });

  it("lossBrl nulo (a carteira sem valor): nada a mais", () => {
    render(<ModelTable results={PORTFOLIO} lossBrl={() => null} />);
    expect(brlCells()).toHaveLength(0);
  });
});

describe("LossSummary: brlRange e notRejectedKey", () => {
  it("sem brlRange (o ativo), nenhuma faixa em reais", () => {
    render(<LossSummary results={ASSET} />);
    expect(brlCells()).toHaveLength(0);
  });

  it("com brlRange, a faixa em reais por nível, logo depois da faixa em %", () => {
    render(
      <LossSummary
        results={PORTFOLIO}
        brlRange={{
          "0.0500": ["1000.00", "2500.50"],
          "0.0100": ["3000.00", "3000.00"],
        }}
      />,
    );
    const at95 = document.querySelector(
      '[data-alpha="0.0500"] [data-part="perda-reais"]',
    ) as HTMLElement;
    const at99 = document.querySelector(
      '[data-alpha="0.0100"] [data-part="perda-reais"]',
    ) as HTMLElement;
    expect(at95.querySelector("b")?.textContent).toBe(
      TEXTOS["risco.faixa"](formatBrlText("1000.00"), formatBrlText("2500.50")),
    );
    // Mínimo igual ao máximo: o valor só, como a faixa em % de um modelo.
    expect(at99.querySelector("b")?.textContent).toBe(formatBrlText("3000.00"));
    expect(at95.previousElementSibling?.classList.contains("ruvor-range")).toBe(true);
  });

  it("um nível sem faixa (nulo) não mostra reais", () => {
    render(
      <LossSummary results={PORTFOLIO} brlRange={{ "0.0500": null, "0.0100": null }} />,
    );
    expect(brlCells()).toHaveLength(0);
  });

  it("sem notRejectedKey, e com a do ativo, a frase do ativo", () => {
    const phrase = TEXTOS["risco.naoRejeitados"](9, 9, 9);
    render(<LossSummary results={ASSET} />);
    const without = [...document.querySelectorAll('[data-phrase="naoRejeitados"]')].map(
      (p) => p.textContent,
    );
    cleanup();
    render(<LossSummary results={ASSET} notRejectedKey="risco.naoRejeitados" />);
    const withKey = [...document.querySelectorAll('[data-phrase="naoRejeitados"]')].map(
      (p) => p.textContent,
    );
    expect(without).toEqual([phrase, phrase]);
    expect(withKey).toEqual(without);
  });
});
