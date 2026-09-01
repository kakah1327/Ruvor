# F2a — Plano de implementação

**Spec:** [F2a — Migração do motor](../specs/F2a-migracao-do-motor.md)
**Status:** rascunho, aguardando revisão

**Objetivo:** tirar o motor numérico de `varlab/`, colocá-lo em `engine/` com layout `src/`,
aplicar o rebrand e provar que o comportamento não mudou.

**Ramo:** `f2a-migracao-do-motor`. Um commit por tarefa.

---

## Como ler este plano

Segue o [PROCESSO §5](../PROCESSO.md#5-anatomia-de-um-plano): contratos, não corpos — com as
duas exceções que a própria regra prevê. Quatro tarefas trazem conteúdo literal, porque nelas
**o conteúdo é o contrato** (T4, T10, T11) ou **a lógica é sutil e a falha é silenciosa**
(T6). As outras oito fixam só contrato e critério.

Toda tarefa é executável por alguém que nunca participou da conversa.

---

## Mapa de arquivos

### Migram para `engine/src/engine/`

| De | Para |
|---|---|
| `varlab/__init__.py` | `engine/src/engine/__init__.py` |
| `varlab/models/` (17 arquivos) | `engine/src/engine/models/` |
| `varlab/backtesting/` (7 arquivos) | `engine/src/engine/backtesting/` |
| `varlab/data/` sem o `cache.py` (5 arquivos) | `engine/src/engine/data/` |
| `varlab/experiments/` (2 arquivos) | `engine/src/engine/experiments/` |
| `varlab/cli.py` | `engine/src/engine/cli.py` |

**33 arquivos.**

### Migram para `engine/tests/`

| De | Para |
|---|---|
| `tests/conftest.py` | `engine/tests/conftest.py` |
| `tests/models/` (5 arquivos) | `engine/tests/models/` |
| `tests/backtesting/` (3 arquivos) | `engine/tests/backtesting/` |

**Verificado:** nenhum arquivo de `tests/` importa `storage`, `web` ou Flask, e nenhum depende
de rede. A suíte inteira sobrevive à remoção.

### Removidos

| Arquivo | Motivo |
|---|---|
| `varlab/data/cache.py` | código morto — `load_cached`/`save_cache` sem nenhum chamador |
| `varlab/storage/` (2 arquivos) | SQLite sai; PostgreSQL entra no F4 |
| `varlab/web/` (5 arquivos) | Flask sai; Django entra no F2b |
| `pyproject.toml` (raiz) | um projeto Python por diretório |

### Permanecem, com imports reescritos

| Arquivo | O que muda |
|---|---|
| `tools/garch_rcheck/export_for_r.py` | linhas 14–17 |
| `tools/garch_rcheck/rugarch_check.R` | nada — não toca Python |
| `tools/docx/docx2md.py` | nada — não importa o pacote |

### Criados

| Arquivo | Responsabilidade |
|---|---|
| `engine/pyproject.toml` | metadados de `ruvor-engine`, dependências, pytest e mypy |
| `engine/requirements-lock.txt` | ambiente de referência congelado |
| `engine/tests/baseline/valores.json` | linha de base numérica |
| `engine/tests/baseline/test_linha_de_base.py` | compara motor migrado contra a linha de base |
| `engine/tests/test_modulos_proibidos.py` | prova que `engine/` não importa plataforma |
| `.gitattributes` | normalização de fim de linha |

### Alterados

| Arquivo | O que muda |
|---|---|
| `.env.example` | esvaziado, com comentário apontando o F2b |
| `.gitignore` | comentário da linha 11, que cita `~/.varlab` |
| `README.md` | bloco de aviso reescrito e instruções Python atualizadas |

### Explicitamente intocados neste bloco

`frontend/` (é do F2b), `brand/`, `docs/`, `CLAUDE.md`. O `CLAUDE.md` descreve `varlab/` como
código atual e ficará desatualizado — a correção é do passo **FECHA** do
[PROCESSO §3](../PROCESSO.md#3-o-ciclo), porque exige reescrever conteúdo, não trocar nome. O
`frontend/src/` cita `varlab` legitimamente e está fora do alvo do rebrand.

---

## Ordem e dependências

```
T1  ambiente e trava
└── T2  captura da linha de base        ← antes de qualquer remoção
    └── T3  mover o motor
        └── T4  empacotamento e instalação   ← engine só é importável a partir daqui
            ├── T5  mover a suíte
            ├── T6  teste de módulos proibidos
            └── T7  reescrever tools/
                └── T8  remover o que morre        (depende de T5, T6 e T7)
                    ├── T9  teste de linha de base
                    ├── T10 verificação de tipos
                    └── T11 .gitattributes
                        └── T12 rebrand final e README
```

**A T4 vem antes de tudo que importa o pacote.** O layout `src/` existe justamente para que
`import engine` só funcione instalado — sem a T4, os critérios de T5, T6 e T8 não teriam como
rodar.

T5, T6 e T7 tocam arquivos disjuntos e podem correr em paralelo. As demais são sequenciais.
Não há tarefa só de criar diretório: cada uma cria o que precisa, porque o git não versiona
diretório vazio e um commit sem conteúdo não existe.

---

### Tarefa 1 — Ambiente de referência e trava

**Depende de:** nada. É a primeira, sem exceção.
**Visual:** não

**Arquivos**
- cria: `engine/requirements-lock.txt`

**Contrato**

Ambiente virtual limpo, Python 3.12, criado a partir do `pyproject.toml` **atual** (o do
protótipo — o `engine/pyproject.toml` só nasce na T4), com os grupos `traditional`, `garch`,
`ml` e `dev`. Sem `web`, sem `storage`.

O arquivo começa com um comentário registrando a versão exata do Python. As **duas** linhas de
instalação editável são removidas: o `-e file:///…` e o comentário
`# Editable install with no version control (varlab==0.1.0)` que o acompanha — este cita
`varlab`, e deixá-lo colocaria o nome dentro de um arquivo em `engine/`, alvo da varredura de
rebrand.

`mypy` e `build`, exigidos por T4 e T10, **não estão nesta trava** — o grupo `dev` do protótipo
só tem `pytest`. Eles entram no `engine/pyproject.toml` na T4. A trava descreve o ambiente que
produziu a linha de base, não o ambiente de desenvolvimento.

**Este ambiente é preservado** até o fim da T9: a T2 captura a linha de base nele, e a T9
compara nele. Recriá-lo pelas faixas de versão do `pyproject.toml` novo poderia resolver
`arch` ou `scipy` em versão diferente, e a comparação de `1e-6` reprovaria por motivo errado.

**Critério de aceite**

```bash
test -f engine/requirements-lock.txt
head -1 engine/requirements-lock.txt | grep -q "3\.12"
! grep -qi "varlab" engine/requirements-lock.txt
! grep -q "^-e " engine/requirements-lock.txt
# a trava descreve o ambiente inteiro, nao so um cabecalho
grep -q "^numpy==" engine/requirements-lock.txt
grep -q "^tensorflow==" engine/requirements-lock.txt
grep -q "^arch==" engine/requirements-lock.txt
test "$(grep -c "==" engine/requirements-lock.txt)" -gt 30
```

**Cerca de escopo**

Não cria `engine/src/`. Não move arquivo. Não altera `pyproject.toml`.

---

### Tarefa 2 — Captura da linha de base

**Depende de:** T1
**Visual:** não

**Arquivos**
- cria: `engine/tests/baseline/valores.json` (e o diretório que o contém)

**Contrato**

Um script executado **no ambiente da T1** roda contra `varlab.*` e grava o JSON. **O script não
é versionado** — escreva-o fora da árvore do repositório para que não entre no commit por
engano. O artefato que sobrevive é o JSON.

Parâmetros, conforme a spec:

| Parâmetro | Valor |
|---|---|
| Série | `numpy.random.default_rng(42).normal(0, 0.01, 552)`, índice `pandas.bdate_range("2020-01-01", periods=552)` |
| Divisão | 252 primeiros dias de treino, **300** de teste |
| `alpha` | `0.05` e `0.01` |
| `horizon` | `1` |

**São 552 dias, não os 500 da fixture atual.** O teste de Basileia exige janela mínima de 250
dias úteis e levanta `ValueError` abaixo disso; com 500 dias sobrariam 248 de teste e o quarto
backtest falharia nas 12 combinações.

O caminho de execução é **chamada direta**: `fit` sobre o treino, `estimate_var` sobre o teste,
e os quatro backtests sobre o par alinhado — não `run_experiment`, que exige um provider. A T9
usa o mesmo caminho.

O JSON congela, por combinação de modelo determinístico e `alpha`:

- a **série de VaR completa** — não o primeiro valor, não uma estatística resumida
- o resultado dos **quatro** testes de backtesting: `statistic`, `p_value`, `passed`

Modelos cobertos, e só estes: `parametric`, `historical`, `monte_carlo`, `garch_1_1`,
`egarch`, `caviar`.

Estrutura: `parametros` no topo, `entradas` com as 12 combinações.

**Critério de aceite**

```bash
python -c "
import json, math
d = json.load(open('engine/tests/baseline/valores.json', encoding='utf-8'))
e = d['entradas']
assert len(e) == 12, len(e)
for k, v in e.items():
    assert len(v['var']) == 300, (k, len(v['var']))
    assert all(x is not None and math.isfinite(x) for x in v['var']), k
    assert len(v['backtests']) == 4, (k, len(v['backtests']))
print('ok')
"
! grep -qi "varlab" engine/tests/baseline/valores.json
```

**Cerca de escopo**

Não inclui `lstm`, `gru` nem `garchnet` — não fixam semente e divergem entre execuções.

**O JSON não pode conter `varlab` em campo nenhum** — nem em nome de classe, nem em caminho de
módulo, nem em metadado de proveniência. Ele vive dentro de `engine/`, que é alvo da varredura
de rebrand da T12, e uma string dessas reprovaria lá na frente.

Não move nem remove nada.

---

### Tarefa 3 — Mover o motor

**Depende de:** T2
**Visual:** não

**Arquivos**
- cria: o diretório `engine/src/engine/`
- move: `varlab/{__init__.py,models/,backtesting/,experiments/,cli.py}` → `engine/src/engine/`
- move: `varlab/data/{__init__.py,preprocessing.py,providers/}` → `engine/src/engine/data/`
- altera: os arquivos movidos que citam `varlab`, `VaR Lab`, Flask ou o comando `web`

**Contrato**

Movimentação com `git mv`, para preservar histórico. Depois, dentro dos arquivos movidos:

- `varlab.` vira `engine.` em todo import
- `varlab` e `VaR Lab` são substituídos também em **docstring e comentário** — são 10
  ocorrências fora de linhas de import, entre elas `__init__.py:1`, `cli.py:1`, `cli.py:12`,
  `backtesting/base.py:5`, `backtesting/registry.py:1` e `models/registry.py:6-7`
- o comando `web` sai de `cli.py` (importa Flask, que está sendo removido) e a opção `--save`
  sai de `run` (importa `storage`)
- a docstring do topo de `cli.py` (linhas 1–3) fica factualmente falsa depois disso: ela cita
  o comando `web` e afirma que a lógica "nunca depende do Flask estar rodando". A linha 1 já
  entra nas 10 ocorrências de rebrand; as linhas 2–3 são reescritas por serem falsas, não por
  citarem o nome antigo. Vale também para `cli.py:39`, "sem subir a web"

**A lógica de modelo não muda.** Fora a remoção do comando `web` e da opção `--save` — ambas
autorizadas acima — nenhuma linha de código executável é editada. É o que a
[D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) exige e o que torna a comparação da
T9 válida. Docstring e comentário não são lógica.

**Contrato do pacote a partir daqui:**

```python
from engine.models import get_model, list_models, load_all_model_modules
from engine.backtesting import get_backtest, list_backtests, load_all_backtest_modules
from engine.experiments.runner import ExperimentConfig, ExperimentResult, run_experiment
from engine.data.providers.yfinance_provider import YFinanceProvider
```

**Critério de aceite**

```bash
find engine -name __pycache__ -type d -exec rm -rf {} +   # .pyc obsoleto contem "varlab"
! grep -rniE "varlab|VaR Lab" engine/src/
test "$(find engine/src/engine -name '*.py' | wc -l)" -eq 33
! grep -nE "def web|--save|flask|Flask" engine/src/engine/cli.py
```

Verificação de importação vem na T4, quando o pacote passa a ser instalável.

**Cerca de escopo**

Não remove `varlab/web/`, `varlab/storage/` nem `varlab/data/cache.py` — é a T8. Não toca em
`tests/` nem em `tools/`. Nenhuma alteração de lógica de modelo ou de backtesting.

---

### Tarefa 4 — Empacotamento e instalação

**Depende de:** T3
**Visual:** não

**Arquivos**
- cria: `engine/pyproject.toml`

**Contrato** — *o conteúdo é o contrato ([PROCESSO §5](../PROCESSO.md#quando-o-conteúdo-entra-no-plano))*

```toml
[project]
name = "ruvor-engine"
version = "0.1.0"
description = "Motor de modelagem e backtesting de risco do Ruvor"
requires-python = ">=3.12"
dependencies = ["click>=8.1"]

[project.optional-dependencies]
traditional = ["numpy>=1.26", "scipy>=1.11", "pandas>=2.1", "yfinance>=0.2"]
garch = ["arch>=6.3", "statsmodels>=0.14"]
ml = ["tensorflow>=2.16"]
dev = ["pytest>=8.0", "mypy>=1.11", "build>=1.2", "setuptools>=68"]
all = ["ruvor-engine[traditional,garch,ml,dev]"]

[project.scripts]
ruvor = "engine.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Os grupos `web` e `storage` do protótipo deixam de existir. A configuração do mypy entra na
T10, no mesmo arquivo.

Contrato da linha de comando, preservado do protótipo:

```
ruvor run --ticker <T> --start <D> --end <D>
          --model <M>...  --backtest <B>...
          [--alpha <A>...]        repetível, padrão: 0.05 e 0.01
          [--train-window <N>]    padrão: 252
```

**`--alpha` e `--train-window` permanecem com os mesmos padrões.** `--train-window` altera
diretamente o número produzido; mudá-la quebraria a linha de base.

**Critério de aceite**

No ambiente da T1, que não tem Django nem Flask:

```bash
pip install -e "./engine[all]"
python -c "import engine.cli; print('ok')"
ruvor --help | grep -q "run"
! ruvor --help | grep -q "web"
ruvor run --help | grep -q -- "--alpha"
ruvor run --help | grep -q -- "--train-window"
! ruvor run --help | grep -q -- "--save"
python -m build --no-isolation engine
```

`--no-isolation` evita que a construção baixe `setuptools` da rede. Ele **só funciona porque
o grupo `dev` declara `setuptools`**: desde o Python 3.12 o `ensurepip` não o instala mais num
ambiente novo, e nem a instalação editável nem o pacote `build` o colocam lá. Sem essa
declaração, o comando falharia por ausência do backend de construção — falha por motivo
errado.

**Cerca de escopo**

Não fixa versão exata de dependência — o motor é biblioteca e usa faixas. A trava da T1 é que
congela versões. Não adiciona configuração de mypy — é da T10.

---

### Tarefa 5 — Mover a suíte de testes

**Depende de:** T4
**Visual:** não

**Arquivos**
- move: `tests/conftest.py`, `tests/models/`, `tests/backtesting/` → **para dentro de**
  `engine/tests/`
- altera: os 6 arquivos de teste que citam `varlab`

**Contrato**

⚠️ **`engine/tests/` já existe** — a T2 gravou `engine/tests/baseline/valores.json` lá dentro.
Um `git mv tests engine/tests` moveria o diretório **para dentro** do existente, criando
`engine/tests/tests/`. O layout ficaria errado e os critérios ingênuos passariam do mesmo
jeito. Mova o **conteúdo**, não o diretório.

Depois, nos seis arquivos que citam o pacote — `test_all_models.py`,
`test_garch_diagnostics.py`, `test_ml_diagnostics.py`, `test_traditional_reference.py`,
`test_all_backtests.py`, `test_formulas.py` — troca-se `varlab.` por `engine.` nos imports
**e** `varlab` por `engine` nas docstrings, que citam caminhos como `varlab/models/…`.

O `conftest.py` não cita o pacote — move sem alteração.

**Critério de aceite**

```bash
test -f engine/tests/conftest.py
test -d engine/tests/models && test -d engine/tests/backtesting
! test -d engine/tests/tests        # o erro silencioso do git mv
rm -rf tests                        # git mv nao remove o __pycache__ que sobra
! test -d tests
pytest engine/tests
find engine -name __pycache__ -type d -exec rm -rf {} +   # DEPOIS do pytest, ver abaixo
! grep -rniE "varlab|VaR Lab" engine/tests/
```

> **A limpeza de `__pycache__` vem depois do `pytest`, não antes.** O diretório do
> repositório se chama `varlab`, e o caminho absoluto fica embutido no bytecode — então
> `.pyc` gerado pela própria execução dos testes casa com o `grep` de rebrand. Limpar antes
> não adianta: o pytest regenera.

**Cerca de escopo**

Nenhum teste é reescrito, renomeado ou tem asserção alterada. Só caminho de import e docstring.

---

### Tarefa 6 — Teste de módulos proibidos

**Depende de:** T4
**Visual:** não

**Arquivos**
- cria: `engine/tests/test_modulos_proibidos.py`

**Contrato** — *a lógica é sutil e a falha é silenciosa ([PROCESSO §5](../PROCESSO.md#quando-o-conteúdo-entra-no-plano))*

Este teste materializa a regra inegociável da
[D-17](../decisoes/D-17-monorepo-engine-sem-django.md), e **já foi escrito de forma vazia três
vezes** durante a revisão:

1. `import engine` não carrega submódulo nenhum
2. os dois carregadores de registry não alcançam `data/`, `experiments/` nem `cli.py`
3. **e este:** engolir `ImportError` torna a inspeção em execução inerte, porque nenhum módulo
   proibido está instalado em ambiente nenhum do projeto — logo `sys.modules` nunca os recebe,
   e o teste aprova mesmo com `import flask` no código

A correção do terceiro caso é registrar **também a tentativa de import de um proibido ausente**,
distinguindo-a da ausência de dependência opcional legítima.

```python
"""Prova que engine/ nao importa nenhuma biblioteca de plataforma.

Duas verificacoes, porque nenhuma sozinha fecha o buraco:
- inspecao em execucao pega import em nivel de modulo
- varredura estatica pega import diferido, dentro do corpo de funcao
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

import engine

PROIBIDOS = frozenset(
    {"django", "rest_framework", "celery", "flask", "fastapi", "sqlalchemy"}
)
RAIZ_FONTE = Path(engine.__file__).parent

# Importa TODO submodulo do pacote e imprime os proibidos encontrados. Roda em
# subprocesso para que modulos trazidos pelo pytest nao contaminem a medicao.
#
# Registra duas coisas: proibido que chegou a ser CARREGADO, e proibido que o
# codigo TENTOU importar mas nao esta instalado. Sem a segunda, o teste seria
# inerte — nenhum proibido esta instalado neste projeto, entao um `import flask`
# no codigo produziria ModuleNotFoundError, seria engolido, e passaria despercebido.
_SONDA = """
import importlib, pkgutil, sys
import engine

PROIBIDOS = {"django", "rest_framework", "celery", "flask", "fastapi", "sqlalchemy"}
tentados = set()

for _, nome, _ in pkgutil.walk_packages(engine.__path__, engine.__name__ + "."):
    try:
        importlib.import_module(nome)
    except ModuleNotFoundError as erro:
        ausente = (erro.name or "").split(".")[0]
        if ausente in PROIBIDOS:
            tentados.add(ausente)
        # senao: dependencia opcional ausente e esperado — ver D-29
    except ImportError:
        pass

carregados = {m.split(".")[0] for m in sys.modules}
print(",".join(sorted((carregados & PROIBIDOS) | tentados)))
"""

# Simula a ausencia do TensorFlow sem exigir um segundo ambiente.
_BLOQUEIO_TF = """
import sys
class _Bloqueio:
    def find_spec(self, nome, caminho=None, alvo=None):
        if nome.split(".")[0] in {"tensorflow", "keras"}:
            raise ImportError("bloqueado para o teste")
        return None
sys.meta_path.insert(0, _Bloqueio())
"""


def _proibidos_encontrados(prefixo: str = "") -> set[str]:
    saida = subprocess.run(
        [sys.executable, "-c", prefixo + _SONDA],
        capture_output=True,
        text=True,
        check=True,
    )
    achado = saida.stdout.strip()
    return set(achado.split(",")) if achado else set()


@pytest.mark.parametrize(
    "prefixo, condicao",
    [("", "com tensorflow"), (_BLOQUEIO_TF, "sem tensorflow")],
)
def test_nenhum_modulo_proibido_e_carregado(prefixo: str, condicao: str) -> None:
    encontrados = _proibidos_encontrados(prefixo)
    assert not encontrados, f"{condicao}: engine importa {sorted(encontrados)}"


def test_nenhum_import_proibido_no_fonte() -> None:
    achados: list[str] = []
    for arquivo in RAIZ_FONTE.rglob("*.py"):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Import):
                nomes = [a.name.split(".")[0] for a in no.names]
            elif isinstance(no, ast.ImportFrom):
                nomes = [(no.module or "").split(".")[0]]
            else:
                continue
            achados += [
                f"{arquivo.name}:{no.lineno} -> {n}" for n in nomes if n in PROIBIDOS
            ]
    assert not achados, "imports proibidos: " + "; ".join(achados)
```

**Critério de aceite**

Os três testes passam — dois do parametrizado, um estático:

```bash
pytest engine/tests/test_modulos_proibidos.py -v
```

E **provam que detectam**, sem exigir instalar biblioteca nenhuma. Duas mutações, cada uma
revertida em seguida:

```bash
# (a) import em nivel de modulo -> o parametrizado precisa REPROVAR
#     Insere DEPOIS do `from __future__`, que precisa ser a primeira instrucao do
#     arquivo. Prefixar na linha 1 produz SyntaxError, e ai o teste reprova pelo
#     motivo errado — provaria o mesmo com qualquer arquivo quebrado.
python -c "
import pathlib; p = pathlib.Path('engine/src/engine/cli.py'); s = p.read_text(encoding='utf-8')
p.write_text(s.replace('from __future__ import annotations\n',
                       'from __future__ import annotations\n\nimport flask\n', 1), encoding='utf-8')"
if pytest engine/tests/test_modulos_proibidos.py -k carregado -q; then
  echo "FALHOU EM DETECTAR (a)"; exit 1
fi
git checkout engine/src/engine/cli.py

# (b) import diferido -> o estatico precisa REPROVAR
python -c "
import pathlib; p = pathlib.Path('engine/src/engine/cli.py'); s = p.read_text(encoding='utf-8')
p.write_text(s.replace('def main() -> None:', 'def main() -> None:\n    import flask', 1), encoding='utf-8')"
if pytest engine/tests/test_modulos_proibidos.py -k fonte -q; then
  echo "FALHOU EM DETECTAR (b)"; exit 1
fi
git checkout engine/src/engine/cli.py
```

**Cerca de escopo**

Não altera nenhum módulo do motor de forma permanente. Não amplia a lista de proibidos.

---

### Tarefa 7 — Reescrever imports em `tools/`

**Depende de:** T4
**Visual:** não

**Arquivos**
- altera: `tools/garch_rcheck/export_for_r.py`

**Contrato**

As linhas **14 a 17**, únicas ocorrências no arquivo:

```python
from varlab.data.preprocessing import fetch_returns
from varlab.data.providers.yfinance_provider import YFinanceProvider
from varlab.models.garch.egarch import EgarchVaR
from varlab.models.garch.garch_1_1 import Garch11VaR
```

passam a `engine.*`.

**Critério de aceite**

Importação **real**, não só análise sintática — `from engine.data.preprocesing import …`
passaria num `ast.parse`. Todo efeito do arquivo está sob `if __name__ == "__main__"`
(linha 52), então importar é seguro e não dispara rede:

```bash
python -c "
import importlib.util
spec = importlib.util.spec_from_file_location('_t', 'tools/garch_rcheck/export_for_r.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('ok')
"
! grep -rn "varlab" tools/
```

**Cerca de escopo**

Não altera `rugarch_check.R` nem `tools/docx/docx2md.py` — nenhum dos dois importa o pacote.

---

### Tarefa 8 — Remover o que morre

**Depende de:** T5, T6, T7
**Visual:** não

**Arquivos**
- remove: `varlab/` inteiro (o que restou: `data/cache.py`, `storage/`, `web/`)
- remove: `pyproject.toml` da raiz
- altera: `.env.example`, `.gitignore`

**Contrato**

`varlab/` deixa de existir.

`.env.example` fica com um comentário indicando que as variáveis chegam no F2b com o Django.
**O arquivo é mantido**, não apagado: é alvo da varredura de rebrand da T12, e apagá-lo
tornaria esse alvo inexistente.

No `.gitignore`, a única alteração necessária é o comentário da **linha 11**, que cita
`~/.varlab`. As demais regras (`__pycache__/`, `.venv/`, `*.parquet`, `frontend/node_modules/`)
não dependem dos caminhos que mudaram, e as duas linhas de `tools/garch_rcheck/` continuam
válidas.

**Critério de aceite**

```bash
pip uninstall -y varlab          # a instalacao editavel do prototipo sobrevive no ambiente
! test -d varlab
! test -f pyproject.toml
test -f .env.example
! python -c "import varlab" 2>/dev/null
! grep -qi "varlab" .env.example .gitignore
pytest engine/tests
```

**Cerca de escopo**

Não remove `tools/`, `frontend/`, `brand/` nem `docs/`. O `frontend/` é do F2b.

---

### Tarefa 9 — Teste de linha de base

**Depende de:** T8
**Visual:** não

**Arquivos**
- cria: `engine/tests/baseline/test_linha_de_base.py`

**Contrato**

Lê `engine/tests/baseline/valores.json`, reproduz os mesmos parâmetros contra `engine.*` pelo
**mesmo caminho de execução da T2** — chamada direta a `fit` e `estimate_var`, não
`run_experiment` — e compara.

**Roda no ambiente da T1**, o mesmo que produziu o JSON. Um ambiente novo resolvido pelas
faixas do `engine/pyproject.toml` poderia trazer `arch` ou `scipy` em versão diferente, e a
comparação reprovaria por motivo errado — exatamente o que a trava existe para evitar.

**Tolerância:** relativa de `1e-6`, **com piso absoluto de `1e-12`**.

O piso não é detalhe: `kupiec` e `christoffersen` produzem estatística próxima de zero quando
a taxa de violação bate exatamente o esperado, e p-valor próximo de zero quando a estatística
é grande. Tolerância só relativa sobre valores dessa ordem reprovaria por ruído de ponto
flutuante.

Não é igualdade bit a bit porque `caviar` usa Nelder-Mead com múltiplos reinícios, e
`garch_1_1` e `egarch` passam pela biblioteca `arch` — otimizador varia no último dígito entre
versões de patch.

Compara as séries de VaR **e** os resultados de backtesting: `statistic` e `p_value` com a
tolerância acima, `passed` com igualdade exata.

**Critério de aceite**

```bash
pytest engine/tests/baseline -v
```

12 combinações verificadas, todas passando.

**Cerca de escopo**

Não cobre `lstm`, `gru` nem `garchnet`. **Não regenera o JSON** — se divergir, o defeito está
na migração, não na linha de base.

---

### Tarefa 10 — Verificação de tipos

**Depende de:** T8
**Visual:** não

**Arquivos**
- altera: `engine/pyproject.toml`

**Contrato** — *o conteúdo é o contrato*

Rigor conforme [D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md), graduado
pela origem do código: exigir anotação obrigatória obrigaria a **editar** código que este
plano só move, contra a D-21.

```toml
[tool.mypy]
python_version = "3.12"
files = ["src"]
disallow_untyped_defs = false
warn_unused_ignores = true
warn_unused_configs = true
warn_redundant_casts = true

[[tool.mypy.overrides]]
module = ["tensorflow.*", "keras.*", "arch.*", "yfinance.*", "scipy.*"]
ignore_missing_imports = true
```

A lista de `overrides` cobre exatamente as bibliotecas de terceiros sem anotação que o código
migrado importa. `statsmodels` **não** entra: nenhum módulo do motor o importa — só o teste
`test_garch_diagnostics.py`, e o alvo do mypy é `src`, não `tests`.

**Se o mypy acusar erro em código migrado**, a saída sancionada é acrescentar
`ignore_errors = true` num override para o módulo específico, com comentário registrando a
dívida — **não** anotar o arquivo, o que violaria a cerca e a D-21. A dívida é paga depois da
Etapa 6, quando a D-21 deixar de congelar o motor.

**Critério de aceite**

O mypy procura a configuração no diretório **corrente**, não nos ancestrais do alvo — então o
comando roda de dentro de `engine/`:

```bash
cd engine && mypy
```

Passa sem erro. E a configuração está sendo lida de fato: `warn_unused_configs` faz o mypy
reclamar de seção `overrides` que não corresponde a nenhum módulo — acrescentar
`module = ["modulo_inexistente.*"]` produz aviso, e removê-lo silencia.

**Cerca de escopo**

Não adiciona anotação de tipo a nenhum arquivo migrado.

---

### Tarefa 11 — `.gitattributes`

**Depende de:** T8
**Visual:** não

**Arquivos**
- cria: `.gitattributes`

**Contrato** — *o conteúdo é o contrato*

```gitattributes
* text=auto eol=lf

*.svg  text
*.R    text
*.csv  text
*.json text

*.docx binary
*.png  binary
*.zip  binary
```

Declarar não basta: num repositório com histórico é preciso renormalizar o que já está
versionado, senão a regra vale só para arquivo novo — e o problema que ela existe para
resolver permanece.

**Critério de aceite**

```bash
test -f .gitattributes
git add .gitattributes          # --renormalize implica -u: nao adiciona arquivo novo
git add --renormalize .
git add --renormalize .
test -z "$(git status --porcelain)"   # na segunda passada precisa estar limpo
```

O `git add .gitattributes` explícito não é redundante: `--renormalize` só toca arquivo já
rastreado, então sem ele o próprio `.gitattributes` ficaria pendente e o critério reprovaria
com tudo correto.

**Cerca de escopo**

Não altera conteúdo de arquivo além do fim de linha.

---

### Tarefa 12 — Rebrand final e README

**Depende de:** T11
**Visual:** não

**Arquivos**
- altera: `README.md`

**Contrato**

O `README.md` é **reescrito**, não varrido — substituição cega apagaria conteúdo com
significado. Duas partes mudam:

**1. O bloco de aviso** (linhas 9–16, "⚠️ Este repositório está em reconstrução"). Ele afirma
que "o código presente é o protótipo VaR Lab". Depois do F2a isso fica falso: o protótipo foi
substituído pelo `engine/`. O bloco é reescrito para dizer o que passa a ser verdade — a
plataforma web ainda não existe, o motor já está no lugar, o frontend antigo sai no F2b.

**2. As instruções Python.** Instalação passa a `pip install -e ./engine`; some `varlab web`;
some `--save`; o comando vira `ruvor run`. A seção do frontend fica como está — é do F2b.

**Critério de aceite**

Sobre o próprio README:

```bash
! grep -q "varlab web" README.md
! grep -q -- "--save" README.md
! grep -q 'traditional,web,dev' README.md        # instrucao antiga de instalacao
! grep -qx "Testes: .pytest." README.md          # pytest deixa de rodar da raiz
grep -q "pip install -e ./engine" README.md
grep -q "ruvor run" README.md
# o bloco de aviso nao pode mais afirmar que o codigo presente e o prototipo
! python -c "
import pathlib, re, sys
t = re.sub(r'\s+', ' ', pathlib.Path('README.md').read_text(encoding='utf-8'))
sys.exit(0 if re.search(r'código presente é o protótipo', t, re.I) else 1)
"
```

E a varredura **normalizada**, que ignora quebra de linha — "VaR Lab" aparece dividido entre
duas linhas no README atual, e um `grep` linha a linha passaria em branco:

```bash
python -c "
import pathlib, re, subprocess, sys
# Enumera pelos arquivos RASTREADOS, nao por rglob: o rebrand vale para o que
# esta versionado. Artefato gerado (.pyc, dist/, egg-info/) nao e alvo — e
# carrega o caminho absoluto do repositorio, que hoje se chama 'varlab'.
rastreados = subprocess.run(['git','ls-files','engine','tools','.env.example','.gitignore'],
                            capture_output=True, text=True, check=True).stdout.split()
falhas = []
for nome in rastreados:
    f = pathlib.Path(nome)
    if not f.is_file(): continue
    try: texto = f.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    if re.search(r'varlab|VaR\s+Lab', re.sub(r'\s+', ' ', texto), re.I):
        falhas.append(nome)
sys.exit('encontrado em: ' + ', '.join(falhas)) if falhas else print('ok')
"
```

> **A enumeração é por `git ls-files`, não por varredura de diretório.** O diretório do
> repositório se chama `varlab`, então **todo caminho absoluto embutido em artefato gerado
> casa com o padrão** — `.pyc`, `dist/`, `egg-info/`. Varrer o disco escaparia por acidente
> (bytecode é binário e cai no tratamento de erro de decodificação), e depender disso é
> frágil. O rebrand vale para o que está versionado.

Fora da varredura, e legitimamente: `docs/prototipo/`, `docs/tcc/`, `docs/decisoes/`,
`docs/ROADMAP.md`, `docs/ESTADO.md`, as specs, o `CLAUDE.md`, o `frontend/` e o próprio
`README.md`.

**Cerca de escopo**

Não toca `CLAUDE.md` nem `docs/ESTADO.md` — a atualização deles é do passo **FECHA** do
[PROCESSO §3](../PROCESSO.md#3-o-ciclo).

---

## Cobertura da spec

| Requisito | Tarefa |
|---|---|
| F2a-01 linha de base antes de qualquer remoção | T1, T2 |
| F2a-02 `engine/` contém o motor | T3 |
| F2a-03 não importa proibidos, verificado por teste | T6 |
| F2a-04 reproduz a linha de base com `1e-6` | T9 |
| F2a-05 suíte migrada e passando | T5 |
| F2a-06 `tools/` com imports reescritos | T7 |
| F2a-07 rebrand nos alvos | T3, T5, T8, T12 |
| F2a-08 empacotamento próprio com grupos preservados | T4 |
| F2a-09 verificação de tipos | T10 |
| F2a-10 `.gitattributes` | T11 |
| F2a-11 código sem valor removido | T8 |

---

## Riscos de execução

**A T2 é irreversível na prática.** Se a linha de base for capturada errada — parâmetro
trocado, modelo faltando — o erro só aparece na T9, depois de `varlab/` já ter sido removido
na T8. Recapturar exigiria voltar o repositório. O critério de aceite da T2 verifica 12
entradas, 300 valores cada, 4 backtests e nenhum nulo, justamente para pegar isso na hora.

**O ambiente da T1 precisa sobreviver até a T9.** É ele que produziu a linha de base e é nele
que a comparação roda. Destruí-lo no meio obriga a recriar a partir de
`engine/requirements-lock.txt` — o que funciona, mas só porque a trava existe.

**A T3 é a maior tarefa do plano.** Move 33 arquivos e reescreve imports e docstrings em quase
todos. Se ficar grande demais para revisar num commit, dividir por subpacote é aceitável — a
cerca de escopo continua valendo para cada pedaço.

**A ordem T5 antes de T8 é obrigatória.** Se `varlab/` for removido antes da suíte migrar, não
há como saber se a migração quebrou alguma coisa.
