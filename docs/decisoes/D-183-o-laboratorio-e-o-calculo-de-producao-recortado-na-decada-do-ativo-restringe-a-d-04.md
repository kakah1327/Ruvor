# D-183 — O laboratório é o cálculo de produção recortado na década do ativo, calculado uma vez e guardado; restringe a D-04 e responde a D-74

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do
[M2.4](../specs/M2.4-regime-de-laboratorio.md) aprovada pelo dono

## Contexto

A [D-04](D-04-dois-regimes-de-operacao.md) previa "dois caminhos de código diferentes sobre o mesmo
motor", e a ARQUITETURA descrevia o laboratório como um protocolo próprio (busca de hiperparâmetros,
retreino anual, 20–60 min). A [D-74](D-74-o-marco-1-e-so-producao.md) deixou o laboratório para o
Marco 2. Desde o M1.5b ([D-80](D-80-o-retreino-de-producao-e-a-cada-252-pregoes-restringe-a-d-18.md)) e
o M1.4b ([D-158](D-158-o-var-do-dia-nao-usa-o-retorno-do-dia-e-os-tradicionais-reestimam-a-cada-252-pregoes-restringe-a-d-97.md)),
a produção **é** esse protocolo: os nove modelos reestimam a cada 252 pregões numa janela que cresce, as
redes fazem a busca 2 × 2 na posição 0, e nenhum modelo usa o retorno do dia. Um protocolo à parte daria
à plataforma dois VaR diferentes para o mesmo dia do mesmo ativo.

## Decisão

O laboratório usa os parâmetros de produção, pelo mesmo `run_models`, sobre a década do ativo
([D-184](D-184-a-decada-e-a-do-ativo-e-o-teste-se-le-em-anos-de-252-pregoes.md)). O que o separa da
produção é **o recorte fixo, o corte por ano de teste e a guarda** — um caminho próprio no backend
(`apps/risk/decade.py`, `apps/risk/lab.py`, as tabelas, a tarefa, a rota), não um protocolo próprio.
Parâmetros escolhidos pela pessoa ficam fora; quem roda é a fila e o operador; o resultado mora em `gold`
([D-185](D-185-o-experimento-mora-em-tres-tabelas-de-gold-imutaveis-e-um-ok-por-identidade.md)).

## Consequências

- A série de VaR da década é **igual, ponto a ponto**, ao começo da série de produção: medido nos 18
  pares do ITUB4 na spec e de novo na fase A da execução real (`n = 2238`, diferença máxima 0,0), com o
  motor `0.4.0`.
- O experimento reaproveita os retratos da produção e custa segundos (~4 s por ativo na fase A, 72
  retratos reaproveitados e nenhum treinado).
- A ARQUITETURA, §"Laboratório e produção", é corrigida no fecho do M2.4.
- A D-04 continua valendo para o que protege: o laboratório justifica, a produção entrega.
