# F3 — Plano de implementação

**Spec:** [F3 — Ambiente local](../specs/F3-ambiente-local.md)
**Status:** ✅ **executado e fechado** (2026-09-04) · dez tarefas, um commit cada, de
`e3e0cb5` a `36d9a4d`. Revisão final aprovada.

> ## O que a execução contrariou
>
> Anotado depois de executar, para que o plano não fique afirmando o que se mostrou falso.
> Nada disso mudou o resultado do bloco.
>
> | O plano dizia | O que se mediu |
> |---|---|
> | imagem `web` ≈ 330 MB, `worker` ≈ 3,2 GB | **467 MB** e **3,79 GB** — a verificação prévia mediu antes de a T3 acrescentar `psycopg`, `celery` e `redis` ao backend |
> | construção do `worker` em ~90 s | **122 s** |
> | *"se recarregar, não ligue [a sondagem]"* | **não recarregou.** O contêiner enxerga o arquivo alterado, mas o Vite não emite evento nenhum: a montagem Windows→contêiner não propaga o aviso. Sondagem ligada em `7a327b3` |
> | *"a unidade do sistema tem ~7 GB livres"* — risco de espaço | **aponta para a unidade errada.** Os dados do Docker estão no `E:`; durante a reconstrução de 3 GB da mutação **b**, o `C:` não se moveu |
> | mutação **a**: o `web` *"nem chega a ser criado"* | ele **é** criado, e fica em `Created` sem nunca iniciar. A substância se sustenta: `--wait` sai 1 |
> | mutação **d**: *"F3-04 reprova"* | reprova **duas** vezes — o `runserver` toca o banco no arranque, e o serviço já fica insalubre antes de o teste rodar |
> | T7: `ignore_missing_imports` resolveria o `mypy` | **insuficiente.** O `untyped-decorator` sobre `@app.task` sobrevive, porque o Celery virando `Any` não torna o decorador tipado. Resolvido sem suprimir nada, aplicando o decorador como chamada sobre função tipada |
>
> Dois vãos de plano, ambos meus e ambos consertados: a verificação de recarga a quente caiu
> entre a T5 (que não tinha conjunto de pé) e a T6 (cuja cerca proíbe tocar em `frontend/`); e
> o critério da T1 verifica **presença** de padrões, não identidade — uma linha a mais no
> `.dockerignore` passaria. O implementador supriu por conta própria com `diff` contra o bloco
> do plano, que é a verificação certa.

**Objetivo:** `docker compose up` na raiz sobe Postgres, Redis, web, worker e frontend, todos
saudáveis; o Django conecta no banco; uma tarefa enfileirada pelo `web` é executada pelo
`worker`; e a imagem `web` não consegue importar TensorFlow.

**Commit por tarefa**, direto na `main`
([D-31](../decisoes/D-31-trabalho-direto-na-main.md)). Sem ramo.

---

## Como ler este plano

