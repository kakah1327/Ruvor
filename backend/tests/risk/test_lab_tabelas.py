"""As tres tabelas do laboratorio (M2.4, RF-05 a RF-07): o V-06 (a imutabilidade e a restricao)
e o V-07 (a migration) do plano, Tarefa 2.

As linhas de teste nascem pelo `objects.create` de cada modelo, com valores quaisquer: o calculo
e a escrita de verdade sao da T3.

O erro do banco envenena a transacao do teste: cada `UPDATE` e `DELETE` por SQL cru, e cada
insercao que deve violar a restricao, roda dentro de `transaction.atomic()`, o ponto de
salvamento, para o comando seguinte no mesmo teste nao quebrar com `current transaction is
aborted` em vez de pelo motivo certo.

O V-07 migra para tras e para a frente, o que pede `transaction=True`: a marca `TRANSACIONAL` e a
fixture `banco_limpo` (`tests/api/migracao.py`), com um `finally` que reaplica a migration -- uma
falha no meio nao deixa o banco de teste sem as tabelas.
"""

from __future__ import annotations

import importlib
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.db import DatabaseError, IntegrityError, connection, models, transaction

from apps.assets.models import Asset, CollectionRun
from apps.risk import config
from apps.risk.models import LabResult, LabRun, LabYear
from tests.api.migracao import TRANSACIONAL, banco_limpo  # noqa: F401

DB = pytest.mark.django_db

AGORA = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)

COLUNAS_RUN = {
    "id": ("bigint", "NO"),
    "asset_id": ("bigint", "NO"),
    "calculated_at": ("timestamp with time zone", "NO"),
    "finished_at": ("timestamp with time zone", "NO"),
    "status": ("character varying", "NO"),
    "origin": ("character varying", "NO"),
    "engine_version": ("character varying", "NO"),
    "seed": ("integer", "NO"),
    "train_window_days": ("integer", "NO"),
    "library_versions": ("jsonb", "NO"),
    "library_versions_hash": ("character varying", "NO"),
    "first_price_date": ("date", "NO"),
    "decade_end": ("date", "NO"),
    "as_of_date": ("date", "NO"),
    "price_count": ("integer", "NO"),
    "train_count": ("integer", "NO"),
    "test_count": ("integer", "NO"),
    "year_count": ("integer", "NO"),
    "price_run_id": ("bigint", "NO"),
    "price_fingerprint": ("character varying", "NO"),
    "requested_models": ("jsonb", "NO"),
    "error": ("text", "NO"),
}

_TESTES = {
    "kupiec_passed": ("boolean", "YES"),
    "kupiec_p_value": ("numeric", "YES"),
    "christoffersen_passed": ("boolean", "YES"),
    "christoffersen_p_value": ("numeric", "YES"),
    "adequate": ("boolean", "YES"),
}

COLUNAS_RESULT = {
    "id": ("bigint", "NO"),
    "run_id": ("bigint", "NO"),
    "model_name": ("character varying", "NO"),
    "model_category": ("character varying", "NO"),
    "alpha": ("numeric", "NO"),
    "hyperparameters": ("jsonb", "NO"),
    "test_count": ("integer", "YES"),
    "violations": ("integer", "YES"),
    "expected_violations": ("numeric", "YES"),
    **_TESTES,
    "dq_passed": ("boolean", "YES"),
    "dq_p_value": ("numeric", "YES"),
    "error": ("text", "NO"),
    "reused_snapshots": ("integer", "YES"),
    "trained_snapshots": ("integer", "YES"),
}

COLUNAS_YEAR = {
    "id": ("bigint", "NO"),
    "result_id": ("bigint", "NO"),
    "index": ("integer", "NO"),
    "start_date": ("date", "NO"),
    "end_date": ("date", "NO"),
    "test_count": ("integer", "NO"),
    "violations": ("integer", "NO"),
    "expected_violations": ("numeric", "NO"),
    **_TESTES,
}

