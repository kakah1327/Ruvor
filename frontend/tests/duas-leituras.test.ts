/**
 * @vitest-environment node
 *
 * V-02, a lista fechada das duas leituras (RF-04, RF-05): as 55 chaves do RF-04, escritas aqui,
 * copiadas da spec. Cada chave com frase avançada (`LEITURA_KEYS`) está na lista, tem entrada em
 * `TEXTOS_AVANCADOS` com o mesmo tipo da iniciante (texto, ou função com o mesmo
 * `Function.length`), e o módulo avançado não tem chave fora de `LEITURA_KEYS`.
 *
 * A falha silenciosa é a chave que nunca ganha avançada e ninguém nota: `PENDENTES` diz quais
 * ainda não têm, e `AS_55 − LEITURA_KEYS` tem de ser exatamente ela — nem mais, nem menos. Cada
 * tarefa de seção tira as suas de `PENDENTES`; a T13 apaga a constante e confere `LEITURA_KEYS`
 * igual a `AS_55`.
 */
import { describe, expect, it } from "vitest";

import { LEITURA_KEYS, TEXTOS_AVANCADOS } from "../src/content/avancado";
import { TEXTOS, type TextoKey } from "../src/content/textos";

const AS_55 = [
  // RF-21 do M1.6b (`LISTA_FECHADA` de textos.test.ts): os 19 campos de `CAMPOS_COM_FRASE`…
  "comportamento.return_1m",
  "comportamento.return_3m",
  "comportamento.return_6m",
  "comportamento.return_12m",
  "comportamento.return_36m",
  "comportamento.return_60m",
  "comportamento.return_120m",
  "comportamento.return_ytd",
  "comportamento.volatility_12m",
  "comportamento.volatility_60m",
  "comportamento.max_drawdown",
  "comportamento.max_drawdown_recovery_sessions",
  "comportamento.beta_60m",
  "comportamento.correlation_60m",
  "comportamento.dividends_12m",
  "comportamento.dividend_payments_12m",
  "comportamento.dividend_yield_12m",
  "comportamento.avg_volume_21d",
  "comportamento.avg_volume_252d",
  // …o histograma, a assimetria e a curtose…
  "comportamento.histograma",
  "comportamento.skewness",
  "comportamento.excess_kurtosis",
  // …o risco…
  "risco.perda95",
  "risco.perda99",
  "risco.discordancia",
  "risco.veredito",
  "risco.naoRejeitados",
  "risco.violacoes",
  "risco.kupiec",
  "risco.christoffersen",
  "risco.dq",
  // …e o preço. São 33.
  "ativo.ultimoFechamento",
  "ativo.precoAjustado",
  // RF-06 do M1.6c: os números da seção Fundamentos, e a variante `closeOutraData`. São 19.
  "fundamentos.revenue_ttm",
  "fundamentos.ebit_ttm",
  "fundamentos.net_income_ttm",
  "fundamentos.net_margin",
  "fundamentos.ebit_margin",
  "fundamentos.roe",
  "fundamentos.gross_debt",
  "fundamentos.cash",
  "fundamentos.net_debt",
  "fundamentos.net_debt_to_equity",
  "fundamentos.close",
  "fundamentos.eps",
  "fundamentos.bvps",
  "fundamentos.pe",
  "fundamentos.pb",
  "fundamentos.equity_parent",
  "fundamentos.total_assets",
  "fundamentos.market_cap",
  "fundamentos.closeOutraData",
  // RF-10 do M1.6c: a posição entre os pares. São 3.
  "fundamentos.pares.posicao",
  "fundamentos.pares.abaixoDeTodas",
  "fundamentos.pares.mediana",
] as const satisfies readonly TextoKey[];

// As chaves de AS_55 ainda sem frase avançada. Nasce com as 55; cada seção tira as suas.
const PENDENTES = [
  "comportamento.return_1m",
  "comportamento.return_3m",
  "comportamento.return_6m",
  "comportamento.return_12m",
  "comportamento.return_36m",
  "comportamento.return_60m",
  "comportamento.return_120m",
  "comportamento.return_ytd",
  "comportamento.volatility_12m",
  "comportamento.volatility_60m",
  "comportamento.max_drawdown",
  "comportamento.max_drawdown_recovery_sessions",
  "comportamento.beta_60m",
  "comportamento.correlation_60m",
  "comportamento.dividends_12m",
  "comportamento.dividend_payments_12m",
  "comportamento.dividend_yield_12m",
  "comportamento.avg_volume_21d",
  "comportamento.avg_volume_252d",
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
  "fundamentos.revenue_ttm",
  "fundamentos.ebit_ttm",
  "fundamentos.net_income_ttm",
  "fundamentos.net_margin",
  "fundamentos.ebit_margin",
  "fundamentos.roe",
  "fundamentos.gross_debt",
  "fundamentos.cash",
  "fundamentos.net_debt",
  "fundamentos.net_debt_to_equity",
  "fundamentos.close",
  "fundamentos.eps",
  "fundamentos.bvps",
  "fundamentos.pe",
  "fundamentos.pb",
  "fundamentos.equity_parent",
  "fundamentos.total_assets",
  "fundamentos.market_cap",
  "fundamentos.closeOutraData",
  "fundamentos.pares.posicao",
  "fundamentos.pares.abaixoDeTodas",
  "fundamentos.pares.mediana",
] as const satisfies readonly TextoKey[];

const ordenada = (chaves: readonly string[]): string[] => [...chaves].sort();

describe("V-02 — a lista fechada das duas leituras", () => {
  it("AS_55 tem 55 chaves distintas, todas em TEXTOS", () => {
    expect(new Set(AS_55).size).toBe(55);
    expect(AS_55.filter((k) => !Object.hasOwn(TEXTOS, k))).toEqual([]);
  });

  it("LEITURA_KEYS não repete chave e está contida em AS_55", () => {
    const chaves: readonly string[] = LEITURA_KEYS;
    expect(new Set(chaves).size).toBe(chaves.length);
    expect(chaves.filter((k) => !(AS_55 as readonly string[]).includes(k))).toEqual([]);
  });

  it("AS_55 − LEITURA_KEYS é exatamente PENDENTES", () => {
    const comAvancada: readonly string[] = LEITURA_KEYS;
    const faltam = AS_55.filter((k) => !comAvancada.includes(k));
    expect(new Set(PENDENTES).size).toBe(PENDENTES.length);
    expect(ordenada(faltam)).toEqual(ordenada(PENDENTES));
  });

  it("o módulo avançado tem exatamente as chaves de LEITURA_KEYS", () => {
    expect(ordenada(Object.keys(TEXTOS_AVANCADOS))).toEqual(ordenada(LEITURA_KEYS));
  });

  it("cada chave de LEITURA_KEYS tem avançada com o tipo e a aridade da iniciante", () => {
    const divergentes: string[] = [];
    for (const chave of LEITURA_KEYS as readonly TextoKey[]) {
      const avancada = (TEXTOS_AVANCADOS as Record<string, unknown>)[chave];
      const iniciante = TEXTOS[chave] as unknown;
      if (avancada === undefined) {
        divergentes.push(`${chave}: sem avançada`);
      } else if (typeof avancada !== typeof iniciante) {
        divergentes.push(`${chave}: ${typeof avancada} ≠ ${typeof iniciante}`);
      } else if (
        typeof avancada === "function" &&
        typeof iniciante === "function" &&
        avancada.length !== iniciante.length
      ) {
        divergentes.push(`${chave}: aridade ${avancada.length} ≠ ${iniciante.length}`);
      }
    }
    expect(divergentes).toEqual([]);
  });
});
