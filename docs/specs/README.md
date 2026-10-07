# Specs

Uma spec por bloco do [ROADMAP](../ROADMAP.md). Descreve **o que deve existir e por quê** —
nunca como implementar.

Nomeação: `<bloco>-<nome-curto>.md` — por exemplo `F2a-migracao-do-motor.md`.

## Antes de escrever

Leia [PROCESSO.md §4](../PROCESSO.md#4-anatomia-de-uma-spec), que traz o modelo completo e o
critério de revisão.

## O teste que a spec precisa passar

**Executável por alguém que nunca participou da conversa.** Se depende de ter estado na
sala, não está pronta. É por isso que a revisão adversarial é feita por um agente **sem** o
histórico da conversa.

## Ciclo

```
escrita → auto-revisão → revisão adversarial → ✋ aprovação humana → plano
```

Spec pequena e local pode ser revisada inline, sem agente. Spec de bloco, que cria contrato
novo ou atravessa mais de um bloco, vai para revisão por agente.

## Specs

| Spec | Bloco | Situação |
|---|---|---|
| [F2a — Migração do motor](F2a-migracao-do-motor.md) | Fundação · F2a | ✅ implementada e fechada |
| [F2b — Casco da aplicação](F2b-casco-da-aplicacao.md) | Fundação · F2b | ✅ implementada e fechada |
| [F3 — Ambiente local](F3-ambiente-local.md) | Fundação · F3 | ✅ implementada e fechada |
| [F4 — Fundação de dados](F4-fundacao-de-dados.md) | Fundação · F4 | ✅ implementada e fechada |
| [F5 — Integração contínua](F5-integracao-continua.md) | Fundação · F5 | ✅ implementada e fechada |
| [M1.1 — Catálogo de ativos](M1.1-catalogo-de-ativos.md) | Marco 1 · M1.1 | ✅ implementada e fechada |
| [M1.2 — Ingestão de preços](M1.2-ingestao-de-precos.md) | Marco 1 · M1.2 | ✅ implementada e fechada |
| [M1.3 — Camadas 1 e 2](M1.3-camadas-1-e-2.md) | Marco 1 · M1.3 | ✅ implementada e fechada |
| [M1.4 — Motor de risco](M1.4-motor-de-risco.md) | Marco 1 · M1.4 | ✅ implementada e fechada |
| [M1.5 — Execução assíncrona](M1.5-execucao-assincrona.md) | Marco 1 · M1.5 | ✅ implementada e fechada |
| [M1.5b — Treino separado da previsão](M1.5b-treino-separado-da-previsao.md) | Marco 1 · M1.5b | ✅ implementada e fechada |
| [M3.1 — Fundamentos](M3.1-fundamentos.md) | Marco 3 · M3.1 · frente `fundamentos` | ✅ implementada e fechada |
| [M1.6a — Fundação da aplicação](M1.6a-fundacao-da-aplicacao.md) | Marco 1 · M1.6a | ✅ implementada e fechada |
| [M1.6b — As telas](M1.6b-as-telas.md) | Marco 1 · M1.6b | ✅ implementada e fechada |
| [M1.6c — Fundamentos e contexto na tela](M1.6c-fundamentos-e-contexto.md) | Marco 1 · M1.6c | ✅ implementada e fechada |
| [M3.2 — Contexto](M3.2-contexto.md) | Marco 3 · M3.2 · frente `fundamentos` | ✅ implementada e fechada |
| [M2.1a — Identidade e acesso](M2.1a-identidade-e-acesso.md) | Marco 2 · M2.1a · frente `identidade` | ✅ implementada — as duas fases; bloco fechado em 2026-09-30 |
| [M4.1 — Relatórios](M4.1-relatorios.md) | Marco 4 · M4.1 · frente `identidade` | ✅ aprovada (2026-09-29); implementada em 2026-09-30 |
| [M2.1m — A coluna do autor do pedido](M2.1m-requested-by.md) | Marco 2 · M2.1m · frente `marco1` | ✅ implementada e fechada |
| [M4.2 — API pública](M4.2-api-publica.md) | Marco 4 · M4.2 · frente `identidade` | ✅ aprovada; implementada em 2026-09-28 |
| [M2.1b — Telas de acesso](M2.1b-telas-de-acesso.md) | Marco 2 · M2.1b · frente `marco1` | ✅ implementada e fechada |
| [M1.5c — Execução presa](M1.5c-execucao-presa.md) | Marco 1 · M1.5c | ✅ implementada e fechada |
| [M2.3 — Camada explicativa](M2.3-camada-explicativa.md) | Marco 2 · M2.3 · frente `marco1` | ✅ implementada e fechada |
| [M3.3 — Estresse histórico](M3.3-estresse-historico.md) | Marco 3 · M3.3 · frente `marco1` | ✅ implementada e fechada |
| [M1.6d — Acabamento](M1.6d-acabamento.md) | Marco 1 · M1.6d | ✅ implementada e fechada |
| [M1.7 — Busca e catálogo](M1.7-busca-e-catalogo.md) | Marco 1 · M1.7 | ✅ implementada e fechada |
| [M2.2a — Carteira](M2.2a-carteira.md) | Marco 2 · M2.2a · frente `identidade` | ✅ aprovada (2026-10-01); implementada no ramo (2026-10-02); a PR de implementação só entra com o parecer da CVM (D-116) |
| [M1.4b — Correção do motor](M1.4b-correcao-do-motor.md) | Marco 1 · M1.4b · frente `marco1` | ✅ implementada e fechada (2026-10-03) |
| [M2.4 — Regime de laboratório](M2.4-regime-de-laboratorio.md) | Marco 2 · M2.4 · frente `marco1` | ✅ implementada e fechada (2026-10-04) |
| [M5.1 — Retorno](M5.1-retorno.md) | Marco 5 · M5.1 · frente `marco1` | ✅ implementada e fechada (2026-10-04) |
| [M2.2b — Telas da carteira](M2.2b-telas-da-carteira.md) | Marco 2 · M2.2b · frente `marco1` | ✅ implementada e fechada (2026-10-07) |
