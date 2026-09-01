# Roadmap

Até onde vamos e em que ordem. Onde estamos agora está em [ESTADO.md](ESTADO.md).

Cada bloco recebe spec própria → plano próprio → implementação, conforme
[PROCESSO.md](PROCESSO.md). Um marco fecha quando todos os seus blocos fecham.

**Legenda:** ⬜ não começou · 🟡 em andamento · ✅ fechado

---

## Fundação

Não entrega nada ao usuário final. É o alicerce, e é o que faltou antes.

| | Bloco | Entrega |
|---|---|---|
| ✅ | **F1 — Documentação de base** | PROCESSO, PRODUTO, ARQUITETURA, decisões, ROADMAP, ESTADO, CLAUDE.md |
| ✅ | **F6 — Agentes do projeto** (antecipado) | definições em `.claude/agents/`, com restrição por ferramenta |
| ✅ | **F2a — Migração do motor** | `engine/` isolado, rebrand, empacotamento próprio, linha de base numérica |
| ⬜ | **F2b — Casco da aplicação** | projeto Django e projeto React funcionais, com identidade Ruvor |
| ⬜ | **F3 — Ambiente local** | `docker compose up` sobe Postgres, Redis, web e worker; cria `infra/` |
| ⬜ | **F4 — Fundação de dados** | primeiras migrations, esquemas bronze/prata/ouro, entidade Organização |
| ⬜ | **F5 — CI** | estilo, tipos e testes a cada mudança |

---

## Marco 1 — a ação, e o risco dela

Digita ITUB4, recebe tudo sobre o comportamento da ação **e** a comparação de risco que
ninguém mais faz. Sem login, sem carteira.

Coincide em grande parte com o conteúdo do TCC — os dois avançam juntos.

| | Bloco | Entrega |
|---|---|---|
| ⬜ | **M1.1 — Catálogo de ativos** | lista de papéis da B3 com nome, setor e situação; base da busca |
| ⬜ | **M1.2 — Ingestão de preços** | histórico + atualização diária, camada bronze com data de coleta |
| ⬜ | **M1.3 — Camadas 1 e 2** | identidade, preço, gráfico, volume, dividendos, retornos, volatilidade, quedas, relação com o Ibovespa |
| ⬜ | **M1.4 — Motor de risco** | semente fixa, manifesto de execução, integração com a fila (a migração é do F2a) |
| ⬜ | **M1.5 — Execução assíncrona** | fila, modo A, pré-cálculo dos ativos cobertos |
| ⬜ | **M1.6 — Aplicação web** | shell, busca, tela do ativo, identidade Ruvor |

**Candidatos a entrar neste marco** (ver [PRODUTO.md](PRODUTO.md#5-requisitos-candidatos)):
discordância entre modelos, "em qual modelo confiar", estresse histórico. Ainda não
decidido.

---

## Marco 2 — vira plataforma

| | Bloco | Entrega |
|---|---|---|
| ⬜ | **M2.1 — Identidade e acesso** | autenticação, papéis, permissões, telas de login |
| ⬜ | **M2.2 — Carteira** | composição pelo usuário e risco de carteira |
| ⬜ | **M2.3 — Camada explicativa** | leitura iniciante/avançado como sistema |

**Pré-requisito:** parecer sobre a fronteira regulatória da CVM.

---

## Marco 3 — "tudo sobre a ação" completo

| | Bloco | Entrega |
|---|---|---|
| ⬜ | **M3.1 — Fundamentos** | camada 4, com fonte adequada para B3 (Yahoo não serve) |
| ⬜ | **M3.2 — Contexto** | camada 5: notícias e comparação setorial |

---

## Marco 4 — produto institucional

| | Bloco | Entrega |
|---|---|---|
| ⬜ | **M4.1 — Relatórios** | exportáveis e auditáveis |
| ⬜ | **M4.2 — API pública** | chaves, escopos, quotas, documentação |

---

## Marco 5

| | Bloco | Entrega |
|---|---|---|
| ⬜ | **M5.1 — Retorno** | estimativa de retorno/lucro |

---

## Trilha paralela — TCC

Independente da plataforma. É tempo de máquina, não desenvolvimento.

| | Tarefa | Observação |
|---|---|---|
| ⬜ | Fixar semente das redes neurais | pré-requisito de tudo abaixo |
| ⬜ | Refazer a Tabela 1 (modelos de ML) | os números atuais vieram de execução sem semente |
| ⬜ | Executar a Etapa 6 | 9 modelos × 4 ativos × 2 níveis; ~1h em CPU paralelizada |
| ⬜ | Escrever §4.5 e o Capítulo 5 | dependem da Etapa 6 |
| ⬜ | Renomear VaR Lab → Ruvor no texto | |
| ⬜ | Corrigir divergências do §3.2 | Flask/Jinja2, QuantReg, ausência de banco |

Detalhe das divergências em
[`docs/prototipo/07-backlog-specs.md`](prototipo/07-backlog-specs.md).

---

## Fora de escopo, registrado

Levantado e deliberadamente adiado ou descartado:

- Execução de ordens e intermediação de investimento — nunca
- Importação de carteira de corretora — [D-03](decisoes/D-03-carteira-montada-pelo-usuario.md)
- Dados tick a tick — [D-04](decisoes/D-04-dois-regimes-de-operacao.md)
- Modelagem multivariada de correlação (caminho caro da carteira) — a decidir
- Expected Shortfall — candidato, sem marco definido
