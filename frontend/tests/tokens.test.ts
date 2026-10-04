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
  // M1.6b: o controle sobre a barra (a chave de tema), com o valor do avatar e nome próprio.
  ["topbar-control", NONE],
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
  // M2.1b (T10): o véu atrás do diálogo (usuarios.html), a barra a 55% sobre transparente.
  ["scrim", NONE],
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
  // M1.6b: o botão marcado da chave de tema.
  ["topbar-text", "topbar-control", 4.5],
  ["code-text", "code-bg", 4.5],
  ["validated", "bg", 4.5],
  ["critical", "bg", 4.5],
  // O eyebrow: sobre a página, o painel, o trilho, o callout e o cabeçalho de tabela, a
  // escolha marcada e o fundo crítico.
  ...[
    "paper",
    "surface",
    "surface-2",
    "callout",
    "critical-soft",
    "choice-selected",
  ].map((bg): Pair => ["decision", bg, 4.5]),
  ["critical-text", "surface", 4.5],
  ...["paper", "canvas", "surface", "surface-2"].map((bg): Pair => ["focus", bg, 3]),
  ["focus-on-dark", "topbar", 3],
  ["focus-on-dark", "code-bg", 3],
  ...SIGNALS.map(([signal, soft]): Pair => [signal, soft, 3]),
  // O sinal dentro do callout crítico fica sobre surface (components.css).
  ...SIGNALS.map(([signal]): Pair => [signal, "surface", 3]),
  // M2.1b (T10): o sobretítulo da cena de acesso; as iniciais no botão de conta; o link no
  // meio do texto, sobre a página e o painel; o papel marcado na chave sobre a superfície; e
  // a confirmação de cópia, no diálogo.
  ["review", "topbar", 4.5],
  ["topbar-text", "avatar", 4.5],
  ["decision-text", "paper", 4.5],
  ["decision-text", "surface", 4.5],
  ["paper", "ink", 4.5],
  ["validated-text", "surface", 4.5],
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
  // M1.6b (T5): a marca como link, a chave de tema, a busca e a tabela que abre.
  ".ruvor-brand",
  ".ruvor-segmented__btn",
  ".ruvor-search__input",
  ".ruvor-search__clear",
  ".ruvor-search__link",
  ".ruvor-chip",
  ".ruvor-table__toggle",
  // M1.6c (T3): o link de comunicado, que abre o documento na CVM.
  ".ruvor-doc__link",
  // M2.3 (T7): o controle de recolher.
  ".ruvor-collapsible__toggle",
  // M2.1b (T10): o link no meio do texto, o "Entrar" da barra, o botão de conta e o item do
  // menu.
  ".ruvor-link",
  ".ruvor-topbar__signin",
  ".ruvor-account--button",
  ".ruvor-menu__item",
  // M2.4 (T11): o contêiner rolável da grade do laboratório, que recebe o foco pelo teclado.
  ".ruvor-lab-scroll",
];

