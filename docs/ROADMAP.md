# Roadmap

Até onde vamos e em que ordem. Onde estamos agora está em [ESTADO.md](ESTADO.md).

Cada bloco recebe spec própria → plano próprio → implementação, conforme
[PROCESSO.md](PROCESSO.md). Um marco fecha quando todos os seus blocos fecham.

**Legenda:** ⬜ não começou · 🟡 em andamento · ✅ fechado

**Frentes trabalham ao mesmo tempo** desde 2026-09-26
([D-84](decisoes/D-84-frentes-com-cerca-de-pastas.md)): `marco1` fica com o M1.5b e o
M1.6, `fundamentos` com o M3.1 e o M3.2; `identidade`, com o M2.1, o M4.2 e o M4.1, é do Kauã desde 2026-09-27 — sem telas: toda interface visual é da `marco1`. A ordem dos marcos é a da entrega ao
usuário; o que impede um bloco de começar é dependência. Quem faz o quê está em
[FRENTES.md](FRENTES.md).

---

## Fundação

Não entrega nada ao usuário final. É o alicerce, e é o que faltou antes.

**✅ Fechada em 2026-09-08.** Sete blocos, do F1 ao F5. O último provou o repositório
numa máquina que não é a do desenvolvedor — e foi lá que se descobriu que a linha de
base numérica do motor não é portátil entre plataformas.

| | Bloco | Entrega |
|---|---|---|
| ✅ | **F1 — Documentação de base** | PROCESSO, PRODUTO, ARQUITETURA, decisões, ROADMAP, ESTADO, CLAUDE.md |
| ✅ | **F6 — Agentes do projeto** (antecipado) | definições em `.claude/agents/`, com restrição por ferramenta |
| ✅ | **F2a — Migração do motor** | `engine/` isolado, rebrand, empacotamento próprio, linha de base numérica |
| ✅ | **F2b — Casco da aplicação** | projeto Django e projeto React funcionais, com identidade Ruvor |
| ✅ | **F3 — Ambiente local** | `docker compose up` sobe Postgres, Redis, web, worker e frontend; duas imagens do backend (web leve, worker com ML); cria `infra/` |
| ✅ | **F4 — Fundação de dados** | primeiras migrations, os quatro esquemas, Organização e usuário próprio |
| ✅ | **F5 — Integração contínua** | estilo, tipos e testes a cada push; quatro trabalhos em máquina limpa |

---

## Marco 1 — a ação, e o risco dela

Digita ITUB4, recebe tudo sobre o comportamento da ação **e** a comparação de risco que
ninguém mais faz. Sem login, sem carteira.

Coincide em grande parte com o conteúdo do TCC — os dois avançam juntos.

| | Bloco | Entrega |
|---|---|---|
| ✅ | **M1.1 — Catálogo de ativos** | lista de papéis da B3 com nome, setor e situação; base da busca — fechado em 2026-09-21, 473 ações + Ibovespa |
| ✅ | **M1.2 — Ingestão de preços** | histórico + atualização incremental, `bronze` com data de coleta, `silver.price` e eventos — fechado em 2026-09-22, quatro ativos de dez anos |
| ✅ | **M1.3 — Camadas 1 e 2** | identidade, preço, gráfico, volume, dividendos, retornos, volatilidade, quedas, **distribuição de retornos** e relação com o Ibovespa — fechado em 2026-09-24, `gold` povoado pelos quatro ativos. **O tamanho não entrou aqui:** a capitalização de mercado não tinha fonte no repositório, e o M3.1 a entregou em `gold.fundamental_indicator` — soma das classes, nula quando falta preço de alguma classe, e sempre nula para PNA e PNB, que a CVM não separa ([D-124](decisoes/D-124-capitalizacao-soma-as-classes-e-a-escala-das-acoes-e-inferida.md)) |
| ✅ | **M1.4 — Motor de risco** | semente fixa nos três modelos neurais, manifesto de execução e o veredito de adequação por (modelo, nível) — `manage.py compute_risk` no contêiner `worker`, `gold.risk_run` e `gold.risk_result` (a migração é do F2a). Fechado em 2026-09-24, quatro ativos × 18 resultados. **A fila não é deste bloco:** a linha original dizia "integração com a fila", o M1.5 dizia a mesma coisa, e a spec do M1.4 resolveu a divergência **a favor do M1.5** — aqui o comando é síncrono |
| ✅ | **M1.5 — Execução assíncrona** | fila, modo A com transação por (ativo, modelo), estado da execução, Beat e o agendamento das ingestões (`import_assets`, `import_prices`) — `compute_risk --async`, sete tarefas em `apps/*/tasks.py` e o serviço `beat`. Fechado em 2026-09-25: a execução real reproduziu os 72 resultados do M1.4 campo a campo, e um tique real do Beat rodou coleta e recálculo sozinho. **Não derruba os 2 min por ativo** — quem faz isso é o M1.5b |
| ✅ | **M1.5b — Treino separado da previsão** | a [D-18](decisoes/D-18-separacao-treino-previsao.md), restringida pela [D-80](decisoes/D-80-o-retreino-de-producao-e-a-cada-252-pregoes-restringe-a-d-18.md): os quatro modelos caros guardam um **retrato** por ponto de retreino em `gold.model_snapshot`, e o recálculo reaproveita os válidos, treina só o que falta e reconstitui a série inteira do backtest por previsão — igual, campo a campo, ao cálculo do zero (`compute_risk --full`). Motor `0.3.0`, imagem do `worker` travada pelo lock, `--max-tasks-per-child=5`. Fechado em 2026-09-27: o cálculo completo custou 141 a 175 s por ativo, e o recálculo sem treino, **4,5 a 10,3 s** — 3,2% a 6,3% do completo. Nasceu ao dividir o M1.5, que ficara com quatro frentes |
| ✅ | **M1.6a — Fundação da aplicação** | o kit completo (tokens dos mockups, escala tipográfica, estados, tema escuro, componentes e a vitrine), as convenções da API aplicadas ([D-86](decisoes/D-86-convencoes-da-api-http.md)), a API de leitura e o **cálculo sob demanda** para ativo não coberto (a cauda longa da [D-19](decisoes/D-19-cobertura-de-ativos-em-camadas.md)), e as métricas na rotina diária. O M1.6 foi dividido em dois em 2026-09-27. Fechado em 2026-09-28: o kit nos dois temas com a folha de componentes e os ícones do Phosphor, a vitrine aprovada no portão de mockup; seis rotas em `/api/v1/` e o `POST` do pedido em `core.compute_request`; um ativo sem preço (`BBDC4`) pedido e calculado em **99,6 s** — coleta, métricas e risco |
| ⬜ | **M1.6b — As telas** | casco, busca e tela do ativo, cada uma com mockup aprovado antes do código, sobre o kit e a API do M1.6a |

