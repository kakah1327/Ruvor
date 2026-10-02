"""M3.3, T3: o estresse no esquema OpenAPI (RF-11; V-08).

`episode` e texto livre, sem enum: a lista de episodios muda por decisao nova, e as linhas
antigas guardam o codigo antigo. So `missing` e enum, anulavel, com os quatro motivos do
RF-03. Molde de `tests/accounts/test_esquema_openapi.py`, da `identidade`, que so e lido.
"""

from __future__ import annotations

from io import StringIO
from typing import Any

import pytest
from django.core.management import call_command
from drf_spectacular.drainage import GENERATOR_STATS
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

MOTIVOS = {"starts_after", "stale_start", "ends_before", "no_trading"}


def _esquema() -> dict[str, Any]:
    # a contagem de avisos do gerador e de classe e sobrevive entre testes
    GENERATOR_STATS.reset()
    call_command("spectacular", "--validate", "--fail-on-warn", stdout=StringIO())
    resposta = APIClient().get("/api/v1/schema")
    assert resposta.status_code == 200
    corpo: dict[str, Any] = resposta.json()
    return corpo


def _resolve(esquema: dict[str, Any], no: dict[str, Any]) -> dict[str, Any]:
    while "$ref" in no:
        no = esquema["components"]["schemas"][no["$ref"].rsplit("/", 1)[-1]]
    return no


def _item(esquema: dict[str, Any]) -> dict[str, Any]:
    """O componente do item de `metric.stress`, seguido pelos `$ref` desde a rota."""
    rota = esquema["paths"]["/api/v1/assets/{ticker}/metrics"]["get"]
    corpo = rota["responses"]["200"]["content"]["application/json"]["schema"]
    metric = _resolve(esquema, corpo)["properties"]["metric"]
    if "allOf" in metric:
        metric = metric["allOf"][0]
    if "oneOf" in metric:
        metric = next(o for o in metric["oneOf"] if "$ref" in o)
    stress = _resolve(esquema, metric)["properties"]["stress"]
    assert stress["type"] == "array"
    return _resolve(esquema, stress["items"])


def test_episode_e_texto_livre_sem_enum() -> None:
    episode = _item(_esquema())["properties"]["episode"]
    assert episode["type"] == "string"
    assert "enum" not in episode
    assert "$ref" not in episode
    assert "allOf" not in episode and "oneOf" not in episode


def test_missing_e_enum_anulavel_com_os_quatro_motivos() -> None:
    esquema = _esquema()
    missing = _item(esquema)["properties"]["missing"]
    # o drf-spectacular escreve o enum anulavel como `oneOf` do enum e do `NullEnum`
    opcoes = [_resolve(esquema, o) for o in missing.get("oneOf", [missing])]
    valores = {v for o in opcoes for v in o.get("enum", []) if v is not None}
    assert valores == MOTIVOS
    anulavel = missing.get("nullable") is True or any(
        o.get("enum") == [None] or None in o.get("enum", []) for o in opcoes
    )
    assert anulavel
