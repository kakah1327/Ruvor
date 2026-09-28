"""M2.1a, T6: `manage.py create_organization` (RF-19; V-13)."""

from __future__ import annotations

import io
import re
from typing import Any

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts import services
from apps.accounts.models import AccessEvent, Organization, User
from tests.accounts.conftest import organizacao, requisicao, usuario

pytestmark = pytest.mark.django_db


def _cria(**opcoes: str) -> str:
    saida = io.StringIO()
    argumentos = {
        "name": "Acme",
        "slug": "acme",
        "admin_email": "Chefe@Acme.Test",
        "admin_name": "Chefe",
        **opcoes,
    }
    call_command(
        "create_organization",
        f"--name={argumentos['name']}",
        f"--slug={argumentos['slug']}",
        f"--admin-email={argumentos['admin_email']}",
        f"--admin-name={argumentos['admin_name']}",
        stdout=saida,
    )
    return saida.getvalue()


def test_v13_cria_organizacao_real_e_admin_com_senha_que_entra() -> None:
    saida = _cria()

    linhas = saida.splitlines()
    assert linhas[0] == "organizacao acme criada"
    achado = re.fullmatch(r"admin chefe@acme\.test senha provisoria: (\S+)", linhas[1])
    assert achado is not None
    senha = achado.group(1)

    org = Organization.objects.get(slug="acme")
    assert org.is_personal is False
    admin = User.objects.get(email="chefe@acme.test")
    assert (admin.organization, admin.role, admin.must_change_password) == (
        org,
        "admin",
        True,
    )
    services.login(requisicao(), email="chefe@acme.test", password=senha)

    (evento,) = AccessEvent.objects.filter(kind="user_created")
    assert (evento.actor, evento.target, evento.organization, evento.ip) == (
        None,
        admin,
        org,
        None,
    )
    assert evento.details == {"via": "create_organization"}
    assert senha not in str(evento.details)


def _contagens() -> tuple[int, int, int]:
    return (
        Organization.objects.count(),
        User.objects.count(),
        AccessEvent.objects.count(),
    )


def test_v13_slug_repetido_nao_grava_nada() -> None:
    organizacao("acme")
    antes = _contagens()
    with pytest.raises(CommandError, match="acme"):
        _cria()
    assert _contagens() == antes


def test_v13_email_repetido_nao_grava_nada() -> None:
    usuario(organizacao("outra"), "chefe@acme.test")
    antes = _contagens()
    with pytest.raises(CommandError, match=re.escape("chefe@acme.test")):
        _cria()
    assert _contagens() == antes


def test_v13_evento_e_mudanca_na_mesma_transacao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from apps.accounts.audit import record as record_real
    from apps.accounts.management.commands import create_organization

    def grava_e_falha(*args: Any, **kwargs: Any) -> None:
        record_real(*args, **kwargs)
        raise RuntimeError("falha depois do evento")

    monkeypatch.setattr(create_organization, "record", grava_e_falha)
    antes = _contagens()
    with pytest.raises(RuntimeError):
        _cria()
    assert _contagens() == antes


def test_v13_slug_longo_e_command_error() -> None:
    antes = _contagens()
    with pytest.raises(CommandError, match="60"):
        _cria(slug="a" * 61)
    assert _contagens() == antes
