/**
 * O ícone único (decisão registrada na T6 do M1.6b): o desenho sai do arquivo do conjunto,
 * `brand/ruvor/icons/`, e nenhum componente de `frontend/src/` copia o `d` à mão.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  type DuotoneGlyph,
  Glyph,
  parseGlyph,
  type RegularGlyph,
} from "../src/components/Glyph";

// Pelo caminho do arquivo, e não por `new URL`: no jsdom, o `URL` é o do navegador.
const HERE = dirname(fileURLToPath(import.meta.url));
const ICONS = resolve(HERE, "../../brand/ruvor/icons");
const SRC = resolve(HERE, "../src");

const REGULAR: RegularGlyph[] = [
  "arrow-left",
  "arrows-clockwise",
  "caret-right",
  "database",
  "info",
  "magnifying-glass",
  "spinner-gap",
  "x",
];
const DUOTONE: DuotoneGlyph[] = ["x-circle"];

/** Os `d` do arquivo, lidos à parte do componente. */
function fileDrawing(path: string): string[] {
  const svg = readFileSync(join(ICONS, path), "utf8");
  return [...svg.matchAll(/\bd="([^"]+)"/g)].map((match) => match[1]);
}

function renderedDrawing(container: HTMLElement): string[] {
  return [...container.querySelectorAll("svg > path")].map(
    (path) => path.getAttribute("d") ?? "",
  );
}

function listTsx(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return listTsx(path);
    return name.endsWith(".tsx") ? [path] : [];
  });
}

afterEach(() => {
  cleanup();
});

describe("Glyph", () => {
  it.each(REGULAR)("%s desenha o arquivo regular do conjunto", (name) => {
    const { container } = render(<Glyph name={name} />);
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("class")).toBe("ruvor-glyph");
    expect(svg?.getAttribute("viewBox")).toBe("0 0 256 256");
    expect(svg?.getAttribute("aria-hidden")).toBe("true");
    expect(renderedDrawing(container)).toEqual(fileDrawing(`regular/${name}.svg`));
  });

  it.each(DUOTONE)("%s duotone desenha o arquivo, com a camada de fundo", (name) => {
    const { container } = render(<Glyph name={name} weight="duotone" />);
    expect(renderedDrawing(container)).toEqual(fileDrawing(`duotone/${name}.svg`));
    const layers = container.querySelectorAll("svg > path");
    expect(layers[0].getAttribute("opacity")).toBe("0.2");
    expect(layers[1].hasAttribute("opacity")).toBe(false);
  });

  it("as classes a mais vêm depois de ruvor-glyph", () => {
    const { container } = render(<Glyph name="x" className="ruvor-glyph--sm" />);
    expect(container.querySelector("svg")?.getAttribute("class")).toBe(
      "ruvor-glyph ruvor-glyph--sm",
    );
  });

  it("arquivo fora da forma do conjunto é erro, não ícone vazio", () => {
    expect(() => parseGlyph("vazio", '<svg viewBox="0 0 256 256"></svg>')).toThrow();
    expect(() =>
      parseGlyph("caixa", '<svg viewBox="0 0 24 24"><path d="M0,0Z"/></svg>'),
    ).toThrow();
  });

  it("nenhum componente de frontend/src/ copia o desenho de um ícone", () => {
    const copied = listTsx(SRC).filter((file) =>
      /["'`]M-?\d/.test(readFileSync(file, "utf8")),
    );
    expect(copied).toEqual([]);
  });
});