TABELAS = ("lab_run", "lab_result", "lab_year")
GATILHOS = ("lab_result_so_cresce", "lab_run_so_cresce", "lab_year_so_cresce")


# --- as linhas de teste -------------------------------------------------------------------


def _ativo(ticker: str = "LABS3") -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=Asset.Status.ACTIVE,
        provider_symbol=f"{ticker}.SA",
        created_at=AGORA,
        updated_at=AGORA,
    )


_SEQUENCIA = iter(range(1, 10_000))


def _run(
    asset: Asset,
    status: str = LabRun.Status.OK,
    *,
    engine_version: str = "0.4.0",
    first_price_date: date = date(2016, 9, 22),
) -> LabRun:
    coleta = CollectionRun.objects.create(source="teste", started_at=AGORA)
    instante = AGORA + timedelta(minutes=next(_SEQUENCIA))
    return LabRun.objects.create(
        asset=asset,
        calculated_at=instante,
        finished_at=instante + timedelta(seconds=5),
        status=status,
        origin=LabRun.Origin.COMMAND,
        engine_version=engine_version,
        seed=config.DEFAULT_SEED,
        train_window_days=config.TRAIN_WINDOW_DAYS,
        library_versions={"numpy": "2.0.0"},
        library_versions_hash="a" * 64,
        first_price_date=first_price_date,
        decade_end=date(first_price_date.year + 10, 9, 22),
        as_of_date=date(2026, 9, 22),
        price_count=2480,
        train_count=252,
        test_count=2227,
        year_count=9,
        price_run=coleta,
        price_fingerprint="b" * 64,
        requested_models=["historical"],
    )


def _result(run: LabRun) -> LabResult:
    return LabResult.objects.create(
        run=run,
        model_name="historical",
        model_category="traditional",
        alpha=Decimal("0.0500"),
        hyperparameters={},
        test_count=2227,
        violations=110,
        expected_violations=Decimal("111.350000"),
        kupiec_passed=True,
        kupiec_p_value=Decimal("0.8900000000"),
        christoffersen_passed=True,
        christoffersen_p_value=Decimal("0.5000000000"),
        dq_passed=True,
        dq_p_value=Decimal("0.3000000000"),
        adequate=True,
    )


def _year(result: LabResult) -> LabYear:
    return LabYear.objects.create(
        result=result,
        index=0,
        start_date=date(2017, 9, 25),
        end_date=date(2018, 9, 24),
        test_count=252,
        violations=12,
        expected_violations=Decimal("12.600000"),
        kupiec_passed=True,
        kupiec_p_value=Decimal("0.8600000000"),
        christoffersen_passed=True,
        christoffersen_p_value=Decimal("0.4000000000"),
        adequate=True,
    )


@pytest.fixture
def linhas() -> tuple[LabRun, LabResult, LabYear]:
    run = _run(_ativo())
    result = _result(run)
    return run, result, _year(result)


def _por_tabela(
    linhas: tuple[LabRun, LabResult, LabYear],
) -> list[tuple[str, type[models.Model], models.Model]]:
    run, result, year = linhas
    return [
        ("lab_run", LabRun, run),
        ("lab_result", LabResult, result),
        ("lab_year", LabYear, year),
    ]


# --- RF-05: as colunas, o esquema, os nomes ----------------------------------------------


@DB
@pytest.mark.parametrize(
    ("tabela", "esperado"),
    [
        ("lab_run", COLUNAS_RUN),
        ("lab_result", COLUNAS_RESULT),
        ("lab_year", COLUNAS_YEAR),
    ],
)
def test_as_colunas_de_cada_tabela(
    tabela: str, esperado: dict[str, tuple[str, str]]
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name, data_type, is_nullable FROM information_schema.columns"
            " WHERE table_schema = 'gold' AND table_name = %s",
            [tabela],
        )
        linhas = cursor.fetchall()
    assert {nome: (tipo, nula) for nome, tipo, nula in linhas} == esperado


