# D-97 — No Marco 1, cada número tem uma frase fixa; as duas leituras continuam no M2.3

**Status:** aceita · 2026-09-28 · restringe a [PRODUTO §2](../PRODUTO.md#2-público-e-postura) no Marco 1

## Contexto

A [PRODUTO §2](../PRODUTO.md#2-público-e-postura) exige que todo número exibido carregue explicação
em linguagem clara, junto do dado. A PRODUTO §4 põe a "camada explicativa iniciante/avançado como
sistema" no Marco 2 (M2.3). A primeira tela de produto, no M1.6b, precisava decidir o quanto entra
antes.

## Decisão

1. **Cada número de análise tem uma frase curta, fixa, ao lado dele** — uma leitura só, em linguagem
   clara. A frase pode usar o próprio valor e nunca recomenda. Número de análise é o que descreve o
   ativo ou o risco dele: retornos, volatilidade, quedas, relação com o índice, distribuição,
   proventos, volume, perdas estimadas, vereditos e testes. **Não é número de análise** o metadado do
   método (pregões usados, semente, versão, instantes), o dado bruto rotulado (o valor de um
   provento) nem a contagem de progresso — esses vêm com rótulo, e o bloco deles tem uma frase só.
2. **Os textos nascem nos mockups e são aprovados no portão**; aprovados, moram num só módulo do
   frontend, uma entrada por chave.
3. **A alternância iniciante/avançado, com dois textos por métrica, continua no M2.3**, que substitui
   esse módulo.

## Consequências

- O M1.6b fixa a lista do que tem frase, e um teste confere que todo item tem texto e aparece junto
  do número.
- No Marco 1 o texto é versionado com o frontend, não com a métrica no banco, como a PRODUTO §2
  descreve para o sistema completo. O M2.3 decide onde ele mora.

Origem: [spec M1.6b — As telas](../specs/M1.6b-as-telas.md) (RF-21).
