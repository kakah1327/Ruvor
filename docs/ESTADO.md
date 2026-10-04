# Estado atual

> **Primeira leitura de qualquer sessão.** Diz onde paramos e o que está aberto.
> Atualizado no fecho de cada bloco. O andamento de cada frente, sessão a sessão, está em
> [`frentes/`](frentes/).

**Última atualização:** 2026-10-04

---

## Onde estamos

**Marco:** ✅ **Marco 1 fechado em 2026-09-29** — a ação, e o risco dela; a Fundação fechou em
2026-09-08
**Bloco:** na frente `marco1`, o **M1.6c fechou em 2026-09-29** — as camadas 4 e 5 na tela do ativo
([D-95](decisoes/D-95-o-m1-6-em-tres-blocos.md), [D-99](decisoes/D-99-as-camadas-4-e-5-depois-do-risco-e-as-tabelas-da-fundamentos-sao-contrato.md)) —,
e entrou na `main` pela PR #17, como o M1.6b pela PR #16; e o **M2.1m fechou em 2026-09-29** — a coluna
`core.compute_request.requested_by`, a metade da `marco1` no M2.1a — e entrou na `main` pela PR #18; o **M1.6d fechou em 2026-09-30** — o
acabamento — e entrou na `main` pela PR #27; o **M1.5c fechou em 2026-09-30** — a execução presa em `running` é
fechada pela varredura — e entrou na `main` pela PR #30, em 2026-10-01; o **M1.7 fechou em 2026-10-02** — a busca sem
acento, `has_risk` e a sugestão pela API, a classificação da B3 com vírgula — e entrou na `main` pela PR #32, no mesmo
dia; o **M2.3 fechou em 2026-10-02** — a camada explicativa: o alternador Iniciante/Avançada no casco, a frase avançada
de cada uma das 55 chaves e os detalhes técnicos recolhidos na iniciante
([D-151](decisoes/D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md) a
[D-153](decisoes/D-153-o-parecer-da-cvm-nao-bloqueia-o-m2-3.md)) —, já com a `main` do M1.7 mesclada, e entrou na
`main` pela PR #33; o **M3.3 fechou em 2026-10-02** — o estresse histórico: o ativo e o Ibovespa lado a
lado nos quatro episódios da D-147, em `gold.stress_episode`, pelo `/metrics` e no bloco "Em momentos de estresse"
([D-146](decisoes/D-146-o-estresse-historico-vira-bloco-so-do-ativo-e-so-com-preco.md) a
[D-148](decisoes/D-148-o-estresse-e-tabela-filha-da-metrica-e-sai-pelo-metrics.md)) —, e entrou na `main` pela PR #37;
o **M1.4b fechou em 2026-10-03** — a correção do motor: o GARCH e o EGARCH sem olhar à frente, os três tradicionais em
janela expansiva reestimada a cada 252 pregões, o motor `0.4.0` e os seis ativos cobertos recalculados do zero
([D-157](decisoes/D-157-alteracao-no-motor-em-lista-fechada-para-a-correcao-do-m1-4b-restringe-a-d-76.md) a
[D-159](decisoes/D-159-a-linha-de-base-numerica-e-a-do-motor-0-4-0-restringe-a-d-44.md)) —, já com a `main` do M2.2a e
do M3.3 mesclada, e entrou na `main` pela PR #38, única — spec, plano e implementação (o portão da spec e do plano foi a
aprovação do dono na conversa, em 2026-10-02); o **M2.1b fechou em 2026-10-03** — as telas de acesso: entrar, cadastro,
troca de senha (inclusive a obrigatória), menu de conta e gestão de usuários, cada uma com mockup aprovado, e o pedido de
cálculo só com conta ([D-140](decisoes/D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md)) —, com a PR de
implementação a abrir pelo dono, revisada pela `identidade`, depois do ajuste dela no caso anônimo do
`test_requested_by.py` — e entrou na `main` pela PR #39; o **M2.4 fechou em 2026-10-04** — o regime de laboratório: o
experimento fixo da década de cada ativo coberto, os nove modelos nos dois níveis pelo cálculo de produção, ano a ano, em
`gold.lab_run`, `lab_result` e `lab_year`, pela rota `/lab` e numa seção da tela do ativo logo depois do risco
([D-183](decisoes/D-183-o-laboratorio-e-o-calculo-de-producao-recortado-na-decada-do-ativo-restringe-a-d-04.md) a [D-187](decisoes/D-187-a-secao-do-laboratorio-fica-na-tela-do-ativo-depois-do-risco-sem-eleger.md)) — e entrou na `main` pela PR #40; o **M5.1 fechou em 2026-10-04** — o retorno: a média histórica e o AR(1) validados fora da amostra contra o retorno zero, com o Diebold-Mariano no veredito, e a previsão do próximo pregão de cada um, sempre junto do veredito, numa seção depois do laboratório; o motor `0.5.0` ([D-188](decisoes/D-188-a-previsao-de-retorno-e-o-log-retorno-de-um-pregao-contra-o-retorno-zero.md) a [D-192](decisoes/D-192-a-tela-mostra-a-validacao-e-a-previsao-junto-dela-com-o-aviso-estende-a-d-160.md)) —, retomado pelo Kauã, com a PR #41 a sair do rascunho; na
frente
`fundamentos`, o **M3.2 fechou em 2026-09-27**, depois do M3.1, e o próximo bloco dela não está
definido; na frente `identidade`, o **M4.1 fechou em 2026-09-30** — o relatório de risco,
exportável e auditável — e entrou na `main` pela PR #28, e o **M2.1a fechou em 2026-09-30** — a T14
preenche o autor do pedido de cálculo, na coluna que o M2.1m criou
([D-107](decisoes/D-107-m2-1a-em-duas-fases-restringe-a-d-82.md)) — e entrou pela PR #29; o **M4.2 fechou em 2026-09-28**;
e o **M2.2a — Carteira fechou no ramo em 2026-10-02** — a composição versionada e o risco dela nos
nove modelos — e entrou na `main` pela PR #34; sem comercialização, o parecer da CVM não a segura ([D-160](decisoes/D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md))
**Frentes:** `marco1` (M1.5b ✅ → M1.6a ✅ → M1.6b ✅ → M1.6c ✅ → M2.1m ✅ → M1.6d ✅ → M1.5c ✅ → M1.7 ✅ → M2.3 ✅ → M3.3 ✅ → M1.4b ✅ → M2.1b ✅ → M2.4 ✅ → M5.1 ✅, com o darkside171 — o M5.1 terminado pelo Kauã) e `identidade` (M2.1a ✅ → M4.2 ✅ →
M4.1 ✅ → M2.2a ✅, com o Kauã desde 2026-09-27, **sem telas** — toda interface visual é da `marco1`); a
`fundamentos` (M3.1 ✅ e M3.2 ✅, também do Kauã) está parada. O andamento de cada uma está em [`frentes/`](frentes/); quem
escreve onde, em [FRENTES.md](FRENTES.md)
([D-84](decisoes/D-84-frentes-com-cerca-de-pastas.md)).
**Ramo:** um por bloco, e PR para entrar na `main`, mesclada pelo dono da frente com a CI
verde ([D-82](decisoes/D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md), que substitui a
D-31; [D-85](decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md), que a restringe)

Existem o motor numérico, o casco da aplicação, o **ambiente local em contêiner** e a
**fundação de dados**. `docker compose up` sobe seis serviços; o Django conecta no
PostgreSQL e tem fila Celery sobre Redis, com o **Celery Beat** agendando a coleta. `migrate`
num banco vazio cria os quatro esquemas
— `core`, `bronze`, `silver` e `gold` —, as tabelas `core.organization` e `core.user` e a
organização fixa do Marco 1 (`slug` `ruvor`), as cinco tabelas da `bronze`, e `silver.asset`,
`silver.price`, `silver.corporate_event`, `silver.company`, `silver.financial_statement` e
`silver.disclosure`. `manage.py import_assets` consulta a B3 e conforma o **catálogo de ações**:
473 na coleta de 2026-09-21. `manage.py import_prices` consulta o Yahoo e conforma
`silver.price` e `silver.corporate_event`: dez anos de PETR4, VALE3, ITUB4 e Ibovespa, ~2.490
pregões cada, com retorno logarítmico. `manage.py compute_metrics` lê a `silver` e povoa a
`gold`: uma linha imutável de métricas de comportamento por ativo e execução, mais os 42
baldes do histograma de retornos. **`manage.py compute_risk`, no contêiner `worker`, é a
camada 3**: roda os nove modelos de VaR e os quatro backtests sobre `silver.price` e grava em
`gold` a execução com o manifesto e os dezoito resultados, cada um com o VaR, os quatro
testes e o veredito de adequação. **Desde o M1.5 isso também roda pela fila:**
`compute_risk --async` enfileira uma abertura por ativo, a `risk_run` nasce no `worker` como
`running`, cada modelo grava os seus dois resultados em transação própria, e o fecho escreve
`ok`, `partial` ou `failed`. **Desde o M3.1 há fundamentos:** `manage.py import_fundamentals`
guarda na `bronze` os zips de ITR e DFP da CVM desde 2016 e conforma companhias e balanços
trimestrais em `silver` — 339 companhias, as do catálogo —, e `manage.py compute_fundamentals`
grava em `gold` os indicadores e a capitalização, uma linha imutável por ação. **Desde o M3.2
há contexto:** `manage.py import_disclosures` guarda na `bronze` os zips do IPE da CVM e conforma
em `silver.disclosure` os fatos relevantes, comunicados ao mercado e avisos aos acionistas das
companhias do catálogo, só na versão corrente — 80.900 —, e o `compute_fundamentals`, depois dos
indicadores, grava em `gold.peer_comparison` a posição de cada ação entre os pares do segmento da
B3, ou do subsetor. Há, além da tarefa de fumaça `config.tasks.ping`, catorze tarefas de app na `main`, em
`apps/risk/tasks.py`, `apps/assets/tasks.py`, `apps/analytics/tasks.py` e
`apps/fundamentals/tasks.py` — dezessete com as três da carteira, em `apps/portfolios/tasks.py`, no
ramo do M2.2a —, tipadas pelo `celery-types`, e o Beat dispara quatro rotinas — o
catálogo, às segundas, e os preços, de segunda a sexta, com as métricas e o recálculo do risco
**encadeados** a eles (`preços → métricas → risco`, desde o M1.6a, e com a varredura das execuções presas antes, desde o M1.5c); os fundamentos, às segundas,
com o cálculo dos indicadores encadeado à coleta; e os comunicados, de segunda a sexta, às 20h.
**Desde o M1.5b o recálculo do risco não refaz o treino:** os quatro modelos caros guardam um
retrato por ponto de retreino em `gold.model_snapshot`, e a rotina reaproveita os válidos,
treina só o que falta e reconstitui a série inteira do backtest por previsão — em segundos por
ativo, igual campo a campo ao cálculo do zero, que `compute_risk --full` ainda faz. O motor está
no `0.4.0` desde o M1.4b: nenhum dos nove modelos usa o retorno do próprio dia, e os três tradicionais reestimam a cada
252 pregões, numa janela que cresce. **Desde o M1.6a há API e kit:** `GET /api/v1/…` entrega catálogo, identidade,
preços, eventos, métricas e risco de um ativo, no formato da
[D-86](decisoes/D-86-convencoes-da-api-http.md), e `POST /api/v1/assets/{ticker}/risk` pede o
cálculo de um ativo nunca calculado — coleta, métricas e risco, pela fila, com um pedido aberto por
ativo, teto global e expiração em `core.compute_request`. O kit de marca tem tokens completos nos
dois temas, a folha de componentes e os ícones, mostrados numa vitrine aprovada no portão de
mockup. **Desde a fase 1 do M2.1a há identidade:** sessão do Django no banco, cache no Redis
(banco 1), papel `admin`/`member` por organização, organização pessoal, e-mail único sem
diferença de caixa, a regra de cada rota de conta como serviço de `apps/accounts`, o bloqueio de
entrada por (e-mail, IP), `core.access_event` — a auditoria de acesso, que só cresce —,
`manage.py create_organization`, e o `createsuperuser` funcionando. **Desde a fase 2 do M2.1a** há as rotas de
conta: `auth/*` e `organization/users*`, com sessão do Django e CSRF, 401 `not_authenticated`
para quem não entrou, `AccountReady` em toda view que exige conta e o limite `auth` por IP.
**Desde o M4.2 a API é pública:** a sessão cria chaves pessoais de leitura em `api-keys`, e a
chave (`Authorization: Bearer rvr_…`) lê as rotas que declaram `api_key_scope = "read"`, só por
método seguro — conta, gestão e as próprias chaves, não; desde o M4.1, isso inclui o relatório da
organização, que é dado privado ([D-115](decisoes/D-115-a-chave-de-leitura-le-o-relatorio-da-organizacao-estende-a-d-108.md)). **Toda rota tem taxa**: por chave, por
usuário e, para anônimo, por IP — as rotas de leitura continuam `AllowAny`, agora com 60 pedidos
por minuto por IP, ajustável por `RUVOR_THROTTLE_ANON`. `GET /api/v1/schema` devolve o esquema
OpenAPI, gerado pelo drf-spectacular sem aviso nem erro. E há o **filtro automático por
organização**, em `apps/accounts/tenancy.py`, aplicado a `core.api_key`. **Desde o M4.1 há
relatórios:** a sessão gera em `POST /api/v1/reports` o relatório de risco de um ativo, guardado
para sempre em `core.report` com os bytes exatos do JSON e o SHA-256 deles, imutável no Django e no
banco — o primeiro gatilho, `report_so_cresce` —, e baixado em JSON (o original) ou CSV (derivado);
`core.report` também usa o filtro por organização. **Desde o M2.2a há carteira** — `apps/portfolios`, a sétima app, e cinco
tabelas, trinta e sete ao todo —, na `main` pela PR #34, sem esperar o parecer da CVM ([D-160](decisoes/D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md)). **Desde o M1.6b há telas:** a busca (`/`) e a tela do ativo (`/ativos/{ticker}`), com a
identidade, o preço, os proventos, o comportamento e o risco — a discordância entre os nove modelos, os
não rejeitados por nível, a tabela com os testes e a trilha do cálculo —, o pedido de cálculo de um
ativo nunca calculado e o acompanhamento dele, nos dois temas, de 360 a 1440 px. **Desde o M1.6c a tela tem as
cinco camadas:** depois do risco, os fundamentos — os 17 indicadores do último balanço, com a frase de cada um, o
porquê de cada nulo e a posição entre os pares do segmento em contagem exata — e os comunicados da companhia à CVM,
com filtro por categoria, pelas rotas `/fundamentals` e `/disclosures`. **Desde o M1.7 a busca ignora acento**, pela
extensão `unaccent` do PostgreSQL ([D-143](decisoes/D-143-a-busca-ignora-acento-pelo-unaccent.md)); o item da busca traz
`has_risk` e a busca o filtra; a sugestão da página inicial e da tela "ativo não encontrado" vem da API
(`has_risk=true&limit=8`), não mais de uma lista fixa; e a classificação da B3 sai da API com vírgula, por tabela
fechada, com o `silver` como veio
([D-144](decisoes/D-144-a-classificacao-da-b3-se-corrige-na-saida-da-api-estende-a-d-47.md)). **Desde o M2.3 há duas leituras:** o alternador
Iniciante/Avançada no casco, lembrado no navegador (`ruvor-reading`), troca a frase de cada um dos 55 números da lista
fechada pela técnica — o que é, como se calcula, sobre que janela — e abre, na avançada, o que a iniciante recolhe: a
assimetria e a curtose, a tabela dos nove modelos com os testes de cada um e a trilha do cálculo. O número é o mesmo nos
dois níveis, e a troca não pede nada à API. **Desde o M2.1b há telas de acesso:** `/entrar` e `/cadastro`, em tela cheia,
fora do casco; `/conta/senha` e `/organizacao/usuarios`, no casco; a troca obrigatória da senha provisória no lugar de
qualquer rota, sem mudar a URL; o menu de conta por último na barra, com o Sair; os avisos de sessão terminada e de página
só para quem entrou; e, para o anônimo, o convite a entrar no lugar do botão de calcular — porque o `POST /risk` passou a
exigir conta pronta ([D-140](decisoes/D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md)). **Desde o M2.4 há o
laboratório:** para cada ativo coberto com a década completa (dez anos de preço desde o primeiro pregão), o experimento
fixo — os nove modelos nos dois níveis pelo mesmo `run_models` da produção, recortados em anos de 252 pregões, com o
veredito de cada ano só a 95% — fica em `gold.lab_run`, `gold.lab_result` e `gold.lab_year`, imutáveis no Django e no
banco, um `ok` por identidade; o fecho do risco o enfileira quando ele é devido, e `manage.py compute_lab` o grava à mão;
a tela do ativo o mostra logo depois do risco, para todos, sem eleger, pela rota `/lab` — quarenta e uma tabelas ao todo
([D-183](decisoes/D-183-o-laboratorio-e-o-calculo-de-producao-recortado-na-decada-do-ativo-restringe-a-d-04.md) a [D-187](decisoes/D-187-a-secao-do-laboratorio-fica-na-tela-do-ativo-depois-do-risco-sem-eleger.md)).
**Desde o M5.1 há o retorno**, no motor `0.5.0`: para cada ativo coberto, a média histórica e o AR(1) preveem o
log-retorno de cada pregão de teste, reestimando a cada 252 pregões, e o backend grava em `gold.return_run` e
`gold.return_result` — imutáveis — o erro relativo à referência de retorno zero, o acerto de direção ao lado da parcela de
alta, o Diebold-Mariano que decide o veredito, o Clark-West e o Pesaran-Timmermann, e a previsão do próximo pregão com a
data; roda no quinto elo da `rotina_diaria` e na cadeia sob demanda, e `manage.py compute_returns` o grava à mão. A tela
do ativo o mostra depois do laboratório, pela rota `/returns`, com o aviso sempre aberto e a previsão só na linha do
modelo, depois do veredito e do histórico, sem seta nem cor — quarenta e três tabelas ao todo
([D-188](decisoes/D-188-a-previsao-de-retorno-e-o-log-retorno-de-um-pregao-contra-o-retorno-zero.md) a [D-192](decisoes/D-192-a-tela-mostra-a-validacao-e-a-previsao-junto-dela-com-o-aviso-estende-a-d-160.md)).

**Existe CI.** Cada pull request e cada push na `main` disparam quatro trabalhos em máquina
limpa — `estilo`, `backend`, `frontend` e `motor` —, e a primeira execução ficou verde nos
quatro. Desde 2026-09-26, **PR vermelha não entra**
([D-83](decisoes/D-83-a-ci-barra-na-pr.md), que substitui a D-42); o barramento automático
espera a proteção da `main` ser ligada no GitHub. `ruff` cobre os dois projetos Python, `Biome` cobre o
frontend, e o motor entrou no estilo com a formatação provada por árvore sintática
([D-44](decisoes/D-44-o-motor-entra-no-estilo.md)).

**O dia a dia de `backend/` e `frontend/` roda dentro do contêiner**
([D-33](decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)); o motor segue no `.venv/` nativo.
**Desde o M1.4 a suíte e o `mypy` do backend rodam no `worker`, não na `web`** — é o único
contêiner que tem o motor, e `apps/risk/` o importa (RF-16b). Consequência que engana quem
não sabe: **`pytest backend` no hospedeiro reprova onze testes e dá erro em duzentos e
vinte**, de propósito — o `settings_test.py` fixa valores de banco inexistentes para que um
`.env` incompleto não passe despercebido. Cinco leem o banco configurado; seis são o V-17 do
M1.5b, que confere a imagem do `worker` e lê o lock em `/repo/engine`, o caminho de dentro do
contêiner; os erros são os testes que pedem `django_db` e nem conseguem criar o banco de teste.
**Dentro do contêiner os cinco exigem `migrate` aplicado.** Não é regressão — medido em
2026-09-27, com 529 testes: `11 failed, 298 passed, 220 errors`, depois do merge das duas
frentes; e no fecho do M3.2, com 622: `11 failed, 357 passed, 254 errors`.

## O que foi concluído

### Documentação e processo (F1)

- **Produto** — [PRODUTO.md](PRODUTO.md): as cinco camadas, público, marcos, requisitos candidatos
- **Arquitetura** — [ARQUITETURA.md](ARQUITETURA.md): pilha, estrutura, banco, execução, auditoria, regimes
- **Processo** — [PROCESSO.md](PROCESSO.md): ciclo, anatomia de spec e plano, agentes, portões
- **95 decisões registradas** — [decisoes/](decisoes/)
- **Identidade visual** — kit em [`brand/ruvor/`](../brand/ruvor/), com as quatro telas de
  referência em `brand/ruvor/mockups/`
- **Agentes do projeto (F6, antecipado)** — [`.claude/agents/`](../.claude/agents/):
  explorador, revisor e implementador

### F2a — Migração do motor

O motor saiu de `varlab/` e virou o pacote `engine/`, com layout `src/`, empacotamento
próprio (`ruvor-engine`) e o rebrand aplicado. Linha de base numérica com diferença zero em
12 combinações; 58 testes; mypy limpo; prova de que `engine/` não importa plataforma.

> A verificação "`import engine` sem Django instalado" foi feita no F2a, num ambiente sem
> Django. Desde o F2b o `.venv/` compartilhado **tem** Django, então a garantia viva passa a
> ser `engine/tests/test_modulos_proibidos.py`, que continua passando.

### F2b — Casco da aplicação

Spec e plano em [`specs/F2b-casco-da-aplicacao.md`](specs/F2b-casco-da-aplicacao.md) e
[`planos/F2b-casco-da-aplicacao.md`](planos/F2b-casco-da-aplicacao.md). Seis tarefas, um
commit cada, direto na `main`.

| Verificação | Resultado |
|---|---|
| `GET /health` → `200 {"status": "ok"}`, sem banco | ✅ `curl` no `runserver` e 2 testes com pytest-django |
| Django sobe sem variável? | ✅ não: `ImproperlyConfigured` citando `RUVOR_SECRET_KEY` |
| mypy estrito sobre `backend/` | ✅ 10 arquivos, com o plugin do django-stubs |
| React em TypeScript estrito | ✅ `tsc --noEmit` limpo; mutação TS7006 reprova |
| Tokens da marca no pacote final | ✅ `--ruvor-ink` presente no CSS do `vite build` |
| Proxy do Vite até o Django | ✅ `localhost:5173/health` responde pelo proxy |
| Sem cor literal em `frontend/src/` | ✅ varredura automatizada; 2 mutações reprovam |
| Tela renderiza marca e estado do backend | ✅ Vitest, 5 testes; mutação de rótulo reprova |
| Frontend do protótipo removido | ✅ 29 arquivos; nenhum resíduo |
| `engine/` segue sem plataforma | ✅ `test_modulos_proibidos` passa com Django instalado |

**Revisão adversarial: aprovada**, sem achado grave. O único achado médio (DOM não limpo
entre os testes da tela) foi corrigido inline antes do fechamento.

**Ambiente:** Node 24.20 entrou via **fnm**, sem substituir o Node 20.11 global da máquina,
que outros projetos usam. `frontend/.nvmrc` e `engine-strict` garantem a versão.

### F3 — Ambiente local

Spec em [`specs/F3-ambiente-local.md`](specs/F3-ambiente-local.md) e plano em
[`planos/F3-ambiente-local.md`](planos/F3-ambiente-local.md). Dez tarefas, um commit cada,
direto na `main`.

| Verificação | Resultado |
|---|---|
| Cinco serviços saudáveis por `docker compose up` | ✅ `--wait` devolve 0; saudáveis na primeira subida |
| Duas imagens do mesmo fonte | ✅ um arquivo, dois alvos; `python --version` idêntico (3.12.14) |
| `import tensorflow` falha na `web`, funciona na `worker` | ✅ e `import django` funciona nas duas — os quatro casos |
| Django conecta no Postgres | ✅ cursor contra o banco **configurado**, conferindo `current_database()` |
| Tarefa enfileirada pelo `web` executada pelo `worker` | ✅ devolve `worker`; modo síncrono desligado |
| `compose` lê o `.env` | ✅ sem nada exportado no shell |
| Frontend alcançável, e `/health` pelo proxy | ✅ nas portas publicadas |
| As quatro portas configuráveis | ✅ trocadas e reverificadas, sem cliente no hospedeiro |
| Teste e tipos dentro do contêiner | ✅ os quatro comandos; `mypy` sobre 14 arquivos, mesma lista do hospedeiro |
| `RUVOR_ALLOWED_HOSTS` tolera espaço | ✅ `_split_hosts`, cinco testes |
| Documentação não mente | ✅ varredura sobre lista fechada de oito trechos |

**As sete mutações reprovaram** — nenhuma verificação do bloco aprova com o trabalho mal
feito. **Revisão final: aprovada**, com os onze requisitos reconferidos por execução e os
cinco arquivos literais idênticos ao plano.

Cinco decisões nasceram do bloco: [D-32](decisoes/D-32-frontend-no-compose.md) (frontend no
compose), [D-33](decisoes/D-33-dia-a-dia-dentro-do-conteiner.md) (dia a dia no contêiner),
[D-34](decisoes/D-34-banco-celery-e-redis-no-f3.md) (banco, Celery e Redis no F3),
[D-35](decisoes/D-35-compose-e-dockerignore-na-raiz.md) (compose na raiz) e
[D-36](decisoes/D-36-versao-do-postgres.md) (Postgres 18).

**Ambiente:** WSL 2.7.12 e Docker Desktop 4.89, instalados em 2026-09-02 com programa e dados
em `E:\Docker` — o `C:` tem pouco espaço. Docker Engine 29.7.2, Compose v5.5.0. As imagens
saíram maiores que a estimativa: `web` 467 MB, `worker` 3,79 GB.

**A recarga a quente exigiu sondagem.** A montagem Windows→contêiner não propaga aviso de
alteração: o contêiner enxerga o arquivo novo, o Vite não emite evento. Ligada em `7a327b3`,
depois de a falta ser medida.

### F4 — Fundação de dados

Spec em [`specs/F4-fundacao-de-dados.md`](specs/F4-fundacao-de-dados.md) e plano em
[`planos/F4-fundacao-de-dados.md`](planos/F4-fundacao-de-dados.md). Sete tarefas, um commit
cada, direto na `main`.

| Verificação | Resultado |
|---|---|
| Os quatro esquemas existem depois do `migrate` | ✅ `core`, `bronze`, `silver`, `gold`, por migration versionada |
| Nenhuma tabela de domínio no `public` | ✅ conjunto **inteiro** de `esquema.tabela` contra lista fechada de nove, não amostra |
| Organização fixa do Marco 1, idempotente | ✅ `slug` `ruvor`; provada com `migrate --fake`, que é o que mantém a linha no banco |
| `AUTH_USER_MODEL` próprio, na primeira migration | ✅ `accounts.User`, `AbstractBaseUser`, autentica por e-mail |
| Organização obrigatória no usuário | ✅ **duas camadas** provadas em testes separados: o gerente recusa, e a coluna é `NOT NULL` |
| `migrate` do zero, e a segunda execução | ✅ código 0 nas duas; `migrate accounts zero` também volta |
| `makemigrations --check` limpo | ✅ |
| mypy sobre o código novo | ✅ 25 arquivos, e a lista nomeia as duas migrations |
| `GET /health` sem tocar no banco | ✅ segue sem marca de banco, como o F2b congelou |
| A imagem constrói com o pacote novo | ✅ e foi preciso copiar os `__init__.py` no `Dockerfile` |

**As onze mutações reprovaram.** **Revisão final: aprovada**, com os dez requisitos
reconferidos por execução e o banco refeito do zero.

Cinco decisões nasceram do bloco: [D-37](decisoes/D-37-esquema-core-para-dado-operacional.md)
(esquema `core`), [D-38](decisoes/D-38-public-guarda-o-encanamento.md) (o `public` guarda o
encanamento, e o esquema vai no `db_table`),
[D-39](decisoes/D-39-usuario-proprio-autentica-por-email.md) (usuário próprio por e-mail),
[D-40](decisoes/D-40-identificadores-de-esquema-em-ingles.md) (identificadores em inglês) e
[D-41](decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md) (o filtro por
organização é do M2.2).

