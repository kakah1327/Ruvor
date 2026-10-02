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
com SHA-256. Desde o
M1.6b existem as **telas**: a busca e a tela do ativo — o Marco 1 está fechado —, e desde o M1.6c a tela tem as
cinco camadas, com os fundamentos, a posição entre os pares e os comunicados da companhia à CVM. Desde o M2.3 há a
**camada explicativa**: as duas leituras, iniciante e avançada, escolhidas no casco.

- `engine/` — motor numérico: pacote Python isolado (`ruvor-engine`) na versão **0.3.0**, 9
  modelos de VaR, 4 testes de backtesting, 145 testes — um deles, o V-04, só roda no `worker` e
  pula fora dele — e linha de base numérica. Roda por linha de comando: `ruvor run`. **Nunca
  importa Django**, e um teste prova isso. Os três modelos neurais fixam semente por
  `engine/src/engine/seeding.py`, no treino e em cada retreino
  ([D-63](docs/decisoes/D-63-semente-fixa-entra-no-manifesto.md),
  [D-75](docs/decisoes/D-75-as-redes-semeiam-em-cada-retreino-estende-a-d-63.md)); os quatro
  modelos caros expõem e aceitam **retratos** do estado treinado, no formato de
  `engine/src/engine/snapshots.py` ([D-76](docs/decisoes/D-76-alteracao-no-motor-em-lista-fechada-restringe-a-d-21.md));
  e o `py.typed` deixa o `mypy` do backend enxergar os tipos dele.
