# D-05 — Horizonte de semanas primeiro, meses depois

**Status:** aceita · 2026-08-29

## Contexto

O padrao regulatorio de Basileia II e 1 dia, e e o que o prototipo implementa. Mas quem pergunta "se eu aplicar" pensa em semanas ou meses.

## Decisão

O horizonte alvo e de **semanas** na primeira versao; meses ficam para depois.

## Consequências

- Quanto mais longo o horizonte, **menos evidencia** existe para validar: 1 dia da ~2.500 pontos de conferencia em 10 anos; 4 semanas da ~120 periodos independentes.
- Com ~120 pontos, os testes estatisticos quase nao detectam nada. Exige janelas sobrepostas com correcao estatistica.
- A spec precisa assumir isso explicitamente, nao descobrir na execucao.
