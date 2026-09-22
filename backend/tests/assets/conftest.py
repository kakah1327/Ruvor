"""Infraestrutura comum dos testes de `apps.assets`: guarda de rede, fixtures e fonte falsa.

`fixture_json` e funcao comum, nao fixture do pytest, e se importa por
`from tests.assets.conftest import fixture_json`.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NoReturn

import pytest

from apps.assets.b3 import B3ClientError, Page
from apps.assets.yahoo import ChartResponse

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def fixture_json(nome: str, subdir: str = "b3") -> dict[str, Any]:
    """Le `tests/fixtures/<subdir>/<nome>.json`. Os JSON tem acento: a codificacao e explicita."""
    with (FIXTURES_DIR / subdir / f"{nome}.json").open(encoding="utf-8") as arquivo:
        data: dict[str, Any] = json.load(arquivo)
    return data


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch: pytest.MonkeyPatch) -> None:
    def recusa(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("teste de assets tentou sair para a rede")

    monkeypatch.setattr("urllib.request.urlopen", recusa)


class FakeSource:
    """Fonte de companhias alimentada por cenario, no lugar do `B3Client`.

    Satisfaz estruturalmente a interface do `importer` (`list_companies` e
    `get_company`). `calls` registra cada `code_cvm` pedido, na ordem. Um `code_cvm`
    fora de `details` e cenario mal montado, e levanta `AssertionError` — nunca `{}`,
    para que "detalhe vazio" no relatorio so conte o `{}` real.
    """

    def __init__(
        self,
        pages: list[list[dict[str, Any]]],
        details: dict[str, dict[str, Any]],
        *,
        fail_listing: bool = False,
        fail_on: str | None = None,
    ) -> None:
        if fail_listing:
            assert len(pages) >= 2, (
                "fail_listing falha na pagina 2: o cenario precisa de duas"
            )
        self.pages = pages
        self.details = details
        self.fail_listing = fail_listing
        self.fail_on = fail_on
        self.calls: list[str] = []

    def list_companies(self) -> Iterator[Page]:
        total_pages = len(self.pages)
        for page_number, items in enumerate(self.pages, start=1):
            if self.fail_listing and page_number == 2:
                raise B3ClientError("fonte falsa: falha na pagina 2")
            yield Page(page_number=page_number, total_pages=total_pages, items=items)

    def get_company(self, code_cvm: str) -> dict[str, Any]:
        self.calls.append(code_cvm)
        if code_cvm == self.fail_on:
            raise B3ClientError(f"fonte falsa: falha em {code_cvm}")
        assert code_cvm in self.details, (
            f"cenario mal montado: {code_cvm} nao tem detalhe em FakeSource.details"
        )
        return self.details[code_cvm]


class FakeYahoo:
    """Fonte de series alimentada por cenario, no lugar do `YahooClient`.

    Satisfaz estruturalmente a interface `ChartSource` (`chart`). `responses` mapeia o
    simbolo pedido a uma lista consumida em ordem: cada item e uma `ChartResponse` a
    devolver ou uma excecao a levantar. `calls` registra `(symbol, period1, period2)` de
    cada pedido, na ordem. Simbolo ausente ou lista esgotada e cenario mal montado, e
    levanta `AssertionError` — nunca uma resposta vazia, para que "ativo falho" no
    relatorio so conte a falha programada.
    """

    def __init__(self, responses: dict[str, list[ChartResponse | Exception]]) -> None:
        self.responses = {symbol: list(items) for symbol, items in responses.items()}
        self.calls: list[tuple[str, int, int]] = []

    def chart(self, symbol: str, period1: int, period2: int) -> ChartResponse:
        self.calls.append((symbol, period1, period2))
        assert symbol in self.responses, (
            f"cenario mal montado: {symbol} nao tem resposta em FakeYahoo.responses"
        )
        assert self.responses[symbol], (
            f"cenario mal montado: as respostas de {symbol} em FakeYahoo se esgotaram"
        )
        response = self.responses[symbol].pop(0)
        if isinstance(response, Exception):
            raise response
        return response
