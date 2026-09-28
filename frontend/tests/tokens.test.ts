/**
 * @vitest-environment node
 *
 * M1.6a — os tokens do kit: V-01 (o claro bate com os mockups), V-02 (a escala
 * tipográfica, parte dos tokens), V-04 (contraste nos dois temas e nas duas cópias do
 * escuro), V-06 (tokens.json igual a tokens.css) e RF-05 (as duas cópias do escuro).
 * E a folha de componentes: V-02 (parte da folha), V-05 (foco visível) e RF-06 (a folha
 * só estiliza classe com o prefixo ruvor-).
 *
 * Lê brand/ruvor/ — no contêiner, a montagem só de leitura em /repo/brand/ruvor.
 */
import { describe, expect, it } from "vitest";

import {
  contrast,
  declarations,
  normalizeHex,
  parseVars,
  readBrand,
  resolve,
  ruleColor,
  rules,
  ruleValue,
} from "./kit";

const TOKENS_CSS = readBrand("tokens.css");
const TOKENS_JSON = JSON.parse(readBrand("tokens.json")) as Record<string, unknown>;
const FOUNDATION = readBrand("mockups/foundation.css");

const LIGHT = ':root, [data-theme="light"]';
const DARK = '[data-theme="dark"]';
const DARK_MEDIA = ':root:not([data-theme="light"])';
const UNTHEMED = ":root";

const PREFIX = "--ruvor-";
const FOUNDATION_ROOT = parseVars(FOUNDATION, ":root");

const THEMES: ReadonlyArray<readonly [string, Record<string, string>]> = [
  ["claro", parseVars(TOKENS_CSS, LIGHT)],
  ["escuro por atributo", parseVars(TOKENS_CSS, DARK)],
  ["escuro pela @media", parseVars(TOKENS_CSS, DARK_MEDIA)],
];

// --- V-01: a tabela de correspondência do plano, como dado ----------------------------

type Source =
  | { readonly kind: "var"; readonly name: string }
  | {
      readonly kind: "rule";
      readonly selector: string;
      readonly property: string;
      readonly index?: number;
    }
  | { readonly kind: "alias"; readonly token: string }
  | { readonly kind: "none" };

const v = (name: string): Source => ({ kind: "var", name });
const r = (selector: string, property: string, index = 0): Source => ({
  kind: "rule",
  selector,
  property,
  index,
});
const alias = (token: string): Source => ({ kind: "alias", token });
const NONE: Source = { kind: "none" };

const CORRESPONDENCE: ReadonlyArray<readonly [string, Source]> = [
  ["ink", v("--ink")],
  ["text", alias("ink")],
  ["paper", v("--paper")],
  ["bg", alias("paper")],
  ["canvas", v("--canvas")],
  ["surface", v("--surface")],
  ["panel", alias("surface")],
  ["surface-2", v("--surface-2")],
  ["border", v("--border")],
  ["text-muted", v("--muted")],
  ["decision", v("--decision")],
  ["decision-soft", v("--decision-soft")],
  ["decision-text", NONE],
  ["review", v("--review")],
  ["review-soft", v("--review-soft")],
  ["review-text", r(".tag.review", "color")],
  ["evidence", v("--evidence")],
  ["evidence-soft", v("--evidence-soft")],
  ["evidence-text", r(".tag.info", "color")],
  ["validated", v("--valid")],
  ["validated-soft", v("--valid-soft")],
  ["validated-text", r(".tag.valid", "color")],
  ["critical", v("--critical")],
  ["critical-soft", v("--critical-soft")],
  ["critical-text", r(".tag.critical", "color")],
  ["topbar", r(".topbar", "background")],
  ["topbar-text", r(".nav a.on", "color")],
  ["topbar-link", r(".nav a", "color")],
  ["topbar-account", r(".account", "color")],
  ["topbar-edge", NONE],
  ["avatar", r(".avatar", "background")],
  ["on-decision", r(".btn.primary", "color")],
  ["choice-selected", r(".choice.on", "background")],
  ["table-head", r("th", "background")],
  ["table-rule", r("td", "border-bottom")],
  ["rank-rule", r(".rank", "border-bottom")],
  ["bar-track", r(".bar", "background")],
  ["callout", r(".callout", "background")],
  ["code-bg", r(".code", "background")],
  ["code-text", r(".code", "color")],
  ["skeleton-base", r(".skeleton", "background", 0)],
  ["skeleton-shine", r(".skeleton", "background", 1)],
  ["icon-review", r(".icon.review", "color")],
  ["control-hover", NONE],
  ["decision-hover", NONE],
  ["focus", NONE],
  ["focus-on-dark", NONE],
];

