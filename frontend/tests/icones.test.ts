/**
 * @vitest-environment node
 *
 * M1.6a T4b (D-93) — os ícones do kit: o conjunto fechado copiado do Phosphor para
 * brand/ruvor/icons/. Todo .svg está no icons.json e vice-versa; cada um tem a caixa do
 * Phosphor e nenhuma cor literal; a licença vem junto; a versão é exata; e a vitrine
 * (docs/mockups/M1.6a/kit.html) mostra cada ícone, com o desenho copiado do arquivo — todo
 * svg dela, não só o da galeria, e cada sinal com o duotone da sua semântica.
 *
 * No contêiner, brand/ruvor e docs/mockups são montagens só de leitura em /repo. Arquivo
 * ausente reprova: nada aqui pula.
 */
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const ICONS = fileURLToPath(new URL("../../brand/ruvor/icons/", import.meta.url));
const KIT = fileURLToPath(
  new URL("../../docs/mockups/M1.6a/kit.html", import.meta.url),
);

type Weight = "regular" | "duotone";
interface Manifest {
  readonly source: string;
  readonly version: string;
  readonly icons: Record<string, Partial<Record<Weight, string>>>;
}

const MANIFEST = JSON.parse(
  readFileSync(join(ICONS, "icons.json"), "utf8"),
) as Manifest;
const NAMES = Object.keys(MANIFEST.icons);
// Os cinco dos sinais (.ruvor-icon), e só eles, têm o duotone.
const SIGNALS = ["check-circle", "warning", "x-circle", "info", "flag"];

function listSvgs(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return listSvgs(path);
    return name.endsWith(".svg") ? [relative(ICONS, path).replaceAll("\\", "/")] : [];
  });
}

const FILES = listSvgs(ICONS).sort();
const LISTED = NAMES.flatMap((name) => Object.values(MANIFEST.icons[name])).sort();

// O que fica entre <svg ...> e </svg>: o desenho.
function drawing(svg: string): string {
  const match = /^\s*<svg\b[^>]*>([\s\S]*)<\/svg>\s*$/.exec(svg);
  if (!match) throw new Error(`não é um svg: ${svg.slice(0, 60)}`);
  return match[1].trim();
}

