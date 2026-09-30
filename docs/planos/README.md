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
| [F2b — Casco da aplicação](F2b-casco-da-aplicacao.md) | [F2b](../specs/F2b-casco-da-aplicacao.md) | ✅ executado e fechado |
| [F3 — Ambiente local](F3-ambiente-local.md) | [F3](../specs/F3-ambiente-local.md) | ✅ executado e fechado |
| [F4 — Fundação de dados](F4-fundacao-de-dados.md) | [F4](../specs/F4-fundacao-de-dados.md) | ✅ executado e fechado |
| [F5 — Integração contínua](F5-integracao-continua.md) | [F5](../specs/F5-integracao-continua.md) | ✅ executado e fechado |
| [M1.1 — Catálogo de ativos](M1.1-catalogo-de-ativos.md) | [M1.1](../specs/M1.1-catalogo-de-ativos.md) | ✅ executado e fechado |
| [M1.2 — Ingestão de preços](M1.2-ingestao-de-precos.md) | [M1.2](../specs/M1.2-ingestao-de-precos.md) | ✅ executado e fechado |
| [M1.3 — Camadas 1 e 2](M1.3-camadas-1-e-2.md) | [M1.3](../specs/M1.3-camadas-1-e-2.md) | ✅ executado e fechado |
| [M1.4 — Motor de risco](M1.4-motor-de-risco.md) | [M1.4](../specs/M1.4-motor-de-risco.md) | ✅ executado e fechado |
| [M1.5 — Execução assíncrona](M1.5-execucao-assincrona.md) | [M1.5](../specs/M1.5-execucao-assincrona.md) | ✅ executado e fechado |
| [M1.5b — Treino separado da previsão](M1.5b-treino-separado-da-previsao.md) | [M1.5b](../specs/M1.5b-treino-separado-da-previsao.md) | ✅ executado e fechado |
| [M3.1 — Fundamentos](M3.1-fundamentos.md) | [M3.1](../specs/M3.1-fundamentos.md) | ✅ executado e fechado |
| [M3.2 — Contexto](M3.2-contexto.md) | [M3.2](../specs/M3.2-contexto.md) | ✅ executado e fechado |
| [M1.6a — Fundação da aplicação](M1.6a-fundacao-da-aplicacao.md) | [M1.6a](../specs/M1.6a-fundacao-da-aplicacao.md) | ✅ executado e fechado |
| [M1.6b — As telas](M1.6b-as-telas.md) | [M1.6b](../specs/M1.6b-as-telas.md) | ✅ executado e fechado |
| [M1.6c — Fundamentos e contexto na tela](M1.6c-fundamentos-e-contexto.md) | [M1.6c](../specs/M1.6c-fundamentos-e-contexto.md) | ✅ executado e fechado |
| [M2.1a — Identidade e acesso](M2.1a-identidade-e-acesso.md) | [M2.1a](../specs/M2.1a-identidade-e-acesso.md) | ✅ fase 1 executada; a fase 2 espera o M1.6a |
| [M4.2 — API pública](M4.2-api-publica.md) | [M4.2](../specs/M4.2-api-publica.md) | ✅ executado (T0 a T10) em 2026-09-28 |
| [M2.3 — Camada explicativa](M2.3-camada-explicativa.md) | [M2.3](../specs/M2.3-camada-explicativa.md) | 🟡 revisado; aguardando aprovação do dono da frente |

**O plano do F2a é o modelo vivo**, e o do F2b mostra como fica um plano de projeto novo, em que quase todo arquivo de configuração entra literal. O F2a é o primeiro exemplar completo e executado: 12 tarefas, mapa
de arquivos, grafo de dependências, e as quatro tarefas em que conteúdo literal entra.

Ele foi executado **com ramo próprio**, antes da
[D-31](../decisoes/D-31-trabalho-direto-na-main.md) — e desde a
[D-82](../decisoes/D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md) é assim de novo: todo
bloco tem ramo, `<frente>/<bloco>-<assunto>`.