- `backend/` — projeto Django com seis apps, `apps/accounts`, `apps/assets`,
  `apps/analytics`, `apps/risk`, `apps/fundamentals` e `apps/api`. `GET /health` e a API em
  `/api/v1/`, no formato da [D-86](docs/decisoes/D-86-convencoes-da-api-http.md): seis rotas de
  leitura — a busca no catálogo e, por ativo, identidade, preços, eventos, métricas e risco — e o
  `POST /api/v1/assets/{ticker}/risk`, que pede o cálculo de um ativo nunca calculado, com um
  pedido aberto por ativo em `core.compute_request`, teto global e expiração
  ([D-89](docs/decisoes/D-89-a-web-enfileira-pelo-nome-da-tarefa.md),
  [D-90](docs/decisoes/D-90-calculo-sob-demanda-so-para-ativo-nunca-calculado.md)); e as
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
  contexto e levanta sem ela ([D-112](docs/decisoes/D-112-o-filtro-automatico-por-organizacao-nasce-no-m4-2.md)); a
  `apps/api` não importa o motor, e a `web` enfileira pelo nome da tarefa. Conecta no PostgreSQL e tem fila Celery sobre
  Redis: a tarefa de fumaça `config.tasks.ping`, por import explícito, e as catorze tarefas de
  app, por descoberta automática — `apps/risk/tasks.py` (a abertura, que pula o ativo já em
  cálculo, uma por (ativo, modelo), o fecho, o leque `recalcular_cobertos` e a varredura
  `fechar_presas`, que fecha pela regra a execução presa em `running`, em `apps/risk/stale.py`),
  `apps/assets/tasks.py` (catálogo, preços, a `rotina_diaria`, que encadeia presas → preços →
  métricas → risco, e a cadeia sob demanda `calcular_sob_demanda`), `apps/analytics/tasks.py` (as métricas
  da rotina) e `apps/fundamentals/tasks.py` (a coleta da
  CVM, o cálculo e a `rotina_fundamentos`, que encadeia os dois, e a `importar_comunicados`). O
  `CELERY_BEAT_SCHEDULE` tem quatro entradas, com horário em `RUVOR_BEAT_ASSETS_CRON`,
  `RUVOR_BEAT_PRICES_CRON`, `RUVOR_BEAT_FUNDAMENTALS_CRON` e `RUVOR_BEAT_DISCLOSURES_CRON`
  ([D-67](docs/decisoes/D-67-uma-tarefa-por-ativo-e-modelo-restringe-o-rf-12-do-m1-4.md) a
  [D-72](docs/decisoes/D-72-o-fecho-escreve-metadado-de-execucao-restringe-a-d-16.md),
  [D-91](docs/decisoes/D-91-a-rotina-diaria-e-precos-metricas-risco-estende-a-d-69.md),
  [D-92](docs/decisoes/D-92-nunca-duas-execucoes-do-mesmo-ativo-ao-mesmo-tempo.md)).
  Configuração por variáveis `RUVOR_*`; mypy estrito, com as tarefas Celery tipadas por
  `celery-types` ([D-134](docs/decisoes/D-134-tarefas-celery-tipadas-por-celery-types.md)) e o
  DRF pelos `djangorestframework-stubs`; 1397 testes com pytest-django, que
  **rodam no contêiner `worker`** — é o único que tem o motor
  ([D-33](docs/decisoes/D-33-dia-a-dia-dentro-do-conteiner.md) segue valendo para o resto).
  `migrate` num banco vazio cria os quatro esquemas — `core`, `bronze`, `silver` e `gold` —,
  as tabelas `core.organization`, `core.user`, `core.compute_request`, `core.api_key` e `core.report`, a organização fixa do Marco 1 (`slug`
  `ruvor`), as cinco tabelas da `bronze`, e `silver.asset`, `silver.price`,
  `silver.corporate_event`, `silver.company`, `silver.financial_statement` e
  `silver.disclosure`, e as sete tabelas da `gold`, `gold.behavior_metric`,
  `gold.return_histogram_bin`, `gold.risk_run`, `gold.risk_result`, `gold.model_snapshot`,
  `gold.fundamental_indicator` e `gold.peer_comparison`, mais `core.compute_request`,
  `core.access_event`, `core.api_key`, `core.report` e `public.django_session` — trinta e duas ao todo. O `AUTH_USER_MODEL`
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
  [D-48](docs/decisoes/D-48-catalogo-em-silver-por-ticker-atualizado-por-coleta.md));
  `manage.py import_prices` consulta o Yahoo e conforma dez anos de preços com retorno
  logarítmico ([D-50](docs/decisoes/D-50-preco-vem-do-chart-v8-do-yahoo-por-http-direto.md) a
  [D-54](docs/decisoes/D-54-transacao-por-ativo-restringe-a-d-48.md)); `manage.py
  compute_metrics` lê `silver` e escreve em `gold`, por ativo e em transação, a linha imutável
  de métricas de comportamento mais os 42 baldes do histograma de retornos
  ([D-55](docs/decisoes/D-55-metrica-de-comportamento-e-imutavel.md) a
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
  [D-81](docs/decisoes/D-81-imagem-do-worker-travada-pelo-lock-e-versoes-na-identidade.md)). `manage.py
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
  casco (`components/Shell.tsx`); consome `brand/ruvor/tokens.css` e `components.css` pelo apelido
  `@brand`, e o proxy do Vite leva `/health` e `/api` à `web`. **Todo texto visível mora em
  `src/content/`** (copiado dos mockups aprovados), e varreduras reprovam cor literal, texto literal
  em `.tsx` (pela árvore sintática, com `@babel/parser`) e vocabulário de recomendação. Desde o M2.3, **duas
  leituras**: o alternador Iniciante/Avançada no casco (`components/ReadingSwitch.tsx`), lembrado em `localStorage`
  (`ruvor-reading`) por `src/reading.ts`, com o padrão iniciante; a frase avançada de cada número da lista fechada em
  `src/content/avancado.ts` (`TEXTOS_AVANCADOS`, mesma chave e mesma assinatura da iniciante de `textos.ts`), e o que é
  método ou estatística recolhido na iniciante pelo `components/Collapsible.tsx`
  ([D-151](docs/decisoes/D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md),
  [D-152](docs/decisoes/D-152-o-nivel-de-leitura-e-escolha-do-visitante.md)) — número novo com frase nasce com as duas
  entradas. 1206 testes.
  `frontend/e2e/` é o roteiro da execução real, com o Playwright na imagem oficial, fora da CI.
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
