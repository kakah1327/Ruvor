# D-31 — Trabalho direto na main enquanto o time for uma pessoa

**Status:** aceita · 2026-09-01

## Contexto

O [PROCESSO](../PROCESSO.md) previa **ramo por plano**, e o F2a foi executado assim: 14
commits num ramo, integrados à `main` no fim.

Ramo existe para isolar trabalho paralelo — impedir que duas pessoas se atropelem, e manter
a `main` sempre entregável enquanto algo incompleto está em andamento. Hoje o
desenvolvimento é de uma pessoa só, e não existe versão publicada para proteger.

## Decisão

**O trabalho acontece direto na `main`** enquanto essas duas condições valerem.

Volta a haver ramo por plano quando **uma** delas mudar:

- mais de uma pessoa desenvolvendo ao mesmo tempo
- existir versão publicada, ou qualquer consumidor da `main` além do próprio time

## Consequências

- Um commit por tarefa continua valendo — é o que dá granularidade para revisar e reverter.
  O que sai é o isolamento em ramo, não a disciplina de commit.
- A `main` passa a conter estado intermediário durante a execução de um plano. É aceitável
  porque ninguém depende dela ainda.
- Reverter um bloco inteiro passa a ser `git revert` de um intervalo, em vez de descartar um
  ramo. Mais trabalhoso, e é o custo assumido.
- Substitui a instrução de ramo em [D-26](D-26-processo-de-desenvolvimento.md), sem revogar
  o resto do processo.
