"""M5.1, T3: `run_compute_returns` contra o banco — V-08, V-09 e V-13 (a gravacao).

O motor roda de verdade (os dois modelos levam milissegundos). As series sao sinteticas e
diarias: o piso e contado em pregoes, 503 e o minimo e 502 e pulado. Os precos saem de
log-retornos `default_rng(...).normal(0, 0.01)` acumulados a partir de 100.

V-09 substitui o `evaluate` do orquestrador do motor (`engine.returns.runner.evaluate`) por
um que devolve a avaliacao escrita no caso, para cada linha da tabela do RF-09.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from importlib.metadata import version
from typing import Any

import numpy as np
import pytest
from engine.data.preprocessing import fetch_returns
from engine.returns import (
    ReturnEvaluation,
    ReturnExperimentConfig,
    ReturnExperimentResult,
    ReturnModelResult,
    get_return_model,
    load_all_return_model_modules,
    run_return_experiment,
)

import apps.returns.compute as compute_module
from apps.accounts.models import Organization, User
from apps.assets.models import Asset, CollectionRun, Price
from apps.returns.compute import (
    InvalidTickers,
    ReturnModelsMissing,
    ReturnsFailed,
    ReturnsReport,
    next_weekday,
    run_compute_returns,
)
from apps.returns.config import RETURN_MODELS, SIGNIFICANCE
from apps.returns.models import ReturnResult, ReturnRun
from apps.risk import config as risk_config
from apps.risk.compute import _bars, _manifest
from apps.risk.provider import SilverPriceProvider

pytestmark = pytest.mark.django_db

Q6 = Decimal("0.000001")
Q10 = Decimal("0.0000000001")

INICIO_1 = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
FIM_1 = datetime(2026, 10, 3, 12, 0, 1, tzinfo=UTC)
INICIO_2 = datetime(2026, 10, 3, 18, 30, tzinfo=UTC)
FIM_2 = datetime(2026, 10, 3, 18, 30, 1, tzinfo=UTC)

SEXTA = date(2026, 10, 2)
QUARTA = date(2026, 9, 30)
SABADO = date(2026, 10, 3)
DOMINGO = date(2026, 10, 4)
SEGUNDA = date(2026, 10, 5)


def relogio(*instantes: datetime) -> Callable[[], datetime]:
    """Um `now()` que devolve os instantes na ordem, repetindo o ultimo."""
    restantes = list(instantes)

    def agora() -> datetime:
        return restantes.pop(0) if len(restantes) > 1 else restantes[0]

    return agora


def dias_uteis(quantidade: int, fim: date = SEXTA) -> list[date]:
    """`quantidade` dias uteis consecutivos terminando em `fim`, em ordem crescente."""
    datas: list[date] = []
    dia = fim
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia -= timedelta(days=1)
    return sorted(datas)


def precos(quantidade: int, *, semente: int = 7) -> list[Decimal]:
    rng = np.random.default_rng(semente)
    nivel = 100.0
    valores = [Decimal("100.000000")]
    for retorno in rng.normal(0, 0.01, quantidade - 1):
        nivel *= math.exp(float(retorno))
        valores.append(Decimal(str(nivel)).quantize(Q6))
    return valores


def collection_run() -> CollectionRun:
    return CollectionRun.objects.create(source="teste", started_at=INICIO_1)


def cria_ativo(ticker: str, *, status: str = Asset.Status.ACTIVE) -> Asset:
    return Asset.objects.create(
        ticker=ticker,
        kind=Asset.Kind.STOCK,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=f"{ticker}.SA",
        created_at=INICIO_1,
        updated_at=INICIO_1,
    )


def cria_serie(
    asset: Asset,
    quantidade: int,
    *,
    datas: list[date] | None = None,
    run_da_ultima: CollectionRun | None = None,
) -> list[Price]:
    """`quantidade` pregoes. `run_da_ultima` desloca so a linha de maior data."""
    dias = datas if datas is not None else dias_uteis(quantidade)
    coleta = collection_run()
    linhas = []
    for i, (dia, adj) in enumerate(zip(dias, precos(quantidade), strict=True)):
        ultima = i == quantidade - 1
        linhas.append(
            Price(
                asset=asset,
                date=dia,
                open=adj,
                high=adj,
                low=adj,
                close=adj,
                adj_close=adj,
                volume=1000,
                log_return=None,
                run=run_da_ultima if (ultima and run_da_ultima) else coleta,
                updated_at=INICIO_1,
            )
        )
    return Price.objects.bulk_create(linhas)


def com_serie(ticker: str, quantidade: int = risk_config.MIN_SESSIONS) -> Asset:
    asset = cria_ativo(ticker)
    cria_serie(asset, quantidade)
    return asset


def q(x: float) -> Decimal:
    return Decimal(repr(x)).quantize(Q10, rounding=ROUND_HALF_EVEN)


def linhas_gravadas() -> tuple[int, int]:
    return ReturnRun.objects.count(), ReturnResult.objects.count()


def previsao_a_mao(asset: Asset, nome: str) -> tuple[Any, float]:
    """A previsao do motor, chamada a mao sobre a mesma serie e o mesmo corte."""
    bars = _bars(asset)
    returns = fetch_returns(
        SilverPriceProvider(),
        asset.ticker,
        bars[0].date.isoformat(),
        bars[-1].date.isoformat(),
    )
    train = returns.iloc[: risk_config.TRAIN_WINDOW_DAYS]
    test = returns.iloc[risk_config.TRAIN_WINDOW_DAYS :]
    previsao = get_return_model(nome)().forecast(train, test)
    return previsao, previsao.next_value


# --- V-08: a execucao, os dois resultados e o manifesto ---------------------------------------


def test_v08_uma_execucao_e_dois_resultados_com_o_manifesto() -> None:
    asset = cria_ativo("AAA3")
    linhas = cria_serie(asset, 600)
    # a coleta mais nova tocou uma linha do meio, nao a de maior data
    nova = CollectionRun.objects.create(source="teste", started_at=INICIO_2)
    Price.objects.filter(pk=linhas[300].pk).update(run=nova)

    report = run_compute_returns(["AAA3"], now=relogio(INICIO_1, FIM_1))

    assert isinstance(report, ReturnsReport)
    run = ReturnRun.objects.get()
    bars = _bars(asset)
    assert run.asset == asset
    assert (run.calculated_at, run.finished_at) == (INICIO_1, FIM_1)
    assert run.engine_version == version("ruvor-engine")
    assert run.train_window_days == risk_config.TRAIN_WINDOW_DAYS == 252
    assert (run.as_of_date, run.first_price_date) == (bars[-1].date, bars[0].date)
    assert (run.price_count, run.train_count, run.test_count) == (
        600,
        252,
        600 - 1 - 252,
    )
    # o test_count e o do manifesto do risco para as mesmas barras
    assert run.test_count == _manifest(asset, INICIO_1, 42, bars)["test_count"]
    # o price_run e o maior run entre as linhas usadas, nao o da linha de maior data
    assert run.price_run_id == max(b.run_id for b in bars) == nova.pk
    assert bars[-1].run_id != nova.pk
    assert run.requested_by is None
    resultados = list(run.results.order_by("model_name"))
    assert [r.model_name for r in resultados] == ["ar_1", "historical_mean"]
    for r in resultados:
        assert r.error == ""
        assert r.hyperparameters == get_return_model(r.model_name)().hyperparameters
        assert r.direction_days is not None and r.r2_os is not None


def test_v08_com_502_pregoes_o_ativo_e_pulado_e_nao_grava_nada() -> None:
    com_serie("AAA3", risk_config.MIN_SESSIONS - 1)
    report = run_compute_returns(["AAA3"], now=relogio(INICIO_1))
    assert linhas_gravadas() == (0, 0)
    assert report.results[0].skipped
    assert report.results[0].reason == compute_module.SKIPPED_SHORT_SERIES


def test_v08_com_503_pregoes_o_ativo_e_calculado() -> None:
    com_serie("AAA3", risk_config.MIN_SESSIONS)
    run_compute_returns(["AAA3"], now=relogio(INICIO_1, FIM_1))
    assert linhas_gravadas() == (1, 2)


def test_v08_a_falha_na_escrita_do_segundo_resultado_nao_deixa_linha(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    com_serie("AAA3")
    original = ReturnResult.save
    chamadas: list[int] = []

    def save(self: ReturnResult, *args: Any, **kwargs: Any) -> None:
        chamadas.append(1)
        if len(chamadas) == 2:
            raise RuntimeError("escrita do segundo resultado")
        original(self, *args, **kwargs)

    monkeypatch.setattr(ReturnResult, "save", save)
    with pytest.raises(ReturnsFailed) as exc:
        run_compute_returns(["AAA3"], now=relogio(INICIO_1, FIM_1))

    assert len(chamadas) == 2
    assert linhas_gravadas() == (0, 0)
    assert "escrita do segundo resultado" in (exc.value.report.results[0].error or "")


def test_v08_a_falha_de_um_ativo_reverte_so_ele(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    com_serie("AAA3")
    com_serie("BBB3")
    original = compute_module.write_returns

    def write_returns(asset: Asset, *args: Any, **kwargs: Any) -> ReturnRun:
        run = original(asset, *args, **kwargs)
        if asset.ticker == "BBB3":
            raise RuntimeError("depois de escrever")
        return run

    monkeypatch.setattr(compute_module, "write_returns", write_returns)
    with pytest.raises(ReturnsFailed):
        run_compute_returns([], now=relogio(INICIO_1, FIM_1))
    assert list(ReturnRun.objects.values_list("asset__ticker", flat=True)) == ["AAA3"]
    assert ReturnResult.objects.count() == 2


def test_v08_o_modelo_que_falha_grava_error_e_numeros_nulos_e_o_outro_grava(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    com_serie("AAA3")

    def com_erro(
        config: ReturnExperimentConfig, provider: Any
    ) -> ReturnExperimentResult:
        result = run_return_experiment(config, provider)
        runs = [
            ReturnModelResult(model_name=r.model_name, error="explodiu")
            if r.model_name == "ar_1"
            else r
            for r in result.runs
        ]
        return ReturnExperimentResult(config=result.config, runs=runs)

    monkeypatch.setattr(compute_module, "run_return_experiment", com_erro)
    report = run_compute_returns(["AAA3"], now=relogio(INICIO_1, FIM_1))

    falho = ReturnResult.objects.get(model_name="ar_1")
    assert falho.error == "explodiu"
    numeros = [
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
    ]
    assert {campo: getattr(falho, campo) for campo in numeros} == dict.fromkeys(numeros)
    assert falho.hyperparameters == get_return_model("ar_1")().hyperparameters
    outro = ReturnResult.objects.get(model_name="historical_mean")
    assert outro.error == "" and outro.r2_os is not None
    assert report.results[0].failed == 1


def test_v08_return_models_com_nome_fora_do_registry_levanta_antes_de_escrever(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    com_serie("AAA3")
    monkeypatch.setattr(compute_module, "RETURN_MODELS", ("ar_1", "nao_existe"))
    with pytest.raises(ReturnModelsMissing) as exc:
        run_compute_returns(["AAA3"], now=relogio(INICIO_1))
    assert exc.value.models == ["nao_existe"]
    assert linhas_gravadas() == (0, 0)


def test_com_o_registry_vazio_a_lista_literal_denuncia_os_dois(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A lista e `RETURN_MODELS`, literal: com o registry vazio, os dois faltam. Um padrao
    que lesse `list_return_models()` nao denunciaria nada (mutacao 17)."""
    com_serie("AAA3")
    monkeypatch.setattr(compute_module, "load_all_return_model_modules", lambda: None)
    monkeypatch.setattr(compute_module, "list_return_models", lambda: [])
    with pytest.raises(ReturnModelsMissing) as exc:
        run_compute_returns(["AAA3"], now=relogio(INICIO_1))
    assert exc.value.models == list(RETURN_MODELS)
    assert linhas_gravadas() == (0, 0)