describe("V-05 — foco visível", () => {
  it.each(INTERACTIVE)("%s tem :focus-visible com outline", (base) => {
    const focus = COMPONENT_RULES.filter((rule) =>
      // o próprio seletor, ou ele com um ancestral (o link da barra: .ruvor-topbar …)
      selectorParts(rule.selector).some(
        (part) =>
          part === `${base}:focus-visible` || part.endsWith(` ${base}:focus-visible`),
      ),
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

  // O anel sobre fundo escuro: a regra geral da barra e do código fica em (0,2,0) e DEPOIS
  // das regras de foco dos componentes, para um .ruvor-btn/.ruvor-input/.ruvor-choice dentro
  // da barra ou do código ganhar o anel escuro (o claro dá 1,98:1 sobre a barra); e o link da
  // barra tem regra própria em (0,3,0), para o recuo de -6px não ser anulado por ela.
  it("o anel sobre fundo escuro vence os componentes e não anula o recuo do link", () => {
    const index = (selector: string): number =>
      COMPONENT_RULES.findIndex((rule) =>
        selectorParts(rule.selector).includes(selector),
      );
    const generic = index(".ruvor-topbar :focus-visible");
    expect(generic, "regra geral da barra, sem :where()").toBeGreaterThan(-1);
    expect(index(".ruvor-code :focus-visible"), "regra geral do código").toBe(generic);
    expect(COMPONENT_RULES[generic].body).toMatch(/var\(--ruvor-focus-on-dark\)/);
    for (const component of [
      ".ruvor-btn:focus-visible",
      ".ruvor-input:focus-visible",
      ".ruvor-select:focus-visible",
      ".ruvor-choice:focus-visible",
      ".ruvor-search__input:focus-visible",
    ]) {
      const at = index(component);
      expect(at, component).toBeGreaterThan(-1);
      expect(at, `${component} vem antes da regra geral`).toBeLessThan(generic);
    }
    expect(
      ruleValue(
        COMPONENTS_CSS,
        ".ruvor-topbar .ruvor-nav__link:focus-visible",
        "outline-offset",
      ),
    ).toBe("-6px");
  });

  it("nenhum outline: none ou 0 na folha", () => {
    expect(COMPONENTS_TEXT).not.toMatch(/outline(-style|-width)?\s*:\s*(none|0)\b/);
  });
});

// M1: o hover do campo não pode vencer a borda crítica do inválido.
describe("RF-03 — o campo inválido mantém a borda no hover", () => {
  it.each([".ruvor-input", ".ruvor-select"])(
    "%s:hover exclui [aria-invalid]",
    (base) => {
      const hovers = COMPONENT_RULES.flatMap((rule) =>
        selectorParts(rule.selector),
      ).filter((part) => part.startsWith(`${base}:hover`));
      expect(hovers.length, `${base}:hover`).toBeGreaterThan(0);
      for (const part of hovers) expect(part).toContain('[aria-invalid="true"]');
    },
  );
});

// D-93: o ícone não muda o conteúdo de quem não o tem. Botão, dica, erro de campo e callout
// só viram flex (com gap) sob :has(> ícone); a regra base fica no fluxo do texto, como no
// mockup — senão o <b> no meio da frase e o text-align se perdem.
const ICON_FLEX: ReadonlyArray<readonly [string, readonly string[]]> = [
  [".ruvor-btn", ["> .ruvor-glyph"]],
  [".ruvor-hint", ["> .ruvor-glyph"]],
  [".ruvor-field__error", ["> .ruvor-glyph"]],
  [".ruvor-callout", ["> .ruvor-icon", "> .ruvor-glyph"]],
];
const FLEX_DECLARATION = /(?<![\w-])(display\s*:\s*(inline-)?flex|gap\s*:)/;

describe("D-93 — o flex do ícone só existe com o ícone", () => {
  it.each(ICON_FLEX)("%s: a regra base não tem display:flex nem gap", (base) => {
    const own = COMPONENT_RULES.filter((rule) =>
      selectorParts(rule.selector).includes(base),
    );
    expect(own.length, base).toBeGreaterThan(0);
    for (const rule of own) expect(rule.body).not.toMatch(FLEX_DECLARATION);
  });

  it.each(ICON_FLEX)("%s: o flex vem só de :has(> ícone)", (base, children) => {
    // Toda parte de seletor do próprio componente (ele, com estado ou :has) que liga o flex.
    const flexParts = COMPONENT_RULES.filter((rule) =>
      FLEX_DECLARATION.test(rule.body),
    ).flatMap((rule) =>
      selectorParts(rule.selector).filter(
        (part) => part === base || part.startsWith(`${base}:`),
      ),
    );
    expect(flexParts.length, `${base} sem flex com ícone`).toBeGreaterThan(0);
    for (const part of flexParts) {
      expect(part.startsWith(`${base}:has(`), part).toBe(true);
      for (const child of children) expect(part).toContain(child);
    }
  });

  it("o sinal no callout crítico fica sobre surface", () => {
    expect(
      ruleValue(COMPONENTS_CSS, ".ruvor-callout--critical .ruvor-icon", "background"),
    ).toBe("var(--ruvor-surface)");
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

// M2.3 (T7): o controle de recolher, do comportamento.html aprovado. Os estados do RF-03 que
// ele tem: o hover (o sublinhado), o foco visível (no V-05, pela lista INTERACTIVE) e o aberto
// (a seta girada pelo aria-expanded); não há disabled nem carregando.
describe("M2.3 — o controle de recolher no kit", () => {
  it("o hover sublinha o rótulo", () => {
    expect(
      ruleValue(
        COMPONENTS_CSS,
        ".ruvor-collapsible__toggle:hover span",
        "text-decoration",
      ),
    ).toBe("underline");
  });

  it("aberto, a seta gira pelo aria-expanded, sem classe a mais", () => {
    expect(
      ruleValue(
        COMPONENTS_CSS,
        '.ruvor-collapsible__toggle[aria-expanded="true"] .ruvor-glyph',
        "transform",
      ),
    ).toBe("rotate(90deg)");
  });

  it("o raiz separa o controle do que vem antes por uma régua de token", () => {
    expect(ruleValue(COMPONENTS_CSS, ".ruvor-collapsible", "border-top")).toBe(
      "1px solid var(--ruvor-table-rule)",
    );
  });
});

// M2.1b (T10): o que os mockups aprovados pediram ao kit e que a vista não confere sozinha —
// o [hidden] do menu, o véu do diálogo em token, a chave sobre a superfície desabilitada e a
// barra estreita até 840 px, sem os seletores por posição do M2.3.
function mediaBodies(css: string, query: string): string[] {
  const text = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const bodies: string[] = [];
  let from = 0;
  for (;;) {
    const at = text.indexOf(`@media ${query}`, from);
    if (at === -1) return bodies;
    const open = text.indexOf("{", at);
    let depth = 1;
    let close = open + 1;
    while (depth > 0) {
      if (text[close] === "{") depth += 1;
      else if (text[close] === "}") depth -= 1;
      close += 1;
    }
    bodies.push(text.slice(open + 1, close - 1));
    from = close;
  }
}

describe("M2.1b — os componentes das telas de acesso no kit", () => {
  it("o menu fechado continua oculto pelo [hidden]", () => {
    expect(ruleValue(COMPONENTS_CSS, ".ruvor-menu[hidden]", "display")).toBe("none");
  });

  it("o véu do diálogo é o token --ruvor-scrim, no próprio ::backdrop", () => {
    expect(ruleValue(COMPONENTS_CSS, ".ruvor-dialog::backdrop", "background")).toBe(
      "var(--ruvor-scrim)",
    );
  });

  it("a chave sobre a superfície tem :disabled, e o hover não vale nele", () => {
    const disabled = ".ruvor-segmented--surface .ruvor-segmented__btn:disabled";
    expect(ruleValue(COMPONENTS_CSS, disabled, "opacity")).toBe("0.5");
    expect(ruleValue(COMPONENTS_CSS, disabled, "cursor")).toBe("not-allowed");
    const hovers = COMPONENT_RULES.flatMap((rule) =>
      selectorParts(rule.selector),
    ).filter((part) =>
      part.startsWith(".ruvor-segmented--surface .ruvor-segmented__btn:hover"),
    );
    expect(hovers.length).toBeGreaterThan(0);
    for (const part of hovers) expect(part).toContain(":not(:disabled");
  });

  it("a barra estreita vale até 840 px e endereça cada peça, não a posição", () => {
    const narrow = mediaBodies(COMPONENTS_CSS, "(max-width: 840px)").join("\n");
    for (const selector of [
      ".ruvor-topbar {",
      ".ruvor-topbar__prefs {",
      ".ruvor-topbar__prefs > .ruvor-segmented:has(+ .ruvor-segmented) {",
      ".ruvor-topbar__prefs > .ruvor-segmented + .ruvor-segmented {",
      ".ruvor-topbar__prefs > .ruvor-topbar__account {",
    ]) {
      expect(narrow, selector).toContain(selector);
    }
    const old = mediaBodies(COMPONENTS_CSS, "(max-width: 720px)").join("\n");
    expect(old).not.toMatch(/\.ruvor-topbar(__prefs|__search|__spacer)?\s*\{/);
    expect(COMPONENTS_TEXT).not.toMatch(
      /\.ruvor-topbar__prefs\s*>\s*:(first|last)-child/,
    );
  });
});

// M2.4 (T11): o que o laboratorio.html aprovado pediu ao kit e que a vista não confere sozinha —
// a grade que rola dentro do contêiner com a coluna dos modelos presa, e as duas cópias das
// colunas da década e dos anos não rejeitados, trocadas em 720 px (ajuste do portão). O foco do
// contêiner está no V-05 (INTERACTIVE); as cores são tokens já medidos no V-04 (texto e texto
// suave sobre surface e table-head, as tags sobre o -soft delas): nenhum par novo.
describe("M2.4 — a grade do laboratório no kit", () => {
  it("o contêiner rola na horizontal, e a página não", () => {
    expect(ruleValue(COMPONENTS_CSS, ".ruvor-lab-scroll", "overflow-x")).toBe("auto");
    expect(ruleValue(COMPONENTS_CSS, ".ruvor-lab-scroll", "max-width")).toBe("100%");
  });

  it("a coluna dos modelos fica presa, sobre a superfície", () => {
    // o seletor tem dois blocos (o de sempre e o estreito, que só quebra o nome): lê os dois
    const row = COMPONENT_RULES.filter(
      (rule) => rule.selector === '.ruvor-lab-grid th[scope="row"]',
    )
      .map((rule) => rule.body)
      .join(";");
    expect(row).toMatch(/(?<![\w-])position:\s*sticky\s*;/);
    expect(row).toMatch(/(?<![\w-])left:\s*0\s*;/);
    expect(row).toMatch(/(?<![\w-])background:\s*var\(--ruvor-surface\)\s*;/);
    expect(
      ruleValue(COMPONENTS_CSS, ".ruvor-lab-grid thead th:first-child", "position"),
    ).toBe("sticky");
  });

  it("até 720 px, a cópia junto do nome aparece e a do fim some; fora, o contrário", () => {
    expect(COMPONENTS_TEXT).toMatch(
      /\.ruvor-lab-grid \.ruvor-lab-grid__narrow \{\s*display: none;\s*\}/,
    );
    const narrow = mediaBodies(COMPONENTS_CSS, "(max-width: 720px)").join("\n");
    expect(narrow).toMatch(
      /\.ruvor-lab-grid \.ruvor-lab-grid__narrow \{\s*display: table-cell;\s*\}/,
    );
    expect(narrow).toMatch(
      /\.ruvor-lab-grid \.ruvor-lab-grid__wide \{\s*display: none;\s*\}/,
    );
  });
});
