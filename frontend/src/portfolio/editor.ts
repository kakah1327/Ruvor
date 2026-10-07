/**
 * O editor da composição (RF-05, RF-06), só funções puras: as linhas, as conferências do cliente,
 * a soma ao vivo e a leitura do `400 invalid_holdings` — como no `lista.html` aprovado.
 *
 * **O texto digitado é o valor do campo, e nada aqui o reescreve**: os centésimos saem dele por
 * `parseWeight` (`weights.ts`), a soma é a de inteiros contra `TOTAL_CENTS`, e o peso só vira o
 * texto da API (`weightToApi`) no corpo do pedido. O editor nunca preenche, arredonda nem
 * distribui (D-116 item 3).
 */

import { ApiError } from "../api/client";
import { TEXTOS } from "../content/textos";
import { formatInteger } from "../format/numbers";
import { groupDigits } from "./notional";
import { parseWeight, sumCents, TOTAL_CENTS, weightToApi } from "./weights";

/** De 2 a 20 ações (`MIN_HOLDINGS`, `MAX_HOLDINGS` de `backend/apps/portfolios/services.py`). */
export const MIN_HOLDINGS = 2;
export const MAX_HOLDINGS = 20;

/** Onde a mensagem da API fica na linha: embaixo do nome, ou embaixo do peso. */
export type RowErrorPlace = "ticker" | "weight";

/** Uma linha do editor: a ação, o texto do peso **como foi digitado** e as mensagens dela. */
export type EditorRow = {
  /** A identidade da linha na tela (a chave do React), estável ao remover outras. */
  key: number;
  ticker: string;
  name: string;
  /** O valor do campo, nunca reescrito. */
  text: string;
  /** A conferência do cliente sobre o peso. */
  error: string | null;
  /** O `reason` da API, pelo `index`. */
  apiError: { place: RowErrorPlace; text: string } | null;
};

let nextKey = 0;

/** Uma linha nova, com o texto dado (vazio ao acrescentar pelo seletor). */
export function newRow(ticker: string, name: string, text = ""): EditorRow {
  nextKey += 1;
  return { key: nextKey, ticker, name, text, error: null, apiError: null };
}

/** A conferência de um peso: o formato, depois de 0,01 a 100,00. */
export function weightError(text: string): string | null {
  const cents = parseWeight(text);
  if (cents === null) return TEXTOS["carteiras.erro.pesoFormato"];
  if (cents < 1 || cents > TOTAL_CENTS) return TEXTOS["carteiras.erro.peso"];
  return null;
}

/**
 * Ao sair do campo: a mensagem do formato aparece; a que já estava se refaz (some, se o peso
 * passou). Mudou a mensagem, a da API na linha sai.
 */
export function blurRow(row: EditorRow): EditorRow {
  const found = weightError(row.text);
  const error =
    found === TEXTOS["carteiras.erro.pesoFormato"]
      ? found
      : row.error !== null
        ? found
        : null;
  if (error === row.error) return row;
  return { ...row, error, apiError: null };
}

/** Centésimos para a tela, com vírgula: 9999 → "99,99"; 1999980 → "19.999,80". */
export function centsText(cents: number): string {
  return `${formatInteger(Math.floor(cents / 100))},${String(cents % 100).padStart(2, "0")}`;
}

/** Um decimal da API em texto ("99.99") para a tela ("99,99"), pelo texto. */
export function apiDecimalText(value: string): string {
  const [whole = "", fraction = ""] = value.split(".");
  return `${groupDigits(whole)},${`${fraction}00`.slice(0, 2)}`;
}

/** A soma ao vivo: o total dos pesos que são números e quantos ficaram fora. */
export function liveSum(rows: readonly EditorRow[]): {
  cents: number;
  outside: number;
} {
  const parsed = rows.map((row) => parseWeight(row.text));
  const good = parsed.filter((cents): cents is number => cents !== null);
  return { cents: sumCents(good), outside: parsed.length - good.length };
}

/**
 * As conferências do cliente sobre a composição (RF-06), na ordem da API: quantas ações, o peso
 * de cada linha e a soma — esta só quando todos os pesos são números. Limpa as mensagens da API.
 */
