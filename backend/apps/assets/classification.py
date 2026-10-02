"""A classificacao da B3 como a API a mostra (M1.7, RF-07; D-144).

O `silver` guarda o texto como a B3 o entrega, com ponto no lugar da virgula (D-47). A API
troca o texto inteiro pelo desta tabela; nunca substitui trecho. Texto novo com ponto, fora
das duas listas, aparece no relatorio do `import_assets` (RF-09).
"""

from collections.abc import Iterable

CORRECTED: dict[str, str] = {
    "Exploração. Refino e Distribuição": "Exploração, Refino e Distribuição",
    "Motores . Compressores e Outros": "Motores, Compressores e Outros",
    "Petróleo. Gás e Biocombustíveis": "Petróleo, Gás e Biocombustíveis",
    "Serv.Méd.Hospit..Análises e Diagnósticos": "Serv.Méd.Hospit., Análises e Diagnósticos",
    "Tecidos. Vestuário e Calçados": "Tecidos, Vestuário e Calçados",
}

# O ponto e abreviacao: ficam como vieram.
KEPT: frozenset[str] = frozenset(
    {
        "Máq. e Equip. Construção e Agrícolas",
        "Máq. e Equip. Industriais",
    }
)


def display_classification(text: str | None) -> str | None:
    if text is None:
        return None
    return CORRECTED.get(text, text)


def unknown_dotted(texts: Iterable[str | None]) -> list[str]:
    """Os textos com ponto fora das duas listas, distintos e em ordem alfabetica (RF-09)."""
    return sorted(
        {
            t
            for t in texts
            if t is not None and "." in t and t not in CORRECTED and t not in KEPT
        }
    )
