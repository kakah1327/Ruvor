"""M2.1a, T2: papel, organizacao pessoal, senha provisoria, e-mail sem caixa e o
`createsuperuser` (RF-05 a RF-08, RF-20; V-14 e V-22).

O V-22 se prova em tres partes, como o V-10c do M1.5 (docstring de
`tests/risk/test_tasks.py`), porque migrar para tras e para a frente dentro do teste nao
funciona neste repositorio:

- **funcao**: as funcoes da `0003`, chamadas com o registro de apps corrente;
- **forma**: a lista `operations` da `0003`, na ordem do RF-08;
- **dado**: o `migrate` do banco de dev, com dado real, medido na T2 e registrado no relato.
"""

from __future__ import annotations

import importlib
from types import ModuleType, SimpleNamespace

import pytest
from django.apps import apps as django_apps
from django.core.management import call_command
from django.db import IntegrityError, connection, migrations, transaction
from django.db.models import UniqueConstraint

from apps.accounts.models import Organization, User
from tests.accounts.conftest import organizacao, usuario

pytestmark = pytest.mark.django_db


def _migration_0003() -> ModuleType:
    return importlib.import_module(
        "apps.accounts.migrations.0003_papel_email_organizacao_pessoal"
    )


def _email_cru(user: User, email: str) -> None:
    """Grava o e-mail sem passar pelo gerente, que o normalizaria."""
    User.objects.filter(pk=user.pk).update(email=email)


# --- o gerente -------------------------------------------------------------------------


def test_create_user_grava_o_email_em_minusculas_e_member() -> None:
    user = usuario(organizacao(), "  Ana@X.COM ")
    user.refresh_from_db()
    assert user.email == "ana@x.com"
    assert user.role == "member"
    assert user.must_change_password is False


def test_get_by_natural_key_normaliza() -> None:
    user = usuario(organizacao(), "ana@x.com")
    assert User.objects.get_by_natural_key("  ANA@X.com ") == user


def test_organizacao_nasce_real() -> None:
    assert Organization.objects.create(name="Nova", slug="nova").is_personal is False


def test_a_ruvor_e_real() -> None:
    assert Organization.objects.get(slug="ruvor").is_personal is False


def test_v14_createsuperuser_noinput_vai_para_a_ruvor_como_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "Adm@Ruvor.Test")
    monkeypatch.setenv("DJANGO_SUPERUSER_NAME", "Administracao")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "outra-senha-longa-77")

    call_command("createsuperuser", "--noinput", verbosity=0)

    user = User.objects.get(email="adm@ruvor.test")
    assert user.organization.slug == "ruvor"
    assert user.role == "admin"
    assert user.is_superuser is True
    assert user.is_staff is True
    assert user.check_password("outra-senha-longa-77")


def test_v14_create_user_sem_organizacao_continua_recusado() -> None:
    with pytest.raises(ValueError, match="organizacao"):
        User.objects.create_user(email="sem@org.test", name="Sem")


# --- V-22, banco ------------------------------------------------------------------------


def test_v22_banco_recusa_o_mesmo_email_em_outra_caixa() -> None:
    org = organizacao()
    usuario(org, "ana@x.com")
    with pytest.raises(IntegrityError), transaction.atomic():
        # `create` do modelo, sem o gerente: o e-mail entra cru.
        User.objects.model(
            email="Ana@x.com", name="Outra", organization=org, role="member"
        ).save()


def test_v22_a_restricao_esta_no_modelo() -> None:
    nomes = [
        constraint.name
        for constraint in User._meta.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    assert nomes == ["user_email_lower_uniq"]


# --- V-22, funcao -----------------------------------------------------------------------


def test_v22_funcao_baixa_emails_e_promove_superusuarios() -> None:
    org = organizacao()
    comum = usuario(org, "comum@x.test")
    adm = User.objects.create_superuser(
        email="adm@x.test", name="Adm", organization=org, password="x" * 12
    )
    _email_cru(comum, "Ana@X.Test")
    User.objects.filter(pk=adm.pk).update(role="member")

    migration = _migration_0003()
    migration.verifica_e_baixa_emails(django_apps, None)
    migration.promove_superusuarios(django_apps, None)

    comum.refresh_from_db()
    adm.refresh_from_db()
    assert comum.email == "ana@x.test"
    assert comum.role == "member"
    assert adm.role == "admin"


def test_v22_funcao_para_na_colisao_e_nada_muda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migration = _migration_0003()
    user = usuario(organizacao(), "caixa@x.test")
    _email_cru(user, "Caixa@X.Test")
    monkeypatch.setattr(
        migration, "_colisoes", lambda model: ["Ana@X.com", "ana@x.com"]
    )
    registro = SimpleNamespace(get_model=lambda *args: User)

    with pytest.raises(RuntimeError) as erro:
        migration.verifica_e_baixa_emails(registro, None)

    assert "Ana@X.com" in str(erro.value)
    assert "ana@x.com" in str(erro.value)
    user.refresh_from_db()
    assert user.email == "Caixa@X.Test"


def test_v22_colisoes_vazia_sem_colisao() -> None:
    org = organizacao()
    usuario(org, "a@x.test")
    usuario(org, "b@x.test")
    assert _migration_0003()._colisoes(User) == []


def test_v22_colisoes_acha_as_linhas_que_colidem() -> None:
    """Com a restricao removida -- antes de qualquer `INSERT` nesta transacao, pela
    armadilha do `pending trigger events` -- e desfeita por excecao no fim.

    Por SQL, com o esquema: o `remove_constraint` do Django emite `DROP INDEX IF EXISTS`
    sem esquema, que nao acha o indice em `core` (o `search_path` e `public`) e passa em
    silencio.
    """

    class Desfaz(Exception):
        pass

    achadas: list[str] = []
    with pytest.raises(Desfaz), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("DROP INDEX core.user_email_lower_uniq")
        org = organizacao()
        primeira = usuario(org, "ana@x.test")
        segunda = usuario(org, "outra@x.test")
        _email_cru(primeira, "Ana@X.test")
        _email_cru(segunda, "ana@x.test")
        achadas = _migration_0003()._colisoes(User)
        raise Desfaz

    assert achadas == ["Ana@X.test", "ana@x.test"]


# --- V-22, forma ------------------------------------------------------------------------


def test_v22_forma_as_operacoes_da_0003_na_ordem() -> None:
    migration = _migration_0003()
    operacoes = migration.Migration.operations
    descricao = [
        (type(op).__name__, getattr(op, "name", None) or getattr(op, "code", None))
        for op in operacoes
    ]
    assert descricao == [
        ("RunPython", migration.verifica_e_baixa_emails),
        ("AddField", "role"),
        ("AddField", "must_change_password"),
        ("AddField", "is_personal"),
        ("AddConstraint", None),
        ("RunPython", migration.promove_superusuarios),
    ]
    assert isinstance(operacoes[4], migrations.AddConstraint)
    assert operacoes[4].constraint.name == "user_email_lower_uniq"
