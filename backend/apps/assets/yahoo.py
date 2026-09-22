"""Cliente do endpoint `chart` v8 do Yahoo Finance.

So faz HTTP, repete e decodifica JSON. Nenhuma regra de negocio mora aqui: nao le
`timestamp`, nao converte fuso, nao descarta pregao nulo — isso e da conformacao. O
endpoint nao e documentado nem prometido pelo Yahoo (spec, "Contratos externos"); a
`bronze` guarda a resposta crua justamente para quando ele mudar.

Diferenca em relacao ao `b3.py`: no Yahoo, um 4xx com corpo JSON e resposta, nao falha
— o 404 do simbolo inexistente vem como `ChartResponse(404, payload)` e vai para a
`bronze` como veio. So levanta `YahooClientError` o que a repeticao nao resolveu e o
corpo que nao e JSON.

A chamada de rede e sempre `urllib.request.urlopen(...)`, com o modulo importado por
inteiro. E o ponto que a guarda de rede dos testes (`tests/assets/conftest.py`) e os
testes do cliente substituem; `from urllib.request import urlopen` escaparia dos dois.
"""

from __future__ import annotations

import importlib.metadata
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

BASE_URL = "https://query2.finance.yahoo.com/v8/finance/chart"
MAX_ATTEMPTS = 3
BACKOFF_SECONDS: tuple[float, ...] = (
    1,
    2,
)  # espera entre a 1a e a 2a, e entre a 2a e a 3a


class YahooClientError(Exception):
    """Qualquer falha do cliente depois das tentativas, inclusive corpo que nao e JSON."""


@dataclass(frozen=True)
class ChartResponse:
    """Uma resposta do `chart`, ja decodificada, com o status HTTP que a trouxe."""

    http_status: int
    payload: dict[str, Any]


def _user_agent() -> str:
    return f"Ruvor/{importlib.metadata.version('ruvor-backend')}"


def _chart_url(symbol: str, period1: int, period2: int) -> str:
    query = urllib.parse.urlencode(
        {
            "period1": period1,
            "period2": period2,
            "interval": "1d",
            "events": "div,splits",
        }
    )
    return f"{BASE_URL}/{urllib.parse.quote(symbol)}?{query}"


class YahooClient:
    """Busca a serie diaria de um simbolo, com ate tres tentativas por chamada."""

    def __init__(
        self, timeout: float = 30.0, sleep: Callable[[float], None] = time.sleep
    ) -> None:
        self._timeout = timeout
        self._sleep = sleep
        self._user_agent = _user_agent()

    def chart(self, symbol: str, period1: int, period2: int) -> ChartResponse:
        """Serie diaria com dividendos e desdobramentos entre `period1` e `period2` (unix)."""
        url = _chart_url(symbol, period1, period2)
        status, body = self._fetch(url)
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise YahooClientError(
                f"{url}: HTTP {status}, corpo nao e JSON ({exc})"
            ) from exc
        if not isinstance(payload, dict):
            raise YahooClientError(
                f"{url}: HTTP {status}, esperava objeto JSON, veio {type(payload).__name__}"
            )
        return ChartResponse(http_status=status, payload=payload)

    def _fetch(self, url: str) -> tuple[int, bytes]:
        """Ate MAX_ATTEMPTS tentativas. Repete em timeout, 5xx e erro de rede.

        4xx nao repete e nao e falha: devolve o status e o corpo como vieram, para que
        `chart` decida pelo conteudo (JSON vira `ChartResponse`; o resto levanta).
        """
        request = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
        last_error: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    body: bytes = response.read()
                    return response.status, body
            except urllib.error.HTTPError as exc:
                if exc.code < 500:
                    error_body: bytes = exc.read()
                    return exc.code, error_body
                last_error = exc
            except (TimeoutError, urllib.error.URLError) as exc:
                last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                self._sleep(BACKOFF_SECONDS[attempt])
        raise YahooClientError(
            f"{url}: falhou {MAX_ATTEMPTS} vezes; ultima: {last_error!r}"
        ) from last_error