describe("D-93 — o conjunto de ícones", () => {
  it("vem do Phosphor, numa versão exata", () => {
    expect(MANIFEST.source).toBe("@phosphor-icons/core");
    expect(MANIFEST.version).toMatch(/^\d+\.\d+\.\d+$/);
  });

  it("o LICENSE existe e é o MIT", () => {
    const license = readFileSync(join(ICONS, "LICENSE"), "utf8");
    expect(license).toMatch(/MIT License/);
  });

  it("todo .svg de icons/ está no icons.json, e vice-versa", () => {
    expect(FILES.length).toBeGreaterThan(0);
    expect(FILES).toEqual(LISTED);
  });

  it("cada entrada tem o regular, e o duotone só nos cinco dos sinais", () => {
    for (const name of NAMES) {
      expect(MANIFEST.icons[name].regular, name).toBe(`regular/${name}.svg`);
    }
    const duotone = NAMES.filter((name) => "duotone" in MANIFEST.icons[name]);
    expect(duotone.sort()).toEqual([...SIGNALS].sort());
    for (const name of duotone) {
      expect(MANIFEST.icons[name].duotone).toBe(`duotone/${name}.svg`);
    }
  });

  it.each(FILES)("%s: caixa do Phosphor e nenhuma cor literal", (file) => {
    const svg = readFileSync(join(ICONS, file), "utf8");
    expect(svg).toMatch(/^\s*<svg\b[^>]*\bviewBox="0 0 256 256"/);
    // Todo atributo de cor é currentColor (ou none); e nenhum valor de cor em lugar nenhum.
    const colors = [
      ...svg.matchAll(/\b(fill|stroke|color|stop-color|flood-color)\s*=\s*"([^"]*)"/g),
    ].map((m) => m[2]);
    expect(
      colors.filter((value) => value !== "currentColor" && value !== "none"),
    ).toEqual([]);
    expect(svg).not.toMatch(/#[0-9a-f]{3,8}\b/i);
    expect(svg).not.toMatch(/\b(rgba?|hsla?|oklch|lab)\(/i);
    expect(svg).not.toMatch(/style\s*=|class\s*=|<!--/);
  });
});

describe("D-93 — a vitrine mostra cada ícone, copiado do arquivo", () => {
  it("a vitrine existe", () => {
    expect(existsSync(KIT), KIT).toBe(true);
  });

  const kit = existsSync(KIT) ? readFileSync(KIT, "utf8") : "";
  const gallery = (attribute: string): Map<string, string> => {
    const found = new Map<string, string>();
    const pattern = new RegExp(
      `<li\\b[^>]*\\b${attribute}="([\\w-]+)"[^>]*>[\\s\\S]*?(<svg\\b[\\s\\S]*?</svg>)`,
      "g",
    );
    for (const match of kit.matchAll(pattern)) {
      expect(found.has(match[1]), `${match[1]} duas vezes`).toBe(false);
      found.set(match[1], match[2]);
    }
    return found;
  };

  it("a galeria regular tem exatamente os ícones do conjunto", () => {
    expect([...gallery("data-gallery-icon").keys()].sort()).toEqual([...NAMES].sort());
  });

  it("a galeria duotone tem exatamente os cinco dos sinais", () => {
    expect([...gallery("data-gallery-duotone").keys()].sort()).toEqual(
      [...SIGNALS].sort(),
    );
  });

  it("o desenho na vitrine é o do arquivo", () => {
    const pairs: Array<[Map<string, string>, Weight]> = [
      [gallery("data-gallery-icon"), "regular"],
      [gallery("data-gallery-duotone"), "duotone"],
    ];
    for (const [shown, weight] of pairs) {
      for (const [name, svg] of shown) {
        const file = MANIFEST.icons[name]?.[weight];
        expect(file, `${name} ${weight}`).toBeDefined();
        const original = readFileSync(join(ICONS, file as string), "utf8");
        expect(drawing(svg), `${name} ${weight}`).toBe(drawing(original));
      }
    }
  });
});

// Todo desenho da vitrine, não só o da galeria: a barra, os botões, as tags, os sinais.
describe("D-93 — todo svg da vitrine é um desenho do conjunto", () => {
  const kit = existsSync(KIT) ? readFileSync(KIT, "utf8") : "";
  const viewBox = (svg: string): string | undefined =>
    /^<svg\b[^>]*\bviewBox="([^"]*)"/.exec(svg.trim())?.[1];

  // Desenho → [arquivo, viewBox]: um por arquivo do conjunto, regular e duotone.
  const BY_DRAWING = new Map<string, readonly [string, string | undefined]>();
  for (const file of FILES) {
    const svg = readFileSync(join(ICONS, file), "utf8");
    BY_DRAWING.set(drawing(svg), [file, viewBox(svg)]);
  }

  it("cada <svg> inline tem o conteúdo e o viewBox de um arquivo de icons/", () => {
    const inline = [...kit.matchAll(/<svg\b[^>]*>[\s\S]*?<\/svg>/g)].map((m) => m[0]);
    // Nenhum <svg> escapa da contagem (um sem fecho, por exemplo).
    expect(inline.length).toBe([...kit.matchAll(/<svg\b/g)].length);
    expect(inline.length).toBeGreaterThan(NAMES.length);
    const wrong = inline.flatMap((svg, index) => {
      const found = BY_DRAWING.get(drawing(svg));
      if (!found) return [`#${index}: desenho fora do conjunto`];
      if (viewBox(svg) !== found[1]) {
        return [
          `#${index} (${found[0]}): viewBox ${viewBox(svg)}, o arquivo tem ${found[1]}`,
        ];
      }
      return [];
    });
    expect(wrong).toEqual([]);
  });

  // O mapa da D-93: a semântica do sinal decide o duotone.
  const DUOTONE_OF: Readonly<Record<string, string>> = {
    decision: "flag",
    review: "warning",
    evidence: "info",
    validated: "check-circle",
    critical: "x-circle",
  };

  it("todo .ruvor-icon--<semântica> contém o duotone da sua semântica", () => {
    const classed = [...kit.matchAll(/class="[^"]*\bruvor-icon--[a-z]+/g)].length;
    const signals = [
      ...kit.matchAll(
        /<\w+\b[^>]*\bclass="[^"]*\bruvor-icon--([a-z]+)\b[^"]*"[^>]*>\s*(<svg\b[\s\S]*?<\/svg>)/g,
      ),
    ];
    expect(signals.length).toBeGreaterThan(0);
    // Todo sinal da página tem o svg como primeiro filho: nenhum fica fora da conferência.
    expect(signals.length).toBe(classed);
    const wrong = signals.flatMap(([, semantic, svg], index) => {
      const expected = DUOTONE_OF[semantic];
      if (!expected) return [`#${index}: semântica desconhecida ${semantic}`];
      const file = BY_DRAWING.get(drawing(svg))?.[0];
      return file === `duotone/${expected}.svg`
        ? []
        : [
            `#${index} ${semantic}: ${file ?? "fora do conjunto"}, esperava duotone/${expected}.svg`,
          ];
    });
    expect(wrong).toEqual([]);
  });
});