**O que a execução contrariou.** A mutação que troca o `db_table` pelo nome sem esquema
**não** reprovava como escrita: quem cria a tabela é o `options` do `CreateModel`, não o
modelo, então aplicá-la só em `models.py` atacava o requisito errado. Nenhuma das quatro
rodadas de revisão pegou — foi preciso executar.

### F5 — Integração contínua

Spec em [`specs/F5-integracao-continua.md`](specs/F5-integracao-continua.md) e plano em
[`planos/F5-integracao-continua.md`](planos/F5-integracao-continua.md). Oito tarefas, onze
commits, direto na `main`.

| Verificação | Resultado |
|---|---|
| Push dispara a CI, e os quatro trabalhos executam | ✅ run `34207505155`, **verde nos quatro**, 2m14s de parede |
| Backend no contêiner, com banco migrado | ✅ `migrate` cria os esquemas do zero no runner; 16 testes |
| Frontend na imagem, não no Node do runner | ✅ os quatro comandos |
| Motor com extras completas | ✅ 34 testes e mypy; TensorFlow instalado pelo lock |
| A imagem `worker` não é construída | ✅ nenhuma menção a `ruvor-worker` no log; só `Worker ID:` do runner |
| `ruff` nos dois projetos Python | ✅ `All checks passed!`; 44 e 25 arquivos formatados |
| `Biome` no frontend | ✅ `biome check .` |
| A formatação não alterou a árvore sintática | ✅ **69 arquivos, zero divergência** — cobre os nove modelos, não os seis da linha de base |
| Documentação não mente | ✅ nove verificações, com os cinco negativos provadamente acusando antes |

**As oito mutações reprovaram.** **Revisão final: aprovada**, com os dez requisitos
reconferidos por execução.

Quatro decisões nasceram do bloco: [D-42](decisoes/D-42-ci-avisa-e-nao-bloqueia.md) (a CI
avisa e não bloqueia), [D-43](decisoes/D-43-ruff-e-biome-e-onde-cada-verificacao-roda.md)
(ruff e Biome, e onde cada verificação roda),
[D-44](decisoes/D-44-o-motor-entra-no-estilo.md) (o motor entra no estilo) e
[D-45](decisoes/D-45-a-ci-mora-em-github-workflows.md) (a CI mora em `.github/workflows/`).

**O achado do bloco não era sobre CI.** A primeira execução do motor em Linux revelou que a
linha de base numérica **não é portátil entre plataformas** — ver a dívida abaixo. Era
exatamente o que a spec dizia na abertura: nunca ninguém havia rodado este repositório numa
máquina limpa.

**Nove rodadas de revisão** entre spec e plano, mais que os quatro blocos anteriores somados.
Todas as reprovações foram de método, não de direção: medição feita fora das condições reais,
e verificação que não sabia reprovar. Está em [aprendizados.md](aprendizados.md).

### M1.1 — Catálogo de ativos

Spec em [`specs/M1.1-catalogo-de-ativos.md`](specs/M1.1-catalogo-de-ativos.md) e plano em
[`planos/M1.1-catalogo-de-ativos.md`](planos/M1.1-catalogo-de-ativos.md). Nove tarefas, oito
commits (a T8 não produz), de `125a81f` a `336803c`, direto na `main`. Primeiro bloco do Marco
1 e primeiro a povoar `bronze` e `silver`.

| Verificação | Resultado |
|---|---|
| As quatro tabelas nos esquemas certos; conjunto inteiro de treze | ✅ `test_esquemas`, e `migrate accounts zero` desfaz o `assets` antes — a dependência de grafo está declarada |
| Ibovespa por migration idempotente | ✅ `--fake` prova; `create` no lugar de `get_or_create` viola o `UNIQUE` |
| Payload da B3 gravado sem transformação | ✅ igualdade semântica com as fixtures; `{}` gravado |
| Só `type == "1"` consultado | ✅ contagem de chamadas do cliente falso |
| Regex de código de ação | ✅ `PETR-DEB62` e `BBAS12` fora; `BBAS11` dentro |
| Segunda coleta só avança `last_seen_run` | ✅ linha a linha, `updated_at` intacto |
| Papel some → `inactive`; volta → `active` | ✅ três coletas, `first_seen_run` intacto |
| Falha no meio não toca na `silver`; `failed` gravado fora da transação | ✅ `Asset` antes == depois; a `bronze` fica com o coletado |
| Código repetido entre companhias → `failed` antes de escrever | ✅ mensagem com os dois `codeCVM` |
| Nenhum teste sai para a rede | ✅ guarda em `urlopen`; `ci.yml` intocado |
| **Coleta real, V-08** (2026-09-21, 68 s) | ✅ `listagem: 3525 companhias em 30 paginas` · `consultadas (type=1): 570` · `acoes conformadas: 473` · `casos de borda: detalhe vazio 8, hasQuotation=S sem codigo de acao 52, classificacao fora de tres partes 0` |
| **Segunda coleta, V-09** (64 s) | ✅ 2 `collection_run`, `max(updated_at)` inalterado, 0 ativas fora da última coleta |

**As nove mutações reprovaram.** **Revisão final: aprovada.** 82 testes no backend; mypy e
ruff limpos; `makemigrations --check` limpo.

Três decisões nasceram do bloco: [D-47](decisoes/D-47-fonte-do-catalogo-e-o-site-da-b3.md)
(a fonte é o site da B3, com o risco assumido),
[D-48](decisoes/D-48-catalogo-em-silver-por-ticker-atualizado-por-coleta.md) (catálogo em
`silver`, por ticker, atualizado por coleta; payload da `bronze` imutável) e
[D-49](decisoes/D-49-catalogo-do-marco-1-so-acoes-e-ibovespa.md) (só ações e Ibovespa).

**O que a execução contrariou.** A B3 devolve `otherCodes: null`, não `[]`; o `cnpj` da
listagem vem sem zeros à esquerda (`191`), o do detalhe completo — a conformação lê o detalhe.
O esqueleto literal do `run_import` no plano desempacotava um `pages` sem uso, que o `ruff`
recusa; virou um `Listing(items, pages)` sem mudar a sequência. E a mutação 9 (`from
urllib.request import urlopen`) **sai para a rede de verdade** quando aplicada: escapa da guarda
e do `urlopen` falso.

**O achado do bloco.** Dos 52 `hasQuotation=S sem codigo de acao`, 44 têm `otherCodes: null` e
**8 têm código com sufixo `B`** — `EQMA3B`, `MRSA3B`, `LTEL3B`... —, ações do mercado de balcão
organizado (SOMA), que o regex do RF-05 exclui por contrato. E `listing_segment` é nulo em 192
das 473 ações: o `market` da listagem vem vazio para a maioria. Registrados abaixo.

### M1.2 — Ingestão de preços

Spec em [`specs/M1.2-ingestao-de-precos.md`](specs/M1.2-ingestao-de-precos.md) e plano em
[`planos/M1.2-ingestao-de-precos.md`](planos/M1.2-ingestao-de-precos.md). Sete tarefas, seis
commits (a T6 não produz), de `2342ae5` a `8040e4d`, direto na `main`.

| Verificação | Resultado |
|---|---|
| Três tabelas nos esquemas certos; conjunto inteiro de dezesseis; `0003` reversível | ✅ |
| Resposta do Yahoo gravada crua, inclusive o 404 | ✅ igualdade semântica, relida da tabela |
| Data no fuso da bolsa; pregão nulo descartado | ✅ o cenário `01:00Z` prova a regra; `03:00Z` não provaria |
| `log_return` em `Decimal` sobre os ajustados quantizados; antecessor do banco | ✅ valores conferidos à mão |
| Reconformar não duplica nem escreve o que não mudou | ✅ `updated_at` e `run` intactos em coleta igual |
| Evento novo rebusca a série inteira | ✅ duas chamadas, a segunda conformada |
| Transação por ativo, quatro formas de falha | ✅ inclusive a (d): gravação que levanta reverte só aquele ativo |
| `provider_symbol` é a única fonte do símbolo | ✅ |
| Nenhum teste sai para a rede | ✅ |
| **Coleta real, V-06** (2026-09-22, **6 s**) | ✅ IBOV 2.490 pregões / 8 descartados; ITUB4, PETR4, VALE3 2.490 / 1; 162, 34 e 23 eventos |
| **Incremental, V-07** (2 s) | ✅ 6–7 pregões por ativo, 0 criados, 0 atualizados — a sobreposição veio idêntica |
| **Ticker inválido, V-08** | ✅ aborta antes de qualquer chamada, sem `collection_run` |

**As doze mutações reprovaram.** **Revisão final: aprovada.** 136 testes no backend; mypy e
ruff limpos.

Cinco decisões nasceram do bloco: [D-50](decisoes/D-50-preco-vem-do-chart-v8-do-yahoo-por-http-direto.md)
(Yahoo por HTTP direto), [D-51](decisoes/D-51-cobertura-e-o-que-tem-preco.md) (cobertura é o
que tem preço), [D-52](decisoes/D-52-a-janela-de-precos-so-cresce.md) (a janela só cresce),
[D-53](decisoes/D-53-evento-novo-rebusca-a-serie-inteira.md) (evento novo rebusca a série) e
[D-54](decisoes/D-54-transacao-por-ativo-restringe-a-d-48.md) (transação por ativo).

**O que a execução contrariou.** Os nulos do Yahoo se movem: o pregão nulo da Petrobras era
2026-09-17 na sonda de domingo e 2026-09-21 na captura de terça — o de 09-17 foi preenchido. O
Yahoo é rápido: 6 s para quatro ativos e dez anos, contra a estimativa de ~1 min por ativo. O
ITUB4 paga dividendo mensal: 158 dividendos e 4 desdobramentos em dez anos. O exemplo de
relatório da spec mostrava `FALHOU (HTTP 404: …)`; o código imprime com o nome da classe,
`FALHOU (InvalidResponse: HTTP 404: …)`, e a spec foi corrigida. A conformação pura ganhou
módulo próprio, `conform_prices.py`, em vez de morar em `prices.py` — o mesmo corte que o M1.1
fez com `conform.py`.

**Lacuna leve, registrada:** `--full` não tem teste pela casca (`call_command`); só por
`run_import_prices`. Trocar `full=full` por `full=False` no comando passaria a suíte. **O M1.3
não repetiu a lacuna:** os três testes do `compute_metrics` são pela casca.

### M1.3 — Camadas 1 e 2

Spec em [`specs/M1.3-camadas-1-e-2.md`](specs/M1.3-camadas-1-e-2.md) e plano em
[`planos/M1.3-camadas-1-e-2.md`](planos/M1.3-camadas-1-e-2.md). Oito tarefas, um commit cada a partir de `c51366a`, mais as correções do fecho
(a T7 não produz; duas correções pós-T7 entraram), de `c51366a` ao commit de fecho, direto na
`main`.
Primeiro bloco que **calcula** em vez de coletar, e o primeiro a povoar `gold`.

| Verificação | Resultado |
|---|---|
| As duas tabelas na `gold`; conjunto inteiro de dezoito; `0001` reversível | ✅ `migrate analytics zero` e `migrate` saem 0 nos dois |
| Uma linha por (ativo, data de cálculo), imutável | ✅ duas execuções → duas linhas; a primeira intacta campo a campo |
| Baldes pendem da métrica e não atravessam execuções | ✅ 42 por linha, `(metric, bin_index)` único |
| Transação por ativo | ✅ `monkeypatch` em `write_metrics` levantando no segundo: o primeiro e o terceiro ficam |
| Retorno por janela, inclusive `ytd` contra o último pregão do ano anterior | ✅ conferido à mão |
| Volatilidade (`stdev`), assimetria e curtose (`pstdev`, −3) | ✅ divisores divergentes de propósito |
| Maior queda, com topo, fundo, recuperação e pregões | ✅ os três cenários: não recuperada, recuperada, platô e empate |
| Beta e correlação, emparelhando por data | ✅ ativo = 2 × índice → beta 2 e correlação 1; órfãos dos dois lados descartados |
| Janela insuficiente grava nulo, e o histograma sai zerado | ✅ `NULL` nas sete colunas, 42 baldes com soma 0 |
| Ausência do Ibovespa é aviso, nunca erro | ✅ linha gravada, nulos e a linha de aviso |
| Sem dependência numérica nova (V-15) | ✅ `backend/pyproject.toml` intocado; nenhum `import numpy`/`pandas` em `apps/analytics/` |
| Nenhum teste sai para a rede | ✅ a guarda subiu para `tests/conftest.py` e vale para a suíte inteira |
| **Execução real** (2026-09-24, 0,1 s) | ✅ quatro ativos, 4 linhas + 168 baldes |
| **Segunda execução** (0,1 s) | ✅ 8 linhas e 336 baldes; a primeira de cada ativo intacta |

200 testes no backend; mypy (67 arquivos) e ruff limpos; cinco serviços saudáveis.

**As mutações: 25 das 28 reprovaram na primeira medição, com três achados.** O placar não é
"as 28 reprovaram", e os três valem mais que o verde:

1. **O acessor do índice** — o cenário que a spec prescrevia (catálogo com um segundo ativo
   `kind="index"`, a reprovação vindo do `MultipleObjectsReturned` do `.get()`) não havia sido
   implementado por nenhuma tarefa. A mutação passava porque a verificação não existia.
2. **O `adj_close` no denominador do *yield*** — o V-18 **não podia** observá-la: a
   `dividend_summary` recebe o divisor já pronto, então a troca não atravessa a fronteira da
   função sob teste.
3. **`INSTALLED_APPS`** — remover `apps.analytics` faz `manage.py check` e `manage.py migrate`
   saírem **os dois 0**; quem acusa é a coleta do pytest, com código **2**. O critério da spec
   apontava para os comandos errados.

Os dois primeiros foram ligados em `fe03c3d`, com a mutação medida antes (passava) e depois
(reprova). O terceiro virou correção de texto da spec: o critério passou a nomear a coleta do
pytest e o código 2.

**Os números da execução real**, capturados da primeira linha de cada ativo:

| Ativo | Pregões | `as_of` | Beta 60m | Correlação 60m | Volatilidade 12m | Maior queda | Topo → fundo | Recuperação |
|---|---|---|---|---|---|---|---|---|
| PETR4 | 2.489 | 2026-09-18 | 0,8926 | 0,4973 | 26,67% | **−63,36%** | 2020-01-06 → **2020-03-18** | 2021-01-07, 199 pregões |
| VALE3 | 2.489 | 2026-09-18 | 0,8591 | 0,5149 | 26,57% | **−43,72%** | 2018-09-25 → **2020-03-23** | 2020-07-14, 77 pregões |
| ITUB4 | 2.489 | 2026-09-18 | 1,0050 | 0,7044 | 24,06% | **−44,34%** | 2020-01-02 → **2020-03-23** | 2023-12-13, 927 pregões |
| IBOV | 2.482 | 2026-09-21 | — | — | 17,51% | **−46,82%** | 2020-01-23 → **2020-03-23** | 2021-01-06, 195 pregões |

**A maior queda dos quatro caiu em março de 2020**, que era a conferência que só o dado real
faz. O beta e a correlação do IBOV são nulos por identidade, não por lacuna — é o RF-08, e por
isso a linha dele sai `ok` sem `(nulas: …)` por essa causa.

**O que a execução contrariou.**

- **`return_120m` saiu nula nos quatro**, e a causa não é defeito: a janela de 120 meses exige
  um pregão em ou antes de `as_of − 120 meses`. A coleta do M1.2 trouxe "dez anos" a partir de
  2016-09-22, e `2026-09-18 − 120 meses = 2016-09-18` é anterior ao primeiro pregão. Faltaram
  quatro dias. Como a [D-52](decisoes/D-52-a-janela-de-precos-so-cresce.md) mantém o início da
  série, a coluna se preenche sozinha quando `as_of` alcançar 2026-09-22 — sem recoleta.
  "Dez anos de histórico" e "a janela de dez anos existe" não são a mesma afirmação.
- **O plano previu que PETR4 quase certamente teria a maior queda não recuperada. Errou:** os
  quatro recuperaram. O ramo de `max_drawdown_recovery_date` nula, que o plano esperava ver em
  dado real, só foi exercido em teste.
- **A maior queda da VALE3 não é a da covid sozinha.** O topo é 2018-09-25 — a queda começa
  antes de Brumadinho e o fundo é o de março de 2020. O `max_drawdown` percorre a **série
  inteira**, não a janela de 60 meses, e este é o caso em que isso aparece.
- **O histograma quase não usa as pontas abertas:** em 1.247–1.248 retornos por ativo, apenas
  **um** caiu fora de [−10%, +10%] (ITUB4, balde 0). O risco "o histograma tem cauda cortada"
  é real de princípio e raro de fato nesta amostra — e a curtose em excesso de 20,73 do ITUB4
  diz que a cauda está lá, dentro do intervalo, onde o histograma não a destaca.
- **O IBOV tem uma observação a menos** (1.247 contra 1.248): a série dele termina em
  2026-09-21 e a das ações em 2026-09-18, e são 2.482 pregões contra 2.489 — o M1.2 descartou
  oito pregões nulos do índice e um de cada ação.
- **`benchmark_observations` == `statistical_observations` nos três**, 1.248: nenhum par se
  perdeu no emparelhamento por data em cinco anos.
- A soma dos 42 baldes bateu com `statistical_observations` em todos — o V-11 valendo em dado
  real.

Seis decisões nasceram do bloco:
[D-55](decisoes/D-55-metrica-de-comportamento-e-imutavel.md) (métrica imutável, uma linha por
ativo e data de cálculo), [D-56](decisoes/D-56-tabela-de-metricas-larga-e-serie-em-tabela-propria.md)
(tabela larga e tipada; série em tabela própria),
[D-57](decisoes/D-57-janela-estatistica-do-marco-1-e-60-meses.md) (a janela estatística é 60
meses), [D-58](decisoes/D-58-calculo-da-camada-2-mora-no-backend.md) (o cálculo da camada 2
mora no backend), [D-59](decisoes/D-59-sem-dependencia-numerica-nova-no-backend.md) (sem
dependência numérica nova) e
[D-60](decisoes/D-60-metrica-descritiva-sem-manifesto-restringe-a-d-15.md) (métrica descritiva
não carrega manifesto; restringe a D-15).

**O bloco não fecha a camada 1 inteira:** a capitalização de mercado não tem fonte no
repositório e é do M3.1. O ROADMAP registra a ressalva.

### M1.4 — Motor de risco

Spec em [`specs/M1.4-motor-de-risco.md`](specs/M1.4-motor-de-risco.md) e plano em
[`planos/M1.4-motor-de-risco.md`](planos/M1.4-motor-de-risco.md). Dez tarefas, um commit cada,
de `4d5a888` ao commit de fecho, direto na `main` — um por tarefa, menos a T9, que não
produz, mais a correção pós-T4 (`f870e96`). **Primeiro bloco em que
a plataforma consome o motor**, e o primeiro com manifesto de execução.

| Verificação | Resultado |
|---|---|
| As duas tabelas na `gold`; conjunto inteiro de **vinte**; `0001` reversível | ✅ `migrate risk zero` e `migrate` saem 0 nos dois |
| A suíte e o `mypy` do backend migram para o `worker` | ✅ e a `web` continua subindo com `apps.risk` instalado, que é o que prova que `models.py` não encosta no motor |
| Semente fixa nos três neurais | ✅ duas **instâncias novas**, mesma semente → séries de VaR exatamente iguais; sementes diferentes → séries diferentes |
| Nada mudou de número no motor | ✅ linha de base intacta (V-05) **e** `run_experiment` igual à chamada direta no mesmo processo (V-05b) |
| `engine/` segue sem Django | ✅ |
| Retornos do provider batem com `silver.price.log_return` | ✅ diferença absoluta < 1e-9 |
| Nenhum arquivo de `apps/risk/` menciona o `yfinance` | ✅ varredura textual sobre todos os `*.py` |
| Dezoito resultados e a janela de 252, sem execução manual | ✅ o V-20, com os **nove modelos de verdade**, redes incluídas |
| Piso de 503 sessões | ✅ 502 pula, 503 calcula — o par |
| Transação por ativo, veredito, imutabilidade, `price_run` da coleta mais recente | ✅ |
| Registry incompleto e nome errado falham alto | ✅ pela casca e contra o comando real |
| **Execução real** (2026-09-24, **512,0 s**) | ✅ quatro ativos, 4 `risk_run` + 72 `risk_result` |
| **Segunda execução** (**509,4 s**) | ✅ 8 `risk_run` e 144 `risk_result`; a primeira de cada ativo **intacta campo a campo** |
| **`compute_risk --model inexistente`** | ✅ `CommandError: modelos ausentes do registry: inexistente`, código 1, **nada gravado** |

241 testes no backend e **102 no motor**; mypy (83 arquivos no backend, 34 no motor) e ruff
limpos nos dois; vinte tabelas.

**As dezoito mutações reprovaram na primeira medição** — contadas no arquivo, não
estimadas: eram quinze na tabela da spec, e a T9 acrescentou a do `load_all_*`, que a T7
havia identificado e que **só é pega por um teste**, porque o `_REGISTRY` do motor é global
de processo.

#### Os números da execução real

O tempo, por ativo, na primeira execução: IBOV 131,1 s · ITUB4 140,4 s · PETR4 125,4 s ·
VALE3 115,1 s. Na segunda: 129,9 · 140,0 · 124,9 · 114,5.

| Ativo | Pregões | `as_of` | Adequados (de 18) | a 95% | a 99% | Falhos |
|---|---|---|---|---|---|---|
| IBOV | 2.482 | 2026-09-21 | **8** | 7 | 1 | 0 |
| ITUB4 | 2.489 | 2026-09-18 | **9** | 6 | 3 | 0 |
| PETR4 | 2.489 | 2026-09-18 | **7** | 3 | 4 | 0 |
| VALE3 | 2.489 | 2026-09-18 | **4** | **0** | 4 | 0 |

**Nenhum modelo falhou** nos 72 (ativo, modelo, nível): `error` vazio em todos, e nenhum
`adequate` nulo. O ramo do veredito nulo, que existe para "não deu para julgar", só foi
exercido em teste.

**A VALE3 não teve nenhum modelo aprovado a 95%**, e isso é **resultado, não defeito** — é
exatamente o caso que a spec previu e que o M1.6 precisa saber desenhar: nenhum dos nove
métodos descreveu bem aquele ativo naquele nível. Dizê-lo é o tipo de honestidade que o
produto promete.

O `var_latest` do último pregão, em cada ativo, pelos nove modelos:

| Modelo | IBOV 95% / 99% | ITUB4 95% / 99% | PETR4 95% / 99% | VALE3 95% / 99% |
|---|---|---|---|---|
| parametric | 2,07% / 2,96% | 2,69% / 3,85% | 4,35% / 6,17% | 4,35% / 6,25% |
| historical | 2,00% / 3,33% | 2,20% / 4,42% | 4,00% / 6,35% | 4,12% / 6,36% |
| monte_carlo | 2,09% / 2,99% | 2,71% / 3,88% | 4,38% / 6,22% | 4,38% / 6,29% |
| garch_1_1 | 1,71% / 2,41% | 2,43% / 3,43% | 3,51% / 4,96% | 3,05% / 4,31% |
| egarch | 1,56% / 2,21% | 2,43% / 3,44% | 3,43% / 4,86% | 3,23% / 4,57% |
| caviar | 1,49% / 2,28% | 2,04% / 2,75% | 3,38% / 6,29% | 3,19% / 5,18% |
| garchnet | 1,32% / 2,89% | 1,62% / 2,56% | 3,89% / 6,54% | 3,84% / 5,70% |
| lstm | 1,31% / 3,44% | 1,68% / 2,74% | 4,02% / 8,00% | 3,87% / 5,78% |
| gru | 1,25% / 4,14% | 1,81% / 3,20% | 4,09% / 6,85% | 4,10% / 5,75% |

**O que a execução contrariou.**

- **O tempo não foi o problema que a spec temia.** A estimativa era **~1 h**, pelo paralelo da
  Etapa 6; a execução inteira levou **8 min 32 s** para os quatro ativos, ~2 min por ativo,
  sequencial e em CPU. É ~7× mais rápido que o teto declarado, então **não há achado de
  desempenho** e **nada precisa ser antecipado do M1.5**. A estimativa da Etapa 6 continua de
  pé para o escopo dela, que é outro.
- **As duas execuções deram os mesmos números, bit a bit, nos 72 (ativo, modelo, nível)** —
  `var_latest`, `var_mean`, violações, os três `p_value`, a zona e o veredito. Inclusive nos
  três neurais, que é o que não acontecia antes deste bloco. É o critério central do bloco
  medido em dado real, e não só em série sintética.
- **A família GARCH é conservadora demais nesta amostra, e o Kupiec a reprova por isso.** O
  EGARCH do IBOV a 99% produziu **5 violações onde se esperavam 22,29** (p = 9e-06); a 95%,
  29 contra 111,45 (p = 0). Kupiec reprova nos dois sentidos, e aqui reprova por sobra de
  margem, não por falta. **O EGARCH não foi aprovado em nenhum ativo e em nenhum nível** — 0
  de 8 —, e o `garch_1_1` só na VALE3 a 99% (15 violações contra 22,36; p = 0,096).
- **O DQ aprovou 8 dos 72**, e a Basileia reprovou **zero**: 70 zonas verdes e 2 amarelas
  (ITUB4 `garchnet` e `historical`, ambos a 95%), nenhuma vermelha. É a medição que sustenta
  o RF-14 em dado real: incluir o DQ no veredito deixaria quase nada de pé, e incluir a
  Basileia não mudaria nada.
- **Os modelos que mais passam são os de ML**, e por pouca margem: `garchnet` 6 aprovações de
  8 possíveis, `caviar`, `gru` e `lstm` 5 cada; `historical`, `monte_carlo` e `parametric` 2
  cada; `garch_1_1` 1; `egarch` 0. A spec já proíbe eleger um vencedor
  ([D-65](decisoes/D-65-a-plataforma-lista-os-aprovados-e-nao-elege-nenhum.md)), e esta
  distribuição mostra por quê: a ordem muda de ativo para ativo.
- **A discordância entre modelos é grande, e é visível já aqui.** No PETR4 a 99%, o
  `var_latest` vai de **4,86%** (EGARCH) a **8,00%** (LSTM) — quase o dobro, para a mesma
  série e o mesmo dia. É o candidato "discordância entre modelos" do ROADMAP aparecendo sem
  ninguém ter implementado nada para ele.
- **`price_run` saiu 3 nos quatro ativos** — a coleta incremental do M1.2 —, e `requested_by`
  nulo nos quatro, como a spec declarou. `engine_version` gravou **`0.2.0`**, que é o bump da
  T2 chegando ao `worker` pela reconstrução da imagem.

Seis decisões nasceram do bloco:
[D-61](decisoes/D-61-backend-alimenta-o-motor-por-dataprovider.md) (o backend alimenta o
motor por um `DataProvider`), [D-62](decisoes/D-62-a-serie-que-vai-ao-motor-e-o-adj-close.md)
(a série que vai ao motor é o `adj_close`),
[D-63](decisoes/D-63-semente-fixa-entra-no-manifesto.md) (semente fixa, aplicada no início de
cada treino, e no manifesto),
[D-64](decisoes/D-64-veredito-de-adequacao-e-kupiec-e-christoffersen.md) (o veredito é Kupiec
e Christoffersen), [D-65](decisoes/D-65-a-plataforma-lista-os-aprovados-e-nao-elege-nenhum.md)
(lista os aprovados e não elege nenhum) e
[D-66](decisoes/D-66-registry-incompleto-e-erro-restringe-o-silencio-do-motor.md) (registry
incompleto é erro, não silêncio).

**Duas pendências que o portão humano tratou, e só uma foi resolvida:** a divergência do
ROADMAP sobre a fila foi resolvida **a favor do M1.5**, e a linha do M1.4 foi corrigida; o
**regime de laboratório continua sem decisão** — está em *Aberto e aguardando decisão*.

### M1.5 — Execução assíncrona

