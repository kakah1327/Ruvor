/**
 * As frases da leitura avançada (RF-05, D-152): uma por chave da lista fechada do RF-04, com a
 * mesma chave e a mesma assinatura da iniciante em `textos.ts`. Na leitura avançada, a frase
 * daqui **substitui** a iniciante; quem monta a frase chama `textFor` (`src/reading.ts`).
 *
 * Toda afirmação sobre o cálculo é conferida no código que calcula, pelos arquivos de
 * conferência de `docs/mockups/M2.3/`, e copiada do mockup aprovado.
 *
 * A avançada declara todos os parâmetros da iniciante, na mesma ordem, inclusive os que não
 * usa — com o prefixo `_` —, para o `Function.length` bater (V-02).
 *
 * `ativo.*`: do `casco-e-preco.html` (T3), literais; as afirmações são as de
 * `conferencia-casco.md`. `comportamento.*`: do `comportamento.html` (T6), literais; as
 * afirmações são as de `conferencia-comportamento.md`.
 */
import type { TEXTOS, TextoKey } from "./textos";

/** Texto vira `string`; função mantém a assinatura (mesma chave, mesmos argumentos: RF-05). */
export type Leitura<T> = T extends string ? string : T;

/** As chaves já com frase avançada. Cresce seção a seção (T4, T7, T10, T13) até as 55 do RF-04. */
export const LEITURA_KEYS = [
  // O cabeçalho e o preço (T4).
  "ativo.ultimoFechamento",
  "ativo.precoAjustado",
  // O comportamento (T7).
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
  "comportamento.histograma",
  "comportamento.skewness",
  "comportamento.excess_kurtosis",
  "comportamento.dividends_12m",
  "comportamento.dividend_payments_12m",
  "comportamento.dividend_yield_12m",
  "comportamento.avg_volume_21d",
  "comportamento.avg_volume_252d",
] as const satisfies readonly TextoKey[];

export type LeituraKey = (typeof LEITURA_KEYS)[number];

