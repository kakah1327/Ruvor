# D-22 — Treino centralizado em uma maquina, em container

**Status:** aceita · 2026-08-29

## Contexto

Com 4 devs, a tentacao e dividir os 4 ativos entre as 4 maquinas para acelerar.

## Decisão

O treino roda em **uma maquina so, dentro de container, com semente fixa**.

## Consequências

- Se cada ativo rodar numa maquina diferente, e o ranking mostrar diferenca, **nao e possivel afirmar se veio do modelo ou da maquina**. Isso destroi a comparabilidade, que e justamente o que o TCC tenta provar.
- O container congela versao de Python e bibliotecas: deixa de importar de quem e a maquina.
- Paralelismo por nucleo, nao por pessoa.
