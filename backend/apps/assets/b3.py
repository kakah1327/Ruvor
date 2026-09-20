"""Cliente dos dois endpoints da B3 que a pagina "Empresas Listadas" consome.

So faz HTTP, repete e decodifica JSON. Nenhuma regra de negocio mora aqui: nao filtra
`type`, nao le `otherCodes` — isso e da conformacao. Os endpoints nao sao documentados
nem prometidos pela B3 (spec, "Contratos externos"); a `bronze` guarda a resposta crua
justamente para quando eles mudarem.

A chamada de rede e sempre `urllib.request.urlopen(...)`, com o modulo importado por
inteiro. E o ponto que a guarda de rede dos testes (`tests/assets/conftest.py`) e os
testes do cliente substituem; `from urllib.request import urlopen` escaparia dos dois.
"""

from __future__ import annotations

import base64
import importlib.metadata
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

BASE_URL = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall"
PAGE_SIZE = (
    120  # maximo aceito pela B3; acima disso a resposta vem com totalPages: null
)
MAX_ATTEMPTS = 3
BACKOFF_SECONDS: tuple[float, ...] = (
    1,
    2,
)  # espera entre a 1a e a 2a, e entre a 2a e a 3a


class B3ClientError(Exception):
    """Qualquer falha do cliente depois das tentativas, inclusive resposta sem sentido."""


@dataclass(frozen=True)
class Page:
    """Uma pagina da listagem, ja decodificada."""

    page_number: int
    total_pages: int
    items: list[dict[str, Any]]


def _encode_param(params: dict[str, Any]) -> str:
    """O parametro de caminho e o JSON dos parametros em base64, como a pagina da B3 faz."""
    raw = json.dumps(params, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def _user_agent() -> str:
    return f"Ruvor/{importlib.metadata.version('ruvor-backend')}"


class B3Client:
    """Lista companhias e busca o detalhe de uma, com ate tres tentativas por chamada."""

    def __init__(
        self, timeout: float = 30.0, sleep: Callable[[float], None] = time.sleep
    ) -> None:
        self._timeout = timeout
        self._sleep = sleep
        self._user_agent = _user_agent()

    def list_companies(self) -> Iterator[Page]:
        """Percorre a listagem inteira, uma `Page` por vez, a partir da pagina 1."""
        page_number = 1
        while True:
            page = self._fetch_page(page_number)
            yield page
            if page_number >= page.total_pages:
                return
            page_number += 1

    def get_company(self, code_cvm: str) -> dict[str, Any]:
        """Detalhe de uma companhia. `codeCVM` inexistente devolve `{}`, e `{}` e devolvido."""
        param = _encode_param({"codeCVM": code_cvm, "language": "pt-br"})
        data = self._get_json(f"{BASE_URL}/GetDetail/{param}")
        if not isinstance(data, dict):
            raise B3ClientError(
                f"detalhe de {code_cvm}: esperava objeto JSON, veio {type(data).__name__}"
            )
        return data

    def _fetch_page(self, page_number: int) -> Page:
        param = _encode_param(
            {"language": "pt-br", "pageNumber": page_number, "pageSize": PAGE_SIZE}
        )
        data = self._get_json(f"{BASE_URL}/GetInitialCompanies/{param}")
        if not isinstance(data, dict):
            raise B3ClientError(
                f"listagem, pagina {page_number}: esperava objeto JSON, veio {type(data).__name__}"
            )
        page_info = data.get("page")
        results = data.get("results")
        if not isinstance(page_info, dict) or not isinstance(results, list):
            raise B3ClientError(
                f"listagem, pagina {page_number}: resposta sem `page` ou `results`"
            )
        total_pages = page_info.get("totalPages")
        if not isinstance(total_pages, int):
            # `totalPages: null` e o que a B3 devolve para pageSize invalido: resposta
            # vazia com HTTP 200. Nao e "acabou", e falha.
            raise B3ClientError(
                f"listagem, pagina {page_number}: totalPages={total_pages!r} (esperava inteiro)"
            )
        return Page(page_number=page_number, total_pages=total_pages, items=results)

    def _get_json(self, url: str) -> Any:
        body = self._get_with_retry(url)
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise B3ClientError(f"{url}: corpo nao e JSON ({exc})") from exc

    def _get_with_retry(self, url: str) -> bytes:
        """Ate MAX_ATTEMPTS tentativas. Repete em timeout, 5xx e erro de rede; 4xx nao."""
        request = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
        last_error: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    body: bytes = response.read()
                    return body
            except urllib.error.HTTPError as exc:
                if exc.code < 500:
                    raise B3ClientError(f"{url}: HTTP {exc.code}") from exc
                last_error = exc
            except (TimeoutError, urllib.error.URLError) as exc:
                last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                self._sleep(BACKOFF_SECONDS[attempt])
        raise B3ClientError(
            f"{url}: falhou {MAX_ATTEMPTS} vezes; ultima: {last_error!r}"
        ) from last_error
