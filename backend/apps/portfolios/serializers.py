"""Os corpos das rotas da carteira (M2.2a, RF-08 a RF-12, RF-21).

**Os `*In`** conferem a forma (RF-09.1): o erro vira 400 `invalid_parameter` com `details.fields`,
pelo tratador de `apps/api/errors.py`. O peso com mais de duas casas **reprova**, nao arredonda.
A regra de conteudo -- quantas posicoes, quais ativos, a soma -- e do servico.

**Os `*Out`** montam o corpo da resposta, a partir dos dicts que a view prepara: os decimais saem
em texto e os instantes no fuso do projeto, pelo `DecimalField` e o `DateTimeField` do DRF
(D-86, item 5).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

# --- entrada -----------------------------------------------------------------------------


def _notional() -> serializers.DecimalField:
    """Nulo, ou ate 2 casas, maior que zero e ate 16 digitos inteiros (RF-08)."""
    return serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal("0.01"),
        allow_null=True,
        required=False,
    )


class HoldingIn(serializers.Serializer[None]):
    ticker = serializers.CharField()
    weight = serializers.DecimalField(max_digits=5, decimal_places=2)


class PortfolioCreateIn(serializers.Serializer[None]):
    name = serializers.CharField(max_length=100)
    notional = _notional()
    holdings = HoldingIn(many=True)


class PortfolioUpdateIn(serializers.Serializer[None]):
    """Ao menos um dos dois (RF-11); `notional: null` tira o valor."""

    name = serializers.CharField(max_length=100, required=False)
    notional = _notional()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs:
            raise serializers.ValidationError("Informe `name`, `notional` ou os dois.")
        return attrs


class HoldingsIn(serializers.Serializer[None]):
    holdings = HoldingIn(many=True)


# --- saida -------------------------------------------------------------------------------


class HoldingOut(serializers.Serializer[dict[str, Any]]):
    ticker = serializers.CharField()
    name = serializers.CharField()
    weight = serializers.DecimalField(max_digits=5, decimal_places=2)


class CreatorOut(serializers.Serializer[dict[str, Any]]):
    email = serializers.EmailField()
    name = serializers.CharField()


class PortfolioOut(serializers.Serializer[dict[str, Any]]):
    """O corpo `portfolio`, lista fechada (RF-12): as posicoes da versao corrente, em ordem de
    ticker."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    notional = serializers.DecimalField(
        max_digits=18, decimal_places=2, allow_null=True
    )
    version = serializers.IntegerField()
    holdings = HoldingOut(many=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    version_created_at = serializers.DateTimeField()
    created_by = CreatorOut()


class PortfolioOneOut(serializers.Serializer[dict[str, Any]]):
    portfolio = PortfolioOut()


class PortfolioListOut(serializers.Serializer[dict[str, Any]]):
    count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    results = PortfolioOut(many=True)
