"""M2.2a, T1: as cinco tabelas da carteira (RF-01 a RF-05; V-01, V-02).

V-01 e a forma: as colunas pelo `information_schema`, os unicos e as checagens no banco, os
campos do resultado contra os de `RiskResult` e as regras de exclusao das FKs. V-02 e a
imutabilidade da versao e da posicao, no Django e no banco, no molde de
`tests/accounts/test_report_modelo.py`.

O erro do banco envenena a transacao do teste: cada escrita que deve falhar no banco roda dentro
de `transaction.atomic()`, o ponto de salvamento, para o passo seguinte nao quebrar com
`current transaction is aborted` em vez de pelo motivo certo.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import DatabaseError, IntegrityError, connection, models, transaction
from django.utils import timezone

from apps.accounts.tenancy import organization_scope
from apps.assets.models import Asset
from apps.portfolios.models import (
    Portfolio,
    PortfolioHolding,
    PortfolioRiskResult,
    PortfolioRiskRun,
    PortfolioVersion,
)
from apps.risk.models import RiskResult, RiskRun
from tests.portfolios.dados import (
    Pessoas,
    acao,
    carteira,
    execucao,
    org_e_pessoas,
    resultado,
)

pytestmark = pytest.mark.django_db

# (tipo, nula); para `numeric`, tambem (precisao, escala)
Coluna = tuple[str, bool] | tuple[str, bool, int, int]

TZ = "timestamp with time zone"
VC = "character varying"

COLUNAS: dict[str, dict[str, Coluna]] = {
    "core.portfolio": {
        "id": ("bigint", False),
        "public_id": ("uuid", False),
        "organization_id": ("bigint", False),
        "created_by_id": ("bigint", False),
        "name": (VC, False),
        "notional": ("numeric", True, 18, 2),
        "created_at": (TZ, False),
        "updated_at": (TZ, False),
        "archived_at": (TZ, True),
    },
    "core.portfolio_version": {
        "id": ("bigint", False),
        "portfolio_id": ("bigint", False),
        "number": ("integer", False),
        "created_by_id": ("bigint", False),
        "created_at": (TZ, False),
    },
    "core.portfolio_holding": {
        "id": ("bigint", False),
        "version_id": ("bigint", False),
        "asset_id": ("bigint", False),
        "weight": ("numeric", False, 5, 2),
    },
    "gold.portfolio_risk_run": {
        "id": ("bigint", False),
        "version_id": ("bigint", False),
        "requested_by_id": ("bigint", False),
        "calculated_at": (TZ, False),
        "finished_at": (TZ, True),
        "status": (VC, False),
        "engine_version": (VC, False),
        "seed": ("integer", False),
        "train_window_days": ("integer", False),
        "first_date": ("date", False),
        "as_of_date": ("date", False),
        "session_count": ("integer", False),
        "train_count": ("integer", False),
        "test_count": ("integer", False),
        "requested_models": ("jsonb", False),
        "price_run_id": ("bigint", False),
        "series_sha256": (VC, False),
    },
    "gold.portfolio_risk_result": {
        "id": ("bigint", False),
        "run_id": ("bigint", False),
        "model_name": (VC, False),
        "model_category": (VC, False),
        "alpha": ("numeric", False, 6, 4),
        "hyperparameters": ("jsonb", False),
        "var_latest": ("numeric", True, 18, 10),
        "var_mean": ("numeric", True, 18, 10),
        "violations": ("integer", True),
        "expected_violations": ("numeric", True, 18, 6),
        "kupiec_passed": ("boolean", True),
        "kupiec_p_value": ("numeric", True, 18, 10),
        "christoffersen_passed": ("boolean", True),
        "christoffersen_p_value": ("numeric", True, 18, 10),
        "dq_passed": ("boolean", True),
        "dq_p_value": ("numeric", True, 18, 10),
        "basel_zone": (VC, True),
        "adequate": ("boolean", True),
        "error": ("text", False),
    },
}


@pytest.fixture
def pessoas() -> Pessoas:
    return org_e_pessoas()


@pytest.fixture
def portfolio(pessoas: Pessoas) -> Portfolio:
    acao("PETR4", [])
    acao("VALE3", [])
    return carteira(pessoas.admin, {"PETR4": "60.00", "VALE3": "40.00"})


def _versao(portfolio: Portfolio) -> PortfolioVersion:
    return PortfolioVersion.unscoped.get(portfolio=portfolio, number=1)


def _posicao(portfolio: Portfolio) -> PortfolioHolding:
    return PortfolioHolding.unscoped.get(
        version__portfolio=portfolio, asset__ticker="PETR4"
    )


# --- V-01: as colunas -------------------------------------------------------------------


@pytest.mark.parametrize("tabela", sorted(COLUNAS))
def test_v01_as_colunas_de_cada_tabela(tabela: str) -> None:
    esquema, nome = tabela.split(".")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name, data_type, is_nullable, numeric_precision, numeric_scale"
            " FROM information_schema.columns"
            " WHERE table_schema = %s AND table_name = %s",
            [esquema, nome],
        )
        linhas = cursor.fetchall()
    encontradas: dict[str, Coluna] = {}
    for coluna, tipo, nula, precisao, escala in linhas:
        if tipo == "numeric":
            encontradas[coluna] = (tipo, nula == "YES", precisao, escala)
        else:
            encontradas[coluna] = (tipo, nula == "YES")
    assert encontradas == COLUNAS[tabela]


def test_v01_o_indice_da_carteira_por_organizacao_e_instante() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexdef FROM pg_indexes"
            " WHERE schemaname = 'core' AND indexname = 'portfolio_org_created'"
        )
        linhas = cursor.fetchall()
    assert len(linhas) == 1
    assert "(organization_id, created_at)" in linhas[0][0]


def test_v01_o_indice_da_execucao_por_versao_e_instante_decrescente() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexdef FROM pg_indexes"
            " WHERE schemaname = 'gold' AND indexname = 'prisk_run_version_recent'"
        )
        linhas = cursor.fetchall()
    assert len(linhas) == 1
    assert "(version_id, calculated_at DESC)" in linhas[0][0]


# --- V-01: os unicos e as checagens -----------------------------------------------------


def test_v01_o_public_id_e_unico(portfolio: Portfolio, pessoas: Pessoas) -> None:
    agora = timezone.now()
    with pytest.raises(IntegrityError), transaction.atomic():
        Portfolio.unscoped.create(
            public_id=portfolio.public_id,
            organization=pessoas.acme,
            created_by=pessoas.admin,
            name="outra",
            created_at=agora,
            updated_at=agora,
        )


def test_v01_duas_versoes_de_mesmo_numero(
    portfolio: Portfolio, pessoas: Pessoas
) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        PortfolioVersion.unscoped.create(
            portfolio=portfolio,
            number=1,
            created_by=pessoas.admin,
            created_at=timezone.now(),
        )


def test_v01_duas_posicoes_do_mesmo_ativo(portfolio: Portfolio) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        PortfolioHolding.unscoped.create(
            version=_versao(portfolio),
            asset=Asset.objects.get(ticker="PETR4"),
            weight=Decimal("1.00"),
        )


def test_v01_dois_resultados_do_mesmo_modelo_e_nivel(
    portfolio: Portfolio, pessoas: Pessoas
) -> None:
    run = execucao(_versao(portfolio), pessoas.admin)
    resultado(run, "historical", "0.0500")
    resultado(run, "historical", "0.0100")
    with pytest.raises(IntegrityError), transaction.atomic():
        resultado(run, "historical", "0.0500")


def test_v01_duas_execucoes_da_versao_no_mesmo_instante(
    portfolio: Portfolio, pessoas: Pessoas
) -> None:
    instante = timezone.now()
    execucao(_versao(portfolio), pessoas.admin, calculated_at=instante)
    with pytest.raises(IntegrityError), transaction.atomic():
        execucao(_versao(portfolio), pessoas.admin, calculated_at=instante)


def test_v01_a_versao_zero_e_recusada(portfolio: Portfolio, pessoas: Pessoas) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        PortfolioVersion.unscoped.create(
            portfolio=portfolio,
            number=0,
            created_by=pessoas.admin,
            created_at=timezone.now(),
        )


@pytest.mark.parametrize("peso", ["0", "100.01", "-1.00"])
def test_v01_o_peso_fora_da_faixa_e_recusado(portfolio: Portfolio, peso: str) -> None:
    acao("ITUB4", [])
    with pytest.raises(IntegrityError), transaction.atomic():
        PortfolioHolding.unscoped.create(
            version=_versao(portfolio),
            asset=Asset.objects.get(ticker="ITUB4"),
            weight=Decimal(peso),
        )


def test_v01_o_peso_100_passa(portfolio: Portfolio) -> None:
    acao("ITUB4", [])
    PortfolioHolding.unscoped.create(
        version=_versao(portfolio),
        asset=Asset.objects.get(ticker="ITUB4"),
        weight=Decimal("100"),
    )


# --- V-01: o resultado e o do ativo menos os retratos -----------------------------------


def _decimais(modelo: type[models.Model]) -> dict[str, tuple[int | None, int | None]]:
    return {
        f.name: (f.max_digits, f.decimal_places)
        for f in modelo._meta.concrete_fields
        if isinstance(f, models.DecimalField)
    }


def test_v01_o_resultado_tem_os_campos_de_risk_result_menos_os_retratos() -> None:
    def nomes(modelo: type[models.Model]) -> set[str]:
        return {f.name for f in modelo._meta.concrete_fields}

    esperado = nomes(RiskResult) - {"reused_snapshots", "trained_snapshots"}
    assert nomes(PortfolioRiskResult) == esperado


def test_v01_cada_campo_do_resultado_tem_o_tipo_de_risk_result() -> None:
    for campo in PortfolioRiskResult._meta.concrete_fields:
        if campo.name in {"id", "run"}:
            continue
        do_ativo = RiskResult._meta.get_field(campo.name)
        assert type(campo) is type(do_ativo), campo.name
        assert campo.null == do_ativo.null, campo.name
    assert _decimais(PortfolioRiskResult) == _decimais(RiskResult)


# --- V-01: as regras de exclusao --------------------------------------------------------

PROTECT = [
    (Portfolio, "organization"),
    (Portfolio, "created_by"),
    (PortfolioVersion, "portfolio"),
    (PortfolioVersion, "created_by"),
    (PortfolioHolding, "version"),
    (PortfolioHolding, "asset"),
    (PortfolioRiskRun, "version"),
    (PortfolioRiskRun, "requested_by"),
    (PortfolioRiskRun, "price_run"),
]


@pytest.mark.parametrize(
    ("modelo", "nome"), PROTECT, ids=[f"{m.__name__}.{n}" for m, n in PROTECT]
)
def test_v01_as_chaves_estrangeiras_sao_protect(
    modelo: type[models.Model], nome: str
) -> None:
    campo = modelo._meta.get_field(nome)
    assert campo.remote_field is not None
    assert getattr(campo.remote_field, "on_delete", None) is models.PROTECT


def test_v01_o_resultado_pende_da_execucao_em_cascade() -> None:
    campo = PortfolioRiskResult._meta.get_field("run")
    assert campo.remote_field is not None
    assert getattr(campo.remote_field, "on_delete", None) is models.CASCADE


def test_v01_o_status_da_execucao_usa_as_escolhas_de_risk_run() -> None:
    campo = PortfolioRiskRun._meta.get_field("status")
    assert list(campo.choices or []) == list(RiskRun.Status.choices)


# --- V-02: versao e posicao so crescem, no Django ---------------------------------------

SO_CRESCE = [
    (PortfolioVersion, "portfolio_version so cresce"),
    (PortfolioHolding, "portfolio_holding so cresce"),
]


def _linha(modelo: type[models.Model], portfolio: Portfolio) -> models.Model:
    return _versao(portfolio) if modelo is PortfolioVersion else _posicao(portfolio)


@pytest.mark.parametrize(("modelo", "mensagem"), SO_CRESCE, ids=["versao", "posicao"])
def test_v02_save_de_linha_existente_levanta(
    portfolio: Portfolio, modelo: type[models.Model], mensagem: str
) -> None:
    linha = _linha(modelo, portfolio)
    with pytest.raises(TypeError, match=mensagem):
        linha.save()


@pytest.mark.parametrize(("modelo", "mensagem"), SO_CRESCE, ids=["versao", "posicao"])
def test_v02_delete_da_instancia_levanta(
    portfolio: Portfolio, modelo: type[models.Model], mensagem: str
) -> None:
    linha = _linha(modelo, portfolio)
    with pytest.raises(TypeError, match=mensagem):
        linha.delete()
    assert modelo._base_manager.filter(pk=linha.pk).exists()


def test_v02_save_da_versao_nao_chega_ao_banco(portfolio: Portfolio) -> None:
    versao = _versao(portfolio)
    versao.number = 9
    with pytest.raises(TypeError, match="portfolio_version so cresce"):
        versao.save()
    assert PortfolioVersion.unscoped.get(pk=versao.pk).number == 1


def test_v02_save_da_posicao_nao_chega_ao_banco(portfolio: Portfolio) -> None:
    posicao = _posicao(portfolio)
    posicao.weight = Decimal("1.00")
    with pytest.raises(TypeError, match="portfolio_holding so cresce"):
        posicao.save()
    assert PortfolioHolding.unscoped.get(pk=posicao.pk).weight == Decimal("60.00")


def test_v02_update_e_delete_da_versao_pelos_dois_gerentes(
    portfolio: Portfolio,
) -> None:
    mensagem = "portfolio_version so cresce"
    with organization_scope(portfolio.organization_id):
        with pytest.raises(TypeError, match=mensagem):
            PortfolioVersion.objects.all().update(number=9)
        with pytest.raises(TypeError, match=mensagem):
            PortfolioVersion.objects.update(number=9)
        with pytest.raises(TypeError, match=mensagem):
            PortfolioVersion.objects.filter(portfolio=portfolio).delete()
        with pytest.raises(TypeError, match=mensagem):
            portfolio.versions.all().delete()
    with pytest.raises(TypeError, match=mensagem):
        PortfolioVersion.unscoped.all().update(number=9)
    with pytest.raises(TypeError, match=mensagem):
        PortfolioVersion.unscoped.update(number=9)
    with pytest.raises(TypeError, match=mensagem):
        PortfolioVersion.unscoped.filter(portfolio=portfolio).delete()
    assert PortfolioVersion.unscoped.get(portfolio=portfolio).number == 1


def test_v02_update_e_delete_da_posicao_pelos_dois_gerentes(
    portfolio: Portfolio,
) -> None:
    mensagem = "portfolio_holding so cresce"
    versao = _versao(portfolio)
    with organization_scope(portfolio.organization_id):
        with pytest.raises(TypeError, match=mensagem):
            PortfolioHolding.objects.all().update(weight=Decimal("1.00"))
        with pytest.raises(TypeError, match=mensagem):
            PortfolioHolding.objects.update(weight=Decimal("1.00"))
        with pytest.raises(TypeError, match=mensagem):
            PortfolioHolding.objects.filter(version=versao).delete()
        with pytest.raises(TypeError, match=mensagem):
            versao.holdings.all().delete()
    with pytest.raises(TypeError, match=mensagem):
        PortfolioHolding.unscoped.all().update(weight=Decimal("1.00"))
    with pytest.raises(TypeError, match=mensagem):
        PortfolioHolding.unscoped.update(weight=Decimal("1.00"))
    with pytest.raises(TypeError, match=mensagem):
        PortfolioHolding.unscoped.filter(version=versao).delete()
    assert sorted(
        PortfolioHolding.unscoped.filter(version=versao).values_list(
            "weight", flat=True
        )
    ) == [Decimal("40.00"), Decimal("60.00")]


# --- V-02: versao e posicao so crescem, no banco ----------------------------------------

SQL_RECUSADO = [
    ("UPDATE core.portfolio_version SET number = 9 WHERE id = %s", "version"),
    ("DELETE FROM core.portfolio_version WHERE id = %s", "version"),
    ("UPDATE core.portfolio_holding SET weight = 1 WHERE id = %s", "holding"),
    ("DELETE FROM core.portfolio_holding WHERE id = %s", "holding"),
]


def test_v02_update_e_delete_por_sql_cru_sao_recusados_pelo_banco(
    portfolio: Portfolio,
) -> None:
    versao = _versao(portfolio)
    posicao = _posicao(portfolio)
    for sql, tabela in SQL_RECUSADO:
        pk = versao.pk if tabela == "version" else posicao.pk
        with (
            pytest.raises(DatabaseError, match=f"portfolio_{tabela} so cresce"),
            transaction.atomic(),
            connection.cursor() as cursor,
        ):
            cursor.execute(sql, [pk])
    assert PortfolioVersion.unscoped.get(pk=versao.pk).number == 1
    assert PortfolioHolding.unscoped.get(pk=posicao.pk).weight == Decimal("60.00")


def test_v02_os_dois_gatilhos_existem_uma_vez() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tgname FROM pg_trigger WHERE tgname LIKE 'portfolio_%%_so_cresce'"
            " ORDER BY tgname"
        )
        assert cursor.fetchall() == [
            ("portfolio_holding_so_cresce",),
            ("portfolio_version_so_cresce",),
        ]


def test_v02_o_truncate_da_posicao_passa(portfolio: Portfolio) -> None:
    with connection.cursor() as cursor:
        # As FKs do Django sao `DEFERRABLE INITIALLY DEFERRED`: a insercao, na mesma transacao
        # do teste, deixa a checagem pendente, e o PostgreSQL recusaria o `TRUNCATE` com
        # "pending trigger events" -- nao pelo gatilho. As checagens rodam antes.
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("TRUNCATE core.portfolio_holding")
    assert PortfolioHolding.unscoped.count() == 0


def test_v02_o_truncate_da_versao_em_cascata_passa(
    portfolio: Portfolio, pessoas: Pessoas
) -> None:
    resultado(execucao(_versao(portfolio), pessoas.admin))
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("TRUNCATE core.portfolio_version CASCADE")
    assert PortfolioVersion.unscoped.count() == 0
    assert PortfolioHolding.unscoped.count() == 0
    assert PortfolioRiskRun.unscoped.count() == 0
    assert PortfolioRiskResult.unscoped.count() == 0


# --- V-02: a carteira e a execucao mudam ------------------------------------------------


def test_v02_save_e_update_da_carteira_passam(portfolio: Portfolio) -> None:
    portfolio.name = "Renomeada"
    portfolio.save()
    with organization_scope(portfolio.organization_id):
        assert Portfolio.objects.filter(pk=portfolio.pk).update(
            archived_at=timezone.now()
        )
    linha = Portfolio.unscoped.get(pk=portfolio.pk)
    assert linha.name == "Renomeada"
    assert linha.archived_at is not None


def test_v02_save_e_update_da_execucao_passam(
    portfolio: Portfolio, pessoas: Pessoas
) -> None:
    run = execucao(_versao(portfolio), pessoas.admin)
    run.engine_version = "0.3.0"
    run.save(update_fields=["engine_version"])
    with organization_scope(portfolio.organization_id):
        assert PortfolioRiskRun.objects.filter(pk=run.pk).update(
            status=RiskRun.Status.OK, finished_at=timezone.now()
        )
    linha = PortfolioRiskRun.unscoped.get(pk=run.pk)
    assert (linha.engine_version, linha.status) == ("0.3.0", RiskRun.Status.OK)