export function checkHoldings(rows: readonly EditorRow[]): {
  rows: EditorRow[];
  total: string[];
  ok: boolean;
} {
  const checked = rows.map((row) => ({
    ...row,
    error: weightError(row.text),
    apiError: null,
  }));
  const total: string[] = [];
  if (rows.length < MIN_HOLDINGS || rows.length > MAX_HOLDINGS) {
    total.push(TEXTOS["carteiras.erro.contagem"](rows.length));
  }
  const parsed = rows.map((row) => parseWeight(row.text));
  if (
    rows.length > 0 &&
    parsed.every((cents) => cents !== null) &&
    sumCents(parsed as number[]) !== TOTAL_CENTS
  ) {
    total.push(TEXTOS["carteiras.erro.soma"](centsText(sumCents(parsed as number[]))));
  }
  return {
    rows: checked,
    total,
    ok: total.length === 0 && checked.every((row) => row.error === null),
  };
}

/** A composição no corpo do pedido: o peso em texto com ponto (`"33.33"`). */
export function holdingsToApi(
  rows: readonly EditorRow[],
): { ticker: string; weight: string }[] {
  return rows.map((row) => {
    const cents = parseWeight(row.text);
    if (cents === null) {
      throw new Error(`peso fora da forma no envio: ${row.ticker}`);
    }
    return { ticker: row.ticker, weight: weightToApi(cents) };
  });
}

/** Cada `reason` de `items` (`backend/apps/portfolios/services.py`), com o lugar na linha. */
const ITEM_REASONS: Record<string, { place: RowErrorPlace; text: string }> = {
  duplicate: { place: "ticker", text: TEXTOS["carteiras.erro.repetida"] },
  unknown_ticker: { place: "ticker", text: TEXTOS["carteiras.erro.desconhecida"] },
  not_a_stock: { place: "ticker", text: TEXTOS["carteiras.erro.naoAcao"] },
  inactive: { place: "ticker", text: TEXTOS["carteiras.erro.inativa"] },
  weight_out_of_range: { place: "weight", text: TEXTOS["carteiras.erro.peso"] },
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * O que a resposta de erro da composição diz, no lugar de cada mensagem (RF-06): o
 * `count_out_of_range` e o `weights_sum` na linha da soma; cada item de `items` na linha do seu
 * `index` (a ordem do editor, que é a do envio); o `invalid_parameter` de forma, e um `reason` fora
 * da lista, na mensagem geral. Erro que não é da composição devolve `null` — a tela decide.
 */
export function applyHoldingsError(
  error: unknown,
  rows: readonly EditorRow[],
): { rows: EditorRow[]; total: string[]; general: string | null } | null {
  if (!(error instanceof ApiError)) return null;
  const cleared: EditorRow[] = rows.map((row) => ({ ...row, apiError: null }));
  const general = { rows: cleared, total: [], general: TEXTOS["carteiras.erro.forma"] };
  if (error.code === "invalid_parameter") return general;
  if (error.code !== "invalid_holdings") return null;

  const { reason } = error.details;
  if (reason === "count_out_of_range" && typeof error.details.count === "number") {
    return {
      rows: cleared,
      total: [TEXTOS["carteiras.erro.contagem"](error.details.count)],
      general: null,
    };
  }
  if (reason === "weights_sum" && typeof error.details.sum === "string") {
    return {
      rows: cleared,
      total: [TEXTOS["carteiras.erro.soma"](apiDecimalText(error.details.sum))],
      general: null,
    };
  }
  const items = error.details.items;
  if (
    reason === "items" &&
    Array.isArray(items) &&
    items.length > 0 &&
    items.every(
      (item) =>
        isRecord(item) &&
        typeof item.index === "number" &&
        Number.isInteger(item.index) &&
        item.index >= 0 &&
        item.index < rows.length &&
        typeof item.reason === "string" &&
        Object.hasOwn(ITEM_REASONS, item.reason),
    )
  ) {
    const marked = [...cleared];
    for (const item of items as { index: number; reason: string }[]) {
      marked[item.index] = {
        ...marked[item.index],
        apiError: ITEM_REASONS[item.reason],
      };
    }
    return { rows: marked, total: [], general: null };
  }
  return general;
}
