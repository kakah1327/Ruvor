# F5 — Plano de implementação

**Spec:** [F5 — Integração contínua](../specs/F5-integracao-continua.md)
**Status:** ✅ **executado e fechado** (2026-09-08) · oito tarefas, onze commits, de `bbcc24a` a `650a716`. Revisão final aprovada.
Três reprovações antes da aprovação. Os dois últimos bloqueios fecharam **por execução, não
por leitura**: a mutação da prova de formatação foi aplicada e reprova nomeando o arquivo, e
o `pip install` da T1 foi resolvido com `--dry-run`.
**Objetivo:** cada push na `main` dispara verificação em máquina limpa; existe estilo no
repositório inteiro, motor incluído; e a imagem `worker` não é construída.

**Commit por tarefa**, direto na `main` ([D-31](../decisoes/D-31-trabalho-direto-na-main.md)).
Sem ramo.

---

## Como ler este plano

Segue o [PROCESSO §5](../PROCESSO.md#5-anatomia-de-um-plano): **contratos, não corpos**. Este
bloco é quase todo arquivo de configuração, e aí *o conteúdo é o contrato* — os blocos de
`ruff`, o `biome.json` e o `ci.yml` entram **literais e completos**. Entra literal também a
prova por árvore sintática, que é o segundo caso do PROCESSO: lógica sutil de falha silenciosa.

Não entram corpos de correção de lint: as violações estão enumeradas na spec, uma a uma, e a
ferramenta as aplica.

---

## O que já foi medido

Executado com `ruff 0.16.6` em contêiner Linux descartável, **sob a configuração real dos
projetos** — nunca com `--isolated` — e **depois de formatar**, salvo onde dito:

| Medido | Resultado |
|---|---|
| `ruff format --check .` no motor | **33** de 44 seriam reescritos (`src` 25 de 33, `tests` 8 de 11) |
| `ruff format --check .` no backend | **4** de 25 |
| `ruff check .` no motor, **antes** de formatar | 27 |
| `ruff check .` no motor, depois | **26** — `src` 23, `tests` 3 |
| `ruff check .` no backend | **2**, antes e depois |
| Piso **com** `E501` | 68 no motor, 7 no backend — a diferença são 42 linhas longas |
| `line-length` 100 em vez de 88 | 24 arquivos de `src` em vez de 25 |
| `UP042` | dispara em `models/base.py` sob o `requires-python` real; silenciada pela configuração |
| `ast.dump()` antes/depois da formatação | **69 arquivos** — 33 de `engine/src`, 11 de `engine/tests`, 25 de `backend` —, zero divergência |
| `engine/requirements-lock.txt` | **59** pacotes; sem `mypy`, `build` nem `ruff`; sem pacote de Windows |
| Lock como arquivo de restrição | `pytest` fica em `9.1.1`; `mypy` e `build` resolvem livres |

**A lição que estes números carregam**, e que reprovou a spec três vezes: **medir com
`--isolated` não é medir o projeto**, e medir lint antes de formatar infla o número. Toda
contagem deste plano é sob configuração real e pós-formatação.

**O que não foi medido:** nada da CI em si. Nenhum trabalho do GitHub Actions jamais rodou
neste repositório — é o que a T8 existe para descobrir.

---

## O que este plano decide

| Decisão | Valor |
|---|---|
| Escopo do estilo | `.` nos dois projetos Python. `engine/tests/` **tem dono**, e é a T2 e a T3 |
| Arquivo de fluxo | `.github/workflows/ci.yml` |
| Nome dos trabalhos | `estilo`, `backend`, `frontend`, `motor` |
| Script do frontend | `lint` |
| Runner | `ubuntu-latest` |
| Onde a prova de formatação vive | `tools/prova_formatacao.py`, **versionada** — a T6 precisa dela, e commit por tarefa não permite restaurar o que nunca entrou |
| `tools/` | **fora do escopo do estilo** — não é projeto Python, e a ARQUITETURA proíbe `pyproject.toml` na raiz. Vira dívida registrada |
| Versão das ações de terceiros | **o plano não inventa** — a T5 confirma no repositório de cada ação, como o F3 fez com etiqueta de imagem |

---

## Rastreabilidade

| Requisito | Cumpre | Prova |
|---|---|---|
| F5-01 | T5 | **T8** |
| F5-02 | T5 | **T5** (a sequência rodada à mão) e T8 |
| F5-03 | T5 | **T4** (os quatro comandos no contêiner) e T8 |
| F5-04 | T5 | **T5** (a sequência de dois passos, num ambiente limpo) e T8 |
| F5-05 | T5 | T5, T6 |
| F5-06 | T1, T2, T3 | T3, e o comando do contrato na T3 |
| F5-07 | T4 | T4 |
| F5-08 | T2 | T2 |
| F5-09 | T6 | T6 |
| F5-10 | T7 + FECHA | T7 + FECHA |

**F5-02, F5-03 e F5-04 ganharam prova local**, como a spec exige ao classificá-los como
"comando local". A primeira versão deste plano os provava só empurrando, o que deixava a
descoberta de qualquer erro para depois de sete commits.

---

## Mapa de arquivos

### Criados

| Arquivo | Tarefa |
|---|---|
| `tools/prova_formatacao.py` | T2 |
| `frontend/biome.json` | T4 |
| `.github/workflows/ci.yml` | T5 |

### Alterados

| Arquivo | Tarefa | O que muda |
|---|---|---|
| `backend/pyproject.toml` | T1 | bloco `[tool.ruff]`, e `ruff` no grupo `dev` |
| `engine/pyproject.toml` | T1 | bloco `[tool.ruff]`, e `ruff` + `mypy` no grupo `dev` |
| `engine/src/` — 25 arquivos · `engine/tests/` — 8 · `backend/` — 4 | T2 | formatação |
| `engine/src/` — 12 arquivos · `engine/tests/` — 2 · `backend/` — 2 | T3 | as 28 violações |
| `frontend/package.json`, `frontend/package-lock.json` | T4 | o Biome entra em `devDependencies`, e o `npm install` reescreve o lock |
| `frontend/tests/cores.test.ts` | T4 | o **unico** arquivo de teste com mudanca real. O Biome tambem reescreve `App.test.tsx`, mas so o fim de linha: o arquivo estava em CRLF, o Biome grava LF, e o `.gitattributes` normaliza -- `git diff` vazio. Nada em `src/` |
| `README.md`, `CLAUDE.md`, `docs/ESTADO.md`, `docs/ARQUITETURA.md`, `docs/specs/README.md`, `docs/planos/README.md` | T7 | a lista fechada |
| `docs/ROADMAP.md`, `docs/aprendizados.md`, cabeçalhos de status | **FECHA** | o que é status |

### Intocados, e é contrato que fiquem

`compose.yaml` — a CI usa o que existe, sem serviço nem porta nova.
`infra/backend.Dockerfile`, `infra/frontend.Dockerfile` — as imagens mudam pelo que instalam
(`pyproject.toml`, `package.json`), não por `COPY` novo.
`engine/requirements-lock.txt` — **não é regenerado**; reescreveria os 59 pinos, e a linha de
base compara a 1e-6 contra números daquele ambiente.
`engine/tests/baseline/valores.json` — se divergir, é achado, não arquivo a atualizar.

---

## Ordem e dependências

```
T1  ruff configurado, e as imagens reconstruidas
     ↓
T2  formatacao, com a prova por arvore sintatica
     ↓
T3  as 28 violacoes de lint
     ↓                        ↘
T4  Biome no frontend          T5  o fluxo, e as sequencias rodadas a mao
     ↘                        ↙
        T6  as mutacoes
             ↓
        T7  documentacao
             ↓
        T8  o primeiro push
```

**T4 e T5 são disjuntos** — `frontend/*` contra `.github/*` — e podem correr em paralelo. O
resto é cadeia estrita: a formatação precisa da configuração, e o lint precisa da formatação,
senão conta violações que a formatação resolveria (medido: 27 antes, 26 depois).

---

### Tarefa 1 — `ruff` configurado, e as imagens reconstruídas

**Depende de:** nada · **Visual:** não

**Arquivos**
- altera: `backend/pyproject.toml`, `engine/pyproject.toml`

**Contrato**

Em **`backend/pyproject.toml`**:

```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
# E501 fora de proposito: o formatador impoe o comprimento de linha, e a regra so
# sobraria para o que ele nao sabe quebrar -- comentario, docstring, texto.
select = ["E", "W", "F", "I", "UP", "RUF"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
# `dependencies` e `operations` sao formato canonico do Django em migration; anotar
# com ClassVar e editar artefato gerado, e o makemigrations --check do F4 reprovaria.
# A lista e fechada de proposito: "ALL" desligaria o lint num diretorio inteiro.
"**/migrations/*.py" = ["RUF012"]
```

Em **`engine/pyproject.toml`**:

```toml
[tool.ruff]
line-length = 88
# Com E501 desligado sobram 42 linhas acima de 88 colunas -- comentario, docstring e
# texto, que o formatador nao quebra. Nao e defeito.

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "RUF"]
# UP042 trocaria `class ModelCategory(str, Enum)` por StrEnum, e a troca NAO e
# equivalente: str() e f-string diferem entre as duas no 3.12, e ModelCategory e
# comparado e formatado em todo o motor. Reavaliar depois da Etapa 6 -- D-44.
ignore = ["E501", "UP042"]
```

Os grupos `dev` recebem as ferramentas, e **a forma da declaração é contrato, não estilo** —
o job `estilo` extrai o especificador daqui e o passa ao `pip`. Com `>=`, ele instalaria a
mais nova e passaria a divergir do contêiner em silêncio, que é o buraco que a
[D-43](../decisoes/D-43-ruff-e-biome-e-onde-cada-verificacao-roda.md) fechou. **É `==`:**

```toml
# backend/pyproject.toml
dev = ["mypy>=2.3", "django-stubs>=6.1", "pytest>=9.1", "pytest-django>=4.14", "ruff==0.16.6"]

# engine/pyproject.toml
dev = ["pytest>=8.0", "mypy==2.3.1", "build>=1.2", "setuptools>=68", "ruff==0.16.6"]
```

**A versão exata das duas ferramentas a T1 confirma no registro antes de escrever**, como o F3
fez com etiqueta de imagem; `0.16.6` era a corrente na escrita da spec, e o `mypy` do motor
precisa de um número porque ele **não está no lock**.

**Restricao estrutural, e ela e o que impede escolher errado:** a
[D-33](../decisoes/D-33-dia-a-dia-dentro-do-conteiner.md) poe motor e backend no **mesmo
`.venv/`**, e o `backend[dev]` exige `mypy>=2.3`. Qualquer pino `==` de `mypy` no motor tem
de satisfazer esse `>=`, senao o `pip install` da T1 e irresolvivel -- `ResolutionImpossible`,
e a T1 nao passa do primeiro comando. O `.venv` tem **2.3.1** hoje, e e por isso que o pino e
esse.

**A tarefa instala o que declarou, e reconstrói a imagem `web`.** Sem isso nada do resto roda:
o `ruff` não existe no `.venv/` hoje, e o `infra/backend.Dockerfile` instala `./backend[dev]`
**em tempo de construção** — o volume traz o fonte, não os pacotes.

**Critério de aceite**

Os números são os da spec, e são o critério. **Se algum divergir, a tarefa para:** significa
que a configuração não é a que foi medida, e todas as tarefas seguintes contam com ela.

```bash
# instalar o que a T1 declarou, no .venv nativo
# O -c e obrigatorio: engine[all] traz especificadores frouxos (numpy>=1.26,
# scipy>=1.11, arch>=6.3), e uma resolucao livre subiria os pinos do .venv --
# fazendo a linha de base divergir na T2 por deriva introduzida aqui.
pip install -c engine/requirements-lock.txt -e "./engine[all]" -e "./backend[dev]"

# ANTES de formatar, escopo `.`, configuracao real
# grep, e nao tail -1: com fixes disponiveis o ruff imprime duas linhas finais,
# e a ultima e a dos fixes, nao a contagem.
cd engine     && ruff check . 2>&1 | grep "^Found"   # Found 27 errors.
cd ../backend && ruff check . 2>&1 | grep "^Found"   # Found 2 errors.
cd ../engine   && ruff format --check . 2>&1 | tail -1  # 33 files would be reformatted
cd ../backend && ruff format --check . 2>&1 | tail -1   # 4 files would be reformatted

# UP042 esta silenciada pela configuracao. Nao use --select UP042: a linha de comando
# sobrepoe o `ignore` e acusa de qualquer jeito. O que prova e a ausencia na saida.
cd ../engine && ruff check . --output-format=concise 2>&1 | grep -c UP042   # 0

# a imagem web passa a ter ruff, e o comando do contrato roda
cd .. && docker compose up -d --build --wait web
docker compose exec -T web sh -c "ruff --version"
```

**Cerca de escopo**

Não formata, não corrige violação, não toca no frontend nem no `ci.yml`.

---

### Tarefa 2 — Formatação, e a prova por árvore sintática

**Depende de:** T1 · **Visual:** não

**Arquivos**
- cria: `tools/prova_formatacao.py`
- altera: 25 de `engine/src/`, 8 de `engine/tests/`, 4 de `backend/`

**Contrato**

A prova entra literal — sem ela, "a formatação não mudou nada" é afirmação, e a falha é
silenciosa. **Ela fica versionada**, em `tools/`, ao lado dos utilitários que já moram lá: a
T6 precisa dela, e com commit por tarefa não há como restaurar o que nunca entrou no histórico.

```python
"""Prova que `ruff format` nao alterou a arvore sintatica de nenhum arquivo.

Formatacao mexe em espaco e quebra de linha; se mexer em qualquer outra coisa, a
arvore muda e este script reprova. E o que autoriza formatar o motor congelado
(D-44) -- e cobre os nove modelos, nao os seis da linha de base numerica.

Cobre a arvore, que e menos que "nada mudou": o ast nao carrega comentario, e a
formatacao move comentario de fim de linha. Quem fecha esse buraco e o `ruff check`
seguinte, que acusaria o que uma supressao deslocada deixasse de esconder.
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import subprocess
import sys

RAIZES = ("engine/src", "engine/tests", "backend")


def arvore(caminho: pathlib.Path) -> str:
    return ast.dump(ast.parse(caminho.read_text(encoding="utf-8")))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--esperados", type=int, default=None)
    args = ap.parse_args()

    # rglob em caminho inexistente devolve vazio sem levantar: rodado do diretorio
    # errado, o script conferiria zero arquivo e sairia 0. A prova que autoriza
    # formatar o motor congelado nao pode aprovar vendo nada.
    for raiz in RAIZES:
        if not pathlib.Path(raiz).is_dir():
            print(f"raiz ausente: {raiz}", file=sys.stderr)
            return 2

    alvos = [p for raiz in RAIZES for p in pathlib.Path(raiz).rglob("*.py")]
    if args.esperados is not None and len(alvos) != args.esperados:
        print(f"esperados {args.esperados}, encontrados {len(alvos)}", file=sys.stderr)
        return 2

    antes = {p: arvore(p) for p in alvos}
    for raiz in RAIZES:
        subprocess.run(["ruff", "format", raiz], check=True)
    divergiram = [str(p) for p in alvos if arvore(p) != antes[p]]

    print(f"arquivos conferidos: {len(alvos)}")
    print("divergiram:", divergiram or "nenhum")
    return 1 if divergiram else 0


if __name__ == "__main__":
    sys.exit(main())
```

**O código de saída é o contrato, não o `print`.** O
[aprendizados.md](../aprendizados.md) registra que `grep` em saída casa com o traceback. São
três códigos: `0` prova, `1` divergiu, **`2` não conferiu o que devia** — e o terceiro existe
porque uma prova que aprova sem olhar nada é pior que prova nenhuma.

**Critério de aceite**

```bash
python tools/prova_formatacao.py --esperados 69   # divergiram: nenhum, saida 0
echo "saida=$?"

cd engine && ruff format --check . && cd ../backend && ruff format --check . && cd ..

# F5-08(b): a linha de base numerica continua passando
pytest engine/tests/baseline -q
pytest engine/tests -q                  # 58 passed

docker compose up -d --wait web
docker compose exec -T web pytest tests # 16 passed
docker compose exec -T web mypy
cd engine && mypy && cd ..
```

**Se a linha de base divergir com a árvore idêntica, a tarefa para e relata o número.** É
contradição, e é achado grave.

**Cerca de escopo**

Não corrige violação de lint. Não toca no frontend. Não remove o script.

---

### Tarefa 3 — As 28 violações de lint

**Depende de:** T2 · **Visual:** não

**Arquivos**
- altera: 12 de `engine/src/`, 2 de `engine/tests/`, 2 de `backend/`

**Contrato**

Enumeradas na spec. A ferramenta aplica a maioria; **seis exigem mão**, por duas razões
diferentes:

| Onde | Por quê | O que fazer |
|---|---|---|
| `engine/src/engine/experiments/runner.py`, duas `RUF100` | o `--fix` **estragaria**: apaga `# noqa: BLE001 - isola falha de …` com a intenção escrita junto | **converter em comentário comum**, mantendo a explicação |
| `backend/config/settings_test.py`, uma `RUF100` | o `--fix` acerta, e é parcial: remove `E402`, mantém `F403` | aceitar |
| `engine/src/engine/models/ml/_quantile_nn.py`, uma `RUF012` | **`RUF012` não tem correção automática** — medido: `--fix` resolve 26 de 27 e deixa exatamente esta | anotar com `ClassVar` |
| `backend/apps/accounts/models.py`, uma `RUF012` | idem — no backend, `ruff check .` reporta `1 fixable` de 2, e a fixável é a `RUF100` | anotar `REQUIRED_FIELDS` com `ClassVar` |
| `engine/tests/models/test_ml_diagnostics.py:17`, uma `F841` | não é auto-fixável | remover a variável morta |

As duas `UP033` de `engine/tests/` a ferramenta aplica sozinha
(`lru_cache(maxsize=None)` → `functools.cache`, o mesmo objeto).

**O separador dos `# noqa` é hífen ASCII, não travessão** — no arquivo é
`# noqa: BLE001 - isola falha de …`. O `grep` do critério usa o prefixo comum e não depende
disso, mas quem for casar o texto inteiro tropeça.

**Cuidado com a `F841`:** o mesmo desempacotamento `train, test = ...` aparece duas vezes no
arquivo, nas linhas 17 e 27, e só a primeira é acusada — a segunda usa `test`. Corrigir a
errada não resolve e quebra o outro teste.

**Critério de aceite**

```bash
cd engine && ruff check . && ruff format --check . && cd ..
cd backend && ruff check . && ruff format --check . && cd ..

# a intencao dos noqa do motor sobreviveu. O texto das duas linhas difere -- uma diz
# "1 modelo", a outra "1 (modelo, alpha)" -- entao o padrao e o prefixo comum.
grep -c "isola falha de 1" engine/src/engine/experiments/runner.py   # 2
grep -c "noqa: BLE001"     engine/src/engine/experiments/runner.py   # 0
grep -c "noqa: F403"       backend/config/settings_test.py           # 1

# F5-06 pelo comando do CONTRATO, que e o que o M1.1 herda e o README vai citar
docker compose exec -T web sh -c "ruff check . && ruff format --check ."

# nada quebrou
pytest engine/tests -q
docker compose exec -T web pytest tests
docker compose exec -T web mypy
```

**Cerca de escopo**

Não muda comportamento. Não toca no `valores.json`. Não corrige `UP042`.

---

### Tarefa 4 — Biome no frontend

**Depende de:** T3 · **Visual:** não

**Arquivos**
- cria: `frontend/biome.json`
- altera: `frontend/package.json`, `frontend/package-lock.json`, e o que o Biome apontar

**Contrato**

O `biome.json` entra literal, pela mesma razão dos blocos de `ruff`: **sem conteúdo definido,
F5-07 aprova qualquer escolha, inclusive a que desliga tudo.**

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.12/schema.json",
  "files": { "includes": ["src/**", "tests/**", "*.ts", "*.json"] },
  "formatter": { "enabled": true, "indentStyle": "space", "indentWidth": 2, "lineWidth": 88 },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "correctness": { "useExhaustiveDependencies": "error", "useHookAtTopLevel": "error" }
    }
  },
  "assist": { "actions": { "source": { "organizeImports": "on" } } },
  "overrides": [
    {
      "includes": ["tests/**"],
      "linter": { "rules": { "suspicious": { "noExportsInTest": "off" } } }
    }
  ]
}
```

**O `overrides` não é conveniência, e sem ele a T4 não passa.** Medido: o `recommended`
acusa `noExportsInTest` em `frontend/tests/cores.test.ts`, que **exporta de propósito** a
função auxiliar da varredura de cor literal — o artefato que prova um requisito do F2b.
As duas saídas eram reestruturar aquele teste, mexendo em prova de bloco fechado, ou
desligar a regra onde ela não cabe. O override é estreito, vale só para `tests/**`, e as
duas regras de React seguem valendo lá.

**O arquivo precisa passar pela propria ferramenta antes de o criterio rodar.** O bloco acima
tem uma linha de 96 colunas -- a do `formatter` --, acima do `lineWidth: 88` que ela mesma
declara: gravado como esta, `npm run lint` sai **1**. Rode `biome check . --write` sobre ele e
**prove que a configuracao nao mudou**, por igualdade profunda de JSON contra este bloco. A
alternativa -- tirar `*.json` do `files.includes` -- mudaria a configuracao, e nao e essa a
escolha.

**As duas regras de React são declaradas, e não deixadas ao "recomendado".** São o motivo pelo
qual a spec registrou ressalva ao escolher o Biome em vez do `eslint-plugin-react-hooks`:
declará-las explicitamente é o que torna a escolha honesta. `lineWidth: 88` casa com o
`line-length` do lado Python.

`package.json` ganha `"lint": "biome check ."` — `check` faz lint **e** formatação numa
invocação, e reporta sem escrever; `--write` é que aplica.

`@biomejs/biome` entra em `devDependencies`, com a versão **confirmada no registro** (era
`2.5.12` na escrita da spec) e igual à do `$schema` acima.

**Depois de mexer no `package.json`, `--renew-anon-volumes`** — o volume anônimo do
`node_modules` sobrevive à recriação e apagaria a dependência nova
([aprendizados.md](../aprendizados.md)).

**Critério de aceite**

```bash
docker compose up -d --build --renew-anon-volumes --wait frontend

# F5-03 e F5-07: os quatro comandos, dentro da imagem
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run build

# a varredura de cor literal do F2b sobreviveu a formatacao
docker compose exec -T frontend npx vitest run tests/cores.test.ts
```

**Cerca de escopo**

Não mexe em `vite.config.ts`, no proxy, em `tokens.css` nem em `brand/`. Não acrescenta regra
além das duas nomeadas acima.

---

### Tarefa 5 — O fluxo da CI, e as sequências rodadas à mão

**Depende de:** T3 · **Visual:** não

**Arquivos**
- cria: `.github/workflows/ci.yml`

**Contrato**

```yaml
name: CI

on:
  push:
    branches: [main]
  workflow_dispatch:

# timeout-minutes em todos: o repositorio e privado, a cota mensal vale, e um job
# pendurado a consome inteira. O `motor` baixa TensorFlow e tem folga maior.
jobs:
  estilo:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@<confirmar>
      - uses: actions/setup-python@<confirmar>
        with: { python-version: "3.12" }
      # A versao sai do pyproject, nao daqui: numero repetido diverge em silencio (D-43).
      - run: |
          RUFF=$(python -c "import tomllib;d=tomllib.load(open('backend/pyproject.toml','rb'));\
          print(next(x for x in d['project']['optional-dependencies']['dev'] if x.startswith('ruff')))")
          pip install "$RUFF"
      - run: cd backend && ruff check . && ruff format --check .
      - run: cd engine && ruff check . && ruff format --check .

  backend:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@<confirmar>
      - run: cp .env.example .env
      - run: docker compose up -d --wait web
      - run: docker compose exec -T web python manage.py migrate
      - run: docker compose exec -T web pytest tests
      - run: docker compose exec -T web mypy

  frontend:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@<confirmar>
      - run: cp .env.example .env
      - run: docker compose up -d --wait frontend
      - run: docker compose exec -T frontend npm run lint
      - run: docker compose exec -T frontend npm test
      - run: docker compose exec -T frontend npm run typecheck
      - run: docker compose exec -T frontend npm run build

  motor:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@<confirmar>
      - uses: actions/setup-python@<confirmar>
        with: { python-version: "3.12" }
      - run: pip install -r engine/requirements-lock.txt
      - run: pip install -e "./engine[all]" -c engine/requirements-lock.txt
      # Sem a linha de base: ela nao e portatil entre plataformas -- 8 das 58
      # reprovam em Linux, e o EGARCH converge para outro otimo. Medido na T5.
      - run: pytest engine/tests --ignore=engine/tests/baseline
      - run: cd engine && mypy
```

**`<confirmar>` é literal no plano de propósito:** a T5 lê a etiqueta maior corrente no
repositório de cada ação e a fixa, como o F3 fez com etiqueta de imagem. Inventar versão de
ação é o mesmo defeito que inventar etiqueta.

**Três coisas que, se erradas, quebram em silêncio:**

1. `cp .env.example .env` **antes** de qualquer `compose` — são onze ocorrências de `${VAR:?}`,
   e o `.env` não vem no clone.
2. `docker compose up` **sempre com o serviço nomeado.** Sem nome sobe tudo, e constrói os
   3,79 GB da `worker`.
3. O `migrate` **antes** do `pytest`. Sem ele reprovam quatro testes, e a falha parece
   regressão do F4.

**A tarefa também roda as três sequências à mão**, porque a spec classifica F5-02, F5-03 e
F5-04 como prováveis localmente, e descobrir erro nelas só na T8 custaria sete commits.

**Critério de aceite**

```bash
# F5-05 local, PRIMEIRO passo -- captura antes de qualquer coisa rodar.
#
# Nao se prova pela ausencia: a imagem existe nesta maquina desde o F3, e apagar
# 3,79 GB para reconstruir e o custo que o requisito existe para evitar. O que se
# prova aqui e que o identificador nao mudou; a ausencia so e verificavel no runner,
# e e a T8 que a confirma.
ANTES=$(docker image ls -q ruvor-worker)

# YAML valido, quatro trabalhos, sem gatilho de PR.
# `on:` vira a chave booleana True no PyYAML -- conferido; nao e `d["on"]`.
python -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); \
  assert sorted(d['jobs'])==['backend','estilo','frontend','motor'], sorted(d['jobs']); \
  assert 'pull_request' not in d[True]; print('ok')"

# F5-05: nenhum compose sem servico nomeado, E nenhuma mencao a worker
! grep -nE 'docker compose (up|build)( -[^ ]+)*[[:space:]]*$' .github/workflows/ci.yml
! grep -n 'worker' .github/workflows/ci.yml

# os tres passos que quebram em silencio
grep -q 'cp .env.example .env' .github/workflows/ci.yml
grep -q 'manage.py migrate'    .github/workflows/ci.yml
grep -q 'requirements-lock.txt' .github/workflows/ci.yml

# nenhuma acao ficou por confirmar
! grep -q '<confirmar>' .github/workflows/ci.yml

# F5-04 provado localmente, num ambiente limpo e descartavel
docker run --rm -v "$PWD:/repo:ro" -w /tmp python:3.12-slim sh -c "
  cp -r /repo/engine . &&
  pip install -q -r engine/requirements-lock.txt &&
  pip install -q -e './engine[all]' -c engine/requirements-lock.txt &&
  python -c 'import tensorflow, arch, engine; print(\"extras ok\")' &&
  pytest engine/tests --ignore=engine/tests/baseline -q"

# A linha de base NAO roda aqui, por causa do `--ignore` acima. Ela ja rodou uma vez
# em Linux, durante a execucao deste bloco, e divergiu: 8 das 58, com o EGARCH
# convergindo para outro otimo. Esta registrado como divida no ESTADO.md, com dono
# na trilha do TCC. Nao se conserta reescrevendo valores.json.

# F5-02 e F5-03 provados pela sequencia exata do fluxo
cp .env.example .env
docker compose up -d --wait web
docker compose exec -T web python manage.py migrate
docker compose exec -T web pytest tests
docker compose exec -T web mypy
docker compose up -d --wait frontend
docker compose exec -T frontend npm run lint

# F5-05 local, ULTIMO passo: nada acima criou nem reconstruiu a worker.
DEPOIS=$(docker image ls -q ruvor-worker)
test "$ANTES" = "$DEPOIS"
```

**A captura de `ANTES` é a primeira linha do bloco, e a de `DEPOIS` a última** — as duas
precisam envolver tudo. Juntas no fim, dariam iguais sempre e o teste passaria sem provar
nada.

**Cerca de escopo**

Não cria proteção de ramo, gatilho de `pull_request`, passo de deploy nem serviço novo no
`compose.yaml`. Não empurra nada.

---

### Tarefa 6 — As mutações

**Depende de:** T4 e T5 · **Visual:** não

**Arquivos**
- nenhum ao fim. Rastreado volta com `git checkout --`; novo sai com `rm`.

**Contrato**

Oito. Se alguma **passar**, é achado, o defeito é do plano, e a tarefa para.

| # | Mutação | Precisa reprovar | Como aplicar |
|---|---|---|---|
| a | Desformatar um arquivo de `backend/` | F5-06 | `ruff format --check .` |
| b | Import não usado em `engine/src` | F5-06 | `ruff check .` |
| c | Desformatar um arquivo de `frontend/src` | F5-07 | `npm run lint` no contêiner |
| d | Quebrar um teste do backend | F5-02 | `pytest` no contêiner |
| e | **Tirar o `migrate` da sequência do backend** | F5-02 | a sequência da T5, sem o `migrate` |
| f | Alterar um valor de `valores.json` | F5-08(b) | `pytest engine/tests/baseline` |
| g | **Mutar o próprio script**: entre a captura de `antes` e a comparação, alterar um arquivo | F5-08(a) | `python tools/prova_formatacao.py --esperados 69` |
| h | **Acrescentar `worker` ao `up -d --wait` do trabalho `backend`** | F5-05 | as **duas** varreduras da T5 |

**A `e` reprova quatro testes, não cinco** — `test_esquemas.py` (dois), `test_organizacao.py` e
`test_a_coluna_organization_id_e_not_null`. O `test_conexao_com_o_banco` passa sem `migrate`,
porque só faz `SELECT current_database()`. Confundir com o cinco do hospedeiro faz a mutação
parecer ter falhado.

**A `h` é por acréscimo, e por isso a T5 tem duas varreduras.** A que procura `compose` sem
serviço nomeado detecta a **ausência** de nome e não veria `up -d --wait web worker`; quem a
pega é a segunda, `! grep -n 'worker' ci.yml`. Provar por construção real seria construir os
3,79 GB que o requisito existe para evitar.

**A `g` muta o script, e não um arquivo de código — e isso foi provado.** A forma óbvia da
mutação, *"trocar uma linha por outra semanticamente diferente e rodar a prova"*, **passa**:
foi aplicada numa cópia, trocando uma expressão por `0.0` em
`models/traditional/parametric.py`, e o script saiu **0**. Tem de sair: ele captura `antes`
**depois** da edição, então a mudança está nos dois lados da comparação. Ele prova que **a
formatação** não mexeu na árvore, não que o arquivo não mudou.

O que se testa aqui é o **instrumento**, então a mutação vai nele — acrescentar, entre a
captura de `antes` e a comparação, uma linha que altere um arquivo:

```python
# MUTACAO g -- entre `antes` e a comparacao
alvo = pathlib.Path("engine/src/engine/models/base.py")
alvo.write_text(alvo.read_text(encoding="utf-8") + "\nX = 1\n", encoding="utf-8")
```

O script precisa sair **1** e nomear o arquivo. Se sair 0, a prova que autoriza formatar
código congelado sob a D-21 não sabe reprovar, e a tarefa para.

**A `g` usa o script versionado da T2.** Não há o que restaurar do histórico.

**Critério de aceite**

As oito aplicadas e revertidas, com comando, saída e **código de saída**; `git status` limpo ao
fim, incluindo não rastreados.

**Cerca de escopo**

Não corrige nada, não deixa arquivo alterado, não commita.

---

### Tarefa 7 — Documentação

**Depende de:** T6 · **Visual:** não

**Arquivos**
- altera: `README.md`, `CLAUDE.md`, `docs/ESTADO.md`, `docs/ARQUITETURA.md`,
  `docs/specs/README.md`, `docs/planos/README.md`

**Contrato**

Mesma divisão do F4: **a T7 escreve o que já é fato; o FECHA escreve o que é status.** A T7
não toca em `ROADMAP.md`, na posição do `ESTADO.md`, em `aprendizados.md` nem nos cabeçalhos.

1. `README.md` — os três comandos de estilo em "Comandos do dia a dia", e a seção de CI
2. `CLAUDE.md` — a linha do `frontend/`, que hoje cita só a varredura de cor literal
3. `docs/ARQUITETURA.md` — a promessa da CI (D-42), a linha 60 do `infra/` (D-45), e
   *"A CI espelha o contêiner, não o `.venv`"* (D-43)
4. `docs/ESTADO.md` — a pendência "Ferramenta de estilo" **sai** de "Aberto e aguardando
   decisão"; a contagem passa de 41 para 45 decisões
5. os índices de `specs/` e de `planos/`. **`decisoes/README.md` ja esta feito** — as
   quatro decisoes nasceram junto com a aprovacao da spec, como o PROCESSO manda

**Critério de aceite**

```bash
# a varredura precisa ACUSAR antes de editar. A frase da CI esta quebrada entre as
# linhas 317 e 318 da ARQUITETURA: grep pela sentenca inteira NAO casa.
! grep -q "passou, não entra"        docs/ARQUITETURA.md
! grep -q "CI a partir do F5"        docs/ARQUITETURA.md
! grep -q "A CI espelha o contêiner" docs/ARQUITETURA.md
! grep -qE "^\| \*\*Ferramenta de estilo\*\*" docs/ESTADO.md
! grep -q "41 decisões registradas" docs/ESTADO.md

grep -q "ruff" README.md
grep -qi "biome" README.md
grep -qE "^\| \[?F5" docs/specs/README.md
grep -qE "^\| \[?F5" docs/planos/README.md
# decisoes/README.md nao entra: ja tem as quatro desde a aprovacao da spec, e um
# grep por D-45 passaria antes de a T7 tocar em nada.
```

**Cerca de escopo**

Não altera código. Não marca o bloco como fechado.

---

### Tarefa 8 — O primeiro push, e a leitura da primeira execução

**Depende de:** T7 · **Visual:** não

**Arquivos** — nenhum. Não produz commit de conteúdo.

**Contrato**

Única tarefa que sai da máquina, e única forma de provar F5-01. O `git push` envia **38 commits
anteriores** mais os sete deste bloco. O repositório é **privado**, confirmado — o push não
publica para fora da conta.

**Entrega quatro coisas:** que os quatro trabalhos executem até o fim; o resultado de cada um;
a **duração** de cada um, que a spec exige para decidir sobre cota; e a confirmação de que
nenhum construiu a `worker`.

**A fronteira que decide o destino de cada achado**, e ela é por passo, não por julgamento:

| Onde falhou | Quem paga |
|---|---|
| `checkout`, `setup-python`, `cp .env.example .env`, `pip install`, `docker compose up` | **preparação** — é defeito do F5, volta para a T5 |
| `ruff`, `pytest`, `mypy`, `npm run …`, `migrate` | **verificação** — é achado sobre o repositório; vira dívida com dono, e o F5 fecha |

**O candidato mais provável, e não é defeito do F5:** a linha de base numérica. O lock congela
versão, não plataforma; `valores.json` foi capturado no Windows, e a tolerância é 1e-6. A
mensagem aponta para o F2a e engana.

**Critério de aceite**

```bash
git push origin main
```

E, da execução: os quatro trabalhos com estado, duração e o passo em que cada um parou, se
parou; e a confirmação de que nenhuma construção produziu `ruvor-worker`. **O relato traz o
registro, não a interpretação.**

**Cerca de escopo**

Não conserta o que a execução achar — a decisão é do orquestrador, pela regra da spec. Não
cria proteção de ramo. Não força push.

---

## O que fica para o passo FECHA

| Arquivo | O quê |
|---|---|
| `docs/ROADMAP.md` | F5 de ⬜ a ✅ — **e a Fundação fecha** |
| `docs/ESTADO.md` | posição, bloco concluído, próximo passo: M1.1 |
| `docs/ESTADO.md` | **o resultado da primeira execução**, e a dívida do que ela achar |
| `docs/specs/README.md`, `docs/planos/README.md` | situação de 🟡 a ✅ |
| cabeçalhos desta spec e deste plano | deixam de dizer "em revisão" |
| `docs/aprendizados.md` | o que custou tempo — inclusive os três erros de medição desta spec |

**E o FECHA empurra.** Ele produz commits depois da T8, e deixá-los parados recriaria
exatamente a situação que a seção "Problema" da spec descreve como motivo do bloco existir.

```bash
! grep -qE '^\| ⬜ \| \*\*F5' docs/ROADMAP.md
! grep -q "F5 é o próximo" docs/ESTADO.md
grep -q '^\*\*Status:\*\* ✅ \*\*implementada e fechada\*\*' docs/specs/F5-integracao-continua.md
grep -q '^\*\*Status:\*\* ✅ \*\*executado e fechado\*\*' docs/planos/F5-integracao-continua.md
git push origin main && git status -sb | head -1   # sem "ahead"
```