// O único -text escurecido pelo RF-04: diferente da fonte, e com este valor.
const DARKENED: Readonly<Record<string, string>> = { "review-text": "#7E652B" };

function sourceHex(source: Source): string {
  if (source.kind === "var") {
    return normalizeHex(resolve(FOUNDATION_ROOT, `var(${source.name})`));
  }
  if (source.kind === "rule") {
    const raw = ruleColor(FOUNDATION, source.selector, source.property, source.index);
    return normalizeHex(resolve(FOUNDATION_ROOT, raw));
  }
  throw new Error(`fonte sem cor: ${source.kind}`);
}

// Sem tema: [token, variável de :root de foundation.css ou seletor e propriedade].
const UNTHEMED_CORRESPONDENCE: ReadonlyArray<
  readonly [string, { readonly var: string } | { readonly rule: [string, string] }]
> = [
  ["font-sans", { var: "--sans" }],
  ["font-mono", { var: "--mono" }],
  ["radius-sm", { var: "--r-sm" }],
  ["radius-md", { var: "--r-md" }],
  ["radius-lg", { var: "--r-lg" }],
  ["shadow", { var: "--shadow" }],
  ["shadow-panel", { rule: [".panel", "box-shadow"] }],
];

const squash = (value: string): string => value.replace(/\s*,\s*/g, ",").trim();

describe("V-01 — os tokens do claro batem com foundation.css", () => {
  const light = parseVars(TOKENS_CSS, LIGHT);

  it("a tabela cobre exatamente as cores do claro", () => {
    const names = Object.keys(light).map((name) => name.slice(PREFIX.length));
    expect(names.sort()).toEqual(CORRESPONDENCE.map(([token]) => token).sort());
  });

  it.each(CORRESPONDENCE)("%s", (token, source) => {
    const value = light[`${PREFIX}${token}`];
    expect(value, token).toBeDefined();
    if (source.kind === "none") return;
    if (source.kind === "alias") {
      expect(value).toBe(`var(${PREFIX}${source.token})`);
      expect(normalizeHex(resolve(light, value))).toBe(
        sourceHex(CORRESPONDENCE.find(([name]) => name === source.token)?.[1] ?? NONE),
      );
      return;
    }
    const expected = sourceHex(source);
    const actual = normalizeHex(value);
    if (token in DARKENED) {
      expect(actual, `${token} tem de ser escurecido`).not.toBe(expected);
      expect(actual).toBe(DARKENED[token]);
    } else {
      expect(actual).toBe(expected);
    }
  });

  it.each(UNTHEMED_CORRESPONDENCE)("sem tema: %s", (token, source) => {
    const expected =
      "var" in source
        ? FOUNDATION_ROOT[source.var]
        : ruleValue(FOUNDATION, source.rule[0], source.rule[1]);
    expect(expected, token).toBeDefined();
    const value = parseVars(TOKENS_CSS, UNTHEMED)[`${PREFIX}${token}`];
    expect(value, token).toBeDefined();
    expect(squash(value)).toBe(squash(expected));
  });
});

// --- V-02: a escala tipográfica --------------------------------------------------------