Spec em [`specs/M1.5-execucao-assincrona.md`](specs/M1.5-execucao-assincrona.md) e plano em
[`planos/M1.5-execucao-assincrona.md`](planos/M1.5-execucao-assincrona.md). Nove tarefas, um
commit cada, de `352c471` ao commit de fecho, direto na `main` — menos a T8, que não produz.
**Primeiro bloco em que o risco roda pela fila, e o primeiro em que alguma coisa roda
sozinha.**

| Verificação | Resultado |
|---|---|
| `status` e `requested_models` sem `default`; a migration `0002` deriva as execuções antigas do dado | ✅ a função, a forma da lista de operações e — V-10c — **as oito do banco real `ok`, com os nove**, remedidas no fecho |
| Nove tarefas por ativo, **enfileiradas**, não executadas em linha (V-02) | ✅ um `chord` de nove e zero `risk_result` depois da abertura |
| Transação por (ativo, modelo), e os dois níveis tudo ou nada (V-03) | ✅ as duas partes |
| Parcial visível; `ok`, `partial` e `failed`; o fecho relativo ao pedido (V-04, V-05, V-05c) | ✅ |
| A tarefa nunca levanta, e o que fica gravado é o par de erro (V-05b) | ✅ com `run_experiment` e com a escrita levantando |
| A `risk_run` nasce no `worker` (V-05d); sem fecho, fica `running` (V-06) | ✅ |
| Síncrono e assíncrono gravam o mesmo, com os nove modelos de verdade (V-07) | ✅ |
| Duas entradas no Beat, o risco encadeado aos preços, o horário é configuração, o elo não se rompe (V-08 a V-10b) | ✅ inclusive o cron em que dia do mês e dia da semana divergem |
| As tarefas de app entram por descoberta automática (V-10d) | ✅ em subprocesso, as sete |
| `engine/` intocado no bloco inteiro (V-11) | ✅ `git diff 2c624b9..HEAD -- engine` vazio |
| Nenhum teste sai para a rede nem fala com o Redis (V-12) | ✅ |
| **Execução real, `compute_risk --async`** (2026-09-25, **4 min 46 s**) | ✅ código 0, o relatório literal, quatro `risk_run` `ok` e 72 `risk_result` — **iguais às execuções 5–8 do M1.4 campo a campo** |
| **Tique real do Beat** (2026-09-25, **4 min 40 s** do disparo ao último fecho) | ✅ `rotina_diaria` → `import_prices` no Yahoo → `recalcular_cobertos` → quatro `risk_run` novas, as quatro `ok` |

304 testes no backend e 102 no motor; mypy (88 arquivos no backend) e ruff limpos; vinte
tabelas; **seis serviços** saudáveis.

**As dezenove mutações reprovaram** — as doze da tabela da spec, as seis que o plano
acrescentou e a do `calculated_at` produzido por abertura, acrescentada na execução. Três
acusam por um caminho que não é o óbvio, e o plano registra: o import explícito de
`apps.risk.tasks` no `celery.py` derruba o processo do pytest com `AppRegistryNotReady` — não
há teste nomeado que reprove, porque não chega a haver teste —; o `finished_at` escrito na
criação não é acusado pelo V-05, que só confere `finished_at` não nulo, mas é pelo V-02, V-04,
V-06 e o teste de `open_run` (a revisão final corrigiu o relato); e a janela da tarefa, só o caso "pregão depois do
`as_of_date`".

#### Os números da execução real

**Medição 1 — o V-10c no banco real.** As oito `risk_run` do M1.4 estão `ok`, com
`requested_models` igual aos nove, 18 `risk_result` cada, nenhuma com erro.

**Medição 2 — `compute_risk --async` sobre os quatro ativos**, com o `worker` reiniciado antes
e `silver.price` intocada desde o M1.4. O comando saiu **0** em 3,5 s e imprimiu:

```
IBOV         enfileirado
ITUB4        enfileirado
PETR4        enfileirado
VALE3        enfileirado
risco assincrono: 4 ativos, 4 enfileirados, 0 pulados; acompanhe em gold.risk_run
```

| Instante (UTC) | O quê |
|---|---|
| 05:48:52,5 | o comando começa |
| 05:48:57,2 | as quatro aberturas terminam — a primeira de cada filho do *prefork* em 1,8 s, as seguintes em 0,04 s |
| 05:49:09 | **primeiros resultados** de IBOV e ITUB4 — `caviar`, `egarch` e `garch_1_1`, ~14 s depois de o comando devolver |
| ~05:51:21 / 05:51:29 | IBOV e ITUB4 com os dezoito |
| ~05:51:30 / ~05:51:41 | **primeiros resultados** de PETR4 e VALE3 — 2 min 34 s e 2 min 45 s depois de o comando devolver |
| 05:53:36,0 | fecho de IBOV, ITUB4 e PETR4, os três em 20 ms |
| 05:53:39,0 | fecho de VALE3 — **4 min 46 s** do começo ao fim, contra os 8 min 32 s do síncrono no M1.4 |

**As dezoito linhas de cada ativo saíram iguais às das execuções 5–8 do M1.4, campo a campo:**
1.080 comparações — 72 resultados × `model_category`, `hyperparameters`, `var_latest`,
`var_mean`, `violations`, `expected_violations`, os três `*_passed` e os três `*_p_value`,
`basel_zone`, `adequate` e `error` —, **zero divergências**; e o manifesto (`engine_version`,
`seed`, as datas, as contagens, `price_run`, `status`, `requested_models`) igual nos quatro.
O script de comparação foi provado contra ativos trocados: acusou 540 divergências.

**RF-12 medido** — memória do `worker` por `docker stats --no-stream`, a cada ~15 s: 157,5 MiB
antes, **pico de 2,94 GiB** na medição 2 (20 amostras) — e **não volta**: 2,91 GiB com o
`worker` ocioso depois. Na medição 4, partindo daí, o pico foi **5,05 GiB** (31 amostras), e
ocioso depois ficou em 5,05 GiB. O contêiner não tem limite declarado; a máquina mostra 15,47
GiB. Ver "o que a execução contrariou".

**Medição 3 — V-11.** `git diff 2c624b9..HEAD -- engine` vazio; `2c624b9` é o pai do commit
da T1.

**Medição 4 — um tique do Beat.** `RUVOR_BEAT_PRICES_CRON=58 2 * * *` no `.env`, `docker
compose up -d --wait beat`, e às **02:58:00 de São Paulo** o Beat enviou
`apps.assets.tasks.rotina_diaria`. A `importar_precos` rodou o `import_prices` real em 0,8 s —
`coleta: 4 ativos, 4 ok, 0 falhos, 0 pulados`; IBOV 2 pregões novos, os outros três 3 cada,
`collection_run` 5 `ok` —, a `recalcular_cobertos` abriu quatro execuções (ids 13–16) com o
mesmo `calculated_at` e `price_run` 5, e as quatro fecharam `ok` às 03:02:40, **4 min 40 s**
depois do disparo. Adequados, de 18: IBOV 8, ITUB4 9, PETR4 7, VALE3 4 — os mesmos totais do
M1.4, com dois ou três pregões a mais. Depois, a linha saiu do `.env`, o `beat` foi recriado,
`printenv` mostrou as duas variáveis vazias e o `CELERY_BEAT_SCHEDULE` voltou a `0 7 * * 1` e
`30 19 * * 1-5`. **O `beat` ficou de pé** — é o estado normal do ambiente a partir daqui.

**O que a execução contrariou.**

- **"Os seis determinísticos em segundos" só vale para parte deles, e só para os primeiros
  ativos da fila.** O cabeçalho do `chord` segue a ordem de `requested_models` — a de `MODELS`,
  alfabética —, e com `--concurrency=2` as duas vagas são tomadas pelas redes assim que elas
  chegam na fila. No IBOV, `caviar`, `egarch` e `garch_1_1` gravaram em ~14 s; `historical`
  esperou ~1 min 40 s, atrás de `garchnet` e `gru`; `monte_carlo` e `parametric`, ~2 min 25 s,
  atrás do `lstm`. E a fila é uma só para todos os ativos: PETR4 e VALE3 não tiveram **nada**
  por 2 min 34 s e 2 min 45 s. Não é defeito do contrato — o plano fixa a ordem do pedido —,
  mas é o oposto do que o "Resultado esperado" da spec promete, e o M1.6 precisa saber antes
  de desenhar a tela. Está em *Aberto e aguardando decisão*.
- **O fecho entra no fim da fila.** O corpo do `chord` é enfileirado quando a última tarefa do
  grupo termina, atrás do que já estava lá: o IBOV ficou **2 min 15 s em `running` com os
  dezoito gravados**, e os quatro fechos saíram juntos, depois da última tarefa do VALE3. Quem
  ler `status` para decidir se a execução acabou vai esperar mais do que o cálculo durou.
- **A memória do `worker` cresce a cada execução e não volta.** 2,9 GiB depois da primeira
  rodada dos quatro ativos, 5,0 GiB depois da segunda. Os filhos do *prefork* vivem entre
  tarefas, e o que eles alocam não volta — a medição é do contêiner inteiro, não por processo,
  então **quem** aloca (o TensorFlow é o suspeito óbvio) não está medido. Com dois filhos, a
  conta "1–2 GB por rede, dois cabem em 4 GB" do RF-12 **não segura** depois de duas rodadas. Não passou do que a
  máquina tem, então é achado **para o M1.5b**, como o plano previu — e é o M1.5b que muda o
  treino de lugar.
- **Os números não mudaram nem um dígito.** Separar os nove em nove chamadas de
  `run_experiment`, em processos-filhos recém-nascidos e sem registry herdado, deu os mesmos 72
  resultados que o síncrono, iguais em todas as casas gravadas — inclusive nas três redes. É o RF-08 medido em dado
  real, e não só no V-07.
- **O `--async` carrega o TensorFlow no processo do comando**: o `enqueue_compute` confere o
  registry antes de enfileirar, e isso importa os módulos das redes — a saída do comando traz
  as mensagens de partida do TensorFlow, e ele levou 3,5 s para enfileirar quatro aberturas.
  Não estorva no `worker`; é mais uma razão para o M1.6, que enfileira da `web`, não herdar
  esse caminho.
- **Mutação em `backend/config/*.py` derruba a `web`**, pela recarga automática, e ela **não
  volta sozinha** quando a mutação é revertida — foi preciso subi-la de novo na T8.
- **O *sync* do Beat ocioso é a cada 300,0 s** (o `max_interval`), medido na T7; o
  `healthcheck` exige o `celerybeat-schedule` tocado há menos de 600 s.
- **Correções de texto, sem mudar contrato**, todas no fim do plano: o esperado do fecho é
  `len(requested_models) * len(config.ALPHAS)`, não `* 2` (a migration mantém `* 2`); o V-05b
  mira `apps.risk.tasks.*`; o relatório tem 13 caracteres antes do status, não 12; o literal do
  Beat foi reformatado pelo `ruff format`; `chain(...)` devolve `celery.canvas._chain`, e o V-09
  identifica a corrente por `subtask_type`; e três arquivos de teste alterados fora do
  inventário da spec, que ganhou a correção.

Seis decisões nasceram do bloco:
[D-67](decisoes/D-67-uma-tarefa-por-ativo-e-modelo-restringe-o-rf-12-do-m1-4.md) (uma tarefa
por (ativo, modelo), e a transação acompanha; restringe o RF-12 do M1.4),
[D-68](decisoes/D-68-o-estado-da-execucao-mora-no-banco.md) (o estado mora no banco, não no
Redis), [D-69](decisoes/D-69-o-agendamento-e-encadeado.md) (o agendamento é encadeado),
[D-70](decisoes/D-70-a-tarefa-nunca-levanta-e-o-fecho-le-o-banco.md) (a tarefa nunca levanta, e
o fecho lê o banco), [D-71](decisoes/D-71-a-risk-run-nasce-no-worker.md) (a `risk_run` nasce no
`worker`) e [D-72](decisoes/D-72-o-fecho-escreve-metadado-de-execucao-restringe-a-d-16.md) (o
fecho escreve metadado de execução; restringe a D-16).

#### Depois do fecho — três pendências decididas (2026-09-25)

- **O `.env.example` fica como está**, com os dois horários preenchidos. Comentar as linhas não
  desligaria nada — ausente ou vazio vale o mesmo padrão do `settings.py` —, só esconderia o
  comportamento. Quem precisar dos preços congelados roda `docker compose stop beat`, como o
  README já diz.
- **O cabeçalho do `chord` sai por custo** — tradicionais, GARCH, ML —
  ([D-73](decisoes/D-73-o-cabecalho-do-chord-sai-por-custo.md)). Dentro de um ativo, os
  modelos baratos passam a gravar antes das redes. **A espera entre ativos continua**, e fica
  com o M1.5b. O V-02 foi ajustado, e a mudança medida: com o cabeçalho na ordem pedida, ele
  reprova.
- **O Marco 1 é só produção; o laboratório vai para o Marco 2**, como bloco M2.4
  ([D-74](decisoes/D-74-o-marco-1-e-so-producao.md)). A PRODUTO e o ROADMAP foram corrigidos.

### M3.1 — Fundamentos

Spec em [`specs/M3.1-fundamentos.md`](specs/M3.1-fundamentos.md) e plano em
[`planos/M3.1-fundamentos.md`](planos/M3.1-fundamentos.md). Frente `fundamentos`, no ramo
`fundamentos/M3.1-fundamentos`: dezenove commits, de `c2994c4` a `5dd0667`, mais o de fecho —
doze de tarefa (T1 a T9, T11, T11b e T11c; a T10 não produz) e sete de correção de spec, plano e
teste. A PR de implementação sai do ramo e passa também pela `marco1`, dona do serviço `beat` e
de `tests/risk/test_beat.py`. **Primeiro bloco fechado por uma frente que não é a `marco1`,
primeiro fora do Marco 1, e o primeiro a trazer balanço.**

| Verificação | Resultado |
|---|---|
| Esquemas, a suíte, o Beat (V-01, V-04, V-05) | ✅ 496 testes no `worker`; `test_esquemas` com as vinte e quatro; `tests/risk/test_beat.py` com as três entradas |
| Sem dependência numérica nova (V-07) | ✅ `backend/pyproject.toml` intocado desde a base do ramo; nenhum `import numpy`/`pandas` em `apps/fundamentals/` |
| **Carga real do zero, V-08** (2026-09-27, **4 min 43 s**) | ✅ 22 arquivos, ~404 MiB; **339 companhias** na `silver`, igual aos 339 `code_cvm` das ações do catálogo; a Petrobras de 2016-03-31 ao trimestre mais recente, sem buraco |
| **Segunda coleta, V-09** | ✅ os 22 `nao modificado`; nenhum `payload` novo na `bronze` |
| **`--reconform 2025`, V-10** | ✅ 0 criados, 0 atualizados, nenhuma chamada à CVM |
| **Cálculo, V-11** | ✅ `calculo: 471 acoes, 0 sem balanco, 0 fora de escala, 0 falhas`; VALE3 com capitalização; PETR4 e ITUB4 com P/L e P/VP e `missing_class_price`; ITUB4 no plano `bank`, com margem nula e ROE; Bradesco, BB, BB Seguridade e BNB com PL e lucro desde 2024 |
| A variável do Beat chega ao serviço (V-12) | ✅ `ok` — e, sem a linha no `compose.yaml`, reprova (mutação 41) |
| **Contra a divulgação das companhias, V-13** | ✅ lucro de 12 meses, PL e dívida bruta de PETR4, VALE3 e ITUB4 — tabela abaixo |

496 testes no backend; vinte e quatro tabelas; cinco apps; dez tarefas de app mais o `ping`;
três entradas no Beat. No hospedeiro, `5 failed, 298 passed, 193 errors` — os mesmos cinco de
antes.

**As mutações reprovaram, e uma só depois de corrigida.** As 40 aplicáveis da T10 reprovaram,
a 41 reprovou na T11, e reprovaram também a da T11b (sem o descarte do ITR) e as quatro da T11c
(sem o RF-08b; o `statement` buscado de novo na escrita; sem o filtro de exercício no ITR do 4º
trimestre; a mãe "Lucro Básico por Ação" aceita como LPA). A 35 passava na primeira medição —
ver abaixo.

**Revisão final em duas rodadas.** A primeira **reprovou**, com um grave: companhias que
informam o lucro só na mãe saíam com lucro 0 — nasceram o RF-08b e a T11c. A segunda
**aprovou**: 0 graves, 3 médios e 5 leves, todos absorvidos; entre eles, a spec listava uma
grafia dos não controladores que não existe na fonte e omitia a dos bancos forma A.

#### Os números da execução real

A carga do zero (2026-09-27) levou **4 min 43 s** para 22 arquivos, ~404 MiB. Memória do
`worker`: ~399 MiB ocioso antes, **pico de 2,235 GiB** durante a conformação. As linhas `ano`
cobrem **2016 a 2026**, com 252 a 338 companhias por ano. A linha
`itr descartados por dfp na mesma data` saiu para AZZAS (`22349`) e Orizon (`25550`) em 2021,
Economatica (`26077`) em 2022 e Tenda (`21148`) em 2023.

**V-13**, em R$ milhões, no 2T26 — **igual à divulgação das companhias** nos nove números:

| Ativo | Lucro de 12 meses | PL | Dívida bruta |
|---|---|---|---|
| PETR4 | 133.376 | 480.950 | 366.533 — 133.734 de dívida financeira + 232.799 de arrendamentos |
| VALE3 | 10.369 | 196.635 | 98.034 |
| ITUB4 | 46.828 | 217.779 | nula — plano `bank` |

Fontes: os releases de RI da Petrobras e da Vale (mziq) e o MD&A do 2T26 do Itaú na SEC — o ITR
do Itaú na CVM é IFRS.

**Depois do RF-08b**, reconformado a partir da `bronze` já baixada: SBSP3 sai com
`net_income_ttm` de R$ 8.040 mi e `roe` 0,178, e **nenhuma** linha da `gold` fica com `roe`,
`net_margin` ou `net_income_ttm` exatamente 0 — antes, eram 37. PETR4, VALE3 e ITUB4 não
mudaram.

**O que a execução contrariou.**

- **ITR e DFP podem ter a mesma data.** A spec dizia que o ITR não tem 4º trimestre, e a
  primeira execução da T11 reprovou a V-08 com `IntegrityError` em quatro (companhia, ano). O
  dono da frente decidiu: vale o DFP. Nasceram o RF-13b e a T11b, e a carga foi refeita do zero
  ([D-128](decisoes/D-128-itr-e-dfp-na-mesma-data-vale-o-dfp.md)).
- **Há companhia que informa o lucro só na mãe**, com as duas filhas zeradas — a Sabesp, e 49
  documentos do catálogo no DFP 2024. A regra dava lucro 0, e ROE e margem 0: número errado com
  cara de certo. Nenhum dos testes o pegava, e a execução real também não: foi a revisão final.
  Vale a mãe ([D-129](decisoes/D-129-lucro-so-na-mae-vale-a-mae.md)).
- **A escala das ações sai nula em cerca de um terço dos documentos**, e quase sempre não pela
  heurística: lucro zerado, LPA ausente nas filhas de "Lucro Básico por Ação", `L/E` negativo;
  fora do fator 2, só 8 no DFP 2024 consolidado. O LPA não cai para a `3.99`. A spec explica a
  conta ("A escala das ações é inferida, não lida").
- **A mutação 35 passava.** O ticker inativo do teste era de uma classe sem ticker ativo, e a
  regra 5 da capitalização dava o mesmo resultado com ou sem o filtro de `status`. O teste que
  faltava — código antigo inativo **da mesma classe** — entrou em `9cacd53`, e a mutação passou
  a reprovar.
- **Os CSVs da CVM têm registros mal formados** — número de campos diferente do cabeçalho, por
  aspas desbalanceadas ou quebra de linha dentro de campo. São descartados na leitura e contados
  por membro, e o relatório diz quantos.

Dez decisões nasceram do bloco:
[D-120](decisoes/D-120-fundamento-vem-dos-dados-abertos-da-cvm.md) (fundamento vem dos dados
abertos da CVM, por HTTP direto),
[D-121](decisoes/D-121-a-bronze-guarda-o-zip-inteiro-e-so-quando-o-conteudo-muda.md) (a `bronze`
guarda o zip inteiro, e só quando o conteúdo muda),
[D-122](decisoes/D-122-conta-se-localiza-pela-descricao-sob-mae-fixa.md) (conta pela descrição
sob mãe fixa; plano de contas por documento; a dívida inclui o arrendamento),
[D-123](decisoes/D-123-resultado-por-trimestre-isolado-e-12-meses-por-soma.md) (trimestre isolado,
4º trimestre derivado, 12 meses por soma),
[D-124](decisoes/D-124-capitalizacao-soma-as-classes-e-a-escala-das-acoes-e-inferida.md) (a
capitalização soma as classes; a escala das ações é inferida),
[D-125](decisoes/D-125-indicadores-em-gold-na-app-da-frente-restringe-a-d-84.md) (os indicadores
em `gold`, na app da frente; restringe a D-84),
[D-126](decisoes/D-126-companhia-e-entidade-ligada-ao-ticker-por-valor.md) (a companhia é
entidade, ligada ao ticker por valor),
[D-127](decisoes/D-127-coleta-de-fundamentos-semanal-e-encadeada-restringe-a-d-69.md) (a coleta
é semanal e encadeia o cálculo; restringe a D-69),
[D-128](decisoes/D-128-itr-e-dfp-na-mesma-data-vale-o-dfp.md) (ITR e DFP na mesma data: vale o
DFP) e [D-129](decisoes/D-129-lucro-so-na-mae-vale-a-mae.md) (lucro só na mãe: vale a mãe).

**A camada 1 fecha a ressalva do M1.3**: a capitalização de mercado passa a existir, em
`gold.fundamental_indicator`, nula quando falta preço de alguma classe e sempre nula para PNA e
PNB.

### M1.5b — Treino separado da previsão

Spec em [`specs/M1.5b-treino-separado-da-previsao.md`](specs/M1.5b-treino-separado-da-previsao.md)
e plano em [`planos/M1.5b-treino-separado-da-previsao.md`](planos/M1.5b-treino-separado-da-previsao.md).
Nove tarefas, um commit por tarefa que produz — a T7 mediu as mutações e não produz —, de
`0985228` ao commit de fecho, no ramo `marco1/M1.5b-treino-separado`, que entra na `main` por PR
([D-82](decisoes/D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md),
[D-85](decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md)). **Muda número do motor** — as três
redes, a partir do segundo trecho de teste —, com a exceção à D-21 declarada e em lista fechada.

| Verificação | Resultado |
|---|---|
| A tabela nasce na `gold`, e a migration `0003` é reversível (V-01) | ✅ no banco de desenvolvimento, antes de haver retrato; as 24 execuções antigas ficaram `full_recompute = false` e os 432 resultados com as contagens nulas |
| **Incremental igual ao do zero, com o motor real (V-02)** | ✅ série do zero, +1 pregão sem cruzar ponto, +1 cruzando: a `var_series` inteira igual ponto a ponto, e os dezoito `risk_result` iguais campo a campo |
| O dia comum não treina (V-03) | ✅ `trained_snapshots == 0` e nenhuma chamada de treino, **por espião** |
| O primeiro trecho das redes não muda (V-04) | ✅ igual bit a bit à referência do `0.2.0`, capturada no `worker` travado; roda só no `worker` |
| `caviar` e baratos intactos (V-05); retomada entre processos bit a bit (V-06) | ✅ |
| Impressão digital estrita, nos dois lados do `trained_through` (V-07) | ✅ decidido pelas contagens, como a spec manda |
| Identidade completa, um retrato fabricado por componente (V-08); imutável e idempotente (V-09) | ✅ os seis componentes; e o novo gravado ao lado |
| `--full` não lê retrato, nos dois caminhos (V-10); o manifesto diz de onde veio (V-11) | ✅ |
| `engine/` só nos arquivos autorizados (V-12) | ✅ `git diff 0f2f7aa..HEAD --stat -- engine/src`: `seeding.py`, `snapshots.py`, `_quantile_nn.py`, `caviar.py`, `runner.py` — cinco da lista do RF-11; `base.py` intocado. Fora de `src/`, só a versão no `pyproject.toml` e os testes. `0f2f7aa` é o pai do commit da spec |
| O tamanho dos retratos (V-13) | ✅ medido — ver abaixo |
| **Execução real (V-14)** | ✅ os cinco passos — ver abaixo, e o que ela **não** mediu |
| A memória do `worker` (V-15) | ✅ sem limite o pico sobe; com `--max-tasks-per-child=5`, não — ver abaixo |
| A imagem travada (V-17); o TensorFlow não entra por `snapshots.py` (V-18); a semente deriva da execução (V-19) | ✅ |

**336 testes no backend e 145 no motor** — 144 no hospedeiro, mais o V-04, que pula fora do
`worker`; mypy (92 arquivos no backend, 35 no motor) e ruff limpos nos dois; **vinte e uma
tabelas**; seis serviços; motor **`0.3.0`**.
A suíte do backend leva **~8 min** no `worker` — o V-02 e os testes que o acompanham treinam as
três redes de verdade. **O tempo dela na CI do GitHub não foi medido.**

**As trinta mutações reprovaram** — as 21 da tabela da spec e 9 acrescentadas pelas tarefas —,
**mais a da T8**, que é o V-15 sem o limite, medida em três rodadas. Três acusam por um caminho
que vale registrar: a do modelo que ignora o `restore` **não muda as contagens** e só é pega pelos
espiões do V-03; e duas da T3 — o otimizador casado por `path` e as chaves do `npz` em `sorted` —
reprovam **levantando erro de forma**, não por número diferente.

#### Os números da execução real

Com o Beat parado desde a T1, o `worker` recriado depois do último commit de código e com
`--max-tasks-per-child=5`. **O tempo de um ativo é a soma das durações das suas nove tarefas
`compute_asset_model`**, lida da linha `risco … modelo=… alpha=0.05 r/t alpha=0.01 r/t N.NNs` do
log do `worker` — não `finished_at − calculated_at`, que inclui a fila.

| Ativo | Passo 1 — `--async --full` | Passo 2 — `--async`, mesma série | Passo 3 — depois da coleta |
|---|---|---|---|
| IBOV | 162,40 s | 8,20 s (5,0%) | 8,14 s (5,0%) |
| ITUB4 | 175,20 s | 8,66 s (4,9%) | 10,27 s (5,9%) |
| PETR4 | 152,65 s | 9,68 s (6,3%) | 8,04 s (5,3%) |
| VALE3 | 140,52 s | 4,50 s (3,2%) | 6,38 s (4,5%) |
| **do comando ao último fecho** | **5 min 35 s** | **25 s** | **25 s** |

**Passo 1** (`risk_run` 49–52, `price_run` 6): as quatro `ok`, 72 resultados, nenhum erro; nos
caros, `reused_snapshots = 0` e `trained_snapshots = 9` nos dois níveis. Os 288 retratos já
existiam, das rodadas `--full` da T8, e **continuaram 288**: a gravação idempotente não duplicou
nenhum. Os 72 resultados saíram iguais, campo a campo, aos da última rodada da T8 (`risk_run`
45–48) — o treino é determinístico entre rodadas. A contagem sozinha não provaria isso: a
unicidade não inclui o `payload`, e um retrato diferente seria descartado em silêncio. Por modelo, no ITUB4: `gru` 68,3 s,
`lstm` 47,5 s, `garchnet` 43,1 s, `caviar` 14,0 s.

**Passo 2** (`risk_run` 53–56): **nada treinado** — `9/0` nos quatro caros, nos dois níveis, nos
quatro ativos — e o resultado **igual ao do passo 1**: 72 pares, pareados por `model_name` e
`alpha`, e 1.080 comparações dos quinze campos restantes do `risk_result` fora os excluídos do
RF-07, **zero divergências**; na `risk_run`, o
manifesto igual nos quatro, com `full_recompute` `true` no passo 1 e `false` no 2. A comparação
foi provada contra ativos trocados: acusou os 72 pares.

