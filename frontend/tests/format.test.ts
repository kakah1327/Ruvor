/**
 * A formatação pt-BR e o V-07, a conversão do VaR (RF-12).
 */
import { describe, expect, it } from "vitest";

import {
  formatCurrency,
  formatDate,
  formatInstant,
  formatInteger,
  formatPercent,
  toNumber,
} from "../src/format/numbers";
import { formatLoss, lossFromVar } from "../src/format/var";

// O Intl separa o símbolo da moeda por espaço não separável.
const normalize = (s: string): string => s.replace(/ /g, " ");

describe("V-07: a conversão do VaR", () => {
  it('"0.0500000000" mostra 4,9%', () => {
    expect(formatLoss("0.0500000000")).toBe("4,9%");
  });

  it("não mostra o valor cru (5,0%) nem o sinal trocado (5,1%)", () => {
    expect(formatLoss("0.0500000000")).not.toBe("5,0%");
    expect(formatLoss("0.0500000000")).not.toBe("5,1%");
  });

  it("lossFromVar é 1 − e^(−v)", () => {
    expect(lossFromVar(0)).toBe(0);
    expect(lossFromVar(0.05)).toBeCloseTo(0.048770575, 9);
    expect(lossFromVar(Math.log(2))).toBeCloseTo(0.5, 12);
  });

  it("aceita número", () => {
    expect(formatLoss(0.0225742647)).toBe("2,2%");
  });
});

describe("formatação pt-BR", () => {
  it("percentual com vírgula e casas fixas", () => {
    expect(formatPercent(0.1234)).toBe("12,3%");
    expect(formatPercent(0.1234, 2)).toBe("12,34%");
    expect(formatPercent(-0.05, 1)).toBe("-5,0%");
  });

  it("moeda em reais", () => {
    expect(normalize(formatCurrency(1234.5))).toBe("R$ 1.234,50");
  });

  it("inteiro com ponto de milhar", () => {
    expect(formatInteger(1234567)).toBe("1.234.567");
  });

  it("data AAAA-MM-DD vira dd/mm/aaaa, sem mudar de dia", () => {
    expect(formatDate("2026-01-02")).toBe("02/01/2026");
    expect(() => formatDate("02/01/2026")).toThrow();
  });

  it("instante ISO com deslocamento, no fuso dado", () => {
    expect(formatInstant("2026-09-28T18:30:00-03:00", "America/Sao_Paulo")).toBe(
      "28/09/2026 18:30",
    );
    expect(formatInstant("2026-09-28T18:30:00-03:00", "UTC")).toBe("28/09/2026 21:30");
  });

  it("toNumber converte o decimal da API e mantém o nulo", () => {
    expect(toNumber("0.0225742647")).toBe(0.0225742647);
    expect(toNumber(null)).toBeNull();
  });
});
