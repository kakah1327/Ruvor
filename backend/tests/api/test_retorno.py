"""M5.1, T5: `GET /api/v1/assets/{ticker}/returns` (RF-14, RF-15) — V-11 e V-13 (a rota).

As linhas de `gold.return_run` e `gold.return_result` sao criadas aqui, pelo ORM, sem o
calculo: a rota so le. A lista de campos de cada nivel e a lista fechada do RF-14, e o teste
reprova campo a mais **e** a menos. A chave pessoal le o `GET`; o `POST`, que a rota nem
tem, a chave recebe 403 `api_key_not_allowed` -- a autenticacao barra o metodo inseguro antes
do despacho.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from io import StringIO
from typing import Any

import pytest
from django.core.management import call_command
from drf_spectacular.drainage import GENERATOR_STATS
from rest_framework.test import APIClient

from apps.accounts import services
from apps.accounts.models import Organization, User
from apps.assets.models import Asset, CollectionRun
from apps.returns.models import ReturnResult, ReturnRun

pytestmark = pytest.mark.django_db

CORPO = {"ticker", "latest"}
LATEST = {
    "calculated_at",
    "engine_version",
    "as_of_date",
    "first_price_date",
    "price_count",
    "train_count",
    "test_count",
    "train_window_days",
    "price_run",
    "results",
}
PRICE_RUN = {"id", "source", "started_at", "finished_at"}
RESULTADO = {
    "model_name",
    "hyperparameters",
    "mse",
    "mse_reference",
    "r2_os",
    "direction_days",
    "hit_rate",
    "up_share",
    "forecast_up_share",
    "dm_statistic",
    "dm_p_value",
    "cw_statistic",
    "cw_p_value",
    "pt_statistic",
    "pt_p_value",
    "beats_reference",
    "direction_skill",
    "next_forecast",
    "next_forecast_date",
    "error",
}

ANTIGA = datetime(2026, 9, 1, 21, 0, tzinfo=UTC)
NOVA = datetime(2026, 10, 2, 21, 0, tzinfo=UTC)


def _ativo(ticker: str = "ITUB4", status: str = Asset.Status.ACTIVE) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=f"{ticker}.SA",
        created_at=ANTIGA,
        updated_at=ANTIGA,
    )


def _execucao(
    asset: Asset,
    calculated_at: datetime,
    *,
    as_of: date = date(2026, 10, 2),
    erro_no_ar: bool = False,
) -> ReturnRun:
    coleta = CollectionRun.objects.create(source="yahoo", started_at=calculated_at)
    run = ReturnRun.objects.create(
        asset=asset,
        calculated_at=calculated_at,
        finished_at=calculated_at,
        engine_version="0.5.0",
        train_window_days=252,
        as_of_date=as_of,
        first_price_date=date(2016, 9, 22),
        price_count=2499,
        train_count=252,
        test_count=2246,
        price_run=coleta,
    )
    # gravados fora da ordem de `model_name`: a rota ordena
    ReturnResult.objects.create(
        run=run,
        model_name="historical_mean",
        hyperparameters={"refit_frequency_days": 252, "window": "expanding"},
        mse=Decimal("0.0003210000"),
        mse_reference=Decimal("0.0003200000"),
        r2_os=Decimal("-0.0031250000"),
        direction_days=2240,
        hit_rate=Decimal("0.5100000000"),
        up_share=Decimal("0.5100000000"),
        forecast_up_share=Decimal("1.0000000000"),
        dm_statistic=Decimal("-0.4000000000"),
        dm_p_value=Decimal("0.6554217416"),
        cw_statistic=Decimal("1.2000000000"),
        cw_p_value=Decimal("0.1150696702"),
        pt_statistic=None,
        pt_p_value=None,
        beats_reference=False,
        direction_skill=None,
        next_forecast=Decimal("0.0004100000"),
        next_forecast_date=date(2026, 10, 5),
    )
    if erro_no_ar:
        ReturnResult.objects.create(
            run=run, model_name="ar_1", hyperparameters={"lags": 1}, error="explodiu"
        )
    else:
        ReturnResult.objects.create(
            run=run,
            model_name="ar_1",
            hyperparameters={"lags": 1},
            mse=Decimal("0.0003190000"),
            mse_reference=Decimal("0.0003200000"),
            r2_os=Decimal("0.0031250000"),
            direction_days=2240,
            hit_rate=Decimal("0.5200000000"),
            up_share=Decimal("0.5100000000"),
            forecast_up_share=Decimal("0.5500000000"),
            dm_statistic=Decimal("1.8000000000"),
            dm_p_value=Decimal("0.0359303191"),
            cw_statistic=Decimal("2.1000000000"),
            cw_p_value=Decimal("0.0178644206"),
            pt_statistic=Decimal("0.9000000000"),
            pt_p_value=Decimal("0.1840601253"),
            beats_reference=True,
            direction_skill=False,
            next_forecast=Decimal("-0.0012300000"),
            next_forecast_date=date(2026, 10, 5),
        )
    return run


def _get(ticker: str, cliente: APIClient | None = None) -> Any:
    return (cliente or APIClient()).get(f"/api/v1/assets/{ticker}/returns")


# --- V-11: a lista fechada e o latest --------------------------------------------------------


def test_v11_os_campos_de_cada_nivel_sao_a_lista_fechada() -> None:
    _execucao(_ativo(), NOVA)
    resposta = _get("ITUB4")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert set(corpo) == CORPO
    assert set(corpo["latest"]) == LATEST
    assert set(corpo["latest"]["price_run"]) == PRICE_RUN
    assert len(corpo["latest"]["results"]) == 2
    for resultado in corpo["latest"]["results"]:
        assert set(resultado) == RESULTADO


def test_v11_o_latest_e_a_execucao_de_maior_calculated_at() -> None:
    asset = _ativo()
    nova = _execucao(asset, NOVA)  # criada primeiro: o id nao decide
    _execucao(asset, ANTIGA, as_of=date(2026, 9, 1))
    latest = _get("ITUB4").json()["latest"]
    assert latest["calculated_at"] == "2026-10-02T18:00:00-03:00"
    assert latest["as_of_date"] == "2026-10-02"
    assert latest["price_run"]["id"] == nova.price_run_id


def test_v11_sem_execucao_o_latest_e_nulo() -> None:
    _ativo()
    assert _get("ITUB4").json() == {"ticker": "ITUB4", "latest": None}


def test_v11_ticker_desconhecido_e_asset_not_found() -> None:
    resposta = _get("NAO3")
    assert resposta.status_code == 404
    assert resposta.json()["error"]["code"] == "asset_not_found"


def test_v11_o_ticker_nao_distingue_caixa() -> None:
    _execucao(_ativo(), NOVA)
    corpo = _get("itub4").json()
    assert corpo["ticker"] == "ITUB4" and corpo["latest"] is not None


def test_v11_o_manifesto_os_resultados_por_modelo_e_os_formatos() -> None:
    run = _execucao(_ativo(), NOVA)
    latest = _get("ITUB4").json()["latest"]
    assert latest["price_run"] == {
        "id": run.price_run_id,
        "source": "yahoo",
        "started_at": "2026-10-02T18:00:00-03:00",
        "finished_at": None,
    }
    assert (
        latest["engine_version"],
        latest["first_price_date"],
        latest["price_count"],
        latest["train_count"],
        latest["test_count"],
        latest["train_window_days"],
    ) == ("0.5.0", "2016-09-22", 2499, 252, 2246, 252)
    ar, media = latest["results"]
    assert [ar["model_name"], media["model_name"]] == ["ar_1", "historical_mean"]
    # decimais como string, datas ISO
    assert ar["dm_p_value"] == "0.0359303191"
    assert ar["next_forecast"] == "-0.0012300000"
    assert ar["next_forecast_date"] == "2026-10-05"
    assert (ar["beats_reference"], ar["direction_skill"]) == (True, False)
    assert (media["pt_p_value"], media["direction_skill"]) == (None, None)
    assert "requested_by" not in latest


# --- V-13 (a rota): a previsao do proximo pregao ---------------------------------------------


def test_v13_a_previsao_sai_em_todo_resultado_e_nula_so_com_error() -> None:
    _execucao(_ativo(), NOVA, erro_no_ar=True)
    ar, media = _get("ITUB4").json()["latest"]["results"]
    assert ar["error"] == "explodiu"
    assert (ar["next_forecast"], ar["next_forecast_date"]) == (None, None)
    assert all(
        ar[c] is None for c in RESULTADO - {"model_name", "hyperparameters", "error"}
    )
    assert (media["next_forecast"], media["next_forecast_date"]) == (
        "0.0004100000",
        "2026-10-05",
    )


def test_v13_ativo_inativo_e_data_passada_devolvem_o_registro() -> None:
    """A API devolve o que foi gravado; quem decide o que mostrar e a tela (RF-18)."""
    asset = _ativo(status=Asset.Status.INACTIVE)
    _execucao(asset, ANTIGA, as_of=date(2026, 9, 1))
    ar, media = _get("ITUB4").json()["latest"]["results"]
    assert ar["next_forecast"] == "-0.0012300000"
    assert media["next_forecast_date"] == "2026-10-05"


# --- a chave pessoal e o metodo ---------------------------------------------------------------


@pytest.fixture
def com_chave() -> APIClient:
    pessoa = User.objects.create_user(
        email="leitora@ruvor.test",
        name="Leitora",
        organization=Organization.objects.get(slug="ruvor"),
        password="x" * 12,
    )
    segredo = services.create_api_key(pessoa, name="leitura", ip=None)[1]
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    return cliente


def test_a_chave_le_o_get(com_chave: APIClient) -> None:
    _execucao(_ativo(), NOVA)
    resposta = _get("ITUB4", com_chave)
    assert resposta.status_code == 200, resposta.content
    assert resposta.json()["latest"] is not None


def test_o_post_com_a_chave_e_api_key_not_allowed(com_chave: APIClient) -> None:
    _ativo()
    resposta = com_chave.post("/api/v1/assets/ITUB4/returns")
    assert resposta.status_code == 403
    assert resposta.json()["error"]["code"] == "api_key_not_allowed"


def test_so_get_o_post_anonimo_e_method_not_allowed() -> None:
    _ativo()
    resposta = APIClient().post("/api/v1/assets/ITUB4/returns")
    assert resposta.status_code == 405
    assert resposta.json()["error"]["code"] == "method_not_allowed"


# --- RF-15: o esquema -------------------------------------------------------------------------


def _resolve(esquema: dict[str, Any], no: dict[str, Any]) -> dict[str, Any]:
    while "$ref" in no:
        no = esquema["components"]["schemas"][no["$ref"].rsplit("/", 1)[-1]]
    return no


def test_rf15_o_esquema_sem_aviso_e_model_name_texto_livre() -> None:
    GENERATOR_STATS.reset()
    call_command("spectacular", "--validate", "--fail-on-warn", stdout=StringIO())
    esquema = APIClient().get("/api/v1/schema").json()
    rota = esquema["paths"]["/api/v1/assets/{ticker}/returns"]
    assert set(rota) == {"get", "parameters"} or set(rota) == {"get"}
    corpo = rota["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    latest = _resolve(esquema, corpo)["properties"]["latest"]
    if "allOf" in latest:
        latest = latest["allOf"][0]
    if "oneOf" in latest:
        latest = next(o for o in latest["oneOf"] if "$ref" in o)
    latest = _resolve(esquema, latest)
    assert set(latest["properties"]) == LATEST
    resultado = _resolve(esquema, latest["properties"]["results"]["items"])
    assert set(resultado["properties"]) == RESULTADO
    model_name = resultado["properties"]["model_name"]
    assert model_name["type"] == "string"
    assert "enum" not in model_name and "$ref" not in model_name
