# Estado atual

> **Primeira leitura de qualquer sessão.** Diz onde paramos e o que está aberto.
> Atualizado ao fim de cada sessão de trabalho.

**Última atualização:** 2026-09-24

---

## Onde estamos

**Marco:** 🟡 **Marco 1** — a ação, e o risco dela; a Fundação fechou em 2026-09-08
**Bloco:** M1.4 fechado em 2026-09-24; **o M1.5 é o próximo**
**Ramo:** trabalho direto na `main` ([D-31](decisoes/D-31-trabalho-direto-na-main.md))

Existem o motor numérico, o casco da aplicação, o **ambiente local em contêiner** e a
**fundação de dados**. `docker compose up` sobe cinco serviços; o Django conecta no
PostgreSQL e tem fila Celery sobre Redis. `migrate` num banco vazio cria os quatro esquemas
— `core`, `bronze`, `silver` e `gold` —, as tabelas `core.organization` e `core.user` e a
organização fixa do Marco 1 (`slug` `ruvor`), as quatro tabelas da `bronze`, e `silver.asset`,
`silver.price` e `silver.corporate_event`. `manage.py import_assets` consulta a B3 e conforma o **catálogo de ações**:
473 na coleta de 2026-09-21. `manage.py import_prices` consulta o Yahoo e conforma
`silver.price` e `silver.corporate_event`: dez anos de PETR4, VALE3, ITUB4 e Ibovespa, ~2.490
pregões cada, com retorno logarítmico. `manage.py compute_metrics` lê a `silver` e povoa a
`gold`: uma linha imutável de métricas de comportamento por ativo e execução, mais os 42
baldes do histograma de retornos. **`manage.py compute_risk`, no contêiner `worker`, é a
camada 3**: roda os nove modelos de VaR e os quatro backtests sobre `silver.price` e grava em
`gold` a execução com o manifesto e os dezoito resultados, cada um com o VaR, os quatro
testes e o veredito de adequação. Vinte tabelas. Ainda não há API de negócio nem tela de
produto.

**Existe CI.** Cada push na `main` dispara quatro trabalhos em máquina limpa — `estilo`,
`backend`, `frontend` e `motor` —, e a primeira execução ficou verde nos quatro. Ela
**avisa e não bloqueia** ([D-42](decisoes/D-42-ci-avisa-e-nao-bloqueia.md)); com trabalho
direto na `main`, não há onde barrar. `ruff` cobre os dois projetos Python, `Biome` cobre o
frontend, e o motor entrou no estilo com a formatação provada por árvore sintática
([D-44](decisoes/D-44-o-motor-entra-no-estilo.md)).

**O dia a dia de `backend/` e `frontend/` roda dentro do contêiner**
([D-33](decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)); o motor segue no `.venv/` nativo.
**Desde o M1.4 a suíte e o `mypy` do backend rodam no `worker`, não na `web`** — é o único
contêiner que tem o motor, e `apps/risk/` o importa (RF-16b). Consequência que engana quem
não sabe: **`pytest backend` no hospedeiro reprova cinco testes e dá erro em cento e nove**,
de propósito — o `settings_test.py` fixa valores de banco inexistentes para que um `.env`
incompleto não passe despercebido. Os cinco leem o banco configurado; os 109 são os que
pedem `django_db` e nem conseguem criar o banco de teste. **Dentro do contêiner os cinco
exigem `migrate` aplicado.** Não é regressão — medido em 2026-09-24, com 240 testes.

## O que foi concluído

### Documentação e processo (F1)

- **Produto** — [PRODUTO.md](PRODUTO.md): as cinco camadas, público, marcos, requisitos candidatos
- **Arquitetura** — [ARQUITETURA.md](ARQUITETURA.md): pilha, estrutura, banco, execução, auditoria, regimes
- **Processo** — [PROCESSO.md](PROCESSO.md): ciclo, anatomia de spec e plano, agentes, portões
- **66 decisões registradas** — [decisoes/](decisoes/)
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
[`planos/M1.4-motor-de-risco.md`](planos/M1.4-motor-de-risco.md). Dez tarefas e dez commits,
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

240 testes no backend e **98 no motor**; mypy (83 arquivos no backend, 34 no motor) e ruff
limpos nos dois; vinte tabelas.

**As dezesseis mutações reprovaram na primeira medição** — contadas no arquivo, não
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

## Próximo passo