@DB
def test_status_e_origin_sem_default() -> None:
    for nome in ("status", "origin"):
        campo = LabRun._meta.get_field(nome)
        assert isinstance(campo, models.CharField)
        assert not campo.has_default(), nome
    assert set(LabRun.Status.values) == {"ok", "partial", "failed"}
    assert set(LabRun.Origin.values) == {"risk_close", "command"}


@DB
@pytest.mark.parametrize(
    ("modelo", "campo", "alvo"),
    [
        (LabRun, "asset", "assets.Asset"),
        (LabRun, "price_run", "assets.CollectionRun"),
        (LabResult, "run", "risk.LabRun"),
        (LabYear, "result", "risk.LabResult"),
    ],
)
def test_as_chaves_estrangeiras_sao_protect(
    modelo: type[models.Model], campo: str, alvo: str
) -> None:
    fk = modelo._meta.get_field(campo)
    assert fk.remote_field is not None
    assert getattr(fk.remote_field, "on_delete", None) is models.PROTECT
    assert fk.related_model is not None
    assert fk.related_model._meta.label == alvo


@DB
def test_o_indice_por_ativo_e_instante_decrescente() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexdef FROM pg_indexes"
            " WHERE schemaname = 'gold' AND indexname = 'lab_run_asset_recent'"
        )
        linhas = cursor.fetchall()
    assert len(linhas) == 1
    assert "(asset_id, calculated_at DESC)" in linhas[0][0]


@DB
def test_as_restricoes_unicas_e_os_nomes_curtos() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'gold'"
            " AND indexname IN ('lab_run_identity_ok', 'lab_result_run_model_alpha',"
            " 'lab_year_result_index')"
        )
        definicoes = dict(cursor.fetchall())
    assert set(definicoes) == {
        "lab_run_identity_ok",
        "lab_result_run_model_alpha",
        "lab_year_result_index",
    }
    assert all(len(nome) <= 30 for nome in definicoes)
    identidade = definicoes["lab_run_identity_ok"]
    assert identidade.startswith("CREATE UNIQUE INDEX")
    assert (
        "(asset_id, engine_version, seed, train_window_days, first_price_date,"
        " decade_end, library_versions_hash)"
    ) in identidade
    assert "WHERE ((status)::text = 'ok'::text)" in identidade
    assert "(run_id, model_name, alpha)" in definicoes["lab_result_run_model_alpha"]
    assert "(result_id, index)" in definicoes["lab_year_result_index"]


def test_as_constantes_do_laboratorio() -> None:
    assert config.LAB_YEAR_DAYS == 252
    assert config.LAB_YEAR_MIN_JUDGED == 126
    assert config.LAB_JUDGED_ALPHAS == (0.05,)
    assert config.LAB_JUDGED_ALPHAS[0] in config.ALPHAS


# --- V-06: imutavel no Django -------------------------------------------------------------


@DB
def test_save_de_linha_existente_levanta_nas_tres(
    linhas: tuple[LabRun, LabResult, LabYear],
) -> None:
    run, result, year = linhas
    run.error = "x"
    result.error = "x"
    year.violations = 99
    for linha in (run, result, year):
        with pytest.raises(TypeError, match="lab so cresce"):
            linha.save()
    assert LabRun.objects.get(pk=run.pk).error == ""
    assert LabResult.objects.get(pk=result.pk).error == ""
    assert LabYear.objects.get(pk=year.pk).violations == 12


@DB
def test_delete_da_instancia_levanta_nas_tres(
    linhas: tuple[LabRun, LabResult, LabYear],
) -> None:
    for _, modelo, linha in _por_tabela(linhas):
        with pytest.raises(TypeError, match="lab so cresce"):
            linha.delete()
        assert modelo._default_manager.filter(pk=linha.pk).exists()


