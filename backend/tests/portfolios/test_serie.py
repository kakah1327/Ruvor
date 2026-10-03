"""M2.2a, T2: a serie da carteira (RF-06; V-03).

Tres acoes fabricadas a mao -- `AAAA3` com as datas 1 a 5, `BBBB3` com 1, 2, 4 e 5 (a lacuna em 3)
e `CCCC3` com 1 a 6 -- e os pesos 50, 30 e 20. A interseccao e 1, 2, 4 e 5, e o retorno de 2 a 4
sai numa data so. Os valores esperados sao escritos a mao, termo a termo, na ordem do ticker, e
comparados com `==` em `float`, nunca com `approx`.

Os precos de 1 a 2 foram escolhidos para que a soma dos tres termos na ordem inversa do ticker
difira, bit a bit, da soma na ordem do ticker -- e que a diferenca sobreviva ao `1 + R` do indice,
que apaga a de um ulp na maioria dos casos: sem isso, trocar a ordem da soma passaria (a mutacao 5
da T7). A pre-condicao e afirmada no teste, sobre o indice.
"""

from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.tenancy import organization_scope
from apps.assets.models import CollectionRun, Price
from apps.portfolios.models import PortfolioVersion
from apps.portfolios.series import (
    AssetCoverage,
    build,
    compute,
    series_sha256,
)
from tests.portfolios.dados import Pessoas, acao, carteira, org_e_pessoas

# 1 -> 2026-03-02 ... 6 -> 2026-03-07
D = {k: date(2026, 3, k + 1) for k in range(1, 7)}

PRECOS: dict[str, dict[int, str]] = {
    "AAAA3": {1: "10", 2: "9", 3: "9.5", 4: "10", 5: "9.8"},
    "BBBB3": {1: "20", 2: "18", 4: "19", 5: "20"},
    "CCCC3": {1: "30", 2: "29.5", 3: "29", 4: "31", 5: "30.5", 6: "31"},
}
PESOS = {"AAAA3": Decimal("50"), "BBBB3": Decimal("30"), "CCCC3": Decimal("20")}


def _precos(
    precos: dict[str, dict[int, str]] = PRECOS,
) -> dict[str, list[tuple[date, Decimal]]]:
    return {
        t: [(D[k], Decimal(v)) for k, v in dias.items()] for t, dias in precos.items()
    }


# Os termos de cada data, escritos a mao: peso / 100 * (preco de hoje / preco de ontem - 1)
TERMOS_2 = (0.5 * (9 / 10 - 1), 0.3 * (18 / 20 - 1), 0.2 * (29.5 / 30 - 1))
TERMOS_4 = (0.5 * (10 / 9 - 1), 0.3 * (19 / 18 - 1), 0.2 * (31 / 29.5 - 1))  # de 2 a 4
TERMOS_5 = (0.5 * (9.8 / 10 - 1), 0.3 * (20 / 19 - 1), 0.2 * (30.5 / 31 - 1))

R_2 = TERMOS_2[0] + TERMOS_2[1] + TERMOS_2[2]
R_4 = TERMOS_4[0] + TERMOS_4[1] + TERMOS_4[2]
R_5 = TERMOS_5[0] + TERMOS_5[1] + TERMOS_5[2]

I_1 = 1.0
I_2 = I_1 * (1 + R_2)
I_4 = I_2 * (1 + R_4)
I_5 = I_4 * (1 + R_5)

DATAS = (D[1], D[2], D[4], D[5])
INDICE = (I_1, I_2, I_4, I_5)

TEXTO = (
    f"2026-03-02|{I_1!r}\n2026-03-03|{I_2!r}\n2026-03-05|{I_4!r}\n2026-03-06|{I_5!r}\n"
)
HASH = "2d452a2619b4686cd95cfbee8b889c299bdaf5d23e2569ed90ccf43c28c5f4c1"


# --- V-03: `compute` e o hash, puros ----------------------------------------------------


def test_v03_a_pre_condicao_a_soma_inversa_muda_o_indice() -> None:
    inversa = TERMOS_2[2] + TERMOS_2[1] + TERMOS_2[0]
    assert inversa != R_2
    assert I_1 * (1 + inversa) != I_2


def test_v03_as_datas_sao_a_interseccao() -> None:
    datas, _ = compute(_precos(), PESOS)
    assert datas == DATAS


def test_v03_o_indice_e_o_escrito_a_mao() -> None:
    _, indice = compute(_precos(), PESOS)
    assert indice == INDICE


def test_v03_o_hash_e_o_escrito_a_mao() -> None:
    assert hashlib.sha256(TEXTO.encode("utf-8")).hexdigest() == HASH
    assert series_sha256(DATAS, INDICE) == HASH


def test_v03_as_mesmas_entradas_dao_o_mesmo_hash() -> None:
    assert series_sha256(*compute(_precos(), PESOS)) == series_sha256(
        *compute(_precos(), PESOS)
    )


def test_v03_a_ordem_de_insercao_dos_pesos_nao_muda_nada() -> None:
    em_ordem = dict(sorted(PESOS.items()))
    inversa = dict(sorted(PESOS.items(), reverse=True))
    assert list(inversa) == ["CCCC3", "BBBB3", "AAAA3"]
    datas_a, indice_a = compute(_precos(), em_ordem)
    datas_b, indice_b = compute(_precos(), inversa)
    assert indice_a == indice_b == INDICE
    assert series_sha256(datas_a, indice_a) == series_sha256(datas_b, indice_b)