const STEPS = ["display", "h2", "h3", "body", "small", "micro", "label", "brand"];
const SUFFIXES = ["size", "leading", "tracking", "weight"];

describe("V-02 — a escala tipográfica é token", () => {
  const unthemed = parseVars(TOKENS_CSS, UNTHEMED);
  const expected = [
    ...STEPS.flatMap((step) => SUFFIXES.map((suffix) => `type-${step}-${suffix}`)),
    "type-label-tracking-table",
    "type-code-leading",
  ];

  it.each(expected)("%s", (token) => {
    const value = unthemed[`${PREFIX}${token}`];
    expect(value, token).toBeDefined();
    expect(value.length).toBeGreaterThan(0);
  });

  it("os tamanhos são em px", () => {
    for (const step of STEPS) {
      expect(unthemed[`${PREFIX}type-${step}-size`]).toMatch(/^\d+px$/);
    }
  });
});

// --- V-04: contraste, nos dois temas e nas duas cópias do escuro ----------------------

const TEXT_BACKGROUNDS = [
  "paper",
  "canvas",
  "surface",
  "surface-2",
  "table-head",
  "callout",
  "choice-selected",
  "critical-soft",
  "control-hover",
];
const SEMANTICS = ["decision", "review", "evidence", "validated", "critical"];
const SIGNALS: ReadonlyArray<readonly [string, string]> = [
  ["decision", "decision-soft"],
  ["icon-review", "review-soft"],
  ["validated", "validated-soft"],
  ["critical", "critical-soft"],
  ["evidence", "evidence-soft"],
];

type Pair = readonly [string, string, number];

const PAIRS: readonly Pair[] = [
  ...["ink", "text-muted"].flatMap((text) =>
    TEXT_BACKGROUNDS.map((bg): Pair => [text, bg, 4.5]),
  ),
  ...SEMANTICS.map((s): Pair => [`${s}-text`, `${s}-soft`, 4.5]),
  ["on-decision", "decision", 4.5],
  ["on-decision", "decision-hover", 4.5],
  ["topbar-link", "topbar", 4.5],
  ["topbar-account", "topbar", 4.5],
  ["topbar-text", "topbar", 4.5],
  ["topbar-account", "avatar", 4.5],
  ["code-text", "code-bg", 4.5],
  ["validated", "bg", 4.5],
  ["critical", "bg", 4.5],
  ["decision", "paper", 4.5],
  ["decision", "surface", 4.5],
  ["critical-text", "surface", 4.5],
  ...["paper", "canvas", "surface", "surface-2"].map((bg): Pair => ["focus", bg, 3]),
  ["focus-on-dark", "topbar", 3],
  ["focus-on-dark", "code-bg", 3],
  ...SIGNALS.map(([signal, soft]): Pair => [signal, soft, 3]),
  ["critical", "surface", 3],
];

describe("V-04 — contraste", () => {
  for (const [theme, vars] of THEMES) {
    const hex = (token: string): string =>
      normalizeHex(resolve(vars, `var(${PREFIX}${token})`));

    it.each(PAIRS)(`${theme}: %s sobre %s ≥ %s`, (text, bg, minimum) => {
      const ratio = contrast(hex(text), hex(bg));
      expect(
        ratio,
        `${text} ${hex(text)} sobre ${bg} ${hex(bg)}`,
      ).toBeGreaterThanOrEqual(minimum);
    });
  }

  it("a fórmula confere com valores conhecidos", () => {
    expect(contrast("#000000", "#FFFFFF")).toBeCloseTo(21, 5);
    expect(contrast("#FFFFFF", "#FFFFFF")).toBeCloseTo(1, 5);
    // Medido na preparação do plano: o texto da tag review do mockup reprova 4,5.
    expect(contrast("#80672C", "#F1EAD9")).toBeCloseTo(4.497, 3);
    expect(contrast("#7E652B", "#F1EAD9")).toBeCloseTo(4.63, 2);
  });
});

