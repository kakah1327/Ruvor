"""O estado da execucao: a regra do fecho, a copia dela na migration, e o V-10c.

O V-10c nao usa `MigrationExecutor`: migrar para tras e para a frente dentro do teste nao
funciona neste repositorio (o `flush` do `transaction=True` nao restaura a organizacao
`ruvor` para os testes que rodam depois, e sem ele a FK adiavel da `pending trigger
events` ao alterar a tabela). Por isso ele se divide em tres partes:

- **(a) a funcao**: o `backfill` da `0002`, chamado com o registro de apps corrente sobre
  execucoes gravadas com `status` e `requested_models` sujos;
- **(b) a forma**: a lista `operations` da `0002` roda o `backfill` depois dos dois
  `AddField` -- e o que pega a migration sem o `RunPython`, em que o valor do `AddField`
  valeria para todo mundo;
- **(c) o dado real**: as oito linhas do banco, medidas na execucao real.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from types import ModuleType

import pytest
from django.apps import apps as django_apps
from django.db import migrations

from apps.assets.models import Asset, CollectionRun
from apps.risk.compute import MODELS, status_for
from apps.risk.models import RiskResult, RiskRun

MIGRATION = "apps.risk.migrations.0002_risk_run_status_e_modelos"

INICIO = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def migration_module() -> ModuleType:
    return importlib.import_module(MIGRATION)


# --- a regra do fecho, e a copia dela na migration ----------------------------------------

CASOS = [
    ((18, 18, 0), "ok"),
    ((18, 18, 18), "failed"),
    ((18, 0, 0), "failed"),
    ((18, 12, 0), "partial"),
    ((18, 18, 2), "partial"),
    ((2, 2, 0), "ok"),
]


def _regras() -> list[tuple[str, Callable[[int, int, int], str]]]:
    return [
        ("compute", status_for),
        ("migration", migration_module().status_for),
    ]


@pytest.mark.parametrize(("argumentos", "esperado"), CASOS)
@pytest.mark.parametrize("origem", ["compute", "migration"])
def test_a_regra_do_fecho_e_a_copia_dela_dao_o_mesmo(
    origem: str, argumentos: tuple[int, int, int], esperado: str
) -> None:
    regra = dict(_regras())[origem]
    assert regra(*argumentos) == esperado


def test_a_lista_da_migration_e_a_de_compute() -> None:
    """A `0002` copia os nove porque nao pode importar o motor; a copia nao envelhece."""
    assert migration_module().MODELS == list(MODELS)


# --- V-10c (a): o backfill deriva do dado --------------------------------------------------


def _ativo(ticker: str) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=INICIO,
        updated_at=INICIO,
    )


def _execucao_suja(ticker: str, coleta: CollectionRun, modelos: list[str]) -> RiskRun:
    """Uma execucao com o estado sujo -- `running` e `[]` -- e dois resultados limpos por
    modelo, gravados na ordem **inversa** da pedida: a ordem de `MODELS` tem de vir do
    `backfill`, nao da ordem de insercao."""
    run = RiskRun.objects.create(
        asset=_ativo(ticker),
        calculated_at=INICIO,
        finished_at=INICIO,
        engine_version="0.2.0",
        seed=42,
        train_window_days=252,
        as_of_date=date(2026, 9, 18),
        first_price_date=date(2024, 9, 18),
        price_count=503,
        train_count=252,
        test_count=250,
        price_run=coleta,
        requested_by=None,
        status=RiskRun.Status.RUNNING,
        requested_models=[],
    )
    RiskResult.objects.bulk_create(
        [
            RiskResult(
                run=run,
                model_name=modelo,
                model_category="traditional",
                alpha=Decimal(alpha),
                hyperparameters={},
            )
            for modelo in reversed(modelos)
            for alpha in ("0.0500", "0.0100")
        ]
    )
    return run


@pytest.mark.django_db
def test_v10c_a_o_backfill_deriva_estado_e_modelos_de_cada_execucao() -> None:
    coleta = CollectionRun.objects.create(source="teste", started_at=INICIO)
    completa = _execucao_suja("AAA3", coleta, list(MODELS))
    so_garch = _execucao_suja("BBB3", coleta, ["garch_1_1"])

    migration_module().backfill(django_apps, None)

    completa.refresh_from_db()
    so_garch.refresh_from_db()
    assert (completa.status, completa.requested_models) == ("ok", list(MODELS))
    assert (so_garch.status, so_garch.requested_models) == ("ok", ["garch_1_1"])


# --- V-10c (b): a migration roda o backfill -----------------------------------------------


def test_v10c_b_a_migration_adiciona_as_duas_colunas_e_roda_o_backfill() -> None:
    modulo = migration_module()
    operacoes = modulo.Migration.operations

    assert [type(op) for op in operacoes] == [
        migrations.AddField,
        migrations.AddField,
        migrations.RunPython,
    ]
    status, modelos, backfill = operacoes
    assert (status.model_name, status.name) == ("riskrun", "status")
    assert (modelos.model_name, modelos.name) == ("riskrun", "requested_models")
    assert backfill.code is modulo.backfill
