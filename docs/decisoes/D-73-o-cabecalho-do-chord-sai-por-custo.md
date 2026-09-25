# D-73 — O cabeçalho do `chord` sai por custo, não na ordem pedida

**Status:** aceita · 2026-09-25

## Contexto

A [D-67](D-67-uma-tarefa-por-ativo-e-modelo-restringe-o-rf-12-do-m1-4.md) criou uma tarefa por
(ativo, modelo), e a abertura as enfileirava na ordem pedida — a alfabética de `MODELS` quando
nada se pede. A execução real do M1.5 mediu o efeito: com a fila por ordem de chegada e duas
vagas no `worker`, as redes tomavam as vagas e os modelos baratos esperavam atrás delas. No
IBOV, `historical` esperou ~1 min 40 s, `monte_carlo` e `parametric` ~2 min 25 s. A promessa do
modo A ([D-07](D-07-resposta-progressiva-modo-a.md)) — os rápidos na hora — não se cumpria.

## Decisão

**A abertura ordena o cabeçalho do `chord` por categoria de modelo: tradicionais, GARCH, ML.**
Dentro de cada categoria vale a ordem pedida (ordenação estável). A ordem de custo mora em
`_COST_RANK`, em `backend/apps/risk/tasks.py`, e lê a `category` que cada modelo já declara no
motor — nenhuma lista de nomes a manter.

O `requested_models` gravado na `risk_run` **continua na ordem pedida**: é o que o fecho
compara, e a ordem de execução não é contrato de ninguém.

## Consequências

- Dentro de um ativo, os modelos baratos passam a gravar antes das redes.
- **Entre ativos, a espera continua.** A fila é por ordem de chegada: os ativos seguintes
  esperam atrás das redes do primeiro. Resolver isso exige fila própria para as redes com
  processo dedicado — infraestrutura nova — ou o [M1.5b](../ROADMAP.md), que faz a previsão das
  redes ser uma passada só e tira o problema pela raiz. Fica com o M1.5b.
- O V-02 do M1.5 muda: o cabeçalho é conferido na ordem de custo, não na pedida.
- O `caviar` é da categoria `ml` e vai junto das redes, embora não seja rede. A categoria é a
  aproximação de custo disponível sem medir cada modelo; se a medição do M1.5b mostrar outra
  ordem, a tabela muda.

Origem: pendência "o modo A entrega menos do que a spec do M1.5 prometeu", decidida pelo
humano em 2026-09-25, depois do fecho do M1.5.
