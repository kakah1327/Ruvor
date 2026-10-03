"""Recaptura a linha de base numerica nas dez entradas que o M1.4b muda (RF-11, D-159).

Uso, no hospedeiro Windows, com o `.venv` importando o motor do codigo a capturar:

    .venv/Scripts/python.exe engine/tests/baseline/capturar.py <saida.json>

O script roda os seis modelos nos dois niveis pelo mesmo caminho de
`test_linha_de_base.py` (a funcao `_resultado` dele, importada, sobre a serie de
`conftest.py`) e compara cada entrada com o "antes", que e o `valores.json` de
`origin/main` (`git show`) -- nunca o arquivo de saida. Termina com erro, sem gravar
nada, se alguma das dez entradas recapturadas sair igual a de `origin/main` (a captura
com o codigo velho regravaria os numeros velhos -- o V-05) ou se alguma do `caviar`
mudar. Ao gravar, so as dez entradas sao trocadas; `parametros`, a ordem e as entradas
do `caviar` saem byte a byte como em `origin/main`.

"Igual" e "mudou" usam a mesma tolerancia do teste (`_proximo`).

Serve a recaptura do M1.4b: o "antes" e `origin/main` e a lista dos cinco modelos esta no
codigo. Depois da mesclagem, rodar de novo sempre recusa (as dez sairiam iguais); uma
recaptura futura, por outra mudanca de calculo decidida, edita o script.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DIR_BASELINE = Path(__file__).resolve().parent
DIR_TESTES = DIR_BASELINE.parent
RAIZ_DO_REPOSITORIO = DIR_TESTES.parent.parent

# `test_linha_de_base.py` importa `conftest` de `engine/tests`; o pytest poe esse
# diretorio no caminho, o script poe a mao.
for _dir in (DIR_TESTES, DIR_BASELINE):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

from test_linha_de_base import _proximo, _resultado  # noqa: E402

import engine  # noqa: E402

MODELOS_RECAPTURADOS = {
    "parametric",
    "historical",
    "monte_carlo",
    "garch_1_1",
    "egarch",
}
MODELO_INTOCADO = "caviar"
CAMINHO_NO_GIT = "origin/main:engine/tests/baseline/valores.json"


def _antes() -> dict:
    """O `valores.json` de `origin/main`, lido pelo `git show`."""
    texto = subprocess.run(
        ["git", "-C", str(RAIZ_DO_REPOSITORIO), "show", CAMINHO_NO_GIT],
        check=True,
        capture_output=True,
        encoding="utf-8",
    ).stdout
    return json.loads(texto)


def _entrada_nova(modelo: str, alpha: float) -> dict:
    """A entrada no formato de `valores.json`, pelo caminho do teste."""
    var_series, backtests = _resultado(modelo, alpha)
    return {
        "modelo": modelo,
        "alpha": alpha,
        "var": [float(v) for v in var_series.tolist()],
        "backtests": {
            nome: {
                "statistic": float(r.statistic),
                "p_value": None if r.p_value is None else float(r.p_value),
                "passed": bool(r.passed),
            }
            for nome, r in backtests.items()
        },
    }


def _iguais(nova: dict, antiga: dict) -> bool:
    """Igualdade pela tolerancia do teste: a serie de VaR e os quatro backtests."""
    if (nova["modelo"], nova["alpha"]) != (antiga["modelo"], antiga["alpha"]):
        return False
    if len(nova["var"]) != len(antiga["var"]):
        return False
    if not all(_proximo(o, e) for o, e in zip(nova["var"], antiga["var"])):
        return False
    if sorted(nova["backtests"]) != sorted(antiga["backtests"]):
        return False
    for nome, ref in antiga["backtests"].items():
        obtido = nova["backtests"][nome]
        if not _proximo(obtido["statistic"], ref["statistic"]):
            return False
        if (obtido["p_value"] is None) != (ref["p_value"] is None):
            return False
        if ref["p_value"] is not None and not _proximo(
            obtido["p_value"], ref["p_value"]
        ):
            return False
        if obtido["passed"] != ref["passed"]:
            return False
    return True


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"uso: {argv[0]} <caminho de saida do valores.json>", file=sys.stderr)
        return 2
    saida = Path(argv[1])

    print(f"engine.__file__ = {engine.__file__}")
    antes = _antes()
    entradas_antes = antes["entradas"]

    modelos_antes = {e["modelo"] for e in entradas_antes.values()}
    if modelos_antes != MODELOS_RECAPTURADOS | {MODELO_INTOCADO}:
        print(f"ERRO: modelos inesperados em origin/main: {sorted(modelos_antes)}")
        return 1

    novas: dict[str, dict] = {}
    erros: list[str] = []
    for chave, antiga in entradas_antes.items():
        nova = _entrada_nova(antiga["modelo"], antiga["alpha"])
        mudou = not _iguais(nova, antiga)
        print(f"{chave}: {'MUDOU' if mudou else 'igual'}")
        if antiga["modelo"] == MODELO_INTOCADO:
            if mudou:
                erros.append(f"{chave} mudou, e o caviar nao pode mudar")
        else:
            if not mudou:
                erros.append(
                    f"{chave} saiu igual a de origin/main: o motor que rodou e o velho?"
                )
            novas[chave] = nova

    if erros:
        print("ERRO: nada gravado.")
        for erro in erros:
            print(f"  - {erro}")
        return 1

    depois = dict(antes)
    depois["entradas"] = {
        chave: novas.get(chave, antiga) for chave, antiga in entradas_antes.items()
    }
    saida.write_bytes((json.dumps(depois, indent=2) + "\n").encode("utf-8"))
    print(f"gravado: {saida} ({len(novas)} entradas recapturadas)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
