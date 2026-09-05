# Estado atual

> **Primeira leitura de qualquer sessão.** Diz onde paramos e o que está aberto.
> Atualizado ao fim de cada sessão de trabalho.

**Última atualização:** 2026-09-05

---

## Onde estamos

**Marco:** Fundação
**Bloco:** F3 fechado e integrado; **F4 é o próximo**
**Ramo:** trabalho direto na `main` ([D-31](decisoes/D-31-trabalho-direto-na-main.md))

Existem o motor numérico, o casco da aplicação, o **ambiente local em contêiner** e a
**fundação de dados**. `docker compose up` sobe cinco serviços; o Django conecta no
PostgreSQL e tem fila Celery sobre Redis. `migrate` num banco vazio cria os quatro esquemas
— `core`, `bronze`, `silver` e `gold` —, as tabelas `core.organization` e `core.user` e a
organização fixa do Marco 1 (`slug` `ruvor`). Ainda não há API de negócio nem tela de
produto, e `bronze`, `silver` e `gold` seguem vazios até o M1.2 e o M1.4.

**O dia a dia de `backend/` e `frontend/` roda dentro do contêiner**
([D-33](decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)); o motor segue no `.venv/` nativo.
Consequência que engana quem não sabe: **`pytest backend` no hospedeiro reprova um teste**, de
propósito — o `settings_test.py` fixa valores de banco inexistentes para que um `.env`
incompleto não passe despercebido. Não é regressão.

## O que foi concluído

### Documentação e processo (F1)

- **Produto** — [PRODUTO.md](PRODUTO.md): as cinco camadas, público, marcos, requisitos candidatos
- **Arquitetura** — [ARQUITETURA.md](ARQUITETURA.md): pilha, estrutura, banco, execução, auditoria, regimes
- **Processo** — [PROCESSO.md](PROCESSO.md): ciclo, anatomia de spec e plano, agentes, portões
- **36 decisões registradas** — [decisoes/](decisoes/)
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

## Próximo passo

**Escrever a spec do F4 — Fundação de dados**: primeiras migrations, esquemas bronze/prata/ouro
([D-13](decisoes/D-13-camadas-bronze-prata-ouro.md)) e a entidade Organização desde a primeira
migration ([D-24](decisoes/D-24-organizacao-desde-a-primeira-migration.md)).

O F4 herda um ambiente em que o Django já conecta no banco, então ele cria migrations sobre
conexão que funciona — e herda também a versão maior do Postgres, fixada em
[D-36](decisoes/D-36-versao-do-postgres.md). A escolha de `INSTALLED_APPS` se justificou lá:
hoje ele tem `django.contrib.contenttypes`, `django.contrib.auth` e `apps.accounts` ao lado
do `rest_framework`.

Depois vem o F5 (CI), que **espelha o contêiner, não o `.venv`**.

---

## Dívida registrada

| Dívida | Onde | Quando se paga |
|---|---|---|
| `ignore_errors` do mypy em `engine.models.ml._quantile_nn` e `engine.models.garch._conditional` | `engine/pyproject.toml`, comentado no próprio arquivo | Depois da Etapa 6, quando a [D-21](decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) deixar de congelar o motor |
| ~~`RUVOR_ALLOWED_HOSTS` não tolera espaço após a vírgula~~ | ~~`backend/config/settings.py`~~ | ✅ **quitada no F3** — virou a função `_split_hosts`, com cinco testes e mutação provada |
| Tarefa Celery é `Any` sob o mypy, porque o Celery não publica tipos | `backend/config/tasks.py`, comentado no próprio arquivo | Quando houver tarefas o bastante para pagar pelo pacote `celery-types` — M1.5 |
| **Não há filtro automático por organização.** O F4 entregou a coluna; o mecanismo que faz a consulta filtrar sozinha não existe — e sem ele, "coluna sem filtro é teatro" | `backend/apps/accounts/models.py` (`User.organization`) | **M2.2**, o bloco que cria a primeira tabela privada de domínio: é obrigação dele, não dívida difusa — [D-41](decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md). O `user` é **exceção permanente**, e o M2.1 precisa isolar listagem de usuário por outro meio |

## Aberto e aguardando decisão

| Tema | Onde |
|---|---|
| Carteira: caminho barato ou caro | [PRODUTO.md](PRODUTO.md#6-restrições-de-produto) |
| Quais requisitos candidatos entram no Marco 1 | [PRODUTO.md](PRODUTO.md#5-requisitos-candidatos) |
| Política de cobertura e atualização de ativos | [PRODUTO.md](PRODUTO.md#8-pendências-de-produto) |
| Hospedagem de produção | [ARQUITETURA.md](ARQUITETURA.md#ambientes) |
| Tema claro vs escuro | kit é claro; decisão de produto pendente |
| **Ferramenta de estilo** | Tem dono: a **spec do F5** escolhe (ruff? prettier? eslint?). O F2b registrou a decisão de não escolher — [plano F2b, "O que este plano decide"](planos/F2b-casco-da-aplicacao.md#o-que-este-plano-decide) |
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
