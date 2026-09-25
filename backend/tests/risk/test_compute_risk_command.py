"""`manage.py compute_risk`: a casca entrega o relatorio, converte as falhas e passa as
duas opcoes adiante.

Todos os casos rodam **pela casca**, com `call_command`, e nunca chamando
`run_compute_risk` direto: o M1.2 registrou como lacuna ter testado o `--full` do
`import_prices` so por dentro, onde trocar o argumento passado pela casca nao reprovaria
nada. Aqui, quem desligasse a ligacao entre o comando e o calculo -- ou trocasse
`seed=seed` por `seed=None` -- veria estes testes falharem.

**Nenhuma rede e treinada aqui**: todo caso usa `--model` com modelo barato. O custo dos
nove e pago uma vez pelo V-20, em `test_compute.py`; o que se prova neste arquivo e a
casca.

A serie e sintetica e diaria, com os 503 pregoes do piso do RF-10b -- abaixo dele o ativo
seria pulado e nao haveria execucao nenhuma para conferir. Os precos saem de log-retornos
`default_rng(...).normal(0, 0.01)` acumulados a partir de 100, e o `log_return` de cada
linha e calculado **aqui**, a partir dos `adj_close` ja arredondados.
"""

from __future__ import annotations

import math
import re
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from io import StringIO
from typing import Any

import numpy as np
import pytest
from django.core.management import CommandError, call_command

from apps.assets.models import Asset, CollectionRun, Price
from apps.risk import config
from apps.risk.compute import MODELS, NO_CANDIDATES
from apps.risk.models import RiskResult, RiskRun

pytestmark = pytest.mark.django_db

Q6 = Decimal("0.000001")
Q10 = Decimal("0.0000000001")

INICIO = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
ULTIMO_PREGAO = date(2026, 9, 18)

# Dois modelos deterministicos e baratos: nenhum treino de rede.
BARATOS = ["parametric", "historical"]


def dias_uteis(quantidade: int, fim: date = ULTIMO_PREGAO) -> list[date]:
    """`quantidade` dias uteis consecutivos terminando em `fim`, em ordem crescente."""
    datas: list[date] = []
    dia = fim
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia -= timedelta(days=1)
    return sorted(datas)


def precos(quantidade: int, *, semente: int = 7) -> list[Decimal]:
    """Precos com log-retornos normais de desvio 1%, a partir de 100."""
    rng = np.random.default_rng(semente)
    nivel = 100.0
    valores = [Decimal("100.000000")]
    for retorno in rng.normal(0, 0.01, quantidade - 1):
        nivel *= math.exp(float(retorno))
        valores.append(Decimal(str(nivel)).quantize(Q6))
    return valores


def cria_ativo(ticker: str) -> Asset:
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


def com_serie(ticker: str, quantidade: int = config.MIN_SESSIONS) -> Asset:
    asset = cria_ativo(ticker)
    coleta = CollectionRun.objects.create(source="teste", started_at=INICIO)
    datas = dias_uteis(quantidade)
    valores = precos(quantidade)
    linhas = []
    anterior: Decimal | None = None
    for dia, adj in zip(datas, valores, strict=True):
        log_return = (
            None
            if anterior is None
            else Decimal(str(math.log(float(adj) / float(anterior)))).quantize(Q10)
        )
        anterior = adj
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
                log_return=log_return,
                run=coleta,
                updated_at=INICIO,
            )
        )
    Price.objects.bulk_create(linhas)
    return asset


# --- caminho feliz -----------------------------------------------------------------------


def test_comando_grava_e_escreve_o_relatorio_em_stdout() -> None:
    """O relatorio sai inteiro, e os dois modelos pedidos viram quatro resultados."""
    com_serie("AAA3")
    stdout = StringIO()

    call_command(
        "compute_risk",
        "AAA3",
        "--model",
        "parametric",
        "--model",
        "historical",
        stdout=stdout,
    )

    saida = stdout.getvalue()
    assert re.search(
        r"^AAA3\s+503 pregoes  ate 2026-09-18\s+4 resultados, \d+ adequados, 0 falhos",
        saida,
        re.MULTILINE,
    )
    assert re.search(
        r"^risco: 1 ativos, 1 ok, 0 falhos, 0 pulados, ", saida, re.MULTILINE
    )
    run = RiskRun.objects.get()
    assert run.asset.ticker == "AAA3"
    assert run.results.count() == 4


# --- as duas opcoes chegam ao lugar certo ------------------------------------------------


def test_model_repetido_e_o_conjunto_que_roda() -> None:
    """Sem a opcao chegar a `run_compute_risk`, rodariam os nove -- e dezoito linhas."""
    com_serie("AAA3")

    call_command(
        "compute_risk",
        "AAA3",
        "--model",
        "parametric",
        "--model",
        "historical",
        stdout=StringIO(),
    )

    assert sorted({r.model_name for r in RiskResult.objects.all()}) == sorted(BARATOS)
    assert RiskResult.objects.count() == 4


