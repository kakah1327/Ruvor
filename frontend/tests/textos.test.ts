/**
 * @vitest-environment node
 *
 * V-14, a metade do módulo: toda chave da lista fechada do RF-21 — cada número de análise tem
 * uma frase fixa — existe em `TEXTOS`. A outra metade, a frase na tela junto do número, é dos
 * testes de cada seção.
 *
 * A lista é a do plano: `comportamento.<campo>` para cada campo do RF-10 menos as três datas
 * da maior queda e as duas contagens, que entram na frase de `comportamento.max_drawdown` e nas
 * notas dos blocos; o histograma, a assimetria e a curtose; a perda a 95% e a 99%, a
 * discordância, o veredito e o não rejeitado; violações, Kupiec, Christoffersen e DQ; o último
 * fechamento e o preço ajustado.
 */
import { describe, expect, it } from "vitest";

import { TEXTOS } from "../src/content/textos";

const CAMPOS_COM_FRASE = [
  "return_1m",
  "return_3m",
  "return_6m",
  "return_12m",
  "return_36m",
  "return_60m",
  "return_120m",
  "return_ytd",
  "volatility_12m",
  "volatility_60m",
  "max_drawdown",
  "max_drawdown_recovery_sessions",
  "beta_60m",
  "correlation_60m",
  "dividends_12m",
  "dividend_payments_12m",
  "dividend_yield_12m",
  "avg_volume_21d",
  "avg_volume_252d",
];

const LISTA_FECHADA = [
  ...CAMPOS_COM_FRASE.map((campo) => `comportamento.${campo}`),
  "comportamento.histograma",
  "comportamento.skewness",
  "comportamento.excess_kurtosis",
  "risco.perda95",
  "risco.perda99",
  "risco.discordancia",
  "risco.veredito",
  "risco.naoRejeitados",
  "risco.violacoes",
  "risco.kupiec",
  "risco.christoffersen",
  "risco.dq",
  "ativo.ultimoFechamento",
  "ativo.precoAjustado",
  // As seis frases de medida dos momentos de estresse (M3.3, D-97).
  "comportamento.estresse.period_return",
  "comportamento.estresse.benchmark_period_return",
  "comportamento.estresse.drawdown",
  "comportamento.estresse.benchmark_drawdown",
  "comportamento.estresse.recovery_sessions",
  "comportamento.estresse.benchmark_recovery_sessions",
  // A lista fechada do laboratório (M2.4, D-97): as nove do portão do `laboratorio.html`.
  "laboratorio.decada",
  "laboratorio.diferenca",
  "laboratorio.violacoesAno",
  "laboratorio.vereditoAno",
  "laboratorio.anoNaoJulgado",
  "laboratorio.semVereditoAno99",
  "laboratorio.violacoesDecada",
  "laboratorio.vereditoDecada",
  "laboratorio.anosNaoRejeitados",
  // A lista fechada do retorno (M5.1, D-97): as sete do portão do `retorno.html`.
  "retorno.veredito",
  "retorno.r2_os",
  "retorno.acerto",
  "retorno.dm",
  "retorno.cw",
  "retorno.pt",
  "retorno.previsao",
];

// Os campos do RF-10 que não têm frase própria: entram na frase ou na nota do bloco.
const SEM_FRASE = [
  "max_drawdown_peak_date",
  "max_drawdown_trough_date",
  "max_drawdown_recovery_date",
  "benchmark_observations",
  "statistical_observations",
];

describe("V-14 — a lista fechada do RF-21 no módulo de textos", () => {
  it("a lista tem as 55 chaves", () => {
    expect(new Set(LISTA_FECHADA).size).toBe(55);
  });

  it.each(LISTA_FECHADA)("%s existe e não é vazia", (chave) => {
    expect(Object.hasOwn(TEXTOS, chave)).toBe(true);
    const valor = (TEXTOS as Record<string, unknown>)[chave];
    expect(["string", "function"]).toContain(typeof valor);
    if (typeof valor === "string") expect(valor.trim()).not.toBe("");
  });

  it.each(SEM_FRASE)("%s não tem frase própria", (campo) => {
    expect(Object.hasOwn(TEXTOS, `comportamento.${campo}`)).toBe(false);
  });
});
