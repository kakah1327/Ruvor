/**
 * @vitest-environment node
 *
 * RF-04 do M1.6d: o `biome.json` usa `"preset": "recommended"`, e o campo
 * descontinuado `"recommended": true` não volta. Sem este teste, a volta dele só
 * apareceria como um aviso num lint que sai 0.
 *
 * O arquivo é JSON puro: se um dia ganhar comentário, o `JSON.parse` quebra, e
 * isso é aviso, não falha silenciosa.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const BIOME = fileURLToPath(new URL("../biome.json", import.meta.url));

interface BiomeConfig {
  linter: { rules: Record<string, unknown> };
}

const config = JSON.parse(readFileSync(BIOME, "utf8")) as BiomeConfig;

describe("biome.json", () => {
  it("liga o conjunto recomendado por preset", () => {
    expect(config.linter.rules.preset).toBe("recommended");
  });

  it("não tem o campo descontinuado recommended em linter.rules", () => {
    expect(Object.hasOwn(config.linter.rules, "recommended")).toBe(false);
  });
});