**Escrever a spec do M1.5 — Execução assíncrona**: fila, modo A, pré-cálculo dos ativos
cobertos e agendamento das ingestões. É o bloco que a spec do M1.4 nomeou ao resolver a
divergência do ROADMAP sobre a fila.

O que ele já encontra pronto: o `compute_risk` síncrono, com transação por ativo e manifesto,
rodando em **~2 min por ativo** — o que muda a pergunta de "dá para esperar?" para "quando
recalcular?". E a `worker`, que desde o M1.4 é o contêiner onde a suíte inteira roda.

Perguntas que a spec encontra na porta: **o que dispara o recálculo** — ingestão nova de
preço, agenda, ou pedido do usuário; **o que o modo A devolve** enquanto o ML não terminou
([D-07](decisoes/D-07-resposta-progressiva-modo-a.md)); e **como a tarefa Celery carrega o
manifesto**, agora que ele existe.

**A reversibilidade barata acabou:** `silver.price` tem ~10 mil linhas e aponta para `asset`.
`migrate assets zero` ainda funciona, mas custa uma coleta real para voltar. **`gold` é a
exceção, e não é linha da tabela de dívida** — não procure lá: o que está lá é **derivado**,
`migrate analytics zero` / `migrate risk zero` apagam tudo, e uma execução de
`compute_metrics` reconstrói em 0,1 s, uma de `compute_risk` em 8,5 min. É a última vez no
Marco 1 em que isso vale.

---

## Dívida registrada

