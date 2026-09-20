"""Conformacao: do cru da B3 (item de listagem + detalhe) para o que vira `silver.asset`.

Funcoes puras sobre dicionarios. Nada aqui importa modelo, abre transacao ou chama o
cliente — isso e do `importer`. Tambem nao decide o que fazer com um mesmo codigo em duas
companhias (RF-16): a conformacao e por companhia, e a duplicata so aparece no conjunto.

Os campos da companhia (`companyName`, `tradingName`, `cnpj`, `codeCVM`, `issuingCompany`)
vem do detalhe, como a spec fixa em "Contratos externos → A fonte → Detalhe". So o
`listing_segment` vem da listagem: e o `market` em codigo (`NM`, `N2`, ...), enquanto o
`market` do detalhe vem por extenso e nao e usado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# RF-05: codigo de acao e quatro caracteres alfanumericos seguidos do sufixo de acao ou
# unit. Debenture (`PETR-DEB62`) e recibo de subscricao (`BBAS12`) ficam de fora.
EQUITY_CODE = re.compile(r"^[A-Z0-9]{4}(3|4|5|6|7|8|11)$")

CLASSIFICATION_SEPARATOR = " / "


@dataclass(frozen=True)
class ConformedAsset:
    """Uma linha de `silver.asset` por vir, para um codigo de acao de uma companhia."""

    ticker: str
    isin: str | None
    name: str
    trading_name: str
    cnpj: str | None
    code_cvm: str | None
    issuer_code: str | None
    sector: str | None
    subsector: str | None
    segment: str | None
    listing_segment: str | None
    provider_symbol: str


@dataclass(frozen=True)
class ConformedCompany:
    """O resultado de conformar uma companhia: as acoes dela e os casos de borda."""

    assets: list[ConformedAsset]
    empty_detail: bool
    quoted_without_code: bool
    odd_classification: bool


def is_company(listing_item: dict[str, Any]) -> bool:
    """So `type == "1"` e companhia com detalhe util (RF-04)."""
    return listing_item.get("type") == "1"


def split_classification(
    text: str | None,
) -> tuple[str | None, str | None, str | None, bool]:
    """Divide `industryClassification` em (setor, subsetor, segmento, fora_do_padrao).

    Cada parte e guardada como veio — a B3 troca virgula por ponto no texto, e nao se
    adivinha onde havia virgula. Menos de tres partes: as faltantes ficam `None`. Mais de
    tres: a terceira recebe as excedentes reunidas com o mesmo separador. O booleano diz
    se o numero de partes foi diferente de tres; classificacao ausente conta como zero
    partes.
    """
    if text is None or text == "":
        return None, None, None, True
    parts = text.split(CLASSIFICATION_SEPARATOR)
    odd = len(parts) != 3
    if len(parts) > 3:
        parts = [parts[0], parts[1], CLASSIFICATION_SEPARATOR.join(parts[2:])]
    padded: list[str | None] = [*parts, None, None, None][:3]
    return padded[0], padded[1], padded[2], odd


def provider_symbol(ticker: str, kind: str) -> str:
    """RF-11: acao e `<ticker>.SA`; o Ibovespa e `^BVSP`."""
    if kind == "stock":
        return f"{ticker}.SA"
    if kind == "index" and ticker == "IBOV":
        return "^BVSP"
    raise ValueError(f"sem provider_symbol para kind={kind!r}, ticker={ticker!r}")


def _optional(value: Any) -> str | None:
    """Texto vazio ou ausente vira `None`; o resto e devolvido como veio."""
    if value is None or value == "":
        return None
    return str(value)


def conform_company(
    listing_item: dict[str, Any], detail: dict[str, Any]
) -> ConformedCompany:
    """Conforma uma companhia. `detail == {}` e "nao encontrado" e nao gera acao.

    `hasQuotation != "S"` nao gera acao e nao levanta flag nenhuma: e companhia
    registrada sem papel em bolsa, e a classificacao dela nao e lida.
    `hasQuotation == "S"` sem nenhum codigo que case o regex e o caso de borda
    `quoted_without_code` (o `ZAMP` da sonda).
    """
    if detail == {}:
        return ConformedCompany(
            assets=[],
            empty_detail=True,
            quoted_without_code=False,
            odd_classification=False,
        )

    if detail.get("hasQuotation") != "S":
        return ConformedCompany(
            assets=[],
            empty_detail=False,
            quoted_without_code=False,
            odd_classification=False,
        )

    sector, subsector, segment, odd_classification = split_classification(
        detail.get("industryClassification")
    )
    other_codes = detail.get("otherCodes") or []
    listing_segment = _optional(listing_item.get("market"))
    assets: list[ConformedAsset] = []
    for entry in other_codes:
        code = entry.get("code")
        if not isinstance(code, str) or not EQUITY_CODE.match(code):
            continue
        assets.append(
            ConformedAsset(
                ticker=code,
                isin=_optional(entry.get("isin")),
                name=str(detail.get("companyName", "")),
                trading_name=str(detail.get("tradingName", "")),
                cnpj=_optional(detail.get("cnpj")),
                code_cvm=_optional(detail.get("codeCVM")),
                issuer_code=_optional(detail.get("issuingCompany")),
                sector=sector,
                subsector=subsector,
                segment=segment,
                listing_segment=listing_segment,
                provider_symbol=provider_symbol(code, "stock"),
            )
        )

    return ConformedCompany(
        assets=assets,
        empty_detail=False,
        quoted_without_code=not assets,
        odd_classification=odd_classification,
    )
