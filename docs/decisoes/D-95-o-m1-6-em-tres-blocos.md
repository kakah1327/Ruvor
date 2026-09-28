# D-95 — O M1.6 em três blocos: as camadas 4 e 5 vão para o M1.6c

**Status:** aceita · 2026-09-28

## Contexto

O M1.6 foi dividido em 2026-09-27: o M1.6a entregou o kit, a API e o cálculo sob demanda; o M1.6b
entregaria as telas. Ao abrir a spec do M1.6b, o dono da frente decidiu que a tela do ativo mostra
as **cinco** camadas — inclusive fundamentos (M3.1) e contexto (M3.2), que já estão em `gold` e em
`silver` pela frente `fundamentos`. Mas a API não tem rota para `gold.fundamental_indicator`,
`gold.peer_comparison` nem `silver.disclosure`, e a spec do M1.6a deixou a exposição com a
`fundamentos`, que está parada. Com casco, busca, tela e rotas novas, o bloco ficava grande.

## Decisão

1. **O M1.6b entrega o casco, a busca e a tela do ativo com as camadas 1 a 3**, e fecha o Marco 1.
2. **O M1.6c acrescenta à mesma tela as camadas 4 e 5**, com as rotas que faltam.
3. **As rotas das camadas 4 e 5 são escritas pela `marco1`, em `apps/api`**, lendo os modelos de
   `apps/fundamentals` só para leitura. As tabelas lidas passam a ser contrato entre frentes — a
   `fundamentos` produz, a `marco1` consome —, e **a PR do M1.6c passa pela revisão da
   `fundamentos`**, como toda PR que consome contrato de outra frente.

## Consequências

- O ROADMAP ganha o M1.6c depois do M1.6b. O Marco 1 fecha com o M1.6b; o M1.6c completa, na tela,
  o Marco 3, embora more na frente `marco1`.
- A tela do M1.6b não reserva lugar vazio para as camadas 4 e 5.
- A spec do M1.6c lista, em [FRENTES.md](../FRENTES.md#contratos-entre-frentes), as tabelas e as
  colunas que viram contrato.

Origem: [spec M1.6b — As telas](../specs/M1.6b-as-telas.md).
