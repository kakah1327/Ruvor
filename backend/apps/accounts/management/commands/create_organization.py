"""`manage.py create_organization --name N --slug S --admin-email E --admin-name A` (M2.1a,
RF-19, D-101).

A organizacao real nasce por comando do operador, com a primeira administradora: senha
provisoria gerada pelo servidor, troca obrigatoria no primeiro acesso. A senha e impressa
**uma vez**, na saida padrao, e nunca guardada em claro nem registrada. O evento
`user_created` vai sem ator -- quem fez foi o operador, fora da API.

Slug ou e-mail repetidos sao conferidos antes de gravar e, de novo, pelo `IntegrityError`
dentro da transacao: nos dois casos, `CommandError` e nada gravado.
"""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.core.validators import validate_email, validate_slug
from django.db import IntegrityError, transaction

from apps.accounts.audit import record
from apps.accounts.models import AccessEvent, Organization, User
from apps.accounts.passwords import generate_temporary_password
from apps.accounts.services import normalize_email


class Command(BaseCommand):
    help = "Cria uma organizacao real e a primeira administradora dela"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--name", required=True)
        parser.add_argument("--slug", required=True)
        parser.add_argument("--admin-email", required=True)
        parser.add_argument("--admin-name", required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        name: str = options["name"].strip()
        slug: str = options["slug"].strip()
        email = normalize_email(options["admin_email"])
        admin_name: str = options["admin_name"].strip()
        try:
            validate_slug(slug)
            validate_email(email)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc
        if not name or not admin_name:
            raise CommandError(
                "nome da organizacao e da administradora sao obrigatorios"
            )
        if Organization.objects.filter(slug=slug).exists():
            raise CommandError(f"a organizacao {slug} ja existe")
        if User.objects.filter(email=email).exists():
            raise CommandError(f"o e-mail {email} ja tem conta")

        senha = generate_temporary_password()
        try:
            with transaction.atomic():
                org = Organization.objects.create(
                    name=name, slug=slug, is_personal=False
                )
                admin = User.objects.create_user(
                    email=email,
                    name=admin_name,
                    organization=org,
                    password=senha,
                    role=User.Role.ADMIN,
                    must_change_password=True,
                )
                record(
                    AccessEvent.Kind.USER_CREATED,
                    email=email,
                    target=admin,
                    organization=org,
                    details={"via": "create_organization"},
                )
        except IntegrityError as exc:
            raise CommandError(f"slug ou e-mail ja existem: {exc}") from exc

        self.stdout.write(f"organizacao {slug} criada")
        self.stdout.write(f"admin {email} senha provisoria: {senha}")