// --- V-06: tokens.json igual a tokens.css ---------------------------------------------

function jsonGroup(path: readonly string[]): Record<string, string> {
  let node: unknown = TOKENS_JSON;
  for (const key of path) {
    node = (node as Record<string, unknown> | undefined)?.[key];
  }
  expect(node, path.join(".")).toBeTypeOf("object");
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(node as Record<string, unknown>)) {
    expect(value, `${path.join(".")}.${key}`).toBeTypeOf("string");
    out[`${PREFIX}${key}`] = value as string;
  }
  return out;
}

const UNTHEMED_GROUPS = ["font", "radius", "shadow", "space", "type"];

describe("V-06 — tokens.json igual a tokens.css", () => {
  it("tem os grupos da forma do plano, e só eles", () => {
    expect(Object.keys(TOKENS_JSON).sort()).toEqual(
      ["color", ...UNTHEMED_GROUPS].sort(),
    );
    expect(Object.keys(TOKENS_JSON.color as object).sort()).toEqual(["dark", "light"]);
  });

  it("claro", () => {
    expect(jsonGroup(["color", "light"])).toEqual(parseVars(TOKENS_CSS, LIGHT));
  });

  it("escuro", () => {
    expect(jsonGroup(["color", "dark"])).toEqual(parseVars(TOKENS_CSS, DARK));
  });

  it("sem tema", () => {
    const merged: Record<string, string> = {};
    for (const group of UNTHEMED_GROUPS) {
      for (const [name, value] of Object.entries(jsonGroup([group]))) {
        expect(name in merged, `${name} em dois grupos`).toBe(false);
        expect(name.startsWith(`${PREFIX}${group}`), `${name} fora de ${group}`).toBe(
          true,
        );
        merged[name] = value;
      }
    }
    expect(merged).toEqual(parseVars(TOKENS_CSS, UNTHEMED));
  });
});

// --- RF-05: os temas -------------------------------------------------------------------

describe("RF-05 — os temas", () => {
  it("o escuro por atributo e o da @media têm exatamente as mesmas declarações", () => {
    const sorted = (list: Array<[string, string]>): string[] =>
      list.map(([name, value]) => `${name}: ${value}`).sort();
    expect(sorted(declarations(TOKENS_CSS, DARK_MEDIA))).toEqual(
      sorted(declarations(TOKENS_CSS, DARK)),
    );
  });

  it("o claro e o escuro têm o mesmo conjunto de nomes", () => {
    const light = Object.keys(parseVars(TOKENS_CSS, LIGHT)).sort();
    expect(Object.keys(parseVars(TOKENS_CSS, DARK)).sort()).toEqual(light);
  });

  it("cada bloco declara o seu color-scheme", () => {
    expect(ruleValue(TOKENS_CSS, LIGHT, "color-scheme")).toBe("light");
    expect(ruleValue(TOKENS_CSS, DARK, "color-scheme")).toBe("dark");
    expect(ruleValue(TOKENS_CSS, DARK_MEDIA, "color-scheme")).toBe("dark");
  });

  it("só cor muda de tema: nenhum token sem tema está nos blocos de tema", () => {
    const themed = Object.keys(parseVars(TOKENS_CSS, LIGHT));
    const unthemed = Object.keys(parseVars(TOKENS_CSS, UNTHEMED));
    expect(themed.filter((name) => unthemed.includes(name))).toEqual([]);
  });
});

// --- A folha de componentes: V-02 (parte da folha), V-05 e o que ela não estiliza -------

