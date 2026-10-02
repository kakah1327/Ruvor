"""V-06 do M1.7: a tabela fechada da classificacao da B3 (RF-07; D-144).

`display_classification` troca o texto **inteiro** pelo da tabela, por igualdade exata; nunca
substitui trecho. Uma regra como `replace(". ", ", ")` acertaria o "Petroleo. Gas" e
estragaria o "Maq. e Equip.", cujo ponto e abreviacao: o teste dos textos que ficam e o que a
reprova. Teste puro, sem banco.
"""

from __future__ import annotations

import pytest

from apps.assets.classification import (
    CORRECTED,
    KEPT,
    display_classification,
    unknown_dotted,
)

# A tabela do RF-07, escrita aqui de novo, e nao lida do modulo: mudar a tabela reprova.
CORRECOES = [
    ("Exploração. Refino e Distribuição", "Exploração, Refino e Distribuição"),
    ("Motores . Compressores e Outros", "Motores, Compressores e Outros"),
    ("Petróleo. Gás e Biocombustíveis", "Petróleo, Gás e Biocombustíveis"),
    (
        "Serv.Méd.Hospit..Análises e Diagnósticos",
        "Serv.Méd.Hospit., Análises e Diagnósticos",
    ),
    ("Tecidos. Vestuário e Calçados", "Tecidos, Vestuário e Calçados"),
]
FICAM = ["Máq. e Equip. Construção e Agrícolas", "Máq. e Equip. Industriais"]


@pytest.mark.parametrize(("da_b3", "mostrado"), CORRECOES)
def test_v06_as_cinco_correcoes(da_b3: str, mostrado: str) -> None:
    assert display_classification(da_b3) == mostrado


@pytest.mark.parametrize("texto", FICAM)
def test_v06_o_ponto_de_abreviacao_fica(texto: str) -> None:
    assert display_classification(texto) == texto


def test_v06_as_duas_listas_sao_exatamente_as_do_rf07() -> None:
    assert dict(CORRECOES) == CORRECTED
    assert set(FICAM) == KEPT


def test_v06_nulo_fica_nulo() -> None:
    assert display_classification(None) is None


def test_v06_texto_sem_ponto_sai_como_veio() -> None:
    assert display_classification("Financeiro") == "Financeiro"
    assert display_classification("Bancos") == "Bancos"


def test_v06_texto_com_ponto_desconhecido_sai_como_veio() -> None:
    # fora da tabela, mesmo com ". " no meio: nada de substituir trecho
    assert display_classification("Papel. Celulose e Outros") == (
        "Papel. Celulose e Outros"
    )


def test_v06_so_o_texto_inteiro_casa() -> None:
    # um texto da tabela dentro de outro maior nao e corrigido
    texto = "Petróleo. Gás e Biocombustíveis e Afins"
    assert display_classification(texto) == texto


def test_v06_unknown_dotted_distintos_em_ordem_e_fora_das_duas_listas() -> None:
    textos = [
        "Tecidos. Vestuário e Calçados",  # corrigido: fora
        "Máq. e Equip. Industriais",  # fica: fora
        "Zeta. Novo",
        None,
        "Financeiro",  # sem ponto: fora
        "Alfa. Novo",
        "Zeta. Novo",  # repetido: uma vez so
    ]

    assert unknown_dotted(textos) == ["Alfa. Novo", "Zeta. Novo"]
    assert unknown_dotted([]) == []
