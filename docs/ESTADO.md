# Estado atual

> **Primeira leitura de qualquer sessão.** Diz onde paramos e o que está aberto.
> Atualizado ao fim de cada sessão de trabalho.

**Última atualização:** 2026-09-22

---

## Onde estamos

**Marco:** 🟡 **Marco 1** — a ação, e o risco dela; a Fundação fechou em 2026-09-08
**Bloco:** M1.2 fechado; **o M1.3 é o próximo**
**Ramo:** trabalho direto na `main` ([D-31](decisoes/D-31-trabalho-direto-na-main.md))

Existem o motor numérico, o casco da aplicação, o **ambiente local em contêiner** e a
**fundação de dados**. `docker compose up` sobe cinco serviços; o Django conecta no
PostgreSQL e tem fila Celery sobre Redis. `migrate` num banco vazio cria os quatro esquemas
— `core`, `bronze`, `silver` e `gold` —, as tabelas `core.organization` e `core.user` e a
organização fixa do Marco 1 (`slug` `ruvor`), as quatro tabelas da `bronze`, e `silver.asset`,
`silver.price` e `silver.corporate_event`. `manage.py import_assets` consulta a B3 e conforma o **catálogo de ações**:
473 na coleta de 2026-09-21. `manage.py import_prices` consulta o Yahoo e conforma
`silver.price` e `silver.corporate_event`: dez anos de PETR4, VALE3, ITUB4 e Ibovespa, ~2.490
pregões cada, com retorno logarítmico. Ainda não há API de negócio nem tela de produto; `gold` segue
vazio até o M1.3.

**Existe CI.** Cada push na `main` dispara quatro trabalhos em máquina limpa — `estilo`,
`backend`, `frontend` e `motor` —, e a primeira execução ficou verde nos quatro. Ela
**avisa e não bloqueia** ([D-42](decisoes/D-42-ci-avisa-e-nao-bloqueia.md)); com trabalho
direto na `main`, não há onde barrar. `ruff` cobre os dois projetos Python, `Biome` cobre o
frontend, e o motor entrou no estilo com a formatação provada por árvore sintática
([D-44](decisoes/D-44-o-motor-entra-no-estilo.md)).

**O dia a dia de `backend/` e `frontend/` roda dentro do contêiner**
([D-33](decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)); o motor segue no `.venv/` nativo.
Consequência que engana quem não sabe: **`pytest backend` no hospedeiro reprova cinco
testes e dá erro em quarenta e nove**, de propósito — o `settings_test.py` fixa valores de banco
inexistentes para que um `.env` incompleto não passe despercebido. Os cinco leem o banco
configurado; os quarenta e nove são os de `assets`, com `django_db`, que nem conseguem criar o banco de
teste. **Dentro do contêiner os cinco exigem `migrate` aplicado.** Não é regressão.

## O que foi concluído

### Documentação e processo (F1)

- **Produto** — [PRODUTO.md](PRODUTO.md): as cinco camadas, público, marcos, requisitos candidatos
- **Arquitetura** — [ARQUITETURA.md](ARQUITETURA.md): pilha, estrutura, banco, execução, auditoria, regimes
- **Processo** — [PROCESSO.md](PROCESSO.md): ciclo, anatomia de spec e plano, agentes, portões
- **45 decisões registradas** — [decisoes/](decisoes/)
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
`run_import_prices`. Trocar `full=full` por `full=False` no comando passaria a suíte.

## Próximo passo

**Escrever a spec do M1.3 — Camadas 1 e 2**: identidade, preço, gráfico, volume, dividendos,
retornos por janela, volatilidade, maior queda e recuperação, relação com o Ibovespa. É o
primeiro bloco que **calcula** em vez de coletar, e o primeiro a povoar `gold`. Lê
`silver.price` e `silver.corporate_event`; escreve métricas de comportamento por ativo.

Perguntas que a spec encontra na porta: **onde o cálculo roda** — `manage.py` síncrono como os
dois blocos anteriores, ou já pela fila (o M1.5 é o bloco da execução assíncrona)? — e **o que
é uma métrica em `gold`**: uma linha por ativo recalculada, ou uma linha por (ativo, data de
cálculo), imutável como a [D-16](decisoes/D-16-resultado-e-imutavel.md) manda para resultado?
A segunda é a leitura da ARQUITETURA; a spec precisa dizer.

**A reversibilidade barata acabou:** `silver.price` tem ~10 mil linhas e aponta para `asset`.
`migrate assets zero` ainda funciona, mas custa uma coleta real para voltar.

---

## Dívida registrada