def test_return_models_e_a_lista_do_registry_completo() -> None:
    from engine.returns import list_return_models

    load_all_return_model_modules()
    assert sorted(RETURN_MODELS) == list_return_models()
    assert SIGNIFICANCE == Decimal("0.05")


def test_v08_uma_segunda_execucao_nao_muda_a_primeira() -> None:
    com_serie("AAA3")
    run_compute_returns(["AAA3"], now=relogio(INICIO_1, FIM_1))
    antes = list(ReturnRun.objects.values()), list(ReturnResult.objects.values())

    run_compute_returns(["AAA3"], now=relogio(INICIO_2, FIM_2))

    assert linhas_gravadas() == (2, 4)
    primeira_run = ReturnRun.objects.filter(calculated_at=INICIO_1)
    assert list(primeira_run.values()) == antes[0]
    assert list(ReturnResult.objects.filter(run__in=primeira_run).values()) == antes[1]


def test_o_requested_by_e_gravado_quando_passado() -> None:
    com_serie("AAA3")
    usuario = User.objects.create_user(
        email="quem@pediu.com",
        name="Quem Pediu",
        organization=Organization.objects.get(slug="ruvor"),
        password="x" * 12,
    )
    run_compute_returns(["AAA3"], requested_by=usuario, now=relogio(INICIO_1, FIM_1))
    assert ReturnRun.objects.get().requested_by == usuario


