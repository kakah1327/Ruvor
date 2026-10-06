"""O `/lab` (M2.4, RF-12): o V-10 do plano, Tarefa 5.

O corpo e lista fechada: o teste confere o **conjunto** de chaves por igualdade em cada nivel --
o corpo, a decada, o `latest`, a coleta, cada resultado, cada ano e o `last_failure` --, e um
campo a mais ou a menos reprova. Os dados sao montados direto no banco (`lab_run`, `lab_result`,
`lab_year`, `risk_run`): o calculo e da T3; aqui se prova a leitura.

O `pending` se prova por tabela sobre `lab_pending` -- cada uma das cinco condicoes o derrubando
sozinha, e o `partial` do mesmo motor o acendendo -- e por dois casos pela rota.

**A chave pessoal** (`apps.accounts.services.create_api_key`, `Authorization: Bearer ...`): 200 no
`GET`; no `POST`, 403 `api_key_not_allowed`, barrado na autenticacao (`_check_reach`,
`apps/accounts/authentication.py`) antes do despacho. Nada muda em `tests/accounts/`.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts import services
from apps.api.views import lab_pending
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk.models import LabResult, LabRun, LabYear, RiskRun
from tests.accounts.conftest import organizacao, usuario

pytestmark = pytest.mark.django_db

SAO_PAULO = ZoneInfo("America/Sao_Paulo")
INICIO = date(2015, 1, 5)

CHAVES = {
    "ticker",
    "active",
    "decade",
    "risk_engine_version",
    "pending",
    "latest",
    "last_failure",
}
CHAVES_DECADA = {
    "first_price_date",
    "end_date",
    "last_price_date",
    "complete",
    "sessions",
}
CHAVES_LATEST = {
    "id",
    "calculated_at",
    "finished_at",
    "status",
    "origin",
    "engine_version",
    "seed",
    "train_window_days",
    "first_price_date",
    "decade_end",
    "as_of_date",
    "price_count",
    "train_count",
    "test_count",
    "year_count",
    "price_run",
    "price_fingerprint",
    "results",
}
CHAVES_COLETA = {"id", "source", "started_at", "finished_at"}
CHAVES_RESULTADO = {
    "model_name",
    "model_category",
    "alpha",
    "test_count",
    "violations",
    "expected_violations",
    "kupiec_passed",
    "kupiec_p_value",
    "christoffersen_passed",
    "christoffersen_p_value",
    "dq_passed",
    "dq_p_value",
    "adequate",
    "error",
    "reused_snapshots",
    "trained_snapshots",
    "years",
}
CHAVES_ANO = {
    "index",
    "start_date",
    "end_date",
    "test_count",
    "violations",
    "expected_violations",
    "kupiec_passed",
    "kupiec_p_value",
    "christoffersen_passed",
    "christoffersen_p_value",
    "adequate",
}
CHAVES_FALHA = {"id", "calculated_at", "engine_version", "error"}


def _iso(instante: datetime) -> str:
    return instante.astimezone(SAO_PAULO).isoformat()


def _lab(client: Client | APIClient, ticker: str = "LABS3") -> dict[str, Any]:
    resposta = client.get(f"/api/v1/assets/{ticker}/lab")
    assert resposta.status_code == 200, resposta.content
    corpo: dict[str, Any] = resposta.json()
    assert set(corpo) == CHAVES
    assert set(corpo["decade"]) == CHAVES_DECADA
    if corpo["latest"] is not None:
        assert set(corpo["latest"]) == CHAVES_LATEST
        assert set(corpo["latest"]["price_run"]) == CHAVES_COLETA
        for resultado in corpo["latest"]["results"]:
            assert set(resultado) == CHAVES_RESULTADO
            for ano in resultado["years"]:
                assert set(ano) == CHAVES_ANO
    if corpo["last_failure"] is not None:
        assert set(corpo["last_failure"]) == CHAVES_FALHA
    return corpo


# --- os dados ------------------------------------------------------------------------------


def _ativo(
    ticker: str = "LABS3",
    *,
    precos: int = 530,
    passo: int = 7,
    status: str = Asset.Status.ACTIVE,
) -> Asset:
    """530 pregoes, um a cada 7 dias: a decada completa (3710 dias) e suficiente (522)."""
    agora = timezone.now()
    asset = Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=f"{ticker}.SA",
        created_at=agora,
        updated_at=agora,
    )
    if precos:
        coleta = CollectionRun.objects.create(source="teste", started_at=agora)
        valor = Decimal("10.000000")
        Price.objects.bulk_create(
            Price(
                asset=asset,
                date=INICIO + timedelta(days=passo * i),
                open=valor,
                high=valor,
                low=valor,
                close=valor,
                adj_close=valor,
                volume=1000,
                log_return=None,
                run=coleta,
                updated_at=agora,
            )
            for i in range(precos)
        )
    return asset


def _lab_run(
    asset: Asset,
    status: str,
    calculated_at: datetime,
    *,
    engine_version: str = "0.4.0",
    error: str = "",
) -> LabRun:
    coleta = CollectionRun.objects.create(source="teste", started_at=calculated_at)
    return LabRun.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        finished_at=calculated_at + timedelta(seconds=5),
        status=status,
        origin=LabRun.Origin.RISK_CLOSE,
        engine_version=engine_version,
        seed=42,
        train_window_days=252,
        library_versions={"numpy": "2.0.0"},
        library_versions_hash="a" * 64,
        first_price_date=INICIO,
        decade_end=date(2025, 1, 5),
        as_of_date=date(2025, 1, 4),
        price_count=522,
        train_count=252,
        test_count=269,
        year_count=2,
        price_run=coleta,
        price_fingerprint="b" * 64,
        requested_models=["historical", "parametric"],
        error=error,
    )


def _resultado(run: LabRun, modelo: str, alpha: str, *, erro: str = "") -> LabResult:
    numeros: dict[str, Any] = (
        {}
        if erro
        else {
            "test_count": 269,
            "violations": 14,
            "expected_violations": Decimal("13.450000"),
            "kupiec_passed": True,
            "kupiec_p_value": Decimal("0.8000000000"),
            "christoffersen_passed": True,
            "christoffersen_p_value": Decimal("0.6000000000"),
            "dq_passed": True,
            "dq_p_value": Decimal("0.4000000000"),
            "adequate": True,
        }
    )
    return LabResult.objects.create(
        run=run,
        model_name=modelo,
        model_category="traditional",
        alpha=Decimal(alpha),
        hyperparameters={"refit_frequency_days": 252},
        error=erro,
        **numeros,
    )


def _ano(resultado: LabResult, index: int, julgado: bool) -> LabYear:
    testes: dict[str, Any] = (
        {
            "kupiec_passed": True,
            "kupiec_p_value": Decimal("0.7000000000"),
            "christoffersen_passed": False,
            "christoffersen_p_value": Decimal("0.0100000000"),
            "adequate": False,
        }
        if julgado
        else {}
    )
    return LabYear.objects.create(
        result=resultado,
        index=index,
        start_date=date(2016, 1, 4) + timedelta(days=365 * index),
        end_date=date(2016, 12, 30) + timedelta(days=365 * index),
        test_count=252 if index == 0 else 17,
        violations=12 if index == 0 else 2,
        expected_violations=Decimal("12.600000") if index == 0 else Decimal("0.850000"),
        **testes,
    )


def _risco(asset: Asset, status: str, calculated_at: datetime, versao: str) -> RiskRun:
    coleta = CollectionRun.objects.create(source="teste", started_at=calculated_at)
    return RiskRun.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        finished_at=calculated_at,
        engine_version=versao,
        seed=42,
        train_window_days=252,
        as_of_date=date(2025, 3, 1),
        first_price_date=INICIO,
        price_count=530,
        train_count=252,
        test_count=277,
        price_run=coleta,
        status=status,
        requested_models=["historical"],
        full_recompute=False,
    )


# --- o corpo -------------------------------------------------------------------------------


def test_o_corpo_completo_com_o_latest_os_resultados_e_os_anos(client: Client) -> None:
    asset = _ativo()
    agora = timezone.now()
    run = _lab_run(asset, LabRun.Status.OK, agora - timedelta(hours=1))
    # gravados fora de ordem: a rota ordena
    _resultado(run, "parametric", "0.0100")
    historical_99 = _resultado(run, "historical", "0.0100")
    historical_95 = _resultado(run, "historical", "0.0500")
    _resultado(run, "parametric", "0.0500", erro="boom")
    _ano(historical_95, 1, julgado=False)
    _ano(historical_95, 0, julgado=True)
    _ano(historical_99, 0, julgado=False)
    _risco(asset, RiskRun.Status.OK, agora - timedelta(hours=2), "0.4.0")

    corpo = _lab(client)
    assert corpo["ticker"] == "LABS3"
    assert corpo["active"] is True
    assert corpo["decade"] == {
        "first_price_date": "2015-01-05",
        "end_date": "2025-01-05",
        "last_price_date": (INICIO + timedelta(days=7 * 529)).isoformat(),
        "complete": True,
        "sessions": 522,
    }
    assert corpo["risk_engine_version"] == "0.4.0"
    assert corpo["pending"] is False
    assert corpo["last_failure"] is None

    latest = corpo["latest"]
    assert latest["id"] == run.pk
    assert latest["status"] == "ok"
    assert latest["origin"] == "risk_close"
    assert latest["calculated_at"] == _iso(run.calculated_at)
    assert latest["decade_end"] == "2025-01-05"
    assert latest["price_run"]["id"] == run.price_run_id
    assert [(r["model_name"], r["alpha"]) for r in latest["results"]] == [
        ("historical", "0.0500"),
        ("historical", "0.0100"),
        ("parametric", "0.0500"),
        ("parametric", "0.0100"),
    ]
    h95 = latest["results"][0]
    assert h95["expected_violations"] == "13.450000"  # decimal como texto
    assert h95["kupiec_p_value"] == "0.8000000000"
    assert [a["index"] for a in h95["years"]] == [0, 1]
    assert h95["years"][0]["adequate"] is False
    assert h95["years"][1]["kupiec_passed"] is None
    assert h95["years"][1]["adequate"] is None
    falho = latest["results"][2]
    assert falho["error"] == "boom"
    assert falho["adequate"] is None and falho["violations"] is None
    assert falho["years"] == []


def test_ativo_sem_preco_tem_a_decada_nula(client: Client) -> None:
    _ativo(precos=0)
    corpo = _lab(client)
    assert corpo["decade"] == {
        "first_price_date": None,
        "end_date": None,
        "last_price_date": None,
        "complete": False,
        "sessions": 0,
    }
    assert corpo["latest"] is None
    assert corpo["last_failure"] is None
    assert corpo["risk_engine_version"] is None
    assert corpo["pending"] is False


def test_ticker_desconhecido_e_404_asset_not_found(client: Client) -> None:
    resposta = client.get("/api/v1/assets/NADA3/lab")
    assert resposta.status_code == 404
    assert resposta.json()["error"]["code"] == "asset_not_found"


def test_o_ticker_sem_distincao_de_caixa(client: Client) -> None:
    _ativo()
    assert _lab(client, "labs3")["ticker"] == "LABS3"


# --- latest e last_failure ------------------------------------------------------------------


def test_latest_e_o_ok_ou_partial_mais_recente_de_qualquer_versao(
    client: Client,
) -> None:
    asset = _ativo()
    agora = timezone.now()
    _lab_run(
        asset, LabRun.Status.OK, agora - timedelta(hours=5), engine_version="0.5.0"
    )
    partial = _lab_run(
        asset, LabRun.Status.PARTIAL, agora - timedelta(hours=3), engine_version="0.4.0"
    )
    falho = _lab_run(asset, LabRun.Status.FAILED, agora - timedelta(hours=1), error="x")
    corpo = _lab(client)
    assert corpo["latest"]["id"] == partial.pk  # nao o `failed` mais novo
    assert corpo["last_failure"] == {
        "id": falho.pk,
        "calculated_at": _iso(falho.calculated_at),
        "engine_version": "0.4.0",
        "error": "x",
    }


def test_last_failure_anterior_ao_latest_nao_sai(client: Client) -> None:
    asset = _ativo()
    agora = timezone.now()
    _lab_run(asset, LabRun.Status.FAILED, agora - timedelta(hours=3), error="velho")
    ok = _lab_run(asset, LabRun.Status.OK, agora - timedelta(hours=1))
    corpo = _lab(client)
    assert corpo["latest"]["id"] == ok.pk
    assert corpo["last_failure"] is None


def test_sem_latest_o_last_failure_e_o_mais_recente(client: Client) -> None:
    asset = _ativo()
    agora = timezone.now()
    _lab_run(asset, LabRun.Status.FAILED, agora - timedelta(hours=3), error="velho")
    novo = _lab_run(
        asset, LabRun.Status.FAILED, agora - timedelta(hours=1), error="novo"
    )
    corpo = _lab(client)
    assert corpo["latest"] is None
    assert corpo["last_failure"]["id"] == novo.pk


def test_risk_engine_version_e_a_da_producao_ok_ou_partial_mais_recente(
    client: Client,
) -> None:
    asset = _ativo()
    agora = timezone.now()
    _risco(asset, RiskRun.Status.OK, agora - timedelta(hours=5), "0.3.0")
    _risco(asset, RiskRun.Status.PARTIAL, agora - timedelta(hours=3), "0.4.0")
    _risco(asset, RiskRun.Status.FAILED, agora - timedelta(hours=2), "0.9.0")
    _risco(asset, RiskRun.Status.RUNNING, agora - timedelta(hours=1), "0.9.1")
    assert _lab(client)["risk_engine_version"] == "0.4.0"


# --- pending -------------------------------------------------------------------------------

DEVIDO: dict[str, Any] = {
    "active": True,
    "complete": True,
    "sessions": 503,
    "risk_engine_version": "0.4.0",
    "latest_engine_version": None,
    "latest_status": None,
}


@pytest.mark.parametrize(
    ("mudanca", "esperado"),
    [
        ({}, True),  # sem latest: devido
        ({"active": False}, False),
        ({"complete": False}, False),
        ({"sessions": 502}, False),
        ({"risk_engine_version": None}, False),
        ({"latest_engine_version": "0.4.0", "latest_status": "ok"}, False),
        # as tres alternativas da ultima condicao
        ({"latest_engine_version": "0.3.0", "latest_status": "ok"}, True),
        ({"latest_engine_version": "0.4.0", "latest_status": "partial"}, True),
        ({"latest_engine_version": "0.3.0", "latest_status": "partial"}, True),
        # o inativo nunca, nem com o `partial`
        (
            {
                "active": False,
                "latest_engine_version": "0.4.0",
                "latest_status": "partial",
            },
            False,
        ),
    ],
)
def test_a_tabela_do_pending(mudanca: dict[str, Any], esperado: bool) -> None:
    assert lab_pending(**{**DEVIDO, **mudanca}) is esperado


def test_pending_pela_rota_com_o_partial_do_mesmo_motor(client: Client) -> None:
    asset = _ativo()
    agora = timezone.now()
    _risco(asset, RiskRun.Status.OK, agora - timedelta(hours=2), "0.4.0")
    _lab_run(asset, LabRun.Status.PARTIAL, agora - timedelta(hours=1))
    assert _lab(client)["pending"] is True
    _lab_run(asset, LabRun.Status.OK, agora)
    assert _lab(client)["pending"] is False


def test_pending_pela_rota_falso_no_inativo_e_na_decada_curta(client: Client) -> None:
    agora = timezone.now()
    inativo = _ativo("INAT3", status=Asset.Status.INACTIVE)
    _risco(inativo, RiskRun.Status.OK, agora, "0.4.0")
    corpo = _lab(client, "INAT3")
    assert corpo["active"] is False and corpo["pending"] is False
    curto = _ativo("CURT3", precos=420, passo=10)
    _risco(curto, RiskRun.Status.OK, agora, "0.4.0")
    corpo = _lab(client, "CURT3")
    assert corpo["decade"]["complete"] is True
    assert corpo["decade"]["sessions"] < 503
    assert corpo["pending"] is False


# --- a chave pessoal ------------------------------------------------------------------------


@pytest.fixture
def chave() -> APIClient:
    ana = usuario(organizacao("acme"), "ana@acme.test", role="admin")
    segredo = services.create_api_key(ana, name="lab", ip=None)[1]
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    return c


def test_a_chave_le_o_get(chave: APIClient) -> None:
    _ativo()
    assert _lab(chave)["ticker"] == "LABS3"


def test_a_chave_no_post_e_403_api_key_not_allowed(chave: APIClient) -> None:
    _ativo()
    resposta = chave.post("/api/v1/assets/LABS3/lab")
    assert resposta.status_code == 403, resposta.content
    assert resposta.json()["error"]["code"] == "api_key_not_allowed"


def test_so_get_o_post_anonimo_nao_e_aceito(client: Client) -> None:
    _ativo()
    resposta = client.post("/api/v1/assets/LABS3/lab")
    assert resposta.status_code == 405
