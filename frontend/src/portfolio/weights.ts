/**
 * A aritmética dos pesos da carteira (RF-06), só funções puras.
 *
 * O peso é lido **por algarismos**, nunca por `parseFloat`: em centésimos inteiros, a soma é
 * exata, e `sumCents(...) === TOTAL_CENTS` decide se ela fecha 100%. Em ponto flutuante,
 * `0.01 + 65.40 + 34.59` dá `100.00000000000001`, e `parseFloat("0.29") * 100` truncado dá 28.
 *
 * O editor guarda o texto digitado como valor do campo e deriva os centésimos dele — nunca
 * reescreve o campo ("5," continua "5,").
 */

/** 100%, em centésimos. */
export const TOTAL_CENTS = 10_000;

/** Até 3 algarismos inteiros e até 2 casas, com o ponto já no lugar da vírgula. */
const WEIGHT = /^\d{0,3}([.]\d{0,2})?$/;

/** O peso digitado em centésimos inteiros; nulo se não for um peso com até 2 casas. */
export function parseWeight(text: string): number | null {
  const normalized = text.trim().replaceAll(",", ".");
  if (!WEIGHT.test(normalized)) {
    return null;
  }
  const [whole = "", fraction = ""] = normalized.split(".");
  if (whole === "" && fraction === "") {
    return null; // ao menos um algarismo no total
  }
  const wholeCents = whole === "" ? 0 : Number(whole) * 100;
  // A parte decimal completada à direita: "5,1" → 10, ",5" → 50, "5," → 00.
  return wholeCents + Number(`${fraction}00`.slice(0, 2));
}

/** Os centésimos de volta ao texto que a API recebe: 3333 -> "33.33", 500 -> "5.00". */
export function weightToApi(cents: number): string {
  return `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, "0")}`;
}

/** A soma, em centésimos inteiros. */
export function sumCents(weights: readonly number[]): number {
  return weights.reduce((total, cents) => total + cents, 0);
}