Segue o [PROCESSO §5](../PROCESSO.md#5-anatomia-de-um-plano): **contratos, não corpos**, com as
duas exceções que a própria regra prevê. Este bloco é quase todo arquivo de configuração, e
aí *o conteúdo é o contrato* — `compose.yaml`, `.dockerignore`, os dois arquivos de construção
e o `.env.example` entram **literais e completos**, não descritos. As mudanças no Python
entram como assinatura e comportamento, não como corpo, porque há padrão no repositório para
imitar.

Toda tarefa é executável por alguém que nunca participou da conversa.

**Tudo o que este plano afirma sobre ferramenta foi executado antes de ser escrito**, num
projeto descartável em `E:\Temp\ruvor-f3-probe`, em 2026-09-03, contra Docker Engine 29.7.2 e
Compose v5.5.0. O projeto foi removido depois. Onde o plano diz "verificado", é isso que
significa — e a seção seguinte registra o que a verificação **contrariou**.

---

## O que a verificação prévia encontrou

Cinco achados que mudam o plano. Três deles teriam produzido falha ou critério vazio se o
plano tivesse sido escrito de memória.

### Achado 1: o Postgres 18 mudou o ponto de montagem

O volume vai em **`/var/lib/postgresql`**, e não em `/var/lib/postgresql/data`, que é o que
toda memória muscular e todo tutorial dizem. O `PGDATA` da imagem é
`/var/lib/postgresql/18/docker`.

Com o caminho antigo, **o contêiner recusa subir** — e a mensagem é boa:

```
Error: in 18+, these Docker images are configured to store database data in a
       format which is compatible with "pg_ctlcluster" [...]
       Counter to that, there appears to be PostgreSQL data in:
         /var/lib/postgresql/data (unused mount/volume)
```

Foi o primeiro erro da verificação. Vai para o [`aprendizados.md`](../aprendizados.md) no
passo FECHA.

### Achado 2: `.env` ausente nao faz o `compose` falhar

A spec prevê, na tabela de mutações, *"renomear o `.env` e exigir que a subida falhe"*.
Verificado: **não falha.**

| Cenário | Código de saída |
|---|---|
| `docker compose up -d` sem `.env`, com `${RUVOR_DB_NAME}` | **0** — só emite `variable is not set. Defaulting to a blank string` |
| O mesmo, com `${RUVOR_DB_NAME:?...}` | **1** — `required variable RUVOR_DB_NAME is missing` |

Consequência para o plano: **o `compose.yaml` declara as variáveis com a sintaxe de
obrigatoriedade `${VAR:?mensagem}`.** Sem isso, o critério de F3-06 passaria vazio — que é
exatamente o que ele existe para impedir. Não é contradição com a spec: é o que torna a
mutação que ela pede realmente executável.

### Achado 3: o TensorFlow decide a versao do Python

| Pacote | Versão | Python suportado |
|---|---|---|
| `tensorflow` | 2.21.0 | 3.10 – **3.13** |
| `django` | 6.1.1 | **3.12** – 3.14 |

A interseção é 3.12 ou 3.13, e a spec exige `python --version` **idêntico** nas duas imagens.
**Escolha: `python:3.12-slim`** — é o do `.venv` local (3.12.10) e o que gerou a linha de base
numérica do motor, então o `worker` não introduz variação de interpretador sobre o
`engine/`.

Nas imagens construídas, as duas deram `Python 3.12.14`.

### Achado 4: grep na saida e armadilha

Ao verificar a mutação "derrubar o `worker`", a checagem inicial procurou o texto do
resultado na saída do comando — e **aprovou indevidamente**. Motivo: o *traceback* do Python
ecoa a linha de código que falhou, e essa linha contém a própria string procurada.

O comportamento real, medido:

| Cenário | Código de saída |
|---|---|
| `worker` de pé | **0**, imprime `worker` |
| `worker` parado | **1**, `celery.exceptions.TimeoutError` |

**Todo critério deste plano se apoia em código de saída.** Onde há casamento de texto, ele
está **dentro** de um comando que sai != 0 quando não casa (`grep -q`, `test`), nunca como
leitura humana da saída. São cinco lugares, e em todos o texto *é* o contrato: o nome de host
em F3-05, o `ModuleNotFoundError` que a spec exige em F3-03, o `"ok"` da rota de saúde, o
`rolldown` na imagem do frontend, e as varreduras de F3-11.

A distinção que importa não é "código de saída *versus* texto" — é **quem decide**: um `grep`
que alimenta o código de saída reprova sozinho; um `grep` cuja saída alguém lê, não.

### Achado 5: o que funcionou como esperado

| Verificação | Resultado |
|---|---|
| Interpolação a partir do `.env` da raiz | `published: "55432"` resolvido; confirma a [D-35](../decisoes/D-35-compose-e-dockerignore-na-raiz.md) |
| `depends_on: condition: service_healthy` | `web` só parte com `postgres` e `redis` saudáveis |
| `hostname: worker` no serviço | tarefa enfileirada pelo `web` devolveu `worker`; o `web` reportou `web` |
| `psycopg` 3.3.5 → Postgres 18 | conectou; `PostgreSQL 18.6 (Debian 18.6-1.pgdg13+2)` |
| `import tensorflow` na `web` | `ModuleNotFoundError`, saída 1 |
| `import django` na `web` | saída 0 |
| `import tensorflow` na `worker` | saída 0 |
| `npm ci` sob `node:24-slim` com `engine-strict` | saída 0 em 9s; `@rolldown`, `rolldown` e `vitest` presentes |
| O mesmo sob `node:20-slim` | saída 1, `EBADENGINE` — a proteção funciona no contêiner |

**Custo medido**, para calibrar expectativa: imagem `web` **328 MB**, imagem `worker`
**3,19 GB**; a construção do `worker` levou **88 s** e consumiu **3,6 GB**.

---

## O que este plano decide

Pontos que a spec deixa para o plano. Cada um é reversível e nenhum contradiz decisão
registrada.

| Tema | Decisão | Motivo |
|---|---|---|
| **Etiquetas das imagens de apoio** | `postgres:18`, `redis:8` | majores correntes, confirmados no registro em 2026-09-03. A spec proíbe `latest` |
| **Imagem base do backend** | `python:3.12-slim` | ver [achado 3](#achado-3-o-tensorflow-decide-a-versao-do-python) |
| **Imagem base do frontend** | `node:24-slim` | casa com `frontend/.nvmrc` (`24`) e com `engines.node >= 24.15`. O major corrente é 26, e o jsdom 30 até o aceita — mas 24 é o que o repositório declara |
| **Versão maior do Postgres** | **18**, registrada em `docs/decisoes/D-36-versao-do-postgres.md` | a spec manda registrar, porque o F4 e a hospedagem herdam |
| **Driver** | `psycopg` 3 (`psycopg[binary]`) | a spec o nomeia; verificado contra Postgres 18.6 |
| **Portas publicadas** | web `8000`, frontend **`5273`**, postgres `55432`, redis `56379` | 5173 é de outro projeto desta máquina; as duas altas evitam colidir com Postgres ou Redis nativos. Todas configuráveis (F3-08) |
| **Nomes das imagens** | `ruvor-web`, `ruvor-worker`, `ruvor-frontend`, via `image:` | nome derivado do diretório quebraria F3-03 se alguém renomeasse a pasta |
| **Sintaxe de obrigatoriedade** | `${VAR:?...}` em toda variável sem padrão sensato | ver [achado 2](#achado-2-env-ausente-nao-faz-o-compose-falhar) |
| **Cliente HTTP nas imagens** | `curl`, instalado na etapa base do backend e na do frontend | as verificações de vida do `web` e do `frontend` precisam dele, e imagem `slim` não traz |
| **Onde a suíte do backend roda** | serviço `web` | a spec decide; o plano só o registra |

---

## Rastreabilidade

| Requisito | Onde é provado |
|---|---|
| F3-01 cinco serviços saudáveis | T6 (`up -d --wait`, que reprova sozinho se algum não ficar saudável), T9 (mutação a) |
| F3-02 duas imagens do mesmo fonte | T2 (um único arquivo de construção, dois alvos) |
| F3-03 isolamento do TensorFlow | T2 (quatro afirmações + paridade de `python --version`), T9 (mutação b) |
| F3-04 Django conecta no Postgres | T8 (`test_conexao_com_o_banco`), T9 (mutação d) |
| F3-05 tarefa executada pelo worker | T6 (`ping` devolve `worker`, com o conjunto de pé), T9 (mutação c) |
| F3-06 `compose` lê o `.env` | T6 (subida sem variável exportada), T9 (mutação e) |
| F3-07 frontend alcançável e proxy | T5 (`vite.config.ts`), T6 (`curl` na porta publicada, `/` e `/health`) |
| F3-08 portas configuráveis | T6 (troca das quatro no `.env`), T9 (mutação f) |
| F3-09 teste e tipos no contêiner | **T8, os quatro comandos** — suíte e tipos do backend, suíte e tipos do frontend, todos por `compose exec`; T9 (mutação g) |
| F3-10 `RUVOR_ALLOWED_HOSTS` tolera espaço | T3 (`test_allowed_hosts`) |
| F3-11 documentação não mente | T10 (varredura + mutação h) |

---

## Mapa de arquivos

### Criados

| Arquivo | Responsabilidade | Tarefa |
|---|---|---|
| `.dockerignore` | o que não entra no contexto de construção | T1 |
| `infra/backend.Dockerfile` | etapa base + alvos `web` e `worker` | T2 |
| `infra/frontend.Dockerfile` | Node com o servidor de desenvolvimento | T4 |
| `compose.yaml` | cinco serviços, rede, volume, verificações de vida | T6 |
| `backend/config/celery.py` | a aplicação Celery | T7 |
| `backend/config/tasks.py` | a tarefa `ping` | T7 |
| `backend/tests/test_allowed_hosts.py` | F3-10 | T3 |
| `backend/tests/test_celery_registro.py` | prova que a tarefa está registrada, sem Redis | T7 |
| `docs/decisoes/D-36-versao-do-postgres.md` | a versão maior escolhida | T6 |

### Alterados

| Arquivo | O que muda | Tarefa |
|---|---|---|
| `backend/pyproject.toml` | ganha `celery`, `redis`, `psycopg[binary]` | T3 |
| `backend/config/settings.py` | `DATABASES` real, configuração do Celery, `_split_hosts` | T3 |
| `backend/config/settings_test.py` | variáveis de banco, **com valores distintos dos do `compose`** | T3 |
| `backend/config/__init__.py` | expõe a aplicação Celery | T7 |
| `frontend/vite.config.ts` | destino do proxy por variável; escuta em todas as interfaces | T5 |
| `.env.example` | variáveis novas, valores de desenvolvimento que funcionam, cabeçalho corrigido | T6 |
| `frontend/.env.example` | comentário corrigido | T5 |
| `README.md` | seção "Executar", "Pré-requisitos", "Comandos do dia a dia" e os **sete** trechos falsos enumerados em T10 | T10 |
| `backend/tests/test_health.py` | **dois donos, declarados:** T3 remove o teste obsoleto (senão a suíte fica vermelha por cinco commits); T8 acrescenta o de conexão, que exige Postgres | T3 e T8 |
| `docs/decisoes/README.md` | ganha a linha de D-36 no índice | T6 |
| `CLAUDE.md` | "Estado do repositório" — parágrafo e item de lista | T10 |

### Intocados

`engine/` (instalado na imagem `worker`; instalar não é alterar — [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md)),
`brand/`, `.gitignore` (volume nomeado, nada a ignorar), `frontend/.nvmrc` e `frontend/.npmrc`,
`docs/ARQUITETURA.md`, `docs/ROADMAP.md` e `docs/ESTADO.md` (já corrigidos com o registro das
decisões, antes deste plano).

---

## Ordem e dependências

| Tarefa | Depende de | Pode correr em paralelo com |
|---|---|---|
| **T3** settings, dependências, função de hosts | — | T4, T5 |
| **T4** `infra/frontend.Dockerfile` | — | T3, T5 |
| **T5** `frontend/vite.config.ts` | — | T3, T4 |
| **T1** `.dockerignore` | — | T3, T4, T5, T7 |
| **T2** `infra/backend.Dockerfile` | T1, T3 | T4, T5, T7 |
| **T7** Celery e a tarefa `ping` | T3 | T1, T2, T4, T5 |
| **T6** `compose.yaml` e `.env.example` | T1, T2, T4, T5, **T7** | — |
| **T8** verificação dentro do contêiner | T6 | — |
| **T9** mutações | T6, T7, T8 | — |
| **T10** documentação | T6, T7, T8, T9 | — |

Uma inversão em relação à numeração, e ela é deliberada: **T7 antes de T6.** Numerar não é
ordenar — o que manda é a coluna "Depende de".

**T1 precede T2**, e não é arbitrário: T2 é a primeira construção do repositório, a única com
transferência de contexto fria, e por isso a única em que a medição do `.dockerignore` diz
alguma coisa — ver [por que a medição mora lá](#por-que-a-medição-do-contexto-é-critério-da-t2).

**T7 antes de T6** não é detalhe de ordenação: o alvo `worker` executa
`celery -A config worker`, e a verificação de vida desse serviço pergunta à fila. Sem
`config/celery.py` e `config/tasks.py`, o contêiner `worker` **nunca fica saudável** e o
critério de T6 reprovaria por trabalho que ainda não foi feito.

Pela mesma razão, **F3-05 é provado em T6**, não em T7: só lá existe conjunto de pé. T7
entrega o código e prova que a tarefa está registrada; T6 prova que ela atravessa a fila.

T3 é a raiz de quase tudo, porque as dependências e as settings precisam existir antes de
qualquer imagem instalar o backend. T6 é o ponto de junção: só ele sobe o conjunto. T8, T9 e
T10 fecham.

---

### Tarefa 1 — `.dockerignore` na raiz

**Depende de:** nada · **Visual:** não · **precede a T2**, que é a primeira construção e paga o
contexto

**Arquivos** — cria: `.dockerignore`

**Contrato** — *o conteúdo é o contrato*

```
.git
.venv
**/__pycache__
**/*.pyc
**/.mypy_cache
**/.pytest_cache
**/*.egg-info
frontend/node_modules
frontend/dist
docs
tools
.env
```

**Todo padrão de diretório aninhado leva `**/`.** Padrão sem ele casa **somente na raiz do
contexto**, e os caches não estão na raiz: `backend/.mypy_cache` tem 19 MB, `engine/.mypy_cache`
tem 14 MB, e há ainda três `.pytest_cache` e dois `*.egg-info`. Sem o prefixo, ~33 MB de
cache puro subiriam ao daemon a cada construção, num contexto que fora isso é de ~2 MB — o
cache seria a maior parte do que se envia.

`.env` está na lista de propósito: as variáveis chegam pelo `compose`, nunca assadas na
imagem. `tools/` entra por ser material de apoio do TCC, sem uso em imagem.

**Critério de aceite**

Esta tarefa não constrói imagem — **a medição do contexto é o critério da T2**, que é a
primeira construção e portanto a única com transferência fria. Ver
[por que a medição mora lá](#por-que-a-medição-do-contexto-é-critério-da-t2).

Aqui o critério é a presença de cada padrão exigido, que reprova se algum faltar:

```bash
for p in '.git' '.venv' '**/__pycache__' '**/*.pyc' '**/.mypy_cache' \
         '**/.pytest_cache' '**/*.egg-info' 'frontend/node_modules' \
         'frontend/dist' 'docs' 'tools' '.env'; do
  grep -qxF "$p" .dockerignore || { echo "falta o padrao: $p"; exit 1; }
done
```

`-x` exige linha inteira e `-F` desliga expressão regular: sem os dois, `.env` casaria
`.env.example` e `docs` casaria qualquer linha que o contivesse, aprovando um arquivo
incompleto.

**Cerca de escopo**

Não cria `infra/` nem arquivo de construção. Não toca no `.gitignore`.

---

### Tarefa 2 — Imagem do backend, dois alvos

**Depende de:** T1, T3 · **Visual:** não

**Arquivos** — cria: `infra/backend.Dockerfile`

**Contrato** — *o conteúdo é o contrato*

```dockerfile
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /repo
COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/config/__init__.py backend/config/__init__.py
RUN pip install --no-cache-dir -e "./backend[dev]"

FROM base AS web
WORKDIR /repo/backend
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS worker
COPY engine/pyproject.toml engine/pyproject.toml
COPY engine/src/engine/__init__.py engine/src/engine/__init__.py
RUN pip install --no-cache-dir -e "./engine[traditional,garch,ml]"
WORKDIR /repo/backend
CMD ["celery", "-A", "config", "worker", "--loglevel=info"]
```

**Um arquivo, dois alvos, uma etapa base** — é o que F3-02 verifica. O código-fonte não é
copiado: vem por montagem no `compose` (T6); as cópias acima existem só para a instalação
editável resolver.

**A `web` não instala `engine/`** — não é "sem o extra de ML", é ausência total
([D-17](../decisoes/D-17-monorepo-engine-sem-django.md)).

**Critério de aceite**

```bash
# Contexto frio: esta e a primeira construcao do repositorio. Se precisar refazer,
# rode antes `docker builder prune -f`, senao o cache faz o criterio aprovar sozinho.
# O tamanho transferido precisa ficar abaixo de 10 MB.
set -o pipefail        # senao uma construcao que falha nao reprova nesta cadeia
docker build -f infra/backend.Dockerfile --target web -t ruvor-web . 2>&1 \
  | tee /dev/stderr \
  | grep -oE 'transferring context: [0-9.]+[kMG]B' | tail -1 \
  | grep -qE ': ([0-9.]+kB|[0-9](\.[0-9]+)?MB)$'

docker build -f infra/backend.Dockerfile --target worker -t ruvor-worker .

# F3-03, as quatro afirmações — todas exigidas
docker run --rm --entrypoint python ruvor-web    -c "import tensorflow" 2>&1 | grep -q ModuleNotFoundError
docker run --rm --entrypoint python ruvor-web    -c "import django"
docker run --rm --entrypoint python ruvor-worker -c "import tensorflow"

# paridade de interpretador
test "$(docker run --rm --entrypoint python ruvor-web --version)" \
   = "$(docker run --rm --entrypoint python ruvor-worker --version)"
```

Esperado, medido na verificação: `web` ≈ 330 MB, `worker` ≈ 3,2 GB, ambas `Python 3.12.14`. A
construção do `worker` leva ~90 s e consome ~3,6 GB — **meça o espaço livre antes e depois** e
registre no relato.

#### Por que a medição do contexto é critério da T2

O BuildKit transfere o contexto **de forma incremental**: da segunda construção em diante, só
o que mudou. Se a medição ficasse numa tarefa posterior, um `.dockerignore` defeituoso
passaria — os megabytes de cache já teriam subido aqui, e a construção seguinte reportaria
poucos kB **por causa do cache, não do arquivo**.

Daí a ordem: `.dockerignore` primeiro (T1), medição na primeira construção (T2). É também o
que evita pagar o custo que o arquivo existe para evitar, num bloco cujo risco declarado é
espaço em disco.

Para repetir a medição depois — na mutação da T9, por exemplo — é preciso esfriar o cache
antes: `docker builder prune -f`.

**Cerca de escopo**

Não cria o `compose.yaml`. Não altera `engine/` nem `backend/`.

---

### Tarefa 3 — Backend: banco, Celery e a função de hosts

**Depende de:** nada · **Visual:** não

**Arquivos**
- altera: `backend/pyproject.toml`, `backend/config/settings.py`, `backend/config/settings_test.py`
- cria: `backend/tests/test_allowed_hosts.py`

**Contrato**

`backend/pyproject.toml` — acrescenta a `dependencies`:
`celery>=5.6`, `redis>=8.1`, `psycopg[binary]>=3.3`.

`backend/config/settings.py`:

- **`DATABASES`** deixa de ser `{}` e passa a apontar para o backend `postgresql`, lendo
  `RUVOR_DB_HOST`, `RUVOR_DB_PORT`, `RUVOR_DB_NAME`, `RUVOR_DB_USER` e `RUVOR_DB_PASSWORD`
  pela função `_required` que já existe no arquivo. **Nenhum app novo em `INSTALLED_APPS`.**
- **Celery**: `CELERY_BROKER_URL` e `CELERY_RESULT_BACKEND`, ambos de `RUVOR_REDIS_URL`.
  `CELERY_TASK_ALWAYS_EAGER` **não é definido** — o modo síncrono fica desligado, e isso é
  contrato ([spec](../specs/F3-ambiente-local.md#contrato-da-tarefa-de-fumaça)).
- **`_split_hosts(valor: str) -> list[str]`**, função nomeada de nível de módulo, que separa
  por vírgula, aplica `.strip()` e descarta vazios. `ALLOWED_HOSTS` passa a chamá-la. É o que
  torna F3-10 testável — hoje a expressão é embutida e não há função a testar.

`backend/config/settings_test.py` — preenche por `os.environ.setdefault` as cinco variáveis de
banco **e também `RUVOR_REDIS_URL`**, todas com valores deliberadamente diferentes dos do
`compose` (por exemplo `RUVOR_DB_NAME=nao-usar`). Duas razões, e as duas são de execução, não
de estilo:

- A spec exige a distinção dos valores de banco: coincidentes, um `.env` incompleto passaria
  despercebido em F3-04.
- **`RUVOR_REDIS_URL` não pode faltar.** `settings.py` passa a lê-la pelo `_required`, e o
  módulo é importado tanto pela suíte quanto pelo plugin do django-stubs
  (`backend/pyproject.toml` aponta `django_settings_module = "config.settings_test"`). Sem o
  preenchimento, **o critério desta tarefa e o da T7 morrem com `ImproperlyConfigured`** antes
  do primeiro teste — no hospedeiro, onde não há Redis.

**Esta tarefa também remove `test_processo_nao_tem_banco`** de `backend/tests/test_health.py`.
Não é escopo alheio: com `DATABASES` preenchido, aquele teste passa a falhar **no mesmo
commit** — ele exige `ImproperlyConfigured` em `connection.cursor()`, e o que passa a ocorrer
é o `RuntimeError` de bloqueio do pytest-django. Deixar a remoção para T8, que só vem depois
de T6, manteria a `main` com suíte vermelha por cinco commits. O teste que **prova a conexão**
continua sendo de T8, porque exige Postgres de pé.

**Critério de aceite**

```bash
pytest backend/tests/test_allowed_hosts.py
pytest backend/tests/test_health.py::test_health_responde_ok
(cd backend && mypy)
```

O `cd` vai entre parênteses de propósito: sem subshell ele persiste, e a linha seguinte
procuraria `backend/backend/tests/`.

O teste de hosts cobre, no mínimo: `"localhost, 127.0.0.1"` → `["localhost", "127.0.0.1"]`;
`""` → `[]`; `"a,,b"` → `["a", "b"]`.

**Mutação obrigatória:** remover o `.strip()` da função e confirmar que o teste reprova.

**Cerca de escopo**

Não cria `celery.py` nem `tasks.py` — é T7. **Não acrescenta** o teste de conexão a
`test_health.py`, só remove o obsoleto — o novo é T8. A suíte só passa a exigir Postgres em
T8; aqui os dois testes restantes rodam sem banco.

---

### Tarefa 4 — Imagem do frontend

**Depende de:** nada · **Visual:** não

**Arquivos** — cria: `infra/frontend.Dockerfile`

**Contrato** — *o conteúdo é o contrato*

```dockerfile
FROM node:24-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /repo/frontend
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci --no-audit --no-fund
CMD ["npm", "run", "dev"]
```

**Instalação completa, sem `--omit=dev`**: F3-09 exige `vitest`, `typescript` e `jsdom` dentro
da imagem, e `node_modules` passa a ser volume do contêiner.

**`brand/ruvor/` não é copiado, de propósito.** O contexto de construção é a raiz por causa do
apelido `@brand`, mas esta imagem não roda `vite build` — só o servidor de desenvolvimento, que
lê o kit pela montagem que o `compose` faz. Copiar assaria uma cópia que divergiria da fonte.

**Critério de aceite**

```bash
docker build -f infra/frontend.Dockerfile -t ruvor-frontend .
docker run --rm --entrypoint sh ruvor-frontend -c "ls node_modules/.bin/vitest node_modules/.bin/tsc"
docker run --rm --entrypoint sh ruvor-frontend -c "ls node_modules | grep -q '^rolldown$'"
```

O último não é zelo excessivo: sem `engine-strict`, o npm **omite em silêncio** o binding
nativo do rolldown e o `vite build` quebra depois com mensagem enganosa —
[armadilha já registrada](../aprendizados.md). Verificado: sob `node:24-slim` a instalação
leva ~9 s e traz `@rolldown`, `rolldown` e `vitest`.

**Mutação obrigatória:** trocar a base para `node:20-slim` e confirmar que a construção
reprova com `EBADENGINE` (verificado).

**Cerca de escopo**

Não altera nada dentro de `frontend/`. Não cria o serviço no `compose`.

---

### Tarefa 5 — `vite.config.ts`: proxy por variável e escuta externa

**Depende de:** nada · **Visual:** não

**Arquivos** — altera: `frontend/vite.config.ts`, `frontend/.env.example`

**Contrato**

- O destino do proxy de `/health` passa a vir de **`VITE_PROXY_TARGET`**, com
  `http://127.0.0.1:8000` — o valor literal de hoje — como padrão. Assim a execução nativa
  segue funcionando sem configuração.
- `server.host` passa a `true`, para escutar em todas as interfaces. Sem isso o contêiner não
  é alcançável do hospedeiro, e o navegador mostra conexão recusada com o serviço de pé.
- A variável **não** vem de `import.meta.env`: o `vite.config.ts` roda antes de o Vite
  carregar os `.env` e não recebe `VITE_*` automaticamente. Leia de `process.env`, que o
  `compose` preenche — `frontend/tsconfig.json` já inclui `types: ["node"]`, então typecheca
  sem alteração.
- `frontend/.env.example`: o comentário atual afirma que o proxy encaminha para `:8000`;
  passa a dizer que o destino é `web:8000` sob o `compose` e `127.0.0.1:8000` fora dele.
  `VITE_PROXY_TARGET` **não** entra neste arquivo — é fixada pelo `compose`
  ([spec](../specs/F3-ambiente-local.md#quais-variáveis-moram-em-qual-arquivo-de-exemplo)).

**A recarga a quente:** a spec manda o plano **verificar**, não supor. Em montagem de disco
entre Windows e contêiner, o aviso de mudança de arquivo frequentemente não atravessa. Depois
que T6 subir o conjunto, edite um arquivo em `frontend/src/` e observe se o navegador
recarrega sozinho. **Se não recarregar**, ligue a sondagem (`server.watch.usePolling`) e
registre no relato que foi necessária — é informação para quem trabalhar na máquina depois.
Se recarregar, **não ligue**: sondagem custa CPU contínua.

**Critério de aceite**

```bash
grep -q '127.0.0.1:8000' frontend/vite.config.ts    # o padrao nativo continua la
(cd frontend && npm run typecheck && npm test)
```

**O `grep` não é redundante.** Os cinco testes existentes não sobem o servidor de
desenvolvimento nem exercitam o proxy — `App.test.tsx` substitui o `fetch` global e
`cores.test.ts` roda sobre o sistema de arquivos. Um padrão **errado** (`?? "http://web:8000"`)
passaria nos dois e quebraria a execução nativa em silêncio, porque T6 e T8 sempre rodam com
`VITE_PROXY_TARGET` definida pelo `compose`, e nada mais no bloco toca o caminho nativo.

A **ausência** de padrão o `tsc` já pega, porque `string | undefined` não serve onde o Vite
espera destino de proxy. O que escapa é só o padrão trocado — e é o que esta linha fecha.

A execução **dentro do contêiner** é F3-09, provada em T8.

**Cerca de escopo**

Não toca em `frontend/src/`. Não altera `.nvmrc`, `.npmrc` nem `package.json`.

---

### Tarefa 6 — `compose.yaml`, `.env.example` e a decisão da versão

**Depende de:** T1, T2, T4, T5, T7 · **Visual:** não

**Arquivos**
- cria: `compose.yaml` (raiz), `docs/decisoes/D-36-versao-do-postgres.md`
- altera: `.env.example` (raiz), `docs/decisoes/README.md` (a linha de D-36 no índice)

**Contrato** — *o conteúdo é o contrato*

`compose.yaml`, na raiz:

```yaml
services:
  postgres:
    image: postgres:18
    environment:
      POSTGRES_DB: ${RUVOR_DB_NAME:?defina no .env}
      POSTGRES_USER: ${RUVOR_DB_USER:?defina no .env}
      POSTGRES_PASSWORD: ${RUVOR_DB_PASSWORD:?defina no .env}
    ports:
      - "${RUVOR_PORT_POSTGRES:?defina no .env}:5432"
    volumes:
      - pgdata:/var/lib/postgresql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 5s
      timeout: 5s
      retries: 20
      start_period: 30s

  redis:
    image: redis:8
    ports:
      - "${RUVOR_PORT_REDIS:?defina no .env}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 20

  web:
    build: { context: ., dockerfile: infra/backend.Dockerfile, target: web }
    image: ruvor-web
    hostname: web
    environment: &backend-env
      RUVOR_SECRET_KEY: ${RUVOR_SECRET_KEY:?defina no .env}
      RUVOR_DEBUG: ${RUVOR_DEBUG:-true}
      RUVOR_ALLOWED_HOSTS: ${RUVOR_ALLOWED_HOSTS:-localhost,127.0.0.1,web}
      RUVOR_DB_HOST: ${RUVOR_DB_HOST:-postgres}
      RUVOR_DB_PORT: ${RUVOR_DB_PORT:-5432}
      RUVOR_DB_NAME: ${RUVOR_DB_NAME:?defina no .env}
      RUVOR_DB_USER: ${RUVOR_DB_USER:?defina no .env}
      RUVOR_DB_PASSWORD: ${RUVOR_DB_PASSWORD:?defina no .env}
      RUVOR_REDIS_URL: ${RUVOR_REDIS_URL:-redis://redis:6379/0}
    volumes:
      - ./backend:/repo/backend
    ports:
      - "${RUVOR_PORT_WEB:?defina no .env}:8000"
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://127.0.0.1:8000/health"]
      interval: 5s
      timeout: 5s
      retries: 20
      start_period: 20s
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }

  worker:
    build: { context: ., dockerfile: infra/backend.Dockerfile, target: worker }
    image: ruvor-worker
    hostname: worker
    environment: *backend-env
    volumes:
      - ./backend:/repo/backend
      - ./engine:/repo/engine
    healthcheck:
      test: ["CMD-SHELL", "celery -A config inspect ping -d celery@$$(hostname) || exit 1"]
      interval: 10s
      timeout: 15s
      retries: 20
      start_period: 30s
    depends_on:
      redis: { condition: service_healthy }

  frontend:
    build: { context: ., dockerfile: infra/frontend.Dockerfile }
    image: ruvor-frontend
    hostname: frontend
    environment:
      VITE_PROXY_TARGET: http://web:8000
    volumes:
      - ./frontend:/repo/frontend
      - ./brand/ruvor:/repo/brand/ruvor:ro
      - /repo/frontend/node_modules
    ports:
      - "${RUVOR_PORT_FRONTEND:?defina no .env}:5173"
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://127.0.0.1:5173/"]
      interval: 5s
      timeout: 5s
      retries: 20
      start_period: 20s
    depends_on:
      web: { condition: service_healthy }

volumes:
  pgdata:
```

Sete pontos que **não são negociáveis**, cada um com o motivo:

| Ponto | Por quê |
|---|---|
| `pgdata:/var/lib/postgresql`, **sem `/data`** | [achado 1](#achado-1-o-postgres-18-mudou-o-ponto-de-montagem) — com `/data` o contêiner recusa subir |
| `POSTGRES_*` mapeadas das `RUVOR_DB_*` | a imagem não lê `RUVOR_*`; sem senha, recusa inicializar |
| `${VAR:?...}` em toda variável sem padrão | [achado 2](#achado-2-env-ausente-nao-faz-o-compose-falhar) — é o que faz a mutação **e** reprovar |
| Verificação de vida do `web` em **`127.0.0.1`**, não em `web` | com o cabeçalho `Host: web`, o Django responderia **400 DisallowedHost** e o serviço nunca ficaria saudável — falha cuja mensagem não aponta para a causa. `web` também entra em `RUVOR_ALLOWED_HOSTS` porque o proxy do frontend usa esse nome |
| `start_period` de 30 s no `postgres` e no `worker` | na primeira subida o Postgres inicializa o agrupamento e o Celery conecta à fila; sem folga, `depends_on` estoura antes |
| Verificação de vida do `worker` — **único ponto de T6 não medido na verificação prévia** | o projeto descartável provou o percurso da fila, mas não esta verificação. A análise sustenta que funciona (`hostname` existe no `slim`, e o nome de nó padrão do Celery é `celery@%h`, casando com `hostname: worker`), mas **se o `worker` não ficar saudável na primeira subida, suspeite dela antes de qualquer outra coisa** |
| `./engine` montado **só no `worker`** | montá-lo na `web` abriria caminho para `import engine` que F3-03 não pegaria, porque o teste olha TensorFlow e não o motor |
| Volume anônimo sobre `/repo/frontend/node_modules` | binário nativo instalado no Windows não serve ao Linux da imagem. **Ele sobrevive à recriação do contêiner**: depois de mexer em `package.json`, é preciso `docker compose up -d --build --renew-anon-volumes`, senão a dependência nova não aparece |

`.env.example` da raiz, literal:

```bash
# Ambiente local. Copie para .env e rode `docker compose up` na raiz.
# O docker compose le este arquivo automaticamente; nada precisa ser exportado no shell.
# Os valores abaixo funcionam como estao — nao ha segredo real aqui.

RUVOR_SECRET_KEY=desenvolvimento-local-nao-usar-em-producao
RUVOR_DEBUG=true
RUVOR_ALLOWED_HOSTS=localhost,127.0.0.1,web

# Host e porta sao os da rede interna do compose, nao do hospedeiro.
RUVOR_DB_HOST=postgres
RUVOR_DB_PORT=5432
RUVOR_DB_NAME=ruvor
RUVOR_DB_USER=ruvor
RUVOR_DB_PASSWORD=ruvor-local

RUVOR_REDIS_URL=redis://redis:6379/0

# Portas publicadas no hospedeiro. 5173 nao e o padrao do frontend: pertence a
# outro projeto desta maquina.
RUVOR_PORT_WEB=8000
RUVOR_PORT_FRONTEND=5273
RUVOR_PORT_POSTGRES=55432
RUVOR_PORT_REDIS=56379
```

O cabeçalho substitui o atual, que diz *"Nada as carrega deste arquivo"* — falso a partir
deste bloco. `RUVOR_SECRET_KEY` deixa de ser vazia porque o `_required` do `settings.py`
rejeita string vazia, e a primeira vez precisa ser só `cp`, sem edição.

`D-36` registra Postgres **18**, com o motivo: o F4 e a hospedagem herdam a escolha, e trocar
depois do F4 deixa de ser grátis.

**Critério de aceite**

```bash
test -z "$(env | grep '^RUVOR_')"          # F3-06: nada exportado no shell
test ! -f .env || mv .env .env.anterior    # nao sobrescreve um .env existente em silencio
cp .env.example .env
docker compose up -d --build --wait        # sai != 0 se algum servico nao ficar saudavel
test "$(docker compose ps --services --filter status=running | wc -l)" -eq 5

curl -fsS http://localhost:8000/health | grep -q '"ok"'
curl -fsS http://localhost:5273/ -o /dev/null
curl -fsS http://localhost:5273/health | grep -q '"ok"'    # F3-07, pelo proxy

# F3-05: a tarefa atravessa a fila e quem executa e o worker
test "$(docker compose exec -T web python -c \
  'from config.tasks import ping; print(ping.delay().get(timeout=30))')" = worker

test -f docs/decisoes/D-36-versao-do-postgres.md
grep -q 'D-36' docs/decisoes/README.md
```

`--wait` é o que torna F3-01 executável: ele **reprova sozinho** se algum serviço não chegar a
saudável, em vez de deixar a decisão para quem lê a saída do `ps`.

**F3-08 — as quatro portas.** Troque as quatro no `.env` para valores livres — `8010`, `5283`,
`55433`, `56380` —, **recrie** com `docker compose up -d --wait`, e prove as quatro na porta
nova:

```bash
# O .env nao e lido pelo shell; carregue-o so aqui, para este bloco de verificacao.
set -a; . ./.env; set +a

curl -fsS "http://localhost:$RUVOR_PORT_WEB/health"      | grep -q '"ok"'
curl -fsS "http://localhost:$RUVOR_PORT_FRONTEND/" -o /dev/null

docker run --rm --add-host=host.docker.internal:host-gateway postgres:18 \
  pg_isready -h host.docker.internal -p "$RUVOR_PORT_POSTGRES"
docker run --rm --add-host=host.docker.internal:host-gateway redis:8 \
  redis-cli -h host.docker.internal -p "$RUVOR_PORT_REDIS" ping | grep -q PONG
```

Duas coisas deste bloco não são opcionais:

- **O `set -a; . ./.env` é local a esta verificação, e não contradiz F3-06.** Aquele requisito
  diz que **o `compose`** não depende de variável exportada — e a linha `test -z "$(env | grep
  '^RUVOR_')"`, no início do critério, já o provou com o shell limpo. Aqui as variáveis são
  carregadas só para o comando de teste saber em qual porta bater. Sem isso, `$RUVOR_PORT_*`
  estaria vazia e `pg_isready -p ""` falharia pelo motivo errado.
- **`host.docker.internal`**, e não `--network host`: no Docker Desktop para Windows, a rede
  do hospedeiro não alcança as portas publicadas como alcançaria no Linux. Usar contêiner
  descartável é o que evita exigir cliente de Postgres ou Redis na máquina — que é o que o
  bloco promete não pedir.

Ao fim, restaure e **limpe o ambiente do shell**:

```bash
cp .env.example .env
unset $(env | grep -oE '^RUVOR_[A-Z_]+' )
test -z "$(env | grep '^RUVOR_')"        # precisa voltar a estar vazio
docker compose up -d --wait
```

O `unset` não é zelo: variável de ambiente **tem precedência sobre o `.env`** no Compose. Se
as `RUVOR_*` carregadas aqui sobreviverem até a T9, a mutação **e** (renomear o `.env`)
encontra tudo no ambiente, o `${VAR:?}` não dispara, e a **única mutação que sustenta F3-06**
sai com código 0 — falso achado que mandaria parar a execução.

**Cerca de escopo**

Não escreve teste. Não altera `README.md`.

---

### Tarefa 7 — Celery e a tarefa de fumaça

**Depende de:** T3 · **Visual:** não

**Arquivos**
- cria: `backend/config/celery.py`, `backend/config/tasks.py`, `backend/tests/test_celery_registro.py`
- altera: `backend/config/__init__.py`

**Contrato**

```
tarefa:   config.tasks.ping
entrada:  nenhuma
saída:    o nome de host de quem executou
```

- `config/celery.py` — a aplicação Celery, lendo a configuração das settings do Django. **Ela
  precisa fazer `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")` antes de
  instanciar a aplicação.** É o único elo entre três critérios que dependem dele —
  `celery -A config worker` no alvo `worker`, a verificação de vida do serviço, e o
  `python -c 'from config.tasks import ping…'` de T6. Sem essa linha, o `worker` não sobe e a
  causa não aparece na mensagem.
- `config/tasks.py` — `ping`, que devolve o nome de host do processo. **Não uma constante:**
  com `"pong"`, o critério passaria com o `worker` desligado.
- `config/__init__.py` — expõe a aplicação, que é o que faz `celery -A config` encontrá-la.
- **A tarefa é registrada por `import` explícito em `config/celery.py`**, depois de a aplicação
  ser criada — não por `include=[...]` nem por descoberta automática. A automática varre
  `INSTALLED_APPS`, que contém apenas `rest_framework`; `config` não está lá e não deve entrar.

  **O mecanismo importa, e não é escolha de estilo.** Com `include=["config.tasks"]`, o worker
  importa a tarefa no arranque mas `app.tasks` continua vazio até a finalização — o teste
  abaixo reprovaria uma implementação correta, e a "correção" natural (importar
  `config.tasks` dentro do teste) tornaria a asserção verdadeira para **qualquer**
  implementação, inclusive a defeituosa. Com `import`, `app.tasks` registra na importação de
  `config`, e o teste tem dente.

**Critério de aceite** — **sem conjunto de pé**, porque T6 ainda não existe. O que esta tarefa
prova é que o código está correto e a tarefa **registrada**; que ela atravessa a fila é F3-05,
provado em T6:

```bash
(cd backend && mypy)
pytest backend/tests/test_celery_registro.py
```

O teste novo confere duas coisas, sem tocar em Redis: que `config.celery.app` existe e é
importável a partir de `config`, e que **`"config.tasks.ping"` está em `app.tasks`**. É essa
segunda asserção que pega o defeito real — sem registro, o `worker` sobe saudável e **nunca
recebe a tarefa**, falha que só apareceria em T6 e pareceria problema de rede.

**O teste não pode importar `config.tasks`.** Se importar, ele passa a valer para qualquer
implementação e deixa de distinguir coisa alguma. Ele importa **só `config`** — é justamente
essa restrição que o torna capaz de reprovar.

Verificado no projeto descartável: com a tarefa registrada, enfileirada pelo `web`, quem
executa é `worker`.

`mypy` estrito continua limpo. Se ele reprovar no código de fila, a saída é
`ignore_missing_imports` **restrito ao módulo do Celery** — nunca `ignore_errors`, que
desligaria a verificação no código novo.

**Cerca de escopo**

Nenhuma tarefa de domínio. Não cria `backend/apps/`.

---

### Tarefa 8 — Conexão com o banco, e F3-09 dentro do contêiner

**Depende de:** T6 · **Visual:** não

**Arquivos** — altera: `backend/tests/test_health.py`

**Contrato**

Entra `test_conexao_com_o_banco`, que **desbloqueia explicitamente o acesso do pytest-django**
e abre um cursor contra o banco **configurado** — não contra um banco de teste criado pelo
pytest. (O `test_processo_nao_tem_banco` obsoleto já saiu em T3, para não deixar a suíte
vermelha no intervalo.)

A distinção é o que sustenta o requisito: `@pytest.mark.django_db` alcança o servidor, mas
cria `test_<nome>` e por isso **não exercita `RUVOR_DB_NAME`**. Um nome de banco errado no
`.env` atravessaria sem ser notado, e é justamente o erro que este bloco existe para pegar.

O teste confere que `current_database()` é o valor de `RUVOR_DB_NAME`.

**Critério de aceite**

F3-04:

```bash
docker compose exec -T web pytest tests/test_health.py::test_conexao_com_o_banco
```

**F3-09 — os quatro comandos, todos dentro do contêiner.** A spec é literal quanto a isso, e
executá-los no hospedeiro não prova nada sobre a imagem:

```bash
docker compose exec -T web      pytest tests
docker compose exec -T web      mypy
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run typecheck
```

O segundo tem uma armadilha que a spec nomeia: **`mypy` sobre zero arquivo sai com sucesso.**
Um caminho errado dentro da imagem faz F3-09 aprovar sem verificar nada. Confirme que ele
diz quantos arquivos examinou, e que o número bate com o do hospedeiro.

**Medição de tempo, exigida pelo risco de desempenho da spec.** Cronometre
`docker compose exec -T web pytest tests` e a mesma suíte nativa, e registre os dois no
relato. Se a execução em contêiner for desproporcionalmente mais lenta, **isso é achado que
volta como questão** — a saída conhecida (mover o repositório para dentro do WSL) muda o fluxo
de todo mundo e não é decisão deste plano.

**Cerca de escopo**

Não altera `test_health_responde_ok`. Não cria migration nem modelo. Não altera nada em
`frontend/`.

---

### Tarefa 9 — As mutações

**Depende de:** T6, T7, T8 · **Visual:** não

**Arquivos** — nenhum. Esta tarefa **não altera o repositório**: injeta erro, observa a
reprovação e desfaz.

**Contrato**

A spec exige que cada família de verificação prove que sabe reprovar. Sete mutações aqui; a
oitava, da varredura de documentação, é a **h** em T10. Cada uma desfeita antes da seguinte:

| | Mutação | Como aplicar | Precisa reprovar |
|---|---|---|---|
| a | quebrar a verificação de vida do `postgres` (trocá-la por `["CMD-SHELL", "exit 1"]`) | `docker compose down && docker compose up -d --wait` | o `postgres` nunca fica saudável, o `web` **nem chega a ser criado**, e `--wait` sai != 0 |
| b | TensorFlow na imagem `web` | acrescentar `RUN pip install --no-cache-dir tensorflow` ao alvo `web` e reconstruir **só ele** | `import tensorflow` na `web` passa a sair 0, e F3-03 reprova |
| c | derrubar o `worker` | `docker compose stop worker` | a tarefa expira com `TimeoutError`; **saída 1** |
| d | `RUVOR_DB_NAME` inexistente | editar o `.env` **e** `docker compose up -d --wait web` | F3-04 reprova |
| e | renomear o `.env` | `test -z "$(env \| grep '^RUVOR_')" && mv .env .env.guardado && docker compose up -d` | **saída 1**, citando a variável faltando |
| f | trocar **só** `RUVOR_PORT_WEB` (8000 → 8010) | editar **e** `docker compose up -d --wait` | `curl` na porta **antiga** (8000) reprova, e na nova (8010) passa; as outras três seguem respondendo |
| g | erro de tipo no `backend/` | editar um arquivo sob `config/` | `docker compose exec -T web mypy` reprova |

**Três delas dependem de recriar o contêiner.** As mutações **d**, **e** e **f** mexem no
`.env`, que é lido **na criação** do contêiner — sem o `up -d` que recria, o processo em
execução mantém o ambiente antigo e a mutação **não reprova**, dando falso verde justamente
onde a tarefa existe para impedir falso verde.

**A mutação a precisa de `down`, não de `stop`.** Duas armadilhas a tornam vacuosa se feita
do jeito óbvio: `GET /health` **não toca no banco** (`config/views.py` devolve a constante),
então parar o `postgres` deixa o `web` saudável para sempre; e `docker compose up -d web`
**sobe as dependências junto**, religando o que se acabou de parar. O que o
`depends_on: service_healthy` protege é a **criação** do contêiner — e só um ciclo completo
de `down` e `up` a exercita.

**A mutação b custa uma reconstrução.** Reconstruir só o alvo `web` com TensorFlow leva
~90 s e alguns GB; **meça o espaço livre antes** e remova a imagem mutante depois
(`docker image rm`), porque a unidade do sistema tem ~7 GB livres.

**Cada uma se apoia em código de saída, não em texto da saída** — ver
[achado 4](#achado-4-grep-na-saida-e-armadilha).

A mutação **e** é a razão de o `compose.yaml` usar `${VAR:?...}`: sem essa sintaxe, ela
**não reprova** (verificado — saída 0, só um aviso).

**Critério de aceite**

Relato com as sete, cada uma com o comando, o código de saída observado e a confirmação de
que o conjunto volta a subir saudável (`docker compose up -d --wait`) e de que o repositório
voltou ao estado anterior:

```bash
rm -f .env.guardado .env.anterior      # o .gitignore cobre .env, nao estes
test -z "$(git status --porcelain)"
```

Os dois arquivos temporários precisam ser removidos à mão: o `.gitignore` ignora `.env`, e só
ele — deixá-los faria o `git status` reprovar por motivo alheio à mutação.

**Cerca de escopo**

Nada permanece alterado. Se alguma mutação **não** reprovar, é achado que **para a execução**
e volta como correção — é o plano que estava errado.

---

### Tarefa 10 — Documentação

**Depende de:** T6, T7, T8, T9 · **Visual:** não

**Arquivos** — altera: `README.md`, `CLAUDE.md`

**Contrato**

O `README.md` passa a ter `docker compose up` como caminho principal, e a tabela "Comandos do
dia a dia" é reescrita conforme a [D-33](../decisoes/D-33-dia-a-dia-dentro-do-conteiner.md):
backend e frontend por `docker compose exec`, motor no `.venv` nativo.

Além da seção "Executar", **estes trechos ficam falsos e precisam sumir** — lista fechada,
derivada da leitura dos arquivos:

| Arquivo | Trecho |
|---|---|
| `README.md` | *"não há banco, API de negócio nem tela de produto"* |
| `README.md` | *"que responde `GET /health` **sem banco**"* |
| `README.md` | "Pré-requisitos" listando Python e Node como exigências do repositório |
| `README.md` | *"Abra `http://localhost:5173`"* |
| `README.md`, subseção "Backend" | *"O Django lê toda a configuração … e **não tem banco**"* |
| `README.md`, subseção "Backend" | *"**Nada carrega o arquivo** até o F3: as variáveis precisam estar exportadas no shell"* |
| `README.md`, "Comandos do dia a dia" | *"`pytest backend` — não precisa de variável exportada"* |
| `CLAUDE.md` | o parágrafo *"Não há banco…"* **e** o item de lista *"Uma rota, `GET /health`, sem banco"* |

As três linhas da subseção "Backend" e a de "Comandos" são as mais fáceis de esquecer: estão
**dentro** da seção "Executar", que quem corrige assume ter reescrito por inteiro, e sobrevivem
justamente por isso.

O `.env.example` já foi corrigido em T6.

**Critério de aceite**

A varredura precisa **normalizar antes de casar**, e três detalhes decidem se ela funciona:

- **`grep` casa por linha, e dois dos trechos atravessam quebra de linha** no arquivo real
  (*"e não⏎tem banco"*, *"Nada carrega o⏎arquivo"*). Sem juntar as linhas, esses dois nunca
  casam — a varredura passaria deixando exatamente as frases mais fáceis de esquecer.
- **`CLAUDE.md` escreve "Não" com maiúscula** e o README com minúscula; sem `-i`, um dos dois
  escapa.
- O `sed` que remove `**` é **defensivo**: nos arquivos de hoje o negrito envolve as frases,
  não as corta. Fica para não depender disso.

**Os quatro arquivos entram no laço.** `.env.example` e `frontend/.env.example` fazem parte da
mesma lista fechada da spec, e o cabeçalho do primeiro é o que ela chama de *"o mais fácil de
esquecer"* — quem apenas **acrescentasse** as variáveis novas, mantendo o cabeçalho antigo,
passaria em tudo:

```bash
for f in README.md CLAUDE.md .env.example frontend/.env.example; do
  sed -e 's/\*\*//g' -e 's/^[[:space:]]*#[[:space:]]*//' "$f" | tr '\n' ' ' | tr -s ' ' \
    | grep -qiE 'não há banco|sem banco|não tem banco|nada carrega o arquivo|localhost:5173|não precisa de variável exportada|Nada as carrega|encaminha /health para o Django' \
    && { echo "trecho falso sobrevive em $f"; exit 1; }
done
grep -q 'docker compose up' README.md
```

O segundo `sed` remove o `#` de comentário do início de cada linha. Sem ele o `.env.example`
escapa: o cabeçalho quebra linha no meio da frase, e ao juntar as linhas o marcador de
comentário fica **dentro** dela — *"Nada as carrega deste # arquivo"*. Os padrões dos dois
`.env.example` também são curtos de propósito, para não depender de onde a linha quebra.

**Conferido contra os arquivos de hoje:** 6 casamentos no `README.md`, 2 no `CLAUDE.md`, 1 em
cada `.env.example` — os oito trechos da lista, nenhum escapando.

**A frase sobre Python fica de fora da lista de proibidos, de propósito.** O motor continua
exigindo Python 3.12+ ([Resultado esperado 2](../specs/F3-ambiente-local.md#resultado-esperado)),
então banir a redação não bania a afirmação — bastaria escrever "Python 3.12+" para passar
mantendo o pré-requisito errado. O que muda ali é a **estrutura** da seção: Docker vira o
pré-requisito do repositório, e Python passa a ser qualificado como exigência apenas do
motor. Isso é inspeção humana, e está declarado como tal.

E a completude do exemplo, que precisa cobrir também as quatro `RUVOR_PORT_*`, que o
`settings.py` não lê e por isso escapariam de uma varredura derivada só dele:

```bash
for v in SECRET_KEY DEBUG ALLOWED_HOSTS DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD \
         REDIS_URL PORT_WEB PORT_FRONTEND PORT_POSTGRES PORT_REDIS; do
  grep -q "^RUVOR_$v=" .env.example || { echo "falta RUVOR_$v"; exit 1; }
done
```

**Mutação h, obrigatória:** rodar a varredura acima contra os arquivos **antes** da correção
(`git stash` ou `git show HEAD:README.md`) e confirmar que ela sai com **código != 0**. Sem
isso, uma varredura com padrão errado aprova em silêncio — é o critério que mais facilmente
passa vazio de todo o bloco.

A redação em si é inspeção humana.

**Cerca de escopo**

Não altera `ARQUITETURA.md`, `ROADMAP.md` nem `ESTADO.md` — já corrigidos. Não faz o passo
FECHA.

---

## O que fica para o passo FECHA

Depois da revisão final da implementação:

| Atualizar | O quê |
|---|---|
| `docs/ESTADO.md` | bloco fechado, dívida do `RUVOR_ALLOWED_HOSTS` quitada, novo estado do repositório |
| `docs/ROADMAP.md` | F3 marcado ✅ |
| `docs/aprendizados.md` | **o ponto de montagem do Postgres 18**; o `.env` ausente que não falha; grep na saída casando com o traceback. E a **poda** do verbete *"`DATABASES = {}` não fica vazio"*, que descreve um teste removido |
| Cabeçalho desta spec e deste plano | status final |
| `docs/specs/README.md` e `docs/planos/README.md` | tabelas de índice |

`CLAUDE.md` já é atualizado em T10, porque o bloco muda o que existe no repositório.
