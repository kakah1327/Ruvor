"""Cliente dos zips de ITR, DFP e IPE do portal de dados abertos da CVM.

So faz HTTP e repete. Nenhuma regra de negocio mora aqui: nao abre o zip, nao calcula
hash, nao decide se o arquivo e novo nem se o 404 e do ano corrente — isso e do
`importer`. A URL e montada aqui, e so aqui (spec, "O cliente da CVM").

Repeticao no molde de `apps/assets/yahoo.py` (`_fetch`): ate tres tentativas, esperas de
1 s e 2 s, sobre timeout, 5xx e erro de rede — e tambem sobre `IncompleteRead` e
`ConnectionResetError` na leitura do corpo, que tem ate ~33 MB. Um 4xx nao repete e volta
como resposta, sem `payload` e sem `Last-Modified`. So levanta `CvmClientError` o que a
repeticao nao resolveu.

A chamada de rede e sempre `urllib.request.urlopen(...)`, com o modulo importado por
inteiro: e o ponto que a guarda `sem_rede` dos testes e os testes do cliente substituem.
"""

from __future__ import annotations

import http.client
import importlib.metadata
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC"
# `KINDS` e o intervalo do `import_fundamentals`; o IPE fica de fora dele e entra so em
# `URL_KINDS`, os tipos que `cvm_url` aceita (M3.2, RF-02b). Sem `Final`, `IPE` seria
# `str`, e nao o literal que o `importer` pede.
KINDS = ("itr", "dfp")
IPE: Final = "ipe"
URL_KINDS = (*KINDS, IPE)
MAX_ATTEMPTS = 3
BACKOFF_SECONDS: tuple[float, ...] = (
    1,
    2,
)  # espera entre a 1a e a 2a, e entre a 2a e a 3a


class CvmClientError(Exception):
    """Qualquer falha do cliente depois das tentativas."""


@dataclass(frozen=True)
class CvmHead:
    """A resposta a um `HEAD`: o status e o `Last-Modified`, se veio."""

    http_status: int
    last_modified: str | None


@dataclass(frozen=True)
class CvmDownload:
    """A resposta a um `GET`. `payload` e nulo num 4xx.

    Desvio declarado da spec, que chama esta classe de `CvmFile`: o nome colidiria com o
    modelo da `bronze`.
    """

    http_status: int
    last_modified: str | None
    url: str
    payload: bytes | None


def _user_agent() -> str:
    return f"Ruvor/{importlib.metadata.version('ruvor-backend')}"


def cvm_url(kind: str, year: int) -> str:
    """A URL do zip de `kind` e `year`: o tipo em maiuscula no caminho, minuscula no nome."""
    if kind not in URL_KINDS:
        raise ValueError(f"tipo de documento desconhecido: {kind!r}")
    return f"{BASE_URL}/{kind.upper()}/DADOS/{kind}_cia_aberta_{year}.zip"


class CvmClient:
    """`HEAD` e `GET` dos zips da CVM, com ate tres tentativas por chamada."""

    def __init__(
        self, timeout: float = 120.0, sleep: Callable[[float], None] = time.sleep
    ) -> None:
        self._timeout = timeout
        self._sleep = sleep
        self._user_agent = _user_agent()

    def head(self, kind: str, year: int) -> CvmHead:
        """So os cabecalhos do zip de `kind` e `year`."""
        request = urllib.request.Request(
            cvm_url(kind, year),
            headers={"User-Agent": self._user_agent},
            method="HEAD",
        )
        status, last_modified, _ = self._fetch(request, read_body=False)
        return CvmHead(http_status=status, last_modified=last_modified)

    def get(self, kind: str, year: int) -> CvmDownload:
        """O zip de `kind` e `year`, inteiro, com o status e o `Last-Modified`."""
        url = cvm_url(kind, year)
        request = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
        status, last_modified, payload = self._fetch(request, read_body=True)
        return CvmDownload(
            http_status=status, last_modified=last_modified, url=url, payload=payload
        )

    def _fetch(
        self, request: urllib.request.Request, *, read_body: bool
    ) -> tuple[int, str | None, bytes | None]:
        """Ate MAX_ATTEMPTS tentativas. Repete em timeout, 5xx, erro de rede e leitura
        interrompida do corpo.

        4xx nao repete e nao e falha: devolve o status, sem `Last-Modified` e sem corpo.
        """
        last_error: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    status: int = response.status
                    last_modified: str | None = response.headers.get("Last-Modified")
                    body: bytes | None = response.read() if read_body else None
                    return status, last_modified, body
            except urllib.error.HTTPError as exc:
                if exc.code < 500:
                    return exc.code, None, None
                last_error = exc
            except (
                TimeoutError,
                urllib.error.URLError,
                http.client.IncompleteRead,
                ConnectionResetError,
            ) as exc:
                last_error = exc
            if attempt < MAX_ATTEMPTS - 1:
                self._sleep(BACKOFF_SECONDS[attempt])
        raise CvmClientError(
            f"{request.full_url}: falhou {MAX_ATTEMPTS} vezes; ultima: {last_error!r}"
        ) from last_error