def test_o_calculated_at_e_o_mesmo_para_todos_os_ativos_da_chamada() -> None:
    com_serie("AAA3")
    com_serie("BBB3")
    run_compute_returns([], now=relogio(INICIO_1, FIM_1, FIM_2))
    assert set(ReturnRun.objects.values_list("calculated_at", flat=True)) == {INICIO_1}


def test_ticker_inexistente_ou_inativo_aborta_antes_de_escrever() -> None:
    com_serie("AAA3")
    inativo = cria_ativo("OLD3", status=Asset.Status.INACTIVE)
    cria_serie(inativo, risk_config.MIN_SESSIONS)
    with pytest.raises(InvalidTickers) as exc:
        run_compute_returns(["AAA3", "NAO3", "OLD3"], now=relogio(INICIO_1))
    assert exc.value.tickers == ["NAO3", "OLD3"]
    assert linhas_gravadas() == (0, 0)


def test_sem_argumentos_calcula_os_ativos_com_preco_e_pula_o_inativo() -> None:
    com_serie("AAA3")
    inativo = cria_ativo("OLD3", status=Asset.Status.INACTIVE)
    cria_serie(inativo, risk_config.MIN_SESSIONS)
    cria_ativo("SEM3")  # sem preco: nao e candidato
    report = run_compute_returns([], now=relogio(INICIO_1, FIM_1))
    assert [(r.ticker, r.skipped) for r in report.results] == [
        ("AAA3", False),
        ("OLD3", True),
    ]
    assert list(ReturnRun.objects.values_list("asset__ticker", flat=True)) == ["AAA3"]
    assert "retorno: 2 ativos, 1 ok, 0 falhos, 1 pulados" in report.render()


