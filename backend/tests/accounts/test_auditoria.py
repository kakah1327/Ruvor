"""M2.1a, T3: `core.access_event` so cresce (RF-23, RF-25; V-18, imutabilidade).

Os quatro caminhos de escrita que alteram ou apagam -- `save` de linha existente, `delete`
da instancia, `update` e `delete` do `QuerySet` -- levantam, e a linha continua igual no
banco. O que cada evento grava, coluna a coluna, e dos testes dos servicos (T4 a T6).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from apps.accounts.audit import record
from apps.accounts.models import AccessEvent
from tests.accounts.conftest import organizacao, usuario

pytestmark = pytest.mark.django_db


def _evento() -> AccessEvent:
    org = organizacao()
    return record(
        "login",
        email="ana@x.test",
        actor=usuario(org, "ana@x.test"),
        organization=org,
        ip="127.0.0.1",
    )


def test_record_grava_as_colunas_e_details_vazio() -> None:
    evento = _evento()
    evento.refresh_from_db()
    assert evento.kind == "login"
    assert evento.email == "ana@x.test"
    assert evento.actor is not None
    assert evento.target is None
    assert evento.ip == "127.0.0.1"
    assert evento.details == {}


def test_record_aceita_ip_nulo_e_sem_ator() -> None:
    evento = record("user_created", email="x@x.test", details={"via": "comando"})
    evento.refresh_from_db()
    assert evento.ip is None
    assert evento.actor is None
    assert evento.details == {"via": "comando"}


def _salva_de_novo(evento: AccessEvent) -> None:
    evento.email = "outro@x.test"
    evento.save()


def _apaga(evento: AccessEvent) -> None:
    evento.delete()


def _atualiza_em_massa(evento: AccessEvent) -> None:
    AccessEvent.objects.filter(pk=evento.pk).update(email="outro@x.test")


def _apaga_em_massa(evento: AccessEvent) -> None:
    AccessEvent.objects.filter(pk=evento.pk).delete()


@pytest.mark.parametrize(
    "escrita", [_salva_de_novo, _apaga, _atualiza_em_massa, _apaga_em_massa]
)
def test_v18_so_cresce(escrita: Callable[[AccessEvent], None]) -> None:
    evento = _evento()
    with pytest.raises(TypeError, match="so cresce"):
        escrita(evento)
    guardado = AccessEvent.objects.get(pk=evento.pk)
    assert guardado.email == "ana@x.test"
