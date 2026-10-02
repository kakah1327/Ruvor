/**
 * @vitest-environment node
 *
 * V-13, o lado do frontend do contrato dos motivos (RF-18): cada motivo da lista fechada de
 * `backend/apps/api/ondemand.py` vira a **sua** frase — não a genérica —, com o número
 * extraído; um motivo desconhecido cai na genérica, com o texto cru entre parênteses.
 *
 * A lista é escrita aqui, igual à de `backend/tests/api/test_motivos.py`: nenhum contêiner vê
 * o backend e o frontend juntos. Mudou o contrato dos motivos do pedido? Atualize
 * `frontend/src/content/motivos.ts`, esta lista e a do teste do backend.
 */
import { describe, expect, it } from "vitest";

import { MOTIVOS_CONHECIDOS, traduzirMotivo } from "../src/content/motivos";
import { TEXTOS } from "../src/content/textos";
import { MIN_SESSIONS } from "../src/risk/config";

// A lista fechada do RF-18, com `N` no lugar do número.
const LISTA = [
  "calculado",
  "serie curta (N pregoes, minimo 503)",
  "falhou na coleta",
  "falhou nas metricas",
  "falhou na abertura",
  "a execucao falhou",
  "o broker recusou o pedido",
  "expirado (N min)",
];

// Cada motivo da lista, com o número que a API mandaria, e a frase que ele tem de virar.
const CASOS: ReadonlyArray<readonly [string, string]> = [
  ["calculado", "O cálculo terminou."],
  [
    "serie curta (1234 pregoes, minimo 503)",
    "A série tem 1.234 pregões; o risco pede no mínimo 503.",
  ],
  ["falhou na coleta", "A coleta dos preços deste ativo falhou."],
  [
    "falhou nas metricas",
    "Os preços foram coletados, mas o cálculo do comportamento falhou.",
  ],
  [
    "falhou na abertura",
    "Os preços e o comportamento ficaram prontos, mas o cálculo do risco não conseguiu começar.",
  ],
  [
    "a execucao falhou",
    "O cálculo do risco começou, mas nenhum modelo chegou a um resultado.",
  ],
  [
    "o broker recusou o pedido",
    "O pedido não chegou a entrar na fila de cálculo, por uma falha do servidor.",
  ],
  ["expirado (45 min)", "O pedido passou de 45 minutos sem terminar e foi encerrado."],
];

const generica = (raw: string): string => TEXTOS["motivos.desconhecido"](raw);

describe("V-13 — os motivos do pedido", () => {
  it("a lista do módulo é a lista do contrato", () => {
    expect([...MOTIVOS_CONHECIDOS]).toEqual(LISTA);
  });

  it("cada motivo da lista tem um caso aqui, na mesma ordem", () => {
    const forma = (reason: string): string =>
      reason.replace(/\d+(?= pregoes| min)/, "N");
    expect(CASOS.map(([reason]) => forma(reason))).toEqual(LISTA);
  });

  it.each(CASOS)("%s vira a sua frase", (reason, frase) => {
    const traduzido = traduzirMotivo(reason);
    expect(traduzido).toBe(frase);
    expect(traduzido).not.toBe(generica(reason));
    expect(traduzido).not.toContain(reason);
  });

  it("as frases são duas a duas diferentes", () => {
    const frases = CASOS.map(([reason]) => traduzirMotivo(reason));
    expect(new Set(frases).size).toBe(CASOS.length);
  });

  it("o número vem do motivo, não de uma constante", () => {
    expect(traduzirMotivo("serie curta (12 pregoes, minimo 503)")).toBe(
      "A série tem 12 pregões; o risco pede no mínimo 503.",
    );
    expect(traduzirMotivo("serie curta (287 pregoes, minimo 600)")).toBe(
      "A série tem 287 pregões; o risco pede no mínimo 600.",
    );
    expect(traduzirMotivo("expirado (30 min)")).toBe(
      "O pedido passou de 30 minutos sem terminar e foi encerrado.",
    );
  });

  it.each([
    "qualquer outro texto",
    "Calculado",
    "calculado ",
    "serie curta (N pregoes, minimo 503)",
    "serie curta (12 pregoes)",
    "expirado",
    "expirado (30 minutos)",
    "",
  ])("o desconhecido %j cai na genérica, com o texto cru", (reason) => {
    expect(traduzirMotivo(reason)).toBe(generica(reason));
    expect(traduzirMotivo(reason)).toContain(`(${reason})`);
  });

  it("o mínimo de pregões do frontend é 503", () => {
    expect(MIN_SESSIONS).toBe(503);
  });
});
