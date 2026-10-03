"""O estresse historico conferido a mao: V-02, V-03, V-04 e a metade do backend do V-09.

Nenhum teste aqui toca banco: `compute_stress` recebe listas de `Bar` montadas no proprio
teste. As bordas usam um episodio de laboratorio, de sabado 2024-01-06 a domingo
2024-01-14, posto no lugar de `EPISODES` por `monkeypatch`; a lista real da D-147 e
conferida a parte.

**Todo valor esperado esta escrito literalmente**, com a conta no comentario.
"""

from __future__ import annotations

import ast
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from apps.analytics import stress
from apps.analytics.metrics import Bar
from apps.analytics.stress import EPISODES, Episode, compute_stress, missing_reason

# V-02 e V-09: escritos aqui, nunca lidos do codigo sob teste.
CODIGOS_VIGENTES = ["jbs_2017", "truckers_2018", "covid_2020", "rates_2021"]
DATAS = {
    "jbs_2017": (date(2017, 5, 17), date(2017, 6, 30)),
    "truckers_2018": (date(2018, 5, 18), date(2018, 6, 29)),
    "covid_2020": (date(2020, 2, 21), date(2020, 3, 31)),
    "rates_2021": (date(2021, 6, 7), date(2022, 7, 14)),
}

# Sabado e domingo: as duas pontas caem fora de pregao (RF-02).
LAB = Episode("lab", date(2024, 1, 6), date(2024, 1, 14))


def serie(*pontos: tuple[str, str]) -> list[Bar]:
    """Pregoes por (data ISO, adj_close); o resto do `Bar` nao entra no estresse."""
    return [
        Bar(
            date=date.fromisoformat(d),
            close=Decimal(p),
            adj_close=Decimal(p),
            volume=1,
            log_return=None,
        )
        for d, p in pontos
    ]


@pytest.fixture
def lab(monkeypatch: pytest.MonkeyPatch) -> Episode:
    monkeypatch.setattr(stress, "EPISODES", (LAB,))
    return LAB


# A serie de referencia das bordas. Indices na serie inteira entre parenteses.
#   01-04 (0) 20  -> antes de P0: o topo de 20 fica fora da janela
#   01-05 (1) 10  -> P0, ultimo pregao <= sabado 01-06
#   01-08 (2)  9  -> 9/10-1 = -0,1
#   01-09 (3)  8  -> 8/10-1 = -0,2, o fundo
#   01-10 (4)  9
#   01-11 (5) 11  -> recupera: 11 >= 10, 5-3 = 2 pregoes
#   01-12 (6) 12  -> Pn, ultimo pregao <= domingo 01-14
#   01-15 (7) 12
BASE = serie(
    ("2024-01-04", "20"),
    ("2024-01-05", "10"),
    ("2024-01-08", "9"),
    ("2024-01-09", "8"),
    ("2024-01-10", "9"),
    ("2024-01-11", "11"),
    ("2024-01-12", "12"),
    ("2024-01-15", "12"),
)


# --- V-02 e V-09: a lista da D-147 -------------------------------------------------------


def test_os_codigos_sao_os_da_d147() -> None:
    assert [e.code for e in EPISODES] == CODIGOS_VIGENTES, (
        "mudou a lista de episodios (D-147) — e decisao nova; atualize os nomes em "
        "`frontend/src/content/textos.ts` e as duas listas de teste"
    )


def test_as_datas_sao_as_da_d147() -> None:
    assert {e.code: (e.start, e.end) for e in EPISODES} == DATAS


def test_a_ordem_e_cronologica() -> None:
    inicios = [e.start for e in EPISODES]
    assert inicios == sorted(inicios)
    assert all(e.start < e.end for e in EPISODES)


def test_sempre_um_resultado_por_episodio_na_ordem_da_lista() -> None:
    # Dias uteis de 2017-01-02 a 2022-12-30, preco constante: todo episodio tem dado.
    dias = []
    d = date(2017, 1, 2)
    while d <= date(2022, 12, 30):
        if d.weekday() < 5:
            dias.append((d.isoformat(), "10"))
        d += timedelta(days=1)
    bars = serie(*dias)
    resultado = compute_stress(bars, None, None)
    assert [r.episode for r in resultado] == CODIGOS_VIGENTES
    assert [(r.start_date, r.end_date) for r in resultado] == [
        DATAS[c] for c in CODIGOS_VIGENTES
    ]
    assert all(r.missing is None for r in resultado)