**Candidatos a entrar neste marco** (ver [PRODUTO.md](PRODUTO.md#5-requisitos-candidatos)):
discordância entre modelos, "em qual modelo confiar", estresse histórico. Ainda não
decidido.

**O regime de laboratório não é deste marco**
([D-74](decisoes/D-74-o-marco-1-e-so-producao.md), 2026-09-25). A camada 3 do Marco 1 é só
produção; o laboratório vai para o Marco 2, como M2.4.

---

## Marco 2 — vira plataforma

| | Bloco | Entrega |
|---|---|---|
| 🟡 | **M2.1a — Identidade e acesso** | **fase 1 implementada em 2026-09-27**; o backend: sessão, cadastro, entrada, papéis `admin`/`member` por organização, gestão de usuários pela administradora, auditoria de acesso e `requested_by` — frente `identidade`, em duas fases ([D-107](decisoes/D-107-m2-1a-em-duas-fases-restringe-a-d-82.md)): a 1 sem nada do M1.6a, a 2 com as rotas, depois do M1.6a. As telas que consomem as rotas são da `marco1` |
| ⬜ | **Telas de acesso** | login, cadastro, troca de senha e gestão de usuários, cada uma com mockup aprovado, sobre o casco e o kit do M1.6b e as rotas do M2.1a — **frente `marco1`** (toda interface visual é dela, decisão do darkside171, 2026-09-27); o bloco é dela nomear |
| ⬜ | **M2.2 — Carteira** | composição pelo usuário e risco de carteira |
| ⬜ | **M2.3 — Camada explicativa** | leitura iniciante/avançado como sistema |
| ⬜ | **M2.4 — Regime de laboratório** | a camada 3 validada ao longo de uma década, na plataforma ([D-04](decisoes/D-04-dois-regimes-de-operacao.md)); veio do Marco 1 pela [D-74](decisoes/D-74-o-marco-1-e-so-producao.md) |

**Pré-requisito:** parecer sobre a fronteira regulatória da CVM.

---

## Marco 3 — "tudo sobre a ação" completo

| | Bloco | Entrega |
|---|---|---|
| ✅ | **M3.1 — Fundamentos** | camada 4, com fonte adequada para B3 (Yahoo não serve) — dados abertos da CVM (ITR e DFP, 2016 em diante) em `bronze`, companhias e balanços trimestrais em `silver`, indicadores e capitalização em `gold`; `import_fundamentals`, `compute_fundamentals` e a coleta semanal encadeada no Beat. Fechado em 2026-09-27, frente `fundamentos`: 339 companhias, 471 ações calculadas, e lucro, PL e dívida de PETR4, VALE3 e ITUB4 iguais à divulgação das companhias. **EBITDA fica de fora** |
| ✅ | **M3.2 — Contexto** | camada 5: notícias e comparação setorial — os comunicados da companhia à CVM (IPE: fato relevante, comunicado ao mercado e aviso aos acionistas) em `silver.disclosure`, só na versão corrente, coletados de segunda a sexta pela quarta entrada do Beat; e a comparação com os pares do segmento da B3, ou do subsetor, em `gold.peer_comparison`, gravada pelo `compute_fundamentals` depois dos indicadores. Fechado em 2026-09-27, frente `fundamentos`: 80.900 comunicados de 339 companhias, 471 ações comparadas, 17 sem grupo. **Imprensa e o texto do documento ficam de fora** ([D-130](decisoes/D-130-noticia-e-o-que-a-companhia-divulga-na-cvm.md)) |

---

## Marco 4 — produto institucional

| | Bloco | Entrega |
|---|---|---|
| ⬜ | **M4.1 — Relatórios** | exportáveis e auditáveis — frente `identidade`, depois do M4.2 |
| ⬜ | **M4.2 — API pública** | chaves, escopos, quotas, documentação — frente `identidade`, depois do M2.1 |

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
| ✅ | Fixar semente das redes neurais | **feito no M1.4** — `engine/src/engine/seeding.py`, aplicada no início de cada treino ([D-63](decisoes/D-63-semente-fixa-entra-no-manifesto.md)). Era pré-requisito de tudo abaixo |
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
