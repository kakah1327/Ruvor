"""`run_compute_metrics` contra o banco: selecao, transacao, imutabilidade e relatorio.

Cobre V-04, V-09b, V-12, V-13, V-14, V-20, V-21, V-22 e V-23, mais os dois ramos que o
plano acrescenta: ticker explicito de ativo `active` sem nenhum preco, e menos de 30 pares
no emparelhamento com a janela de 60 meses existindo.

**O que se confere aqui nao e numero de metrica** -- isso e do `test_metrics.py`, contra
valor escrito a mao. Aqui se confere o que so aparece com banco: quem entra no laco, o que
a transacao reverte, o que fica nulo na coluna e o que sai no relatorio.

As series sao **mensais**, nao diarias: a janela de N meses olha datas de calendario, e uma
serie mensal de 129 pregoes exerce as mesmas fronteiras que dez anos de pregao diario sem
criar 2.500 linhas por ativo. O `adj_close` cresce de um em um a partir de 100, e o
`log_return` de cada linha e `ln(adj/anterior)` -- calculado no proprio teste, nunca pelo
codigo sob teste.

O IBOV nasce da migration `assets.0002_ibovespa`: os testes o buscam, nao o criam, e o
V-20 o **apaga** para provar a ausencia.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import NoReturn

import pytest
from django.utils import timezone

import apps.analytics.compute as compute_module
from apps.analytics.compute import (
    AssetResult,
    InvalidTickers,
    MetricsFailed,
    MetricsReport,
    run_compute_metrics,
    write_metrics,
)
from apps.analytics.metrics import Bar, Metrics
from apps.analytics.models import BehaviorMetric, ReturnHistogramBin, StressEpisode
from apps.analytics.stress import EpisodeResult, compute_stress
from apps.assets.models import Asset, CollectionRun, CorporateEvent, Price

pytestmark = pytest.mark.django_db

Q10 = Decimal("0.0000000001")

# Relogio fixo das execucoes: duas datas distintas, porque `(asset, calculated_at)` e unico
# e duas execucoes no mesmo instante colidiriam.
RUN_1 = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
RUN_2 = datetime(2026, 9, 23, 18, 30, tzinfo=UTC)

DIA = 15  # todas as series caem no dia 15, para a janela de N meses bater exato


def meses(ano: int, mes: int, quantidade: int) -> list[date]:
    """`quantidade` datas mensais consecutivas, dia 15, a partir de `(ano, mes)`."""
    datas = []
    for i in range(quantidade):
        total = ano * 12 + (mes - 1) + i
        y, m = divmod(total, 12)
        datas.append(date(y, m + 1, DIA))
    return datas


# 129 meses de 2016-01-15 a 2026-09-15: toda janela de retorno existe, a de 60 meses tem
# 61 pregoes (60 observacoes) e a de 252 pregoes de volume nao existe.
SERIE_LONGA = meses(2016, 1, 129)
AS_OF = SERIE_LONGA[-1]
assert AS_OF == date(2026, 9, 15)

# 37 meses de 2023-09-15 a 2026-09-15: o ativo de tres anos do V-09/V-09b. A janela de 36
# meses existe; a de 60 e a de 120, nao.
SERIE_TRES_ANOS = meses(2023, 9, 37)

# Um pregao velho o bastante para a janela de 60 meses existir (2021-09-15 e a fronteira),
# e 20 mensais recentes: 20 pares no emparelhamento, abaixo do minimo de 30.
SERIE_ESPARSA = [date(2021, 5, DIA), *meses(2025, 2, 20)]


def collection_run() -> CollectionRun:
    return CollectionRun.objects.create(source="teste", started_at=timezone.now())


def make_asset(
    ticker: str,
    *,
    status: str = Asset.Status.ACTIVE,
    kind: str = Asset.Kind.STOCK,
) -> Asset:
    """Um ativo do catalogo. `kind` e parametro por causa do V-14, que precisa de um
    **segundo** indice: com um so, `.get(kind="index")` e `.get(ticker="IBOV")` devolvem
    a mesma linha e a mutacao do acessor passa verde."""
    now = timezone.now()
    return Asset.objects.create(
        ticker=ticker,
        kind=kind,
        name=f"{ticker} S.A.",
        trading_name=ticker,
        status=status,
        provider_symbol=f"{ticker}.SA",
        created_at=now,
        updated_at=now,
    )


def make_prices(asset: Asset, datas: list[date], *, passo: int = 1) -> None:
    """Serie crescente: `adj_close` 100, 100+passo, 100+2*passo... e `log_return` =
    ln(adj/anterior).

    O primeiro pregao fica com `log_return` nulo, como o `import_prices` grava.

    `passo` existe para o segundo indice do V-14: com o passo padrao a serie dele seria
    identica a do IBOV, trocar o benchmark nao mudaria beta nenhum, e a acao deixaria de
    dar sinal.
    """
    run = collection_run()
    now = timezone.now()
    anterior: Decimal | None = None
    linhas = []
    for i, d in enumerate(datas):
        adj = Decimal(100 + i * passo)
        log_return = None if anterior is None else (adj / anterior).ln().quantize(Q10)
        linhas.append(
            Price(
                asset=asset,
                date=d,
                open=adj,
                high=adj,
                low=adj,
                close=adj,
                adj_close=adj,
                volume=1000 + i,
                log_return=log_return,
                run=run,
                updated_at=now,
            )
        )
        anterior = adj
    Price.objects.bulk_create(linhas)


def ibov(*, com_preco: bool = True) -> Asset:
    """O IBOV da migration. Ganha a mesma serie longa, para o emparelhamento existir."""
    asset = Asset.objects.get(ticker="IBOV")
    if com_preco:
        make_prices(asset, SERIE_LONGA)
    return asset


def com_serie_longa(ticker: str) -> Asset:
    asset = make_asset(ticker)
    make_prices(asset, SERIE_LONGA)
    return asset


def linha(ticker: str) -> BehaviorMetric:
    return BehaviorMetric.objects.get(asset__ticker=ticker)


def resultado(report: MetricsReport, ticker: str) -> AssetResult:
    return next(r for r in report.results if r.ticker == ticker)


def snapshot(metric: BehaviorMetric) -> dict[str, object]:
    """Todos os campos da linha, inclusive a chave: e o "campo a campo" do V-04."""
    return {f.attname: getattr(metric, f.attname) for f in BehaviorMetric._meta.fields}


# --- V-13: ticker invalido nao escreve nada -------------------------------------------


def test_v13_ticker_inexistente_aborta_antes_de_qualquer_escrita() -> None:
    ibov()
    com_serie_longa("AAA3")

    with pytest.raises(InvalidTickers) as info:
        run_compute_metrics(["AAA3", "XPTO9"])

    assert info.value.tickers == ["XPTO9"]
    assert BehaviorMetric.objects.count() == 0
    assert ReturnHistogramBin.objects.count() == 0


def test_v13_ticker_inativo_tambem_aborta_e_nao_escreve() -> None:
    ibov()
    inativo = make_asset("BAZZ4", status=Asset.Status.INACTIVE)
    make_prices(inativo, SERIE_LONGA)

    with pytest.raises(InvalidTickers) as info:
        run_compute_metrics(["BAZZ4"])

    assert info.value.tickers == ["BAZZ4"]
    assert BehaviorMetric.objects.count() == 0


# --- V-21: os tres casos da selecao sem argumentos ------------------------------------


def test_v21_sem_argumentos_processa_ativo_pula_inativo_e_ignora_sem_preco() -> None:
    ibov()
    com_serie_longa("AAA3")
    inativo = make_asset("BAZZ4", status=Asset.Status.INACTIVE)
    make_prices(inativo, SERIE_LONGA)
    make_asset("SEMP3")  # ativo, sem nenhuma linha em silver.price

    report = run_compute_metrics([])

    tickers = [r.ticker for r in report.results]
    # o IBOV tambem e candidato: tem preco e esta ativo.
    assert tickers == ["AAA3", "IBOV", "BAZZ4"]
    assert "SEMP3" not in report.render()
    assert resultado(report, "BAZZ4").skipped
    assert resultado(report, "BAZZ4").reason == "inativo"
    assert not resultado(report, "AAA3").skipped
    assert set(BehaviorMetric.objects.values_list("asset__ticker", flat=True)) == {
        "AAA3",
        "IBOV",
    }


# --- o ramo que o plano acrescenta: ticker explicito de ativo sem preco ---------------


def test_ticker_explicito_de_ativo_sem_preco_e_pulado_sem_linha_em_gold() -> None:
    ibov()
    make_asset("XPTO9")  # ativo, `active`, sem preco nenhum

    report = run_compute_metrics(["XPTO9"])

    assert resultado(report, "XPTO9").skipped
    assert resultado(report, "XPTO9").reason == "sem preco"
    assert BehaviorMetric.objects.count() == 0
    assert ReturnHistogramBin.objects.count() == 0
    # Nada de "informe tickers" a quem acabou de informar um.
    assert report.render() == (
        "XPTO9              0 pregoes  -               pulado: sem preco"
    )


def test_sem_argumentos_e_sem_candidato_pede_tickers() -> None:
    inativo = make_asset("BAZZ4", status=Asset.Status.INACTIVE)
    make_prices(inativo, SERIE_LONGA)

    report = run_compute_metrics([])

    assert report.render().splitlines()[-1] == (
        "nenhum ativo ativo com preco; informe tickers"
    )
    assert BehaviorMetric.objects.count() == 0


# --- V-04 e V-22: recalcular insere linha nova, com os baldes dela --------------------


def test_v04_duas_execucoes_dao_duas_linhas_e_a_primeira_fica_intacta() -> None:
    ibov()
    com_serie_longa("AAA3")

    run_compute_metrics(["AAA3"], now=lambda: RUN_1)
    primeira = linha("AAA3")
    antes = snapshot(primeira)

    run_compute_metrics(["AAA3"], now=lambda: RUN_2)

    linhas = list(BehaviorMetric.objects.filter(asset__ticker="AAA3").order_by("id"))
    assert len(linhas) == 2
    assert [m.calculated_at for m in linhas] == [RUN_1, RUN_2]
    depois = snapshot(BehaviorMetric.objects.get(pk=primeira.pk))
    assert depois == antes


def test_v22_os_baldes_nao_atravessam_execucoes() -> None:
    ibov()
    com_serie_longa("AAA3")

    run_compute_metrics(["AAA3"], now=lambda: RUN_1)
    run_compute_metrics(["AAA3"], now=lambda: RUN_2)

    linhas = list(BehaviorMetric.objects.filter(asset__ticker="AAA3").order_by("id"))
    for metric in linhas:
        baldes = ReturnHistogramBin.objects.filter(metric=metric)
        assert baldes.count() == 42
        assert set(baldes.values_list("bin_index", flat=True)) == set(range(42))
    assert ReturnHistogramBin.objects.count() == 84

    # O balde nao tem vida propria: apagar a metrica leva os 42 dela, e so os dela. O
    # `CASCADE` e implementado pelo Django em Python e nao aparece no DDL -- por isso a
    # prova e aqui, e nao no `psql`.
    linhas[0].delete()
    assert ReturnHistogramBin.objects.count() == 42
    assert set(ReturnHistogramBin.objects.values_list("metric_id", flat=True)) == {
        linhas[1].pk
    }


# --- V-12: uma transacao por ativo ----------------------------------------------------


def test_v12_escrita_que_levanta_no_segundo_reverte_so_ele(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ibov()
    for ticker in ("AAA3", "BBB3", "CCC3"):
        com_serie_longa(ticker)
    vistos: list[str] = []

    def fake_write(
        asset: Asset,
        calculated_at: datetime,
        metrics: Metrics,
        stress: list[EpisodeResult],
    ) -> BehaviorMetric:
        vistos.append(asset.ticker)
        if asset.ticker != "BBB3":
            return write_metrics(asset, calculated_at, metrics, stress)
        # grava a linha e os 42 baldes e so entao levanta: sem isso nao haveria o que
        # reverter, e o teste passaria verde com a transacao no lugar errado.
        write_metrics(asset, calculated_at, metrics, stress)
        raise RuntimeError("gravacao quebrou depois da linha e dos baldes")

    monkeypatch.setattr("apps.analytics.compute.write_metrics", fake_write)
    assert compute_module.write_metrics is fake_write

    with pytest.raises(MetricsFailed) as info:
        run_compute_metrics(["AAA3", "BBB3", "CCC3"], now=lambda: RUN_1)

    report = info.value.report
    assert vistos == ["AAA3", "BBB3", "CCC3"]
    assert resultado(report, "BBB3").error == (
        "RuntimeError: gravacao quebrou depois da linha e dos baldes"
    )
    assert resultado(report, "AAA3").error is None
    assert resultado(report, "CCC3").error is None
    # o primeiro e o terceiro ficam gravados, com os baldes; o segundo nao deixa rastro
    assert set(BehaviorMetric.objects.values_list("asset__ticker", flat=True)) == {
        "AAA3",
        "CCC3",
    }
    assert ReturnHistogramBin.objects.count() == 84


# --- V-14 e V-20: o indice, presente e ausente ----------------------------------------


def test_v14_o_ibovespa_nao_tem_beta_consigo_mesmo() -> None:
    # O cenario tem **dois** ativos `kind="index"`, e o segundo nao e enfeite: com um so,
    # `.get(kind=Asset.Kind.INDEX)` e `.get(ticker="IBOV")` devolvem a mesma linha e
    # a mutacao do acessor passa verde. Com dois, ela levanta `MultipleObjectsReturned`.
    # A serie do segundo sobe de tres em tres, e por isso os log-retornos dele nao sao os
    # do IBOV: trocar o benchmark muda o beta de quem for comparado contra ele.
    ibov()
    segundo_indice = make_asset("IBXX", kind=Asset.Kind.INDEX)
    make_prices(segundo_indice, SERIE_LONGA, passo=3)
    com_serie_longa("AAA3")

    report = run_compute_metrics(["AAA3", "IBOV", "IBXX"], now=lambda: RUN_1)

    metric = linha("IBOV")
    assert metric.beta_60m is None
    assert metric.correlation_60m is None
    assert metric.benchmark_observations is None
    # o resto foi calculado: nulo ali e identidade, nao lacuna
    assert metric.statistical_observations == 60
    assert metric.volatility_60m is not None
    # e por ser identidade, nao entra em `null_columns` -- a linha do IBOV nao traz
    # "(nulas: beta_60m, ...)".
    assert resultado(report, "IBOV").null_columns == ["avg_volume_252d"]
    assert not report.benchmark_missing
    assert "aviso:" not in report.render()

    # A acao e quem da o sinal do benchmark trocado. A serie dela e a do IBOV sao a
    # mesma serie, entao a regressao e de x contra x: beta 1 e correlacao 1, exatos e
    # analiticos. Contra o segundo indice -- log-retornos ln((100+3i)/(97+3i)), que nao
    # sao proporcionais a ln((100+i)/(99+i)) -- nenhum dos dois valores se repete.
    acao = linha("AAA3")
    assert acao.beta_60m == Decimal("1.0000000000")
    assert acao.correlation_60m == Decimal("1.0000000000")
    assert acao.benchmark_observations == 60
    assert resultado(report, "AAA3").null_columns == ["avg_volume_252d"]

    # E o segundo indice **nao** e o Ibovespa: ele tem beta, porque quem escolhe o
    # benchmark e o ticker, nunca o `kind`.
    outro = linha("IBXX")
    assert outro.benchmark_observations == 60
    assert outro.beta_60m is not None
    assert outro.correlation_60m is not None


def test_v20_banco_sem_ibovespa_grava_a_linha_e_avisa() -> None:
    com_serie_longa("PETR4")
    Asset.objects.filter(ticker="IBOV").delete()

    report = run_compute_metrics(["PETR4"], now=lambda: RUN_1)

    metric = linha("PETR4")
    assert metric.beta_60m is None
    assert metric.correlation_60m is None
    assert metric.benchmark_observations is None
    assert metric.statistical_observations == 60  # o resto foi calculado
    assert report.benchmark_missing
    assert resultado(report, "PETR4").null_columns == ["avg_volume_252d"]
    assert report.render().splitlines()[-2] == (
        "aviso: IBOV sem preco — beta e correlacao nulos em todos os ativos"
    )


def test_ibovespa_existente_mas_sem_preco_tambem_e_ausencia() -> None:
    com_serie_longa("PETR4")  # o IBOV da migration fica sem nenhuma linha de preco

    report = run_compute_metrics(["PETR4"], now=lambda: RUN_1)

    assert report.benchmark_missing
    assert linha("PETR4").benchmark_observations is None


# --- V-09b: janela estatistica inexistente grava NULL, nunca 0 ------------------------


def test_v09b_tres_anos_gravam_nulo_nas_sete_colunas_e_42_baldes_zerados() -> None:
    ibov()
    curto = make_asset("XPTO3")
    make_prices(curto, SERIE_TRES_ANOS)

    report = run_compute_metrics(["XPTO3"], now=lambda: RUN_1)

    metric = linha("XPTO3")
    assert metric.statistical_observations is None  # NULL, nunca 0
    assert metric.volatility_60m is None
    assert metric.skewness is None
    assert metric.excess_kurtosis is None
    assert metric.beta_60m is None
    assert metric.correlation_60m is None
    assert metric.benchmark_observations is None
    assert metric.return_120m is None
    assert metric.return_36m is not None  # a de 36 meses existe
    assert metric.price_count == 37
    assert metric.first_price_date == date(2023, 9, 15)

    baldes = ReturnHistogramBin.objects.filter(metric=metric)
    assert baldes.count() == 42
    assert sum(b.count for b in baldes) == 0

    # com indice presente, o nulo das tres colunas do benchmark e falta de historico e
    # aparece no relatorio.
    assert resultado(report, "XPTO3").null_columns == [
        "return_60m",
        "return_120m",
        "volatility_60m",
        "beta_60m",
        "correlation_60m",
        "benchmark_observations",
        "skewness",
        "excess_kurtosis",
        "statistical_observations",
        "avg_volume_252d",
    ]


# --- o ramo que o plano acrescenta: menos de 30 pares, com a janela existindo ---------


def test_menos_de_30_pares_zera_beta_mas_grava_a_contagem_real() -> None:
    ibov()
    esparso = make_asset("RARO3")
    make_prices(esparso, SERIE_ESPARSA)

    report = run_compute_metrics(["RARO3"], now=lambda: RUN_1)

    metric = linha("RARO3")
    assert metric.statistical_observations == 20  # a janela de 60 meses existe
    assert metric.volatility_60m is not None
    assert metric.beta_60m is None
    assert metric.correlation_60m is None
    assert metric.benchmark_observations == 20  # a contagem real, nunca nulo
    # `return_120m` e nulo porque a serie esparsa comeca em 2021; `beta_60m` e
    # `correlation_60m` sao nulos por falta de pares, e por isso entram -- mas
    # `benchmark_observations`, preenchido, nao entra.
    assert resultado(report, "RARO3").null_columns == [
        "return_120m",
        "beta_60m",
        "correlation_60m",
        "avg_volume_252d",
    ]


# --- V-23: o formato do relatorio -----------------------------------------------------

# As strings abaixo sao escritas a mao, no formato do exemplo da spec ("O comando"): mesmo
# alinhamento 12/8/14, mesma cauda, mesmo resumo. Nao sao o exemplo em si -- os 2.490
# pregoes dele nenhum teste monta -- e nenhuma e derivada do codigo sob teste. O relatorio
# e construido direto, com `elapsed` fixo, para a comparacao ser deterministica.

RELATORIO_COMPLETO = (
    "AAA3             120 pregoes  ate 2026-09-15  ok\n"
    "BBB3             120 pregoes  ate 2026-09-15  ok  (nulas: return_120m)\n"
    "CCC3              12 pregoes  ate 2026-09-15  ok  (nulas: return_1m, return_3m)\n"
    "DDD3               0 pregoes  -               pulado: inativo\n"
    "metricas: 4 ativos, 3 ok, 0 falhos, 1 pulados, 1.2s"
)

RELATORIO_COM_AVISO_E_FALHA = (
    "AAA3             120 pregoes  ate 2026-09-15  ok\n"
    "BBB3             120 pregoes  ate 2026-09-15  FALHOU (RuntimeError: quebrou)\n"
    "EEE3               0 pregoes  -               pulado: sem preco\n"
    "aviso: IBOV sem preco — beta e correlacao nulos em todos os ativos\n"
    "metricas: 3 ativos, 1 ok, 1 falhos, 1 pulados, 0.4s"
)


def test_v23_o_relatorio_tem_o_formato_da_spec() -> None:
    report = MetricsReport(
        [
            AssetResult("AAA3", 120, AS_OF, [], None, False),
            AssetResult("BBB3", 120, AS_OF, ["return_120m"], None, False),
            AssetResult("CCC3", 12, AS_OF, ["return_1m", "return_3m"], None, False),
            AssetResult("DDD3", 0, None, [], None, True, "inativo"),
        ],
        1.2,
    )

    assert report.render() == RELATORIO_COMPLETO
    assert not report.failed


def test_v23_o_aviso_do_indice_e_a_linha_de_falha() -> None:
    report = MetricsReport(
        [
            AssetResult("AAA3", 120, AS_OF, [], None, False),
            AssetResult("BBB3", 120, AS_OF, [], "RuntimeError: quebrou", False),
            AssetResult("EEE3", 0, None, [], None, True, "sem preco"),
        ],
        0.4,
        benchmark_missing=True,
    )

    assert report.render() == RELATORIO_COM_AVISO_E_FALHA
    assert report.failed


def test_v23_o_resumo_conta_os_pulados_no_total() -> None:
    # Divergencia declarada em relacao ao molde: `PricesReport` conta so os nao-pulados.
    report = MetricsReport(
        [AssetResult("DDD3", 0, None, [], None, True, "inativo")], 0.1
    )
    assert report.render().splitlines()[-1] == (
        "nenhum ativo ativo com preco; informe tickers"
    )

    com_um_ok = MetricsReport(
        [
            AssetResult("AAA3", 120, AS_OF, [], None, False),
            AssetResult("DDD3", 0, None, [], None, True, "inativo"),
        ],
        0.1,
    )
    assert com_um_ok.render().splitlines()[-1] == (
        "metricas: 2 ativos, 1 ok, 0 falhos, 1 pulados, 0.1s"
    )


# --- dividendo com `amount` nulo nao entra na soma ------------------------------------


def test_dividendo_sem_valor_e_descartado_ao_montar_a_lista() -> None:
    ibov()
    asset = com_serie_longa("AAA3")
    run = collection_run()
    CorporateEvent.objects.create(
        asset=asset,
        date=date(2026, 6, 15),
        kind=CorporateEvent.Kind.DIVIDEND,
        amount=Decimal("2.500000"),
        run=run,
    )
    CorporateEvent.objects.create(
        asset=asset,
        date=date(2026, 7, 15),
        kind=CorporateEvent.Kind.DIVIDEND,
        amount=None,
        run=run,
    )

    run_compute_metrics(["AAA3"], now=lambda: RUN_1)

    metric = linha("AAA3")
    assert metric.dividend_payments_12m == 1
    assert metric.dividends_12m == Decimal("2.500000")


# --- M3.3: os episodios de estresse, na mesma transacao (V-05) ------------------------


def episodios(metric: BehaviorMetric) -> list[StressEpisode]:
    return list(StressEpisode.objects.filter(metric=metric).order_by("start_date"))


def campos(episodio: StressEpisode) -> dict[str, object]:
    return {f.attname: getattr(episodio, f.attname) for f in StressEpisode._meta.fields}


def test_m33_uma_linha_por_episodio_com_a_definicao_copiada() -> None:
    ibov()
    com_serie_longa("AAA3")

    run_compute_metrics(["AAA3", "IBOV"], now=lambda: RUN_1)

    # As datas escritas aqui sao as da D-147, nao lidas de `EPISODES`.
    esperado = [
        ("jbs_2017", date(2017, 5, 17), date(2017, 6, 30)),
        ("truckers_2018", date(2018, 5, 18), date(2018, 6, 29)),
        ("covid_2020", date(2020, 2, 21), date(2020, 3, 31)),
        ("rates_2021", date(2021, 6, 7), date(2022, 7, 14)),
    ]
    acao = episodios(linha("AAA3"))
    assert [(e.episode, e.start_date, e.end_date) for e in acao] == esperado
    # A serie e mensal, no dia 15: o ciclo de juros comeca em 2021-06-07 e a base e
    # 2021-05-15, 23 dias antes -- `stale_start`. Os outros tres tem base a menos de 10.
    assert [e.missing for e in acao] == [None, None, None, "stale_start"]
    com_dado, juros = acao[:3], acao[3]
    # A serie sobe sempre: queda zero.
    assert all(e.drawdown == 0 for e in com_dado)
    # A acao e o IBOV tem a mesma serie: o indice do recorte e o retorno da propria acao.
    assert all(e.benchmark_period_return is not None for e in com_dado)
    assert all(e.benchmark_period_return == e.period_return for e in com_dado)
    # No ciclo de juros o indice tambem tem base velha: as tres dele, nulas.
    assert juros.period_return is None
    assert juros.benchmark_period_return is None

    # No proprio IBOV as tres do indice sao nulas: nao se compara consigo mesmo.
    indice = episodios(linha("IBOV"))
    assert len(indice) == 4
    assert [e.missing for e in indice] == [None, None, None, "stale_start"]
    assert all(e.benchmark_period_return is None for e in indice)
    assert all(e.benchmark_drawdown is None for e in indice)
    assert all(e.benchmark_recovery_sessions is None for e in indice)


def test_m33_recalcular_nao_muda_os_episodios_antigos() -> None:
    ibov()
    com_serie_longa("AAA3")

    run_compute_metrics(["AAA3"], now=lambda: RUN_1)
    primeira = linha("AAA3")
    antes = [campos(e) for e in episodios(primeira)]

    run_compute_metrics(["AAA3"], now=lambda: RUN_2)

    depois = [campos(e) for e in episodios(BehaviorMetric.objects.get(pk=primeira.pk))]
    assert depois == antes
    assert StressEpisode.objects.count() == 8


def test_m33_falha_na_escrita_do_estresse_nao_deixa_metrica_nem_baldes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ibov()
    com_serie_longa("AAA3")

    def quebra(*args: object, **kwargs: object) -> NoReturn:
        raise RuntimeError("estresse quebrou")

    # Depois da linha e dos 42 baldes ja escritos: so o `atomic` os desfaz.
    monkeypatch.setattr(StressEpisode.objects, "bulk_create", quebra)

    with pytest.raises(MetricsFailed) as info:
        run_compute_metrics(["AAA3"], now=lambda: RUN_1)

    assert (
        resultado(info.value.report, "AAA3").error == "RuntimeError: estresse quebrou"
    )
    assert BehaviorMetric.objects.count() == 0
    assert ReturnHistogramBin.objects.count() == 0
    assert StressEpisode.objects.count() == 0


def test_m33_excecao_no_calculo_do_estresse_falha_so_o_ativo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ibov()
    for ticker in ("AAA3", "BBB3", "CCC3"):
        com_serie_longa(ticker)
    original = compute_stress
    chamadas: list[int] = []

    def estresse_que_falha_no_segundo(
        bars: list[Bar], benchmark: list[Bar] | None, calendar: list[Bar] | None
    ) -> list[EpisodeResult]:
        # As tres series sao iguais; o segundo ativo do laco, em ordem de ticker, e o BBB3.
        chamadas.append(1)
        if len(chamadas) == 2:
            raise RuntimeError("calculo do estresse quebrou")
        return original(bars, benchmark, calendar)

    monkeypatch.setattr(
        "apps.analytics.compute.compute_stress", estresse_que_falha_no_segundo
    )

    with pytest.raises(MetricsFailed) as info:
        run_compute_metrics(["AAA3", "BBB3", "CCC3"], now=lambda: RUN_1)

    report = info.value.report
    assert resultado(report, "BBB3").error == (
        "RuntimeError: calculo do estresse quebrou"
    )
    assert resultado(report, "AAA3").error is None
    assert resultado(report, "CCC3").error is None
    assert set(BehaviorMetric.objects.values_list("asset__ticker", flat=True)) == {
        "AAA3",
        "CCC3",
    }
    assert StressEpisode.objects.count() == 8
