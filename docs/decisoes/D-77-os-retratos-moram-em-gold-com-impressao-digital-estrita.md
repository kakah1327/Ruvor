# D-77 — Os retratos moram em `gold`, imutáveis, com impressão digital estrita sobre os preços, e guardam o estado do otimizador

**Status:** aceita · 2026-09-27

## Contexto

Para não refazer dez anos de backtest todo dia
([D-18](D-18-separacao-treino-previsao.md)), o estado treinado de cada modelo caro em cada
ponto de retreino precisa ser guardado e reaproveitado. Três perguntas: onde mora, o que guarda,
e quando deixa de valer.

## Decisão

**Mora em `gold.model_snapshot`**, uma linha por (ativo, modelo, nível, ponto de retreino),
**imutável** como o resto de `gold` ([D-16](D-16-resultado-e-imutavel.md)): nunca é alterado
nem apagado; retrato que deixa de valer é ignorado. **A gravação é idempotente**
(`bulk_create(..., ignore_conflicts=True)`, em transação própria): duas execuções que treinam o
mesmo retrato não colidem, e a segunda não vira par de erro pela
[D-70](D-70-a-tarefa-nunca-levanta-e-o-fecho-le-o-banco.md). Retratos parciais — os pontos
treinados antes de um retreino tardio falhar — são gravados mesmo assim.

**O que guarda:** nas redes, os pesos, **o estado do otimizador** (Adam: contador de passos e
momentos) e a configuração escolhida pela busca; no `caviar`, o `beta`. O estado do otimizador
não é opcional: restaurar só os pesos diverge do retreino no mesmo processo em 6,1e-3 (sonda da
spec); restaurar pesos e otimizador, **nesta ordem** — `optimizer.build`, `set_weights`, as
variáveis do otimizador casadas **por posição** —, sai igual bit a bit.

**Quando vale:** um retrato só é reaproveitado se os **onze** componentes da identidade forem
iguais aos de agora — ativo, modelo, nível, posição, semente, versão do motor, versões das seis
bibliotecas que calculam ([D-81](D-81-imagem-do-worker-travada-pelo-lock-e-versoes-na-identidade.md)),
hiperparâmetros, janela de treino, primeiro pregão e a **impressão digital dos preços**. A
impressão digital é o SHA-256 de (data, `repr(float(adj_close))`) de cada pregão, do primeiro
até o último que aquele ponto viu (`train_window_days + position`). **É estrita**: qualquer
diferença nesse prefixo — inclusive na sexta casa, depois de uma reconformação por evento
corporativo ([D-53](D-53-evento-novo-rebusca-a-serie-inteira.md)) — invalida aquele ponto e
todos os seguintes.

## Consequências

- **Nada apaga retrato.** Cada invalidação cria uma linhagem nova (72 retratos por ativo) e a
  antiga fica. A política de retenção fica em aberto: apagar é `delete` em `gold`, o que a D-16
  proíbe, e precisaria de decisão própria, com o número na mão. O V-13 do M1.5b mediu ~3,1 MiB
  por linhagem de ativo (ver o ESTADO).
- A impressão digital estrita pode invalidar demais se toda reconformação mexer em preço
  antigo. A saída, se o número for ruim, **não** é afrouxá-la — é estudar a reconformação do
  M1.2, que é onde o preço antigo muda.
- O formato do `payload` é `npz` sem `pickle`. **Não é determinístico em bytes** (o `zip` grava
  a hora): dois retratos iguais se comparam desempacotando, nunca pelos bytes.

Origem: [spec M1.5b — Treino separado da previsão](../specs/M1.5b-treino-separado-da-previsao.md)
(RF-01 a RF-03).