@DB
def test_update_e_delete_do_queryset_levantam_nas_tres(
    linhas: tuple[LabRun, LabResult, LabYear],
) -> None:
    for _, modelo, linha in _por_tabela(linhas):
        gerentes = [modelo._default_manager, modelo._base_manager]
        assert all(g.all().__class__.__name__ == "LabQuerySet" for g in gerentes)
        for gerente in gerentes:
            with pytest.raises(TypeError, match="lab so cresce"):
                gerente.all().update(pk=linha.pk)
            with pytest.raises(TypeError, match="lab so cresce"):
                gerente.filter(pk=linha.pk).delete()
            with pytest.raises(TypeError, match="lab so cresce"):
                gerente.update(pk=linha.pk)
        assert modelo._default_manager.filter(pk=linha.pk).exists()


@DB
def test_update_e_delete_pelo_acessor_reverso_levantam(
    linhas: tuple[LabRun, LabResult, LabYear],
) -> None:
    run, result, _ = linhas
    for consulta in (run.asset.lab_runs.all(), run.results.all(), result.years.all()):
        with pytest.raises(TypeError, match="lab so cresce"):
            consulta.delete()
        with pytest.raises(TypeError, match="lab so cresce"):
            consulta.update(id=0)
    assert LabYear.objects.count() == 1


@DB
def test_o_insert_continua_valendo(linhas: tuple[LabRun, LabResult, LabYear]) -> None:
    run, result, year = linhas
    assert (
        LabRun.objects.count(),
        LabResult.objects.count(),
        LabYear.objects.count(),
    ) == (
        1,
        1,
        1,
    )
    assert year.result_id == result.pk and result.run_id == run.pk


# --- V-06: imutavel no banco --------------------------------------------------------------


@DB
@pytest.mark.parametrize("tabela", TABELAS)
@pytest.mark.parametrize(
    "sql",
    ["UPDATE gold.{t} SET id = id WHERE id = %s", "DELETE FROM gold.{t} WHERE id = %s"],
)
def test_update_e_delete_crus_sao_recusados_nas_tres(
    linhas: tuple[LabRun, LabResult, LabYear], tabela: str, sql: str
) -> None:
    linha = {t: obj for t, _, obj in _por_tabela(linhas)}[tabela]
    with (
        pytest.raises(DatabaseError, match="lab so cresce"),
        transaction.atomic(),
        connection.cursor() as cursor,
    ):
        cursor.execute(sql.format(t=tabela), [linha.pk])
    assert type(linha)._default_manager.filter(pk=linha.pk).exists()


@DB
def test_os_tres_gatilhos_existem_uma_vez_cada() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT t.tgname, c.relname FROM pg_trigger t"
            " JOIN pg_class c ON c.oid = t.tgrelid"
            " WHERE t.tgname LIKE 'lab_%%_so_cresce' ORDER BY t.tgname"
        )
        assert cursor.fetchall() == [
            ("lab_result_so_cresce", "lab_result"),
            ("lab_run_so_cresce", "lab_run"),
            ("lab_year_so_cresce", "lab_year"),
        ]


@DB
def test_o_truncate_passa(linhas: tuple[LabRun, LabResult, LabYear]) -> None:
    with connection.cursor() as cursor:
        # As FKs do Django sao `DEFERRABLE INITIALLY DEFERRED`: a insercao, na mesma transacao
        # do teste, deixa a checagem pendente, e o PostgreSQL recusaria o `TRUNCATE` com
        # "pending trigger events" -- nao pelo gatilho. As checagens rodam antes.
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("TRUNCATE gold.lab_year, gold.lab_result, gold.lab_run")
    assert (
        LabRun.objects.count(),
        LabResult.objects.count(),
        LabYear.objects.count(),
    ) == (
        0,
        0,
        0,
    )


# --- RF-07: um `ok` por identidade --------------------------------------------------------


@DB
def test_segundo_ok_da_mesma_identidade_e_integrity_error() -> None:
    asset = _ativo()
    _run(asset, LabRun.Status.OK)
    with pytest.raises(IntegrityError), transaction.atomic():
        _run(asset, LabRun.Status.OK)
    assert LabRun.objects.filter(status="ok").count() == 1


