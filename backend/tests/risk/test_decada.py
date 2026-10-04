"""A decada do ativo e a serie (RF-02 do M2.4): o V-02 do plano, Tarefa 1.

`apps.risk.decade` e puro: `decade_end` e `decade_of` se provam sem banco, sobre `Price` nao
gravados; `valid_bars` le `silver.price` e se prova contra o banco. A coluna `adj_close` e
`NOT NULL` no banco, entao o caso do nulo passa por um duble da consulta, e o do zero e o do
negativo, pelo banco de verdade.

A ultima parte confere, pela arvore sintatica, que o modulo nao importa o motor -- a `web` o
importa, e a `web` nao tem o motor (molde de `tests/api/test_sem_motor.py`).
"""

from __future__ import annotations

import ast
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

import apps.risk.decade as decade_module
from apps.assets.models import Asset, CollectionRun, Price
from apps.risk import config
from apps.risk.compute import _bars
from apps.risk.decade import Decade, decade_end, decade_of, valid_bars

AGORA = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
UM = Decimal("10.000000")


def barra(dia: date, adj_close: Decimal | None = UM) -> Price:
    """Um `Price` so na memoria: `decade_of` le apenas `date`.

    O `cast` deixa montar o `adj_close` nulo que a coluna `NOT NULL` nao aceita no banco.
    """
    return Price(date=dia, adj_close=cast(Decimal, adj_close))


def dias_uteis(inicio: date, quantidade: int) -> list[date]:
    datas: list[date] = []
    dia = inicio
    while len(datas) < quantidade:
        if dia.weekday() < 5:
            datas.append(dia)
        dia += timedelta(days=1)
    return datas


# --- o fim da decada ----------------------------------------------------------------------


def test_o_fim_e_a_mesma_data_dez_anos_depois() -> None:
    assert decade_end(date(2016, 9, 22)) == date(2026, 9, 22)


def test_29_de_fevereiro_vira_28_no_ano_que_nao_e_bissexto() -> None:
    assert decade_end(date(2016, 2, 29)) == date(2026, 2, 28)


def test_29_de_fevereiro_sempre_vira_28_e_28_fica_28() -> None:
    """`y` e `y + 10` nunca sao os dois bissextos (`y + 10` e `y + 2` modulo 4)."""
    assert decade_end(date(2020, 2, 29)) == date(2030, 2, 28)
    assert decade_end(date(2014, 2, 28)) == date(2024, 2, 28)


# --- a decada sobre a serie ----------------------------------------------------------------


def test_sem_barras_nao_ha_decada() -> None:
    assert decade_of([]) is None


def test_o_fim_se_conta_do_primeiro_pregao_e_nao_do_ultimo() -> None:
    barras = [
        barra(date(2016, 9, 22)),
        barra(date(2020, 5, 4)),
        barra(date(2027, 1, 6)),
    ]
    decada = decade_of(barras)
    assert decada is not None
    assert decada.first_price_date == date(2016, 9, 22)
    assert decada.end_date == date(2026, 9, 22)
    assert decada.last_price_date == date(2027, 1, 6)


@pytest.mark.parametrize(
    ("ultimo", "completa"),
    [
        (date(2026, 9, 22), True),  # o ultimo pregao igual ao fim
        (date(2026, 9, 21), False),  # um dia antes
        (date(2026, 9, 23), True),  # depois
    ],
)
def test_completa_com_o_ultimo_pregao_no_fim_ou_depois(
    ultimo: date, completa: bool
) -> None:
    decada = decade_of(
        [barra(date(2016, 9, 22)), barra(date(2021, 3, 1)), barra(ultimo)]
    )
    assert decada is not None
    assert decada.complete is completa


def test_o_pregao_exatamente_no_fim_entra_na_serie_e_o_seguinte_fica_fora() -> None:
    no_fim = barra(date(2026, 9, 22))
    depois = barra(date(2026, 9, 23))
    barras = [barra(date(2016, 9, 22)), barra(date(2021, 3, 1)), no_fim, depois]
    decada = decade_of(barras)
    assert decada is not None
    assert decada.series == barras[:3]
    assert decada.series[-1] is no_fim
    assert depois not in decada.series
    assert decada.sessions == 3
    # `last_price_date` e da serie inteira, nao da serie do experimento
    assert decada.last_price_date == date(2026, 9, 23)


