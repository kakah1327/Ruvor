# D-96 — A discordância entre modelos e os não rejeitados por ativo entram no Marco 1

**Status:** aceita · 2026-09-28 · promove os candidatos 5.1 e 5.2 da [PRODUTO §5](../PRODUTO.md#5-requisitos-candidatos)

## Contexto

A PRODUTO §8 sugeria 5.1, 5.2 e 5.3 para o Marco 1, sem decisão. Os dois primeiros saem do que a
API do M1.6a já entrega: o `var_latest` dos nove modelos por nível e o `adequate` de cada
(modelo, nível). O 5.3 (estresse histórico) não tem rota.

## Decisão

1. **5.1 — a discordância entra**: por nível, a faixa entre a menor e a maior perda estimada pelos
   modelos que calcularam, dita como informação ("os modelos estimam entre X% e Y%"). O limite
   entre "próximos" e "distantes" **não** é fixado: a tela mostra a faixa e explica, sem
   classificar.
2. **5.2 — os não rejeitados entram, pela [D-65](D-65-a-plataforma-lista-os-aprovados-e-nao-elege-nenhum.md)**:
   por nível, a lista dos modelos com `adequate = true`, em ordem fixa, **sem eleger nenhum** — sem
   ranking, sem pontuação, sem "recomendado". "Nenhum adequado" e "não julgado" têm frase própria.
3. **5.3 e o resto continuam candidatos.**

## Consequências

- A pontuação de evidência e o ranking dos mockups de referência `02` e `04` não entram na tela.
- A PRODUTO §5 e §8 passam a dizer que 5.1 e 5.2 estão no Marco 1.

Origem: [spec M1.6b — As telas](../specs/M1.6b-as-telas.md) (RF-13, RF-14).