| Dívida | Onde | Quando se paga |
|---|---|---|
| **Ações de balcão organizado (SOMA) ficam fora do catálogo.** 8 companhias com `hasQuotation=S` têm código com sufixo `B` (`EQMA3B`, `MRSA3B`, `LTEL3B`, `PRMN3B`...), que o regex do RF-05 exclui; 44 outras vêm com `otherCodes: null`. Estão na `bronze`, não na `silver` | `backend/apps/assets/conform.py`, `EQUITY_CODE` | Quando o produto decidir se balcão entra — é decisão de cobertura (D-19); mudar o regex é uma linha e o relatório do `import_assets` já conta os casos |
| **`listing_segment` nulo em 192 das 473 ações.** O `market` da listagem da B3 vem vazio para a maioria das companhias; só NM/N1/N2 vêm preenchidos | `silver.asset.listing_segment` | Quando a tela precisar do segmento — a fonte alternativa é o `market` por extenso do detalhe (`"BOVESPA NIVEL 2"`), que a spec do M1.1 decidiu não usar |
| `ignore_errors` do mypy em `engine.models.ml._quantile_nn` e `engine.models.garch._conditional` | `engine/pyproject.toml`, comentado no próprio arquivo | Depois da Etapa 6, quando a [D-21](decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) deixar de congelar o motor |
| ~~`RUVOR_ALLOWED_HOSTS` não tolera espaço após a vírgula~~ | ~~`backend/config/settings.py`~~ | ✅ **quitada no F3** — virou a função `_split_hosts`, com cinco testes e mutação provada |
| **`gold.risk_run.requested_by` é sempre nulo, e a [D-15](decisoes/D-15-manifesto-de-execucao.md) fica cumprida pela metade.** Ela exige "a pedido de quem", e não há usuário autenticado antes do M2.1. A coluna nasceu anulável e nenhum caminho do código a preenche | `backend/apps/risk/models.py`, `RiskRun.requested_by` | **M2.1**, que constrói o fluxo de identidade. Não exige migration de dado: as execuções antigas legitimamente não têm autor |
| Tarefa Celery é `Any` sob o mypy, porque o Celery não publica tipos | `backend/config/tasks.py`, comentado no próprio arquivo | Quando houver tarefas o bastante para pagar pelo pacote `celery-types` — M1.5 |
| ~~**RF-14 não tinha verificação permanente.** Apagar `backend/tests/conftest.py` deixava a suíte inteira verde: o teste que provava a guarda era descartável, medido e removido pela T2~~ | ~~`backend/tests/`~~ | ✅ **quitada no fecho do M1.3** — `tests/test_guarda_de_rede.py`, com a mutação medida: sem a guarda, reprova |
| **O V-15 só existe enquanto alguém digita o comando.** "Sem dependência numérica nova" (RF-13) é verificado por `git diff` no `pyproject.toml` e `grep` por `numpy\|pandas`, rodados à mão na T4 e na T8. Nada na suíte nem na CI reprova quem acrescentar `numpy` amanhã — a imagem `web` cresceria e só alguém olhando notaria | `.github/workflows/ci.yml`, `backend/pyproject.toml` | Quando a CI ganhar uma verificação de dependência. **O M1.4 já respondeu a segunda metade:** o backend importa `pandas` em `apps/risk/provider.py` e **não o declara** — ele chega pelo motor, instalado só no `worker` —, então a `web` continua sem dependência numérica. O que segue sem guarda automática é o `pyproject.toml` |
| **Não há filtro automático por organização.** O F4 entregou a coluna; o mecanismo que faz a consulta filtrar sozinha não existe — e sem ele, "coluna sem filtro é teatro" | `backend/apps/accounts/models.py` (`User.organization`) | **M2.2**, o bloco que cria a primeira tabela privada de domínio: é obrigação dele, não dívida difusa — [D-41](decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md). O `user` é **exceção permanente**, e o M2.1 precisa isolar listagem de usuário por outro meio |
| **`createsuperuser` não funciona.** O gerente exige organização e o comando não tem como fornecê-la: pôr `organization` em `REQUIRED_FIELDS` faria o `create_superuser` receber a **chave crua**, porque `ForeignKey.clean` devolve a pk (`createsuperuser.py:150,233`). Falha com `ValueError: o usuario precisa de organizacao` | `backend/apps/accounts/managers.py`, comentado no próprio arquivo | **M2.1**, que constrói o fluxo de identidade e decide como um primeiro usuário nasce. Enquanto isso, criar usuário exige `shell` |
| **O campo `recommended` do Biome está descontinuado.** `npm run lint` emite `DEPRECATED — use "preset" instead` e sai 0, então não quebra hoje. Quebra no dia em que alguém subir a versão maior do Biome, e aí a CI reprova por configuração, não por código | `frontend/biome.json`, campo `linter.rules.recommended` | quando o Biome for atualizado — o pino é exato (`2.5.12`), então não acontece sozinho |
| **A linha de base numérica não é portátil entre plataformas.** 8 das 64 do motor reprovam em Linux — remedido em 2026-09-15 no `worker` desta máquina, com as mesmas versões de biblioteca do Windows. O `garch_1_1` desvia ~2,1e-6, no limiar da tolerância — aritmética de BLAS. O EGARCH cai em **outro ótimo local**: a série da linha de base é ruído i.i.d. sem estrutura EGARCH, a superfície é quase plana, e no próprio Windows o VaR sobe de 8% a 113% no primeiro bloco. O que era **defeito** — o reajuste não convergia em Linux (`code 4`, VaR de 2032%) — foi pago pela [D-46](decisoes/D-46-ajuste-garch-tenta-de-novo-quando-nao-converge.md). O lock congela **versão, não plataforma** | `engine/tests/baseline/valores.json`, capturado no Windows | **Não se paga: se aceita.** A linha de base provou a migração no F2a e não é referência de EGARCH. A CI segue rodando o motor **sem** ela ([spec F5](specs/F5-integracao-continua.md#a-linha-de-base-não-é-portátil-entre-plataformas)); a Etapa 6 gera a referência dela própria, em contêiner ([D-22](decisoes/D-22-treino-centralizado-em-container.md)) |

## Aberto e aguardando decisão

| Tema | Onde |
|---|---|
| **O regime de laboratório sai do Marco 1 — e ninguém decidiu isso.** A [PRODUTO §4](PRODUTO.md#4-marcos) promete a camada 3 **nos dois regimes** ([D-04](decisoes/D-04-dois-regimes-de-operacao.md)); o M1.4 entregou **só produção**, e **nenhum bloco do ROADMAP retoma o laboratório** — nem o M1.5, nem o M1.6. A spec do M1.4 assumiu "o Marco 1 é só produção" **para poder existir** e marcou como pendente de confirmação. Três saídas: (1) o Marco 1 vira só produção e nasce a decisão que restringe a PRODUTO; (2) nasce um **M1.7** para o laboratório; (3) o `ruvor run` é declarado suficiente e a PRODUTO é corrigida. **Enquanto ninguém escolher, adiar é descartar sem dizer** | [ROADMAP.md](ROADMAP.md#marco-1--a-ação-e-o-risco-dela), [PRODUTO.md](PRODUTO.md#4-marcos) |
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

Ver [ROADMAP.md](ROADMAP.md#trilha-paralela--tcc).
