/**
 * @vitest-environment node
 *
 * V-09, a outra metade: nenhum componente de `frontend/src/` tem texto visível em literal —
 * todo texto vem do módulo de textos (RF-21). Pela árvore sintática, não por regex: cada
 * `.tsx` é lido com `@babel/parser`, e a árvore é percorrida. Reprova:
 *
 * - um `JSXText` com letra — espaço, número e pontuação passam (`—`, `·`, `%`, `:`);
 * - em posição que renderiza, um `StringLiteral` com letra, ou uma parte fixa com letra de um
 *   `TemplateLiteral`. Posição que renderiza é o filho direto de um elemento JSX e, descendo
 *   recursivamente a partir dele, os dois ramos de `ConditionalExpression`, os operandos de
 *   `LogicalExpression` e as partes de `TemplateLiteral` — não desce em chamada de função,
 *   acesso a membro, objeto nem seta;
 * - a mesma regra no valor dos atributos de texto (`TEXT_ATTRIBUTES`), em qualquer elemento
 *   ou componente.
 *
 * A lista de exceções é vazia. Comentário — o `biome-ignore` dentro da abertura de uma tag, ou
 * `{/* … *\/}` entre os filhos — não é texto: não é nó da árvore.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

import { parse } from "@babel/parser";
import { describe, expect, it } from "vitest";

const SRC = fileURLToPath(new URL("../src", import.meta.url));

const TEXT_ATTRIBUTES = new Set([
  "aria-label",
  "aria-description",
  "title",
  "placeholder",
  "alt",
  "label",
  "caption",
  "hint",
  "message",
  "text",
]);

const LETTER = /\p{L}/u;

// O pedaço da árvore do Babel que a varredura lê.
type AstNode = { type: string; loc?: { start: { line: number } } | null } & Record<
  string,
  unknown
>;

// Chaves que não levam a nós filhos (posição, comentários, metadados).
const SKIP = new Set([
  "loc",
  "start",
  "end",
  "range",
  "extra",
  "leadingComments",
  "trailingComments",
  "innerComments",
  "comments",
  "tokens",
]);

function isNode(value: unknown): value is AstNode {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { type?: unknown }).type === "string"
  );
}

function children(node: AstNode): AstNode[] {
  const out: AstNode[] = [];
  for (const [key, value] of Object.entries(node)) {
    if (SKIP.has(key)) continue;
    if (Array.isArray(value)) out.push(...value.filter(isNode));
    else if (isNode(value)) out.push(value);
  }
  return out;
}

function line(node: AstNode): number {
  return node.loc?.start.line ?? 0;
}

// O literal em posição que renderiza: desce só por ternário, `&&`/`||`/`??` e template.
function checkRendered(expr: AstNode, found: string[]): void {
  switch (expr.type) {
    case "StringLiteral":
      if (LETTER.test(String(expr.value))) found.push(`${line(expr)} literal`);
      return;
    case "TemplateLiteral": {
      const quasis = (expr.quasis as AstNode[]) ?? [];
      for (const quasi of quasis) {
        const value = quasi.value as { raw: string; cooked?: string | null };
        if (LETTER.test(value.cooked ?? value.raw))
          found.push(`${line(quasi)} template`);
      }
      for (const inner of (expr.expressions as AstNode[]) ?? [])
        checkRendered(inner, found);
      return;
    }
    case "ConditionalExpression":
      checkRendered(expr.consequent as AstNode, found);
      checkRendered(expr.alternate as AstNode, found);
      return;
    case "LogicalExpression":
      checkRendered(expr.left as AstNode, found);
      checkRendered(expr.right as AstNode, found);
      return;
    default:
      return;
  }
}

function attributeName(attr: AstNode): string | null {
  const name = attr.name as AstNode;
  return name.type === "JSXIdentifier" ? String(name.name) : null;
}

/** Os achados de texto visível em literal num código-fonte TSX, como "linha tipo". */
export function findJsxText(source: string): string[] {
  const ast = parse(source, {
    sourceType: "module",
    plugins: ["jsx", "typescript"],
  }) as unknown as AstNode;
  const found: string[] = [];
  const visit = (node: AstNode): void => {
    if (node.type === "JSXText") {
      if (LETTER.test(String(node.value))) found.push(`${line(node)} texto`);
    } else if (node.type === "JSXElement" || node.type === "JSXFragment") {
      for (const child of (node.children as AstNode[]) ?? []) {
        if (child.type === "JSXExpressionContainer") {
          checkRendered(child.expression as AstNode, found);
        }
      }
    } else if (node.type === "JSXAttribute") {
      const name = attributeName(node);
      const value = node.value as AstNode | null;
      if (name !== null && TEXT_ATTRIBUTES.has(name) && value !== null) {
        if (value.type === "JSXExpressionContainer") {
          checkRendered(value.expression as AstNode, found);
        } else {
          checkRendered(value, found);
        }
      }
    }
    for (const child of children(node)) visit(child);
  };
  visit(ast);
  return found;
}

