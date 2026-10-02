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
 * `conferencia-casco.md`.
 */
import type { TEXTOS, TextoKey } from "./textos";

/** Texto vira `string`; função mantém a assinatura (mesma chave, mesmos argumentos: RF-05). */
export type Leitura<T> = T extends string ? string : T;

/** As chaves já com frase avançada. Cresce seção a seção (T4, T7, T10, T13) até as 55 do RF-04. */
export const LEITURA_KEYS = [
  // O cabeçalho e o preço (T4).
  "ativo.ultimoFechamento",
  "ativo.precoAjustado",
] as const satisfies readonly TextoKey[];

export type LeituraKey = (typeof LEITURA_KEYS)[number];

export const TEXTOS_AVANCADOS: {
  readonly [K in LeituraKey]: Leitura<(typeof TEXTOS)[K]>;
} = {
  "ativo.ultimoFechamento": (data: string) =>
    `O fechamento do pregão de ${data}, o mais recente coletado, como o Yahoo Finance o informa — sem o ajuste por proventos do preço ajustado. A data é a do pregão no fuso da bolsa.`,
  "ativo.precoAjustado":
    "Fechamento ajustado como o Yahoo Finance o informa; o Ruvor não refaz o ajuste. A série vai do primeiro pregão coletado — a primeira coleta pede dez anos — até o último, e é pedida de novo inteira quando chega provento ou desdobramento novo, porque o ajuste muda todo o passado. Dela sai o retorno diário, o logaritmo da razão entre o fechamento ajustado e o do pregão anterior, que é o que vai aos modelos de risco.",
};
