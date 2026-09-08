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
