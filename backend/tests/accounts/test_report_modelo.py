"""M4.1, T1: a tabela `core.report`, imutavel no Django e no banco (RF-01, RF-02; V-01 a V-03).

O relatorio de teste nasce por `Report.objects.create` sob `organization_scope`, com um conteudo
qualquer: o conteudo de verdade e da T2, e o servico que o gera, da T3.

O erro do banco envenena a transacao do teste: cada `UPDATE` e `DELETE` por SQL cru roda dentro de
`transaction.atomic()`, o ponto de salvamento, para o comando seguinte no mesmo teste nao quebrar
com `current transaction is aborted` em vez de pelo motivo certo.
"""

from __future__ import annotations

import hashlib
from datetime import timedelta

import pytest
from django.db import DatabaseError, IntegrityError, connection, models, transaction
from django.db.models import ProtectedError
from django.utils import timezone

from apps.accounts.models import Organization, Report, User
from apps.accounts.tenancy import organization_scope
from apps.risk.models import RiskRun
from tests.accounts.conftest import organizacao, usuario
from tests.accounts.risco_de_teste import ativo, execucao_completa

pytestmark = pytest.mark.django_db

COLUNAS = {
    "id": "bigint",
    "public_id": "uuid",
    "organization_id": "bigint",
    "requested_by_id": "bigint",
    "created_at": "timestamp with time zone",
    "kind": "character varying",
    "format_version": "integer",
    "asset_id": "bigint",
    "risk_run_id": "bigint",
    "content": "bytea",
    "sha256": "character varying",
    "size_bytes": "integer",
}

CONTEUDO = b'{"format":"teste"}'


def _relatorio(org: Organization, user: User, run: RiskRun, **campos: object) -> Report:
    valores: dict[str, object] = {
        "organization": org,
        "requested_by": user,
        "created_at": timezone.now(),
        "kind": Report.Kind.ASSET_RISK,
        "format_version": 1,
        "asset": run.asset,
        "risk_run": run,
        "content": CONTEUDO,
        "sha256": hashlib.sha256(CONTEUDO).hexdigest(),
        "size_bytes": len(CONTEUDO),
    }
    valores.update(campos)
    with organization_scope(org.pk):
        return Report.objects.create(**valores)


@pytest.fixture
def run() -> RiskRun:
    return execucao_completa(ativo("ITUB4"), timezone.now() - timedelta(hours=1))


@pytest.fixture
def relatorio(run: RiskRun) -> Report:
    org = organizacao("org-a")
    return _relatorio(org, usuario(org, "a@a.test", role="admin"), run)


# --- V-01: a tabela --------------------------------------------------------------------


def test_v01_as_colunas_da_tabela() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name, data_type, is_nullable FROM information_schema.columns"
            " WHERE table_schema = 'core' AND table_name = 'report'"
        )
        linhas = cursor.fetchall()
    assert {nome: tipo for nome, tipo, _ in linhas} == COLUNAS
    assert {nome for nome, _, nula in linhas if nula == "YES"} == set()


def test_v01_o_public_id_e_unico_no_banco(relatorio: Report, run: RiskRun) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Report.unscoped.create(
            public_id=relatorio.public_id,
            organization=relatorio.organization,
            requested_by=relatorio.requested_by,
            created_at=timezone.now(),
            kind=Report.Kind.ASSET_RISK,
            format_version=1,
            asset=run.asset,
            risk_run=run,
            content=CONTEUDO,
            sha256=hashlib.sha256(CONTEUDO).hexdigest(),
            size_bytes=len(CONTEUDO),
        )


def test_o_indice_por_organizacao_e_instante() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexdef FROM pg_indexes"
            " WHERE schemaname = 'core' AND indexname = 'report_org_created'"
        )
        linhas = cursor.fetchall()
    assert len(linhas) == 1
    assert "(organization_id, created_at)" in linhas[0][0]


# --- V-02: imutavel no Django ------------------------------------------------------------


def test_v02_save_de_linha_existente_levanta(relatorio: Report) -> None:
    relatorio.sha256 = "f" * 64
    with pytest.raises(TypeError, match="report so cresce"):
        relatorio.save()
    assert Report.unscoped.get(pk=relatorio.pk).sha256 != "f" * 64


def test_v02_delete_da_instancia_levanta(relatorio: Report) -> None:
    with pytest.raises(TypeError, match="report so cresce"):
        relatorio.delete()
    assert Report.unscoped.filter(pk=relatorio.pk).exists()


