/**
 * @vitest-environment node
 *
 * V-11 do M1.4b: as avançadas de `risco.perda95` e `risco.perda99` dizem, literalmente, o que
 * o RF-14 da spec `docs/specs/M1.4b-correcao-do-motor.md` aprovou no portão (D-158). O texto
 * fica escrito aqui, inteiro: qualquer mudança — inclusive a frase velha do M2.3 de volta —
 * reprova.
 */
import { describe, expect, it } from "vitest";

import { TEXTOS_AVANCADOS } from "../src/content/avancado";

/** As duas frases do RF-14, literais (os blocos citados da spec, numa linha só). */
const RF14 = {
  "risco.perda95":
    "VaR de 1 dia a 95%: o quantil de 5% do retorno logarítmico diário, com o sinal trocado — espera-se um retorno abaixo de −VaR em 5% dos dias. Cada modelo estima esse quantil do seu jeito, nunca com o retorno do próprio dia: nos seis que se atualizam a cada pregão, o número mostrado é o do último pregão, com os dados até a véspera; nos três tradicionais — histórico, paramétrico e Monte Carlo —, ele só muda quando o modelo é reestimado, a cada 252 pregões, sobre todos os retornos conhecidos até ali. Vai à tela como perda percentual simples, 1 − e^(−VaR).",
  "risco.perda99":
    "O mesmo VaR a 99%: o quantil de 1% — espera-se um retorno abaixo de −VaR em 1% dos dias —, estimado e mostrado da mesma forma.",
} as const;

describe("V-11 — as frases do RF-14", () => {
  it.each(Object.entries(RF14))("%s é a do RF-14", (chave, frase) => {
    expect(TEXTOS_AVANCADOS[chave as keyof typeof RF14]).toBe(frase);
  });
});
