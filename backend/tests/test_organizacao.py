"""F4-03: a organizacao do Marco 1 existe, uma so, com o slug congelado.

Usa `django_db_blocker` e nao a marca `django_db`: a marca conecta num banco
`test_<nome>` recriado pelo pytest-django, e a organizacao que interessa e a que a
migration de dados criou no banco configurado.
"""

from pytest_django.plugin import DjangoDbBlocker

from apps.accounts.models import Organization


def test_existe_exatamente_uma_organizacao_ruvor(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    with django_db_blocker.unblock():
        organizacoes = list(Organization.objects.filter(slug="ruvor"))

    assert len(organizacoes) == 1
    assert organizacoes[0].name == "Ruvor"