**Passo 3** — `import_prices` real às 05:49:45 UTC (código 0; `coleta: 4 ativos, 4 ok`, `price_run`
7) e `compute_risk --async` (`risk_run` 57–60). **Os quatro ficaram no dia comum** —
`trained_snapshots == 0` em todos —, **e os quatro abaixo de 10%** do passo 1: de 4,5% a 5,9%.
Mas veja "o que a execução contrariou": **a coleta, num domingo, não trouxe pregão novo.**

**Passo 4 — retratos invalidados pela coleta: zero**, nos quatro ativos. A coleta só atualizou
o último pregão (2026-09-25) de cada um, e mudou o `adj_close` de dois — IBOV (183.476,859375 →
183.477) e PETR4 (47,990002 → 48,07) —, pregão que nenhum retrato viu: o último ponto de retreino
(posição 2.016) enxerga até o índice 2.268 — da série de 2.494 pregões do PETR4 e da de 2.486 do
IBOV. Por isso mudaram só o `egarch` e o
`garch_1_1` desses dois (8 dos 72 resultados), e nenhum dos caros.

**Passo 5 — o `caviar` e os cinco baratos do passo 1 iguais aos do `0.2.0`** (`risk_run` 21–24,
mesma série): 48 pares, 720 comparações, **zero divergências**; manifesto igual, fora o
`engine_version`. As três redes divergem nos 24 pares — é o RF-05, declarado.

**V-13 — o tamanho.** `payload_bytes` dos 288 retratos, com o estado do otimizador:

| Modelo | Mínimo | Médio | Máximo |
|---|---|---|---|
| `caviar` | 286 B | 286 B | 286 B |
| `garchnet` | 19,5 KiB | 48,5 KiB | 158,3 KiB |
| `gru` | 15,8 KiB | 71,3 KiB | 121,6 KiB |
| `lstm` | 18,8 KiB | 58,1 KiB | 156,8 KiB |

Uma linhagem (72 retratos) custa de **1,14 MiB** (VALE3) a **4,26 MiB** (ITUB4) — a busca de
configuração escolhe redes de tamanhos diferentes —, **3,13 MiB em média**; a tabela inteira
ocupa 14,3 MB para 13,1 MB de `payload` (fator 1,09). **Para 473 ações, uma linhagem: ~1,45 GiB**
de `payload`, ~1,6 GiB com a tabela; ~2 GiB se todas custassem como o ITUB4. **O acúmulo pela taxa
medida no passo 4 é zero** — e o número não vale nada: foi uma coleta, sem pregão e sem evento.
A estimativa que ele não substitui: o `adj_close` do Yahoo é ajustado por provento (difere do
`close` em ~99% dos pregões de ITUB4, PETR4 e VALE3), a D-53 rebusca a série inteira a cada evento
novo, e então **cada provento provavelmente invalida a linhagem desde a posição 0** — cálculo
completo e 3,1 MiB novos. A `silver.corporate_event` tem 162 eventos do ITUB4, 34 da PETR4 e 23
da VALE3 em dez anos. **Não medido**; é o que o dia útil precisa mostrar.

**V-15 — a memória** (T8), pela soma do `VmRSS` dos processos `celery` a cada 5 s. Sem limite,
três rodadas `--full` seguidas: picos de **3,8, 5,9 e 6,7 GiB** — os filhos retêm ~190 MiB por
tarefa de rede —, e o `worker` chegou a ~360 MiB livres. Com `--max-tasks-per-child=5`: **3,0, 2,6
e 2,8 GiB**.

**O Beat voltou** depois da execução (`docker compose up -d --no-deps beat`), saudável, com a agenda
padrão: `0 7 * * 1` (catálogo) e `30 19 * * 1-5` (preços e risco), as duas variáveis vazias.

**O que a execução contrariou.**

- **O dia comum do passo 3 não teve pregão novo.** A execução foi num domingo: a coleta
  reconformou o pregão de sexta e não acrescentou nenhum. Formalmente os quatro cumprem o
  critério da spec — sem retrato invalidado, sem ponto cruzado —, e o custo não deve mudar com
  um pregão a mais, porque o recálculo reconstitui a série inteira de qualquer jeito. **Mas o
  caso "um pregão novo" em dado real ficou sem medir**, e a taxa de invalidação também. O
  primeiro tique do Beat num dia útil (segunda, 19h30) mede os dois sem esforço: as linhas
  `risco …` do log do `worker` trazem o tempo e o `r/t` de cada tarefa.
- **Cerca de 40% do dia comum é reciclar filho, não prever.** Com `--max-tasks-per-child=5`, a
  primeira tarefa de cálculo de cada filho novo do *prefork* (o `ForkPoolWorker-N` da linha de log) paga
  ~1,7 a 1,9 s a mais — `historical`, `parametric` e `caviar`, que levam 0,06 a 0,09 s num filho
  já usado, levaram 1,76 a 1,79 s; uma rede, ~3,2 s contra 1,1 a 1,4 s. Foram 7 das 36 tarefas
  do passo 2, ~12 s dos 31 s somados dos quatro ativos. Num filho já usado, a rede custa 1,1 a 1,4 s pelos dois níveis — 0,55 a 0,7 s por
  (rede, nível), **o que a sonda da spec previu** (0,58 s). O limite da memória e o custo do dia
  comum puxam em sentidos opostos; está medido, não decidido.
- **O preço de um retrato na posição 0 invalidado é o de um ativo novo.** Se a estimativa do
  V-13 se confirmar, os pagadores de provento voltam ao cálculo completo a cada evento — o
  risco que a spec declarou, agora com a razão provável: o `adj_close` retroativo. A saída que
  a spec registra **não** é afrouxar a impressão digital; é estudar a reconformação do M1.2.
- **A memória, medida por processo, é pior que a do M1.5**: 3,8 → 5,9 → 6,7 GiB, não os 2,9 →
  5,0 do `docker stats`. E **não há um número de tarefas a partir do qual o filho passa a reter** —
  retém desde a primeira. O 5 saiu do teto do pior caso, não de um joelho na curva.
- **A máquina travou duas vezes** durante o bloco, com o TensorFlow rodando no hospedeiro e no
  `worker` ao mesmo tempo. O WSL passou a ter teto de **8 GB** (`.wslconfig`), e a regra é um
  comando pesado por vez ([aprendizados](aprendizados.md)).
- **Correções do plano, sem mudar contrato**, registradas no fim dele: recriar o `worker` exige
  `--force-recreate --no-deps`; a escolha do `--max-tasks-per-child` não tinha o "número a
  partir do qual" que o plano supunha; o V-03 depende dos espiões, não só das contagens; duas
  mutações da T3 reprovam por erro de forma; o `payload` não é determinístico em bytes; e a PR
  de implementação, que o critério da T9 pede aberta, fica para o dono da frente.

Sete decisões nasceram do bloco, na ordem da spec:
[D-75](decisoes/D-75-as-redes-semeiam-em-cada-retreino-estende-a-d-63.md) (as redes semeiam em
cada retreino; estende a D-63),
[D-76](decisoes/D-76-alteracao-no-motor-em-lista-fechada-restringe-a-d-21.md) (alteração no
motor em lista fechada; restringe a D-21),
[D-77](decisoes/D-77-os-retratos-moram-em-gold-com-impressao-digital-estrita.md) (os retratos
moram em `gold`, com impressão digital estrita e o estado do otimizador),
[D-78](decisoes/D-78-incremental-igual-ao-do-zero-e-full-e-a-referencia.md) (incremental igual
ao do zero, e `--full` é a referência),
[D-79](decisoes/D-79-os-quatro-caros-usam-retratos-e-os-cinco-baratos-nao.md) (os quatro caros
usam retratos; os cinco baratos, não),
[D-80](decisoes/D-80-o-retreino-de-producao-e-a-cada-252-pregoes-restringe-a-d-18.md) (o
retreino de produção é a cada 252 pregões; restringe a D-18) e
[D-81](decisoes/D-81-imagem-do-worker-travada-pelo-lock-e-versoes-na-identidade.md) (a imagem do
`worker` travada pelo lock, e as versões na identidade do retrato).

### M3.2 — Contexto

Spec em [`specs/M3.2-contexto.md`](specs/M3.2-contexto.md) e plano em
[`planos/M3.2-contexto.md`](planos/M3.2-contexto.md). Frente `fundamentos`, no ramo
`fundamentos/M3.2-contexto`: onze commits de tarefa, de `98f49db` a `bc7f29c`, mais o de fecho —
T1 a T10 e T12; a T11 não produz. A T8 foi commitada antes da T2 (o `peers.py` é puro e não
depende dos modelos), contra a ordem numérica que o plano pede; nada mais mudou por isso. A PR
de implementação passa também pela `marco1`: escreve no serviço `beat` do `compose.yaml`, em
`tests/risk/test_beat.py`, no comentário das tarefas de `apps/assets`, `apps/risk` e `config`, e
remove um override do `backend/pyproject.toml`.

| Verificação | Resultado |
|---|---|
| Esquemas, a suíte, estilo e migrations (V-01, V-03, V-04) | ✅ 622 testes no `worker`; `test_esquemas` com as vinte e sete; `mypy` estrito limpo em 135 arquivos; `ruff check` e `ruff format --check` limpos; `makemigrations --check` sem mudanças |
| A volta da `0002` (V-02, num banco descartável) | ✅ `migrate fundamentals 0001` e `migrate` com código 0; depois da volta, `bronze.cvm_file` com `[('itr', 1)]` — a linha `ipe` saiu, a `itr` ficou |
| Sem dependência nova (V-05) | ✅ `project.dependencies` iguais às do merge-base: as cinco de sempre |
| **Carga real do IPE, V-06** (2026-09-27, **118 s**) | ✅ código 0; `coleta: 11 arquivos, 11 novos`; **80.900** linhas em `silver.disclosure`, de **339 companhias** — 17.618 fatos relevantes, 50.793 comunicados ao mercado e 12.489 avisos aos acionistas; a Petrobras em 2026-09-19 com "Petrobras informa sobre adesão à nova subvenção econômica" |
| **Segunda coleta e `--reconform 2024`, V-07** | ✅ os 11 `nao modificado`; `ano 2024: 328 companhias, 0 criados, 0 atualizados, 0 removidos, 0 falhos` |
| **Cálculo com os preços do dia, V-08** | ✅ `comparacao: 471 acoes, 17 sem grupo, 0 falhas` e `calculo: 471 acoes, 0 sem balanco, 0 fora de escala, 0 falhas`; 471 `peer_comparison` para 471 indicadores, nenhuma com `asset` ou `calculated_at` diferente do indicador; menor `peer_count` não nulo, 3 |
| A variável do Beat chega ao serviço (V-09) | ✅ `RUVOR_BEAT_DISCLOSURES_CRON='15 21 3 * 2'` no `docker compose config` do `beat` |
| Os tipos do Celery (V-10) | ✅ nenhum override de `celery`; `celery-types` 0.26.0 no `worker`. A imagem **não** foi reconstruída para o V-10: a que roda já tinha o pacote |

622 testes no backend; vinte e sete tabelas; cinco apps; onze tarefas de app mais o `ping`;
quatro entradas no Beat e quatro variáveis `RUVOR_BEAT_*`.

**As 26 mutações da T11 reprovaram, todas com código 1**, e a árvore voltou limpa depois de cada
uma. A primeira linha `FAILED` de cada uma:

| # | Mutação | Reprovou em |
|---|---|---|
| 1 | identidade por (protocolo, versão) | `test_rf04_mesmo_protocolo_e_versao_com_dois_links_sao_duas_linhas` |
| 2, 3 | uma categoria a menos; `"Assembleia"` a mais | `test_rf03_as_tres_categorias_entram_com_o_valor_da_tabela` |
| 4 | título sem o recuo para `Tipo`/`Especie` | `test_rf05_assunto_vazio_recua_para_o_tipo` |
| 5 | truncar em 500 + `…` | `test_rf05_assunto_de_761_vira_500_com_reticencias` |
| 6 | reconformar gravando sempre | `test_rf04_reconformar_igual_nao_cria_nem_atualiza_nem_remove` |
| 7 | não remover o link superado | `test_rf04a_versao_superada_por_reapresentacao_e_removida` |
| 8 | `year_links` pelo zip inteiro | `test_rf04a_link_que_vai_para_categoria_de_fora_e_removido` |
| 9 | remoção pelos links da companhia | `test_rf04a_link_que_passa_da_que_ordena_primeiro_para_a_seguinte` |
| 10 | coleta sem o caminho (b) | `test_rf07b_b_companhia_nova_com_tudo_nao_modificado` |
| 11 | (b) calculado depois de (a) | `test_rf07b_a_e_b_na_mesma_coleta` |
| 12 | link divergente aceito | `test_rf04b_duplicada_com_assunto_diferente_e_conflito_sem_documento` |
| 13, 14 | `_current_versions` sem `kinds`; `ipe` em `KINDS` | `test_rf02b_ipe_na_bronze_nao_chega_aos_indices_do_m31` |
| 15 | sem o recuo para o subsetor | `test_rf11_segmento_de_tres_fica_no_segmento` |
| 16 | grupo pelo nome do segmento | `test_rf11_segmento_de_mesmo_nome_noutro_subsetor_nao_se_mistura` |
| 17 | grupo contando tickers | `test_rf11_companhia_de_dois_tickers_conta_uma_vez_no_tamanho_do_grupo` |
| 18 | percentil com `<=` | `test_rf13_n_impar` |
| 19 | mediana sem a própria ação | `test_rf13_n_par_media_dos_dois_centrais` |
| 20 | `n < 3` sem anular | `test_rf13_n_dois_com_grupo_de_tres_companhias_e_nulo` |
| 21 | grupo dos valores calculados | `test_rf10_acao_que_falhou_na_primeira_fase_fica_fora_do_grupo` |
| 22 | segunda fase numa transação só | `test_rf15_falha_na_comparacao_de_uma_acao_reverte_so_ela` |
| 23 | quarta entrada com `crontab(*campos)` | `test_rf17_horario_de_comunicados_vem_da_variavel_com_campos_nomeados` |
| 24 | sem a linha do `compose.yaml` | V-09: `RUVOR_BEAT_DISCLOSURES_CRON=None` |
| 25 | o override de `celery.*` de volta | V-10: `[{'module': ['celery', 'celery.*'], 'ignore_missing_imports': True}]` |
| 26 | a volta da `0002` sem apagar o `ipe` | V-02: `[('ipe', 1), ('itr', 1)]` depois da volta |

**Revisão final em uma rodada: aprovou**, com 0 graves, 0 médios e 3 leves. Dois viraram
registro aqui: a ordem dos commits e a saída das verificações, que é esta tabela. O terceiro
fica registrado sem correção: uma exceção **fora** do laço por ação da segunda fase — na consulta
das linhas ou no próprio `compare_all` — propaga crua, sem `FundamentalsFailed`, e o relatório
da primeira fase se perde, embora os indicadores fiquem gravados. A spec só cobre a falha por
ação, e hoje o `compare_all` não tem caminho plausível de exceção.

#### Os números da execução real

A carga do IPE do zero (2026-09-27) levou **118 s** para 11 arquivos, ~20 MiB. Memória do
contêiner que rodou a carga: **pico de ~152 MiB**, amostrado a cada 3 s — o IPE é pequeno perto
do ITR e do DFP, cujo pico foi 2,235 GiB. As linhas `ano` cobrem 2016 a 2026, de 242 a 331
companhias e de 4.782 (2016) a 9.806 (2021) comunicados por ano.

**V-08**, a comparação na execução de 2026-09-27: 390 ações no segmento (285 companhias), 64 no
subsetor (42) e 17 sem grupo (**12 companhias, o mesmo número medido no catálogo pela spec**).

| Ativo | Grupo | `roe`: percentil, mediana dos pares, pares |
|---|---|---|
| PETR4 | segmento Petróleo. Gás e Biocombustíveis / Exploração. Refino e Distribuição | 1,0000 · 0,1126 · 7 |
| VALE3 | segmento Materiais Básicos / Mineração / Minerais Metálicos | 0,0000 · 0,0953 · 4 |
| ITUB4 | segmento Financeiro / Intermediários Financeiros / Bancos | 0,8235 · 0,1396 · 18 |

`pe` e `pb` saíram **nulos em todas**: só PETR4, VALE3, ITUB4 e o Ibovespa têm preço, e as três
companhias estão em segmentos diferentes — nenhum grupo chega a 3 valores. É o que a spec previu
("A comparação de `pe` e `pb` sai quase sempre vazia hoje").

**O que a execução contrariou.**

- **80.900, não 80.842.** A spec mediu 80.842 comunicados, e a carga gravou 58 a mais. Não é a
  fonte: a medição contou pares (protocolo, versão) distintos, e a identidade decidida é o link
  ([D-131](decisoes/D-131-documento-do-ipe-se-identifica-pelo-link.md)). A consulta por par sobre
  a `silver` carregada devolve exatamente 80.842, e os 58 são os pares repetidos com links
  diferentes que a própria spec cita. Virou aprendizado.
- **O worktree não é o que o contêiner monta.** A implementação correu num `git worktree`, e o
  `worker` monta o `./backend` do checkout principal: a suíte "no `worker`" rodaria o código
  velho. Tudo foi rodado em contêiner avulso com o worktree montado por cima. Virou aprendizado.

Cinco decisões nasceram do bloco:
[D-130](decisoes/D-130-noticia-e-o-que-a-companhia-divulga-na-cvm.md) (a notícia é o que a
companhia divulga na CVM, não a imprensa),
[D-131](decisoes/D-131-documento-do-ipe-se-identifica-pelo-link.md) (o documento se identifica
pelo link, e a `silver` guarda só a versão corrente),
[D-132](decisoes/D-132-pares-sao-o-segmento-da-b3-pela-tupla.md) (os pares são o segmento da B3,
ou o subsetor, pela tupla; a posição é o percentil),
[D-133](decisoes/D-133-coleta-de-comunicados-diaria-restringe-a-d-127.md) (a coleta de
comunicados é diária, em entrada própria; restringe a D-127) e
[D-134](decisoes/D-134-tarefas-celery-tipadas-por-celery-types.md) (as tarefas Celery são
tipadas por `celery-types`).

**A dívida de tipos do Celery está quitada** (ver "Dívida registrada").

### M2.1a — Identidade e acesso, fase 1

Spec em [`specs/M2.1a-identidade-e-acesso.md`](specs/M2.1a-identidade-e-acesso.md) e plano em
[`planos/M2.1a-identidade-e-acesso.md`](planos/M2.1a-identidade-e-acesso.md). Frente `identidade`,
ramo `identidade/M2.1-identidade-e-acesso`. **Só a fase 1**
([D-107](decisoes/D-107-m2-1a-em-duas-fases-restringe-a-d-82.md)): sem rota HTTP e sem importar
`rest_framework`; a fase 2 espera o M1.6a. Spec: duas revisões adversariais (a 1 reprovou, 1 grave;
a 2 aprovou). Plano: duas (a 1 reprovou, 1 grave; a 2 aprovou). Seis commits de tarefa, T1 a T6, e
um de correção na T5.

| Verificação | Resultado |
|---|---|
| Sessão, middleware, cookies, cache, validadores (V-01, V-02, V-17) | ✅ `public.django_session`; `MIDDLEWARE` na ordem do RF-01; `Secure` segue `RUVOR_SECURE_COOKIES`; cache `RedisCache` em `RUVOR_CACHE_URL` (banco 1) e `LocMemCache` na suíte |
| Migration `0003` com dado real (V-22, dado) | ✅ dois usuários inseridos pelo `psql` em caixa mista, `migrate accounts 0003` sem `pending trigger events`: e-mails minúsculos, superusuário `admin`, o outro `member`; a unicidade de `Lower(email)` virou o índice `user_email_lower_uniq` |
| Serviços da conta, gestão, comando, auditoria (V-05 a V-14, V-16, V-18) | ✅ 99 testes em `tests/accounts/` |
| Concorrência do `last_admin` (V-11) | ✅ duas threads, `transaction=True`: termina com uma `admin` |
| **Execução real (V-24)** | ✅ `createsuperuser --noinput` na `ruvor`; `create_organization` com senha provisória; pelos serviços: troca obrigatória, criação, desativação (a sessão cai), `last_admin`, cadastro com organização pessoal, bloqueio na 6ª tentativa com a senha certa (`wait_seconds` 900; a chave no banco 1 do Redis, o 0 só com o Celery), saída; 14 linhas em `core.access_event`, coluna a coluna como o RF-24 |
| Suíte, tipos, estilo | ✅ **721 testes** no `worker`; `mypy` estrito limpo; `ruff check` e `ruff format --check` limpos; `makemigrations --check` sem mudança |

**As 18 mutações da T7 reprovaram**, cada uma no teste previsto, e o código voltou limpo depois
de cada uma.

**Duas armadilhas novas, em [aprendizados](aprendizados.md):** o `flush` do `transaction=True`
só vê cinco tabelas do `public` — não limpa `core`, `bronze`, `silver` nem `gold`, e o `TRUNCATE`
falha sem `available_apps` —; e o `remove_constraint` do Django passa em silêncio sem remover
índice fora do `public`.

Oito decisões: [D-100](decisoes/D-100-a-api-autentica-por-sessao-do-django-com-csrf.md) a
[D-107](decisoes/D-107-m2-1a-em-duas-fases-restringe-a-d-82.md).

### M4.2 — API pública

Spec em [`specs/M4.2-api-publica.md`](specs/M4.2-api-publica.md) e plano em
[`planos/M4.2-api-publica.md`](planos/M4.2-api-publica.md). Frente `identidade`, ramo
`identidade/M4.2-api-publica`, nascido do da fase 2 do M2.1a. Spec: três revisões adversariais (a
terceira aprovou). Plano: duas (a 1 reprovou, 2 graves; a 2 aprovou). Nove commits de tarefa, T0 a
T8, e o do fecho.

| Verificação | Resultado |
|---|---|
| drf-spectacular 0.30.0 sobre Django 6.1.1 (T0) | ✅ instala, gera e valida; a linha de base tinha 23 avisos e 87 erros, que a T8 zerou |
| O filtro por organização (V-17) | ✅ o gerente levanta sem contexto, o middleware zera no começo e no fim do pedido, o acessor reverso filtra, `ApiKey.unscoped` só em `authentication.py` |
| Criar, listar, revogar (V-02 a V-05, V-12) | ✅ pelos serviços e pela rota; duas criações simultâneas com 9 ativas terminam com 10; desativar e redefinir a senha provisória revogam |
| Autenticação e alcance (V-06 a V-09, V-13) | ✅ as cinco falhas dão o mesmo 401 `invalid_api_key`; a chave lê as rotas `"read"` e recebe 403 `api_key_not_allowed` no resto, inclusive `api-keys`; não passa pelo CSRF |
| A taxa (V-10, V-11) | ✅ as três variáveis — ausentes e vazias valem o padrão; cada linha do RF-08 dá 429 com `Retry-After`; duas chaves e dois IPs contam separado; a suíte inteira verde com a taxa anônima real |
| O esquema (V-14) | ✅ `spectacular --validate --fail-on-warn` limpo; o resolvedor contra o esquema nos dois sentidos, 21 operações; `apiKeyAuth` só nas `"read"`; `default` → `ApiError` em toda operação |
| **Execução real (V-16)** | ✅ pelo proxy do Vite, com `curl`: cadastro, chave criada; a chave leu `/assets`, `/assets/ITUB4/risk` e `/schema` (`application/vnd.oai.openapi+json`) e recebeu 403 no `POST /risk`; revogada, 401. No `psql`: `last_used_at` gravado e `signup`, `api_key_created` e `api_key_revoked` com o IP do contêiner `frontend`. A **61ª** leitura anônima no minuto → 429, `Retry-After: 56`, com o `.env` sem `RUVOR_THROTTLE_ANON` |
| Suíte, tipos, estilo | ✅ **1147 testes** no `worker`; `mypy` estrito limpo em 207 arquivos; `ruff check` e `ruff format --check` limpos |

**As 19 mutações da T9 reprovaram**, cada uma no teste previsto, e o código voltou limpo depois de
cada uma. A 16 — tirar o `cache.clear()` de `tests/conftest.py` — reprovou a suíte inteira com 49
falhas: a taxa anônima real é alcançada pela suíte, e a limpeza é o que a segura. A 19 — importar
`APIView` no topo de `throttling.py` — derruba a partida do pytest com o `ImportError` do import
parcial do DRF, e derrubou também a `web`, que precisou de `restart`.

**Duas armadilhas novas, em [aprendizados](aprendizados.md):** o `--fail-on-warn` reprova enum com
o mesmo nome de campo (`ENUM_NAME_OVERRIDES` resolve), e a contagem de avisos do drf-spectacular
sobrevive entre testes (`GENERATOR_STATS.reset()`).

Cinco decisões: [D-108](decisoes/D-108-a-api-aceita-chave-pessoal-de-leitura.md) a
[D-112](decisoes/D-112-o-filtro-automatico-por-organizacao-nasce-no-m4-2.md).

### M1.6a — Fundação da aplicação

Spec em [`specs/M1.6a-fundacao-da-aplicacao.md`](specs/M1.6a-fundacao-da-aplicacao.md) e plano em
[`planos/M1.6a-fundacao-da-aplicacao.md`](planos/M1.6a-fundacao-da-aplicacao.md). Frente `marco1`,
no ramo `marco1/M1.6-aplicacao-web`: quinze tarefas — T1 a T14 e a T4b, acrescentada no portão da
vitrine —, com commit por tarefa que produz, de `072a944` a `3f907ce`, mais o de fecho; a T13
mediu as mutações e não produz. Duas trilhas andaram em paralelo, o kit (T2 a T4b) e o backend
(T1, T5 a T12). A implementação entra na `main` por PR, mesclada pelo dono da frente
([D-85](decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md)); a PR fica para ele abrir.

| Verificação | Resultado |
|---|---|
| O kit: tokens do claro iguais aos mockups, escala tipográfica, nenhuma cor nem tamanho de fonte literal, contraste nos dois temas e nas duas cópias do escuro, foco visível, `tokens.json` igual ao `tokens.css` (V-01 a V-06) | ✅ na suíte do frontend; o `review-text` escurecido para `#7E652B` (4,63:1) é a única exceção por valor do V-01 |
| **A vitrine aprovada** (V-07) | ✅ pelo dono da frente em 2026-09-28, no estado de `9e2c7fb` — ver "o que a execução contrariou" |
| O formato de erro da D-86, com `DEBUG` ligado e desligado; a permissão declarada em cada view; a `apps/api` sem o motor (V-08 a V-10) | ✅ |
| As rotas de leitura, a busca e a paginação, o `/risk` nos treze estados (V-11 a V-13) | ✅ |
| Um pedido por ativo, o teto estrito, as respostas do `POST`, a expiração e o enfileiramento pelo nome (V-14 a V-18) | ✅ as corridas com threads e barreiras, em `transaction=True` |
| A cadeia por ticker, a abertura com pedido e nunca duas execuções do mesmo ativo (V-19, V-19b, V-19c) | ✅ as quatro corridas abertura × abertura e abertura × fecho |
| Os tipos do Celery (V-19d) | ✅ a dívida veio quitada pelo M3.2; este bloco acrescentou `tests/test_tipos.py`, que reprova o override de volta |
| As métricas na rotina (V-20); nenhum teste sai para a rede (V-22) | ✅ |
| **O proxy (V-21)** | ✅ `/api/v1/assets` respondeu pela porta do `frontend`, pelo proxy do Vite |
| **Execução real (V-23)** | ✅ ver abaixo |

**844 testes no backend**, verdes em duas rodadas seguidas no `worker`, e **345 no frontend**;
`mypy` estrito, `ruff check`, `ruff format --check`, `npm run lint`, `npm run typecheck` e
`npm run build` limpos. **Vinte e oito tabelas** — as vinte e sete do M3.2 mais
`core.compute_request` —; **seis apps**, com a `apps/api`; **treze tarefas de app** mais o `ping`,
com `apps.analytics.tasks.calcular_metricas` e `apps.assets.tasks.calcular_sob_demanda`; **quatro
entradas no Beat**.

**As 46 mutações remedidas na T13 reprovaram** — 23 do backend e 23 do frontend —, e a árvore
ficou limpa ao fim. Uma acusa por um caminho que vale registrar: a
mutação "sem a trava global do `POST`" reprova em três dos quatro casos concorrentes, não nos
quatro — no do pedido vencido, o `UPDATE` do `expire_stale` sobre a mesma linha já serializa as
duas transações, e o teste diz isso.