export const TEXTOS_AVANCADOS: {
  readonly [K in LeituraKey]: Leitura<(typeof TEXTOS)[K]>;
} = {
  "ativo.ultimoFechamento": (data: string) =>
    `O fechamento do pregão de ${data}, o mais recente coletado, como o Yahoo Finance o informa — sem o ajuste por proventos do preço ajustado. A data é a do pregão no fuso da bolsa.`,
  "ativo.precoAjustado":
    "Fechamento ajustado como o Yahoo Finance o informa; o Ruvor não refaz o ajuste. A série vai do primeiro pregão coletado — a primeira coleta pede dez anos — até o último, e é pedida de novo inteira quando chega provento ou desdobramento novo, porque o ajuste muda todo o passado. Dela sai o retorno diário, o logaritmo da razão entre o fechamento ajustado e o do pregão anterior, que é o que vai aos modelos de risco.",
  // O comportamento (T7): do `comportamento.html` aprovado, literais; as afirmações são as de
  // `conferencia-comportamento.md`.
  "comportamento.return_1m": (x: string) =>
    `Retorno simples, não logarítmico, do fechamento ajustado que o Yahoo Finance informa, na janela de 1 mês de calendário: o fechamento ajustado do último pregão sobre o do primeiro pregão da janela, menos 1. A janela começa no último pregão em ou antes de um mês de calendário antes do último pregão. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_3m": (x: string) =>
    `O mesmo cálculo, na janela de 3 meses de calendário. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_6m": (x: string) =>
    `O mesmo cálculo, na janela de 6 meses de calendário. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_12m": (x: string) =>
    `O mesmo cálculo, na janela de 12 meses de calendário. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_36m": (x: string) =>
    `O mesmo cálculo, na janela de 36 meses de calendário, acumulado, não anualizado. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_60m": (x: string) =>
    `O mesmo cálculo, na janela de 60 meses de calendário, acumulado, não anualizado. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_120m": (x: string) =>
    `O mesmo cálculo, na janela de 120 meses de calendário, acumulado, não anualizado. Sem pregão em ou antes do início da janela, o número é nulo. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_ytd": (x: string) =>
    `Retorno simples do preço ajustado desde o fechamento do último pregão antes do ano corrente (em regra, o do ano anterior) até o último pregão — não desde o primeiro pregão do ano corrente. Sem pregão antes do ano corrente, o número é nulo. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.volatility_12m": (v: string) =>
    `Desvio-padrão amostral (divisor n − 1) dos retornos logarítmicos diários — o logaritmo da razão entre o fechamento ajustado e o do pregão anterior — na janela de 12 meses de calendário, vezes √252 para a base anual: ${v}. Fica de fora o retorno do primeiro pregão da janela, que mede o movimento anterior a ela; com menos de 2 retornos, o número é nulo.`,
  "comportamento.volatility_60m": (v: string) =>
    `O mesmo desvio-padrão amostral (divisor n − 1) dos retornos logarítmicos diários, na janela de 60 meses de calendário, vezes √252: ${v}.`,
  "comportamento.max_drawdown": (
    queda: string,
    topo: string,
    fundo: string,
    desde: string,
    volta: string | null,
  ) =>
    `A maior queda da série inteira do fechamento ajustado que o Yahoo Finance informa, desde ${desde}: a razão mais negativa entre o fechamento ajustado de um pregão e o topo anterior a ele, menos 1 — do topo de ${topo} ao fundo de ${fundo}, uma queda de ${queda}. No empate, ficam o primeiro topo de um platô e a primeira queda de mesma profundidade. ${volta ? `A volta é o primeiro pregão depois do fundo cujo fechamento ajustado alcança o do topo: ${volta}.` : "Nenhum pregão depois do fundo alcançou o fechamento ajustado do topo: a volta nula é informação, não falta de histórico."}`,
  "comportamento.max_drawdown_recovery_sessions": (anos: string) =>
    `Pregões contados do fundo, exclusive, à volta ao topo, inclusive — fundo no pregão 5 e volta no 8 dão 3. Divididos por 252, o ano de bolsa, dão cerca de ${anos} anos.`,
  "comportamento.beta_60m": (b: string, oposta: boolean) =>
    `Inclinação da regressão linear por mínimos quadrados dos retornos logarítmicos diários da ação sobre os do Ibovespa, na janela de 60 meses de calendário da ação; cada retorno se emparelha com o do índice na mesma data, e o par só vale com o do índice não nulo. Com menos de 30 pares, nulo. Inclinação ${oposta ? "negativa" : "positiva ou nula"}: ${b} de retorno logarítmico da ação para cada 1% de retorno logarítmico do índice, em média.`,
  "comportamento.correlation_60m": (c: string) =>
    `Coeficiente de correlação de Pearson entre os retornos logarítmicos diários da ação e os do Ibovespa, sobre os mesmos pares do beta: 60 meses de calendário, emparelhados por data, mínimo de 30. Aqui, ${c}.`,
  "comportamento.histograma":
    "Contagem dos retornos logarítmicos diários da janela de 60 meses de calendário em 42 baldes: 40 de largura 0,005 (0,5 ponto), de −0,10 a +0,10, fechados à esquerda e abertos à direita, mais as duas pontas abertas — abaixo de −0,10 e a partir de +0,10. Têm a cor de queda os baldes cujo limite de cima não passa de zero; o dia de retorno exatamente zero cai no balde [0; 0,005), que tem a cor de alta.",
  "comportamento.skewness": (s: string, sinal: number) =>
    `Assimetria pelo estimador enviesado g1: o terceiro momento central, com divisor n, sobre o desvio-padrão populacional (divisor n) ao cubo, nos retornos logarítmicos diários da janela de 60 meses. Nula abaixo de 4 retornos ou com desvio zero. ${sinal < 0 ? `Aqui, ${s}: negativa.` : sinal > 0 ? `Aqui, ${s}: positiva.` : "Aqui, exatamente zero."}`,
  "comportamento.excess_kurtosis": (k: string, sinal: number) =>
    `Curtose em excesso pelo estimador enviesado g2: o quarto momento central, com divisor n, sobre o desvio-padrão populacional à quarta, menos 3 — zero é a curva normal. Mesma janela de 60 meses e mesmos mínimos da assimetria. Aqui, ${k}: ${sinal > 0 ? "acima de zero" : "zero ou abaixo"}.`,
  "comportamento.dividends_12m":
    "Soma dos valores dos eventos de dividendo que o Yahoo Finance informa, com data entre a do último pregão menos 12 meses de calendário e a do último pregão, inclusive nos dois extremos. Evento sem valor fica de fora; sem pagamento, a soma é zero, não nula.",
  "comportamento.dividend_payments_12m":
    "Quantidade dos mesmos eventos de dividendo que o Yahoo Finance informa, na janela de 12 meses de calendário, inclusive nos dois extremos — só os que têm valor.",
  "comportamento.dividend_yield_12m": (d: string, x: string) =>
    `A soma de 12 meses dos proventos dividida pelo fechamento não ajustado de ${d}, o último pregão. R$ 100 × o rendimento = ${x}.`,
  "comportamento.avg_volume_21d":
    "Média aritmética do volume dos últimos 21 pregões da série — contagem de pregões, não de meses —, com o volume de cada pregão como vem do Yahoo Finance. Com menos de 21 pregões, o número é nulo, nunca uma média parcial.",
  "comportamento.avg_volume_252d":
    "A mesma média aritmética do volume, sobre os últimos 252 pregões da série. Com menos de 252 pregões, nula — nunca uma média parcial.",
};
