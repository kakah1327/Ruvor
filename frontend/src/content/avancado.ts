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
 */
import type { TEXTOS, TextoKey } from "./textos";

/** Texto vira `string`; função mantém a assinatura (mesma chave, mesmos argumentos: RF-05). */
export type Leitura<T> = T extends string ? string : T;

/** As chaves já com frase avançada. Cresce seção a seção (T4, T7, T10, T13) até as 55 do RF-04. */
export const LEITURA_KEYS = [] as const satisfies readonly TextoKey[];

export type LeituraKey = (typeof LEITURA_KEYS)[number];

export const TEXTOS_AVANCADOS: {
  readonly [K in LeituraKey]: Leitura<(typeof TEXTOS)[K]>;
} = {};