def test_seed_chega_a_execucao_e_omitida_vale_o_padrao() -> None:
    """A coluna `seed` do manifesto e a semente pedida -- ou `config.DEFAULT_SEED`."""
    com_serie("AAA3")
    com_serie("BBB3")

    call_command(
        "compute_risk",
        "AAA3",
        "--model",
        "parametric",
        "--seed",
        "7",
        stdout=StringIO(),
    )
    call_command("compute_risk", "BBB3", "--model", "parametric", stdout=StringIO())

    assert RiskRun.objects.get(asset__ticker="AAA3").seed == 7
    assert RiskRun.objects.get(asset__ticker="BBB3").seed == config.DEFAULT_SEED
    assert config.DEFAULT_SEED != 7  # senao o primeiro assert passaria por acidente


# --- RF-17: o que falha alto antes de escrever -------------------------------------------


def test_v15_registry_incompleto_falha_alto_e_nao_grava_nada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """V-15, pela casca: ambiente com menos de nove modelos, execucao sem `--model`.

    O registry e encurtado no ponto em que `compute` o consulta. Os sete que faltam sao
    nomeados, a saida e 1, e `gold` fica vazia.
    """
    com_serie("AAA3")
    monkeypatch.setattr("apps.risk.compute.list_models", lambda: sorted(BARATOS))

    with pytest.raises(CommandError) as info:
        call_command("compute_risk", "AAA3", stdout=StringIO())

    assert str(info.value) == (
        "modelos ausentes do registry: caviar, egarch, garch_1_1, garchnet, gru, "
        "lstm, monte_carlo"
    )
    assert info.value.returncode == 1
    assert RiskRun.objects.count() == 0
    assert RiskResult.objects.count() == 0


def test_modelo_pedido_por_nome_errado_falha_alto_e_nao_grava_nada() -> None:
    """A outra leitura do RF-17: com `--model`, o que se denuncia e o nome errado."""
    com_serie("AAA3")

    with pytest.raises(CommandError) as info:
        call_command(
            "compute_risk",
            "AAA3",
            "--model",
            "parametric",
            "--model",
            "inexistente",
            stdout=StringIO(),
        )

    assert str(info.value) == "modelos ausentes do registry: inexistente"
    assert info.value.returncode == 1
    assert RiskRun.objects.count() == 0


# --- RF-18 e a falha que imprime o relatorio ---------------------------------------------


def test_ticker_invalido_vira_command_error_com_saida_1_e_nao_escreve() -> None:
    com_serie("AAA3")

    with pytest.raises(CommandError) as info:
        call_command(
            "compute_risk", "AAA3", "XPTO9", "--model", "parametric", stdout=StringIO()
        )

    assert str(info.value) == "tickers invalidos ou inativos: XPTO9"
    assert info.value.returncode == 1
    assert RiskRun.objects.count() == 0


def test_falha_escreve_o_relatorio_antes_de_sair_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`RiskFailed` leva o relatorio inteiro a stdout; o erro vai a stderr e sai 1."""
    com_serie("AAA3")

    def quebra(*args: object, **kwargs: object) -> None:
        raise RuntimeError("gravacao quebrou")

    monkeypatch.setattr("apps.risk.compute.write_risk", quebra)
    stdout = StringIO()

    with pytest.raises(CommandError) as info:
        call_command("compute_risk", "AAA3", "--model", "parametric", stdout=stdout)

    assert str(info.value) == "risco com falhas: AAA3"
    assert info.value.returncode == 1
    saida = stdout.getvalue()  # o relatorio inteiro saiu antes do erro
    assert re.search(
        r"^AAA3\s+503 pregoes  ate 2026-09-18\s+"
        r"FALHOU \(RuntimeError: gravacao quebrou\)",
        saida,
        re.MULTILINE,
    )
    assert re.search(
        r"^risco: 1 ativos, 0 ok, 1 falhos, 0 pulados, ", saida, re.MULTILINE
    )
    assert RiskRun.objects.count() == 0


# --- `--async`: enfileira, nao cria `risk_run` -------------------------------------------


@pytest.fixture
def fila(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """O duplo do `_enqueue`: guarda o que recebeu e nao fala com o Redis."""
    recebidos: list[Any] = []
    monkeypatch.setattr("apps.risk.tasks._enqueue", recebidos.append)
    return recebidos


def inativo_com_preco(ticker: str) -> Asset:
    """Um ativo inativo com um preco: candidato pulado do ramo sem argumentos."""
    asset = com_serie(ticker, 2)
    Asset.objects.filter(pk=asset.pk).update(status=Asset.Status.INACTIVE)
    return asset


def test_v05d_async_enfileira_uma_abertura_por_ativo_e_nao_cria_risk_run(
    fila: list[Any],
) -> None:
    """V-05d, pela casca. Os dois ativos tem os 503 pregoes do piso: sem isso, "nenhuma
    `risk_run`" seria verdade ate no sincrono, que pula serie curta."""
    com_serie("PETR4")
    com_serie("VALE3")
    stdout = StringIO()

    call_command("compute_risk", "--async", "PETR4", "VALE3", stdout=stdout)

    assert [s.task for s in fila] == ["apps.risk.tasks.abrir_execucao"] * 2
    assert [s.args[0] for s in fila] == ["PETR4", "VALE3"]
    assert len({s.args[1] for s in fila}) == 1  # o mesmo `calculated_at_iso`
    assert {(s.args[2], tuple(s.args[3])) for s in fila} == {
        (config.DEFAULT_SEED, tuple(MODELS))
    }
    assert RiskRun.objects.count() == 0
    assert stdout.getvalue().splitlines()[-1] == (
        "risco assincrono: 2 ativos, 2 enfileirados, 0 pulados; "
        "acompanhe em gold.risk_run"
    )