@DB
@pytest.mark.parametrize(
    ("primeiro", "segundo"),
    [
        (LabRun.Status.FAILED, LabRun.Status.OK),
        (LabRun.Status.PARTIAL, LabRun.Status.OK),
        (LabRun.Status.PARTIAL, LabRun.Status.PARTIAL),
        (LabRun.Status.FAILED, LabRun.Status.FAILED),
        (LabRun.Status.OK, LabRun.Status.PARTIAL),
        (LabRun.Status.OK, LabRun.Status.FAILED),
    ],
)
def test_partial_e_failed_nao_entram_na_restricao(primeiro: str, segundo: str) -> None:
    asset = _ativo()
    _run(asset, primeiro)
    _run(asset, segundo)
    assert LabRun.objects.filter(asset=asset).count() == 2


@DB
def test_ok_com_outra_versao_do_motor_passa() -> None:
    asset = _ativo()
    _run(asset, LabRun.Status.OK, engine_version="0.4.0")
    _run(asset, LabRun.Status.OK, engine_version="0.5.0")
    assert LabRun.objects.filter(asset=asset, status="ok").count() == 2


@DB
def test_ok_de_outra_decada_ou_de_outro_ativo_passa() -> None:
    asset = _ativo()
    _run(asset, LabRun.Status.OK)
    _run(asset, LabRun.Status.OK, first_price_date=date(2017, 9, 22))
    _run(_ativo("OUTR3"), LabRun.Status.OK)
    assert LabRun.objects.filter(status="ok").count() == 3


@DB
def test_resultado_e_ano_duplicados_sao_integrity_error(
    linhas: tuple[LabRun, LabResult, LabYear],
) -> None:
    run, result, _ = linhas
    with pytest.raises(IntegrityError), transaction.atomic():
        _result(run)
    with pytest.raises(IntegrityError), transaction.atomic():
        _year(result)


# --- V-07: a migration vai e volta ---------------------------------------------------------


def _tabelas_do_lab() -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'gold'"
            " AND tablename LIKE 'lab\\_%%'"
        )
        return {linha[0] for linha in cursor.fetchall()}


def _funcao_existe() -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace"
            " WHERE n.nspname = 'gold' AND p.proname = 'lab_so_cresce'"
        )
        return cursor.fetchone() is not None


def _gatilhos() -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tgname FROM pg_trigger WHERE tgname LIKE 'lab_%%_so_cresce'"
            " ORDER BY tgname"
        )
        return [linha[0] for linha in cursor.fetchall()]


def test_a_0004_depende_da_assets_0003_e_nao_da_0004() -> None:
    """O `migrate assets 0003` de `tests/assets/test_unaccent.py` nao pode desfazer a `risk.0004`."""
    modulo = importlib.import_module("apps.risk.migrations.0004_gold_lab")
    assert set(modulo.Migration.dependencies) == {
        ("assets", "0003_yahoo_chart_price_corporate_event"),
        ("risk", "0003_model_snapshot"),
    }


@TRANSACIONAL
@pytest.mark.usefixtures("banco_limpo")
def test_v07_a_volta_remove_e_a_ida_recria_tabelas_funcao_e_gatilhos() -> None:
    assert _tabelas_do_lab() == set(TABELAS)
    assert _funcao_existe()
    assert _gatilhos() == list(GATILHOS)
    try:
        call_command("migrate", "risk", "0003", verbosity=0)
        assert _tabelas_do_lab() == set()
        assert not _funcao_existe()
        assert _gatilhos() == []

        call_command("migrate", "risk", verbosity=0)
        assert _tabelas_do_lab() == set(TABELAS)
        assert _funcao_existe()
        assert _gatilhos() == list(GATILHOS)
    finally:
        call_command("migrate", "risk", verbosity=0)
