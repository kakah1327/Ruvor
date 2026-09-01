# D-09 — Construcao de uma camada por vez, cada uma com sua spec

**Status:** aceita · 2026-08-29

## Contexto

O produto tem cinco camadas de analise e varios subsistemas. Especificar tudo junto produz spec vaga — que foi o diagnostico do estado anterior.

## Decisão

Cada bloco recebe **spec propria, plano proprio e implementacao propria**, e e visto funcionando antes do proximo comecar.

## Consequências

- Nenhuma spec cobre mais de um bloco.
- O roadmap define a ordem; o ESTADO registra onde estamos.
- Ver `docs/PROCESSO.md`.
