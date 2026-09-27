# D-75 — As redes semeiam em cada retreino, com semente derivada da execução e da posição; estende a D-63

**Status:** aceita · 2026-09-27

## Contexto

A [D-63](D-63-semente-fixa-entra-no-manifesto.md) fixou a semente das três redes (`garchnet`,
`lstm`, `gru`) e a aplicou **uma vez**, no início de `_fit_for_alpha`. Cada retreino posterior
chama `model.fit` sobre o mesmo modelo, e o embaralhamento dos lotes consome o gerador aleatório
**de onde o processo parou**: o retreino na posição *k* dependia de tudo o que tinha rodado antes
no mesmo processo.

O M1.5b separa treino de previsão: um cálculo incremental, num processo novo, retoma o retreino
*k* a partir de um retrato, sem ter rodado os anteriores — e não tem aquele estado do gerador.
Guardar o estado do gerador junto com a rede seria a alternativa que não muda número; não há
garantia de que o TensorFlow permita capturá-lo de forma confiável.

## Decisão

**As três redes semeiam no início de cada retreino**, com `seeding.apply(position)`, e a
semente de cada posição sai de `seeding.derive(position)`, que combina a semente da execução com
a posição do ponto de retreino:

- `derive(0)` devolve **a semente da execução, sem transformação** — o treino inicial e a busca
  de configuração saem iguais aos do `0.2.0`;
- para `position > 0`, `(semente * 100_003 + position) mod (2**31 − 1)`: posições diferentes dão
  sementes diferentes, e sementes da execução diferentes dão sementes diferentes na mesma
  posição.

**O `caviar` não muda**: segue semeando por retreino com `int(alpha * 10000) + pos`, sem a
semente da execução, como a D-63 registra. Copiar esse padrão nas redes faria o embaralhamento
dos retreinos deixar de variar com o `--seed`.

## Consequências

- **É a exceção à [D-21](D-21-motor-ml-congelado-ate-etapa-6.md) que muda número, declarada.**
  Os números das três redes mudam em relação ao M1.4 e ao M1.5 **a partir do segundo trecho de
  teste**; o primeiro sai igual, e o V-04 o prova contra uma referência capturada com o `0.2.0`
  no `worker` (`engine/tests/fixtures/redes_trecho0.json`). O motor sobe para **`0.3.0`**.
- As execuções antigas em `gold` não são tocadas: carregam `engine_version` `0.2.0`.
- A Etapa 6 do TCC, que ainda não rodou, rodará sobre o `0.3.0`.
- A D-63 não é editada; passa a valer estendida por esta.

Origem: [spec M1.5b — Treino separado da previsão](../specs/M1.5b-treino-separado-da-previsao.md)
(RF-05).