function listTsx(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return listTsx(path);
    return name.endsWith(".tsx") ? [path] : [];
  });
}

describe("V-09 — sem texto visível em literal nos componentes", () => {
  it("a varredura encontra os componentes", () => {
    const files = listTsx(SRC).map((f) => relative(SRC, f).replaceAll("\\", "/"));
    expect(files).toContain("App.tsx");
    expect(files).toContain("components/Shell.tsx");
    expect(files).toContain("components/SearchBox.tsx");
  });

  it("nenhum .tsx de src/ tem texto visível em literal", () => {
    const findings = listTsx(SRC).flatMap((file) =>
      findJsxText(readFileSync(file, "utf8")).map((f) => `${relative(SRC, file)}:${f}`),
    );
    expect(findings).toEqual([]);
  });
});

describe("V-09 — os casos de fixação da varredura de JSX", () => {
  // Cada caso é um módulo inteiro; o que pega tem de dar pelo menos um achado.
  const PEGA: ReadonlyArray<readonly [string, string]> = [
    ["texto em linha própria", "const a = <p>\n  Backend: ok\n</p>;"],
    ["número e palavra", "const a = <p>1 ano</p>;"],
    ["literal entre chaves", 'const a = <p>{"texto"}</p>;'],
    ["ternário", 'const a = <p>{ok ? "Sim" : "Não"}</p>;'],
    ["&&", 'const a = <p>{x && "texto"}</p>;'],
    ["template com expressão", `const a = <p>{\`Olá \${n}\`}</p>;`],
    ["atributo literal", 'const a = <button aria-label="Fechar" />;'],
    ["atributo entre chaves", 'const a = <button aria-label={"Fechar"} />;'],
    ["title com template", "const a = <span title={`Oi`} />;"],
    ["prop de componente", 'const a = <Tag label="inativo" />;'],
    ["filho de fragmento", "const a = <>Oi</>;"],
    ["ternário aninhado", 'const a = <p>{a ? b : c ? "x" : null}</p>;'],
    ["template dentro de ternário", `const a = <p>{ok ? \`Sim \${n}\` : null}</p>;`],
  ];

  const NAO_PEGA: ReadonlyArray<readonly [string, string]> = [
    ["comparações com &&", "const ok = a > b && c < d;"],
    ["ternário de elementos", "const a = n > max ? <A /> : <B />;"],
    ["seta com <", "const f = (r: Res) => r.status < 500;"],
    ["genérico de tipo", "type P = Readonly<Props>;"],
    ["genérico de chamada", "const [n] = useState<number>(0);"],
    ["pontuação", "const a = <td>—</td>;"],
    ["expressão numérica", "const a = <p>{n}</p>;"],
    ["atributo do módulo", 'const a = <b aria-label={TEXTOS["x"]} />;'],
    [
      "className condicional",
      'const a = <i className={ok ? "ruvor-tag--validated" : "ruvor-tag--review"} />;',
    ],
    ["chave condicional", 'const a = <p>{TEXTOS[ok ? "a" : "b"]}</p>;'],
    [
      "comentário biome-ignore na abertura da tag",
      [
        "const a = (",
        "  <ul",
        "    // biome-ignore lint/a11y/noNoninteractiveElementToInteractiveRole: a lista do kit",
        '    role="listbox"',
        "  />",
        ");",
      ].join("\n"),
    ],
    ["comentário entre os filhos", "const a = <p>{/* um comentário qualquer */}</p>;"],
    [
      "href e data-*",
      'const a = <a href="/ativos/ITUB4" data-risk-state="E1" role="link" />;',
    ],
    ["chamada de função", 'const a = <p>{traduz("texto")}</p>;'],
  ];

  it.each(PEGA)("pega: %s", (_, source) => {
    expect(findJsxText(source).length).toBeGreaterThan(0);
  });

  it.each(NAO_PEGA)("não pega: %s", (_, source) => {
    expect(findJsxText(source)).toEqual([]);
  });
});