| Dívida | Onde | Quando se paga |
|---|---|---|
| **Ações de balcão organizado (SOMA) ficam fora do catálogo.** 8 companhias com `hasQuotation=S` têm código com sufixo `B` (`EQMA3B`, `MRSA3B`, `LTEL3B`, `PRMN3B`...), que o regex do RF-05 exclui; 44 outras vêm com `otherCodes: null`. Estão na `bronze`, não na `silver` | `backend/apps/assets/conform.py`, `EQUITY_CODE` | Quando o produto decidir se balcão entra — é decisão de cobertura (D-19); mudar o regex é uma linha e o relatório do `import_assets` já conta os casos |
| **`listing_segment` nulo em 192 das 473 ações.** O `market` da listagem da B3 vem vazio para a maioria das companhias; só NM/N1/N2 vêm preenchidos | `silver.asset.listing_segment` | Quando a tela precisar do segmento — a fonte alternativa é o `market` por extenso do detalhe (`"BOVESPA NIVEL 2"`), que a spec do M1.1 decidiu não usar |
| `ignore_errors` do mypy em `engine.models.ml._quantile_nn` e `engine.models.garch._conditional` | `engine/pyproject.toml`, comentado no próprio arquivo | Depois da Etapa 6, quando a [D-21](decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) deixar de congelar o motor |
| ~~`RUVOR_ALLOWED_HOSTS` não tolera espaço após a vírgula~~ | ~~`backend/config/settings.py`~~ | ✅ **quitada no F3** — virou a função `_split_hosts`, com cinco testes e mutação provada |
| Tarefa Celery é `Any` sob o mypy, porque o Celery não publica tipos | `backend/config/tasks.py`, comentado no próprio arquivo | Quando houver tarefas o bastante para pagar pelo pacote `celery-types` — M1.5 |
| **Não há filtro automático por organização.** O F4 entregou a coluna; o mecanismo que faz a consulta filtrar sozinha não existe — e sem ele, "coluna sem filtro é teatro" | `backend/apps/accounts/models.py` (`User.organization`) | **M2.2**, o bloco que cria a primeira tabela privada de domínio: é obrigação dele, não dívida difusa — [D-41](decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md). O `user` é **exceção permanente**, e o M2.1 precisa isolar listagem de usuário por outro meio |
| **`createsuperuser` não funciona.** O gerente exige organização e o comando não tem como fornecê-la: pôr `organization` em `REQUIRED_FIELDS` faria o `create_superuser` receber a **chave crua**, porque `ForeignKey.clean` devolve a pk (`createsuperuser.py:150,233`). Falha com `ValueError: o usuario precisa de organizacao` | `backend/apps/accounts/managers.py`, comentado no próprio arquivo | **M2.1**, que constrói o fluxo de identidade e decide como um primeiro usuário nasce. Enquanto isso, criar usuário exige `shell` |
| **O campo `recommended` do Biome está descontinuado.** `npm run lint` emite `DEPRECATED — use "preset" instead` e sai 0, então não quebra hoje. Quebra no dia em que alguém subir a versão maior do Biome, e aí a CI reprova por configuração, não por código | `frontend/biome.json`, campo `linter.rules.recommended` | quando o Biome for atualizado — o pino é exato (`2.5.12`), então não acontece sozinho |
| **A linha de base numérica não é portátil entre plataformas.** 8 das 64 do motor reprovam em Linux — remedido em 2026-09-15 no `worker` desta máquina, com as mesmas versões de biblioteca do Windows. O `garch_1_1` desvia ~2,1e-6, no limiar da tolerância — aritmética de BLAS. O EGARCH cai em **outro ótimo local**: a série da linha de base é ruído i.i.d. sem estrutura EGARCH, a superfície é quase plana, e no próprio Windows o VaR sobe de 8% a 113% no primeiro bloco. O que era **defeito** — o reajuste não convergia em Linux (`code 4`, VaR de 2032%) — foi pago pela [D-46](decisoes/D-46-ajuste-garch-tenta-de-novo-quando-nao-converge.md). O lock congela **versão, não plataforma** | `engine/tests/baseline/valores.json`, capturado no Windows | **Não se paga: se aceita.** A linha de base provou a migração no F2a e não é referência de EGARCH. A CI segue rodando o motor **sem** ela ([spec F5](specs/F5-integracao-continua.md#a-linha-de-base-não-é-portátil-entre-plataformas)); a Etapa 6 gera a referência dela própria, em contêiner ([D-22](decisoes/D-22-treino-centralizado-em-container.md)) |

## Aberto e aguardando decisão

| Tema | Onde |
|---|---|
| Carteira: caminho barato ou caro | [PRODUTO.md](PRODUTO.md#6-restrições-de-produto) |
| Quais requisitos candidatos entram no Marco 1 | [PRODUTO.md](PRODUTO.md#5-requisitos-candidatos) |
| Política de cobertura e atualização de ativos | [PRODUTO.md](PRODUTO.md#8-pendências-de-produto) |
| Hospedagem de produção | [ARQUITETURA.md](ARQUITETURA.md#ambientes) |
| Tema claro vs escuro | kit é claro; decisão de produto pendente |
| **Escala tipográfica nos tokens** | `tokens.css` não define tamanho de fonte. O casco não declara `font-size` nenhum; a primeira tela de produto (Marco 1) precisa que o kit decida |

## Pendências que bloqueiam trabalho futuro

| Pendência | Bloqueia |
|---|---|
| **Kit de marca incompleto** — faltam estados de interação (só `:active`) e modo escuro | O portão de mockup do Marco 1 |
| **Parecer sobre fronteira CVM** | Marco 2 (carteira) |
| **Verificação de marca e domínio "Ruvor"** | Nada agora; risco se descoberto tarde |
| **Medir o gargalo do treino** | Decisão sobre GPU vs paralelização — ver [D-20](decisoes/D-20-experimentos-em-cpu.md) |

---

## Trilha paralela — TCC

Independente da plataforma, é tempo de máquina. Nada iniciado. Sequência obrigatória:

1. Fixar a semente das redes neurais
2. Refazer a Tabela 1
3. Executar a Etapa 6
4. Escrever §4.5 e o Capítulo 5

O motor já roda por linha de comando (`ruvor run`), então a Etapa 6 pode ser executada assim
que a semente for corrigida.

Ver [ROADMAP.md](ROADMAP.md#trilha-paralela--tcc).
