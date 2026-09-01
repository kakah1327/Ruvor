# D-17 — Monorepo, com o motor numerico isolado do Django

**Status:** aceita · 2026-08-29

## Contexto

O motor numerico e o ativo cientifico do projeto e carrega dependencias pesadas (TensorFlow passa de meio giga). O framework web e detalhe de entrega.

## Decisão

**Monorepo**, com `engine/` como pacote Python puro que **nao importa Django em hipotese alguma**.

## Consequências

- O motor roda sem a plataforma: a Etapa 6 do TCC pode ser executada por linha de comando hoje.
- Duas imagens Docker do mesmo codigo: `web` leve, `worker` pesado.
- E testavel isoladamente, o que da credibilidade cientifica.
- Pode ser publicado como pacote aberto — o que torna verdadeira a afirmacao do TCC sobre codigo aberto para ensino e pesquisa, sem mudar a justificativa da pesquisa.
