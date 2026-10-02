"""M2.2a, T5: a unica saida sem escopo da carteira (RF-18; V-10, a parte desta tarefa).

O teto global conta execucoes de todas as organizacoes, o que o gerente com escopo nao faz por
construcao. Por isso `apps/portfolios/services.py` esta na lista fechada `CHAMADORES_DE_UNSCOPED`
de `tests/accounts/test_tenancy.py` -- e aqui se prova que, dentro dele, `.unscoped` so aparece no
corpo de `count_running_everywhere`, que devolve um inteiro e nenhuma linha.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.accounts.test_tenancy import CHAMADORES_DE_UNSCOPED, _chamadores_de_unscoped

SERVICES = Path(__file__).resolve().parents[2] / "apps" / "portfolios" / "services.py"
SAIDAS = {"unscoped", "_base_manager"}


def _funcoes_com_saida() -> dict[str, ast.FunctionDef]:
    arvore = ast.parse(SERVICES.read_text(encoding="utf-8"))
    achadas: dict[str, ast.FunctionDef] = {}
    fora_de_funcao = False
    for no in arvore.body:
        tem = any(
            isinstance(n, ast.Attribute) and n.attr in SAIDAS for n in ast.walk(no)
        )
        if not tem:
            continue
        if isinstance(no, ast.FunctionDef):
            achadas[no.name] = no
        else:
            fora_de_funcao = True
    assert not fora_de_funcao, "saida sem escopo fora de funcao em services.py"
    return achadas


def test_v10_unscoped_so_em_count_running_everywhere() -> None:
    achadas = _funcoes_com_saida()
    assert set(achadas) == {"count_running_everywhere"}
    funcao = achadas["count_running_everywhere"]
    assert isinstance(funcao.returns, ast.Name)
    assert funcao.returns.id == "int"


def test_v10_a_varredura_do_tenancy_acha_e_aceita_o_arquivo() -> None:
    assert "portfolios/services.py" in _chamadores_de_unscoped()
    assert "portfolios/services.py" in CHAMADORES_DE_UNSCOPED
