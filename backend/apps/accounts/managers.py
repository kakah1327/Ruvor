"""Gerente do usuario: criar usuario exige organizacao, e o e-mail e minusculo.

Primeira das duas camadas de obrigatoriedade da organizacao (F4-04). A segunda e o
`NOT NULL` da coluna, que vem da propria definicao do campo no modelo.

O superusuario e a excecao: sem organizacao, ele vai para a `ruvor`, a organizacao fixa da
plataforma, como `admin` (M2.1a, RF-20, D-105) -- e o que faz o `createsuperuser`
funcionar, porque o comando do Django nao tem como passar a organizacao.

O e-mail e baixado inteiro para minusculas, sem espaco nas pontas, ao criar e ao buscar
(RF-08). O `normalize_email` do Django baixa so o dominio.

Nao ha aqui gerente com escopo por organizacao: a D-41 atribui o filtro automatico ao
bloco que criar a primeira tabela privada de dominio, o M2.2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from apps.accounts.models import Organization, User

# A organizacao fixa da plataforma, criada pela `0002` de `accounts`.
PLATFORM_ORGANIZATION_SLUG = "ruvor"


class UserManager(BaseUserManager["User"]):
    """Cria usuario e superusuario, sempre com organizacao.

    Sem `use_in_migrations`, de proposito. Com ele, o `makemigrations` serializa o
    gerente na migration, que passa a importar este modulo e a instanciar a classe
    pelo nome -- e ai renomear a classe ou mover o arquivo quebra o `migrate` de
    qualquer banco a partir do zero. E a mesma razao pela qual migration de dados usa
    `apps.get_model` em vez de importar `models.py`.
    """

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        """Minusculas inteiras e sem espaco nas pontas (RF-08)."""
        return (email or "").strip().lower()

    def get_by_natural_key(self, username: str | None) -> User:
        """Busca pelo e-mail normalizado: `Ana@X.com` acha `ana@x.com`."""
        return self.get(**{self.model.USERNAME_FIELD: self.normalize_email(username)})

    def create_user(
        self,
        email: str,
        name: str,
        organization: Organization | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ) -> User:
        """Cria um usuario. Sem `email` ou sem `organization`, levanta `ValueError`.

        A organizacao e declarada com padrao `None` de proposito: quem esquecer recebe a
        recusa explicita do gerente, e nao um `TypeError` de assinatura. Sem `role`, o
        usuario e `member`.
        """
        if not email:
            raise ValueError("o usuario precisa de e-mail")
        if organization is None:
            raise ValueError("o usuario precisa de organizacao")
        extra_fields.setdefault("role", "member")
        user = self.model(
            email=self.normalize_email(email),
            name=name,
            organization=organization,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        name: str,
        organization: Organization | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ) -> User:
        """Cria um superusuario `admin`; sem organizacao, na `ruvor`."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("superusuario precisa de is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("superusuario precisa de is_superuser=True")
        if organization is None:
            # Import local: no topo seria circular, porque `models.py` importa este modulo.
            from apps.accounts.models import Organization

            organization = Organization.objects.db_manager(self._db).get(
                slug=PLATFORM_ORGANIZATION_SLUG
            )
        return self.create_user(
            email=email,
            name=name,
            organization=organization,
            password=password,
            **extra_fields,
        )
