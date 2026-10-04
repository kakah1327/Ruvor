"""M5.1, T3 — V-07: as duas tabelas do retorno em `gold`, a migration e o que ela depende.

As colunas, os tipos e a nulabilidade sao conferidos contra o RF-10 no `information_schema`
(a DDL prova o que o banco garante sozinho; a `CASCADE` e o `PROTECT` sao do ORM). A volta
`migrate returns zero` remove as duas tabelas, e a ida as recria; o `makemigrations --check`
sai limpo.

**A dependencia da `returns.0001` e a `assets.0003`, nao a `assets.0004_unaccent`** (o achado
do M2.4): o `tests/assets/test_unaccent.py` faz `migrate assets 0003` e volta so pela
`assets`; uma migration que dependesse da `0004` seria desfeita e nao reaplicada, e as duas
tabelas sumiriam do banco de teste para o resto da suite.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection

from tests.api.migracao import TRANSACIONAL, banco_limpo  # noqa: F401

APP = Path(__file__).resolve().parents[2] / "apps" / "returns"

N18 = ("numeric", 18, 10)

#: (tipo, nulo) por coluna, literal do RF-10; FKs pela coluna `_id`
RETURN_RUN = {
    "id": ("bigint", False),
    "asset_id": ("bigint", False),
    "calculated_at": ("timestamp with time zone", False),
    "finished_at": ("timestamp with time zone", False),
    "engine_version": ("character varying", False),
    "train_window_days": ("integer", False),
    "as_of_date": ("date", False),
    "first_price_date": ("date", False),
    "price_count": ("integer", False),
    "train_count": ("integer", False),
    "test_count": ("integer", False),
    "price_run_id": ("bigint", False),
    "requested_by_id": ("bigint", True),
}

RETURN_RESULT = {
    "id": ("bigint", False),
    "run_id": ("bigint", False),
    "model_name": ("character varying", False),
    "hyperparameters": ("jsonb", False),
    "mse": (N18, True),
    "mse_reference": (N18, True),
    "r2_os": (N18, True),
    "direction_days": ("integer", True),
    "hit_rate": (N18, True),
    "up_share": (N18, True),
    "forecast_up_share": (N18, True),
    "dm_statistic": (N18, True),
    "dm_p_value": (N18, True),
    "cw_statistic": (N18, True),
    "cw_p_value": (N18, True),
    "pt_statistic": (N18, True),
    "pt_p_value": (N18, True),
    "beats_reference": ("boolean", True),
    "direction_skill": ("boolean", True),
    "next_forecast": (N18, True),
    "next_forecast_date": ("date", True),
    "error": ("text", False),
}


def _colunas(tabela: str) -> dict[str, tuple[object, bool]]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name, data_type, numeric_precision, numeric_scale, is_nullable"
            " FROM information_schema.columns"
            " WHERE table_schema = 'gold' AND table_name = %s",
            [tabela],
        )
        linhas = cursor.fetchall()
    return {
        nome: (
            (tipo, precisao, escala) if tipo == "numeric" else tipo,
            nulo == "YES",
        )
        for nome, tipo, precisao, escala, nulo in linhas
    }


def _tabelas_do_retorno() -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT schemaname || '.' || tablename FROM pg_tables"
            " WHERE tablename IN ('return_run', 'return_result')"
        )
        return {linha[0] for linha in cursor.fetchall()}


def _restricoes(tabela: str) -> set[tuple[str, str]]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT c.conname, pg_get_constraintdef(c.oid) FROM pg_constraint c"
            " JOIN pg_class t ON t.oid = c.conrelid"
            " JOIN pg_namespace n ON n.oid = t.relnamespace"
            " WHERE n.nspname = 'gold' AND t.relname = %s AND c.contype = 'u'",
            [tabela],
        )
        return set(cursor.fetchall())


@pytest.mark.django_db
def test_return_run_tem_as_colunas_do_rf10() -> None:
    assert _colunas("return_run") == RETURN_RUN


@pytest.mark.django_db
def test_return_result_tem_as_colunas_do_rf10() -> None:
    assert _colunas("return_result") == RETURN_RESULT


@pytest.mark.django_db
def test_as_unicidades_do_rf10() -> None:
    assert _restricoes("return_run") == {
        ("return_run_asset_calculated_at", "UNIQUE (asset_id, calculated_at)")
    }
    assert _restricoes("return_result") == {
        ("return_result_run_model", "UNIQUE (run_id, model_name)")
    }


def test_a_0001_depende_da_assets_0003_e_nao_da_0004() -> None:
    """O `migrate assets 0003` de `tests/assets/test_unaccent.py` nao pode desfazer a
    `returns.0001`."""
    modulo = importlib.import_module("apps.returns.migrations.0001_gold_return_run")
    assert {tuple(d) for d in modulo.Migration.dependencies} == {
        ("assets", "0003_yahoo_chart_price_corporate_event"),
        ("accounts", "__first__"),
    }


def test_models_nao_importa_o_motor() -> None:
    arvore = ast.parse((APP / "models.py").read_text(encoding="utf-8"))
    importados: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(alias.name.split(".")[0] for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module is not None:
            importados.add(no.module.split(".")[0])
    assert "engine" not in importados


def test_nenhum_caminho_da_app_altera_ou_apaga_linha() -> None:
    """D-16: so `create`. Nenhuma chamada a `update`, `delete`, `save` de instancia
    existente ou `bulk_update` nos modulos da app."""
    proibidos = {"update", "delete", "bulk_update", "update_or_create", "get_or_create"}
    achados = []
    for arquivo in APP.rglob("*.py"):
        if "migrations" in arquivo.parts:
            continue
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if (
                isinstance(no, ast.Call)
                and isinstance(no.func, ast.Attribute)
                and no.func.attr in proibidos
            ):
                achados.append(f"{arquivo.name}:{no.lineno} {no.func.attr}")
    assert achados == []


@pytest.mark.django_db
def test_makemigrations_check_sai_limpo() -> None:
    call_command("makemigrations", "returns", "--check", "--dry-run", verbosity=0)


@TRANSACIONAL
@pytest.mark.usefixtures("banco_limpo")
def test_v07_a_volta_remove_e_a_ida_recria_as_duas_tabelas() -> None:
    assert _tabelas_do_retorno() == {"gold.return_run", "gold.return_result"}
    try:
        call_command("migrate", "returns", "zero", verbosity=0)
        assert _tabelas_do_retorno() == set()

        call_command("migrate", "returns", verbosity=0)
        assert _tabelas_do_retorno() == {"gold.return_run", "gold.return_result"}
    finally:
        call_command("migrate", "returns", verbosity=0)
