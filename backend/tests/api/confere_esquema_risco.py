"""Confere, no esquema OpenAPI gerado, o 401 e o 403 do `POST /risk` (M2.1b, V-03).

Script, nao teste: o nome nao comeca por `test_`, e o pytest nao o coleta. A T2 do plano o
chama depois do `manage.py spectacular --validate --fail-on-warn --file <arquivo>`:

    python tests/api/confere_esquema_risco.py /tmp/schema.yaml

Sai 0 se as respostas do `post` de `/api/v1/assets/{ticker}/risk` tiverem `401` e `403`; 1,
com o que faltou, se nao. Por ser um arquivo, nenhuma aspa passa pelo `sh -c`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

CAMINHO = "/api/v1/assets/{ticker}/risk"
EXIGIDAS = ("401", "403")


def faltam(esquema: dict[str, Any]) -> list[str]:
    """As respostas exigidas que o `post` do `/risk` nao declara."""
    respostas = esquema["paths"][CAMINHO]["post"]["responses"]
    declaradas = {str(codigo) for codigo in respostas}
    return [codigo for codigo in EXIGIDAS if codigo not in declaradas]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"uso: {argv[0]} <schema.yaml>", file=sys.stderr)
        return 2
    esquema = yaml.safe_load(Path(argv[1]).read_text(encoding="utf-8"))
    ausentes = faltam(esquema)
    if ausentes:
        print(
            f"o post de {CAMINHO} nao declara: {', '.join(ausentes)}", file=sys.stderr
        )
        return 1
    print(f"o post de {CAMINHO} declara {', '.join(EXIGIDAS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
