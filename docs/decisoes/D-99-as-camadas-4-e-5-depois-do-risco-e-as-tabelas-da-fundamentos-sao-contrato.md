# D-99 — As camadas 4 e 5 entram depois do risco, e as tabelas da `fundamentos` que a tela lê são contrato

**Status:** aceita · 2026-09-29 · estende a [D-95](D-95-o-m1-6-em-tres-blocos.md)

## Contexto

A D-95 mandou o M1.6c acrescentar à tela do ativo as camadas 4 (fundamentos) e 5 (contexto), com as
rotas escritas pela `marco1` sobre as tabelas da `fundamentos`. Três escolhas ficaram para a spec dele:
onde as seções entram, com que garantia a `marco1` lê tabelas de outra frente, e qual comparação com os
pares a tela mostra — a tabela `gold.peer_comparison` é imutável, uma linha por cálculo, e a segunda fase
do cálculo pode falhar e deixar o indicador mais recente sem comparação (RF-15 do M3.2).

## Decisão

1. **As seções Fundamentos e Comunicados da companhia à CVM entram depois do risco**, que continua onde o
   M1.6b o pôs (decisão do dono da frente, 2026-09-29): o risco é o diferencial, e os fundamentos e os
   comunicados vêm como leitura complementar.
2. **As tabelas lidas viram contrato "só cresce"** em [FRENTES.md](../FRENTES.md#contratos-entre-frentes) —
   `gold.fundamental_indicator`, `gold.peer_comparison`, `silver.disclosure`, `silver.company` e as três
   colunas de `silver.financial_statement` que a tela mostra: coluna nova pode; mudar o sentido,
   renomear ou tirar uma coluna lida exige a revisão da `marco1`. As listas fechadas de valores que a tela
   traduz (`account_plan`, `per_share_missing`, `market_cap_missing`, `peer_level`, `category`) também.
3. **A posição entre os pares é a do próprio indicador** — a ligação um-para-um do M3.2 —, não a
   comparação mais recente: a posição fala dos mesmos números que a tela mostra. Indicador sem comparação
   mostra "sem comparação", e não a de outro cálculo.

## Consequências

- A tela passa a pedir sete rotas; a taxa do anônimo do M4.2 pesa mais, e a spec do M1.6c a mede.
- A `fundamentos` passa a revisar a PR de quem mudar o que a tela lê, e a `marco1` a revisar a dela.
- Fecha a faixa D-85 a D-99 da `marco1`; a próxima, D-140 a D-159, é reservada em FRENTES.md.

Origem: [spec M1.6c — Fundamentos e contexto na tela](../specs/M1.6c-fundamentos-e-contexto.md).
