/**
 * Formatação pt-BR. Toda função recebe número já convertido (a API manda decimal como
 * string: `toNumber` faz a conversão, e só na hora de formatar ou calcular).
 */

import type { Dec } from "../api/types";

/** O decimal da API como número; nulo continua nulo. */
export function toNumber(value: Dec | null): number | null {
  return value === null ? null : Number(value);
}

const percentFormats = new Map<number, Intl.NumberFormat>();

/** Fração como percentual: 0.049 → "4,9%", com `digits` casas fixas. */
export function formatPercent(value: number, digits = 1): string {
  let format = percentFormats.get(digits);
  if (format === undefined) {
    format = new Intl.NumberFormat("pt-BR", {
      style: "percent",
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
    percentFormats.set(digits, format);
  }
  return format.format(value);
}

const currency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** Valor em reais: 1234.5 → "R$ 1.234,50". */
export function formatCurrency(value: number): string {
  return currency.format(value);
}

const currencyWhole = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

/** Valor em reais sem centavos, para o rótulo de eixo: 1234.5 → "R$ 1.235". */
export function formatCurrencyWhole(value: number): string {
  return currencyWhole.format(value);
}

/**
 * O sinal de menos tipográfico (U+2212) no lugar do hífen que o `Intl` põe à frente do
 * número negativo, como nos mockups: "-0,5%" → "−0,5%".
 */
export function typographicMinus(text: string): string {
  return text.replace(/^-/, "−");
}

const signedPercentFormats = new Map<number, Intl.NumberFormat>();

/** Fração como percentual com sinal (o zero sem sinal), e o menos tipográfico: "+5%", "−5%". */
export function formatSignedPercent(value: number, digits = 1): string {
  let format = signedPercentFormats.get(digits);
  if (format === undefined) {
    format = new Intl.NumberFormat("pt-BR", {
      style: "percent",
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
      signDisplay: "exceptZero",
    });
    signedPercentFormats.set(digits, format);
  }
  return typographicMinus(format.format(value));
}

const integer = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

/** Inteiro com separador de milhar: 1234567 → "1.234.567". */
export function formatInteger(value: number): string {
  return integer.format(value);
}

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Data da API (AAAA-MM-DD) como dd/mm/aaaa. Pela string, sem `Date`: uma data sem hora
 * lida por `Date` vira meia-noite UTC e muda de dia a oeste de Greenwich.
 */
export function formatDate(value: string): string {
  const match = ISO_DATE.exec(value);
  if (match === null) {
    throw new Error(`data fora do formato AAAA-MM-DD: ${value}`);
  }
  const [, year, month, day] = match;
  return `${day}/${month}/${year}`;
}

/**
 * Instante da API (ISO com deslocamento) como "dd/mm/aaaa hh:mm", no fuso do navegador —
 * ou no `timeZone` dado.
 */
export function formatInstant(value: string, timeZone?: string): string {
  const instant = new Date(value);
  if (Number.isNaN(instant.getTime())) {
    throw new Error(`instante inválido: ${value}`);
  }
  const parts = new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZone,
  }).formatToParts(instant);
  const part = (type: Intl.DateTimeFormatPartTypes): string =>
    parts.find((p) => p.type === type)?.value ?? "";
  return `${part("day")}/${part("month")}/${part("year")} ${part("hour")}:${part("minute")}`;
}

const decimalFormats = new Map<number, Intl.NumberFormat>();

/** Número com `digits` casas fixas, sem unidade: 0.8512 → "0,85" (com 2). */
export function formatDecimal(value: number, digits: number): string {
  let format = decimalFormats.get(digits);
  if (format === undefined) {
    format = new Intl.NumberFormat("pt-BR", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
    decimalFormats.set(digits, format);
  }
  return format.format(value);
}

const currencyPrecise = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 6,
});

/**
 * Valor em reais com até seis casas, para o provento por ação, que a API guarda com seis:
 * 0.0217 → "R$ 0,0217".
 */
export function formatCurrencyPrecise(value: number): string {
  return currencyPrecise.format(value);
}

/** As unidades do valor abreviado, da menor para a maior. */
const COMPACT_UNITS = [
  [1e3, "mil"],
  [1e6, "mi"],
  [1e9, "bi"],
  [1e12, "tri"],
] as const;

/**
 * Valor em reais abreviado (M1.6c, "Os valores em reais"): abaixo de mil, inteiro ("R$ 950");
 * depois "R$ 12,3 mil", "R$ 46,8 mi", "R$ 217,8 bi" e "R$ 2,7 tri", com uma casa; negativo
 * com o menos tipográfico à frente ("−R$ 8,2 bi"), como o `fCompact` do mockup aprovado.
 *
 * A unidade é escolhida **depois do arredondamento**: 999.960.000 não sai "R$ 1.000,0 mi",
 * sobe para "R$ 1,0 bi" — e 999,6 não sai "R$ 1.000", sobe para "R$ 1,0 mil". A forma
 * inteira, para o `aria-label`, é a de `formatCurrency` com `typographicMinus`.
 */
export function formatCompactCurrency(value: number): string {
  const sign = value < 0 ? "−" : "";
  const abs = Math.abs(value);
  if (Math.round(abs) < 1e3) {
    return `${sign}${currencyWhole.format(abs)}`;
  }
  // A menor unidade em que o valor arredondado fica abaixo de mil; acima disso, "tri".
  let chosen: { scaled: number; unit: string } = { scaled: 0, unit: "" };
  for (const [base, unit] of COMPACT_UNITS) {
    chosen = { scaled: Math.round((abs / base) * 10) / 10, unit };
    if (chosen.scaled < 1e3) break;
  }
  return `${sign}R$ ${formatDecimal(chosen.scaled, 1)} ${chosen.unit}`;
}