# --- V-09: o veredito sobre o p quantizado ----------------------------------------------------


def _avaliacao(dm_p: float | None, pt_p: float | None) -> ReturnEvaluation:
    return ReturnEvaluation(
        mse=0.0001,
        mse_reference=0.00011,
        r2_os=0.0909090909,
        direction_days=240,
        hit_rate=0.55,
        up_share=0.52,
        forecast_up_share=0.6,
        dm_statistic=1.7,
        dm_p_value=dm_p,
        cw_statistic=1.9,
        cw_p_value=0.03,
        pt_statistic=0.4 if pt_p is not None else None,
        pt_p_value=pt_p,
    )


def _com_avaliacao(monkeypatch: pytest.MonkeyPatch, ev: ReturnEvaluation) -> None:
    monkeypatch.setattr("engine.returns.runner.evaluate", lambda realized, forecast: ev)


@pytest.mark.parametrize(
    ("dm_p", "pt_p", "gravado", "beats", "skill"),
    [
        (0.049, 0.5, Decimal("0.0490000000"), True, False),
        (0.05, 0.5, Decimal("0.0500000000"), False, False),
        (None, 0.5, None, False, False),
        # quantiza primeiro, decide depois: o float cru seria < 0,05
        (0.04999999999996, 0.5, Decimal("0.0500000000"), False, False),
        (0.5, 0.01, Decimal("0.5000000000"), False, True),
        (0.5, 0.05, Decimal("0.5000000000"), False, False),
        (0.01, None, Decimal("0.0100000000"), True, None),
    ],
)
def test_v09_o_veredito_da_tabela_do_rf09(
    monkeypatch: pytest.MonkeyPatch,
    dm_p: float | None,
    pt_p: float | None,
    gravado: Decimal | None,
    beats: bool,
    skill: bool | None,
) -> None:
    com_serie("AAA3")
    _com_avaliacao(monkeypatch, _avaliacao(dm_p, pt_p))
    run_compute_returns(["AAA3"], now=relogio(INICIO_1, FIM_1))
    for r in ReturnResult.objects.all():
        assert r.dm_p_value == gravado
        assert r.beats_reference is beats
        assert r.direction_skill is skill


