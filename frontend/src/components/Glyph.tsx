/**
 * O ícone (D-93): o desenho vem do arquivo do conjunto em `brand/ruvor/icons/`, lido como
 * texto pelo apelido `@brand` (`?raw`, do Vite) — nenhum componente copia o `d` à mão.
 *
 * Todo arquivo do conjunto tem a mesma forma: `<svg viewBox="0 0 256 256">` com um ou dois
 * `<path d="…">`, o de fundo do duotone com `opacity`. O componente extrai os `<path>` e os
 * desenha num `<svg class="ruvor-glyph">`, decorativo: o rótulo é do elemento em volta.
 *
 * Ícone novo entra na tabela abaixo, com o import do arquivo.
 */

import infoDuotone from "@brand/icons/duotone/info.svg?raw";
import warningDuotone from "@brand/icons/duotone/warning.svg?raw";
import xCircleDuotone from "@brand/icons/duotone/x-circle.svg?raw";
import arrowLeft from "@brand/icons/regular/arrow-left.svg?raw";
import arrowsClockwise from "@brand/icons/regular/arrows-clockwise.svg?raw";
import calendarBlank from "@brand/icons/regular/calendar-blank.svg?raw";
import caretRight from "@brand/icons/regular/caret-right.svg?raw";
import chartLine from "@brand/icons/regular/chart-line.svg?raw";
import checkCircle from "@brand/icons/regular/check-circle.svg?raw";
import database from "@brand/icons/regular/database.svg?raw";
import info from "@brand/icons/regular/info.svg?raw";
import magnifyingGlass from "@brand/icons/regular/magnifying-glass.svg?raw";
import scales from "@brand/icons/regular/scales.svg?raw";
import spinnerGap from "@brand/icons/regular/spinner-gap.svg?raw";
import x from "@brand/icons/regular/x.svg?raw";

const REGULAR = {
  "arrow-left": arrowLeft,
  "arrows-clockwise": arrowsClockwise,
  "calendar-blank": calendarBlank,
  "caret-right": caretRight,
  "chart-line": chartLine,
  "check-circle": checkCircle,
  database,
  info,
  "magnifying-glass": magnifyingGlass,
  scales,
  "spinner-gap": spinnerGap,
  x,
} as const;

/** Os duotone só vão nos sinais (`.ruvor-icon`), pela D-93. */
const DUOTONE = {
  info: infoDuotone,
  warning: warningDuotone,
  "x-circle": xCircleDuotone,
} as const;

export type RegularGlyph = keyof typeof REGULAR;
export type DuotoneGlyph = keyof typeof DUOTONE;

type GlyphPath = { d: string; opacity: string | undefined };

const PATH = /<path d="([^"]+)"(?: opacity="([^"]+)")?\s*\/>/g;
const VIEW_BOX = 'viewBox="0 0 256 256"';

/** Os `<path>` de um arquivo do conjunto. Arquivo fora da forma é erro, não ícone vazio. */
export function parseGlyph(name: string, svg: string): GlyphPath[] {
  const paths = [...svg.matchAll(PATH)].map((match) => ({
    d: match[1],
    opacity: match[2],
  }));
  if (paths.length === 0 || !svg.includes(VIEW_BOX)) {
    throw new Error(`ícone fora da forma do conjunto: ${name}`);
  }
  return paths;
}

function parseAll<K extends string>(
  table: Readonly<Record<K, string>>,
): Record<K, GlyphPath[]> {
  const parsed = {} as Record<K, GlyphPath[]>;
  for (const name of Object.keys(table) as K[]) {
    parsed[name] = parseGlyph(name, table[name]);
  }
  return parsed;
}

const REGULAR_PATHS = parseAll(REGULAR);
const DUOTONE_PATHS = parseAll(DUOTONE);

type GlyphProps = {
  /** Classes a mais, além de `ruvor-glyph`: `ruvor-glyph--sm`, `ruvor-spin`… */
  className?: string;
} & (
  | { name: RegularGlyph; weight?: "regular" }
  | { name: DuotoneGlyph; weight: "duotone" }
);

export function Glyph(props: GlyphProps) {
  const paths =
    props.weight === "duotone" ? DUOTONE_PATHS[props.name] : REGULAR_PATHS[props.name];
  const className =
    props.className === undefined ? "ruvor-glyph" : `ruvor-glyph ${props.className}`;

  return (
    <svg
      className={className}
      viewBox="0 0 256 256"
      aria-hidden="true"
      focusable="false"
    >
      {paths.map((path) => (
        <path key={path.d} d={path.d} opacity={path.opacity} />
      ))}
    </svg>
  );
}