const COMPONENTS_CSS = readBrand("components.css");
const COMPONENTS_TEXT = COMPONENTS_CSS.replace(/\/\*[\s\S]*?\*\//g, "");
const COMPONENT_RULES = rules(COMPONENTS_CSS);
// A lista de seletores, partida só nas vírgulas de fora de parênteses (:not(a, b)).
function selectorParts(selector: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let start = 0;
  for (let index = 0; index < selector.length; index += 1) {
    const char = selector[index];
    if (char === "(") depth += 1;
    else if (char === ")") depth -= 1;
    else if (char === "," && depth === 0) {
      parts.push(selector.slice(start, index).trim());
      start = index + 1;
    }
  }
  parts.push(selector.slice(start).trim());
  return parts;
}

describe("V-02 — a folha não tem tamanho de fonte literal", () => {
  it("todo font-size é var(...) ou inherit", () => {
    const values = [
      ...COMPONENTS_TEXT.matchAll(/(?<![\w-])font-size\s*:\s*([^;}]+)/g),
    ].map((match) => match[1].trim());
    expect(values.length).toBeGreaterThan(0);
    expect(
      values.filter((value) => !/^(var\(--ruvor-[\w-]+\)|inherit)$/.test(value)),
    ).toEqual([]);
  });

  it("nenhum atalho font: com número em px, em, rem ou %", () => {
    const values = [...COMPONENTS_TEXT.matchAll(/(?<![\w-])font\s*:\s*([^;}]+)/g)].map(
      (match) => match[1].trim(),
    );
    expect(values.filter((value) => /\d\s*(px|em|rem|%)/.test(value))).toEqual([]);
  });
});

const INTERACTIVE = [
  ".ruvor-btn",
  ".ruvor-input",
  ".ruvor-select",
  ".ruvor-choice",
  ".ruvor-nav__link",
];

describe("V-05 — foco visível", () => {
  it.each(INTERACTIVE)("%s tem :focus-visible com outline", (base) => {
    const focus = COMPONENT_RULES.filter((rule) =>
      selectorParts(rule.selector).includes(`${base}:focus-visible`),
    );
    expect(focus.length, `${base}:focus-visible`).toBeGreaterThan(0);
    const outlines = focus.flatMap((rule) =>
      [...rule.body.matchAll(/(?<![\w-])outline\s*:\s*([^;]+)/g)].map((m) =>
        m[1].trim(),
      ),
    );
    expect(outlines.length, `${base}:focus-visible sem outline`).toBeGreaterThan(0);
    for (const value of outlines) expect(value).not.toMatch(/^(none|0)\b/);
  });

  it("nenhum outline: none ou 0 na folha", () => {
    expect(COMPONENTS_TEXT).not.toMatch(/outline(-style|-width)?\s*:\s*(none|0)\b/);
  });
});

describe("RF-06 — a folha só estiliza classe", () => {
  it("encontra as regras", () => {
    expect(COMPONENT_RULES.length).toBeGreaterThan(0);
  });

  it("só tem @media e @keyframes como @-regra", () => {
    const atRules = [...COMPONENTS_TEXT.matchAll(/@([\w-]+)/g)].map(
      (match) => match[1],
    );
    expect(atRules.filter((name) => name !== "media" && name !== "keyframes")).toEqual(
      [],
    );
  });

  it("todo seletor tem classe ruvor- e nenhum é html, body ou título solto", () => {
    // Os passos de @keyframes (from, to, porcentagens) não entram: rules() pula a @-regra.
    const bad = COMPONENT_RULES.flatMap((rule) => selectorParts(rule.selector)).filter(
      (part) =>
        !/\.ruvor-[\w-]/.test(part) ||
        /(^|[\s>+~(,])(html|body|h[1-6])(?![\w-])/.test(part),
    );
    expect(bad).toEqual([]);
  });

  it("toda classe da folha tem o prefixo ruvor-", () => {
    const classes = [...COMPONENTS_TEXT.matchAll(/\.(-?[a-z_][\w-]*)/gi)]
      .map((match) => match[1])
      .filter((name) => !/^\d/.test(name));
    expect(classes.filter((name) => !name.startsWith("ruvor-"))).toEqual([]);
  });
});