#### Os números da execução real

Com o Beat parado desde a T1, e `web` e `worker` recriados depois do último commit de código.

**V-21**: o proxy do Vite respondeu `/api/v1/assets` pela porta do `frontend`.

**V-23, as leituras**: os quatro ativos cobertos (ITUB4, PETR4, VALE3, IBOV), **as seis rotas
com 200**. O `/prices` do ITUB4, a série inteira: **349.113 bytes**, 2.494 pregões, em **0,045
s**.

**V-23, o pedido**: `POST` no ITUB4 → **409 `asset_already_covered`**. `POST` no **`BBDC4`**, ativo
do catálogo sem preço até então → **202**, pedido id 1; um segundo `POST` 0,2 s depois devolveu
**o mesmo pedido**. O pedido fechou `done`, motivo `calculado`, em **99,6 s**:

| Etapa | Tempo |
|---|---|
| coleta de preço — 2.490 pregões, de 2016-09-28 a 2026-09-25, e 152 eventos | 2,18 s |
| métricas e abertura do risco | 3,84 s |
| risco — `lstm` 47,5 s, `gru` 44,7 s, `garchnet` 44,0 s, `caviar` 15,2 s; os cinco baratos até 1,9 s cada; os quatro caros treinaram 9 retratos cada | 93,5 s |

A `risk_run` 61 fechou `ok`, com os 18 resultados sem erro. **O `BBDC4` passou a ser coberto para
sempre** ([D-51](decisoes/D-51-cobertura-e-o-que-tem-preco.md)): a rotina diária o recalcula a
partir de agora, como os outros quatro.

**O Beat voltou** depois da execução, com as quatro entradas.

**O que a execução contrariou.**

- **O `flush` do Django não serve aos testes `transaction=True`.** O plano foi aprovado supondo que
  ele esvaziava o banco ao fim de cada teste; a T6 mediu que ele não enxerga as tabelas com
  esquema no `db_table` e, sem `available_apps`, nem roda. O plano foi corrigido antes do código:
  a marca `TRANSACIONAL` e a fixture `banco_limpo`, em `tests/api/migracao.py`, que **todo** teste
  `transaction=True` usa — cinco módulos, não os quatro que o plano nomeava. Virou aprendizado.
- **A zona de Basileia do `BBDC4` saiu `verde` nos 18 resultados**, inclusive o `historical` a 5%
  com 159 violações para 111,85 esperadas. É possível defeito na zona de Basileia do M1.4 para o
  nível de 5%, e **não foi investigado** — está em *Aberto*.
- **O portão da vitrine aprovou com uma ressalva**: "textual demais, faltam ícones". O dono
  comparou três bibliotecas (`docs/mockups/M1.6a/icones-comparativo.html`) e escolheu o Phosphor
  ([D-93](decisoes/D-93-os-icones-do-produto-vem-do-phosphor.md)); a T4b pôs o conjunto fechado
  em `brand/ruvor/icons/` e enxugou a vitrine, que voltou ao portão e foi aprovada.
- **A folha pagou duas vezes por especificidade**: o `:where` que baixou o anel de foco sobre
  fundo escuro para um botão dentro da barra, e o `flex` na regra base que quebrou o texto misto
  sem ícone. E o `decision` do tema escuro subiu de `#D07E8E` para `#D38595` (e o hover para
  `#E0A0AC`), porque como texto ficava abaixo de 4,5:1 em três fundos. Virou aprendizado.
- **Correções do plano, sem mudar contrato**, registradas no fim dele: o banco dos testes
  `transaction=True`; o quinto módulo; "dois pedidos ligados fecham juntos" com ativos distintos,
  por causa do índice parcial; o vencido do V-15; a anotação do `CELERY_BEAT_SCHEDULE`, que o M3.2
  tornou desnecessária; os motivos de falha da cadeia, que a T11 definiu e a T12 moveu; o
  `/prices` com intervalo sem conferir as chaves (`d5c8224`); o `flex` só com ícone; a montagem de
  `docs/mockups` no `frontend`; as três classes de arranjo acrescentadas; o `decision` escuro; o
  anel da barra; e a T4b.

Sete decisões nasceram do bloco — as seis da spec, na ordem dela, e a do portão:
[D-87](decisoes/D-87-os-mockups-sao-a-referencia-visual-do-kit.md) (os mockups são a referência
visual, e o texto das tags é escurecido o mínimo para 4,5:1),
[D-88](decisoes/D-88-o-kit-tem-dois-temas-pelos-mesmos-tokens.md) (dois temas, pelos mesmos
tokens de cor),
[D-89](decisoes/D-89-a-web-enfileira-pelo-nome-da-tarefa.md) (a `web` enfileira pelo nome da
tarefa, e os nomes são contrato interno),
[D-90](decisoes/D-90-calculo-sob-demanda-so-para-ativo-nunca-calculado.md) (cálculo sob demanda
só para ativo nunca calculado, um pedido aberto por ativo, teto e expiração),
[D-91](decisoes/D-91-a-rotina-diaria-e-precos-metricas-risco-estende-a-d-69.md) (a rotina diária
é `preços → métricas → risco`; estende a D-69),
[D-92](decisoes/D-92-nunca-duas-execucoes-do-mesmo-ativo-ao-mesmo-tempo.md) (nunca duas
execuções do mesmo ativo ao mesmo tempo) e
[D-93](decisoes/D-93-os-icones-do-produto-vem-do-phosphor.md) (os ícones vêm do Phosphor, num
conjunto fechado dentro do kit).

### M1.6b — As telas

Spec em [`specs/M1.6b-as-telas.md`](specs/M1.6b-as-telas.md) e plano em
[`planos/M1.6b-as-telas.md`](planos/M1.6b-as-telas.md). Frente `marco1`, ramo `marco1/M1.6b-as-telas`.
Treze tarefas, um commit cada que produz, de `aefddd8` a `236985c`; spec e plano com duas rodadas de
revisão adversarial cada, e três portões de mockup aprovados pelo dono em 2026-09-28
(`docs/mockups/M1.6b/busca.html`, `ativo.html`, `ativo-estados.html`). Cinco decisões:
[D-94](decisoes/D-94-os-graficos-sao-do-uplot.md) a
[D-98](decisoes/D-98-o-horizonte-do-marco-1-e-1-dia-restringe-a-d-05.md).

| Verificação | Resultado |
|---|---|
| Mockups aprovados antes do código (V-01) | ✅ os três, nos dois temas, com os textos de cada número |
| Suítes | ✅ **731 no frontend** (eram 345) e **947 no backend** (os 943 mais os 4 do contrato dos motivos); lint, tipos e build limpos |
| Mutações | ✅ **as 28 da T12 reprovaram**, e a revisão final aplicou mais 16, que também reprovaram |
| Texto só dos mockups | ✅ `frontend/src/content/textos.ts` conferido contra os dois mockups por teste (2.000 argumentos por função); nenhum texto literal em `.tsx`, pela árvore sintática |
| Sem recomendação (D-65) | ✅ varredura do vocabulário nas duas formas; a tabela em ordem fixa; sem zona de Basileia |
| Execução real (V-18) | ✅ o roteiro `frontend/e2e/capturas.mjs`, na imagem do Playwright 1.63.0 e na rede do contêiner `frontend`, saiu com 0: 114 conferências, 21 capturas, nenhuma rolagem horizontal, o tema pela chave e pelo sistema |
| Cálculo sob demanda pela tela | ✅ o `AALR3`, sem preço, foi de E8 a E5 em 150 ms e a **E1 em 100,8 s** — coleta, métricas e risco —, em linha com os 99,6 s do M1.6a |
| A medida do RF-24 (V-19) | ✅ a segunda carga do `ITUB4` ficou pronta em **312 ms** (a primeira, que aquece o Vite, em 415 ms); as rotas do ativo em 33 a 132 ms, o `/prices` com **349.253 B** sem compressão; a busca em ~15 ms aquecida (56 ms a frio). **Sem cache neste bloco**: a decisão fica com a hospedagem |
| API e backend intocados | ✅ `git diff main -- backend/` mostra só `backend/tests/api/test_motivos.py` |

**O que a execução mostrou:**

- **O primeiro tique do Beat num dia útil** (2026-09-28, 19h30) rodou a rotina inteira — preços →
  métricas → risco — nos cinco ativos então cobertos, com os modelos caros reaproveitando os 9
  retratos e treinando 0 (`9/0` no log do `worker`), em 1 a 3 s por modelo. **A taxa de invalidação
  medida num dia útil foi zero**; a estimativa do V-13 do M1.5b (proventos invalidam a linhagem) segue
  sem medida, porque nenhum dos cinco pagou provento no dia.
- **As métricas do ITUB4 estavam em 18/09 e o risco em 25/09** antes do tique: o atraso vinha só do
  Beat parado durante o M1.6a, e o tique de 28/09 alinhou as duas.
- **O `AALR3` saiu com os nove modelos "não adequado" nos dois níveis**, e a faixa entre eles é larga
  (2,9% a 8,5% a 95%, 4,5% a 13,1% a 99%): é o caso "nenhum adequado" da D-65, e a tela o diz como
  informação.
- **A medida é de desenvolvimento**: o `main.tsx` usa `StrictMode`, e o Vite em desenvolvimento pede
  cada rota duas vezes por carga.
- **O Vite recusa outro `Host`** (403 para `frontend:5173`): a execução real entra na rede do próprio
  contêiner, por `--network container:…`, e usa `localhost`.
- **Os três mockups aprovados divergiam entre si** em quatro pontos; a T5 os unificou no kit, e as
  decisões estão no plano (T5, "Correções registradas na execução").

### M1.6c — Fundamentos e contexto na tela

Spec em [`specs/M1.6c-fundamentos-e-contexto.md`](specs/M1.6c-fundamentos-e-contexto.md) e plano em
[`planos/M1.6c-fundamentos-e-contexto.md`](planos/M1.6c-fundamentos-e-contexto.md). Frente `marco1`, ramo
`marco1/M1.6c-fundamentos-e-contexto`. Nove tarefas, de `f6f21d0` a `f00f3d2`, mais a correção da revisão final;
spec com duas rodadas de revisão, plano com uma, o mockup aprovado no portão em 2026-09-29. Uma decisão:
[D-99](decisoes/D-99-as-camadas-4-e-5-depois-do-risco-e-as-tabelas-da-fundamentos-sao-contrato.md).

