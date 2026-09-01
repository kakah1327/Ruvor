# D-28 — Frontend em TypeScript

**Status:** aceita · 2026-08-31

## Contexto

O frontend do protótipo era JavaScript puro. Como ele é descartado inteiro e o projeto React
nasce de novo no F2b, a escolha entre JavaScript e TypeScript está aberta.

A [D-12](D-12-tipagem-obrigatoria.md) exige tipagem no Python, mas foi escrita pensando só no
backend e não diz nada sobre o frontend.

## Decisão

O frontend é escrito em **TypeScript**, com verificação estrita habilitada desde o primeiro
arquivo.

## Consequências

- A razão da D-12 vale igual aqui: o time vem de C#, Java e Angular, e produz mais com o
  compilador avisando antes de rodar. Escolher JavaScript desperdiçaria esse repertório.
- Rigor alto custa quase nada em código que nasce agora — e custa caro se for adicionado
  depois, quando já houver telas para converter.
- O contrato da API passa a poder ser tipado de ponta a ponta quando o Marco 1 chegar.
- Não afeta o `engine/` nem o `backend/`, que seguem a D-12.