def test_async_passa_seed_e_model_as_aberturas(fila: list[Any]) -> None:
    com_serie("AAA3")

    call_command(
        "compute_risk",
        "--async",
        "AAA3",
        "--seed",
        "7",
        "--model",
        "parametric",
        stdout=StringIO(),
    )

    assert [(s.args[0], s.args[2], s.args[3]) for s in fila] == [
        ("AAA3", 7, ["parametric"])
    ]


def test_async_ticker_invalido_sai_1_e_nao_enfileira_nada(fila: list[Any]) -> None:
    """`AAA3` e valido: quem enfileirasse antes de validar o mandaria para a fila."""
    com_serie("AAA3")

    with pytest.raises(CommandError) as info:
        call_command("compute_risk", "--async", "AAA3", "XPTO9", stdout=StringIO())

    assert str(info.value) == "tickers invalidos ou inativos: XPTO9"
    assert info.value.returncode == 1
    assert fila == []
    assert RiskRun.objects.count() == 0


def test_async_modelo_inexistente_sai_1_e_nao_enfileira_nada(fila: list[Any]) -> None:
    com_serie("AAA3")

    with pytest.raises(CommandError) as info:
        call_command(
            "compute_risk",
            "--async",
            "AAA3",
            "--model",
            "inexistente",
            stdout=StringIO(),
        )

    assert str(info.value) == "modelos ausentes do registry: inexistente"
    assert info.value.returncode == 1
    assert fila == []


def test_async_sem_argumentos_e_sem_candidato_pede_tickers(fila: list[Any]) -> None:
    cria_ativo("AAA3")  # sem preco: nem candidato
    stdout = StringIO()

    call_command("compute_risk", "--async", stdout=stdout)

    assert stdout.getvalue() == NO_CANDIDATES + "\n"
    assert fila == []


def test_async_sem_argumentos_e_so_inativos_lista_os_pulados_e_pede_tickers(
    fila: list[Any],
) -> None:
    inativo_com_preco("BAZZ4")
    stdout = StringIO()

    call_command("compute_risk", "--async", stdout=stdout)

    assert stdout.getvalue().splitlines() == [
        "BAZZ4        pulado: inativo",
        NO_CANDIDATES,
    ]
    assert fila == []


def test_async_o_relatorio_e_o_literal_do_plano(fila: list[Any]) -> None:
    """Ramo sem argumentos, com um inativo: a saida e a do plano, linha a linha.

    O `IBOV` ja existe -- a migration `assets.0002` o cria, ativo e sem preco --; aqui ele
    so ganha um preco, que e o que o torna candidato."""
    ibov = Asset.objects.get(ticker="IBOV")
    Price.objects.create(
        asset=ibov,
        date=ULTIMO_PREGAO,
        open=Decimal("100.000000"),
        high=Decimal("100.000000"),
        low=Decimal("100.000000"),
        close=Decimal("100.000000"),
        adj_close=Decimal("100.000000"),
        volume=1000,
        log_return=None,
        run=CollectionRun.objects.create(source="teste", started_at=INICIO),
        updated_at=INICIO,
    )
    com_serie("PETR4", 2)
    inativo_com_preco("BAZZ4")
    stdout = StringIO()

    call_command("compute_risk", "--async", stdout=stdout)

    assert stdout.getvalue().splitlines() == [
        "IBOV         enfileirado",
        "PETR4        enfileirado",
        "BAZZ4        pulado: inativo",
        "risco assincrono: 3 ativos, 2 enfileirados, 1 pulados; "
        "acompanhe em gold.risk_run",
    ]
    assert [s.args[0] for s in fila] == ["IBOV", "PETR4"]
