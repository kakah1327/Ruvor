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