def test_sem_dado_ainda_assim_devolve_todos() -> None:
    # Serie de 2024: comeca depois de todos os episodios.
    resultado = compute_stress(BASE, None, None)
    assert [r.episode for r in resultado] == CODIGOS_VIGENTES
    assert [r.missing for r in resultado] == ["starts_after"] * 4


# --- V-03: as medidas --------------------------------------------------------------------


def test_pontas_no_fim_de_semana_e_as_medidas(lab: Episode) -> None:
    (r,) = compute_stress(BASE, None, None)
    assert r.missing is None
    assert r.window_start_date == date(2024, 1, 5)  # sexta antes do sabado
    assert r.window_end_date == date(2024, 1, 12)  # sexta antes do domingo
    assert r.period_return == Decimal("0.2000000000")  # 12/10 - 1
    assert r.drawdown == Decimal("-0.2000000000")  # 8/10 - 1, topo de 20 fora da janela
    assert r.drawdown_peak_date == date(2024, 1, 5)
    assert r.drawdown_trough_date == date(2024, 1, 9)
    assert r.recovery_date == date(2024, 1, 11)
    assert r.recovery_sessions == 2  # indices 3 -> 5


def test_pontas_no_feriado(monkeypatch: pytest.MonkeyPatch) -> None:
    # Quarta 2024-01-10 e sexta 2024-01-12 sem pregao, como feriados: inicio na quarta cai
    # na terca, fim na sexta cai na quinta.
    ep = Episode("lab", date(2024, 1, 10), date(2024, 1, 12))
    monkeypatch.setattr(stress, "EPISODES", (ep,))
    bars = serie(
        ("2024-01-09", "10"),
        ("2024-01-11", "12"),
        ("2024-01-15", "12"),
    )
    (r,) = compute_stress(bars, None, None)
    assert (r.window_start_date, r.window_end_date) == (
        date(2024, 1, 9),
        date(2024, 1, 11),
    )
    assert r.period_return == Decimal("0.2000000000")


def test_period_return_com_valor_conhecido_e_quantizacao(lab: Episode) -> None:
    # 4/3 - 1 = 0,333... -> 0.3333333333 a dez casas. Com P0 e Pn trocados: 3/4-1 = -0,25.
    bars = serie(
        ("2024-01-05", "3"),
        ("2024-01-08", "3.5"),
        ("2024-01-12", "4"),
        ("2024-01-15", "4"),
    )
    (r,) = compute_stress(bars, None, None)
    assert r.period_return == Decimal("0.3333333333")


