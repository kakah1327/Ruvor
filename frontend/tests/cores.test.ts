/**
 * @vitest-environment node
 *
 * F2b-09: nenhum valor de cor literal em frontend/src/. Cor só entra por token.
 *
 * Vive fora de src/ de propósito: os próprios padrões abaixo reprovariam se o
 * arquivo estivesse dentro do alvo da varredura.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const SRC = fileURLToPath(new URL("../src", import.meta.url));

// Hexadecimal de 3, 4, 6 ou 8 dígitos, terminado por não-alfanumérico.
const HEX = /#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{4}|[0-9a-f]{3})(?![0-9a-z_-])/i;
// Funções de cor.
const FUNCTION = /\b(?:rgba?|hsla?|oklch|lab)\(/i;
// Nomes, só em posição de valor: precedidos por ":" (declaração CSS ou objeto
// de estilo), aspas opcionais, e seguidos por fim de valor — não por "-" nem
// letra, para que "white-space" e "required" não casem.
const NAMES =
  "white|black|red|green|blue|gray|grey|silver|orange|yellow|purple|navy|teal";
const NAMED = new RegExp(`:\\s*['"]?\\s*(?:${NAMES})(?![a-z0-9_-])`, "i");

const PATTERNS: ReadonlyArray<readonly [string, RegExp]> = [
  ["hexadecimal", HEX],
  ["função de cor", FUNCTION],
  ["nome de cor", NAMED],
];

function listFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    return statSync(full).isDirectory() ? listFiles(full) : [full];
  });
}

export function findLiteralColors(root: string): string[] {
  const findings: string[] = [];
  for (const file of listFiles(root)) {
    const lines = readFileSync(file, "utf8").split(/\r?\n/);
    lines.forEach((line, index) => {
      for (const [label, pattern] of PATTERNS) {
        const match = pattern.exec(line);
        if (match) {
          findings.push(`${relative(root, file)}:${index + 1} ${label}: ${match[0]}`);
        }
      }
    });
  }
  return findings;
}

describe("F2b-09 — sem cor literal em src/", () => {
  it("a varredura encontra pelo menos um arquivo", () => {
    expect(listFiles(SRC).length).toBeGreaterThan(0);
  });

  it("nenhum arquivo de src/ contém cor literal", () => {
    expect(findLiteralColors(SRC)).toEqual([]);
  });

  it("os padrões detectam o que prometem e ignoram falso positivo", () => {
    const detect = (s: string): boolean => PATTERNS.some(([, p]) => p.test(s));
    const bad = [
      "color: #fff",
      "color:#ffff",
      "background: #F7F6F2",
      "border: 1px solid #292A2E80",
      "rgb(1,2,3)",
      "rgba(0,0,0,.5)",
      "hsl(0 0% 0%)",
      "hsla(0,0%,0%,1)",
      "oklch(0.5 0 0)",
      "lab(50% 0 0)",
      "color: white",
      "color: 'red'",
      'background: "navy"',
      "{ color: gray }",
    ];
    const good = [
      "white-space: nowrap",
      "const required = true",
      "#root { margin: 0 }",
      "color: var(--ruvor-ink)",
      "url(#clip)",
      'className="status--ok"',
      "// rendered in gray-ish tone",
      "grid-template-areas: 'header'",
      'id="whitelist"',
    ];
    for (const s of bad) expect(detect(s), s).toBe(true);
    for (const s of good) expect(detect(s), s).toBe(false);
  });
});
