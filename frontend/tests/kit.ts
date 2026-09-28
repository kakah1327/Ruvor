/**
 * Leitor de CSS dos testes do kit (M1.6a).
 *
 * Lê os arquivos de brand/ruvor/ — no contêiner `frontend`, montados só para leitura em
 * /repo/brand/ruvor — e tira deles declarações, cores e contraste. É um leitor mínimo,
 * para CSS de folha: não entende aninhamento além de uma @-regra de bloco, nem chave
 * dentro de string.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const BRAND = new URL("../../brand/ruvor/", import.meta.url);

export function readBrand(name: string): string {
  return readFileSync(fileURLToPath(new URL(name, BRAND)), "utf8");
}

export interface Rule {
  readonly selector: string;
  readonly body: string;
}

function normalizeSelector(selector: string): string {
  return selector
    .replace(/\s+/g, " ")
    .replace(/\s*,\s*/g, ", ")
    .trim();
}

/** As regras de estilo, inclusive as de dentro de @media; as @-regras não entram. */
export function rules(css: string): Rule[] {
  const text = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const found: Rule[] = [];
  const walk = (source: string): void => {
    let position = 0;
    while (position < source.length) {
      const open = source.indexOf("{", position);
      if (open === -1) return;
      const prelude = source.slice(position, open).trim();
      let depth = 1;
      let close = open + 1;
      while (close < source.length && depth > 0) {
        if (source[close] === "{") depth += 1;
        else if (source[close] === "}") depth -= 1;
        close += 1;
      }
      if (depth !== 0) throw new Error(`chave sem par depois de "${prelude}"`);
      const body = source.slice(open + 1, close - 1);
      if (prelude.startsWith("@")) {
        if (/^@media\b/.test(prelude)) walk(body);
      } else {
        found.push({ selector: normalizeSelector(prelude), body });
      }
      position = close;
    }
  };
  walk(text);
  return found;
}

function ruleFor(css: string, selector: string): Rule {
  const wanted = normalizeSelector(selector);
  const matches = rules(css).filter((rule) => rule.selector === wanted);
  if (matches.length !== 1) {
    throw new Error(`esperava um bloco "${wanted}", achei ${matches.length}`);
  }
  return matches[0];
}

/** Todas as declarações do bloco daquele seletor exato, na ordem. */
export function declarations(css: string, selector: string): Array<[string, string]> {
  return ruleFor(css, selector)
    .body.split(";")
    .map((part) => part.trim())
    .filter((part) => part.length > 0)
    .map((part) => {
      const colon = part.indexOf(":");
      if (colon === -1) throw new Error(`declaração sem ":" em "${selector}": ${part}`);
      return [part.slice(0, colon).trim(), part.slice(colon + 1).trim()];
    });
}

/** As declarações `--*` do bloco daquele seletor exato. */
export function parseVars(css: string, selector: string): Record<string, string> {
  const vars: Record<string, string> = {};
  for (const [name, value] of declarations(css, selector)) {
    if (name.startsWith("--")) vars[name] = value;
  }
  return vars;
}

/** O valor de uma propriedade no bloco daquele seletor exato. */
export function ruleValue(css: string, selector: string, property: string): string {
  const found = declarations(css, selector).filter(([name]) => name === property);
  if (found.length !== 1) {
    throw new Error(
      `esperava um "${property}" em "${selector}", achei ${found.length}`,
    );
  }
  return found[0][1];
}

const COLOR = /#[0-9a-f]{3,8}\b|var\(\s*--[\w-]+\s*\)/gi;

/**
 * A cor de uma propriedade: o valor simples, a cor de um atalho (`1px solid #e7e4df`) ou
 * a parada de um gradiente pela posição. Devolve como está — hexadecimal ou `var(--x)`.
 */
export function ruleColor(
  css: string,
  selector: string,
  property: string,
  index = 0,
): string {
  const colors = ruleValue(css, selector, property).match(COLOR) ?? [];
  if (index >= colors.length) {
    throw new Error(`"${selector}" { ${property} } não tem a cor de índice ${index}`);
  }
  return colors[index];
}

/** Segue `var(--x)` até um valor que não seja referência. */
export function resolve(vars: Record<string, string>, value: string): string {
  let current = value.trim();
  for (let step = 0; step < 20; step += 1) {
    const reference = /^var\(\s*(--[\w-]+)\s*\)$/.exec(current);
    if (!reference) return current;
    const next = vars[reference[1]];
    if (next === undefined) throw new Error(`variável indefinida: ${reference[1]}`);
    current = next.trim();
  }
  throw new Error(`referência circular a partir de ${value}`);
}

/** Maiúsculas e hexadecimal curto expandido: `#fff` → `#FFFFFF`. */
export function normalizeHex(hex: string): string {
  const match = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(hex.trim());
  if (!match) throw new Error(`não é cor hexadecimal de 3 ou 6 dígitos: ${hex}`);
  const digits =
    match[1].length === 3
      ? [...match[1]].map((digit) => digit + digit).join("")
      : match[1];
  return `#${digits.toUpperCase()}`;
}

function luminance(hex: string): number {
  const digits = normalizeHex(hex).slice(1);
  const [r, g, b] = [0, 2, 4].map((start) => {
    const channel = Number.parseInt(digits.slice(start, start + 2), 16) / 255;
    return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** Razão de contraste pela fórmula WCAG 2.x. */
export function contrast(hexA: string, hexB: string): number {
  const [light, dark] = [luminance(hexA), luminance(hexB)].sort((a, b) => b - a);
  return (light + 0.05) / (dark + 0.05);
}
