"""M2.1a, RF-05 a RF-08: papel, senha provisoria, organizacao pessoal e e-mail sem caixa.

A ordem das operacoes e contrato (V-22, "forma"):

1. a verificacao de colisao e a reescrita dos e-mails para minusculas -- antes da restricao,
   que recusaria a tabela com e-mail em caixa mista colidindo;
2. as tres colunas novas, com o valor das linhas que existem;
3. a unicidade de `Lower(email)`;
4. a promocao dos superusuarios a `admin` -- depois do `AddField` de `role`, que nasce
   `member` em todas.

As funcoes ficam no nivel do modulo, com nome, para os testes as chamarem com o registro de
apps corrente (V-22, "funcao"): migrar para tras e para a frente dentro do teste nao funciona
neste repositorio (docstring de `tests/risk/test_tasks.py`).
"""

from __future__ import annotations

from typing import Any

from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.db.models import Count
from django.db.models.functions import Lower, Trim


def _colisoes(user_model: Any) -> list[str]:
    """Os e-mails originais que colidem quando normalizados, ordenados -- pela mesma regra
    da reescrita: sem espaco nas pontas e em minusculas."""
    repetidos = (
        user_model.objects.annotate(minusculo=Lower(Trim("email")))
        .values("minusculo")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
        .values_list("minusculo", flat=True)
    )
    return sorted(
        user_model.objects.annotate(minusculo=Lower(Trim("email")))
        .filter(minusculo__in=list(repetidos))
        .values_list("email", flat=True)
    )


def verifica_e_baixa_emails(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor | None
) -> None:
    """Para se dois e-mails colidem em minusculas; senao, grava todos em minusculas."""
    user_model = apps.get_model("accounts", "User")
    colidem = _colisoes(user_model)
    if colidem:
        raise RuntimeError(
            "e-mails que colidem em minusculas, resolva antes de migrar: "
            + ", ".join(colidem)
        )
    for pk, email in user_model.objects.values_list("pk", "email"):
        normalizado = email.strip().lower()
        if normalizado != email:
            user_model.objects.filter(pk=pk).update(email=normalizado)


def promove_superusuarios(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor | None
) -> None:
    """Todo superusuario que ja existe vira `admin` da propria organizacao."""
    user_model = apps.get_model("accounts", "User")
    user_model.objects.filter(is_superuser=True).update(role="admin")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_marco1_organization")]

    operations = [
        migrations.RunPython(verifica_e_baixa_emails, migrations.RunPython.noop),
        migrations.AddField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[("admin", "Admin"), ("member", "Member")],
                default="member",
                max_length=10,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="must_change_password",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="organization",
            name="is_personal",
            field=models.BooleanField(default=False),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                Lower("email"), name="user_email_lower_uniq"
            ),
        ),
        migrations.RunPython(promove_superusuarios, migrations.RunPython.noop),
    ]
