/**
 * M2.2b (T5), V-03 — a aritmética dos pesos (RF-06) e do valor em reais, por algarismos, nunca
 * por ponto flutuante: `src/portfolio/weights.ts` e `src/portfolio/notional.ts`.
 */
import { describe, expect, it } from "vitest";

import { formatCurrency } from "../src/format/numbers";
import {
  formatBrlText,
  groupDigits,
  NOTIONAL_MAX_INT_DIGITS,
  notionalToApi,
  parseNotional,
} from "../src/portfolio/notional";
import {
  parseWeight,
  sumCents,
  TOTAL_CENTS,
  weightToApi,
} from "../src/portfolio/weights";

describe("parseWeight: o peso em centésimos, lido por algarismos", () => {
  it.each([
    ["0,29", 29], // parseFloat × 100 truncado daria 28
    ["1,15", 115], // e 114
    ["0,57", 57], // e 56
    ["5,1", 510],
    [",5", 50],
    ["5,", 500],
    ["5", 500],
    ["100", 10_000],
    ["100,00", 10_000],
    ["0,01", 1],
    ["999,99", 99_999],
    ["33,33", 3333],
    ["65.40", 6540], // o ponto vale como a vírgula
    ["  34,59  ", 3459], // espaços nas pontas
    ["\t7,5\n", 750],
    ["0", 0],
    ["007", 700],
  ])("%j → %i", (text, cents) => {
    expect(parseWeight(text)).toBe(cents);
  });

  it.each([
    "",
    "   ",
    ",",
    ".",
    "1000", // mais de 3 algarismos inteiros
    "1,234", // mais de 2 casas
    "0,001",
    "1,2,3",
    "1.2.3",
    "1,2.3",
    "-5",
    "+5",
    "5%",
    "abc",
    "5 0",
    "1e2",
    "Infinity",
    "NaN",
    "５", // algarismo de largura total
  ])("%j não é peso → nulo", (text) => {
    expect(parseWeight(text)).toBeNull();
  });
});

describe("a soma em centésimos inteiros", () => {
  it("0,01 + 65,40 + 34,59 fecha 100% (em ponto flutuante, 100.00000000000001)", () => {
    const cents = ["0,01", "65,40", "34,59"].map(parseWeight) as number[];
    expect(sumCents(cents)).toBe(10_000);
    expect(sumCents(cents) === TOTAL_CENTS).toBe(true);
    // A prova de que o caso é o do ponto flutuante: a soma dos `number` não dá 100.
    expect(0.01 + 65.4 + 34.59).not.toBe(100);
  });

  it("33,33 × 3 não fecha; 33,33 + 33,33 + 33,34 fecha", () => {
    expect(sumCents([3333, 3333, 3333])).toBe(9999);
    expect(sumCents([3333, 3333, 3334])).toBe(TOTAL_CENTS);
  });

  it("vazio soma zero; TOTAL_CENTS é 10.000", () => {
    expect(sumCents([])).toBe(0);
    expect(TOTAL_CENTS).toBe(10_000);
  });
});

describe("weightToApi: os centésimos no texto da API", () => {
  it.each([
    [3333, "33.33"],
    [500, "5.00"],
    [1, "0.01"],
    [29, "0.29"],
    [10_000, "100.00"],
    [510, "5.10"],
  ])("%i → %j", (cents, text) => {
    expect(weightToApi(cents)).toBe(text);
  });

  it("ida e volta: o texto digitado chega à API com 2 casas", () => {
    expect(weightToApi(parseWeight("5,") as number)).toBe("5.00");
    expect(weightToApi(parseWeight(",5") as number)).toBe("0.50");
    expect(weightToApi(parseWeight("1,15") as number)).toBe("1.15");
  });
});

describe("parseNotional: o valor em reais, pelo texto", () => {
  it("9.999.999.999.999.999,99 exato: 16 algarismos inteiros, sem passar por Number", () => {
    const n = parseNotional("9.999.999.999.999.999,99");
    expect(n).toEqual({ int: "9999999999999999", dec: "99" });
    expect(notionalToApi(n as NonNullable<typeof n>)).toBe("9999999999999999.99");
    // Em ponto flutuante, o mesmo valor não sobrevive:
    expect(String(Number("9999999999999999.99"))).not.toBe("9999999999999999.99");
  });

  it("17 algarismos inteiros → nulo, nas duas formas", () => {
    expect(NOTIONAL_MAX_INT_DIGITS).toBe(16);
    expect(parseNotional("10000000000000000")).toBeNull();
    expect(parseNotional("10.000.000.000.000.000,00")).toBeNull();
    expect(parseNotional("99999999999999999,99")).toBeNull();
  });

  it('"10000," → "10000.00"', () => {
    const n = parseNotional("10000,");
    expect(n).toEqual({ int: "10000", dec: "00" });
    expect(notionalToApi(n as NonNullable<typeof n>)).toBe("10000.00");
  });

  it.each([
    ["10.000,00", "10000.00"],
    ["10.000", "10000.00"], // o ponto com três algarismos é milhar
    ["1.000", "1000.00"],
    ["10.5", "10.50"], // com um ou dois, é centavo
    ["10.50", "10.50"],
    ["10000,5", "10000.50"],
    ["10000.50", "10000.50"],
    ["250.000,00", "250000.00"],
    ["250000", "250000.00"],
    ["  50.000,00 ", "50000.00"],
    ["0,01", "0.01"],
    ["007", "7.00"], // zeros à esquerda saem
    ["0010,5", "10.50"],
  ])("%j → %j", (text, api) => {
    const n = parseNotional(text);
    expect(n).not.toBeNull();
    expect(notionalToApi(n as NonNullable<typeof n>)).toBe(api);
  });

  it.each([
    "",
    "  ",
    "0",
    "0,00",
    "000,0",
    "10.000,999", // mais de 2 casas
    "10,999",
    "1.00.000", // milhar fora do lugar
    "10.000.5", // o ponto como centavo depois do milhar
    "10,000,00",
    ",50", // sem parte inteira
    "-10",
    "R$ 10",
    "1e5",
    "10 000",
    "abc",
  ])("%j → nulo", (text) => {
    expect(parseNotional(text)).toBeNull();
  });
});

describe("groupDigits e formatBrlText: a exibição pelo texto", () => {
  it.each([
    ["0", "0"],
    ["100", "100"],
    ["1000", "1.000"],
    ["250000", "250.000"],
    ["9999999999999999", "9.999.999.999.999.999"],
  ])("groupDigits(%j) → %j", (int, grouped) => {
    expect(groupDigits(int)).toBe(grouped);
  });

  it.each(["0.00", "0.01", "1234.50", "100000.00", "4915.37", "-12.30"])(
    "formatBrlText(%j) é o que o Intl mostra",
    (value) => {
      expect(formatBrlText(value)).toBe(formatCurrency(Number(value)));
    },
  );

  it("16 algarismos inteiros, exatos (o Intl, por Number, arredondaria)", () => {
    expect(formatBrlText("9999999999999999.99")).toBe("R$ 9.999.999.999.999.999,99");
    expect(formatCurrency(Number("9999999999999999.99"))).not.toBe(
      "R$ 9.999.999.999.999.999,99",
    );
  });
});
