# Ruvor

Plataforma de análise de risco em ações. O usuário quer saber **quanto pode perder** se
aplicar em uma ação ou carteira, e a plataforma responde com transparência sobre o método.

**Diferencial:** múltiplos algoritmos comparados sobre a mesma base, com validação
estatística de qual deles merece confiança para aquele ativo.

---

## Comece por aqui

0. **Qual é a sua frente?** `git branch --show-current`: o prefixo antes da `/` é a frente, e
   **[`docs/frentes/<frente>.md`](docs/frentes/)** diz o bloco e o próximo passo. As frentes
   trabalham ao mesmo tempo, e cada uma tem pastas onde pode escrever
   ([`docs/FRENTES.md`](docs/FRENTES.md)). Na `main`, **não comece trabalho**: pergunte a frente.
1. **[`docs/ESTADO.md`](docs/ESTADO.md)** — onde paramos e o que está aberto. **Leia sempre.**
2. **[`docs/PROCESSO.md`](docs/PROCESSO.md)** — como se trabalha aqui. **Leia antes de produzir qualquer coisa.**
3. **[`docs/aprendizados.md`](docs/aprendizados.md)** — armadilhas já descobertas. Leia antes de implementar.

Antes de mandar spec ou plano para revisão, rode a
[lista de verificação](docs/PROCESSO.md#antes-de-mandar-revisar). A primeira spec do projeto
custou cinco rodadas de revisão pelos seis defeitos que ela cobre.

---

## Autoridade dos documentos

Nem tudo no repositório é referência. Esta tabela resolve dúvida.

### Manda

| Documento | Sobre |
|---|---|
| [`docs/PROCESSO.md`](docs/PROCESSO.md) | como spec, plano e código nascem e são revisados |
| [`docs/PRODUTO.md`](docs/PRODUTO.md) | o que a plataforma é, para quem, marcos |
| [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) | pilha, estrutura, banco, execução, auditoria |
| [`docs/decisoes/`](docs/decisoes/) | decisões tomadas, com o porquê — **append-only** |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | ordem dos blocos e status |
| [`docs/ESTADO.md`](docs/ESTADO.md) | posição atual, atualizada no fecho de cada bloco |
| [`docs/FRENTES.md`](docs/FRENTES.md) e [`docs/frentes/`](docs/frentes/) | quem faz o quê, a cerca de pastas de cada frente, os contratos entre elas e o andamento de cada uma |
| [`docs/specs/`](docs/specs/) e [`docs/planos/`](docs/planos/) | o trabalho corrente |
| [`brand/ruvor/`](brand/ruvor/) | tokens nos dois temas, a folha de componentes, os ícones, logo, regras e as quatro telas de referência (`mockups/`), de que os tokens derivam ([D-87](docs/decisoes/D-87-os-mockups-sao-a-referencia-visual-do-kit.md)) |

### NÃO é referência

| Caminho | O que é | Cuidado |
|---|---|---|
| [`docs/prototipo/`](docs/prototipo/) | documentação do protótipo **VaR Lab**, que está sendo substituído | linha de base de revisão, **não** modelo de spec nem de código |
| [`docs/tcc/`](docs/tcc/) | trabalho acadêmico | escopo de pesquisa, **não** especificação de produto |
| `brand/ruvor/estudos/` | histórico de como se chegou à marca | em divergência com o kit, **o kit vence** |
| `brand/ruvor/examples/` | estudos visuais anteriores | em divergência, **`brand/ruvor/mockups/` vence** |

Se um documento antigo contradiz um destes, **estes vencem**.

---

## Regras invioláveis

**Commits sem assinatura de ferramenta.** Nenhum commit leva `Co-Authored-By`, referência a
assistente de IA ou link de sessão. A autoria é do time. Sem exceção
([D-27](docs/decisoes/D-27-commits-sem-assinatura.md)).

**Não commitar nem enviar por iniciativa própria.** Exceto o commit por tarefa dentro do
ramo do bloco. **Nunca direto na `main`**: tudo entra por PR, com a CI verde, aprovada e
mesclada pelo dono da frente ([D-82](docs/decisoes/D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md),
[D-85](docs/decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md)).

**Não escrever fora da cerca da sua frente** ([FRENTES.md](docs/FRENTES.md#cercas)). Precisa?
Combina na spec, e a frente dona revisa.

**Nunca inventar.** Não existe função, parâmetro, caminho ou endpoint "provável". Verifica
antes de usar.

**Perguntar quando** a resposta muda o resultado e não dá para derivar da spec, das decisões
ou do código. **Não perguntar quando** é derivável, convenção, ou barato de reverter.

**O lugar de perguntar é a spec, não a implementação.**

**Contrato congelado durante a implementação.** Mudou, para e escala.

**Relatar fielmente.** Teste falhou, diz que falhou, com a saída. Etapa pulada, diz que
pulou. Não existe "deve funcionar".

**`engine/` não importa Django.** Nunca ([D-17](docs/decisoes/D-17-monorepo-engine-sem-django.md)).

**Toda tela de produto passa por mockup aprovado antes de virar código**
([PROCESSO.md §7](docs/PROCESSO.md#7-portão-de-mockup)). Casco técnico — tela que só prova
que a infraestrutura responde — está fora
([D-30](docs/decisoes/D-30-portao-de-mockup-so-para-tela-de-produto.md)).

---

## Como o trabalho anda

```
ROADMAP → SPEC → ✋ → PLANO → ✋ → IMPLEMENTAÇÃO (contínua) → REVISÃO → fecha
                                    └ tarefa visual → mockup → ✋ → implementa
```

**Portões humanos:** spec, plano e cada mockup. O resto roda sozinho.
**Princípio:** portão humano onde o erro é caro e a máquina não detecta; autonomia onde o
teste detecta.

Detalhe completo, incluindo a anatomia de spec e de plano, em
[`docs/PROCESSO.md`](docs/PROCESSO.md).

---

## Idioma

Documentação, specs, planos, decisões, comentários e mensagens de commit **em português**.
Código — nomes de variável, função, classe — em inglês.

---

## Estado do repositório

Existem o **motor**, o **casco da aplicação**, o **ambiente local em contêiner**, a
**fundação de dados** — os quatro esquemas do banco, as primeiras tabelas, o **catálogo de
ações** da B3 e dez anos de preço de seis ativos — os quatro do Marco 1 e dois pedidos sob demanda —, as primeiras **métricas de
comportamento** e o **risco** em `gold`: nove modelos de VaR, quatro backtests e o veredito
de adequação por ativo —, calculado **pela fila**, **agendado** pelo Celery Beat e, desde o
M1.5b, **sem refazer o treino**: os modelos caros reaproveitam retratos. Desde a fase 1 do M2.1a
há **identidade**: sessão, papel por organização, a regra das rotas de conta como serviço e a
auditoria de acesso; desde a fase 2, as rotas de conta e, desde a T14, o **autor do pedido** de
cálculo, gravado no pedido e na execução que ele abre. Desde o M1.6a existem a **API de leitura** em `/api/v1/`, o **cálculo sob
demanda** de um ativo nunca calculado e o **kit de marca completo**, nos dois temas. Desde o
M4.2 a API tem **chave pessoal de leitura**, **taxa em toda rota**, o **esquema OpenAPI** e o
**filtro automático por organização**, e desde o M4.1, **relatórios** de risco guardados para sempre,
com SHA-256. O M2.2a, a **carteira** — composição versionada e o risco dela nos nove modelos —, entrou na
`main` pela PR #34; o parecer da CVM não a segura enquanto não houver comercialização
([D-160](docs/decisoes/D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md)). Desde o
M1.6b existem as **telas**: a busca e a tela do ativo — o Marco 1 está fechado —, e desde o M1.6c a tela tem as
cinco camadas, com os fundamentos, a posição entre os pares e os comunicados da companhia à CVM. Desde o M1.7
a **busca ignora acento**, pela extensão `unaccent` do PostgreSQL, a sugestão da página inicial vem da API
(`has_risk`) e a classificação da B3 sai da API com vírgula. Desde o M2.3 há a
**camada explicativa**: as duas leituras, iniciante e avançada, escolhidas no casco. Desde o M3.3, o
**estresse histórico**: o ativo e o Ibovespa lado a lado nos quatro episódios da D-147, em `gold.stress_episode`, pelo
`/metrics` e no bloco "Em momentos de estresse" da tela. Desde o M1.4b, o **motor corrigido** (`0.4.0`): nenhum dos
nove modelos usa o retorno do próprio dia, e os três tradicionais reestimam a cada 252 pregões, numa janela que cresce.
Desde o M2.1b, as **telas de acesso**: entrar, criar conta, trocar a senha — inclusive a troca obrigatória da senha
provisória —, o menu de conta no casco e a gestão de usuários da organização; e o pedido de cálculo **exige conta**
([D-140](docs/decisoes/D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md)). Desde o M2.4, o **regime de
laboratório**: o experimento fixo da década de cada ativo coberto — os nove modelos nos dois níveis pelo mesmo
`run_models` da produção, recortados em anos de 252 pregões — em `gold.lab_run`, `gold.lab_result` e `gold.lab_year`,
disparado depois do fecho do risco e por `manage.py compute_lab`, pela rota `/lab` e numa seção da tela do ativo logo
depois do risco, sem eleger ([D-183](docs/decisoes/D-183-o-laboratorio-e-o-calculo-de-producao-recortado-na-decada-do-ativo-restringe-a-d-04.md)
a [D-187](docs/decisoes/D-187-a-secao-do-laboratorio-fica-na-tela-do-ativo-depois-do-risco-sem-eleger.md)).
Desde o M5.1, o **retorno**: a média histórica e o AR(1) validados fora da amostra contra o retorno zero, com o
Diebold-Mariano no veredito, e a previsão do próximo pregão de cada um, sempre junto do veredito e do histórico, em
`gold.return_run` e `gold.return_result`, pela rota `/returns` e numa seção da tela do ativo depois do laboratório, com o
aviso sempre aberto ([D-188](docs/decisoes/D-188-a-previsao-de-retorno-e-o-log-retorno-de-um-pregao-contra-o-retorno-zero.md) a [D-192](docs/decisoes/D-192-a-tela-mostra-a-validacao-e-a-previsao-junto-dela-com-o-aviso-estende-a-d-160.md)).

- `engine/` — motor numérico: pacote Python isolado (`ruvor-engine`) na versão **0.5.0**, 9
  modelos de VaR, 4 testes de backtesting, desde o M5.1 o pacote `engine.returns` — a média histórica e o AR(1) de
  retorno, a validação e o orquestrador, com registry próprio ([D-189](docs/decisoes/D-189-o-motor-ganha-o-pacote-engine-returns-em-lista-fechada-e-vai-a-0-5-0-restringe-a-d-21-a-d-76-e-a-d-157.md)) —, 229 testes — 25 deles a linha de base numérica, que só vale no Windows e se
  regenera por `engine/tests/baseline/capturar.py` ([D-159](docs/decisoes/D-159-a-linha-de-base-numerica-e-a-do-motor-0-4-0-restringe-a-d-44.md)),
  e um, o V-04, que só roda no `worker` e pula fora dele. Desde o M1.4b, o GARCH e o EGARCH **não olham à frente** — a σ
  do dia *t* sai dos retornos até *t* − 1 — e os três tradicionais estimam em **janela expansiva**, reestimada a cada
  252 pregões; `engine/tests/test_sem_olhar_a_frente.py` prova por perturbação, nos seis não neurais, que o VaR de um
  dia não usa o retorno dele nem os seguintes
  ([D-157](docs/decisoes/D-157-alteracao-no-motor-em-lista-fechada-para-a-correcao-do-m1-4b-restringe-a-d-76.md),
  [D-158](docs/decisoes/D-158-o-var-do-dia-nao-usa-o-retorno-do-dia-e-os-tradicionais-reestimam-a-cada-252-pregoes-restringe-a-d-97.md)). Roda por linha de comando: `ruvor run`. **Nunca
  importa Django**, e um teste prova isso. Os três modelos neurais fixam semente por
  `engine/src/engine/seeding.py`, no treino e em cada retreino
  ([D-63](docs/decisoes/D-63-semente-fixa-entra-no-manifesto.md),
  [D-75](docs/decisoes/D-75-as-redes-semeiam-em-cada-retreino-estende-a-d-63.md)); os quatro
  modelos caros expõem e aceitam **retratos** do estado treinado, no formato de
  `engine/src/engine/snapshots.py` ([D-76](docs/decisoes/D-76-alteracao-no-motor-em-lista-fechada-restringe-a-d-21.md));
  e o `py.typed` deixa o `mypy` do backend enxergar os tipos dele.
- `backend/` — projeto Django com oito apps, `apps/accounts`, `apps/assets`,
  `apps/analytics`, `apps/risk`, `apps/fundamentals`, `apps/api`, `apps/portfolios` e, desde o M5.1, `apps/returns`. `GET /health` e a API em
  `/api/v1/`, no formato da [D-86](docs/decisoes/D-86-convencoes-da-api-http.md): oito rotas de
  leitura — a busca no catálogo, sem diferença de caixa nem de acento no nome e no nome de pregão,
  pelo lookup `unaccent` ([D-143](docs/decisoes/D-143-a-busca-ignora-acento-pelo-unaccent.md)), com
  o campo e o filtro `has_risk` (a execução fechada mais recente `ok` ou `partial`), e, por ativo, identidade, preços, eventos, métricas, risco e, desde o M2.4, o laboratório (`/lab`, que lê os modelos e o
  módulo puro `apps/risk/decade.py`, nunca o motor) e, desde o M5.1, o retorno (`/returns`, que só lê `apps.returns.models`) — e o
  `POST /api/v1/assets/{ticker}/risk`, que pede o cálculo de um ativo nunca calculado, com um
  pedido aberto por ativo em `core.compute_request`, teto global e expiração
  ([D-89](docs/decisoes/D-89-a-web-enfileira-pelo-nome-da-tarefa.md),
  [D-90](docs/decisoes/D-90-calculo-sob-demanda-so-para-ativo-nunca-calculado.md)) — desde o M2.1b, **só com conta
  pronta**: `ReadOpenWriteAccountReady` (`apps/api/permissions.py`) deixa o `GET` aberto e passa a escrita ao
  `AccountReady`, e o anônimo recebe 401 ([D-140](docs/decisoes/D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md)); e as
  rotas de conta, `auth/*` e `organization/users*`, com sessão do Django e CSRF — quem não entrou
  recebe 401 `not_authenticated`, e toda view que exige conta declara `AccountReady`
  ([D-100](docs/decisoes/D-100-a-api-autentica-por-sessao-do-django-com-csrf.md),
  [D-102](docs/decisoes/D-102-papeis-admin-e-member-por-organizacao.md)); desde o M4.2, a
  **chave pessoal de leitura** (`api-keys*`, `Authorization: Bearer rvr_…`), que só lê as views
  com `api_key_scope = "read"`, por método seguro — **toda view declara `api_key_scope`** e
  `extend_schema` —, a **taxa em toda rota**, por chave, por usuário e, para anônimo, por IP
  (`RUVOR_THROTTLE_*`), e o esquema OpenAPI em `GET /api/v1/schema`, gerado pelo drf-spectacular
  sem aviso nem erro ([D-108](docs/decisoes/D-108-a-api-aceita-chave-pessoal-de-leitura.md) a
  [D-111](docs/decisoes/D-111-a-chave-guarda-so-o-hash-e-a-conta-mudada-revoga.md)); desde o M4.1,
  as rotas de relatório, `reports*`: a sessão gera em `POST /api/v1/reports` o relatório de risco de
  um ativo, e a sessão ou a chave lista, lê e baixa `/json` (os bytes guardados) e `/csv` (derivado)
  — a chave de leitura lê o relatório da organização, dado privado, e recebe 403 no `POST`
  ([D-113](docs/decisoes/D-113-o-relatorio-e-uma-foto-guardada-com-sha-256.md) a
  [D-115](docs/decisoes/D-115-a-chave-de-leitura-le-o-relatorio-da-organizacao-estende-a-d-108.md)); tabela
  privada nova usa o gerente de `apps/accounts/tenancy.py`, que filtra pela organização do
  contexto e levanta sem ela ([D-112](docs/decisoes/D-112-o-filtro-automatico-por-organizacao-nasce-no-m4-2.md)); desde o
  M2.2a, as rotas da **carteira**, `portfolios*`: criar, listar, ler, mudar, arquivar e trocar a
  composição — pesos em %, exatamente os enviados, versão nova a cada troca, `core.portfolio_version`
  e `core.portfolio_holding` só crescem, com gatilho — e pedir (`POST .../risk`, só sessão) e ler o
  risco da versão corrente, com a perda em reais calculada na leitura; a série única da carteira
  (`apps/portfolios/series.py`, só biblioteca padrão) vai aos nove modelos pelas três tarefas da
  carteira, sob a trava consultiva da execução (7104), com um cálculo por organização e teto global
  (`RUVOR_PORTFOLIO_*`) ([D-116](docs/decisoes/D-116-o-parecer-da-cvm-nao-bloqueia-a-spec-da-carteira-e-segura-a-implementacao.md) a
  [D-119](docs/decisoes/D-119-o-risco-da-carteira-e-sob-demanda-em-gold-na-app-da-frente.md)); a
  `apps/api` e o lado da web de `apps/portfolios` não importam o motor, e a `web` enfileira pelo nome da tarefa. Conecta no PostgreSQL e tem fila Celery sobre
  Redis: a tarefa de fumaça `config.tasks.ping`, por import explícito, e as dezenove tarefas de
  app, por descoberta automática — `apps/risk/tasks.py` (a abertura, que pula o ativo já em
  cálculo, uma por (ativo, modelo), o fecho — que, desde o M2.4, enfileira o laboratório devido por um `on_commit` —, o
  leque `recalcular_cobertos`, a varredura `fechar_presas`, que fecha pela regra a execução presa em `running`, em
  `apps/risk/stale.py`, e `calcular_laboratorio`, o experimento de um ativo, que nunca levanta),
  `apps/assets/tasks.py` (catálogo, preços, a `rotina_diaria`, que encadeia presas → preços →
  métricas → risco → retorno, e a cadeia sob demanda `calcular_sob_demanda`), `apps/returns/tasks.py` (`calcular_retornos`,
  o quinto elo da rotina, que nunca levanta — [D-191](docs/decisoes/D-191-o-retorno-mora-em-apps-returns-e-roda-no-quinto-elo-da-rotina-estende-a-d-91.md)), `apps/analytics/tasks.py` (as métricas
  da rotina) e `apps/fundamentals/tasks.py` (a coleta da
  CVM, o cálculo e a `rotina_fundamentos`, que encadeia os dois, e a `importar_comunicados`) e
  `apps/portfolios/tasks.py` (a abertura, uma por modelo e o fecho do risco da carteira). O
  `CELERY_BEAT_SCHEDULE` tem quatro entradas, com horário em `RUVOR_BEAT_ASSETS_CRON`,
  `RUVOR_BEAT_PRICES_CRON`, `RUVOR_BEAT_FUNDAMENTALS_CRON` e `RUVOR_BEAT_DISCLOSURES_CRON`
  ([D-67](docs/decisoes/D-67-uma-tarefa-por-ativo-e-modelo-restringe-o-rf-12-do-m1-4.md) a
  [D-72](docs/decisoes/D-72-o-fecho-escreve-metadado-de-execucao-restringe-a-d-16.md),
  [D-91](docs/decisoes/D-91-a-rotina-diaria-e-precos-metricas-risco-estende-a-d-69.md),
  [D-92](docs/decisoes/D-92-nunca-duas-execucoes-do-mesmo-ativo-ao-mesmo-tempo.md)).
  Configuração por variáveis `RUVOR_*`; mypy estrito, com as tarefas Celery tipadas por
  `celery-types` ([D-134](docs/decisoes/D-134-tarefas-celery-tipadas-por-celery-types.md)) e o
  DRF pelos `djangorestframework-stubs`; 1972 testes com pytest-django, que
  **rodam no contêiner `worker`** — é o único que tem o motor
  ([D-33](docs/decisoes/D-33-dia-a-dia-dentro-do-conteiner.md) segue valendo para o resto).
  `migrate` num banco vazio cria os quatro esquemas — `core`, `bronze`, `silver` e `gold` — e a
  extensão `unaccent` (`apps/assets/migrations/0004_unaccent.py`; o banco de produção precisa dela),
  as tabelas `core.organization`, `core.user`, `core.compute_request`, `core.api_key`, `core.report`,
  `core.portfolio`, `core.portfolio_version` e `core.portfolio_holding`, a organização fixa do Marco 1 (`slug`
  `ruvor`), as cinco tabelas da `bronze`, e `silver.asset`, `silver.price`,
  `silver.corporate_event`, `silver.company`, `silver.financial_statement` e
  `silver.disclosure`, e as quinze tabelas da `gold`, `gold.behavior_metric`,
  `gold.return_histogram_bin`, `gold.stress_episode`, `gold.risk_run`, `gold.risk_result`, `gold.model_snapshot`,
  `gold.fundamental_indicator`, `gold.peer_comparison`, `gold.portfolio_risk_run` e
  `gold.portfolio_risk_result` e, desde o M2.4, `gold.lab_run`, `gold.lab_result` e `gold.lab_year` — imutáveis no Django e
  no banco, pelo gatilho `lab_so_cresce`, da migration `risk.0004` — e, desde o M5.1, `gold.return_run` e
  `gold.return_result` (a migration `returns.0001`), mais `core.compute_request`,
  `core.access_event`, `core.api_key`, `core.report` e `public.django_session` — quarenta e três ao todo. O `AUTH_USER_MODEL`
  é próprio e autentica por e-mail, **sem diferença de caixa**
  ([D-39](docs/decisoes/D-39-usuario-proprio-autentica-por-email.md),
  [D-106](docs/decisoes/D-106-limite-de-tentativas-no-redis-e-email-sem-caixa.md)); o usuário tem
  papel `admin` ou `member` na organização, e a organização pode ser pessoal. `apps/accounts`
  tem a regra das rotas de conta como serviço (`services.py`), sem importar o DRF, e as views dela por cima, o bloqueio de
  entrada por (e-mail, IP) no cache do Django — Redis, banco 1, `RUVOR_CACHE_URL` —, a auditoria
  `core.access_event`, que só cresce, `core.report`, imutável no Django e no banco — o primeiro
  gatilho, `report_so_cresce`, recusa `UPDATE` e `DELETE` e deixa o `TRUNCATE` passar —, e
  `manage.py create_organization`; o `createsuperuser` põe
  o superusuário na `ruvor` ([D-100](docs/decisoes/D-100-a-api-autentica-por-sessao-do-django-com-csrf.md)
  a [D-107](docs/decisoes/D-107-m2-1a-em-duas-fases-restringe-a-d-82.md)). `manage.py
  import_assets` consulta a B3 e conforma o catálogo de ações em `silver.asset`
  ([D-47](docs/decisoes/D-47-fonte-do-catalogo-e-o-site-da-b3.md),
  [D-48](docs/decisoes/D-48-catalogo-em-silver-por-ticker-atualizado-por-coleta.md)) — a
  classificação fica em `silver` como a B3 a entrega, com ponto no lugar da vírgula, e a API a corrige na
  saída pela tabela fechada de `apps/assets/classification.py`; o relatório da coleta conta o texto com
  ponto fora dela ([D-144](docs/decisoes/D-144-a-classificacao-da-b3-se-corrige-na-saida-da-api-estende-a-d-47.md));
  `manage.py import_prices` consulta o Yahoo e conforma dez anos de preços com retorno
  logarítmico ([D-50](docs/decisoes/D-50-preco-vem-do-chart-v8-do-yahoo-por-http-direto.md) a
  [D-54](docs/decisoes/D-54-transacao-por-ativo-restringe-a-d-48.md)); `manage.py
  compute_metrics` lê `silver` e escreve em `gold`, por ativo e em transação, a linha imutável
  de métricas de comportamento mais os 42 baldes do histograma de retornos e, desde o M3.3, os
  quatro episódios de estresse da D-147 (`apps/analytics/stress.py`, só biblioteca padrão), no
  mesmo `atomic` ([D-146](docs/decisoes/D-146-o-estresse-historico-vira-bloco-so-do-ativo-e-so-com-preco.md) a
  [D-148](docs/decisoes/D-148-o-estresse-e-tabela-filha-da-metrica-e-sai-pelo-metrics.md);
  [D-55](docs/decisoes/D-55-metrica-de-comportamento-e-imutavel.md) a
  [D-60](docs/decisoes/D-60-metrica-descritiva-sem-manifesto-restringe-a-d-15.md)). **`gold`
  deixou de estar vazio no M1.3**; o cálculo da camada 2 usa só a biblioteca padrão.
  `manage.py compute_risk` roda os nove modelos de VaR sobre `silver.price` e grava em `gold`
  a execução com o manifesto e os resultados, cada um com o VaR, os quatro backtests e o
  veredito de adequação
  ([D-61](docs/decisoes/D-61-backend-alimenta-o-motor-por-dataprovider.md) a
  [D-66](docs/decisoes/D-66-registry-incompleto-e-erro-restringe-o-silencio-do-motor.md));
  com `--async`, enfileira uma abertura por ativo e devolve — a `risk_run` nasce no `worker`
  como `running`, cada modelo grava os seus dois resultados em transação própria, e o fecho
  escreve `status` (`ok`, `partial` ou `failed`) e `finished_at` — só sobre execução `running`; a presa há mais de
  `RUVOR_RISK_STALE_AFTER_MIN` é fechada pela mesma regra, pela rotina ou por `manage.py close_stale_runs`. Os quatro modelos caros
  (`lstm`, `gru`, `garchnet`, `caviar`) guardam um retrato por ponto de retreino em
  `gold.model_snapshot`, e o cálculo reaproveita os válidos, treina só o que falta e reconstitui
  a série inteira por previsão — igual ao do zero, que `--full` faz
  ([D-77](docs/decisoes/D-77-os-retratos-moram-em-gold-com-impressao-digital-estrita.md) a
  [D-81](docs/decisoes/D-81-imagem-do-worker-travada-pelo-lock-e-versoes-na-identidade.md)). `manage.py compute_lab
  [TICKER ...]`, síncrono, no `worker`, grava o experimento da década dos ativos devidos (`apps/risk/lab.py`, que confere
  a série de novo depois do cálculo e grava sob a trava do ativo, só se não houver `ok` da identidade), com uma linha por
  ativo — `gravado`, `já calculado`, `década incompleta`, `série curta`, `inativo` ou `FALHOU` —; sem `--full` nem
  `--force`, e nada no Beat ([D-185](docs/decisoes/D-185-o-experimento-mora-em-tres-tabelas-de-gold-imutaveis-e-um-ok-por-identidade.md),
  [D-186](docs/decisoes/D-186-o-experimento-roda-pela-fila-depois-do-fecho-do-risco-de-producao.md)). `manage.py
  compute_returns [TICKER ...]`, no `worker`, grava por ativo coberto, numa transação, a `return_run` e os dois
  `return_result` — o veredito decidido sobre o *p* do Diebold-Mariano quantizado a 10 casas, abaixo de 0,05 —, com a
  previsão do próximo pregão e a data, o primeiro dia de semana depois do último preço ([D-190](docs/decisoes/D-190-a-validacao-do-retorno-e-o-diebold-mariano-contra-o-zero-e-nenhum-modelo-e-eleito.md),
  [D-191](docs/decisoes/D-191-o-retorno-mora-em-apps-returns-e-roda-no-quinto-elo-da-rotina-estende-a-d-91.md)). `manage.py
  import_fundamentals` guarda na `bronze` os zips de ITR e DFP da CVM desde 2016 e conforma
  companhias e balanços trimestrais em `silver`, com `--reconform` para refazê-la sem rede;
  `manage.py compute_fundamentals` grava em `gold` os indicadores e a capitalização, uma linha
  imutável por ação ([D-120](docs/decisoes/D-120-fundamento-vem-dos-dados-abertos-da-cvm.md) a
  [D-129](docs/decisoes/D-129-lucro-so-na-mae-vale-a-mae.md)) e, depois deles, a comparação de
  cada ação com os pares do segmento da B3, ou do subsetor, em `gold.peer_comparison`
  ([D-132](docs/decisoes/D-132-pares-sao-o-segmento-da-b3-pela-tupla.md)); `manage.py
  import_disclosures` guarda na `bronze` os zips do IPE da CVM desde 2016 e conforma em `silver`
  os fatos relevantes, comunicados ao mercado e avisos aos acionistas das companhias do
  catálogo, só na versão corrente
  ([D-130](docs/decisoes/D-130-noticia-e-o-que-a-companhia-divulga-na-cvm.md),
  [D-131](docs/decisoes/D-131-documento-do-ipe-se-identifica-pelo-link.md)). O
  backend **não declara** `numpy` nem `pandas`: o `pandas` chega pelo motor, que só é
  instalado no `worker`.
- `frontend/` — React em TypeScript estrito, Vite, Vitest, `react-router` e o **uPlot** nos
  gráficos ([D-94](docs/decisoes/D-94-os-graficos-sao-do-uplot.md)). As rotas `/` (a busca) e
  `/ativos/{ticker}` (a tela do ativo, com o risco, o pedido de cálculo e o acompanhamento), dentro do
  casco (`components/Shell.tsx`); desde o M2.1b, `/conta/senha` (a troca voluntária) e `/organizacao/usuarios` (a
  gestão, que o menu só oferece à `admin` de organização não pessoal) também no casco, e `/entrar` e `/cadastro` fora
  dele, em tela cheia. Na raiz das rotas, o `SessionProvider` (`src/session/`) lê `auth/me` uma vez e dá a sessão a todas as telas;
  com a senha provisória por trocar, mostra a **troca obrigatória** no lugar de qualquer rota, sem mudar a URL (menos
  em `/entrar` e `/cadastro`); o `next` da entrada só aceita caminho interno (`safeNext`). O **menu de conta** fica por
  último na barra (`components/AccountMenu.tsx`), os avisos de sessão terminada e de página só para quem entrou em
  `components/SignInNotice.tsx`, e o anônimo vê, no lugar do botão de calcular, o convite a entrar. O cliente
  (`src/api/client.ts`) tem `apiPost`, `apiPatch` e `apiDelete` com corpo JSON, pede `auth/csrf` antes de toda escrita
  sem cookie e repete uma vez em `csrf_failed`; o proxy do Vite preserva o `Host` (`changeOrigin: false`), para a
  checagem de origem do CSRF valer em desenvolvimento. A caixa de busca **de página** — a `/` e a tela "ativo não
  encontrado" — pede a sugestão à API (`has_risk=true&limit=8`) uma vez por montagem, e a da barra não
  pede; consome `brand/ruvor/tokens.css` e `components.css` pelo apelido
  `@brand`, e o proxy do Vite leva `/health` e `/api` à `web`. **Todo texto visível mora em
  `src/content/`** (copiado dos mockups aprovados), e varreduras reprovam cor literal, texto literal
  em `.tsx` (pela árvore sintática, com `@babel/parser`) e vocabulário de recomendação. Desde o M2.3, **duas
  leituras**: o alternador Iniciante/Avançada no casco (`components/ReadingSwitch.tsx`), lembrado em `localStorage`
  (`ruvor-reading`) por `src/reading.ts`, com o padrão iniciante; a frase avançada de cada número da lista fechada em
  `src/content/avancado.ts` (`TEXTOS_AVANCADOS`, mesma chave e mesma assinatura da iniciante de `textos.ts`), e o que é
  método ou estatística recolhido na iniciante pelo `components/Collapsible.tsx`
  ([D-151](docs/decisoes/D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md),
  [D-152](docs/decisoes/D-152-o-nivel-de-leitura-e-escolha-do-visitante.md)) — número novo com frase nasce com as duas
  entradas. Desde o M2.4, a seção do laboratório (`components/LabSection.tsx`, os estados em `src/lab/state.ts` e a
  releitura limitada a 2 minutos em `src/lab/useLabPolling.ts`), logo depois do risco, com o `/lab` fora do `data-ready`.
  Desde o M5.1, a seção do retorno (`components/ReturnsSection.tsx`, os estados e a visibilidade da previsão em
  `src/returns/state.ts`), depois do laboratório, com o `/returns` fora do `data-ready` e a lista ampliada do vocabulário
  só nas `retorno.*` (`tests/vocabulario.test.ts`).
  1822 testes.
  `frontend/e2e/` são os roteiros da execução real — `capturas.mjs` e, desde o M2.1b, `acesso.mjs`, que confere as
  telas de acesso no navegador e as compara com os mockups aprovados —, com o Playwright na imagem oficial, fora da CI.
  Lint e formatação são do **Biome**, por `npm run lint`
  ([D-43](docs/decisoes/D-43-ruff-e-biome-e-onde-cada-verificacao-roda.md)) — do lado Python,
  os dois projetos usam `ruff`. O `package.json` exige **Node 24.15+**, travado por
  `engine-strict` — mas isso é da imagem `node:24-slim`, não da máquina: quem não sair do
  contêiner não precisa de Node instalado.
- `compose.yaml` na raiz — `docker compose up` sobe seis serviços: `postgres`, `redis`,
  `web`, `worker`, `beat` e `frontend`. O `worker` roda com `--concurrency=2` e
  `--max-tasks-per-child=5`, e a imagem dele instala o motor com o lock como restrição; o `beat` usa a
  imagem do `worker`, sem `build` próprio, e **agenda coleta real** — `docker compose stop
  beat` quando isso não for desejado. Backend e frontend rodam aí no dia a dia; o motor segue
  no `.venv/` nativo ([D-33](docs/decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)).

Um só `.venv/` na raiz para motor e backend. O protótipo Flask, o SQLite e o frontend antigo
foram removidos por inteiro.