| Verificação | Resultado |
|---|---|
| As rotas | ✅ `/fundamentals` (o último indicador com a comparação **do próprio cálculo**) e `/disclosures` (paginada, com filtro, pela ligação direta por `code_cvm`), no molde da D-86, com a chave de leitura do M4.2 e o esquema OpenAPI sem aviso |
| O contrato com a `fundamentos` | ✅ as tabelas lidas em [FRENTES.md](FRENTES.md#contratos-entre-frentes); `test_valores_fundamentos.py` lê as listas de motivo **da fonte** — `REASON_NULLS` inteiro e os retornos de `market_cap()` por `ast` — e reprova motivo novo |
| Suítes | ✅ **1215 no backend** (a suíte rodou desanexada no `worker`, com o Beat parado) e **1092 no frontend** |
| Mutações | ✅ todas as das T1 a T6 reprovaram, cada uma revertida |
| Texto só do mockup | ✅ as 112 chaves `fundamentos.*` e `comunicados.*` conferidas contra o mockup; nenhuma forma de "notícia" |
| Execução real | ✅ 245 conferências sem falha (depois da correção da revisão final) em ITUB4 (banco: os nulos do plano de contas), IBOV (as frases de índice) e PETR4 (a posição entre os pares em quatro indicadores); a tela do ITUB4 pronta em **369 ms** |
| **A taxa do anônimo** | com a taxa padrão (60/min), **5 cargas completas da tela do ativo e 84 pedidos até o primeiro 429** — em desenvolvimento, 14 pedidos por carga pelo `StrictMode` |

**O que a execução mostrou:**

- **O banco real não tem vários dos casos da spec** (medido na T0): P/L e P/VP **nunca** têm comparação com pares — só
  quatro ações têm esses múltiplos, e nenhum grupo chega a três —; P/L negativo não ocorre (os 86 LPA negativos têm o
  P/L nulo); não há ação com comunicados sem `silver.company`, ação sem `code_cvm` nem indicador sem comparação. Esses
  ramos só os testes provam.
- **A taxa aceitou 81 pedidos com o limite em 60 por minuto** antes de recusar. A hipótese — o `SimpleRateThrottle` do
  DRF conta sem atomicidade quando o `runserver` atende em paralelo — **não foi provada**, e parte da diferença pode vir
  dos pedidos que o `StrictMode` aborta. É da `identidade` e da hospedagem.
- **O Docker travou e voltou** durante o bloco: depois de uma falta de memória, o motor parou de responder com os
  contêineres ainda servindo; foi reiniciado pelo shell elevado, com o banco intacto (memória da máquina).

### M2.1m — A coluna do autor do pedido

Spec em [`specs/M2.1m-requested-by.md`](specs/M2.1m-requested-by.md) e plano em
[`planos/M2.1m-requested-by.md`](planos/M2.1m-requested-by.md). Frente `marco1`, ramo `marco1/M2.1m-requested-by`. Uma
tarefa de código, `4825389`, e o FECHA; spec com duas rodadas de revisão, plano com uma. Nenhuma decisão nova.

| Verificação | Resultado |
|---|---|
| A coluna | ✅ `core.compute_request.requested_by_id`, `bigint`, anulável, FK para `core.user` com `PROTECT` — o literal do contrato do plano do M2.1a |
| A migration | ✅ `api.0002`, só um `AddField`, pelo `makemigrations` e `ruff format`; `makemigrations --check` limpo; aplicada no banco de dev |
| A API não muda | ✅ `test_risco.py` (o `CHAVES_PEDIDO`) e `test_esquema_openapi.py` verdes sem mudança |
| Suíte | ✅ **1218 no backend** (1215 + 3), em 11 min 34 s, com o Beat parado; `mypy`, `ruff check` e `ruff format --check` limpos |
| Mutações | ✅ as três reprovaram: sem o `null=True` no modelo e na migration, o V-01 e o V-02; `CASCADE`, o V-02; o autor no serializador, 6 testes de `test_risco.py` |

**Nenhum código preenche a coluna**: isso é a T14 do M2.1a, da `identidade`, agora livre para começar. A dívida da
`risk_run` sempre nula segue aberta até ela. *(Paga pela T14, em 2026-09-30: ver o fecho do M2.1a abaixo.)*

### M1.6d — Acabamento

Spec em [`specs/M1.6d-acabamento.md`](specs/M1.6d-acabamento.md) e plano em
[`planos/M1.6d-acabamento.md`](planos/M1.6d-acabamento.md). Frente `marco1`, ramo `marco1/M1.6d-acabamento`. Quatro
tarefas de código — `218e26a`, `90638cb`, `6c98a15`, `d999e94` —, a T5 (mutações e suítes, sem arquivo) e o FECHA.
Nenhuma decisão nova. Paga quatro dívidas: três aqui e a do roteiro, já paga no M1.6c.

| Verificação | Resultado |
|---|---|
| A região viva do risco | ✅ uma `ruvor-sr-only`, sempre montada, só com o andamento (E2 e E3 recalculando, E4, E5 na fila e `running`); vazia no E1; o embrulho do corpo sem `aria-live` |
| Fundamentos e Comunicados | ✅ nenhum `aria-live` na seção; o carregando e a contagem seguem `role="status"` |
| O Biome | ✅ `"preset": "recommended"`; o lint sai 0 sem `DEPRECATED`; o teste reprova o campo antigo |
| A guarda de dependência | ✅ `tests/test_dependencias.py`, só biblioteca padrão; reprova `numpy>=2` e `Pandas[performance]` |
| Suítes | ✅ **1099 no frontend** e **1299 no backend** (com os testes do M4.1), em 10 min 2 s, com o Beat parado; lint, typecheck, build e `mypy` limpos |
| Mutações | ✅ as sete da spec reprovaram duas vezes — na tarefa dona e de novo na T5, sobre o código final |

**O que a execução mostrou:** a região viva repete o texto do andamento que o painel visível mostra, e seis buscas
antigas por texto em `risco.test.tsx` passaram a achar dois elementos. Elas agora exigem **exatamente um** fora de
`[aria-live]` (o ajudante `inBody`), e o V-01 confere à parte o texto exato da região — ver
[aprendizados](aprendizados.md). O Docker parou no meio do bloco, e a porta
publicada do PostgreSQL caiu numa faixa reservada pelo Windows: o `.env` local passou a `56432`.

### M1.5c — Execução presa

Spec em [`specs/M1.5c-execucao-presa.md`](specs/M1.5c-execucao-presa.md) e plano em
[`planos/M1.5c-execucao-presa.md`](planos/M1.5c-execucao-presa.md). Frente `marco1`, ramo `marco1/M1.5c-execucao-presa`.
Oito tarefas de código, de `15df430` a `f0ae2d2`, a T9 (mutações, sem arquivo) e a T10 (execução real e FECHA). Duas
decisões, aceitas com a spec: [D-149](decisoes/D-149-a-execucao-presa-e-fechada-pela-regra-do-fecho.md) e
[D-150](decisoes/D-150-o-fecho-so-escreve-sobre-execucao-em-running.md).

**O que passou a existir:** a `risk_run` `running` há mais de `RUVOR_RISK_STALE_AFTER_MIN` (360 por padrão, nunca menos
que o prazo do pedido sob demanda) é fechada **pela regra do fecho** — `ok`, `partial` ou `failed` pelo que foi gravado
—, junto com os pedidos ligados, por `apps/risk/stale.py`; a varredura é o **primeiro elo da `rotina_diaria`**
(`fechar_presas`, que nunca levanta) e o comando `manage.py close_stale_runs [--dry-run] [--older-than-min N]`. O
`close_run` só escreve sobre execução `running`; a tarefa por modelo grava sob a trava do ativo e só em execução aberta,
e descarta o que chega depois do fecho; a abertura que não consegue enfileirar fecha a própria execução `failed`.

| Verificação | Resultado |
|---|---|
| Suíte | ✅ **1330 no backend**, em 11 min 47 s, com o Beat parado; `mypy` e `ruff` limpos — e, depois de receber a `main` com a T14 do M2.1a e o M4.1, **1397** (1366 + 31), em 11 min 52 s, com os três testes de concorrência verdes de novo |
| Concorrência | ✅ as três corridas novas (a varredura × o fecho, × a tarefa por modelo, e a abertura sem broker) verdes em três rodadas seguidas |
| Mutações | ✅ as onze da tabela da T9 reprovaram |
| O leque sem treino do ITUB4 | ✅ **7,9 s** e **8,5 s**, contra 8,66 s e 10,27 s no M1.5b: a trava nova não pesou |
| A presa | o `--full` do ITUB4 (execução 75) derrubado por `kill worker` **6,8 s depois de a execução nascer** (00:46:20,7 → 00:46:27,4 UTC), com **10 de 18** resultados — os cinco modelos baratos; `lstm`, `gru`, `garchnet` e `caviar` sem gravar |
| A varredura | `--dry-run`: `10/18 fecharia partial`; a tarefa `fechar_presas`, chamada no `worker`, fechou-a **`partial`**, com as linhas `presas:` no log; o `/risk` a mostrou como `latest`, `partial` |
| O descarte | as reservadas voltaram **1 h depois** de entregues (o `visibility_timeout` do Redis): `lstm` e `gru` treinaram (51 s e 71 s) e **descartaram** — `execucao 75 fechada: modelo lstm descartado`; a contagem ficou em 10. As de `garchnet` e `caviar`, em execução no `kill`, já estavam confirmadas e se perderam |
| A rotina real | ao voltar, o Beat disparou a `rotina_diaria` atrasada: o primeiro elo foi o `fechar_presas` (`nenhuma execução presa`), depois preços e métricas |

**O que a execução mostrou:** sem `acks_late`, a tarefa que está rodando quando o `worker` morre se perde, e as
reservadas só voltam depois do `visibility_timeout` — a execução nunca fecharia sozinha, e é a varredura que a fecha.
Ver [aprendizados](aprendizados.md).

### M4.1 — Relatórios

Spec em [`specs/M4.1-relatorios.md`](specs/M4.1-relatorios.md) e plano em
[`planos/M4.1-relatorios.md`](planos/M4.1-relatorios.md). Frente `identidade`, ramo
`identidade/M4.1-relatorios`. Spec: duas revisões adversariais (a 1 reprovou, 1 grave; a 2 aprovou).
Plano: duas (a 1 reprovou, 2 graves; a 2 aprovou). Cinco commits de tarefa — T0 a T3 (`038273b`,
`f58b9c6`, `e62ac7e`, `bc72bd9`), já na `main` pela PR #25, e a T4 (`4971b89`) —, a errata da T5
(`11fc3fa`) e o do fecho. **Fechou em 2026-09-30** e entrou na `main` pela PR #28.

| Verificação | Resultado |
|---|---|
| `core.report` (T1) | ✅ imutável no Django (o `save` de linha existente e o `delete` levantam, e os dois gerentes recusam `update` e `delete` em massa) e no banco, pelo gatilho `report_so_cresce`, que deixa o `TRUNCATE` passar; `PROTECT` para `gold.risk_run` e `silver.asset`; filtrada por organização |
| O conteúdo, os bytes e o CSV (T2) | ✅ o JSON com o manifesto, os 18 resultados e o resumo por nível, em bytes canônicos, com o SHA-256 deles; o CSV derivado do JSON guardado |
| Os serviços e as rotas (T3, T4) | ✅ gerar pela sessão em `POST /api/v1/reports`; listar, ler e baixar `/json` (os bytes guardados, sem passar pelo renderizador do DRF) e `/csv` pela sessão ou pela chave; o esquema limpo no `--fail-on-warn` |
| **Execução real (V-18)** | ✅ pelo proxy do Vite, com `curl` e cookie, com usuário criado pelo `auth/signup`: `POST reports` do `ITUB4` → 201, `risk_run_id` 5, `as_of_date` 2026-09-29; o `sha256sum` do `/json` igual ao `sha256` do relatório (`6c991b3e…0a085`); o `/csv` com 19 linhas e 15 colunas; a chave lista e baixa, e recebe 403 `api_key_not_allowed` no `POST`; anônimo, 401. No `psql`, `UPDATE core.report SET size_bytes = 0` → `ERROR: report so cresce` |
| O tamanho do relatório | **10 077 bytes** de `content` no `ITUB4` — a spec estimava "dezenas de KB" |
| Suíte, tipos, estilo | ✅ **1361 testes** no `worker`, em 21 min 3 s, num contêiner avulso com banco de teste próprio (`RUVOR_DB_NAME=ruvor_m41`), ao lado do `worker` da sessão do M2.1; `mypy` estrito limpo em 221 arquivos; `ruff check` e `ruff format --check` limpos (222 arquivos) |
| Mutações (T5) | ✅ as 19 reprovaram, cada uma no teste previsto. A 17 — `ReportOut.kind` como `ChoiceField` — foi **retirada por errata do dono**: o gerador não avisa, e o `CharField` fica pelo motivo certo, corrigido na spec |

**O relatório é lido sem registro de leitura.** A [D-104](decisoes/D-104-auditoria-de-acesso-em-core-access-event-restringe-a-d-41.md)
previa que o dado privado nascesse no M2.2 com registro de leitura; o relatório é o primeiro dado
privado e nasceu antes, sem esse registro, como a spec declara em *Riscos* e a
[D-115](decisoes/D-115-a-chave-de-leitura-le-o-relatorio-da-organizacao-estende-a-d-108.md) anota.

**Seis armadilhas novas, em [aprendizados](aprendizados.md):** o `operationId` de lista e item que
colide; o `JSONRenderer` que devolve os mesmos bytes, salvo o U+2028; o editor que converte o escape
do U+2028 no caractere; o `TRUNCATE` com `pending trigger events`; a data em `-03:00` contra `Z`; e o
banco de teste próprio pelo `RUVOR_DB_NAME`, para duas suítes ao mesmo tempo.

Três decisões: [D-113](decisoes/D-113-o-relatorio-e-uma-foto-guardada-com-sha-256.md) a
[D-115](decisoes/D-115-a-chave-de-leitura-le-o-relatorio-da-organizacao-estende-a-d-108.md).

### M2.1a — Identidade e acesso, fase 2 e fecho

Mesma spec e mesmo plano da fase 1, na seção *Fase 2 — as rotas*. Frente `identidade`, ramo
`identidade/M2.1-identidade-e-acesso`. As T9 a T13 entraram na `main` pela PR #13 (2026-09-28): o
tratador com 401, 400 e 429 e os cabeçalhos, a sessão com CSRF na API, `AccountReady`, o limite
`auth` por IP, e as rotas `auth/*` e `organization/users*`. A T14 esperou a coluna da `marco1` (M2.1m,
PR #18) e entrou em 2026-09-30 (`affc70c`). A T15 (mutações) não tem commit, e a T16 é este fecho.

| Verificação | Resultado |
|---|---|
| O autor do pedido (V-19, T14) | ✅ `tests/accounts/test_requested_by.py`, 5 casos: o `POST /risk` logado grava o usuário no pedido novo, e a abertura grava o mesmo na `risk_run`; o anônimo grava nulo nos dois; o segundo usuário com pedido aberto recebe 202, e o pedido continua do primeiro; a execução já em andamento continua de quem chegou primeiro; a abertura sem pedido (a rotina) grava nulo |
| **Execução real (V-25)** | ✅ pelo proxy do Vite, com `curl` e o `X-CSRFToken` lido do arquivo de cookies a cada escrita: `csrf` 204 → `signup` 201 (organização pessoal, `admin`) → `me` 200 → `logout` 204 → `me` 401 `not_authenticated` → `login` 200 → `password` 204. `create_organization` pelo comando; a `admin` nova entra com a senha provisória, recebe 403 `password_change_required` em `organization/users`, troca a senha e então cria (201), lista (200, dois usuários) e desativa (200). No `psql`, 9 linhas em `core.access_event`: `signup`, `logout`, `login`, `password_changed`, `user_created` (`{"via": "create_organization"}`, sem IP), `login`, `password_changed`, `user_created` e `user_updated` (`is_active` de `true` para `false`), todas com o IP do contêiner `frontend` menos a do comando |
| **Execução real do autor (T16)** | ✅ `POST /risk` logado do `ABCB4`, nunca calculado, com o `worker` reiniciado: o pedido 2 e a `risk_run` 10 com `requested_by_id` 12, o usuário do V-25. **A primeira tentativa, com o `ABEV3`, abriu a `risk_run` 9 com autor nulo**: o pedido tinha o autor, porque a `web` recarrega, mas o `worker` estava de pé desde antes do commit e rodava o código antigo. A execução 9 fechou `ok`, sem autor, e fica assim: é o registro do que o código antigo gravou |
| Suíte, tipos, estilo | ✅ **1304 testes** no `worker` (1299 + 5), em 17 min 19 s, antes de a `main` trazer o M4.1 — depois do merge dela, **1366** (os 1361 do M4.1 e os 5), com o Beat e o `frontend` parados; `mypy` estrito limpo em 221 arquivos; `ruff check` e `ruff format --check` limpos; `makemigrations --check` sem mudança; `spectacular --validate --fail-on-warn` limpo |

**As dezesseis mutações da T15 reprovaram**: as quinze que não dependiam da T14 (19 a 31, com a
29b) na fase 2, e a 32 (`_decide` sem gravar o usuário, 3 testes) e a 33 (a abertura sem repassar o
autor, 2 testes) agora. O código voltou limpo depois de cada uma.

**A ordem com a `marco1`:** a T14 entrou **antes** do M2.1b, que só tem spec e plano na `main` — o
`POST /risk` segue `AllowAny`. O caso anônimo existe, e quando a
[D-140](decisoes/D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md) entrar, o teste dele passa a
esperar 401, ajustado pela `identidade`. **Desvio do contrato do plano:** a view usa
`isinstance(request.user, User)` no lugar do `is_authenticated`. O resultado é o mesmo, e o `mypy`
recusa `AbstractBaseUser` na FK.

**Uma armadilha nova, em [aprendizados](aprendizados.md):** o `worker` roda o código de quando subiu,
mesmo com o arquivo novo montado; o `--max-tasks-per-child` não resolve, porque o filho nasce por
`fork` do pai antigo.

Nenhuma decisão nova: as oito, [D-100](decisoes/D-100-a-api-autentica-por-sessao-do-django-com-csrf.md) a
[D-107](decisoes/D-107-m2-1a-em-duas-fases-restringe-a-d-82.md), vieram com a spec.

### M1.7 — Busca e catálogo

Spec em [`specs/M1.7-busca-e-catalogo.md`](specs/M1.7-busca-e-catalogo.md) e plano em
[`planos/M1.7-busca-e-catalogo.md`](planos/M1.7-busca-e-catalogo.md). Frente `marco1`, ramo
`marco1/M1.7-busca-e-catalogo`, implementado num worktree. Nove tarefas, de `1713174` (T0) a `ea0f35c` (T8), a partir da `main`
em `804cda4`, que não avançou durante o bloco; o mockup `docs/mockups/M1.7/busca-sugestao.html` aprovado pelo dono no portão da T4, em
2026-10-02, depois da revisão. Duas decisões, aceitas com a spec:
[D-143](decisoes/D-143-a-busca-ignora-acento-pelo-unaccent.md) e
[D-144](decisoes/D-144-a-classificacao-da-b3-se-corrige-na-saida-da-api-estende-a-d-47.md); a D-145 fica sem uso. Paga
as três dívidas que o M1.6b registrou: a busca com acento, a classificação com ponto e a sugestão fixa. **Fechou em 2026-10-02** e entrou na `main` pela PR #32, no mesmo dia.

**O que passou a existir:** a extensão `unaccent` (`apps/assets/migrations/0004_unaccent.py`, com
`django.contrib.postgres` em `INSTALLED_APPS`) e o `q` da busca sem diferença de caixa nem de acento no nome e no nome de
pregão; `has_risk` no item da busca — a execução fechada mais recente `ok` ou `partial`, a regra que a tela usa — e o
filtro `has_risk=true|false`, comparado como texto (`True`, `1` e o vazio dão 400); a tabela fechada de
`apps/assets/classification.py`, aplicada na saída da API em `sector`, `subsector`, `segment` e nos `group_*` dos pares,
com o `silver` e o `gold.peer_comparison` intactos, e a quinta linha do relatório do `import_assets`
(`classificacao com ponto fora da tabela: N`); no frontend, a sugestão pedida pela caixa de busca **de página** — a `/`
e a tela "ativo não encontrado" — uma vez por montagem, com carregando, erro, nenhum, a lista e o "e mais N";
`sugestoes.ts` saiu, e o `MIN_SESSIONS` foi para `frontend/src/risk/config.ts`.

| Verificação | Resultado |
|---|---|
| Suítes | ✅ **1456 no backend** (eram 1397), em 12 min 24 s, num contêiner avulso do `worker` com o worktree montado e o Beat parado; **1110 no frontend** (eram 1099); `mypy` estrito limpo em 232 arquivos, `ruff check` e `ruff format --check` limpos, `makemigrations --check` sem mudança, `spectacular --validate --fail-on-warn` limpo; lint, typecheck e build do frontend limpos |
| Mutações (T7) | ✅ as 20 reprovaram sobre o código final, cada uma revertida — as das T1, T2, T3 e T6, e as extras registradas no plano |
| **Execução real (V-12)** | ✅ o roteiro `frontend/e2e/capturas.mjs`, na imagem do Playwright 1.63.0 e na rede do contêiner `frontend`, com `RUVOR_E2E_SOB_DEMANDA=0` e `RUVOR_E2E_EMPRESA=PETR4`: **258 conferências, 0 falhas**, 20 capturas, nenhum erro de página |
| A sugestão pela API | ✅ os atalhos lidos da `/` renderizada — `AALR3`, `BBDC4`, `IBOV`, `ITUB4`, `PETR4`, `VALE3` — iguais, na mesma ordem, à primeira página de `has_risk=true&limit=8` (`count` 6); sem "e mais N", porque o `count` não passa de 8 (o caso com `count` 11 só os testes provam); cada um com `latest` `ok` no `/risk` |
| Acento e classificação | ✅ "itaú" lista o `ITUB4` na página de busca; a tela do `PETR4` mostra "Petróleo, Gás e Biocombustíveis" e "Exploração, Refino e Distribuição", sem ponto |
| O mockup | ✅ a `/` e o `/ativos/XPTO3` servidos pelo `frontend`, nos dois temas, em 1440 e 360 px, iguais ao estado "lista (count 6)" do mockup aprovado — os mesmos textos, atalhos e disposição, sem rolagem horizontal. Carregando, erro e nenhum só pelos testes unitários: o banco real não os produz sem mexer no stack |
| A taxa (RF-13) | a medida da taxa do roteiro (`measureRate`) carrega só `/ativos/ITUB4`: **não inclui a página inicial**, e não conta o pedido novo da sugestão; não rodou nesta execução (`RUVOR_THROTTLE_ANON` alto no `.env` local, como no M1.6c) |

**O que a execução mostrou:** o banco real tem seis ativos com risco, todos com a fechada mais recente `ok`; o
"e mais N", o `failed` mais novo que um `ok` e a `running` mais nova que a fechada só aparecem nas fixtures. Duas
armadilhas novas em [aprendizados](aprendizados.md): o filtro por campo de `annotate` atrás de `QuerySet[Asset]`, que
o `mypy` recusa, e o efeito de montagem que corre depois de o título aparecer.

### M2.3 — Camada explicativa

Spec em [`specs/M2.3-camada-explicativa.md`](specs/M2.3-camada-explicativa.md) e plano em
[`planos/M2.3-camada-explicativa.md`](planos/M2.3-camada-explicativa.md). Frente `marco1`, ramo
`marco1/M2.3-camada-explicativa`. Dezesseis tarefas: as quatro conferências técnicas (T2, T5, T8, T11), os quatro
mockups (T3, T6, T9, T12), cada um com revisão e portão, aprovados pelo dono em 2026-10-02; o código em `18d4d4b` (T1),
`b7b5ac8` (T4), `ff43fbd` (T7), `077da3a` (T10), `d317be3` (T13) e `b5c13e9` (o roteiro, T15); a T0 e a T14 sem
arquivo de código. Três decisões, com a spec: [D-151](decisoes/D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md)
(o texto mora no frontend), [D-152](decisoes/D-152-o-nivel-de-leitura-e-escolha-do-visitante.md) (o nível é do
visitante, global, padrão iniciante) e [D-153](decisoes/D-153-o-parecer-da-cvm-nao-bloqueia-o-m2-3.md) (o parecer da
CVM não bloqueia o bloco). A D-154 ficou sem uso.

**O que passou a existir:** `frontend/src/reading.ts` (`getReading`, `setReading`, `onReadingChange`, `useReading`,
`textFor`), lido de forma síncrona no primeiro desenho; o `ReadingSwitch` no casco, ao lado do tema; `TEXTOS_AVANCADOS`
em `frontend/src/content/avancado.ts`, com a mesma chave e a mesma assinatura da iniciante para cada uma das 55 chaves,
e a `risco.tabela.intro` avançada em `BLOCOS_AVANCADOS`, fora das 55; o `Collapsible` (e `.ruvor-collapsible` no kit)
para a assimetria e a curtose, a tabela dos nove e a trilha, e as linhas de teste da tabela abertas pelo nível; as
marcas `data-reading`, `data-collapsible` e `data-open` para a execução real.

**Três iniciantes emendadas, por exceção ao "Fora" da spec, aprovadas pelo dono nos portões:**

- `comportamento.return_ytd` (portão da T6): dizia "Desde o primeiro pregão do ano", e o cálculo parte do fechamento do
  último pregão do ano anterior — passa a "Desde o fechamento do último pregão do ano passado, com os proventos: R$ 100
  viraram ${x}.";
- `fundamentos.pares.abaixoDeTodas` (portão da T12): "abaixo de todas" era falso com empate no menor valor — passa a
  "Nenhuma das outras ${outras} companhias do grupo com este indicador calculado tem número menor.";
- a D-64 pela **expressão única** "não do número de hoje" (portão da T9, a alternativa da conferência), em
  `risco.veredito` e nos ramos `k ≥ 1` e `k = 0` de `risco.naoRejeitados`, nas duas leituras — muda as três iniciantes,
  como o RF-08 previa.

| Verificação | Resultado |
|---|---|
| A lista fechada (V-02) | ✅ `LEITURA_KEYS` igual às 55 do RF-04, cada uma nas duas entradas com a mesma aridade; `PENDENTES` apagada na T13 |
| O alternador (V-03) | ✅ o primeiro desenho já sai no nível lembrado (`renderToString`); valor desconhecido e armazenamento que lança dão iniciante |
| As frases, o recolhimento, a D-64, o vocabulário (V-04 a V-07) | ✅ por seção, nos dois níveis; nenhum recolhível dentro de `aria-live`; a expressão da D-64 em cada ramo exigido; `avancado.ts` na varredura, e a regra `pior` dos Fundamentos também na avançada |
| Suíte, lint, tipos, build (V-09, V-11) | ✅ **1206 testes no frontend** (29 arquivos), contra a linha de base de 1099 — **1217** depois de receber a `main` com o M1.7, que trouxe 11; `npm run lint`, `typecheck` e `build` limpos; `backend/` e `engine/` sem diferença da `main` |
| Mutações (T14) | ✅ as 39 das T1, T4, T7, T10 e T13 reprovaram sobre o código final, cada uma revertida |
| **Execução real (V-10)** | ✅ **631 conferências, 0 falhas**, 52 capturas, com o Beat parado e a taxa do anônimo subida. O ITUB4 (execução 85) e o PETR4 (86) conferidos em E1 pela API antes do navegador. Nos dois ativos, nos dois níveis, nos dois temas, em 360 e 1440 px (16 combinações): `data-reading` certo; na iniciante, `moments`, `models` e `trail` em `data-open="false"`, a tabela fora da árvore, e, aberta pelo botão, as nove `tests` em `false`; na avançada, tudo em `true`; **zero pedido** `/api/v1/` nos 2 s depois de cada troca pelo alternador (16 de 16); em 360 px, o casco sem rolagem horizontal; nenhum erro de página. A segunda carga do ITUB4 em **389 ms** |

**O que a execução mostrou:** nada que os testes não tivessem pego — a execução real saiu verde na primeira rodada.
O que custou tempo foi antes dela, nos testes e nos mockups: o `getByText` que não acha frase com "R$ "; as iniciantes
que devolviam união de literais e travavam o `Leitura<T>`; e os mockups que continuam mostrando as frases anteriores às
emendas (o `comportamento.html` e o `fundamentos.html`, e a vista `itub4` do `risco.html`) — ver
[aprendizados](aprendizados.md) e o [índice dos mockups](mockups/README.md).

### M2.2a — Carteira

Spec em [`specs/M2.2a-carteira.md`](specs/M2.2a-carteira.md) e plano em
[`planos/M2.2a-carteira.md`](planos/M2.2a-carteira.md), aprovados e na `main` pela PR #31. Frente
`identidade`, ramo `identidade/M2.2-carteira`, no worktree `.claude/worktrees/identidade+M2.2-carteira`.
Spec: três revisões (a 2 reprovou por um grave, o `FOR UPDATE OF` com esquema; a 3 aprovou). Plano:
três (a 3 aprovou). Sete commits de tarefa — T0 (`01d2e63`), T1 (`1c25905`), T2 (`5cc26da`), T3
(`69a403a`), T4 (`c88495b`), T5 (`06830fe`), T6 (`0127446`) —, a T7 sem commit e o do fecho. **Fechou em
2026-10-02** e entrou na `main` pela PR #34; o parecer da CVM deixou de segurá-la, porque a plataforma não vai ser comercializada por enquanto ([D-160](decisoes/D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md)).

| Verificação | Resultado |
|---|---|
| As cinco tabelas (V-01, V-02, T1) | ✅ `core.portfolio`, `core.portfolio_version`, `core.portfolio_holding`, `gold.portfolio_risk_run` e `gold.portfolio_risk_result`, com os únicos e as checagens; versão e posição só crescem no Django e no banco (`portfolio_version_so_cresce`, `portfolio_holding_so_cresce`), e o `TRUNCATE` passa; `migrate portfolios zero` e de volta: 0 e 2 gatilhos |
| O filtro (V-10) | ✅ as cinco no `OrganizationScopedManager`, com o `unscoped` de gerente base; a varredura do M4.2 pega também `_base_manager`, e a única saída nova é `count_running_everywhere` |
| A série (V-03, V-04) | ✅ interseção das datas, retorno simples ponderado, índice em `float` na ordem do ticker, conferidos contra valores escritos à mão e o hash literal; o provedor dá ao motor o mesmo quadro que um montado à mão |
| A composição (V-05 a V-09) | ✅ pelo serviço, sem contexto posto, e pela rota: os sete `reason` do `invalid_holdings`, o peso gravado como veio, versão nova só quando a composição muda, duas trocas ao mesmo tempo dão as versões 2 e 3, o mesmo 404 para o que não é da organização |
| O risco (V-11 a V-18) | ✅ cada saída do pedido, a trava dos pedidos (7103) com duas threads, o corretor que recusa, a abertura, a tarefa por modelo nos três caminhos, o fecho, as duas corridas da trava da execução (7104), a leitura com o resumo e a perda em reais escritos à mão |
| A chave, o CSRF, o esquema, a web sem o motor (V-19 a V-23) | ✅ a chave lista e lê, recebe 403 na escrita; o esquema limpo no `--fail-on-warn`, **sem** entrada nova no `ENUM_NAME_OVERRIDES`; o lado da web não carrega o motor (subprocesso e `ast`); a conversão igual à `_row` do ativo nos cinco casos |
| **Execução real (V-25)** | ✅ pelo proxy do Vite, com `curl` e cookie, com o principal no HEAD do ramo (`0127446`), `web` e `worker` de pé nele e o Beat parado: `PETR4 40` / `VALE3 30` / `ITUB4 30`, `notional` `100000.00` → 201; `POST .../risk` → 202; **`ok` em 143 s** (`calculated_at` → `finished_at`; 147 s pelo relógio do `curl`), 18 resultados, nenhum erro; 2 493 datas (2016-09-27 a 2026-09-29), `price_run` 18; o `loss_brl` dos 18 conferido à parte, e o índice reconstruído do `psql` com a fórmula do RF-06 deu o mesmo `series_sha256` (`83f1f684…5db60d`); a 5%, de R$ 1 749,50 (`caviar`) a R$ 2 891,41 (`monte_carlo`), não rejeitados `caviar`, `garchnet` e `lstm`; a 1%, de R$ 2 508,92 a R$ 4 712,76, não rejeitado só o `caviar`. Pedir de novo → 409 `portfolio_risk_up_to_date` com `run_id` 1; a chave lê (200) e recebe 403 no `POST`; trocar os pesos → versão 2, `latest` nulo, pedir → 202, `ok` em 148 s. No `psql`, `UPDATE core.portfolio_holding SET weight = 1` → `ERROR: portfolio_holding so cresce` |
| O atraso na rotina | **não medido**: o Beat ficou parado, como o plano manda quando a rotina não roda junto. O que se sabe: uma carteira ocupa o `worker` por ~2,5 min, da ordem do cálculo completo de um ativo |
| Suíte, tipos, estilo | ✅ **1652 testes** no `worker` (1397 + 255), em 16 min 56 s — **1711** depois de receber a `main` com o M1.7 e o M2.3 (os 1456 dela e os 255), em 16 min 43 s —, num contêiner avulso com o worktree montado e banco de teste próprio (`RUVOR_DB_NAME=ruvor_m22`); `mypy` estrito limpo em 261 arquivos; `ruff check` e `ruff format --check` limpos; `makemigrations --check` sem mudança; `spectacular --validate --fail-on-warn` limpo |
| Mutações (T7) | ✅ as 25 reprovaram, cada uma no teste da coluna do plano; `git status` limpo depois |

**O que a execução contrariou.**

- **A pré-condição da mutação 5, como o plano a escreveu, não bastava.** A soma em ordem inversa
  diferir bit a bit da soma na ordem do ticker é necessário e não suficiente: a diferença de um ulp
  some no `1 + R` do índice, e a mutação sobreviveu na primeira medição. Os preços do teste foram
  trocados para que o próprio índice mude, e a pré-condição passou a ser afirmada sobre o índice.
- **As tarefas de app são dezessete, não dezesseis**: a spec contou antes de o M1.5c trazer a
  `fechar_presas`.
- **O tempo bateu com a estimativa** do RF-15 (141 a 175 s): 143 e 148 s, com as quatro redes
  treinadas do zero em cada pedido.

**Uma armadilha nova, em [aprendizados](aprendizados.md):** a pré-condição que prova que a ordem da
soma em `float` importa precisa ser afirmada sobre o número que o teste compara, não sobre um
intermediário.

Quatro decisões, que vieram com a spec: [D-116](decisoes/D-116-o-parecer-da-cvm-nao-bloqueia-a-spec-da-carteira-e-segura-a-implementacao.md) a [D-119](decisoes/D-119-o-risco-da-carteira-e-sob-demanda-em-gold-na-app-da-frente.md).

### M3.3 — Estresse histórico

Spec em [`specs/M3.3-estresse-historico.md`](specs/M3.3-estresse-historico.md) e plano em
[`planos/M3.3-estresse-historico.md`](planos/M3.3-estresse-historico.md). Frente `marco1`, ramo
`marco1/M3.3-estresse-historico`. Nove tarefas: a T0 a T4 numa máquina, num worktree, mescladas na `main` pela PR #36
com o portão da T4 pendente; a T5 a T8 noutra máquina, com o ramo no checkout principal, de `442e984` (T5) a `7d42e07`
(T6), a T7 e a T8 sem arquivo de código. O mockup `docs/mockups/M3.3/ativo-estresse.html` aprovado pelo dono no portão,
em 2026-10-02, **sem ajuste** — com as duas chaves que ele pediu fora da tabela do plano. Três decisões, aceitas com a
spec: [D-146](decisoes/D-146-o-estresse-historico-vira-bloco-so-do-ativo-e-so-com-preco.md) a
[D-148](decisoes/D-148-o-estresse-e-tabela-filha-da-metrica-e-sai-pelo-metrics.md). Promove o requisito candidato 5.3,
só do ativo. **Fechou em 2026-10-02**; a PR de implementação é do dono.

**O que passou a existir:** `apps/analytics/stress.py`, só biblioteca padrão — os quatro episódios curados da D-147
(a delação da JBS, a greve dos caminhoneiros, a chegada da covid e a alta dos juros), cada um com o retorno do
pregão-base ao final, a maior queda dentro da janela, a recuperação procurada na série inteira, o motivo de "sem dado"
(`starts_after`, `stale_start`, `ends_before`, `no_trading`) e o Ibovespa no mesmo recorte —; `gold.stress_episode`,
filha da linha de métrica, gravada no mesmo `atomic` do `compute_metrics`, sem tarefa, comando nem entrada no Beat
nova; o campo `stress` em `/metrics`, ao lado de `histogram`, com `episode` em texto livre e `missing` como enum no
esquema; no frontend, o `StressBlock` depois de "Maior queda", com o ativo e o Ibovespa medida a medida, as seis frases
de medida nas duas leituras (61 na lista fechada do V-02) e cada estado com a frase dele; no kit, `.ruvor-episodes`,
`.ruvor-episode` e `.ruvor-pair`, com a seção "Telas do M3.3" na vitrine.

| Verificação | Resultado |
|---|---|
| Suítes | ✅ **1747 no backend** (eram 1711), em 33 min 11 s, no `worker` com o Beat parado e nenhuma outra suíte rodando; **1263 no frontend** (eram 1217); `mypy` estrito limpo em 272 arquivos, `ruff check` e `ruff format --check` limpos, `makemigrations --check` sem mudança, `spectacular --validate --fail-on-warn` sem aviso; lint, `typecheck` e build do frontend limpos |
| Mutações (T7) | ✅ as 22 reprovaram sobre o código final, cada uma revertida com o `git status` igual ao de antes — 12 da T1, 4 da T2, 2 da T3 e 4 da T6 |
| O kit (T5) | ✅ as 24 capturas do mockup (três vistas, dois temas, dois níveis, 1440 e 360 px) idênticas byte a byte antes e depois de o estilo local virar classe do kit; os testes do kit verdes |
| A tela (T6) | ✅ PETR4 e IBOV nos dois temas, nos dois níveis, em 1440 e 360 px: o bloco logo depois de "Maior queda", os quatro episódios, sem rolagem horizontal, sem erro de página, sem 429; igual ao mockup |
| **O oráculo (T8)** | ✅ a consulta SQL da T0, literal, logo depois do `compute_metrics`: nos oito conjuntos (IBOV e PETR4), datas e pregões iguais ao gravado, `period_return` e `drawdown` a menos de 5E-11 |
| **Execução real (V-13)** | o roteiro `capturas.mjs`, sem mudança, com `RUVOR_E2E_SOB_DEMANDA=0` e `RUVOR_E2E_EMPRESA=PETR4`: a 1ª rodada **641 de 642**, reprovando só o tempo do RF-24 (3.514 ms, limite de 2 s); a 2ª, sem mudança nenhuma, ✅ **642 de 642**, 1.469 ms, 52 capturas, nenhum erro de página. As marcas: quatro `[data-episode]` na ordem nas três páginas, nenhum `[data-missing]`, o índice nulo só no IBOV |
| A hipótese do ajuste | **não exercida**: nenhum provento nem coleta de preço entre os dois cálculos da máquina; os episódios das duas linhas de cada ativo são iguais |
| Revisão final | inline, contra a spec (RF-01 a RF-16 e V-01 a V-14), sem divergência; não houve rodada do revisor adversarial separado |

**O que a execução mostrou:** a máquina nova começou com o banco vazio — a reinstalação do Docker Desktop apagou o
disco de dados —, e `gold` foi refeita do zero para os quatro ativos do Marco 1: o `compute_risk` levou 52 min, todos
`ok`. O banco não tem ativo com "sem dado" nem queda zero nos episódios: os quatro motivos, o índice nulo fora do IBOV e
a queda zero só os testes provam. A ABCB4, a ABEV3, a BBDC4 e o AALR3 não foram recalculados aqui. Dois aprendizados
novos: a máquina nova (o `.wslconfig` fora do clone, e quanto custa refazer `gold`) e o tempo do RF-24, que depende da
máquina.

### M1.4b — Correção do motor

Spec em [`specs/M1.4b-correcao-do-motor.md`](specs/M1.4b-correcao-do-motor.md) e plano em
[`planos/M1.4b-correcao-do-motor.md`](planos/M1.4b-correcao-do-motor.md). Frente `marco1`, ramo
`marco1/M1.4b-correcao-do-motor`, no worktree `E:/Temp/Trilobit/varlab-wt/M1.4b-correcao-do-motor`. Spec com duas rodadas
de revisão adversarial, plano com uma, os dois aprovados pelo dono em 2026-10-02. Nove tarefas: T0 (`24145bf`), T1
(`ebb307a`), T2 (`9a612bc`), T3 (`6906ccb`), T4 (`dd2ddcc`, `854dbaa`), T5 (`fe0dceb`, `8c5cbc8`), T6 (`3d1cc5e`), a
revisão da implementação antes da execução real, T6b (`a101039`, 0 graves e 0 médios), e T7 (`9fb9819`, a referência do
trecho 0). Sem portão de mockup ([D-158](decisoes/D-158-o-var-do-dia-nao-usa-o-retorno-do-dia-e-os-tradicionais-reestimam-a-cada-252-pregoes-restringe-a-d-97.md)).
Três decisões, com a spec: [D-157](decisoes/D-157-alteracao-no-motor-em-lista-fechada-para-a-correcao-do-m1-4b-restringe-a-d-76.md)
(a lista fechada), D-158 (o VaR do dia sem o retorno do dia, os tradicionais a cada 252 pregões, as frases sem mockup) e
[D-159](decisoes/D-159-a-linha-de-base-numerica-e-a-do-motor-0-4-0-restringe-a-d-44.md) (a linha de base do `0.4.0`).
**Fechou em 2026-10-03**; o ramo recebeu a `main` com o M2.2a, o M3.3 e a D-160 antes da execução real, e a PR de
implementação é do dono.

**O que mudou:** `_sigma_path` prevê a σ do dia `pos` com os retornos até `pos − 1` (o `forecast` começa em
`n_train + pos − 1`); os três tradicionais estimam o VaR por trechos de 252 pregões sobre todos os retornos conhecidos no
início do trecho (`engine/src/engine/models/traditional/_expanding.py`), com o Monte Carlo tirando os sorteios de cada
trecho em sequência de um só gerador, e declaram `refit_frequency_days = 252`; o motor é o `0.4.0`, e todos os retratos
`0.3.0` ficam inválidos pela impressão digital; `engine/tests/test_sem_olhar_a_frente.py` prova por perturbação, nos
seis modelos não neurais, que mudar os retornos de *t* em diante não muda o VaR de nenhum dia até *t*; a linha de base
se recaptura por `engine/tests/baseline/capturar.py`; as avançadas de `risco.perda95` e `risco.perda99` dizem a janela
nova; `backend/tests/risk/test_compute.py` lê a versão da metadata, não mais o literal.

**A execução real**, na ordem do RF-13, com o Beat parado do começo ao fim:

| Passo | O que aconteceu |
|---|---|
| 2 — a referência `0.3.0` | checkout principal na `main`; `worker` recriado (`Created` 2026-10-02T14:30:49Z), `version` = `0.3.0`; `compute_risk --async --full` dos seis às 14:31:02Z; `risk_run` **89 a 94, todas `ok`**; a fila vazia (as seis fechadas, `celery inspect` vazio, `redis llen celery` = 0) |
| interrupção | o primeiro build da imagem `0.4.0` morreu por falta de memória no hospedeiro (1,4 GB livres de 32); o checkout principal voltou à `main`, para código e versão ficarem coerentes, e o Docker caiu e voltou. **Nada foi gravado com versão trocada** |
| 3 | checkout principal destacado no HEAD do ramo, já com a `main` mesclada (`9d787d6`); o `migrate` aplicou `analytics.0002_gold_stress_episode` e `portfolios.0001_portfolio` no banco de desenvolvimento |
| 4 | `docker compose build worker`; `worker` recriado (`Created` 2026-10-03T00:29:05Z), `version` = `0.4.0` |
| 5 — o trecho 0 (RF-12, V-06) | a fixture recapturada: o diff só em `garchnet/0.05`, `garchnet/0.01` e `captured_with_engine` (`0.4.0`); **o `lstm` e o `gru` iguais**; sem a variável, verde; `9fb9819` |
| 6 — o recálculo `0.4.0` | `compute_risk --async --full` dos seis às 00:33:12Z; `risk_run` **95 a 100, todas `ok`**; a fila vazia pela mesma condição |
| 7 — o RF-15 (V-10) | no ITUB4 (execução 98), nos dois níveis: ver abaixo |
| 8 | o Beat recriado com a imagem `0.4.0`, saudável; **o checkout principal fica no HEAD do ramo até a mesclagem da PR** |

**O tempo do zero:** as seis execuções correm em paralelo no `worker` (`--concurrency=2`), e cada uma leva o tempo do
leque inteiro — a referência `0.3.0`, 8 min 20 s (a do VALE3, 8 min 36 s); a `0.4.0`, **7 min 52 s a 7 min 56 s**. Bate
com os ~8 min que a spec estimou para um `--full` dos seis; o tempo de um ativo sozinho não foi medido. Os tradicionais
por trechos não pesam.

**A comparação campo a campo (V-09)**, das execuções 89 a 94 contra 95 a 100, mesma série (`as_of_date` 2026-10-01, os
mesmos pregões por ativo), 108 pares (ativo, modelo, nível):

- **O `lstm`, o `gru` e o `caviar`, idênticos nos seis ativos**: 36 de 36 pares iguais em `var_latest`, `var_mean`,
  violações, os três p-valores, zona, `adequate`, hiperparâmetros e erro.
- **Os outros seis, com `var_latest` diferente em todos os 72 pares.** Nos tradicionais, o valor `0.3.0` era o quantil
  (ou a normal, ou a simulação) dos 252 primeiros retornos, constante no teste: o `0.4.0` difere dele nos 36 pares.
- **O GARCH e o EGARCH tinham violações de menos** — viam o choque do dia. Corrigidos, as violações sobem nos seis
  ativos e nos dois níveis — nos 24 pares —, chegando perto das esperadas (~111 a 112 a 5% e ~22 a 1%, em 2.220 a 2.245 dias de teste) no BBDC4, no IBOV e no ITUB4, e passando delas no AALR3: o
  EGARCH a 5% no ITUB4, de **48 para 101**; no IBOV, de 29 para 111; no BBDC4, de 32 para 104; a 1%, fora o AALR3, de
  4–12 para 20–41. O GARCH a 5%, de 49–63 para 65–100 (fora o AALR3, 116 → 142).
- **Os tradicionais erravam para os dois lados, conforme o ativo.** O quantil de 2016–2017 era baixo para o AALR3, o
  BBDC4, o IBOV e o ITUB4 (violações de mais: o `historical` a 5% do BBDC4, **159 → 112**; do ITUB4, 187 → 113; do AALR3,
  253 → 196) e alto para o VALE3 (violações de menos: 47 → 68) e, no `historical`, para o PETR4 (80 → 92). Na janela que
  cresce, o `parametric` e o `monte_carlo` a 5% ficam com 74 a 85 violações no BBDC4, no IBOV e no ITUB4 — abaixo das
  ~112 esperadas, e perdem o veredito.
- **O `garchnet`** muda pouco: violações a ±7 das de antes, em todos os pares.

A mudança de veredito (`adequate`), em quantos dos seis ativos o modelo não é rejeitado, antes → depois:

| Modelo | 5% | 1% |
|---|---|---|
| `historical` | 1 → 2 (ganham BBDC4 e ITUB4; perde IBOV) | 1 → 0 (perde ITUB4) |
| `parametric` | 3 → 0 (perdem BBDC4, IBOV e ITUB4) | 0 → 0 |
| `monte_carlo` | 3 → 0 (perdem BBDC4, IBOV e ITUB4) | 0 → 0 |
| `garch_1_1` | 0 → 1 (ganha IBOV) | 2 → 3 (ganha IBOV) |
| `egarch` | 0 → 3 (ganham BBDC4, IBOV e ITUB4) | 0 → 0 |
| `garchnet` | 4 → 4 | 2 → 3 (ganha ITUB4) |
| `lstm`, `gru`, `caviar` | iguais | iguais |
| **Total dos nove** | **20 → 19** | **13 → 14** |

O risco da spec ("o veredito do GARCH deve piorar") **não se confirmou no veredito**: o GARCH e o EGARCH tinham
violações de menos, e o Kupiec rejeita a cobertura baixa tanto quanto a alta — corrigidos, chegam perto da esperada e
**ganham** o veredito em parte dos ativos. A zona de Basileia mudou em sete pares, seis deles no AALR3 (o
`historical` a 1%, vermelha → verde; o `parametric` e o `monte_carlo` nos dois níveis, vermelha → amarela; o GARCH a
1%, verde → amarela) e um no ITUB4 (o `historical` a 5%, amarela → verde).

**O RF-15, a zona de Basileia (V-10):** um script avulso, no `worker`, rodou o motor `0.4.0` sobre a série da execução
98 (ITUB4, 2.498 pregões até 2026-10-01), pelo mesmo `run_models` do cálculo, um modelo por vez como a tarefa, sem gravar nada. **A guarda bateu
nos 18**: `var_latest` e violações recompostos iguais aos gravados. A zona recalculada pelas violações dos **últimos
250** dias bate com a gravada nos 18 — todas verdes, com 6 a 15 violações a 5% (12,5 esperadas) e 1 a 3 a 1% (2,5),
enquanto o teste inteiro tem, por exemplo, 113 no `historical` a 5%. **A entrada de *Aberto* fecha sem defeito:** a
suspeita comparava as violações do teste inteiro, que o Kupiec usa, com a zona, que olha só 250 dias.

| Verificação | Resultado |
|---|---|
| Sem olhar à frente (V-01 a V-03) | ✅ por perturbação, nos seis não neurais, em *t* fora do piso da σ; contra o `arch`, nas posições 0, 100, 252 e 400 |
| A lista fechada (V-07) | ✅ `git diff --stat origin/main -- engine/src/`: os seis arquivos da D-157 (o `pyproject.toml` fica fora de `engine/src/`); `base.py` só nas duas docstrings |
| A linha de base (V-05) | ✅ as dez entradas das cinco famílias mudaram, as duas do `caviar` iguais; **25 verdes** no hospedeiro |
| O trecho 0 (V-06) | ✅ só o `garchnet` mudou |
| Mutações (T6) | ✅ todas reprovam: o laço antigo do GARCH, o VaR constante, o gerador por trecho, o hiperparâmetro fora, o script com o motor velho, a frase velha |
| Suítes (V-08) | ✅ depois da `main` mesclada: **1747 no backend** (`mypy` e `ruff` limpos); **152 no motor** sem a linha de base, no contêiner avulso do `worker` com o motor do ramo, em 4 min 51 s — o V-04 (o trecho 0) entre eles, verde; **25 da linha de base** no hospedeiro; **1265 no frontend** |

**O que a execução mostrou.**

- **O build da imagem pode morrer por falta de memória do hospedeiro**, e a execução real fica no meio: o checkout
  principal voltou à `main` enquanto não havia imagem nova, para nenhum cálculo sair com código e versão desencontrados.
- **O Beat, ao voltar, dispara na hora o que perdeu o horário**: na partida, o `PersistentScheduler` mandou a
  `rotina_diaria` e a `importar_comunicados`, que tinham passado do horário com ele parado. A rotina coletou o pregão
  de 2026-10-02 e abriu as execuções incrementais 101 a 106, `0.4.0`, com o código do ramo — todas `ok` em
  **~1 min 41 s**. Saiu coerente porque o checkout já estava no ramo. **E o caso de provento que faltava medir
  apareceu:** o BBDC4 tem dividendo com data de 2026-10-02, e a linhagem dele se retreinou inteira — 72 retratos novos,
  os mesmos 72 que o `--full` grava por ativo —, enquanto os outros cinco não gravaram nenhum. O tempo do BBDC4 sozinho
  não foi medido.
- **A consulta "a última execução `0.4.0` de cada ativo" pegou a incremental em curso**: a primeira tabela do V-09 saiu
  com 10 linhas do BBDC4, de uma execução ainda aberta. Refeita pelo `id` (89 a 94 contra 95 a 100), 108.
- Quatro aprendizados novos, em [aprendizados](aprendizados.md): o build morto e a regra de devolver o checkout; o
  `docker compose run --rm` que perde a saída se cortado; a folga da guarda do piso da σ; e o Beat que dispara ao voltar,
  com a comparação fixada pelo `id`.

**O impacto no TCC.** As Tabelas 1 e 2 de `docs/tcc/TCC_II_VaR_ML_v3.md` e a conclusão preliminar de que o GARCH e o
EGARCH ganham dos "tradicionais estáticos" saíram do motor com os dois defeitos: o GARCH via o retorno do dia, e os
tradicionais eram o quantil do primeiro ano. Refazê-las é da [trilha do TCC](#trilha-paralela--tcc), sobre o `0.4.0`.

**A imagem é uma só.** Desde o passo 4, a imagem compartilhada do `worker` diz `0.4.0`. Os outros worktrees que rodam o
backend em contêiner avulso dessa imagem (o M2.1b, os da `identidade`) têm, em `backend/tests/risk/test_compute.py`, a
versão `"0.3.0"` literal em duas asserções, que reprovam **até o ramo receber a `main` com o M1.4b**. E, até a PR ser
mesclada, **nenhum outro ramo é servido pelo stack**: o checkout principal fica no HEAD deste, porque um cálculo com o
motor `0.3.0` montado gravaria números velhos com o rótulo `0.4.0`, para sempre (D-16).

### M2.1b — Telas de acesso

Spec em [`specs/M2.1b-telas-de-acesso.md`](specs/M2.1b-telas-de-acesso.md) e plano em
[`planos/M2.1b-telas-de-acesso.md`](planos/M2.1b-telas-de-acesso.md). Frente `marco1`, ramo
`marco1/M2.1b-telas-de-acesso`, no worktree `E:/Temp/Trilobit/varlab-wt/M2.1b-telas-de-acesso`. Dezesseis tarefas: T1
(`3461a9b`), T2 (`24a424f`), T3 (`aedee23`), T4 (`611c5a9`); os cinco mockups (T5 a T9), cada um com revisão e portão,
aprovados pelo dono em 2026-10-03; T10 (`b367557`), T11 (`8e5125f`), T12 (`5c391c6`), T13 (`ca686d2`), T14 (`7b1b990`,
e `45a06c5`, a correção que a execução real pediu); a T15 sem arquivo; a T16, o roteiro (`77b989d`) e o FECHA. Uma
decisão, com a spec: [D-140](decisoes/D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md) (o pedido de cálculo
exige conta pronta); a D-141 e a D-142 ficaram sem uso. **Fechou em 2026-10-03**; a PR de implementação é do dono,
revisada pela `identidade`, e **espera o ajuste dela** no caso anônimo do `tests/accounts/test_requested_by.py`.

**O que passou a existir:** no backend, só a permissão do `POST /risk` — `ReadOpenWriteAccountReady`
(`apps/api/permissions.py`), o 401 e o 403 no esquema do `post` e os docstrings do pedido (o de `ComputeRequest`
inclusive) dizendo o que o código faz. No frontend: o cliente HTTP com `apiPatch`, `apiDelete`, corpo JSON, 204 sem
corpo, o `auth/csrf` antes de toda escrita sem cookie e uma repetição em `csrf_failed`; o proxy do Vite com
`changeOrigin: false`; a sessão em `src/session/` (`SessionProvider` na rota de layout da raiz, um `auth/me` por carga,
`safeNext` e `signInHref`); as telas `SignInScreen`, `SignUpScreen`, `PasswordScreen` (voluntária e obrigatória) e
`UsersScreen`; o `AccountMenu` por último na barra e o `SignInNotice`; o convite do E7/E8 pela sessão, e o 401 e o 403 do
`POST`; no kit, a cena de acesso, o lugar da conta e o menu, o diálogo, o copiar, os tokens novos e a barra estreita até
840 px; os textos `acesso.*`, `cadastro.*`, `senha.*`, `conta.*` e `usuarios.*`; e o roteiro `frontend/e2e/acesso.mjs`,
com a conta do passo 4 do `capturas.mjs` criada pelo próprio roteiro e a chave `RUVOR_E2E_SO_CONTA`.

**O que os portões mudaram** (registrado no plano): o menu de conta **por último** na barra, depois da chave de tema, num
lugar de largura fixa, só com as iniciais abaixo de 1024 px; a barra estreita em três linhas até 840 px (era 720); o papel
`admin` se mostra **"Administração"** na gestão de usuários; a dica da senha compartilhada pelo cadastro e pelas duas
trocas; o "Continuar" depois do sucesso da troca; o 401 nas trocas e na gestão no lugar da ação.

**A execução real**, com o checkout principal no HEAD do ramo e o Beat parado, pelo orquestrador:

| Passo | O que aconteceu |
|---|---|
| O proxy (T1) | o `/health` pela porta 5273 do hospedeiro respondeu **200** |
| `acesso.mjs`, 1ª rodada | **129 de 130**: o diálogo da gestão de usuários reabria antes do `close` do navegador (ver abaixo); a organização `e2e-20261003163511` foi gasta nela |
| `acesso.mjs`, 2ª rodada | ✅ **133 conferências, 0 falhas, 36 comparações com os mockups sem diferença**; 7 pedidos no limite `auth`, **0 esperas**. O cadastro `e2e-u-20261003194338@exemplo.com`; o membro `e2e-m-20261003194338@exemplo.com`; a administradora `e2e-20261003164333@exemplo.com`, da organização `e2e-20261003164333`; o ticker sem risco, **ABCB4** |
| `capturas.mjs`, `RUVOR_E2E_SO_CONTA=1` | ✅ 3 conferências, 0 falhas — a tela do ativo abre logada |
| `capturas.mjs` completo | a 1ª rodada reprovou por **429** — a taxa do anônimo, 60/min, com o `auth/me` a mais por carga; a 2ª, com `RUVOR_THROTTLE_ANON=100000/min` só durante a rodada, ✅ **644 conferências, 0 falhas**. O `.env` voltou igual, com o sha256 conferido |
| O fim | o Beat religado e o checkout principal de volta à `main` |

| Verificação | Resultado |
|---|---|
| Suíte do backend | **1 failed, 1752 passed** (1753). A falha é `tests/accounts/test_requested_by.py::test_v19_o_pedido_anonimo_grava_nulo_no_pedido_e_na_execucao`: o caso anônimo, que espera 202 e autor nulo, e com a D-140 recebe 401. É da `identidade`, na cerca dela — a pré-condição externa do plano —, e **a PR espera esse ajuste**. `mypy` e `ruff` limpos |
| Frontend | ✅ **1621 testes** (eram 1265); lint, `typecheck` e build limpos — o build avisa do pacote acima de 500 kB, registrado na T12, sem ação neste bloco |
| A cerca do backend | ✅ `git diff --stat` mostra só os sete arquivos da T2 — `apps/api/models.py`, `apps/api/permissions.py`, `apps/api/views.py` e os quatro de `tests/api/`; nada em `backend/tests/accounts/` |
| Mutações (T15) | as 22 da tabela, mais a nova da T12 (a obrigatória chama `reload()` no 204) e quatro variantes, de novo sobre `2c4f730`: **todas reprovam**, cada uma revertida com o `git status --porcelain` vazio — backend 4 e 2 falhas (M1, M2), frontend de 1 a 10 falhas por mutação |

**O que a execução mostrou:** o dublê de `<dialog>` dos testes disparava o evento `close` de forma síncrona, e no
navegador ele chega numa tarefa enfileirada: entre o `close()` e o evento, a linha trocada renderizava com o diálogo já
fechado e o estado ainda aberto, e o efeito chamava `showModal()` de novo. Os 1610 testes passavam; só o `acesso.mjs`
mostrou. A correção (`45a06c5`) guarda o elemento em que o `showModal()` já foi chamado, e o dublê passou a disparar o
`close` num `setTimeout`, com um teste que reprova sem a correção. E o `capturas.mjs` completo precisa da taxa do anônimo
subida, agora com um pedido a mais por carga. Os dois em [aprendizados](aprendizados.md).

**Pendência para a `identidade`:** `verbose_name` em `User.name` e `User.email`. A mensagem de semelhança da senha, que o
cadastro e a troca mostram como a API a manda, cita o campo em inglês ("…parecida com name", "…parecida com email").

### M2.4 — Regime de laboratório

Spec em [`specs/M2.4-regime-de-laboratorio.md`](specs/M2.4-regime-de-laboratorio.md) e plano em
[`planos/M2.4-regime-de-laboratorio.md`](planos/M2.4-regime-de-laboratorio.md), aprovados pelo dono em 2026-10-03. Frente
`marco1`, ramo `marco1/M2.4-regime-de-laboratorio`, no worktree `E:/Temp/Trilobit/varlab-wt/M2.4-regime-de-laboratorio`.
Quinze tarefas, T0 a T14: T1 (`f617a50`), T2 (`d58c1b2`), T3 (`48eca48`, e `696e859`, a correção da revisão de
implementação), T4 (`b885ef2`), T5 (`064a0a2`), T6 (`65e42a6`), T7 — a fase A — (`fbd9cb4`), T8 (`e7a04f5`, `e263c16`),
o mockup aprovado na T9 (`5008161`), T10 (`c73b397`, `2175cc9`), T11 (`6ea0633`), T12 (`6e0a24c`), T13 (`ff51702`) e a
T14 — a fase B — (`dd4efc7`) e o FECHA. Cinco decisões, com a spec:
[D-183](decisoes/D-183-o-laboratorio-e-o-calculo-de-producao-recortado-na-decada-do-ativo-restringe-a-d-04.md) (o laboratório é o cálculo de produção recortado na década do ativo),
[D-184](decisoes/D-184-a-decada-e-a-do-ativo-e-o-teste-se-le-em-anos-de-252-pregoes.md) (a década e os anos de 252, o
veredito por ano só a 95%), [D-185](decisoes/D-185-o-experimento-mora-em-tres-tabelas-de-gold-imutaveis-e-um-ok-por-identidade.md)
(as três tabelas, imutáveis, um `ok` por identidade), [D-186](decisoes/D-186-o-experimento-roda-pela-fila-depois-do-fecho-do-risco-de-producao.md)
(pela fila depois do fecho, e `compute_lab`) e [D-187](decisoes/D-187-a-secao-do-laboratorio-fica-na-tela-do-ativo-depois-do-risco-sem-eleger.md) (a seção na tela do ativo, sem eleger). **Fechou em
2026-10-04**; a PR de implementação é do dono, e nenhuma revisão de outra frente é obrigatória.

**O que passou a existir:** no backend, `apps/risk/decade.py` (a década, pura, sem o motor; `compute._bars` delega a ele
o filtro), `apps/risk/lab.py` (os anos, a soma conferida, a identidade, `lab_due`, `run_lab` — o registry conferido antes
de calcular, o mesmo `run_models` com `full=False`, a série relida depois do cálculo — e `write_lab` sob a trava do ativo,
que só grava sem `ok` da identidade), as três tabelas da migration `risk.0004` com o gatilho `lab_so_cresce`, a tarefa
`calcular_laboratorio`, o `on_commit` no fecho do risco, `manage.py compute_lab` e a rota `GET /api/v1/assets/{ticker}/lab`.
No frontend, a seção `LabSection` logo depois do risco, os nove estados e as três notas (`src/lab/state.ts`), a releitura
de no máximo 2 minutos depois do acompanhamento (`src/lab/useLabPolling.ts`), o `/lab` fora do `data-ready`, a lista
fechada de nove chaves `laboratorio.*` nas duas leituras e as classes `ruvor-lab-*` no kit. No roteiro, a seção do
laboratório e a comparação com o mockup.

**A execução real**, em duas fases, com o checkout principal no HEAD do ramo e o Beat parado:

| Fase | O que aconteceu |
|---|---|
| A (T7, `696e859`) | a `risk.0004` aplicada; o IBOV pelo fecho do risco (`lab_run` 1, `risk_close`, 4,18 s) e, pelo `compute_lab`, BBDC4, ITUB4, PETR4 e VALE3 (`lab_run` 2 a 5, 3,8 a 5,7 s cada, **72 retratos reaproveitados e nenhum treinado**); o **AALR3** saiu "década incompleta (completa em 2026-10-28)"; a segunda rodada, toda "já calculado", sem mudar contagem; **o prefixo**: a década do ITUB4 igual ao começo da série de produção nos 18 pares, `n = 2238`, **diferença máxima 0,0**; as conferências por SQL (nenhum retrato treinado, a soma dos anos igual às violações, os testes nulos a 99%) e os seis `UPDATE`/`DELETE` crus recusados com `lab so cresce`; a foto do `/lab` do ITUB4 e do IBOV para o mockup |
| B (T14, `ff51702`) | o `/lab` igual byte a byte à foto da fase A; o roteiro com **918 conferências, 0 falhas**, 226 da seção do laboratório (ITUB4 e IBOV, dois temas, 1440 e 360 px, dois níveis) e **16 comparações com o mockup aprovado sem diferença**; a taxa do anônimo subida só na `web`, pela variável do shell, sem tocar o `.env`; **a taxa**, com a padrão: 18 pedidos por carga, 5 cargas completas por minuto, o 429 no 108.º pedido |
| O fim | o checkout principal de volta à `main`, o `worker` recriado nela, o Beat religado, o `.env` igual (sha256 conferido) nas duas fases |

| Verificação | Resultado |
|---|---|
| Suíte do backend | ✅ **1909 passed** (eram 1753); `mypy` e `ruff` limpos |
| Frontend | ✅ **41 arquivos, 1724 testes** (eram 1621); lint, `typecheck` e build limpos (o aviso de pedaço acima de 500 kB, de sempre) |
| O motor | ✅ `git diff --stat origin/main...HEAD -- engine/` vazio: nenhuma linha de `engine/` |
| Mutações | as 32 do backend (com a 17 em duas variantes) e a 48, de novo na T6, e as do frontend na T13: **todas reprovam**; mais as da correção da revisão (a série relida, o ramo do `IntegrityError`, a escrita sem a trava) |

**O que a execução mostrou:** a dependência que o `makemigrations` gera para uma migration com chave para `silver.asset`
é a última da `assets` — a `0004_unaccent` —, e o `test_unaccent` a desfaz sem refazer: a primeira suíte da T2 perdeu as
três tabelas (`2 failed`); a `risk.0004` depende da `assets.0003`. Duas suítes ao mesmo tempo estouram o tempo de 5 s dos
testes também no frontend (T12). A revisão de implementação pediu que a série seja relida depois do cálculo — um provento
no meio gravaria o experimento sobre preços que o banco já não tem. A spec dizia "~190" e "perto de 10%"; as contas da
conferência dão **192** e **perto de 7%**, e a D-184 nasceu corrigida. Os dois aprendizados em
[aprendizados](aprendizados.md).

### M5.1 — Retorno

Spec em [`specs/M5.1-retorno.md`](specs/M5.1-retorno.md) e plano em [`planos/M5.1-retorno.md`](planos/M5.1-retorno.md),
aprovados pelo dono em 2026-10-03. Frente `marco1`, ramo `marco1/M5.1-retorno`. T0 a T9 com o darkside171, no worktree
dele — T1 (`fe2f0e9`), T2 (`81c4434`), T3 (`0be6194`, e `fb5d769`, a correção da revisão de implementação), T4 (`208b21a`),
T5 (`472c912`), T6 (`4b7bd6c`), T7 — a fase A — (`19833d9`), T8 (`e725675`) e o mockup aprovado na T9 (`ef0f04e`) —; **a
retomada, T10 a T14, com o Kauã, na máquina dele**: a `main` com o M2.4 recebida (`bc50562`), os ajustes da revisão do
mockup e as duas escolhas do portão (`bcc5eaf`), T10 (`94ca818`), T11 (`13a813c`), T12 (`f123e02`), T13 (registrada em
`74652b3`) e a T14 com o FECHA. Cinco decisões, com a spec: [D-188](decisoes/D-188-a-previsao-de-retorno-e-o-log-retorno-de-um-pregao-contra-o-retorno-zero.md) (o log-retorno de um pregão contra o retorno
zero, e a previsão do próximo pregão), [D-189](decisoes/D-189-o-motor-ganha-o-pacote-engine-returns-em-lista-fechada-e-vai-a-0-5-0-restringe-a-d-21-a-d-76-e-a-d-157.md) (o pacote `engine.returns` em lista fechada, o motor `0.5.0`),
[D-190](decisoes/D-190-a-validacao-do-retorno-e-o-diebold-mariano-contra-o-zero-e-nenhum-modelo-e-eleito.md) (o Diebold-Mariano no veredito; nenhum modelo eleito), [D-191](decisoes/D-191-o-retorno-mora-em-apps-returns-e-roda-no-quinto-elo-da-rotina-estende-a-d-91.md) (a app `apps/returns`, o quinto elo
da rotina, a rota `/returns`) e [D-192](decisoes/D-192-a-tela-mostra-a-validacao-e-a-previsao-junto-dela-com-o-aviso-estende-a-d-160.md) (a previsão só junto da validação, o aviso, e o M5.1 segue a D-160).
**Fechou em 2026-10-04**; a PR de implementação (#41) é do dono, e nenhuma revisão de outra frente é obrigatória.

**O que passou a existir:** no motor, `engine/src/engine/returns/` — a média histórica e o AR(1) em walk-forward com
reestimação a cada 252 pregões em janela que cresce, a validação (`r2_os`, acerto de direção, DM, CW e PT com Newey-West)
e o orquestrador —, sem mudar nenhuma linha de arquivo existente, no `0.5.0`. No backend, `apps/returns` com
`gold.return_run` e `gold.return_result` (imutáveis, a migration `returns.0001`), o cálculo com o veredito decidido sobre
o *p* quantizado, `manage.py compute_returns`, a tarefa `calcular_retornos` como quinto elo da `rotina_diaria` (nunca
levanta) e o passo na cadeia sob demanda, e a rota `GET /api/v1/assets/{ticker}/returns`. No frontend, a seção
`ReturnsSection` depois do laboratório e antes dos Fundamentos, os estados R1 a R8 e a visibilidade da previsão em
`src/returns/state.ts`, a lista fechada de sete chaves `retorno.*` nas duas leituras, a lista ampliada do vocabulário só
nas `retorno.*`, e as classes `ruvor-returns-*` no kit. No roteiro, as conferências da seção do retorno.

**A execução real.** A fase A do dono (T7) rodou na máquina dele; **a da retomada, de novo, na do Kauã**, porque o banco é
outro — outros ativos cobertos (ABCB4 e ABEV3 no lugar de BBDC4 e AALR3), preços até 29 e 30/09 e o risco ainda no motor
`0.3.0` —, com o Beat parado e o `.env` igual do começo ao fim (sha256 `92bf67a4…`):

| Fase | O que aconteceu |
|---|---|
| A — a referência | com o código da `main` (worktree em `origin/main` montado num `worker` avulso, imagem `0.4.0`, o `worker` parado): `import_prices` (os seis até 2026-10-02), `compute_metrics` e `compute_risk --full`, síncrono: `risk_run` 11 a 16, `0.4.0`, `ok`, 18 resultados cada, 1314,6 s |
| A — o `0.5.0` | `migrate` (a `returns.0001`), `docker compose build worker` (2 min 35 s), `version("ruvor-engine")` = `0.5.0`; `compute_risk --full`, síncrono: `risk_run` 17 a 22, `ok`, 1287,4 s; **os 108 pares iguais** (`serie_igual` nos seis; `pares 108, iguais 108`, todos os campos de `risk_result` menos os retratos) |
| A — o retorno | `compute_returns`: 6 ativos, 6 `ok`, 0,2 s; **nenhum modelo bate a referência** nos 12; `next_forecast_date` = 2026-10-05 nos 12; o oráculo (`numpy`, sem `engine.returns`): **pior diferença 4,982e-11, nenhuma divergência**; `{'0.5.0'}` como única versão em `gold.return_run` |
| B | o `worker` recriado na imagem `0.5.0`; um tique da `rotina_diaria`: `risk_run` 23 a 28 `ok` em 40 a 57 s (os retratos reaproveitados), `return_run` 7 a 12 `0.5.0`, e o laboratório `0.5.0` dos seis pelo fecho (`lab_run` 1 a 6, `risk_close`); o roteiro (`RUVOR_E2E_SO_RETORNO=1`, a taxa do anônimo subida só na `web` e devolvida): **558 conferências, 0 falhas**, 24 capturas — ITUB4, PETR4 e IBOV, dois temas, 1440 e 360 px, dois níveis |

| Verificação | Resultado |
|---|---|
| Suíte do backend | ✅ **1972 passed** (eram 1909 na `main`); `mypy` e `ruff` limpos |
| Frontend | ✅ **43 arquivos, 1822 testes** (eram 1724); lint, `typecheck` e build limpos |
| O motor | ✅ **204 passed** no contêiner (152 + 52 do retorno), o `test_redes_trecho0.py` no `worker`, `mypy` e `ruff` limpos; a linha de base no hospedeiro, **25 passed**, sem recaptura (`valores.json` igual ao da `main`) |
| `web` | `manage.py check` sem problema; `spectacular --validate --fail-on-warn` sem aviso |
| Mutações | 1 a 33 (motor e backend) na T6; 34 a 58 (frontend) na T13: **todas reprovam** |

**O que a retomada mostrou:** o V-09 do laboratório (M2.4) era instável — a trava sai no commit, antes de a outra thread
marcar o evento no `finally` —, e reprovava 3 de 5 vezes; corrigido para conferir no banco (`ef59c7f`), 8 de 8 verdes.
A imagem e o volume do `frontend` precisam ser refeitos depois de receber a `main` com o `react-router`. E a fase A noutra
máquina começa por refazer a referência. Os três em [aprendizados](aprendizados.md).

## Próximo passo

**Na frente `marco1`, a PR do M5.1** (#41, implementação, T0 a T14), que sai do rascunho e o dono mescla com a CI verde;
nenhuma revisão de outra frente é obrigatória. O M2.4 entrou pela PR #40. **A imagem do `worker` é uma só e passa a
dizer `0.5.0`**: um checkout noutro ramo sem o M5.1 não pode rodar o cálculo do risco com ela (a versão sairia errada em
linhas imutáveis), e a primeira rotina de cada máquina depois da mesclagem retreina os quatro modelos caros (os retratos
`0.4.0` não valem) e refaz o laboratório. **O M2.2b** recebe a `main` com o M5.1 antes da tela: a ordem das seções é
risco → laboratório → retorno → Fundamentos → Comunicados. **O AALR3 completa a década em 2026-10-28**: o primeiro fecho do
risco depois disso grava o experimento dele. **O parecer da CVM, quando vier antes de comercializar, precisa cobrir o M5.1
nomeadamente** (D-192). Ramos e a regra de onde cada comando roda estão em [frentes/marco1.md](frentes/marco1.md).

**Antes de expor a aplicação fora da máquina**, a hospedagem decide o cache e a compressão do `/prices` (341 KiB sem
compressão). O recado da [D-90](decisoes/D-90-calculo-sob-demanda-so-para-ativo-nunca-calculado.md) — "limite por IP ou
login" — fecha pelo login com o M2.1b ([D-140](decisoes/D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md)), mas
login não é cota: o cadastro é aberto, e qualquer pedido bem-sucedido torna o ativo coberto para sempre — o `AALR3` já
entrou assim.

**O tique do Beat num dia útil já foi visto** (2026-09-28, ver o M1.6b): a rotina inteira, sem
treino. **O que falta medir** é um dia em que um ativo coberto pague provento — se ele aparecer com
`trained_snapshots` 9, a estimativa do V-13 do M1.5b se confirma. A rotina agora inclui o `BBDC4` e o
`AALR3`. **Visto em 2026-10-03**, no tique que o Beat disparou ao voltar no fecho do M1.4b: o dividendo do `BBDC4` com
data de 2026-10-02 retreinou a linhagem inteira dele (72 retratos novos), e os outros cinco ativos nenhum; o tempo do
`BBDC4` sozinho segue sem medida.

**`gold` segue derivado, mas deixou de ser barato de refazer à mão:** o Beat acrescenta uma
`risk_run` por ativo coberto a cada dia útil — seis, desde o `AALR3` —, e `migrate risk zero`
apagaria essa história junto — e, desde o M1.5b, os retratos. Ela ainda se reconstrói — o preço
está em `silver`, e um `--full` dos quatro ativos do M1.5b levava ~5,5 min —, mas só para a série de hoje, não para a de cada dia passado.

**Na frente `identidade`, o M2.2a está na `main`** (PR #34), sem o parecer da CVM
([D-160](decisoes/D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md)). O M2.2b, as telas da carteira, é da `marco1` e não espera o parecer. O
próximo bloco da frente é escolha do dono ([frentes/identidade.md](frentes/identidade.md)). **O recado do M4.2 para a `marco1` e o M2.2:** toda view nova declara
`api_key_scope` e `extend_schema`; tabela privada nova usa o gerente de `tenancy.py`; teste usa
`force_login`, não `force_authenticate`; em dev, suba `RUVOR_THROTTLE_ANON` no `.env` — a página
de ativo são cinco `GET`, todos com o IP do contêiner `frontend`.

**Na frente `fundamentos`, o próximo bloco não está definido.** O M3.2 fecha o Marco 3 do
ROADMAP para esta frente, e a escolha é do dono dela ([frentes/fundamentos.md](frentes/fundamentos.md)).
O que o M3.1 e o M3.2 deixam para quem vier: as telas dos fundamentos e do contexto são de outro
bloco, depois do casco do M1.6. A dos fundamentos precisa mostrar de quando é o preço
(`price_date`) e o que entra na dívida. A do contexto precisa chamar os documentos de
"comunicados da companhia à CVM", não de notícias, e mostrar o grupo de pares e o nível. A coleta
de fundamentos passa pelo `worker` — pico de 2,235 GiB na carga do zero —, às segundas às 8h; a
de comunicados, de segunda a sexta às 20h, é leve.

---

## Dívida registrada

| Dívida | Onde | Quando se paga |
|---|---|---|
| **Ações de balcão organizado (SOMA) ficam fora do catálogo.** 8 companhias com `hasQuotation=S` têm código com sufixo `B` (`EQMA3B`, `MRSA3B`, `LTEL3B`, `PRMN3B`...), que o regex do RF-05 exclui; 44 outras vêm com `otherCodes: null`. Estão na `bronze`, não na `silver` | `backend/apps/assets/conform.py`, `EQUITY_CODE` | Quando o produto decidir se balcão entra — é decisão de cobertura (D-19); mudar o regex é uma linha e o relatório do `import_assets` já conta os casos |
| **`listing_segment` nulo em 192 das 473 ações.** O `market` da listagem da B3 vem vazio para a maioria das companhias; só NM/N1/N2 vêm preenchidos | `silver.asset.listing_segment` | Quando a tela precisar do segmento — a fonte alternativa é o `market` por extenso do detalhe (`"BOVESPA NIVEL 2"`), que a spec do M1.1 decidiu não usar |
| `ignore_errors` do mypy em `engine.models.ml._quantile_nn` e `engine.models.garch._conditional` | `engine/pyproject.toml`, comentado no próprio arquivo | Depois da Etapa 6, quando a [D-21](decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) deixar de congelar o motor |
| ~~`RUVOR_ALLOWED_HOSTS` não tolera espaço após a vírgula~~ | ~~`backend/config/settings.py`~~ | ✅ **quitada no F3** — virou a função `_split_hosts`, com cinco testes e mutação provada |
| ~~**`gold.risk_run.requested_by` é sempre nulo, e a [D-15](decisoes/D-15-manifesto-de-execucao.md) fica cumprida pela metade.** Ela exige "a pedido de quem", e não há usuário autenticado antes do M2.1. A coluna nasceu anulável e nenhum caminho do código a preenche~~ | ~~`backend/apps/risk/models.py`, `RiskRun.requested_by`~~ | ✅ **quitada no M2.1a** (T14, 2026-09-30) — o pedido sob demanda logado grava o autor, e a execução que ele abre também. A rotina e o caminho síncrono seguem nulos: não têm quem pediu. As execuções antigas ficam sem autor, sem migration de dado |
| ~~Tarefa Celery é `Any` sob o mypy, porque o Celery não publica tipos. **O M1.5 criou sete e não pagou** ([RF-14](specs/M1.5-execucao-assincrona.md#rf-14)); **o M3.1 criou três e também não pagou**, por cerca: adotar `celery-types` muda o `backend/pyproject.toml` e o registro das **oito** tarefas que existiam antes dele (as sete de app e o `ping`), em arquivos da `marco1` — aceito pelo dono da frente em 2026-09-26. **São onze agora**, todas registradas sem decorador, e o `ignore_missing_imports` de `celery.*` segue~~ | ~~`backend/pyproject.toml`~~ | ✅ **quitada no M3.2** — `celery-types==0.26.0` no extra `dev`, o override saiu, e o `mypy` estrito segue limpo com as doze tarefas; a forma de registro ficou, pelo ponto de teste ([D-134](decisoes/D-134-tarefas-celery-tipadas-por-celery-types.md)). O M1.6a acrescentou duas tarefas, limpas no `mypy`, e a guarda que o `mypy` não dá: `tests/test_tipos.py` reprova o override de `celery` de volta (V-19d) |
| ~~**RF-14 não tinha verificação permanente.** Apagar `backend/tests/conftest.py` deixava a suíte inteira verde: o teste que provava a guarda era descartável, medido e removido pela T2~~ | ~~`backend/tests/`~~ | ✅ **quitada no fecho do M1.3** — `tests/test_guarda_de_rede.py`, com a mutação medida: sem a guarda, reprova |
| ~~**O V-15 só existe enquanto alguém digita o comando.** "Sem dependência numérica nova" (RF-13) é verificado por `git diff` no `pyproject.toml` e `grep` por `numpy\|pandas`, rodados à mão na T4 e na T8. Nada na suíte nem na CI reprova quem acrescentar `numpy` amanhã~~ | ~~`.github/workflows/ci.yml`, `backend/pyproject.toml`~~ | ✅ **quitada no M1.6d** — `backend/tests/test_dependencias.py` reprova qualquer das seis bibliotecas de `_BIBLIOTECAS` em `project.dependencies` ou num extra, com o nome normalizado (PEP 503), e confere a lista copiada contra a de `test_versoes_travadas.py`; roda no job `backend` da CI |
| ~~**Não há filtro automático por organização.** O F4 entregou a coluna; o mecanismo que faz a consulta filtrar sozinha não existe — e sem ele, "coluna sem filtro é teatro"~~ | ~~`backend/apps/accounts/models.py` (`User.organization`)~~ | ✅ **quitada no M4.2** — `apps/accounts/tenancy.py`, aplicado à primeira tabela privada, `core.api_key` ([D-112](decisoes/D-112-o-filtro-automatico-por-organizacao-nasce-no-m4-2.md)); o M2.2 só o aplica. `core.user` e `core.access_event` ficam fora, por nome ([D-41](decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md), [D-104](decisoes/D-104-auditoria-de-acesso-em-core-access-event-restringe-a-d-41.md)) |
| ~~`createsuperuser` não funciona.~~ | ~~`backend/apps/accounts/managers.py`~~ | ✅ **quitada na fase 1 do M2.1a** — sem organização, o superusuário vai para a `ruvor`, como `admin` ([D-105](decisoes/D-105-superusuario-mora-na-ruvor-restringe-a-d-39.md)); `--noinput` com as `DJANGO_SUPERUSER_*` funciona |
| **Quem esquece a senha da organização pessoal fica sem saída.** Não há envio de e-mail: a redefinição é da administradora, e na organização pessoal ela é a própria pessoa. Até lá, o operador redefine por `shell` | `backend/apps/accounts/services.py` | O primeiro bloco que decidir envio de e-mail (hospedagem) — [spec M2.1a, Riscos](specs/M2.1a-identidade-e-acesso.md#riscos-e-questões-em-aberto) |
| **`django_session` cresce sem limpeza.** Sessão vencida fica na tabela até alguém rodar `manage.py clearsessions` | `public.django_session` | Uma entrada própria no Beat quando o volume justificar, ou na hospedagem |
| **A taxa anônima depende de `NUM_PROXIES`.** Sem ele certo, atrás de um proxy todo pedido chega com o IP do proxy, e os 60 por minuto por IP viram teto do site inteiro — o mesmo risco do limite `auth` do M2.1a, agora sobre a leitura | `backend/config/settings.py`, `REST_FRAMEWORK["NUM_PROXIES"]` | A hospedagem, antes de expor a API ([D-109](decisoes/D-109-toda-rota-da-api-tem-taxa.md)) |
| ~~**O campo `recommended` do Biome está descontinuado.** `npm run lint` emite `DEPRECATED — use "preset" instead` e sai 0~~ | ~~`frontend/biome.json`, campo `linter.rules.recommended`~~ | ✅ **quitada no M1.6d** — `"preset": "recommended"`, e `frontend/tests/biome.test.ts` reprova o campo antigo de volta |
| **A linha de base numérica não é portátil entre plataformas.** 8 das 64 do motor reprovam em Linux — remedido em 2026-09-15 no `worker` desta máquina, com as mesmas versões de biblioteca do Windows. O `garch_1_1` desvia ~2,1e-6, no limiar da tolerância — aritmética de BLAS. O EGARCH cai em **outro ótimo local**: a série da linha de base é ruído i.i.d. sem estrutura EGARCH, a superfície é quase plana, e no próprio Windows o VaR sobe de 8% a 113% no primeiro bloco. O que era **defeito** — o reajuste não convergia em Linux (`code 4`, VaR de 2032%) — foi pago pela [D-46](decisoes/D-46-ajuste-garch-tenta-de-novo-quando-nao-converge.md). O lock congela **versão, não plataforma**. (As medidas de Linux são do motor `0.3.0`; não foram refeitas no `0.4.0`.) | `engine/tests/baseline/valores.json`, capturado no Windows | **Não se paga: se aceita.** Desde o M1.4b a linha de base é a do motor `0.4.0`, não mais a paridade com o protótipo VaR Lab nas cinco famílias corrigidas, e se regenera por `engine/tests/baseline/capturar.py`, no hospedeiro Windows ([D-159](decisoes/D-159-a-linha-de-base-numerica-e-a-do-motor-0-4-0-restringe-a-d-44.md)). Ela prova que o motor não muda sem querer, e não é referência de EGARCH. A CI segue rodando o motor **sem** ela ([spec F5](specs/F5-integracao-continua.md#a-linha-de-base-não-é-portátil-entre-plataformas)); a Etapa 6 gera a referência dela própria, em contêiner ([D-22](decisoes/D-22-treino-centralizado-em-container.md)) |
| ~~**A busca diferencia acento.** "itaú" não acha nada: o catálogo grava "ITAU", e a busca casa sem caixa, mas com acento~~ | ~~`backend/apps/api/views.py`, a busca do RF-12 do M1.6a~~ | ✅ **quitada no M1.7** — o lookup `unaccent` do Django, bilateral, no nome e no nome de pregão, com a extensão criada pela `apps/assets/migrations/0004_unaccent.py`; o banco de produção precisa dela ([D-143](decisoes/D-143-a-busca-ignora-acento-pelo-unaccent.md)) |
| ~~**O setor da B3 vem com ponto no lugar da vírgula** ("Petróleo. Gás e Biocombustíveis"), e a tela mostra como chega~~ | ~~`silver.asset.sector`, a conformação do M1.1~~ | ✅ **quitada no M1.7**, na **saída da API**, não na conformação: a tabela fechada de `apps/assets/classification.py` corrige cinco textos e deixa os dois de abreviação; o `silver` e o `gold.peer_comparison` seguem com o texto da B3, e o relatório do `import_assets` conta o texto com ponto fora da tabela ([D-144](decisoes/D-144-a-classificacao-da-b3-se-corrige-na-saida-da-api-estende-a-d-47.md)) |
| ~~**A sugestão da busca é uma lista fixa** dos ativos com risco (`frontend/src/content/sugestoes.ts`), e envelhece: o `AALR3` ganhou risco na execução real e não está nela. O roteiro da execução real tem uma cópia da lista~~ | ~~`frontend/src/content/sugestoes.ts`, `frontend/e2e/capturas.mjs`~~ | ✅ **quitada no M1.7** — não por `has_prices`, mas por `has_risk` (a fechada mais recente `ok` ou `partial`, a regra da tela): a caixa de página pede `has_risk=true&limit=8` uma vez por montagem; `sugestoes.ts` saiu, e o `MIN_SESSIONS` foi para `frontend/src/risk/config.ts`; o roteiro confere a sugestão contra a API |
| ~~**O `aria-live` da seção de risco envolve a seção inteira**: na passagem do cálculo para o resultado, o leitor de tela pode anunciar a tabela toda~~ | ~~`frontend/src/components/RiskSection.tsx`~~ | ✅ **quitada no M1.6d** — uma região `ruvor-sr-only`, sempre montada, só com o andamento; Fundamentos e Comunicados perderam o `aria-live` do embrulho |
| ~~**O roteiro da execução real não reprova por erro de página** — junta os `pageerror` sem conferir~~ | ~~`frontend/e2e/capturas.mjs`~~ | ✅ **quitada no M1.6c** (T8, `f00f3d2`) |
| **`comportamento.nota.retornos` afirma o que o código não ancora**: diz que o preço ajustado "já inclui proventos e desdobramentos", e o ajuste vem pronto da fonte, sem regra própria no código. Achado na conferência técnica do M2.3 (T5) e deixado fora pelo dono no portão da T6, porque a frase não é das 55 nem das três emendas | `frontend/src/content/textos.ts`, `comportamento.nota.retornos` | Num bloco que corrija o texto da iniciante, ou quando a conformação do preço documentar o ajuste |
| **A taxa do anônimo aceitou 81 pedidos com o limite em 60 por minuto** (execução real do M1.6c). Hipótese não provada: o `SimpleRateThrottle` do DRF conta sem atomicidade sob o `runserver` concorrente. E, com a taxa certa, a tela do ativo aguenta **5 cargas por minuto** a um anônimo em desenvolvimento | `backend/apps/accounts/throttling.py` (frente `identidade`), `RUVOR_THROTTLE_ANON` | Antes de expor a aplicação: a `identidade` confirma a contagem, e a hospedagem decide a taxa e se a tela junta rotas |
| **O V-04 é verificação manual.** O primeiro trecho das três redes igual à referência — recapturada no `0.4.0` pelo M1.4b, com o `lstm` e o `gru` iguais aos do `0.2.0` e só o `garchnet` mudado (`engine/tests/test_redes_trecho0.py`) só roda no `worker`, onde `RUVOR_REFERENCE_ENV=worker`; fora dele pula com motivo. **Nenhum job da CI o roda** — o `backend` roda só `backend/tests`, e o `motor` roda no Linux da CI, que não é o do `worker` | `engine/tests/test_redes_trecho0.py`, `engine/tests/fixtures/redes_trecho0.json` | **Não se paga: se roda à mão** — `docker compose exec -T worker python -m pytest /repo/engine/tests/test_redes_trecho0.py` — em toda mudança que possa alterar o que o motor calcula, como a linha de base |
| **A prova por seção no avançado cobre só 2 das 6 chaves do estresse** (revisão da PR #37, do M3.3, achado médio): a prova de que cada chave da seção sai na avançada e nunca na iniciante, como a do M2.3 para as outras seções, só exerce `period_return` e `benchmark_recovery_sessions` das seis medidas do estresse | `frontend/tests/estresse.test.tsx` | No próximo bloco que tocar o `StressBlock` ou as frases do estresse |
| **Dois ramos do índice no estresse sem teste** (revisão da PR #37, achado médio): `benchmark_drawdown = 0` e `benchmark_recovery_sessions = null`, no Ibovespa do episódio, não são exercidos | `frontend/src/components/StressBlock.tsx`, `frontend/tests/estresse.test.tsx` | Idem |
| **A mensagem de semelhança da senha cita o campo em inglês** ("…parecida com name", "…parecida com email"): o cadastro e a troca de senha do M2.1b mostram as mensagens de `details.fields` como a API as manda, e o validador do Django usa o nome do campo, porque `User.name` e `User.email` não têm `verbose_name` | `backend/apps/accounts/models.py` (frente `identidade`) | Quando a `identidade` puser o `verbose_name` em português nos dois campos — pedido registrado no fecho do M2.1b |
| **O pacote do build do frontend passou de 500 kB** (510,60 kB na T12 do M2.1b): o Vite só avisa, e o build sai 0 | `frontend/`, `npm run build` | Quando o tempo de carga pedir, com divisão por rota |
| **Os menores da revisão da PR #37:** "1 pregões" (o plural de `comportamento.estresse.pregoes` com *n* = 1); o `data-field` da célula "Sem dado"; a tabela de chaves do plano do M3.3 (o portão aprovou duas chaves fora dela); e o registro da frente `marco1` sem as PRs #33 e #36 | `frontend/src/content/textos.ts`, `frontend/src/components/StressBlock.tsx`, `docs/planos/M3.3-estresse-historico.md`, `docs/frentes/marco1.md` | Num bloco de acabamento da `marco1` |

## Aberto e aguardando decisão

| Tema | Onde |
|---|---|
| **A política de retenção dos retratos** — nada apaga retrato: cada invalidação cria uma linhagem nova (~3,1 MiB por ativo) e a antiga fica. Apagar é `delete` em `gold`, que a [D-16](decisoes/D-16-resultado-e-imutavel.md) proíbe, e precisa de decisão própria, com a taxa de invalidação medida em dia útil — o fecho do M1.5b mediu zero numa coleta de domingo, e estimou que cada provento invalida a linhagem inteira | [spec M1.5b](specs/M1.5b-treino-separado-da-previsao.md#os-retratos-se-acumulam-e-nada-os-apaga), [D-77](decisoes/D-77-os-retratos-moram-em-gold-com-impressao-digital-estrita.md) |
| Carteira: caminho barato ou caro | [PRODUTO.md](PRODUTO.md#6-restrições-de-produto) |
| Política de cobertura e atualização de ativos | [PRODUTO.md](PRODUTO.md#8-pendências-de-produto) |
| Hospedagem de produção | [ARQUITETURA.md](ARQUITETURA.md#ambientes) |
| ~~**A zona de Basileia a 5% pode estar errada** — na execução real do M1.6a, os 18 resultados do `BBDC4` saíram com `basel_zone` `verde`, inclusive o `historical` a 5% com **159 violações para 111,85 esperadas**. Possível defeito na zona de Basileia do M1.4 para o nível de 5%. **Não investigado**; o veredito de adequação não usa a zona ([D-64](decisoes/D-64-veredito-de-adequacao-e-kupiec-e-christoffersen.md)), mas ela é gravada e o `/risk` a expõe. **A tela do M1.6b não a mostra** até a investigação. As 159 violações do `historical` têm explicação provável na entrada dos tradicionais, abaixo: o VaR deles é o do primeiro ano, constante no teste inteiro~~ — ✅ **fechada no M1.4b (RF-15), sem defeito:** no ITUB4, sobre o motor `0.4.0`, nos dois níveis, a zona recalculada pelas violações dos últimos 250 dias bate com a gravada nos 18 resultados. A suspeita comparava as violações do teste inteiro, que o Kupiec usa, com a zona, que olha só 250 dias. Mostrar a zona na tela é decisão de outro bloco | ~~[spec M1.4](specs/M1.4-motor-de-risco.md), [ESTADO, M1.6a](#m16a--fundação-da-aplicação)~~; [ESTADO, M1.4b](#m14b--correção-do-motor), [spec M1.4b, RF-15](specs/M1.4b-correcao-do-motor.md#rf-15) |
| ~~**O GARCH e o EGARCH usam o retorno do próprio dia na previsão** (achado na conferência do M2.3, 2026-10-02, não investigado). Em `_sigma_path`, `fixed.forecast(start=n_train + pos, horizon=1, …)` devolve na primeira linha a previsão **para o dia seguinte** a `n_train + pos`, já condicionada ao retorno desse dia; ela é gravada em `sigma_1d[pos]` e o backtest a compara com o retorno de `pos`. Se confirmado, o VaR do dia vê o próprio retorno (olhar à frente de um dia), e os backtests dos dois modelos ficam otimistas; o GARCHNet, que recebe a mesma série por `full_sigma_series` (`engine/src/engine/models/ml/garchnet.py:30`), pode herdar o desvio. Mexer é mudar o motor, sob a [D-21](decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) e a [D-76](decisoes/D-76-alteracao-no-motor-em-lista-fechada-restringe-a-d-21.md)~~ — ✅ **fechada no M1.4b**: confirmado (a linha *k* do `forecast` é a variância de *k* + 1, com o retorno de *k*) e corrigido — `_sigma_path` prevê a σ do dia `pos` com os retornos até `pos − 1`; o `garchnet` recebe a série corrigida. Com a correção, as violações dos dois sobem para perto das esperadas | ~~`engine/src/engine/models/garch/_conditional.py:115`; `engine/src/engine/experiments/runner.py:110` (o alinhamento com o retorno do teste)~~; [D-157](decisoes/D-157-alteracao-no-motor-em-lista-fechada-para-a-correcao-do-m1-4b-restringe-a-d-76.md), [D-158](decisoes/D-158-o-var-do-dia-nao-usa-o-retorno-do-dia-e-os-tradicionais-reestimam-a-cada-252-pregoes-restringe-a-d-97.md), [ESTADO, M1.4b](#m14b--correção-do-motor) |
| ~~**Os três tradicionais são ajustados só nos 252 primeiros retornos, e o VaR deles é constante no teste inteiro** (achado na conferência do M2.3, 2026-10-02). O `run_experiment` treina cada modelo uma vez em `returns.iloc[:252]`, e o `historical` (como o `parametric` e o `monte_carlo`) devolve o mesmo número para todo dia do teste. **O "número de hoje" deles vem do primeiro ano da série**, dez anos atrás. É a explicação provável das 159 violações do `historical` do `BBDC4` na entrada da zona de Basileia, acima; as duas se investigam juntas. Mexer é mudar o motor (D-21, D-76)~~ — ✅ **fechada no M1.4b**: os três reestimam a cada 252 pregões, numa janela que cresce desde o primeiro retorno; o `historical` a 5% do `BBDC4` passou de 159 a 112 violações | ~~`engine/src/engine/experiments/runner.py:87` e `:93`; `engine/src/engine/models/traditional/historical.py:24`~~; [D-158](decisoes/D-158-o-var-do-dia-nao-usa-o-retorno-do-dia-e-os-tradicionais-reestimam-a-cada-252-pregoes-restringe-a-d-97.md), [ESTADO, M1.4b](#m14b--correção-do-motor) |

## Pendências que bloqueiam trabalho futuro

| Pendência | Bloqueia |
|---|---|
| **Parecer sobre fronteira CVM** | Só a comercialização — cobrar, ou abrir a plataforma a terceiros como serviço. Não segura a carteira nem bloco nenhum do roadmap ([D-160](decisoes/D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md)) |
| **Verificação de marca e domínio "Ruvor"** | Nada agora; risco se descoberto tarde |
| **Medir o gargalo do treino** | Decisão sobre GPU vs paralelização — ver [D-20](decisoes/D-20-experimentos-em-cpu.md) |

---

## Trilha paralela — TCC

Independente da plataforma, é tempo de máquina. Sequência obrigatória:

1. ~~Fixar a semente das redes neurais~~ — ✅ **feito no M1.4**
   ([D-63](decisoes/D-63-semente-fixa-entra-no-manifesto.md))
2. Refazer a Tabela 1 — os números atuais vieram de execução **sem** semente
3. Executar a Etapa 6
4. Escrever §4.5 e o Capítulo 5

O motor roda por linha de comando (`ruvor run`) e a semente está fixa, então **o passo 1 não
bloqueia mais nada**. Uma medição do M1.4 muda a expectativa de custo: os nove modelos sobre
quatro ativos e dois níveis levaram **8,5 min** sequenciais em CPU pelo caminho do
`run_experiment` — muito abaixo da estimativa de ~1 h que a Etapa 6 carrega. Não é a mesma
carga, mas convém remedir antes de planejar paralelização.

**Desde o M1.5b o motor é o `0.3.0`**, e as três redes semeiam em cada retreino
([D-75](decisoes/D-75-as-redes-semeiam-em-cada-retreino-estende-a-d-63.md)): os números delas
mudam a partir do segundo trecho de teste. A Etapa 6, que ainda não rodou, rodará sobre o `0.3.0`.

**Desde o M1.4b o motor é o `0.4.0`**, e a Etapa 6 roda sobre ele
([D-157](decisoes/D-157-alteracao-no-motor-em-lista-fechada-para-a-correcao-do-m1-4b-restringe-a-d-76.md)): o GARCH e o
EGARCH não veem mais o retorno do próprio dia, e os três tradicionais reestimam a cada 252 pregões, numa janela que
cresce. **As Tabelas 1 e 2 de `docs/tcc/TCC_II_VaR_ML_v3.md` e a conclusão preliminar de que o GARCH e o EGARCH ganham
dos "tradicionais estáticos" saíram do motor com os dois defeitos** e precisam ser refeitas nesta trilha, sobre o
`0.4.0`. Na plataforma, nos seis ativos cobertos, o GARCH e o EGARCH tinham violações de menos, e os tradicionais
erravam para os dois lados (ver o [fecho do M1.4b](#m14b--correção-do-motor)). O `lstm`, o `gru` e o `caviar` não mudam.

Ver [ROADMAP.md](ROADMAP.md#trilha-paralela--tcc).
