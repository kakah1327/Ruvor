"""V-06: as listas fechadas de valores que a tela traduz (M1.6c, Contratos da spec).

A tela nao mostra o valor cru: `frontend/src/content/nulos.ts` e as frases traduzem cada um.
Valor novo numa destas listas e mudanca de contrato entre a `fundamentos` e a `marco1`, nao
crescimento livre (D-99): este teste le cada lista **da fonte** e a compara com a escrita aqui
— e o frontend fixa as mesmas em `frontend/tests/nulos.test.ts`. Molde: `test_motivos.py`.

- `account_plan`, `peer_level` e `category`: os `choices`;
- `per_share_missing`: o dicionario `REASON_NULLS` **inteiro**, cada motivo e as colunas que
  ele anula;
- `market_cap_missing`: nao e `choices` nem constante — sao os literais nos `return` de
  `market_cap()`, lidos por `ast`. Todo `return` precisa ser uma tupla de dois elementos, e o
  segundo, um literal `str` ou `None`: qualquer outra forma reprova, para nenhum motivo escapar.
"""

from __future__ import annotations

import ast
import inspect
import textwrap

from apps.fundamentals.indicators import REASON_NULLS, market_cap
from apps.fundamentals.models import AccountPlan, Disclosure, PeerComparison

MENSAGEM = (
    "mudou o contrato da tela com a fundamentos — atualize "
    "`frontend/src/content/nulos.ts`, as frases e este teste, com a revisão da "
    "`marco1` (D-99)"
)

ACCOUNT_PLAN = ["general", "bank", "insurance", "unknown"]
PEER_LEVEL = ["segment", "subsector", "none"]
CATEGORY = ["fato_relevante", "comunicado", "aviso_acionistas"]

PER_SHARE_MISSING = {
    "unit": ("price_date", "close", "eps", "bvps", "pe", "pb"),
    "stale_statement": ("price_date", "close", "eps", "bvps", "pe", "pb"),
    "no_share_count": ("eps", "bvps", "pe", "pb"),
    "share_scale_unknown": ("eps", "bvps", "pe", "pb"),
    "no_price": ("price_date", "close", "pe", "pb"),
}

MARKET_CAP_MISSING = [
    "stale_statement",
    "no_share_count",
    "share_scale_unknown",
    "ambiguous_class",
    "no_price",
    "missing_class_price",
]


def test_account_plan() -> None:
    assert list(AccountPlan.values) == ACCOUNT_PLAN, MENSAGEM


def test_peer_level() -> None:
    assert list(PeerComparison.Level.values) == PEER_LEVEL, MENSAGEM


def test_category() -> None:
    assert list(Disclosure.Category.values) == CATEGORY, MENSAGEM


def test_per_share_missing_e_o_dicionario_inteiro() -> None:
    assert dict(REASON_NULLS) == PER_SHARE_MISSING, MENSAGEM


def _motivos_de_market_cap() -> list[str]:
    """Os segundos elementos literais dos `return` de `market_cap()`, na ordem do codigo.

    Reprova (`AssertionError`) o `return` que nao seja tupla de dois, e o segundo elemento que
    nao seja literal `str` nem `None`.
    """
    fonte, primeira = inspect.getsourcelines(market_cap)
    arvore = ast.parse(textwrap.dedent("".join(fonte)))
    (funcao,) = arvore.body
    assert isinstance(funcao, ast.FunctionDef) and funcao.name == "market_cap"
    retornos = [no for no in ast.walk(funcao) if isinstance(no, ast.Return)]
    assert retornos, "market_cap() sem return: a varredura ficou inerte"
    motivos: list[str] = []
    for retorno in sorted(retornos, key=lambda no: no.lineno):
        linha = primeira + retorno.lineno - 1  # a linha em `indicators.py`
        valor = retorno.value
        assert isinstance(valor, ast.Tuple) and len(valor.elts) == 2, (
            f"indicators.py, linha {linha}: return de market_cap() que não é tupla de dois "
            f"— motivo que não é literal escapa ao contrato; {MENSAGEM}"
        )
        segundo = valor.elts[1]
        assert isinstance(segundo, ast.Constant) and (
            segundo.value is None or isinstance(segundo.value, str)
        ), (
            f"indicators.py, linha {linha}: motivo que não é literal escapa ao contrato; "
            f"{MENSAGEM}"
        )
        if isinstance(segundo.value, str):
            motivos.append(segundo.value)
    return motivos


def test_market_cap_missing_pelos_literais_de_market_cap() -> None:
    assert _motivos_de_market_cap() == MARKET_CAP_MISSING, MENSAGEM


def test_market_cap_tem_sete_retornos_hoje() -> None:
    # seis motivos e o `return total, None`: o ramo do `None` e ignorado, nao some
    arvore = ast.parse(textwrap.dedent(inspect.getsource(market_cap)))
    retornos = [no for no in ast.walk(arvore) if isinstance(no, ast.Return)]
    assert len(retornos) == 7, MENSAGEM
