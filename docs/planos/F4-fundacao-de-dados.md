# F4 — Plano de implementação

**Spec:** [F4 — Fundação de dados](../specs/F4-fundacao-de-dados.md)
**Status:** ✅ **aprovado** (2026-09-05) — em implementação
Duas rodadas. Os critérios de aceite foram executados contra o contêiner de pé durante a
revisão; os quatro achados da segunda rodada foram absorvidos antes do portão.
**Objetivo:** `migrate` num banco vazio cria os quatro esquemas e as tabelas do projeto;
existe Organização e usuário próprio na primeira migration; nenhuma tabela de domínio nasce
no `public`; e a organização fixa do Marco 1 existe.

**Commit por tarefa**, direto na `main` ([D-31](../decisoes/D-31-trabalho-direto-na-main.md)).
Sem ramo.

---

## Como ler este plano

Segue o [PROCESSO §5](../PROCESSO.md#5-anatomia-de-um-plano): **contratos, não corpos**. Entra
conteúdo literal em três lugares, e só neles:

1. **Onde o conteúdo é o contrato** — os fragmentos de `backend/pyproject.toml` e de
   `infra/backend.Dockerfile`, e os `db_table` dos modelos. Não existe "implementação"
   separada do valor.
2. **Onde a lógica é sutil e a falha é silenciosa** — a migration de esquemas (a ordem das
   operações decide se funciona), a migration de dados (idempotência), e a consulta de
   verificação de F4-02 (que passa vazia se for escrita como amostra).
3. **Em nada mais.** Os corpos dos modelos, dos gerentes e dos testes não entram: a spec
   já fixa campos, tipos e comportamento, e há padrão no repositório para imitar.

Toda tarefa é executável por alguém que nunca participou da conversa.

---

## O que já foi medido, e o que não foi

O contrato central deste bloco — esquema embutido no `db_table` — **foi medido de ponta a
ponta durante a revisão da spec**, contra o `postgres:18` do `compose`, com um projeto Django
6.1 descartável contendo exatamente os dois modelos desta spec. O banco de sonda foi removido
e o `ruvor` não foi tocado.

| Medido | Resultado |
|---|---|
| Tabelas criadas | `core`: `organization`, `user`, `user_groups`, `user_user_permissions`. `public`: `django_migrations`, `django_content_type`, `auth_permission`, `auth_group`, `auth_group_permissions`. Exatamente a lista fechada da spec |
| Nomes de índice e restrição | saem **sem** esquema embutido — `organization_slug_key`, `user_organization_id_599fe387_fk_organization_id` |
| `migrate` num banco vazio | 15 migrations, código 0 |
| Segunda execução | `No migrations to apply.`, código 0 |
| `makemigrations --check --dry-run` | `No changes detected` |
| `migrate accounts zero` com `reverse_sql` | `Unapplying acc.0001_initial... OK` |
| `packages = ["config", "apps"]` com `backend/apps/` ausente | `error: package directory 'apps' does not exist` |
| `packages = ["config", "apps"]` com os diretórios presentes | instalação editável conclui; `apps.accounts` **não** precisa ser listado |
| `pytest.mark.django_db` no teste do `/health` | **não** faz o teste falhar — a marca concede acesso, não exige uso |

**O que não foi medido, e por que o plano não inventa:** a correção do `Dockerfile`. O padrão
está no próprio arquivo — ele já copia `backend/config/__init__.py` antes do
`pip install -e` —, e a T1 existe para prová-lo por construção real, não por dedução. Se a
construção falhar, é erro de plano e a T1 para, conforme o [PROCESSO §6](../PROCESSO.md#quando-parar).

---

## O que este plano decide

Decisões de implementação que a spec deixou em aberto de propósito, tomadas aqui para que
sete tarefas não as derivem de sete jeitos:

| Decisão | Valor |
|---|---|
| Rótulo do app | `accounts` — derivado do último componente de `apps.accounts`, que é o padrão do Django |
| `AUTH_USER_MODEL` | `"accounts.User"` |
| Ordem dentro da `0001` | `RunSQL` dos quatro esquemas **primeiro**, depois os dois `CreateModel` |
| Onde os esquemas são criados | na `0001` do `accounts`, e não numa migration de app separado — não há segundo app, e um app só para criar esquema é cerimônia sem dono |
| Chave da organização do Marco 1 na migration de dados | o `slug`, por `get_or_create`, nunca o `id` |
| Comprimento dos campos de texto | os da spec: `name` 120, `slug` 60, `email` 254 |

**O que este plano NÃO decide:** nada sobre ferramenta de estilo (é do F5), nada sobre
endpoint (é do Marco 1), e nada sobre o gerente com escopo por organização, que a
[D-41](../decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md) atribui ao M2.2.

---

## Rastreabilidade

| Requisito | Tarefa que o cumpre | Tarefa que o prova |
|---|---|---|
| F4-01 — os quatro esquemas existem | T3 | T3, T5 |
| F4-02 — nenhuma tabela de domínio no `public` | T2, T3 | T3, T5 |
| F4-03 — organização do Marco 1, idempotente | T4 | T4, T5 |
| F4-04 — `AUTH_USER_MODEL` e organização obrigatória | T2, T3 | T5 |
| F4-05 — `migrate` do zero, segunda execução sem efeito | T3 | T3 |
| F4-06 — `makemigrations --check` limpo | T3 | T3 |
| F4-07 — mypy cobre o código novo | T1 | T1, T2, T3, T4, T5 |
| F4-08 — suíte passa, `/health` sem banco | T5 | T5, T6 |
| F4-09 — a imagem constrói com o pacote novo | T1 | T1 |
| F4-10 — documentação não mente | T7 (fatos) + FECHA (status) | T7 (fatos) + FECHA (status) |

As onze mutações da spec ficam concentradas na **T6**, como no F3.

---

## Mapa de arquivos

### Criados

| Arquivo | Tarefa |
|---|---|
| `backend/apps/__init__.py` | T1 |
| `backend/apps/accounts/__init__.py` | T1 |
| `backend/apps/accounts/apps.py` | T1 |
| `backend/apps/accounts/migrations/__init__.py` | T1 |
| `backend/apps/accounts/models.py` | T2 |
| `backend/apps/accounts/managers.py` | T2 |
| `backend/apps/accounts/migrations/0001_esquemas_organization_user.py` | T3 |
| `backend/apps/accounts/migrations/0002_marco1_organization.py` | T4 |
| `backend/tests/test_esquemas.py` | T5 |
| `backend/tests/test_organizacao.py` | T5 |
| `backend/tests/test_usuario.py` | T5 |

### Alterados

| Arquivo | Tarefa | O que muda |
|---|---|---|
| `backend/pyproject.toml` | T1 | `packages` e `[tool.mypy] files` |
| `infra/backend.Dockerfile` | T1 | duas linhas `COPY` antes do `pip install` |
| `backend/config/settings.py` | T1, T2 | `INSTALLED_APPS` (T1 e T2), `AUTH_USER_MODEL` (T2) |
| `README.md` | T7 | linha do `migrate` em "Comandos do dia a dia" |
| `CLAUDE.md` | T7 | o estado do repositório |
| `docs/ESTADO.md` | T7 | as duas afirmações factuais que o F4 falsifica **e** a linha de dívida da D-41. A **posição** é do FECHA |
| `docs/ARQUITETURA.md` | T7 | `apps/` deixa de ser futuro; a tabela de esquemas ganha o `core` |
| `docs/specs/README.md`, `docs/planos/README.md` | T7 | linha do F4, com situação 🟡. O ✅ é do FECHA |
| `docs/ROADMAP.md` | **FECHA** | F4 marcado ✅ — só depois da revisão final |
| `docs/aprendizados.md` | **FECHA** | o que custou tempo; só se sabe ao fim |

### Intocados, e é contrato que fiquem

`backend/config/settings_test.py` — nada no F4 acrescenta variável obrigatória.
`backend/config/celery.py` — o registro por import explícito continua necessário: o app novo
entra em `INSTALLED_APPS`, mas não tem tarefa, e a descoberta automática continua sem alcançar
`config.tasks`.
`backend/config/views.py` e `urls.py` — `/health` é contrato congelado desde o F2b.
`compose.yaml`, `engine/`, `frontend/` — fora do bloco.

---

## Ordem e dependências

```
T1  pacote, empacotamento, imagem
     ↓
T2  modelos, gerente, AUTH_USER_MODEL
     ↓
T3  migration 0001 — esquemas e tabelas
     ↓
T4  migration 0002 — organização do Marco 1
     ↓
T5  testes da suíte
     ↓
T6  mutações
     ↓
T7  documentação
```

**Cadeia estrita, sem paralelo.** Cada tarefa toca o estado do banco ou o estado do pacote que
a seguinte pressupõe. Não há dois arquivos disjuntos que compensem o risco de intercalar.

---

### Tarefa 1 — O pacote `apps/accounts`, o empacotamento e a imagem

**Depende de:** nada
**Visual:** não

**Arquivos**
- cria: `backend/apps/__init__.py`, `backend/apps/accounts/__init__.py`,
  `backend/apps/accounts/apps.py`, `backend/apps/accounts/migrations/__init__.py`
- altera: `backend/pyproject.toml`, `infra/backend.Dockerfile`, `backend/config/settings.py`

**Contrato**

Os três arquivos que mudam entram literais, porque neles o conteúdo **é** o contrato.

`backend/pyproject.toml` — duas linhas, e só elas:

```toml
packages = ["config", "apps"]
```

```toml
files = ["config", "apps", "manage.py", "tests"]
```

`infra/backend.Dockerfile` — duas linhas novas, imediatamente **antes** do
`RUN pip install --no-cache-dir -e "./backend[dev]"` do estágio `base`, ao lado da linha que
já copia o `config`:

```dockerfile
COPY backend/apps/__init__.py backend/apps/__init__.py
COPY backend/apps/accounts/__init__.py backend/apps/accounts/__init__.py
```

`backend/config/settings.py` — `INSTALLED_APPS` passa a:

```python
INSTALLED_APPS = ["rest_framework", "apps.accounts"]
```

`apps.py` declara `name = "apps.accounts"`. O rótulo resultante é `accounts`, e é ele que
nomeia as migrations.

**As três mudanças vão no mesmo commit, e isso é o ponto da tarefa.** Declarar `apps` em
`packages` sem criar os `__init__.py` e sem corrigir o `Dockerfile` produz um commit em que a
imagem **não constrói** — medido: `error: package directory 'apps' does not exist`.

**Critério de aceite**

```bash
# F4-09 — a imagem constrói do zero com o pacote novo declarado.
# Os dois alvos, e nao so o `web`: eles compartilham o estagio `base`, que e onde o
# `pip install -e` roda. Reconstruir so um deixa o conjunto com duas versoes do `base`.
docker compose build --no-cache web worker

# o app carrega e as checagens do Django passam
docker compose up -d --wait
docker compose exec -T web python manage.py check

# F4-07 — o mypy passa E a lista de arquivos verificados nomeia o pacote novo.
# Contar arquivos nao basta: e a lista que precisa citar `apps`. O formato da linha
# foi conferido no conteiner: LOG: Found source: BuildSource(path='config/settings.py', ...)
docker compose exec -T web mypy --verbose 2>&1 | grep -q "path='apps/"
docker compose exec -T web mypy

# a suite continua passando
docker compose exec -T web pytest tests
```

**Cerca de escopo**

Não cria modelo, não cria migration, não toca em `AUTH_USER_MODEL`, não acrescenta
`contenttypes` nem `auth`. Não mexe em `compose.yaml`.

---

### Tarefa 2 — `Organization`, `User` e o `AUTH_USER_MODEL`

**Depende de:** T1
**Visual:** não

**Arquivos**
- cria: `backend/apps/accounts/models.py`, `backend/apps/accounts/managers.py`
- altera: `backend/config/settings.py`

**Contrato**

Os campos são os da [spec](../specs/F4-fundacao-de-dados.md#organization) e não se repetem
aqui. O que entra literal é o que **não** é derivável: os dois `db_table`, porque o
identificador em duas partes é o contrato da
[D-38](../decisoes/D-38-public-guarda-o-encanamento.md) e um erro de aspas aqui muda o esquema
em que a tabela nasce.

```python
# Organization
class Meta:
    db_table = 'core"."organization'

# User
class Meta:
    db_table = 'core"."user'
```

`settings.py` recebe, no mesmo commit:

```python
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "apps.accounts",
]

AUTH_USER_MODEL = "accounts.User"
```

**`MIDDLEWARE` não muda.** A exigência de `AuthenticationMiddleware` só dispara com
`LoginRequiredMiddleware` presente, e ele não está — a checagem é o `auth.E013`, em
`django/contrib/auth/checks.py:258`. A consequência está registrada na
[D-39](../decisoes/D-39-usuario-proprio-autentica-por-email.md); o fato está na fonte.

`managers.py` traz o gerente do usuário, com `create_user` e `create_superuser` que **exigem
organização**. É a primeira das duas camadas de obrigatoriedade de F4-04; a segunda é o
`NOT NULL` da coluna, que vem da própria definição do campo.

**Critério de aceite**

```bash
docker compose up -d --wait

# o modelo trocado e reconhecido, e as checagens do auth passam
docker compose exec -T web python manage.py check

# Via `manage.py shell` com entrada padrao, e nao `python -c`: o conteiner NAO tem
# DJANGO_SETTINGS_MODULE no ambiente (conferido), entao `python -c` nao sobe o Django.
# A entrada padrao tambem evita escapar as aspas do db_table.
docker compose exec -T web python manage.py shell <<'PY'
from django.conf import settings
from django.contrib.auth import get_user_model
U = get_user_model()
assert settings.AUTH_USER_MODEL == "accounts.User", settings.AUTH_USER_MODEL
assert U._meta.db_table == 'core"."user', U._meta.db_table
assert U.USERNAME_FIELD == "email"
assert not U._meta.get_field("organization").null
print("ok")
PY

# os dois modelos estao registrados e pendentes de migration —
# e o codigo de saida 1 aqui e o esperado, porque a 0001 so nasce na T3
docker compose exec -T web python manage.py makemigrations --check --dry-run; test $? -eq 1

docker compose exec -T web mypy
docker compose exec -T web pytest tests
```

**Cerca de escopo**

Não cria migration — é da T3. Não cria a base abstrata nem gerente com escopo por
organização: a [D-41](../decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md)
os atribui ao M2.2. Não cria `superuser` nenhum.

---

### Tarefa 3 — Migration `0001`: os quatro esquemas e as duas tabelas

**Depende de:** T2
**Visual:** não

**Arquivos**
- cria: `backend/apps/accounts/migrations/0001_esquemas_organization_user.py`

**Contrato**

A migration é gerada por `makemigrations` e **editada** para receber, como **primeira**
operação, a criação dos esquemas. A ordem é o contrato: `CreateModel` antes do `CREATE
SCHEMA` falha, porque a tabela não tem onde nascer.

O bloco entra literal por ser lógica sutil de falha silenciosa — sem `reverse_sql` a
migration fica irreversível e `migrate accounts zero` deixa de funcionar, que é o caminho
normal de refazer o bloco enquanto não há dado:

```python
operations = [
    migrations.RunSQL(
        sql=[
            "CREATE SCHEMA IF NOT EXISTS core",
            "CREATE SCHEMA IF NOT EXISTS bronze",
            "CREATE SCHEMA IF NOT EXISTS silver",
            "CREATE SCHEMA IF NOT EXISTS gold",
        ],
        reverse_sql=[
            "DROP SCHEMA IF EXISTS gold",
            "DROP SCHEMA IF EXISTS silver",
            "DROP SCHEMA IF EXISTS bronze",
            "DROP SCHEMA IF EXISTS core",
        ],
    ),
    # ... os dois CreateModel gerados por makemigrations, nesta ordem
]
```

`DROP SCHEMA` sem `CASCADE` de propósito: reverter com tabela dentro **deve** falhar em vez
de apagar dado. Na volta completa, os `CreateModel` já removeram as tabelas antes.

**Critério de aceite**

```bash
# banco do zero, para que o criterio nao aprove sobre estado anterior
docker compose down -v && docker compose up -d --wait

# F4-05 — migrate do zero
docker compose exec -T web python manage.py migrate

# F4-05 — segunda execucao nao aplica nada
docker compose exec -T web python manage.py migrate 2>&1 | grep -q "No migrations to apply"

# F4-06 — modelo e migration em sincronia
docker compose exec -T web python manage.py makemigrations --check --dry-run

# F4-01 e F4-02 — lista fechada, esquema por tabela.
# A consulta compara o conjunto INTEIRO; amostra aprovaria com uma tabela no lugar errado.
docker compose exec -T postgres psql -U ruvor -d ruvor -tAc "
  SELECT schemaname||'.'||tablename FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog','information_schema')
  ORDER BY 1" | tr -d '\r' | sort > /tmp/f4-tabelas.txt
cat > /tmp/f4-esperado.txt <<'EOF'
core.organization
core.user
core.user_groups
core.user_user_permissions
public.auth_group
public.auth_group_permissions
public.auth_permission
public.django_content_type
public.django_migrations
EOF
diff /tmp/f4-esperado.txt /tmp/f4-tabelas.txt

# F4-01 — os quatro esquemas, inclusive os que ainda nao tem tabela
docker compose exec -T postgres psql -U ruvor -d ruvor -tAc "
  SELECT count(*) FROM information_schema.schemata
  WHERE schema_name IN ('core','bronze','silver','gold')" | tr -d '\r ' | grep -qx 4

# reversibilidade
docker compose exec -T web python manage.py migrate accounts zero
docker compose exec -T web python manage.py migrate

# a tarefa produz codigo verificado
docker compose exec -T web mypy
docker compose exec -T web pytest tests
```

**Cerca de escopo**

Não cria a organização do Marco 1 — é da T4. Não escreve teste da suíte — é da T5. Não edita
os `CreateModel` gerados: o que a T2 definiu no modelo é o que vale.

---

### Tarefa 4 — Migration `0002`: a organização do Marco 1

**Depende de:** T3
**Visual:** não

**Arquivos**
- cria: `backend/apps/accounts/migrations/0002_marco1_organization.py`

**Contrato**

Migration de dados, separada da de esquema. Entra literal por ser exatamente o caso de falha
silenciosa: uma versão que use `create()` em vez de `get_or_create()` passa na primeira
execução e duplica na segunda, e o defeito só aparece em outra máquina.

```python
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps


def cria_organizacao_do_marco1(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Organization = apps.get_model("accounts", "Organization")
    Organization.objects.get_or_create(slug="ruvor", defaults={"name": "Ruvor"})


def remove_organizacao_do_marco1(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Organization = apps.get_model("accounts", "Organization")
    Organization.objects.filter(slug="ruvor").delete()


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_esquemas_organization_user")]

    operations = [
        migrations.RunPython(cria_organizacao_do_marco1, remove_organizacao_do_marco1),
    ]
```

**Este bloco é o arquivo inteiro, e não excerto** — ao contrário do da T3, que mostra só a
lista `operations`. Os três imports e a classe estão aqui porque sem eles o arquivo não
importa e o `MigrationLoader` o recusa.

**As anotações não são estilo, são obrigação.** A T1 põe `apps` em `[tool.mypy] files`, e o
`pyproject.toml` tem `strict = true` — as migrations moram dentro do pacote verificado. Foi
medido: sem elas, o bloco reprova com dois `no-untyped-def`. A `0001` no formato que o
`makemigrations` gera passa sem ajuste; só as funções da `RunPython` precisam de anotação.

`apps.get_model` e não o import de `models.py`: o modelo histórico é o único que corresponde
ao estado daquele ponto da história, e importar o vivo quebra a migration no dia em que o
modelo mudar.

**Critério de aceite**

```bash
docker compose up -d --wait
docker compose exec -T web python manage.py migrate

# F4-03 — existe exatamente uma, com o slug congelado
docker compose exec -T postgres psql -U ruvor -d ruvor -tAc \
  "SELECT count(*) FROM core.organization WHERE slug='ruvor'" | tr -d '\r ' | grep -qx 1
docker compose exec -T postgres psql -U ruvor -d ruvor -tAc \
  "SELECT name FROM core.organization WHERE slug='ruvor'" | tr -d '\r ' | grep -qx Ruvor

# Idempotencia — e o `--fake` e o ponto.
#
# Desaplicar de verdade executaria `remove_organizacao_do_marco1`, que APAGA a linha:
# a reaplicacao seguinte nao encontraria nada, e uma implementacao com `create()` passaria.
# Com `--fake`, o registro e desfeito e a LINHA FICA — entao a reaplicacao roda a migration
# de dados contra um banco que ja tem a organizacao, que e exatamente o caso que
# `get_or_create` existe para tratar. Conferido na fonte: `unapply_migration(..., fake=True)`
# nao executa as operacoes, so registra (`db/migrations/executor.py`).
docker compose exec -T web python manage.py migrate accounts 0001 --fake
docker compose exec -T web python manage.py migrate
docker compose exec -T postgres psql -U ruvor -d ruvor -tAc \
  "SELECT count(*) FROM core.organization" | tr -d '\r ' | grep -qx 1

# a reversao de verdade tambem precisa funcionar, para `migrate accounts zero` continuar valendo
docker compose exec -T web python manage.py migrate accounts 0001
docker compose exec -T postgres psql -U ruvor -d ruvor -tAc \
  "SELECT count(*) FROM core.organization" | tr -d '\r ' | grep -qx 0
docker compose exec -T web python manage.py migrate

# a tarefa produz codigo verificado
docker compose exec -T web mypy
docker compose exec -T web pytest tests
```

**Cerca de escopo**

Não cria usuário nenhum. Não acrescenta campo ao modelo.

---

### Tarefa 5 — Os testes da suíte

**Depende de:** T4
**Visual:** não

**Arquivos**
- cria: `backend/tests/test_esquemas.py`, `backend/tests/test_organizacao.py`,
  `backend/tests/test_usuario.py`

**Contrato**

Os três usam `django_db_blocker`, e não a marca `django_db`, pelo motivo que o
`test_conexao_com_o_banco` do F3 já documenta: a marca conecta em `test_<nome>` e não
exercita o banco configurado.

| Arquivo | O que prova |
|---|---|
| `test_esquemas.py` | F4-01 e F4-02 — os quatro esquemas existem, e o conjunto de `esquema.tabela` é **idêntico** à lista fechada. Comparar conjunto inteiro é o contrato: `assertIn` aprovaria com tabela no lugar errado |
| `test_organizacao.py` | F4-03 — existe exatamente uma organização com `slug='ruvor'` e `name='Ruvor'` |
| `test_usuario.py` | F4-04, nas **duas camadas**, em testes separados: (a) `create_user` sem organização levanta; (b) a coluna `organization_id` é `NOT NULL` no banco. Mais: `AUTH_USER_MODEL == "accounts.User"`, e a `0001` do `accounts` contém a criação do usuário — migration posterior reprova |

**A lista de nove tabelas existe em dois lugares** — o heredoc do critério da T3 e o
`test_esquemas.py` — porque a T3 roda antes de o teste existir. **A partir da T5 o teste é a
fonte**, e o critério da T5 executa também o comando da T3: se as duas divergirem, uma das
duas reprova. Duplicata que ninguém confronta é como a lista fechada apodrece.

**A suíte passa a exigir um banco migrado**, e não apenas alcançável como no F3. É
consequência declarada da spec; quem rodar `pytest` com o conjunto de pé mas sem `migrate`
verá esses três reprovarem, e é o comportamento certo.

**Critério de aceite**

```bash
docker compose up -d --wait
docker compose exec -T web python manage.py migrate

# F4-08 — a suite inteira, incluindo o teste de /health do F2b, sem marca de banco
docker compose exec -T web pytest tests
docker compose exec -T web mypy

# A duplicata da lista de nove tabelas morre AQUI: a lista esperada e extraida do
# proprio teste e confrontada com o banco. A partir desta tarefa o teste e a fonte,
# e o heredoc da T3 deixa de ter voto. Comentario nao confronta nada — por isso e
# comando.
# Nomes proprios da T5, e `rm` antes: a T3 grava em /tmp/f4-tabelas.txt, e um
# arquivo velho dela sobrevivendo aqui daria falso verde numa execucao parcial.
rm -f /tmp/f4t5-do-teste.txt /tmp/f4t5-tabelas.txt
grep -oE '(core|public)\.[a-z_]+' backend/tests/test_esquemas.py | sort -u > /tmp/f4t5-do-teste.txt
docker compose exec -T postgres psql -U ruvor -d ruvor -tAc "
  SELECT schemaname||'.'||tablename FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog','information_schema')
  ORDER BY 1" | tr -d '\r' | sort > /tmp/f4t5-tabelas.txt
diff /tmp/f4t5-do-teste.txt /tmp/f4t5-tabelas.txt
```

**Consequência para quem escreve o teste:** as nove tabelas precisam aparecer em
`test_esquemas.py` na forma literal `esquema.tabela` — é o que torna a extração possível, e é
o que impede a lista de existir em dois lugares que ninguém confronta.

**Cerca de escopo**

Não altera `test_health.py` nem `test_conexao_com_o_banco`. Não cria modelo só para teste.

---

### Tarefa 6 — As mutações

**Depende de:** T5
**Visual:** não

**Arquivos**
- nenhum, ao fim. Cada mutação é aplicada, executada, observada e revertida: arquivo
  **rastreado** volta com `git checkout --`, nunca por reescrita — o
  `Set-Content -Encoding utf8` do PowerShell 5.1 grava BOM e suja o arquivo, como o
  [aprendizados.md](../aprendizados.md) registra. Arquivo **novo** sai com `rm`.

**Contrato**

As onze da spec. Cada uma precisa reprovar a verificação apontada, e o relato registra o
**comando, a saída e o código de saída** — não "reprovou".

| # | Mutação | Precisa reprovar | Como aplicar |
|---|---|---|---|
| a | Remover o `CREATE SCHEMA` do **`gold`** da `0001` | F4-01 | `down -v` + `up -d --wait` + `migrate` |
| b | Trocar um `db_table` pelo nome sem esquema | F4-02 | `down -v` + `up -d --wait` + `migrate` |
| c | Trocar `get_or_create` por `create` na `0002` | F4-03, na reaplicação | `migrate accounts 0001 --fake` + `migrate` |
| d | Mover a criação do usuário para uma `0003` | F4-04 | `down -v` + `up -d --wait` + `migrate`; **cria arquivo novo** |
| e | Tirar a exigência de organização do `create_user` | F4-04, camada do gerente | `pytest tests` |
| f | Declarar o `organization` do usuário com `null=True` | F4-04, camada do banco | migration nova + `down -v` + `migrate` |
| g | Trocar o `RunSQL` dos esquemas por um comentário dizendo "criar à mão" | F4-05 | `down -v` + `up -d --wait` + `migrate` |
| h | Acrescentar campo ao modelo sem gerar migration | F4-06 | `makemigrations --check --dry-run` |
| i | Tirar `apps` de `[tool.mypy] files` | F4-07 | `mypy --verbose` |
| j | Fazer a view do `/health` tocar no banco | F4-08 | `pytest tests` |
| k | Declarar `apps` em `packages` sem copiá-lo no `Dockerfile` | F4-09 | `build --no-cache web` |

**Seis delas exigem recriar o banco, e sem isso não reprovam.** `a`, `b`, `d`, `f` e `g`
mudam o que a migration produz, e o banco já migrado continua com as tabelas onde estavam: a
verificação de F4-01/F4-02 não se move e a mutação dá **falso verde**, justamente na tarefa
que existe para impedir falso verde. É o mesmo achado que o F3 registrou. Sempre
`docker compose down -v && docker compose up -d --wait` antes, e `migrate` depois.

**A mutação `c` só reprova com `--fake`.** Desaplicar de verdade executa a função de reversão,
que apaga a linha — e aí `create()` passa. É a razão de o critério da T4 usar `--fake`, e a
razão de esta linha existir aqui.

**`gold` e não `core` na mutação `a`.** Removendo o `core`, quem quebra é o `migrate` — e aí
reprova F4-05, não F4-01, que é o alvo declarado. Com o `gold`, o `migrate` passa e a contagem
de esquemas reprova, que é o que a mutação existe para mostrar.

**As mutações `d` e `f` criam arquivo novo, e `git checkout --` não as desfaz.** As duas
acrescentam migration (`0003`), e arquivo não rastreado sai com `rm`. O `git status` limpo ao
fim é o que pega o esquecimento.

**A mutação `k` custa minutos** — é reconstrução sem cache. Deixe-a por último.

**A mutação `j` é pela view, e isso é decidido, não escolha.** Acrescentar
`pytest.mark.django_db` ao teste **não** o faz falhar — foi medido: a marca concede acesso ao
banco, nunca exige que ele seja usado. Quem garante F4-08 é o bloqueio do pytest-django sobre
o teste **sem** marca.

**Critério de aceite**

As onze aplicadas e revertidas, com a saída de cada uma no relato, e `git status` limpo ao
fim. Uma mutação que **passe** é achado, e a tarefa para: significa que a verificação
correspondente não sabe reprovar, e o defeito está no plano, não no código.

**Cerca de escopo**

Não corrige nada. Não deixa arquivo alterado.

---

### Tarefa 7 — Documentação, e a dívida registrada

**Depende de:** T6
**Visual:** não

**Arquivos**
- altera: `README.md`, `CLAUDE.md`, `docs/ESTADO.md`, `docs/ARQUITETURA.md`,
  `docs/specs/README.md`, `docs/planos/README.md`

**Contrato**

**A divisão entre esta tarefa e o passo FECHA é explícita, e é o que evita as duas escreverem
o mesmo arquivo com instruções opostas.**

| Quem | O quê | Por quê |
|---|---|---|
| **T7** | o que já é **fato** quando ela roda: o código existe, as migrations existem, o banco tem os esquemas | não depende de a revisão final passar |
| **FECHA** | o que é **status**: bloco fechado, posição, próximo passo, cabeçalhos de status | mentiria se a revisão final reprovasse |

Por isso a T7 **não toca em `docs/ROADMAP.md`** e não mexe na posição do `ESTADO.md`.

O que a T7 faz:

1. `README.md` — "Comandos do dia a dia" ganha
   `docker compose exec -T web python manage.py migrate`.
2. `CLAUDE.md` — o backend deixa de ser "projeto Django sem app de domínio", e o parágrafo de
   estado do repositório passa a citar a fundação de dados.
3. `docs/ARQUITETURA.md` — a tabela de camadas ganha o `core`, e a nota *"`apps/` nasce no
   F4"* deixa de ser futuro.
4. `docs/ESTADO.md` — as duas afirmações **factuais** que o F4 falsifica ("Ainda não há
   migrations…" e "`INSTALLED_APPS` ainda é só `rest_framework`…"), mais a linha nova na
   tabela **"Dívida registrada"**: o filtro automático por organização, adiado para o M2.2,
   citando a [D-41](../decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md).
5. `docs/specs/README.md` e `docs/planos/README.md` — linha do F4, com situação
   **🟡 em revisão final**. O ✅ é do FECHA.

A dívida do item 4 é a que sustenta a resolução inteira do filtro adiado. Sem ela, "adiado"
vira "esquecido" — e é por isso que ela tem verificação própria, ancorada **na tabela certa**,
em vez de confiar em quem escreve.

**Critério de aceite**

```bash
# F4-10, parte da T7 — nenhum dos trechos factuais sobrevive. Sao SETE das dez linhas
# da lista fechada da spec; as outras tres sao do FECHA.
# A varredura precisa reprovar contra os arquivos de HOJE: rode-a antes de editar,
# confirme que os cinco primeiros ACUSAM, e so entao edite.
! grep -q "projeto Django sem app de domínio" CLAUDE.md
! grep -q "Ainda não há migrations" docs/ESTADO.md
! grep -q "INSTALLED_APPS. ainda é só" docs/ESTADO.md
! grep -q "apps/. nasce no F4" docs/ARQUITETURA.md
! grep -q "Existem o \*\*motor\*\*, o \*\*casco da aplicação\*\* e o \*\*ambiente local em contêiner\*\*" CLAUDE.md

# as ausencias que precisam passar a existir
grep -q "manage.py migrate" README.md
grep -q '`core`' docs/ARQUITETURA.md
grep -qE "^\| \[?F4" docs/specs/README.md
grep -qE "^\| \[?F4" docs/planos/README.md

# A divida, ancorada NA TABELA e nao no arquivo: a linha precisa estar depois do
# titulo "Divida registrada" e antes do proximo titulo de secao. `grep -q D-41` no
# arquivo inteiro aprovaria com a citacao em qualquer lugar.
awk '/^## Dívida registrada/,/^## [^D]/' docs/ESTADO.md | grep -q "D-41"
```

**Cerca de escopo**

Não altera código. **Não toca em `docs/ROADMAP.md`, nem na posição do `ESTADO.md`, nem em
`docs/aprendizados.md`, nem nos cabeçalhos de status desta spec e deste plano** — os cinco são
do FECHA. Não marca o bloco como fechado.

---

## O que fica para o passo FECHA

Depois da revisão final da implementação, e não antes. É a **outra metade de F4-10** — o que
seria mentira se a revisão reprovasse:

| Arquivo | O quê |
|---|---|
| `docs/ROADMAP.md` | a linha do F4 na tabela da Fundação passa de ⬜ a ✅ |
| `docs/ESTADO.md` | a posição — "**Bloco:** F3 fechado… F4 é o próximo" — e a seção "Próximo passo", que passa a apontar o F5 |
| `docs/specs/README.md`, `docs/planos/README.md` | a situação do F4 passa de 🟡 a ✅ |
| cabeçalho de status **desta** spec e **deste** plano | deixam de dizer "em revisão" |
| `docs/aprendizados.md` | o que custou tempo e reincidiria — só se sabe depois de executar |

**Verificação do FECHA**, que fecha as seis linhas restantes da
[lista fechada da spec](../specs/F4-fundacao-de-dados.md#o-que-fica-falso):

```bash
! grep -q "F4 é o próximo" docs/ESTADO.md
! grep -q "Escrever a spec do F4" docs/ESTADO.md
! grep -qE '^\| ⬜ \| \*\*F4' docs/ROADMAP.md

# Os cabecalhos de status sao verificados por afirmacao, e nao por negacao.
# `! grep -q "aguardando revisão"` NAO serve: o cabecalho da spec ja diz "plano em
# escrita" desde o portao humano, entao a negativa aprova sem ninguem ter mexido nele.
#
# E o padrao vai ANCORADO na linha de status. Sem a ancora, `grep -q "executado e
# fechado"` casaria com esta propria linha de criterio, dentro deste arquivo, e
# aprovaria vazio — conferido.
grep -q '^\*\*Status:\*\* ✅ \*\*implementada e fechada\*\*' docs/specs/F4-fundacao-de-dados.md
grep -q '^\*\*Status:\*\* ✅ \*\*executado e fechado\*\*' docs/planos/F4-fundacao-de-dados.md
```

**A conta:** a T7 cobre sete linhas da lista fechada (1, 2, 3, 6, 7, 9 e 10 da tabela da
spec); o FECHA cobre três (4, 5 e 8). Juntas, as dez — e é por isso que a rastreabilidade
atribui F4-10 às duas, e não só à T7. Os dois `grep` de cabeçalho **não** são da lista
fechada: são o item do [PROCESSO §3](../PROCESSO.md#o-passo-fecha) sobre spec e plano ficarem
dizendo "aguardando revisão" para sempre.
