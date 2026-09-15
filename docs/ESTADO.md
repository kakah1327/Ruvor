# Estado atual

> **Primeira leitura de qualquer sessão.** Diz onde paramos e o que está aberto.
> Atualizado ao fim de cada sessão de trabalho.

**Última atualização:** 2026-09-15

---

## Onde estamos

**Marco:** ✅ **Fundação fechada** — sete blocos, do F1 ao F5
**Bloco:** F5 fechado e integrado; **o M1.1 é o próximo**, e abre o Marco 1
**Ramo:** trabalho direto na `main` ([D-31](decisoes/D-31-trabalho-direto-na-main.md))

Existem o motor numérico, o casco da aplicação, o **ambiente local em contêiner** e a
**fundação de dados**. `docker compose up` sobe cinco serviços; o Django conecta no
PostgreSQL e tem fila Celery sobre Redis. `migrate` num banco vazio cria os quatro esquemas
— `core`, `bronze`, `silver` e `gold` —, as tabelas `core.organization` e `core.user` e a
organização fixa do Marco 1 (`slug` `ruvor`). Ainda não há API de negócio nem tela de
produto, e `bronze`, `silver` e `gold` seguem vazios até o M1.2 e o M1.4.

**Existe CI.** Cada push na `main` dispara quatro trabalhos em máquina limpa — `estilo`,
`backend`, `frontend` e `motor` —, e a primeira execução ficou verde nos quatro. Ela
**avisa e não bloqueia** ([D-42](decisoes/D-42-ci-avisa-e-nao-bloqueia.md)); com trabalho
direto na `main`, não há onde barrar. `ruff` cobre os dois projetos Python, `Biome` cobre o
frontend, e o motor entrou no estilo com a formatação provada por árvore sintática
([D-44](decisoes/D-44-o-motor-entra-no-estilo.md)).

**O dia a dia de `backend/` e `frontend/` roda dentro do contêiner**
([D-33](decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)); o motor segue no `.venv/` nativo.
Consequência que engana quem não sabe: **`pytest backend` no hospedeiro reprova cinco
testes**, de propósito — o `settings_test.py` fixa valores de banco inexistentes para que um
`.env` incompleto não passe despercebido. Era um até o F3; o F4 acrescentou quatro que leem o
banco. **Dentro do contêiner eles também exigem `migrate` aplicado.** Não é regressão.

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

## Próximo passo

**Escrever a spec do M1.1 — Catálogo de ativos**, que abre o Marco 1 e é o primeiro código de
domínio de verdade: lista de papéis da B3 com nome, setor e situação, base da busca.

Ele é o primeiro consumidor do que a Fundação deixou pronto — os esquemas e a convenção de
migration do F4, o estilo e a CI do F5 — e o primeiro a povoar a camada `bronze`, que nasceu
vazia.

Duas coisas mudam de natureza a partir daqui. **O M1.1 tem tela?** Não: catálogo é dado, e a
tela do ativo é o M1.6. Mas do M1.6 em diante vale o
[portão de mockup](PROCESSO.md#7-portão-de-mockup), e o kit de marca ainda está incompleto —
faltam estados de interação e modo escuro. **E a partir do M1.2 acaba a reversibilidade
barata:** com preços dentro, mudar esquema, nome de tabela ou modelo de usuário passa a exigir
migração de dados.

---

## Dívida registrada

| Dívida | Onde | Quando se paga |
|---|---|---|
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
