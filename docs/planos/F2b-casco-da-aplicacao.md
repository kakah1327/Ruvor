# F2b — Plano de implementação

**Spec:** [F2b — Casco da aplicação](../specs/F2b-casco-da-aplicacao.md)
**Status:** ✅ aprovado (2026-09-01) · 🟡 em execução

**Objetivo:** criar o projeto Django e o projeto React funcionais, com a identidade Ruvor,
provar que os dois sobem e conversam, e remover o frontend do protótipo.

**Commit por tarefa**, direto na `main` ([D-31](../decisoes/D-31-trabalho-direto-na-main.md)).
Sem ramo.

---

## Como ler este plano

Segue o [PROCESSO §5](../PROCESSO.md#5-anatomia-de-um-plano): contratos, não corpos — com as
duas exceções que a própria regra prevê. Este bloco é quase todo configuração de projeto
novo, então o conteúdo literal aparece mais do que no F2a: **em projeto novo não há padrão
para imitar**, e cada arquivo de configuração *é* o contrato. Dois testes entram literais
porque **a lógica é sutil e a falha é silenciosa** (T3 e T5).

Toda tarefa é executável por alguém que nunca participou da conversa.

**Tudo o que este plano afirma sobre ferramenta foi executado antes de ser escrito**, num
projeto descartável com as versões listadas abaixo, em 2026-09-01 — e a revisão adversarial
reexecutou os conteúdos literais **tal como estão neste plano**, inclusive os que o projeto
descartável não tinha idênticos (`views.py` separado, `manage.py`/`wsgi`/`asgi` gerados pelo
Django, `.npmrc`, instalação editável). Onde o plano diz "verificado", é isso que significa.

---

## O que este plano decide

Pontos que a spec deixa em aberto ou que o [ESTADO](../ESTADO.md#aberto-e-aguardando-decisão)
pede que o plano resolva. Cada um é reversível; nenhum contradiz decisão registrada.

| Tema | Decisão | Motivo |
|---|---|---|
| **Versões do backend** | faixas mínimas = versões correntes em 2026-09-01: Django 6.1, DRF 3.18, mypy 2.3, django-stubs 6.1, pytest 9.1, pytest-django 4.14. `requires-python = ">=3.12"` | Django 6.1 exige Python ≥ 3.12 (verificado no PyPI), o mesmo piso do motor. Sem trava de versão: `backend/` é aplicação, e a reprodutibilidade de ambiente é do F3 |
| **Versões do frontend** | idem: React 19.2, Vite 8.2, TypeScript 7.0, Vitest 4.1, jsdom 30 | são as correntes; o `package-lock.json` é versionado e trava o resto |
| **Node** | **Node 24 (LTS), a partir da 24.15**, declarado em `engines` e em `.nvmrc`, com `engine-strict=true` em `.npmrc` | Vite 8 exige Node ≥ 20.19 ou ≥ 22.12, e jsdom 30 exige `^22.22.2 \|\| ^24.15.0`. O piso 24.15 é o do jsdom: com `engine-strict`, uma 24.x mais antiga reprovaria a instalação apontando para o jsdom, não para o projeto. A máquina de desenvolvimento tem 20.11, que já saiu de suporte. Sem `engine-strict`, o npm sob Node incompatível **pula em silêncio** o binding nativo do rolldown e o build quebra com mensagem enganosa — aconteceu na verificação deste plano |
| **Configuração de teste do Django** | módulo `config/settings_test.py`, que preenche `RUVOR_*` e reexporta `config.settings` | `conftest.py` **não serve**: o pytest-django chama `django.setup()` antes de carregar qualquer conftest, na raiz ou em `tests/` — verificado nas duas posições. O plugin do django-stubs tem o mesmo problema e aponta para o mesmo módulo |
| **Carregador de `.env`** | nenhum. As variáveis vêm do ambiente do processo | dependência a menos. O `docker compose` do F3 lê `.env` nativamente; fora dele, exporta-se no shell |
| **Ferramenta de estilo** | **fora deste bloco.** A spec do F5 é dona da escolha | a spec do F2b não a lista, e adicioná-la aqui seria escopo novo. Registrar isto tira o tema da condição de "território órfão" apontada no ESTADO |
| **Escala tipográfica** | a tela do casco **não declara `font-size`** | é casco técnico; usa o tamanho padrão do navegador. A lacuna dos tokens segue aberta para o Marco 1, onde há tela de produto |
| **Onde vive a rota de saúde** | `config/views.py`, função `health`, sem DRF | é infraestrutura, não recurso de API. DRF entra em `INSTALLED_APPS` e nada mais — verificado que sobe sem `django.contrib.auth` |
| **Ambiente de DOM dos testes** | jsdom | padrão do ecossistema; exige Node ≥ 22.22, coberto pela decisão de Node |
| **Onde ficam os testes do frontend** | `frontend/tests/`, fora de `src/` | a varredura de cores (F2b-09) tem os padrões de cor dentro dela; em `src/` ela reprovaria a si mesma |

### Pré-requisito de ambiente

**Node 24.15 ou superior instalado na máquina de desenvolvimento**, antes da T4. Não é
tarefa do plano — não gera arquivo — mas o critério da T4 começa por `node --version` e
reprova sem ele.

O `.venv/` da raiz continua sendo o único ambiente Python; `backend/` é instalado nele em
modo editável, ao lado do motor.

---

## Rastreabilidade

| Requisito | Onde é provado |
|---|---|
| F2b-01 `GET /health` → `200 {"status": "ok"}` | T2 (`curl` contra o `runserver`), T3 (`test_health_responde_ok`) |
| F2b-02 sem banco | T2 (`DATABASES = {}`), T3 (`test_processo_nao_tem_banco` + mutação b) |
| F2b-03 React sobe e renderiza | T4 (`npm run dev`, `curl` do `index.html`), T5 (`App.test.tsx`) |
| F2b-04 consome `tokens.css` | T4 (`grep --ruvor-ink dist/assets/*.css`) |
| F2b-05 TypeScript estrito | T4 (`tsconfig.json` + mutação TS7006) |
| F2b-06 mypy estrito no backend | T2 (`mypy` + mutação `no-untyped-def`), T3 (com `tests/`) |
| F2b-07 `.env.example` lista `RUVOR_*` | T2 |
| F2b-08 frontend do protótipo removido | T1, reconferido na T4 |
| F2b-09 sem cor literal em `src/` | T5 (`cores.test.ts` + mutações a, b) |
| F2b-10 fumaça: marca e estado do backend | T5 (`App.test.tsx` + mutação c) |
| README com instruções do frontend (spec, "O frontend nasce do zero") | T6 |

---

## Mapa de arquivos

### Removidos — o frontend do protótipo, inteiro

Os **29 arquivos** rastreados em `frontend/` (`git ls-files frontend`):

| Grupo | Arquivos |
|---|---|
| raiz | `.env.example`, `.gitignore`, `.oxlintrc.json`, `index.html`, `package.json`, `package-lock.json`, `vite.config.js` |
| `public/` | `favicon.svg` |
| `src/` | `App.jsx`, `main.jsx` |
| `src/api/` | `apiStatusStore.js`, `client.js`, `loadingStore.js` |
| `src/components/` | `ApiOfflineBanner.jsx`, `Badge.jsx`, `Card.jsx`, `Chip.jsx`, `ErrorBoundary.jsx`, `Layout.jsx`, `LoadingBar.jsx`, `ResultsTable.jsx`, `Skeleton.jsx`, `ThemeToggle.jsx` |
| `src/pages/` | `Dashboard.jsx`, `NotFound.jsx`, `ResultDetail.jsx`, `ResultsList.jsx` |
| `src/styles/` | `theme.css` |
| `src/utils/` | `formatDate.js` |

Nada é reaproveitado. `frontend/node_modules/`, se existir no disco, não é rastreado.

### Criados — `backend/`

| Arquivo | Responsabilidade |
|---|---|
| `backend/pyproject.toml` | dependências, pytest, mypy, django-stubs |
| `backend/manage.py` | ponto de entrada do Django |
| `backend/config/__init__.py` | vazio |
| `backend/config/settings.py` | configuração, lida de `RUVOR_*`; sem banco |
| `backend/config/settings_test.py` | preenche `RUVOR_*` e reexporta `settings` |
| `backend/config/urls.py` | uma rota: `/health` |
| `backend/config/views.py` | a função `health` |
| `backend/config/wsgi.py`, `backend/config/asgi.py` | os do `django-admin startproject`, sem alteração de conteúdo |
| `backend/tests/__init__.py` | vazio |
| `backend/tests/test_health.py` | F2b-01 e F2b-02 executáveis |

### Criados — `frontend/`

| Arquivo | Responsabilidade |
|---|---|
| `frontend/package.json`, `frontend/package-lock.json` | dependências, scripts, `engines` |
| `frontend/.npmrc`, `frontend/.nvmrc` | `engine-strict`; versão do Node |
| `frontend/.gitignore` | `node_modules/`, `dist/`, `.env*` exceto o exemplo |
| `frontend/.env.example` | `VITE_API_BASE_URL` |
| `frontend/tsconfig.json` | TypeScript estrito |
| `frontend/vite.config.ts` | apelido `@brand`, `fs.allow`, proxy de `/health`, Vitest |
| `frontend/index.html` | título, favicon, `#root` |
| `frontend/public/ruvor-mark.svg` | cópia de `brand/ruvor/ruvor-mark.svg` — a única cópia permitida pela spec |
| `frontend/src/vite-env.d.ts` | tipos do Vite |
| `frontend/src/main.tsx` | importa `@brand/tokens.css` e monta `App` |
| `frontend/src/App.tsx` | a tela de verificação |
| `frontend/src/app.css` | estilo da tela, só com tokens |
| `frontend/tests/App.test.tsx` | F2b-10 |
| `frontend/tests/cores.test.ts` | F2b-09 |

### Alterados

| Arquivo | O que muda |
|---|---|
| `.env.example` (raiz) | deixa de ser vazio; lista as três variáveis `RUVOR_*` |
| `README.md` | bloco de aviso e seção de execução |

### Explicitamente intocados

`engine/`, `brand/` (consumido, nunca modificado — spec), `docs/` (é do passo FECHA),
`CLAUDE.md` (idem), `.gitignore` da raiz (já ignora `frontend/node_modules/`; o resto fica no
`frontend/.gitignore`), `tools/`.

---

## Ordem e dependências

```
T1  remover o frontend do protótipo ─────────┐
                                             ├── T4  projeto React
T2  projeto Django e rota de saúde ──┬───────┘      └── T5  testes do frontend ──┐
                                     └── T3  testes do backend ──────────────────┴── T6  README
```

T1 e T2 tocam arquivos disjuntos e correm em paralelo. T3 e T4 também. T4 depende de T2
porque seu critério prova o proxy contra o Django real. T6 fecha, porque descreve o que as
outras criaram.

---

### Tarefa 1 — Remover o frontend do protótipo

**Depende de:** nada
**Visual:** não

**Arquivos**
- remove: os 29 arquivos de `frontend/` listados no mapa

**Contrato**

`git rm -r frontend`. Depois da tarefa, `frontend/` não existe no índice nem no disco —
`node_modules/` local, se houver, é apagado junto.

**Critério de aceite**

```bash
test -z "$(git ls-files frontend)"
! test -d frontend
```

**Cerca de escopo**

Não cria nada. Não toca no `README.md`, que ainda cita o frontend antigo — é a T6. Não toca no
`.gitignore` da raiz.

---

### Tarefa 2 — Projeto Django e rota de saúde

**Depende de:** nada
**Visual:** não

**Arquivos**
- cria: `backend/pyproject.toml`, `backend/manage.py`, `backend/config/{__init__,settings,settings_test,urls,views,wsgi,asgi}.py`, `backend/tests/__init__.py`
- altera: `.env.example` (raiz)

**Contrato** — *o conteúdo é o contrato ([PROCESSO §5](../PROCESSO.md#quando-o-conteúdo-entra-no-plano))*

`backend/pyproject.toml`:

```toml
[project]
name = "ruvor-backend"
version = "0.1.0"
description = "Aplicacao web do Ruvor"
requires-python = ">=3.12"
dependencies = ["django>=6.1", "djangorestframework>=3.18"]

[project.optional-dependencies]
dev = ["mypy>=2.3", "django-stubs>=6.1", "pytest>=9.1", "pytest-django>=4.14"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

# Nao e pacote distribuivel. Declarar o pacote evita a descoberta automatica do
# setuptools, que falha com manage.py e config/ lado a lado.
[tool.setuptools]
packages = ["config"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings_test"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.12"
files = ["config", "manage.py", "tests"]
strict = true
plugins = ["mypy_django_plugin.main"]

# O plugin importa o modulo de settings. config.settings exige RUVOR_SECRET_KEY e
# derrubaria o mypy sem a variavel; settings_test a preenche.
[tool.django-stubs]
django_settings_module = "config.settings_test"
```

`backend/config/settings.py`:

```python
"""Configuracao do Django. Tudo vem de variaveis RUVOR_*; nao ha banco neste bloco (F4)."""

from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"variavel de ambiente obrigatoria ausente: {name}")
    return value


SECRET_KEY = _required("RUVOR_SECRET_KEY")
DEBUG = os.environ.get("RUVOR_DEBUG", "false").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [h for h in os.environ.get("RUVOR_ALLOWED_HOSTS", "").split(",") if h]

INSTALLED_APPS = ["rest_framework"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Vazio de proposito: F2b-02. O Django preenche com o backend "dummy", que levanta
# ImproperlyConfigured em qualquer acesso — e o teste da T3 prova isso.
DATABASES: dict[str, dict[str, str]] = {}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
```

`backend/config/settings_test.py`:

```python
"""Configuracao da suite de testes e do plugin do mypy: preenche as variaveis RUVOR_*
obrigatorias com valores fixos e reexporta config.settings sem alteracao.

Nao e conftest.py porque o pytest-django chama django.setup() antes de carregar
qualquer conftest — o modulo de settings e o unico lugar que roda antes."""

import os

os.environ.setdefault("RUVOR_SECRET_KEY", "somente-para-teste")
os.environ.setdefault("RUVOR_ALLOWED_HOSTS", "testserver")

from config.settings import *  # noqa: E402, F403
```

`backend/config/views.py`:

```python
from django.http import HttpRequest, JsonResponse


def health(request: HttpRequest) -> JsonResponse:
    """Rota de saude: sem autenticacao, sem banco. Contrato congelado na spec."""
    return JsonResponse({"status": "ok"})
```

`backend/config/urls.py`:

```python
from django.urls import path

from config.views import health

urlpatterns = [path("health", health)]
```

**Como gerar o esqueleto:** de dentro de `backend/`, `django-admin startproject config .`
cria `manage.py` e `config/{__init__,settings,urls,wsgi,asgi}.py`. Em seguida, `settings.py`
e `urls.py` são **substituídos** pelo conteúdo acima — o gerado traz SQLite, apps de
autenticação e sessão, tudo fora deste bloco. `views.py` e `settings_test.py` são criados.

`backend/manage.py` — o gerado, com a assinatura anotada (`def main() -> None:`) para
passar no mypy estrito; nada mais muda. `wsgi.py` e `asgi.py` são os gerados, sem alteração.

`.env.example` da raiz:

```dotenv
# Variaveis que o Django exige (backend/config/settings.py). Nada as carrega deste
# arquivo: exporte no shell, ou deixe o docker compose (F3) le-lo.
RUVOR_SECRET_KEY=
RUVOR_DEBUG=true
RUVOR_ALLOWED_HOSTS=localhost,127.0.0.1
```

`backend/tests/__init__.py` nasce vazio aqui porque o mypy lista `tests` em `files` e
reprova se o caminho não existir; a T3 cria `test_health.py` ao lado dele.

**Sobre "o Django exige" as três variáveis** (spec, F2b-07): só `RUVOR_SECRET_KEY` derruba o
processo se faltar. `RUVOR_DEBUG` e `RUVOR_ALLOWED_HOSTS` têm padrão seguro — `false` e
vazio — porque exigi-las só acrescentaria uma forma de não subir sem ganhar segurança. É a
leitura que este plano adota; as três continuam listadas no `.env.example`.

**Ordem de instalação.** O `.venv/` da raiz não tem Django, e o `pip install -e` do backend
falha enquanto `config/` não existir (`package directory 'config' does not exist`). Então:

1. `pip install "django>=6.1"` — só para ter o `django-admin`
2. de dentro de `backend/`: `django-admin startproject config .`
3. escrever `pyproject.toml` e substituir/criar os arquivos conforme o contrato
4. `pip install -e "./backend[dev]"`, da raiz

Criar `config/` à mão antes do passo 2 não serve: o `startproject` recusa nome que já seja
módulo importável.

**Critério de aceite**

No `.venv/` da raiz, depois da ordem de instalação acima. Os comandos de `manage.py` rodam
de dentro de `backend/`, e o mypy também — ele lê a configuração do diretório corrente.

```bash
pip install -e "./backend[dev]"
pip show ruvor-backend >/dev/null     # instalado em modo editavel
cd backend

# sobe com as variaveis, e nao sobe sem elas — F2b-07 tem dono
RUVOR_SECRET_KEY=x RUVOR_ALLOWED_HOSTS=localhost python manage.py check
! env -u RUVOR_SECRET_KEY python manage.py check 2>/dev/null
env -u RUVOR_SECRET_KEY python manage.py check 2>&1 | grep -q "RUVOR_SECRET_KEY"

# responde a rota de saude sem banco — F2b-01, F2b-02
RUVOR_SECRET_KEY=x RUVOR_ALLOWED_HOSTS=localhost,127.0.0.1 \
  python manage.py runserver 8000 --noreload &
PID=$!
curl -s --retry 20 --retry-delay 1 --retry-all-errors http://127.0.0.1:8000/health
#   -> {"status": "ok"}
test "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/health)" = "200"
kill $PID

# tipos — F2b-06
mypy                          # Success: no issues found
```

Antes de subir o servidor, confirme que a porta está livre — `netstat -ano | grep ":8000 "`
vazio. **Nunca encerre processo por porta**: encerre o PID que você iniciou. No Git Bash,
`kill $!` encerra o processo nativo (verificado); **não** use `taskkill` com `$!` — esse
número é o PID do MSYS, não o do Windows, e pode acertar processo alheio.

E o mypy prova que está em modo estrito: acrescentar a `views.py` uma função sem anotação
(`def sem_tipo(x): return x`) produz `error: Function is missing a type annotation
[no-untyped-def]`; remover a função silencia. Verificado com mypy 2.3.1 e django-stubs 6.1.0.

```bash
! grep -q "F2b" ../.env.example        # o placeholder do F2a foi substituido
grep -q "^RUVOR_SECRET_KEY=" ../.env.example
grep -q "^RUVOR_DEBUG=" ../.env.example
grep -q "^RUVOR_ALLOWED_HOSTS=" ../.env.example
```

**Cerca de escopo**

Não cria app de domínio, modelo, migration nem endpoint além de `/health`. Não configura
banco, Celery ou CORS. Não importa `engine` — se parecer necessário, o escopo saiu do lugar.
Não cria `tests/test_health.py` — é a T3. Não toca no `README.md`.

---

### Tarefa 3 — Suíte de testes do backend

**Depende de:** T2
**Visual:** não

**Arquivos**
- cria: `backend/tests/test_health.py`

**Contrato** — *a lógica é sutil e a falha é silenciosa*

Dois testes. O primeiro é a rota. O segundo é a prova de F2b-02 — e o jeito óbvio de
escrevê-lo, `assert settings.DATABASES == {}`, **reprova com tudo certo**: o Django preenche
o dicionário vazio com um backend `dummy` na primeira leitura. A prova correta é ativa: acessar
o banco precisa levantar `ImproperlyConfigured`.

```python
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import Client


def test_health_responde_ok(client: Client) -> None:
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_processo_nao_tem_banco() -> None:
    """F2b-02: nao ha banco configurado, e qualquer acesso falha alto."""
    with pytest.raises(ImproperlyConfigured):
        connection.cursor()
```

**Critério de aceite**

Da raiz do repositório, **sem nenhuma variável `RUVOR_*` exportada** — é o que prova que
`settings_test.py` faz o trabalho:

```bash
env -u RUVOR_SECRET_KEY -u RUVOR_ALLOWED_HOSTS pytest backend -q     # 2 passed
```

E os dois testes detectam o que prometem. Duas mutações, cada uma revertida em seguida:

```bash
# (a) a rota muda -> o primeiro teste REPROVA
sed -i 's/"status": "ok"/"status": "nok"/' backend/config/views.py
if pytest backend -q -k health >/dev/null 2>&1; then echo "FALHOU EM DETECTAR (a)"; exit 1; fi
git checkout backend/config/views.py

# (b) um banco aparece -> o segundo teste REPROVA (o pytest-django bloqueia o acesso com
#     RuntimeError, que nao e ImproperlyConfigured; o efeito e o mesmo: detectou)
python - <<'PY'
import pathlib
p = pathlib.Path("backend/config/settings.py")
p.write_text(p.read_text(encoding="utf-8").replace(
    'DATABASES: dict[str, dict[str, str]] = {}',
    'DATABASES: dict[str, dict[str, str]] = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}',
), encoding="utf-8")
PY
if pytest backend -q -k banco >/dev/null 2>&1; then echo "FALHOU EM DETECTAR (b)"; exit 1; fi
git checkout backend/config/settings.py

cd backend && mypy       # continua limpo com tests/ incluido
```

**Cerca de escopo**

Não altera `settings.py` nem `views.py` de forma permanente. Não adiciona fixture, conftest
nem teste além dos dois.

---

### Tarefa 4 — Projeto React

**Depende de:** T1, T2
**Visual:** não — casco técnico, fora do portão por definição ([D-30](../decisoes/D-30-portao-de-mockup-so-para-tela-de-produto.md))

**Arquivos**
- cria: `frontend/package.json`, `frontend/package-lock.json`, `frontend/.npmrc`, `frontend/.nvmrc`, `frontend/.gitignore`, `frontend/.env.example`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/index.html`, `frontend/public/ruvor-mark.svg`, `frontend/src/{vite-env.d.ts,main.tsx,App.tsx,app.css}`

**Contrato** — *o conteúdo é o contrato*

Os arquivos são escritos à mão, **não** gerados por `npm create vite`: o modelo `react-ts`
traz `index.css` e `App.css` cheios de cor literal, mais `vite.svg`, e limpar custa mais que
escrever.

`frontend/package.json`:

```json
{
  "name": "ruvor-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "engines": { "node": ">=24.15" },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "typecheck": "tsc --noEmit",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  },
  "devDependencies": {
    "@testing-library/dom": "^10.4.0",
    "@testing-library/react": "^16.3.3",
    "@types/node": "^24.0.0",
    "@types/react": "^19.2.18",
    "@types/react-dom": "^19.2.5",
    "@vitejs/plugin-react": "^6.1.1",
    "jsdom": "^30.0.1",
    "typescript": "^7.0.2",
    "vite": "^8.2.2",
    "vitest": "^4.1.11"
  }
}
```

`@testing-library/dom` é *peer dependency* de `@testing-library/react` e precisa ser
declarada. Nada de roteamento, gráfico ou fonte — a spec manda dependências mínimas.

`frontend/.npmrc`: `engine-strict=true`. `frontend/.nvmrc`: `24`.

`frontend/.gitignore`:

```gitignore
node_modules/
dist/
.env
.env.*
!.env.example
```

`frontend/.env.example`:

```dotenv
# Vazio: mesma origem (o proxy do Vite encaminha /health para o Django em :8000).
# Preenchido: URL absoluta de outro host, sem barra final.
VITE_API_BASE_URL=
```

`frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "types": ["vite/client", "node"],
    "paths": { "@brand/*": ["../brand/ruvor/*"] }
  },
  "include": ["src", "tests", "vite.config.ts"]
}
```

`frontend/vite.config.ts` — o `defineConfig` vem de `vitest/config`, que estende o do Vite
com a chave `test`; assim há um arquivo de configuração só:

```ts
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const repoRoot = fileURLToPath(new URL("..", import.meta.url));
const brandDir = fileURLToPath(new URL("../brand/ruvor", import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@brand": brandDir } },
  server: {
    fs: { allow: [repoRoot] },
    proxy: { "/health": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "jsdom",
    include: ["tests/**/*.test.{ts,tsx}"],
  },
});
```

`frontend/index.html`:

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" type="image/svg+xml" href="/ruvor-mark.svg" />
    <title>Ruvor</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`frontend/public/ruvor-mark.svg`: cópia byte a byte de `brand/ruvor/ruvor-mark.svg`.

**Contrato da tela**, que os testes da T5 verificam:

| Elemento | Contrato |
|---|---|
| `main.tsx` | importa `@brand/tokens.css` **antes** de `./app.css`; monta `<App />` em `#root` sob `StrictMode` |
| `App.tsx` | exporta `App`. Renderiza `<img alt="Símbolo Ruvor" src="/ruvor-mark.svg">`, `<h1>Ruvor</h1>` e `<p role="status">Backend: …</p>` |
| estado do backend | ao montar, `fetch(\`${VITE_API_BASE_URL ?? ""}/health\`)`. Texto: `verificando…` enquanto pendente; `ok` se `response.ok` **e** o JSON do corpo tem a propriedade `status === "ok"` (igualdade de propriedade, não do objeto inteiro); `indisponível` em qualquer outro caso, inclusive exceção de rede ou corpo que não é JSON |
| `app.css` | só `var(--ruvor-*)` para cor e fonte; `body` com `--ruvor-bg`, `--ruvor-text`, `--ruvor-font-sans`; o estado em `--ruvor-font-mono`, com `--ruvor-validated` para ok, `--ruvor-critical` para indisponível, `--ruvor-text-muted` para pendente. **Nenhum `font-size`** |

Cor nunca é o único sinal ([brand](../../brand/ruvor/README.md#regras-de-interface)): o
texto do estado muda junto com a cor.

**Critério de aceite**

Com Node 24 instalado e o Django da T2 disponível. Comandos de `npm` rodam de dentro de
`frontend/`:

```bash
node --version | grep -q "^v24\."
cd frontend
npm install                                   # gera package-lock.json
test -f package-lock.json
test -d node_modules/@rolldown/binding-win32-x64-msvc   # Linux: binding-linux-x64-gnu
npm run typecheck                             # tsc 7: sem saida, exit 0
npm run build
grep -l -- "--ruvor-ink" dist/assets/*.css    # os tokens chegaram ao pacote via @brand
```

O último comando é o que prova F2b-04 de verdade: o apelido resolveu, o `fs.allow` liberou a
leitura fora da raiz do frontend, e o CSS final contém os tokens.

Proxy, contra o Django real (porta 8000 livre antes de começar):

```bash
# terminal 1, em backend/:  RUVOR_SECRET_KEY=x RUVOR_ALLOWED_HOSTS=localhost,127.0.0.1 python manage.py runserver 8000
# terminal 2, em frontend/: npm run dev
curl -s http://localhost:5173/health          # -> {"status": "ok"}, passou pelo proxy
test "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5173/ruvor-mark.svg)" = "200"
curl -s http://localhost:5173/ | grep -q "<title>Ruvor</title>"
```

> **`localhost`, não `127.0.0.1`.** O Vite 8 escuta em `localhost`, que no Windows resolve
> para IPv6 (`::1`) — `curl http://127.0.0.1:5173` é recusado com tudo funcionando. Verificado.

F2b-08 — nada do protótipo sobreviveu:

```bash
cd ..
! git ls-files frontend | grep -E '\.(jsx|js)$'
! test -f frontend/.oxlintrc.json
! test -f frontend/public/favicon.svg
! grep -rniE "varlab|VaR Lab" frontend --exclude-dir=node_modules --exclude-dir=dist
```

E o `strict` está ligado de fato: acrescentar a `App.tsx` uma função com parâmetro sem tipo
(`export function semTipo(x) { return x; }`) produz `error TS7006: Parameter 'x' implicitly
has an 'any' type`; remover silencia.

**Cerca de escopo**

Não cria teste — é a T5. Não instala fonte, roteador nem biblioteca de gráfico. Não copia nada
de `brand/` além do símbolo, e não altera nada em `brand/`. Não declara `font-size`. Não toca
no `README.md` nem no `.gitignore` da raiz. Não versiona `dist/`.

---

### Tarefa 5 — Testes do frontend: fumaça e varredura de cores

**Depende de:** T4
**Visual:** não

**Arquivos**
- cria: `frontend/tests/App.test.tsx`, `frontend/tests/cores.test.ts`

**Contrato** — *a lógica é sutil e a falha é silenciosa*

`frontend/tests/App.test.tsx` — F2b-10. `fetch` é substituído por dublê; nenhum teste depende
do Django estar de pé:

```tsx
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

function stubFetch(body: unknown, ok = true): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok, json: async () => body })),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("tela de verificação", () => {
  it("renderiza a marca e o estado ok do backend", async () => {
    stubFetch({ status: "ok" });
    render(<App />);
    expect(screen.getByRole("heading", { name: "Ruvor" })).toBeDefined();
    expect(screen.getByAltText("Símbolo Ruvor")).toBeDefined();
    expect(await screen.findByText("Backend: ok")).toBeDefined();
  });

  it("mostra indisponível quando o backend não responde", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("rede");
      }),
    );
    render(<App />);
    expect(await screen.findByText("Backend: indisponível")).toBeDefined();
  });
});
```

`frontend/tests/cores.test.ts` — F2b-09. Três armadilhas, todas resolvidas no código:

1. **Ambiente `node`, declarado no cabeçalho.** Sob jsdom, `URL` é a do jsdom e
   `fileURLToPath` a rejeita — o teste morre na primeira linha, antes de varrer nada.
2. **Nome de cor só em posição de valor.** `red` casaria `required`; `white`, com limite de
   palavra, casaria `white-space`. O padrão exige `:` antes e não-identificador depois.
3. **A varredura precisa encontrar arquivo.** Um `src/` vazio ou um caminho errado passaria
   com lista vazia; o primeiro teste garante que há o que varrer. O terceiro teste é a prova
   de que os padrões pegam o que devem e ignoram o que não devem — fica no próprio arquivo
   para que uma edição nos padrões reprove na hora.

```ts
/**
 * @vitest-environment node
 *
 * F2b-09: nenhum valor de cor literal em frontend/src/. Cor só entra por token.
 *
 * Vive fora de src/ de propósito: os próprios padrões abaixo reprovariam se o
 * arquivo estivesse dentro do alvo da varredura.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const SRC = fileURLToPath(new URL("../src", import.meta.url));

// Hexadecimal de 3, 4, 6 ou 8 dígitos, terminado por não-alfanumérico.
const HEX = /#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{4}|[0-9a-f]{3})(?![0-9a-z_-])/i;
// Funções de cor.
const FUNCTION = /\b(?:rgba?|hsla?|oklch|lab)\(/i;
// Nomes, só em posição de valor: precedidos por ":" (declaração CSS ou objeto
// de estilo), aspas opcionais, e seguidos por fim de valor — não por "-" nem
// letra, para que "white-space" e "required" não casem.
const NAMES =
  "white|black|red|green|blue|gray|grey|silver|orange|yellow|purple|navy|teal";
const NAMED = new RegExp(`:\\s*['"]?\\s*(?:${NAMES})(?![a-z0-9_-])`, "i");

const PATTERNS: ReadonlyArray<readonly [string, RegExp]> = [
  ["hexadecimal", HEX],
  ["função de cor", FUNCTION],
  ["nome de cor", NAMED],
];

function listFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    return statSync(full).isDirectory() ? listFiles(full) : [full];
  });
}

export function findLiteralColors(root: string): string[] {
  const findings: string[] = [];
  for (const file of listFiles(root)) {
    const lines = readFileSync(file, "utf8").split(/\r?\n/);
    lines.forEach((line, index) => {
      for (const [label, pattern] of PATTERNS) {
        const match = pattern.exec(line);
        if (match) {
          findings.push(
            `${relative(root, file)}:${index + 1} ${label}: ${match[0]}`,
          );
        }
      }
    });
  }
  return findings;
}

describe("F2b-09 — sem cor literal em src/", () => {
  it("a varredura encontra pelo menos um arquivo", () => {
    expect(listFiles(SRC).length).toBeGreaterThan(0);
  });

  it("nenhum arquivo de src/ contém cor literal", () => {
    expect(findLiteralColors(SRC)).toEqual([]);
  });

  it("os padrões detectam o que prometem e ignoram falso positivo", () => {
    const detect = (s: string): boolean => PATTERNS.some(([, p]) => p.test(s));
    const bad = [
      "color: #fff",
      "color:#ffff",
      "background: #F7F6F2",
      "border: 1px solid #292A2E80",
      "rgb(1,2,3)",
      "rgba(0,0,0,.5)",
      "hsl(0 0% 0%)",
      "hsla(0,0%,0%,1)",
      "oklch(0.5 0 0)",
      "lab(50% 0 0)",
      "color: white",
      "color: 'red'",
      'background: "navy"',
      "{ color: gray }",
    ];
    const good = [
      "white-space: nowrap",
      "const required = true",
      "#root { margin: 0 }",
      "color: var(--ruvor-ink)",
      "url(#clip)",
      'className="status--ok"',
      "// rendered in gray-ish tone",
      "grid-template-areas: 'header'",
      'id="whitelist"',
    ];
    for (const s of bad) expect(detect(s), s).toBe(true);
    for (const s of good) expect(detect(s), s).toBe(false);
  });
});
```

A varredura cobre **todo arquivo** sob `src/`, de qualquer extensão — é por isso que o
símbolo da marca vive em `public/`: seu `fill="#292A2E"` reprovaria aqui.

Limite conhecido e aceito: um seletor de id que por acaso seja hexadecimal válido (`#add`,
`#bad`) casaria. Não há nenhum no casco, e o Marco 1 decide se troca o id ou refina o padrão.

**Critério de aceite**

```bash
cd frontend
npm test            # Test Files 2 passed, Tests 5 passed
npm run typecheck   # os testes estao em "include" e passam no strict
```

E os testes detectam. Três mutações, cada uma revertida em seguida:

```bash
# (a) cor hexadecimal em CSS -> cores.test REPROVA, apontando arquivo e linha
printf '\n.x { color: #fff; }\n' >> src/app.css
if npm test >/dev/null 2>&1; then echo "FALHOU EM DETECTAR (a)"; exit 1; fi
npm test 2>&1 | grep -q "app.css:[0-9]* hexadecimal: #fff"
git checkout src/app.css

# (b) nome de cor em objeto de estilo TSX -> cores.test REPROVA
sed -i 's|<h1>Ruvor</h1>|<h1 style={{ color: "navy" }}>Ruvor</h1>|' src/App.tsx
if npm test >/dev/null 2>&1; then echo "FALHOU EM DETECTAR (b)"; exit 1; fi
git checkout src/App.tsx

# (c) o rotulo do estado muda -> App.test REPROVA
sed -i 's/Backend: /Servidor: /' src/App.tsx
if npm test >/dev/null 2>&1; then echo "FALHOU EM DETECTAR (c)"; exit 1; fi
git checkout src/App.tsx

npm test            # limpo de novo
```

As mutações (a) e (b) foram executadas na verificação deste plano e reprovaram como previsto;
a saída de (a) foi `expected [ 'app.css:32 hexadecimal: #fff' ] to deeply equal []`.

**Cerca de escopo**

Não altera `src/` de forma permanente. Não amplia a lista de nomes de cor da spec. Não
adiciona `@testing-library/jest-dom` nem outro matcher — `toBeDefined` basta.

---

### Tarefa 6 — README

**Depende de:** T3, T5
**Visual:** não

**Arquivos**
- altera: `README.md`

**Contrato**

Reescrita de duas partes, não varredura:

**1. O bloco de aviso** (linhas 9–19). A linha 15 diz que o `frontend/` "ainda é o do
protótipo e será substituído no F2b" — falso depois deste bloco. O bloco passa a dizer o que
é verdade: existe o casco da aplicação (Django respondendo `/health`, React renderizando a
tela de verificação), e ainda **não** há banco, API de negócio nem tela de produto.

**2. A seção "Executar o motor"** (a partir da linha 80). A citação "Não há API: a camada web
chega no F2b" sai. A seção vira "Executar", com três subseções: motor (o que já está lá),
backend e frontend. Os parágrafos 110–111, sobre o frontend do protótipo, saem.

O que a parte de backend e frontend precisa conter, no mínimo:

| Item | Conteúdo |
|---|---|
| Pré-requisitos | Python 3.12 e **Node 24.15 ou superior**; o `.npmrc` recusa Node mais antigo |
| Instalar backend | `pip install -e "./backend[dev]"`, no mesmo `.venv/` do motor |
| Variáveis | copiar `.env.example` para `.env` e exportar no shell — nada as carrega do arquivo até o F3 |
| Subir backend | `cd backend && python manage.py runserver 8000` |
| Subir frontend | `cd frontend && npm install && npm run dev`, abrir `http://localhost:5173` |
| Dia a dia | acrescentar à tabela: `pytest backend`, `cd backend && mypy`, `npm test`, `npm run typecheck`, `npm run build` |

**Critério de aceite**

```bash
! grep -q "ainda é o do protótipo" README.md
! grep -q "chega no F2b" README.md
grep -q 'pip install -e "./backend\[dev\]"' README.md
grep -q "manage.py runserver" README.md
grep -q "npm run dev" README.md
grep -q "npm test" README.md
grep -q "npm run typecheck" README.md
grep -q "pytest backend" README.md
grep -qE "Node(\.js)? 24" README.md
grep -q "localhost:5173" README.md
```

**Cerca de escopo**

Não altera `docs/`, `CLAUDE.md` nem `ESTADO.md` — são do passo FECHA. Não altera o restante
do README (diferencial, documentação, pilha, origem acadêmica).

---

## O que fica para o passo FECHA

Fora do plano, conforme [PROCESSO §3](../PROCESSO.md#o-passo-fecha): `ESTADO.md`,
`ROADMAP.md`, `aprendizados.md`, cabeçalho desta spec e deste plano, as tabelas de
`specs/README.md` e `planos/README.md`, e `CLAUDE.md` — cuja seção "Estado do repositório"
deixa de ser verdadeira quando o casco existir.

Candidatos a `aprendizados.md`, já descobertos na verificação deste plano:

- `conftest.py` não consegue definir variável de ambiente antes do pytest-django chamar
  `django.setup()`; o lugar é um módulo de settings de teste
- `DATABASES = {}` não fica vazio: o Django o preenche com o backend `dummy`; provar
  "não tem banco" é provar que o acesso levanta `ImproperlyConfigured`
- npm sob Node incompatível pula dependência opcional nativa em silêncio; `engine-strict`
  transforma isso em erro na instalação
- Vite 8 escuta em `localhost`, que resolve para IPv6 no Windows; `127.0.0.1` recusa
- ao subir servidor em teste, encerre pelo PID que você iniciou, nunca por porta — uma porta
  "livre" pode estar ocupada por outro programa da máquina; e no Git Bash `$!` é PID do
  MSYS, que serve para `kill` mas não para `taskkill`

E uma frase para o `ESTADO.md`: depois deste bloco o `.venv/` compartilhado passa a ter
Django, então "`import engine` sem Django instalado ✅" descreve o que foi provado no F2a, não
o ambiente corrente — a garantia viva passa a ser só `engine/tests/test_modulos_proibidos.py`.