def test_decada_do_29_de_fevereiro_corta_em_28() -> None:
    barras = [
        barra(date(2016, 2, 29)),
        barra(date(2026, 2, 27)),
        barra(date(2026, 2, 28)),
    ]
    barras.append(barra(date(2026, 3, 2)))
    decada = decade_of(barras)
    assert decada is not None
    assert decada.end_date == date(2026, 2, 28)
    assert [b.date for b in decada.series] == [
        date(2016, 2, 29),
        date(2026, 2, 27),
        date(2026, 2, 28),
    ]
    assert decada.complete is True


@pytest.mark.parametrize(
    ("quantidade", "suficiente"),
    [(config.MIN_SESSIONS - 1, False), (config.MIN_SESSIONS, True)],
)
def test_suficiente_a_partir_do_piso(quantidade: int, suficiente: bool) -> None:
    assert config.MIN_SESSIONS == 503
    decada = decade_of([barra(d) for d in dias_uteis(date(2016, 1, 4), quantidade)])
    assert decada is not None
    assert decada.sessions == quantidade
    assert decada.sufficient is suficiente


def test_suficiente_conta_so_a_serie_do_experimento() -> None:
    """Pregoes depois do fim nao contam para o piso."""
    dentro = [barra(d) for d in dias_uteis(date(2016, 1, 4), config.MIN_SESSIONS - 1)]
    fora = [barra(d) for d in dias_uteis(date(2026, 1, 5), 10)]
    decada = decade_of([*dentro, *fora])
    assert decada is not None
    assert decada.complete is True
    assert decada.sessions == config.MIN_SESSIONS - 1
    assert decada.sufficient is False


def test_a_decada_e_imutavel() -> None:
    decada = decade_of([barra(date(2016, 9, 22))])
    assert isinstance(decada, Decade)
    with pytest.raises(AttributeError):
        decada.sessions = 999  # type: ignore[misc]


# --- a serie valida, contra o banco --------------------------------------------------------


def _ativo(ticker: str) -> Asset:
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


def _grava(asset: Asset, linhas: list[tuple[date, Decimal]]) -> None:
    coleta = CollectionRun.objects.create(source="teste", started_at=AGORA)
    Price.objects.bulk_create(
        Price(
            asset=asset,
            date=dia,
            open=UM,
            high=UM,
            low=UM,
            close=UM,
            adj_close=adj,
            volume=1000,
            log_return=None,
            run=coleta,
            updated_at=AGORA,
        )
        for dia, adj in linhas
    )


@pytest.mark.django_db
@pytest.mark.parametrize("ruim", [Decimal("0"), Decimal("-1.000000")])
def test_o_primeiro_pregao_com_adj_close_zero_ou_negativo_e_pulado(
    ruim: Decimal,
) -> None:
    asset = _ativo("DECA3")
    # gravados fora de ordem: a serie sai em ordem de data
    _grava(
        asset,
        [
            (date(2026, 9, 23), UM),
            (date(2016, 9, 21), ruim),
            (date(2016, 9, 22), UM),
            (date(2020, 1, 2), UM),
        ],
    )
    barras = valid_bars(asset)
    assert [b.date for b in barras] == [
        date(2016, 9, 22),
        date(2020, 1, 2),
        date(2026, 9, 23),
    ]
    decada = decade_of(barras)
    assert decada is not None
    assert decada.first_price_date == date(2016, 9, 22)
    assert decada.end_date == date(2026, 9, 22)
    assert decada.complete is True
    assert decada.sessions == 2


@pytest.mark.django_db
def test_valid_bars_so_do_ativo_pedido() -> None:
    asset = _ativo("DECA3")
    outro = _ativo("OUTR3")
    _grava(asset, [(date(2016, 9, 22), UM)])
    _grava(outro, [(date(2015, 1, 2), UM)])
    assert [b.date for b in valid_bars(asset)] == [date(2016, 9, 22)]


