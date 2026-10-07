/**
 * O valor da carteira em reais, lido **por texto** (a correção da T5 registrada no plano, com a
 * regra aprovada no portão do `lista.html`).
 *
 * O `notional` vai a 16 algarismos inteiros (`max_digits=18, decimal_places=2` de `_notional()`
 * em `backend/apps/portfolios/serializers.py`), além do inteiro exato do JavaScript: nenhum
 * `Number` nem `parseFloat` na leitura, no envio ou na exibição. A parte inteira e os centavos
 * andam como strings de algarismos.
 */

/** Os algarismos inteiros que a API aceita. */
export const NOTIONAL_MAX_INT_DIGITS = 16;

/** O valor lido: a parte inteira sem zeros à esquerda e os dois centavos, em algarismos. */
export type Notional = { int: string; dec: string };

/** A forma brasileira com milhar: "10.000" ou "10.000,5"; os centavos só depois da vírgula. */
const WITH_THOUSANDS = /^(\d{1,3}(?:\.\d{3})+)(?:,(\d{0,2}))?$/;

/** Sem milhar, com vírgula ou ponto nos centavos: "10000", "10000,5", "10000.50", "10000,". */
const PLAIN = /^(\d+)(?:[.,](\d{0,2}))?$/;

/**
 * O valor digitado, ou nulo — fora das duas formas, zero, ou com mais de 16 algarismos
 * inteiros. O ponto seguido de exatamente três algarismos é milhar ("1.000" é mil); com um ou
 * dois, é centavo ("10.5" é dez e cinquenta). A vírgula ou o ponto sem centavos vale ("10000,").
 */
export function parseNotional(text: string): Notional | null {
  const trimmed = text.trim();
  let whole: string;
  let fraction: string;
  const grouped = WITH_THOUSANDS.exec(trimmed);
  const plain = grouped === null ? PLAIN.exec(trimmed) : null;
  if (grouped !== null) {
    whole = (grouped[1] ?? "").replaceAll(".", "");
    fraction = grouped[2] ?? "";
  } else if (plain !== null) {
    whole = plain[1] ?? "";
    fraction = plain[2] ?? "";
  } else {
    return null;
  }
  const int = whole.replace(/^0+(?=\d)/, "");
  const dec = `${fraction}00`.slice(0, 2);
  if (int.length > NOTIONAL_MAX_INT_DIGITS) {
    return null;
  }
  if (int === "0" && dec === "00") {
    return null; // a partir de 0,01
  }
  return { int, dec };
}

/** O valor no texto que a API recebe, com ponto: `{int: "10000", dec: "00"}` → "10000.00". */
export function notionalToApi(notional: Notional): string {
  return `${notional.int}.${notional.dec}`;
}

/** Os algarismos em grupos de três, pelo texto: "250000" → "250.000". */
export function groupDigits(int: string): string {
  return int.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

/**
 * Um decimal da API em reais ("1234.5", "-0.25"), pelo texto: "R$ 1.234,50", com o espaço
 * inseparável depois do "R$" e o sinal antes dele, como o `Intl.NumberFormat` em `pt-BR` —
 * sem passar por `Number`. Os centavos além do segundo são cortados (a API manda 2 casas).
 */
export function formatBrlText(value: string): string {
  const negative = value.startsWith("-");
  const digits = negative ? value.slice(1) : value;
  const [whole = "", fraction = ""] = digits.split(".");
  const int = whole.replace(/^0+(?=\d)/, "") || "0";
  const dec = `${fraction}00`.slice(0, 2);
  return `${negative ? "-" : ""}R$ ${groupDigits(int)},${dec}`;
}
