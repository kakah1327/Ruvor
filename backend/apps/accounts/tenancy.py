"""O filtro automatico por organizacao (M4.2, RF-13; D-41, D-112).

A consulta a uma tabela privada filtra sozinha pela organizacao do contexto, para que esquecer
o filtro deixe de ser possivel. **Sem organizacao no contexto, o gerente levanta** -- falha
fechada, nunca "devolve tudo".

**O contexto** e um `ContextVar` com o `organization_id` (um inteiro: o filtro nao precisa da
linha). Duas fontes o poem:

- a autenticacao do pedido HTTP (as classes de `apps/accounts/authentication.py`), e o
  `OrganizationScopeMiddleware` o zera no comeco e no fim de cada pedido -- o processo pode
  reusar threads, e contexto que sobra de um pedido vazaria para o seguinte;
- o proprio servico, com `organization_scope(<organization_id de quem pede>)`, que poe e
  restaura. Assim o servico funciona igual pela rota, pelo teste direto, por um comando ou numa
  thread -- uma thread nova nao herda o `ContextVar`.

**O gerente base** do modelo privado e um `Manager()` sem escopo (`Meta.base_manager_name`): o
Django o usa no `refresh_from_db`, no `save` de linha existente e na coleta da exclusao, onde nao
ha o que filtrar. **Chamada explicita ao gerente sem escopo so em lugar nomeado**, guardado por
teste (`tests/accounts/test_tenancy.py`).

Django puro, sem DRF: a varredura `test_fase1_sem_drf` continua guardando este modulo.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TypeVar

from django.db import models
from django.http import HttpRequest, HttpResponse

_M = TypeVar("_M", bound=models.Model)

_organization_id: ContextVar[int | None] = ContextVar(
    "ruvor_organization_id", default=None
)


class OrganizationScopeMissing(RuntimeError):
    """Consulta a tabela privada sem organizacao no contexto."""


def current_organization_id() -> int | None:
    return _organization_id.get()


def set_organization_id(value: int | None) -> None:
    _organization_id.set(value)


@contextmanager
def organization_scope(organization_id: int) -> Iterator[None]:
    """Poe a organizacao no contexto e, ao sair -- normal ou por excecao --, restaura a de
    antes."""
    token = _organization_id.set(organization_id)
    try:
        yield
    finally:
        _organization_id.reset(token)


class OrganizationScopedManager(models.Manager[_M]):
    """O gerente padrao da tabela privada: filtra pela organizacao do contexto.

    O caminho do campo da organizacao e atributo de classe do modelo, `organization_field`, e
    nao argumento do construtor: o acessor reverso do Django subclassa o gerente padrao e o
    constroi sem argumentos (`related_descriptors.py:682` e `:724`).
    """

    def get_queryset(self) -> models.QuerySet[_M]:
        organization_id = current_organization_id()
        if organization_id is None:
            raise OrganizationScopeMissing(
                f"{self.model.__name__} sem organizacao no contexto"
            )
        # `getattr`, e nao o atributo: o `Manager[_M]` generico nao o enxerga no `mypy`
        field: str = getattr(self.model, "organization_field")
        return super().get_queryset().filter(**{field: organization_id})


class OrganizationScopeMiddleware:
    """Zera o contexto da organizacao no comeco e no fim de cada pedido."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        set_organization_id(None)
        try:
            return self.get_response(request)
        finally:
            set_organization_id(None)
