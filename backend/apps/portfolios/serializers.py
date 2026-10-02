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

from apps.risk.models import RiskRun

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


# --- o risco (RF-16, RF-17) ---------------------------------------------------------------


def _var() -> serializers.DecimalField:
    return serializers.DecimalField(max_digits=18, decimal_places=10, allow_null=True)


def _brl() -> serializers.DecimalField:
    return serializers.DecimalField(max_digits=18, decimal_places=2, allow_null=True)


class PortfolioResultOut(serializers.Serializer[dict[str, Any]]):
    """As colunas do RF-05 menos `basel_zone`, mais a perda em reais (RF-16, RF-17)."""

    model_name = serializers.CharField()
    model_category = serializers.CharField()
    alpha = serializers.DecimalField(max_digits=6, decimal_places=4)
    hyperparameters = serializers.JSONField()
    var_latest = _var()
    var_mean = _var()
    violations = serializers.IntegerField(allow_null=True)
    expected_violations = serializers.DecimalField(
        max_digits=18, decimal_places=6, allow_null=True
    )
    kupiec_passed = serializers.BooleanField(allow_null=True)
    kupiec_p_value = _var()
    christoffersen_passed = serializers.BooleanField(allow_null=True)
    christoffersen_p_value = _var()
    dq_passed = serializers.BooleanField(allow_null=True)
    dq_p_value = _var()
    adequate = serializers.BooleanField(allow_null=True)
    error = serializers.CharField(allow_blank=True)
    loss_brl = _brl()


class PortfolioLevelOut(serializers.Serializer[dict[str, Any]]):
    """Um nivel, a regra do `summary` do relatorio (M4.1, RF-03): lista, sem eleger (D-65)."""

    alpha = serializers.DecimalField(max_digits=6, decimal_places=4)
    computed = serializers.ListField(child=serializers.CharField())
    var_min = _var()
    var_max = _var()
    loss_brl_min = _brl()
    loss_brl_max = _brl()
    not_rejected = serializers.ListField(child=serializers.CharField())


class PortfolioRunOut(serializers.Serializer[dict[str, Any]]):
    """A execucao fechada mais nova da versao corrente, com o manifesto (D-15)."""

    id = serializers.IntegerField()
    version = serializers.IntegerField()
    status = serializers.ChoiceField(choices=RiskRun.Status.choices)
    calculated_at = serializers.DateTimeField()
    finished_at = serializers.DateTimeField(allow_null=True)
    engine_version = serializers.CharField(allow_blank=True)
    seed = serializers.IntegerField()
    train_window_days = serializers.IntegerField()
    first_date = serializers.DateField()
    as_of_date = serializers.DateField()
    session_count = serializers.IntegerField()
    train_count = serializers.IntegerField()
    test_count = serializers.IntegerField()
    requested_models = serializers.ListField(child=serializers.CharField())
    series_sha256 = serializers.CharField()
    price_run_id = serializers.IntegerField()
    requested_by = CreatorOut()
    results = PortfolioResultOut(many=True)
    summary = PortfolioLevelOut(many=True)


class PortfolioProgressOut(serializers.Serializer[dict[str, Any]]):
    """A execucao em andamento: quantos resultados ja gravou e quantos espera."""

    id = serializers.IntegerField()
    version = serializers.IntegerField()
    calculated_at = serializers.DateTimeField()
    requested_models = serializers.ListField(child=serializers.CharField())
    results_written = serializers.IntegerField()
    results_expected = serializers.IntegerField()


class PortfolioRiskBodyOut(serializers.Serializer[dict[str, Any]]):
    portfolio_id = serializers.UUIDField()
    version = serializers.IntegerField()
    notional = _brl()
    latest = PortfolioRunOut(allow_null=True)
    in_progress = PortfolioProgressOut(allow_null=True)


class PortfolioRiskOut(serializers.Serializer[dict[str, Any]]):
    portfolio_risk = PortfolioRiskBodyOut()