def test_a_recuperacao_e_procurada_fora_da_janela(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Fim na quarta 01-10: a janela vai de 01-05 a 01-10, o fundo e 01-09, e a recuperacao
    # (01-11, 11 >= 10) esta depois do fim do episodio.
    monkeypatch.setattr(
        stress, "EPISODES", (Episode("lab", date(2024, 1, 6), date(2024, 1, 10)),)
    )
    (r,) = compute_stress(BASE, None, None)
    assert r.window_end_date == date(2024, 1, 10)
    assert r.drawdown_trough_date == date(2024, 1, 9)
    assert r.recovery_date == date(2024, 1, 11)
    assert r.recovery_sessions == 2


def test_sem_recuperacao_os_dois_nulos(lab: Episode) -> None:
    bars = serie(("2024-01-05", "10"), ("2024-01-08", "8"), ("2024-01-15", "9"))
    (r,) = compute_stress(bars, None, None)
    assert r.drawdown == Decimal("-0.2000000000")
    assert (r.recovery_date, r.recovery_sessions) == (None, None)


def test_queda_zero_topo_e_fundo_em_p0_sem_recuperacao(lab: Episode) -> None:
    # Nunca abaixo do topo corrente: 10, 10 (plato), 11, 12. Depois do episodio cai e volta
    # — o `max_drawdown` do M1.3, sem o tratamento, acharia "recuperacao" em 01-08.
    bars = serie(
        ("2024-01-05", "10"),
        ("2024-01-08", "10"),
        ("2024-01-09", "11"),
        ("2024-01-12", "12"),
        ("2024-01-15", "9"),
        ("2024-01-16", "12"),
    )
    (r,) = compute_stress(bars, None, None)
    assert r.drawdown == Decimal("0E-10")
    assert r.drawdown == 0
    assert r.drawdown_peak_date == r.drawdown_trough_date == date(2024, 1, 5)
    assert (r.recovery_date, r.recovery_sessions) == (None, None)


def test_desempate_de_topos_iguais_vale_o_primeiro(lab: Episode) -> None:
    # 10 (01-05), 8, 10 (01-09), 7 (01-10): a queda e 7/10-1 = -0,3, medida do PRIMEIRO
    # topo de 10. Com o topo trocado por `>=`, o topo seria 01-09.
    bars = serie(
        ("2024-01-05", "10"),
        ("2024-01-08", "8"),
        ("2024-01-09", "10"),
        ("2024-01-10", "7"),
        ("2024-01-12", "8"),
        ("2024-01-15", "8"),
    )
    (r,) = compute_stress(bars, None, None)
    assert r.drawdown == Decimal("-0.3000000000")
    assert r.drawdown_peak_date == date(2024, 1, 5)
    assert r.drawdown_trough_date == date(2024, 1, 10)


def test_desempate_de_quedas_iguais_vale_a_primeira(lab: Episode) -> None:
    # 10, 8 (01-08), 10 (01-09), 8 (01-10): duas quedas de -0,2; fica a de 01-08, que
    # recupera em 01-09 (indice 2 - 1 = 1 pregao).
    bars = serie(
        ("2024-01-05", "10"),
        ("2024-01-08", "8"),
        ("2024-01-09", "10"),
        ("2024-01-10", "8"),
        ("2024-01-12", "9"),
        ("2024-01-15", "9"),
    )
    (r,) = compute_stress(bars, None, None)
    assert r.drawdown_trough_date == date(2024, 1, 8)
    assert r.recovery_date == date(2024, 1, 9)
    assert r.recovery_sessions == 1


# --- V-03: os motivos e a precedencia ----------------------------------------------------


def test_starts_after() -> None:
    bars = serie(("2024-01-08", "10"), ("2024-01-15", "10"))
    assert missing_reason(bars, LAB, None) == "starts_after"


def test_stale_start_a_11_dias() -> None:
    # 2023-12-26 -> 2024-01-06: 11 dias corridos.
    bars = serie(("2023-12-26", "10"), ("2024-01-08", "10"), ("2024-01-15", "10"))
    assert missing_reason(bars, LAB, None) == "stale_start"


def test_a_fronteira_de_10_dias_nao_tem_motivo() -> None:
    # 2023-12-27 -> 2024-01-06: 10 dias corridos, ainda aceito.
    bars = serie(("2023-12-27", "10"), ("2024-01-08", "10"), ("2024-01-15", "10"))
    assert missing_reason(bars, LAB, None) is None


CALENDARIO = serie(
    ("2024-01-05", "1"),
    ("2024-01-08", "1"),
    ("2024-01-11", "1"),
    ("2024-01-12", "1"),
    ("2024-01-15", "1"),
)


def test_ends_before_parando_no_ultimo_pregao_do_calendario_nao_tem_motivo() -> None:
    # Fim no domingo 01-14; o ultimo pregao do calendario ate ali e a sexta 01-12.
    bars = serie(("2024-01-05", "10"), ("2024-01-08", "10"), ("2024-01-12", "10"))
    assert missing_reason(bars, LAB, CALENDARIO) is None


def test_ends_before_um_pregao_antes() -> None:
    bars = serie(("2024-01-05", "10"), ("2024-01-08", "10"), ("2024-01-11", "10"))
    assert missing_reason(bars, LAB, CALENDARIO) == "ends_before"


def test_no_trading() -> None:
    # Base na sexta 01-05 e a serie continua em 01-15, mas nenhum pregao em (01-06, 01-14].
    bars = serie(("2024-01-05", "10"), ("2024-01-15", "10"))
    assert missing_reason(bars, LAB, None) == "no_trading"


def test_precedencia_serie_que_acaba_antes_do_inicio_e_ends_before() -> None:
    # Base em 01-03 (3 dias, nao e velha) e a serie acaba ali: tambem nao ha negocio na
    # janela, mas o motivo verdadeiro e o fim da serie.
    bars = serie(("2024-01-02", "10"), ("2024-01-03", "10"))
    assert missing_reason(bars, LAB, None) == "ends_before"


def test_precedencia_base_velha_com_serie_curta_e_stale_start() -> None:
    # Base em 2023-12-20 (17 dias) e a serie para em 01-08, antes do fim do mercado.
    bars = serie(("2023-12-20", "10"), ("2024-01-08", "10"))
    assert missing_reason(bars, LAB, CALENDARIO) == "stale_start"


def test_com_motivo_as_medidas_do_ativo_sao_nulas(lab: Episode) -> None:
    bars = serie(("2024-01-08", "10"), ("2024-01-15", "10"))
    (r,) = compute_stress(bars, None, None)
    assert r.missing == "starts_after"
    assert (r.start_date, r.end_date) == (LAB.start, LAB.end)
    medidas = (
        r.window_start_date,
        r.window_end_date,
        r.period_return,
        r.drawdown,
        r.drawdown_peak_date,
        r.drawdown_trough_date,
        r.recovery_date,
        r.recovery_sessions,
    )
    assert medidas == (None,) * 8


# --- V-03: o indice ----------------------------------------------------------------------


def test_o_indice_e_calculado_com_o_ativo_sem_dado(lab: Episode) -> None:
    ativo = serie(("2024-01-08", "10"), ("2024-01-15", "10"))  # starts_after
    (r,) = compute_stress(ativo, BASE, BASE)
    assert r.missing == "starts_after"
    assert r.benchmark_period_return == Decimal("0.2000000000")
    assert r.benchmark_drawdown == Decimal("-0.2000000000")
    assert r.benchmark_recovery_sessions == 2


def test_o_indice_ao_lado_do_ativo_com_dado(lab: Episode) -> None:
    ativo = serie(("2024-01-05", "3"), ("2024-01-08", "3.5"), ("2024-01-12", "4"))
    (r,) = compute_stress(ativo, BASE, BASE)
    assert r.period_return == Decimal("0.3333333333")
    assert r.benchmark_period_return == Decimal("0.2000000000")


def test_sem_indice_as_tres_nulas(lab: Episode) -> None:
    # O proprio IBOV, ou sem IBOV no catalogo: `benchmark=None`.
    (r,) = compute_stress(BASE, None, BASE)
    assert r.missing is None
    assert (
        r.benchmark_period_return,
        r.benchmark_drawdown,
        r.benchmark_recovery_sessions,
    ) == (None, None, None)


def test_indice_que_comeca_depois_fica_nulo(lab: Episode) -> None:
    indice = serie(("2024-01-08", "10"), ("2024-01-15", "10"))
    (r,) = compute_stress(BASE, indice, indice)
    assert r.missing is None
    assert r.benchmark_period_return is None
    assert r.benchmark_drawdown is None
    assert r.benchmark_recovery_sessions is None


def test_indice_cortado_dentro_do_episodio_fica_nulo(lab: Episode) -> None:
    # A serie do indice para na quarta 01-10, antes do fim do episodio: avaliado sem
    # calendario, e `ends_before`. Com ele como calendario de si mesmo, mediria a janela
    # parcial de 01-05 a 01-10 em silencio.
    indice = serie(
        ("2024-01-05", "10"),
        ("2024-01-08", "9"),
        ("2024-01-09", "8"),
        ("2024-01-10", "9"),
    )
    (r,) = compute_stress(BASE, indice, None)
    assert r.missing is None
    assert r.benchmark_period_return is None
    assert r.benchmark_drawdown is None
    assert r.benchmark_recovery_sessions is None


# --- V-04: a pureza ----------------------------------------------------------------------


def test_stress_so_importa_a_biblioteca_padrao_e_metrics() -> None:
    fonte = Path(stress.__file__).read_text(encoding="utf-8")
    permitidos = set(sys.stdlib_module_names) | {"__future__"}
    for no in ast.walk(ast.parse(fonte)):
        if isinstance(no, ast.Import):
            nomes = [a.name for a in no.names]
        elif isinstance(no, ast.ImportFrom):
            nomes = [no.module or ""]
        else:
            continue
        for nome in nomes:
            assert (
                nome.split(".")[0] in permitidos or nome == "apps.analytics.metrics"
            ), f"stress.py importa {nome}"
