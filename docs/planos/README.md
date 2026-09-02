# Planos

Um plano por spec aprovada. Nomeação igual à da spec de origem.

## Antes de escrever

Leia [PROCESSO.md §5](../PROCESSO.md#5-anatomia-de-um-plano), que traz o modelo de tarefa
completo.

## A regra que define o formato

> **O plano especifica contratos, não corpos.**

Código completo dentro do plano é desperdício: escreve-se duas vezes e a segunda versão
diverge no minuto em que a realidade aparece. Lista de tarefas soltas é pior: o agente novo
re-deriva decisões já tomadas, e cada um deriva diferente.

Cada tarefa declara: arquivos, contrato, critério de aceite, cerca de escopo, dependências e
se é visual.

## A regra dura

**Tarefa sem critério de aceite executável não entra no plano.** É o que torna a execução
contínua segura — com um teste como critério, o agente não consegue se enganar sobre ter
terminado.

## Planos

| Plano | Spec | Situação |
|---|---|---|
| [F2a — Migração do motor](F2a-migracao-do-motor.md) | [F2a](../specs/F2a-migracao-do-motor.md) | ✅ executado e fechado |
| [F2b — Casco da aplicação](F2b-casco-da-aplicacao.md) | [F2b](../specs/F2b-casco-da-aplicacao.md) | 🟡 revisado · **aguardando aprovação humana** |

**O plano do F2a é o modelo vivo.** É o primeiro exemplar completo e executado: 12 tarefas, mapa
de arquivos, grafo de dependências, e as quatro tarefas em que conteúdo literal entra.

Uma ressalva ao copiá-lo: ele foi executado **com ramo próprio**, antes da
[D-31](../decisoes/D-31-trabalho-direto-na-main.md). Plano novo não cria ramo.