def test_v02_update_e_delete_do_queryset_pelo_gerente_escopado(
    relatorio: Report,
) -> None:
    with organization_scope(relatorio.organization_id):
        with pytest.raises(TypeError, match="report so cresce"):
            Report.objects.all().update(size_bytes=0)
        with pytest.raises(TypeError, match="report so cresce"):
            Report.objects.filter(pk=relatorio.pk).delete()
        with pytest.raises(TypeError, match="report so cresce"):
            Report.objects.update(size_bytes=0)
        with pytest.raises(TypeError, match="report so cresce"):
            relatorio.requested_by.reports.all().delete()
    assert Report.unscoped.get(pk=relatorio.pk).size_bytes == len(CONTEUDO)


def test_v02_update_e_delete_do_queryset_pelo_gerente_base(relatorio: Report) -> None:
    with pytest.raises(TypeError, match="report so cresce"):
        Report.unscoped.all().update(size_bytes=0)
    with pytest.raises(TypeError, match="report so cresce"):
        Report.unscoped.filter(pk=relatorio.pk).delete()
    with pytest.raises(TypeError, match="report so cresce"):
        Report.unscoped.update(size_bytes=0)
    assert Report.unscoped.get(pk=relatorio.pk).size_bytes == len(CONTEUDO)


# --- V-03: imutavel no banco -------------------------------------------------------------


def test_v03_update_por_sql_cru_e_recusado_pelo_banco(relatorio: Report) -> None:
    with (
        pytest.raises(DatabaseError, match="report so cresce"),
        transaction.atomic(),
        connection.cursor() as cursor,
    ):
        cursor.execute(
            "UPDATE core.report SET size_bytes = 0 WHERE id = %s", [relatorio.pk]
        )
    assert Report.unscoped.get(pk=relatorio.pk).size_bytes == len(CONTEUDO)


def test_v03_delete_por_sql_cru_e_recusado_pelo_banco(relatorio: Report) -> None:
    with (
        pytest.raises(DatabaseError, match="report so cresce"),
        transaction.atomic(),
        connection.cursor() as cursor,
    ):
        cursor.execute("DELETE FROM core.report WHERE id = %s", [relatorio.pk])
    assert Report.unscoped.filter(pk=relatorio.pk).exists()


def test_v03_update_e_delete_no_mesmo_teste_cada_um_no_seu_ponto(
    relatorio: Report,
) -> None:
    for sql in (
        "UPDATE core.report SET sha256 = 'x' WHERE id = %s",
        "DELETE FROM core.report WHERE id = %s",
    ):
        with (
            pytest.raises(DatabaseError, match="report so cresce"),
            transaction.atomic(),
            connection.cursor() as cursor,
        ):
            cursor.execute(sql, [relatorio.pk])
    assert Report.unscoped.filter(pk=relatorio.pk).count() == 1


def test_v03_o_truncate_passa(relatorio: Report) -> None:
    with connection.cursor() as cursor:
        # As FKs do Django sao `DEFERRABLE INITIALLY DEFERRED`: a insercao do relatorio, na
        # mesma transacao do teste, deixa a checagem delas pendente, e o PostgreSQL recusa o
        # `TRUNCATE` com "pending trigger events" -- nao pelo gatilho `report_so_cresce`. O
        # `banco_limpo` e o `psql` truncam em transacao propria; aqui, as checagens rodam antes.
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("TRUNCATE core.report")
    assert Report.unscoped.count() == 0


def test_v03_o_gatilho_existe_uma_vez() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM pg_trigger WHERE tgname = 'report_so_cresce'"
        )
        assert cursor.fetchone() == (1,)


# --- os `PROTECT` ------------------------------------------------------------------------


@pytest.mark.parametrize("nome", ["organization", "requested_by", "asset", "risk_run"])
def test_as_quatro_chaves_estrangeiras_sao_protect(nome: str) -> None:
    campo = Report._meta.get_field(nome)
    assert campo.remote_field is not None
    assert getattr(campo.remote_field, "on_delete", None) is models.PROTECT


def test_apagar_a_execucao_citada_levanta_protected_error(
    relatorio: Report, run: RiskRun
) -> None:
    with pytest.raises(ProtectedError) as erro:
        run.delete()
    assert relatorio in erro.value.protected_objects
    assert RiskRun.objects.filter(pk=run.pk).exists()
