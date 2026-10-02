/**
 * @vitest-environment node
 *
 * V-06 do M2.3, a D-64 nos dois níveis (RF-08): o veredito fala da série no período de teste,
 * não do número de hoje — e a frase tem de dizer isso, por chave e por ramo.
 *
 * A expressão de cada chave, aprovada no portão do `risco.html` (T9), fica escrita aqui. O
 * portão escolheu a alternativa da conferência: **uma expressão só para as duas chaves**, "não
 * do número de hoje".
 *
 * - `risco.veredito` é texto: as duas entradas contêm a expressão;
 * - `risco.naoRejeitados`: a expressão em cada saída dos exemplos com `julgados > 0` de
 *   `EXEMPLOS` (iniciante) e de `EXEMPLOS_AVANCADOS` (avançada) — os ramos `k ≥ 1` e `k = 0`.
 *   O ramo `julgados = 0` é isento (não há veredito) e fica fora **pelo filtro**, não por lista;
 *   e cada registro tem ao menos um exemplo de `k ≥ 1` e um de `k = 0`.
 */
import { describe, expect, it } from "vitest";

import { TEXTOS_AVANCADOS } from "../src/content/avancado";
import { TEXTOS } from "../src/content/textos";
import { EXEMPLOS, EXEMPLOS_AVANCADOS } from "./exemplos";

/** As expressões aprovadas no portão da T9, uma por chave. */
const EXPRESSAO = {
  "risco.veredito": "não do número de hoje",
  "risco.naoRejeitados": "não do número de hoje",
} as const;

type NaoRejeitadosArgs = readonly [k: number, julgados: number, total: number];

const REGISTROS = [
  {
    nivel: "iniciante",
    exemplos: EXEMPLOS,
    frase: TEXTOS["risco.naoRejeitados"],
  },
  {
    nivel: "avançada",
    exemplos: EXEMPLOS_AVANCADOS,
    frase: TEXTOS_AVANCADOS["risco.naoRejeitados"],
  },
] as const;

type Exemplos = (typeof REGISTROS)[number]["exemplos"];

/** Todos os exemplos de `risco.naoRejeitados` de um registro. */
function todos(exemplos: Exemplos): NaoRejeitadosArgs[] {
  return (exemplos["risco.naoRejeitados"] ?? []) as NaoRejeitadosArgs[];
}

/** Os exemplos com veredito: `julgados > 0` — os ramos `k ≥ 1` e `k = 0`. */
function julgados(exemplos: Exemplos): NaoRejeitadosArgs[] {
  return todos(exemplos).filter(([, j]) => j > 0);
}

describe("V-06 — risco.veredito, nas duas leituras", () => {
  it.each([
    ["iniciante", TEXTOS["risco.veredito"]],
    ["avançada", TEXTOS_AVANCADOS["risco.veredito"]],
  ])("a %s contém a expressão", (_nivel, frase) => {
    expect(frase).toContain(EXPRESSAO["risco.veredito"]);
  });
});

describe.each(REGISTROS)(
  "V-06 — risco.naoRejeitados, na $nivel",
  ({ exemplos, frase }) => {
    it("cada exemplo com julgados > 0 contém a expressão", () => {
      const casos = julgados(exemplos);
      expect(casos.length).toBeGreaterThan(0);
      const faltam = casos.filter(
        (args) => !frase(...args).includes(EXPRESSAO["risco.naoRejeitados"]),
      );
      expect(faltam).toEqual([]);
    });

    it("há exemplo do ramo k ≥ 1 e do ramo k = 0 entre os julgados", () => {
      const casos = julgados(exemplos);
      expect(casos.some(([k]) => k >= 1)).toBe(true);
      expect(casos.some(([k]) => k === 0)).toBe(true);
    });

    it("o exemplo com julgados = 0 está no registro e o filtro o tira", () => {
      const isentos = todos(exemplos).filter(([, j]) => j === 0);
      expect(isentos.length).toBeGreaterThan(0);
      const casos = julgados(exemplos);
      for (const isento of isentos) expect(casos).not.toContain(isento);
      expect(casos).toHaveLength(todos(exemplos).length - isentos.length);
    });
  },
);