def test_v03_o_retorno_e_simples_e_nao_logaritmico() -> None:
    # o indice de 1 a 2 e 1 + soma dos retornos simples ponderados, nao exp(soma dos log)
    _, indice = compute(_precos(), PESOS)
    assert indice[1] == 1.0 * (1 + R_2)


def test_v03_acao_sem_preco_esvazia_a_serie() -> None:
    precos = _precos() | {"DDDD3": []}
    datas, indice = compute(precos, PESOS | {"DDDD3": Decimal("10")})
    assert (datas, indice) == ((), ())
    assert series_sha256(datas, indice) == hashlib.sha256(b"").hexdigest()


# --- V-03: `build` sobre as acoes gravadas ----------------------------------------------


@pytest.fixture
def pessoas() -> Pessoas:
    return org_e_pessoas()


def _grava(precos: dict[str, dict[int, str]] = PRECOS) -> None:
    for ticker, lista in _precos(precos).items():
        acao(ticker, lista)


def _versao(pessoas: Pessoas, pesos: dict[str, str]) -> PortfolioVersion:
    portfolio = carteira(pessoas.admin, pesos)
    return PortfolioVersion.unscoped.get(portfolio=portfolio, number=1)


PESOS_TEXTO = {"AAAA3": "50.00", "BBBB3": "30.00", "CCCC3": "20.00"}


@pytest.mark.django_db
def test_v03_build_da_o_mesmo_que_compute(pessoas: Pessoas) -> None:
    _grava()
    versao = _versao(pessoas, PESOS_TEXTO)
    with organization_scope(pessoas.acme.pk):
        serie = build(versao)
    assert serie.dates == DATAS
    assert serie.index == INDICE
    assert serie.sha256 == HASH


@pytest.mark.django_db
def test_v03_build_a_cobertura_de_cada_acao_sozinha(pessoas: Pessoas) -> None:
    _grava()
    versao = _versao(pessoas, PESOS_TEXTO)
    with organization_scope(pessoas.acme.pk):
        serie = build(versao)
    assert serie.coverage == (
        AssetCoverage(ticker="AAAA3", first_date=D[1], sessions=5),
        AssetCoverage(ticker="BBBB3", first_date=D[1], sessions=4),
        AssetCoverage(ticker="CCCC3", first_date=D[1], sessions=6),
    )


@pytest.mark.django_db
def test_v03_build_o_price_run_e_o_maior_das_datas_da_interseccao(
    pessoas: Pessoas,
) -> None:
    sem_o_dia_6 = PRECOS | {
        "CCCC3": {k: v for k, v in PRECOS["CCCC3"].items() if k != 6}
    }
    _grava(sem_o_dia_6)
    coleta_de_c = Price.objects.get(asset__ticker="CCCC3", date=D[1]).run_id
    # uma linha fora da interseccao (o dia 6 so existe em C), de uma coleta mais nova
    tardia = CollectionRun.objects.create(
        source="yahoo_chart", started_at=timezone.now()
    )
    linha = Price.objects.get(asset__ticker="CCCC3", date=D[5])
    linha.pk = None
    linha.date = D[6]
    linha.run = tardia
    linha.save()
    assert tardia.pk > coleta_de_c
    versao = _versao(pessoas, PESOS_TEXTO)
    with organization_scope(pessoas.acme.pk):
        serie = build(versao)
    coletas = set(
        Price.objects.filter(date__in=DATAS, asset__ticker__in=PESOS).values_list(
            "run_id", flat=True
        )
    )
    assert serie.price_run_id == max(coletas) == coleta_de_c


@pytest.mark.django_db
def test_v03_build_com_janela_so_as_datas_dela(pessoas: Pessoas) -> None:
    _grava()
    versao = _versao(pessoas, PESOS_TEXTO)
    with organization_scope(pessoas.acme.pk):
        serie = build(versao, first=D[2], last=D[5])
    assert serie.dates == (D[2], D[4], D[5])
    assert serie.index == (1.0, 1.0 * (1 + R_4), 1.0 * (1 + R_4) * (1 + R_5))


@pytest.mark.django_db
def test_v03_build_acao_sem_preco(pessoas: Pessoas) -> None:
    _grava()
    acao("DDDD3", [])
    versao = _versao(pessoas, PESOS_TEXTO | {"AAAA3": "40.00", "DDDD3": "10.00"})
    with organization_scope(pessoas.acme.pk):
        serie = build(versao)
    assert (serie.dates, serie.index, serie.price_run_id) == ((), (), None)
    assert serie.coverage[3] == AssetCoverage(
        ticker="DDDD3", first_date=None, sessions=0
    )


@pytest.mark.django_db
def test_v03_build_preco_zero_tira_a_data_da_acao(pessoas: Pessoas) -> None:
    _grava(PRECOS | {"AAAA3": PRECOS["AAAA3"] | {4: "0"}})
    versao = _versao(pessoas, PESOS_TEXTO)
    with organization_scope(pessoas.acme.pk):
        serie = build(versao)
    assert serie.dates == (D[1], D[2], D[5])
    assert serie.coverage[0] == AssetCoverage(
        ticker="AAAA3", first_date=D[1], sessions=4
    )