def test_v09_com_error_os_dois_vereditos_sao_nulos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    com_serie("AAA3")

    def tudo_falha(
        config: ReturnExperimentConfig, provider: Any
    ) -> ReturnExperimentResult:
        return ReturnExperimentResult(
            config=config,
            runs=[
                ReturnModelResult(model_name=n, error="x") for n in config.model_names
            ],
        )

    monkeypatch.setattr(compute_module, "run_return_experiment", tudo_falha)
    run_compute_returns(["AAA3"], now=relogio(INICIO_1, FIM_1))
    assert list(
        ReturnResult.objects.values_list("beats_reference", "direction_skill")
    ) == [(None, None), (None, None)]


# --- V-13: a previsao do proximo pregao, gravada ---------------------------------------------


@pytest.mark.parametrize(
    ("as_of", "esperado"),
    [
        (SEXTA, SEGUNDA),
        (QUARTA, date(2026, 10, 1)),
        (SABADO, SEGUNDA),
        (DOMINGO, SEGUNDA),
    ],
)
def test_v13_next_weekday(as_of: date, esperado: date) -> None:
    assert next_weekday(as_of) == esperado


def test_v13_next_forecast_e_o_next_value_quantizado_e_a_data_da_sexta() -> None:
    asset = com_serie("AAA3")  # o ultimo pregao e a sexta 2026-10-02
    run_compute_returns(["AAA3"], now=relogio(INICIO_1, FIM_1))
    run = ReturnRun.objects.get()
    assert run.as_of_date == SEXTA
    for r in run.results.all():
        _, proximo = previsao_a_mao(asset, r.model_name)
        assert r.next_forecast == q(proximo)
        assert r.next_forecast_date == SEGUNDA


def test_v13_a_data_com_o_ultimo_pregao_num_sabado() -> None:
    asset = cria_ativo("AAA3")
    datas = [*dias_uteis(risk_config.MIN_SESSIONS - 1, fim=SEXTA), SABADO]
    cria_serie(asset, risk_config.MIN_SESSIONS, datas=datas)
    run_compute_returns(["AAA3"], now=relogio(INICIO_1, FIM_1))
    assert set(ReturnResult.objects.values_list("next_forecast_date", flat=True)) == {
        SEGUNDA
    }


def test_v13_a_previsao_vai_a_coluna_ja_quantizada() -> None:
    """O `Decimal` que vai a coluna tem 10 casas antes do banco: o `float` cru seria
    arredondado por outra regra, na conversao do Django."""
    evaluation = _avaliacao(0.3, 0.3)
    run = ReturnModelResult(
        model_name="ar_1", evaluation=evaluation, next_value=0.000123456789012345
    )
    campos = compute_module._fields(run, SEXTA)
    previsao = campos["next_forecast"]
    assert isinstance(previsao, Decimal)
    assert previsao == Decimal("0.0001234568")
    assert previsao.as_tuple().exponent == -10
    assert campos["next_forecast_date"] == SEGUNDA
    falho = compute_module._fields(replace(run, error="x"), SEXTA)
    assert (falho["next_forecast"], falho["next_forecast_date"]) == (None, None)


def test_o_q_aceita_np_float64_e_quantiza_como_o_float() -> None:
    """O motor pode devolver `np.float64` (revisao de implementacao da T3): quantiza sem
    levantar, igual ao `float` do mesmo valor."""
    assert compute_module._q(np.float64(0.000123456789012345)) == Decimal(
        "0.0001234568"
    )
    assert compute_module._q(np.float64(0.05)) == q(0.05) == Decimal("0.0500000000")
    assert compute_module._q(None) is None