def test_o_primeiro_pregao_com_adj_close_nulo_e_pulado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A coluna e `NOT NULL`: o nulo so chega por um duble da consulta."""
    asset = Asset(ticker="DECA3")
    linhas = [
        barra(date(2020, 1, 2)),
        barra(date(2016, 9, 21), None),
        barra(date(2016, 9, 22)),
    ]

    class _Consulta:
        def filter(self, **filtro: object) -> _Consulta:
            assert filtro == {"asset": asset}
            return self

        def order_by(self, campo: str) -> list[Price]:
            assert campo == "date"
            return sorted(linhas, key=lambda p: p.date)

    class _PriceFalso:
        objects = _Consulta()

    monkeypatch.setattr(decade_module, "Price", _PriceFalso)
    barras = valid_bars(asset)
    assert [b.date for b in barras] == [date(2016, 9, 22), date(2020, 1, 2)]
    decada = decade_of(barras)
    assert decada is not None
    assert decada.first_price_date == date(2016, 9, 22)


@pytest.mark.django_db
def test_compute_bars_devolve_o_mesmo_que_valid_bars() -> None:
    asset = _ativo("DECA3")
    _grava(
        asset,
        [
            (date(2016, 9, 21), Decimal("0")),
            (date(2016, 9, 22), UM),
            (date(2020, 1, 2), UM),
        ],
    )
    assert [b.pk for b in _bars(asset)] == [b.pk for b in valid_bars(asset)]
    assert [b.date for b in _bars(asset)] == [date(2016, 9, 22), date(2020, 1, 2)]


# --- o modulo nao importa o motor ----------------------------------------------------------

PACOTES_PROIBIDOS = frozenset({"engine", "tensorflow", "pandas", "numpy"})
MODULOS_PROIBIDOS = frozenset(
    {"apps.risk.compute", "apps.risk.snapshots", "apps.risk.tasks", "apps.risk.lab"}
)
# O que `decade.py` pode importar fora da biblioteca padrao (RF-02, o plano).
MODULOS_PERMITIDOS = frozenset({"apps.assets.models", "apps.risk.config"})

_ARQUIVO = Path(decade_module.__file__)


def _nomes_importados(no: ast.Import | ast.ImportFrom) -> list[str]:
    if isinstance(no, ast.Import):
        return [a.name for a in no.names]
    assert no.level == 0, "decade.py nao usa import relativo"
    base = no.module or ""
    # `from apps.risk import config` importa `apps.risk.config`: confere os dois nomes
    return [base, *(f"{base}.{a.name}" for a in no.names)]


def _imports() -> list[ast.Import | ast.ImportFrom]:
    arvore = ast.parse(_ARQUIVO.read_text(encoding="utf-8"))
    return [n for n in ast.walk(arvore) if isinstance(n, ast.Import | ast.ImportFrom)]


def test_decade_nao_importa_o_motor_nem_os_modulos_proibidos() -> None:
    nos = _imports()
    assert nos, "a varredura nao achou import nenhum"
    achados = [
        f"{_ARQUIVO.name}:{no.lineno} -> {nome}"
        for no in nos
        for nome in _nomes_importados(no)
        if nome.split(".")[0] in PACOTES_PROIBIDOS
        or any(nome == m or nome.startswith(m + ".") for m in MODULOS_PROIBIDOS)
    ]
    assert not achados, "imports proibidos: " + "; ".join(achados)


def test_decade_so_importa_a_biblioteca_padrao_e_os_dois_modulos() -> None:
    fora: list[str] = []
    for no in _imports():
        if isinstance(no, ast.Import):
            fora += [
                a.name
                for a in no.names
                if a.name.split(".")[0] not in sys.stdlib_module_names
            ]
            continue
        base = no.module or ""
        if base == "__future__" or base.split(".")[0] in sys.stdlib_module_names:
            continue
        if base in MODULOS_PERMITIDOS:
            continue
        # `from apps.risk import config`: o submodulo importado tem de ser permitido
        fora += [
            f"{base}.{a.name}"
            for a in no.names
            if f"{base}.{a.name}" not in MODULOS_PERMITIDOS
        ]
    assert not fora, "imports fora da lista: " + "; ".join(fora)
