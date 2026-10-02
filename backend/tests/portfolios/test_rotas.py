"""M2.2a, T4: as rotas da composicao (RF-08 a RF-12, RF-19 a RF-21; V-05 a V-09, V-19 a V-21 pela
rota).

A sessao entra por `force_login`; a chave, por `Bearer`, criada pelo servico do M4.2. As leituras de
conferencia vao pelo gerente base (`unscoped`).
"""

from __future__ import annotations

import ast
import uuid
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command
from django.utils import timezone
from drf_spectacular.drainage import GENERATOR_STATS
from rest_framework.test import APIClient

from apps.portfolios.models import Portfolio, PortfolioVersion
from apps.portfolios.services import create_portfolio
from apps.portfolios.views import STATUS_BY_CODE
from tests.portfolios.dados import (
    Pessoas,
    acao,
    chave,
    erro,
    org_e_pessoas,
    sessao,
)

pytestmark = pytest.mark.django_db

LISTA = "/api/v1/portfolios"
CORPO = {
    "id",
    "name",
    "notional",
    "version",
    "holdings",
    "created_at",
    "updated_at",
    "version_created_at",
    "created_by",
}
NAO_ACHOU = {
    "error": {
        "code": "portfolio_not_found",
        "message": "Carteira não encontrada.",
        "details": {},
    }
}
NOVA = {
    "name": "Renda",
    "notional": "100000.00",
    "holdings": [
        {"ticker": "VALE3", "weight": "30.00"},
        {"ticker": " petr4 ", "weight": "70"},
    ],
}
OUTRA_COMPOSICAO = {
    "holdings": [
        {"ticker": "ITUB4", "weight": "50"},
        {"ticker": "BBAS3", "weight": "50"},
    ]
}


@pytest.fixture
def pessoas() -> Pessoas:
    for ticker in ("PETR4", "VALE3", "ITUB4", "BBAS3"):
        acao(ticker, [])
    return org_e_pessoas()


def _cria(cliente: APIClient, corpo: dict[str, Any] = NOVA) -> dict[str, Any]:
    resposta = cliente.post(LISTA, corpo, format="json")
    assert resposta.status_code == 201, resposta.content
    portfolio: dict[str, Any] = resposta.json()["portfolio"]
    return portfolio


def _iso(instante: Any) -> str:
    return str(timezone.localtime(instante).isoformat())


# --- V-05: criar ------------------------------------------------------------------------


def test_v05_cria_e_devolve_a_lista_fechada(pessoas: Pessoas, debug: bool) -> None:
    resposta = sessao(pessoas.member).post(LISTA, NOVA, format="json")

    assert resposta.status_code == 201, resposta.content
    corpo = resposta.json()
    assert set(corpo) == {"portfolio"}
    portfolio = corpo["portfolio"]
    assert set(portfolio) == CORPO
    linha = Portfolio.unscoped.get(public_id=uuid.UUID(portfolio["id"]))
    versao = PortfolioVersion.unscoped.get(portfolio=linha)
    assert portfolio == {
        "id": str(linha.public_id),
        "name": "Renda",
        "notional": "100000.00",
        "version": 1,
        "holdings": [  # em ordem de ticker, nunca de peso
            {"ticker": "PETR4", "name": "PETR4 S.A.", "weight": "70.00"},
            {"ticker": "VALE3", "name": "VALE3 S.A.", "weight": "30.00"},
        ],
        "created_at": _iso(linha.created_at),
        "updated_at": _iso(linha.updated_at),
        "version_created_at": _iso(versao.created_at),
        "created_by": {"email": "member@acme.test", "name": "Pessoa de Teste"},
    }


def test_v05_sem_notional_sai_nulo(pessoas: Pessoas) -> None:
    corpo = {k: v for k, v in NOVA.items() if k != "notional"}
    assert _cria(sessao(pessoas.admin), corpo)["notional"] is None


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("name", "   "),
        ("name", "x" * 101),
        ("notional", "0"),
        ("notional", "-1"),
        ("notional", "1.001"),
        ("holdings", "PETR4"),
    ],
)
def test_v05_forma_invalida_e_invalid_parameter(
    pessoas: Pessoas, campo: str, valor: str, debug: bool
) -> None:
    resposta = sessao(pessoas.admin).post(LISTA, NOVA | {campo: valor}, format="json")
    corpo = erro(resposta, 400, "invalid_parameter")
    assert campo in corpo["error"]["details"]["fields"]
    assert not Portfolio.unscoped.exists()


def test_v05_peso_com_tres_casas_reprova_e_nao_arredonda(
    pessoas: Pessoas, debug: bool
) -> None:
    corpo = NOVA | {
        "holdings": [
            {"ticker": "PETR4", "weight": "12.345"},
            {"ticker": "VALE3", "weight": "87.655"},
        ]
    }
    resposta = sessao(pessoas.admin).post(LISTA, corpo, format="json")
    detalhes = erro(resposta, 400, "invalid_parameter")["error"]["details"]
    assert "holdings" in detalhes["fields"]
    assert not Portfolio.unscoped.exists()


# --- V-06: a regra da composicao pela rota ----------------------------------------------


def test_v06_invalid_holdings_com_os_details_do_servico(
    pessoas: Pessoas, debug: bool
) -> None:
    corpo = NOVA | {
        "holdings": [
            {"ticker": "PETR4", "weight": "50"},
            {"ticker": "XXXX3", "weight": "50"},
        ]
    }
    resposta = sessao(pessoas.admin).post(LISTA, corpo, format="json")
    assert erro(resposta, 400, "invalid_holdings")["error"] == {
        "code": "invalid_holdings",
        "message": "Composição inválida.",
        "details": {
            "reason": "items",
            "items": [{"index": 1, "ticker": "XXXX3", "reason": "unknown_ticker"}],
        },
    }


def test_v06_a_soma_pela_rota_sai_com_duas_casas(pessoas: Pessoas) -> None:
    corpo = NOVA | {
        "holdings": [
            {"ticker": "PETR4", "weight": "33.3"},
            {"ticker": "VALE3", "weight": "66.6"},
        ]
    }
    resposta = sessao(pessoas.admin).post(LISTA, corpo, format="json")
    assert erro(resposta, 400, "invalid_holdings")["error"]["details"] == {
        "reason": "weights_sum",
        "sum": "99.90",
    }


# --- V-07: listar, ler, mudar, arquivar -------------------------------------------------


def test_v07_lista_com_limit_e_offset(pessoas: Pessoas, debug: bool) -> None:
    cliente = sessao(pessoas.admin)
    criadas = [_cria(cliente, NOVA | {"name": f"c{i}"}) for i in range(3)]
    _cria(sessao(pessoas.de_fora), NOVA | {"name": "de fora"})

    tudo = cliente.get(LISTA)
    assert tudo.status_code == 200, tudo.content
    assert tudo.json()["count"] == 3
    assert [p["id"] for p in tudo.json()["results"]] == [
        p["id"] for p in reversed(criadas)
    ]

    pagina = cliente.get(LISTA, {"limit": 1, "offset": 1}).json()
    assert (pagina["count"], pagina["limit"], pagina["offset"]) == (3, 1, 1)
    assert [p["id"] for p in pagina["results"]] == [criadas[1]["id"]]
    assert set(pagina["results"][0]) == CORPO


@pytest.mark.parametrize(
    "consulta", [{"limit": "abc"}, {"limit": "0"}, {"offset": "-1"}]
)
def test_v07_limit_e_offset_invalidos(
    pessoas: Pessoas, consulta: dict[str, str], debug: bool
) -> None:
    erro(sessao(pessoas.admin).get(LISTA, consulta), 400, "invalid_parameter")


def test_v07_ler_uma(pessoas: Pessoas) -> None:
    cliente = sessao(pessoas.admin)
    criada = _cria(cliente)
    resposta = cliente.get(f"{LISTA}/{criada['id']}")
    assert resposta.status_code == 200, resposta.content
    assert resposta.json() == {"portfolio": criada}


def test_v07_patch_vazio_e_invalid_parameter(pessoas: Pessoas, debug: bool) -> None:
    cliente = sessao(pessoas.admin)
    criada = _cria(cliente)
    erro(
        cliente.patch(f"{LISTA}/{criada['id']}", {}, format="json"),
        400,
        "invalid_parameter",
    )


def test_v07_patch_notional_nulo_e_nome(pessoas: Pessoas) -> None:
    cliente = sessao(pessoas.admin)
    criada = _cria(cliente)
    resposta = cliente.patch(
        f"{LISTA}/{criada['id']}", {"notional": None, "name": "Outro"}, format="json"
    )
    assert resposta.status_code == 200, resposta.content
    portfolio = resposta.json()["portfolio"]
    assert (portfolio["notional"], portfolio["name"], portfolio["version"]) == (
        None,
        "Outro",
        1,
    )


def test_v07_delete_e_depois_404_em_tudo(pessoas: Pessoas, debug: bool) -> None:
    cliente = sessao(pessoas.admin)
    url = f"{LISTA}/{_cria(cliente)['id']}"

    resposta = cliente.delete(url)
    assert resposta.status_code == 204
    assert resposta.content == b""

    chamadas: tuple[Callable[[], Any], ...] = (
        lambda: cliente.get(url),
        lambda: cliente.patch(url, {"name": "x"}, format="json"),
        lambda: cliente.delete(url),
        lambda: cliente.put(f"{url}/holdings", OUTRA_COMPOSICAO, format="json"),
    )
    for chamada in chamadas:
        assert erro(chamada(), 404, "portfolio_not_found") == NAO_ACHOU


# --- V-08: trocar a composicao ----------------------------------------------------------


def test_v08_put_holdings_cria_a_versao_2_e_a_mesma_nao(
    pessoas: Pessoas, debug: bool
) -> None:
    cliente = sessao(pessoas.member)
    url = f"{LISTA}/{_cria(sessao(pessoas.admin))['id']}/holdings"

    resposta = cliente.put(url, OUTRA_COMPOSICAO, format="json")
    assert resposta.status_code == 200, resposta.content
    portfolio = resposta.json()["portfolio"]
    assert portfolio["version"] == 2
    assert [h["ticker"] for h in portfolio["holdings"]] == ["BBAS3", "ITUB4"]

    de_novo = cliente.put(
        url, {"holdings": list(reversed(OUTRA_COMPOSICAO["holdings"]))}, format="json"
    )
    assert de_novo.status_code == 200, de_novo.content
    assert de_novo.json()["portfolio"]["version"] == 2


def test_v08_put_holdings_invalido(pessoas: Pessoas) -> None:
    cliente = sessao(pessoas.admin)
    url = f"{LISTA}/{_cria(cliente)['id']}/holdings"
    erro(cliente.put(url, {"holdings": "x"}, format="json"), 400, "invalid_parameter")
    corpo = {"holdings": [{"ticker": "PETR4", "weight": "100"}]}
    detalhes = erro(cliente.put(url, corpo, format="json"), 400, "invalid_holdings")
    assert detalhes["error"]["details"] == {"reason": "count_out_of_range", "count": 1}


# --- V-09: o mesmo 404 para o que nao e seu ---------------------------------------------


def test_v09_o_mesmo_404_para_outra_organizacao_e_id_ruim(
    pessoas: Pessoas, debug: bool
) -> None:
    criada = _cria(sessao(pessoas.admin))
    ids = [
        (pessoas.de_fora, criada["id"]),
        (pessoas.admin, str(uuid.uuid4())),
        (pessoas.admin, "abc"),
        (pessoas.admin, criada["id"].upper()),
    ]
    for quem, pid in ids:
        cliente = sessao(quem)
        url = f"{LISTA}/{pid}"
        chamadas: tuple[Callable[[], Any], ...] = (
            lambda: cliente.get(url),
            lambda: cliente.patch(url, {"name": "x"}, format="json"),
            lambda: cliente.delete(url),
            lambda: cliente.put(f"{url}/holdings", OUTRA_COMPOSICAO, format="json"),
        )
        for chamada in chamadas:
            assert erro(chamada(), 404, "portfolio_not_found") == NAO_ACHOU
    linha = Portfolio.unscoped.get(public_id=uuid.UUID(criada["id"]))
    assert (linha.name, linha.archived_at) == ("Renda", None)


# --- V-19: a chave ----------------------------------------------------------------------


def test_v19_a_chave_lista_e_le_so_a_organizacao_da_dona(
    pessoas: Pessoas, debug: bool
) -> None:
    criada = _cria(sessao(pessoas.admin))
    _cria(sessao(pessoas.de_fora), NOVA | {"name": "de fora"})
    cliente = chave(pessoas.member)

    lista = cliente.get(LISTA)
    assert lista.status_code == 200, lista.content
    assert [p["id"] for p in lista.json()["results"]] == [criada["id"]]
    uma = cliente.get(f"{LISTA}/{criada['id']}")
    assert uma.status_code == 200, uma.content


def test_v19_a_chave_nao_escreve(pessoas: Pessoas, debug: bool) -> None:
    url = f"{LISTA}/{_cria(sessao(pessoas.admin))['id']}"
    cliente = chave(pessoas.admin)
    chamadas: tuple[Callable[[], Any], ...] = (
        lambda: cliente.post(LISTA, NOVA, format="json"),
        lambda: cliente.patch(url, {"name": "x"}, format="json"),
        lambda: cliente.delete(url),
        lambda: cliente.put(f"{url}/holdings", OUTRA_COMPOSICAO, format="json"),
    )
    for chamada in chamadas:
        erro(chamada(), 403, "api_key_not_allowed")
    assert Portfolio.unscoped.count() == 1
    assert PortfolioVersion.unscoped.count() == 1


def test_v19_anonimo_recebe_401_em_todas(pessoas: Pessoas, debug: bool) -> None:
    url = f"{LISTA}/{_cria(sessao(pessoas.admin))['id']}"
    cliente = APIClient()
    chamadas: tuple[Callable[[], Any], ...] = (
        lambda: cliente.get(LISTA),
        lambda: cliente.post(LISTA, NOVA, format="json"),
        lambda: cliente.get(url),
        lambda: cliente.patch(url, {"name": "x"}, format="json"),
        lambda: cliente.delete(url),
        lambda: cliente.put(f"{url}/holdings", OUTRA_COMPOSICAO, format="json"),
    )
    for chamada in chamadas:
        erro(chamada(), 401, "not_authenticated")


# --- V-20: CSRF -------------------------------------------------------------------------


def test_v20_criar_exige_csrf(pessoas: Pessoas, debug: bool) -> None:
    cliente = sessao(pessoas.admin, csrf=True)
    sem_token = cliente.post(LISTA, NOVA, format="json")
    assert sem_token.status_code == 403, sem_token.content
    assert not Portfolio.unscoped.exists()
    assert cliente.get("/api/v1/auth/csrf").status_code == 204
    token = cliente.cookies["csrftoken"].value
    com_token = cliente.post(LISTA, NOVA, format="json", HTTP_X_CSRFTOKEN=token)
    assert com_token.status_code == 201, com_token.content


# --- V-21: o esquema --------------------------------------------------------------------


def test_v21_o_esquema_valida_sem_aviso() -> None:
    GENERATOR_STATS.reset()
    call_command("spectacular", "--validate", "--fail-on-warn", "--file", "/dev/null")


# --- RF-20: todo codigo levantado tem traducao ------------------------------------------

SERVICES = Path(__file__).resolve().parents[2] / "apps" / "portfolios" / "services.py"
# os codigos do risco, que a T5 faz nascer em `services.py`
DA_T5 = {
    "insufficient_history",
    "portfolio_risk_up_to_date",
    "portfolio_compute_busy",
    "portfolio_queue_full",
}


def _codigos_levantados() -> set[str]:
    codigos: set[str] = set()
    for no in ast.walk(ast.parse(SERVICES.read_text(encoding="utf-8"))):
        if not (
            isinstance(no, ast.Call)
            and isinstance(no.func, ast.Name)
            and no.func.id == "PortfolioError"
        ):
            continue
        primeiro = no.args[0] if no.args else None
        assert isinstance(primeiro, ast.Constant) and isinstance(primeiro.value, str), (
            f"services.py:{no.lineno}: codigo de PortfolioError nao literal"
        )
        codigos.add(primeiro.value)
    return codigos


def test_rf20_todo_codigo_levantado_tem_traducao_e_nenhuma_traducao_e_morta() -> None:
    # igualdade, e nao inclusao: com zero chamadas achadas, a inclusao passaria vazia
    assert _codigos_levantados() | DA_T5 == set(STATUS_BY_CODE)
    assert len(STATUS_BY_CODE) == 7


def test_a_carteira_criada_pelo_servico_aparece_na_rota(pessoas: Pessoas) -> None:
    portfolio = create_portfolio(
        pessoas.admin,
        name="pelo servico",
        notional=None,
        holdings=[
            {"ticker": "PETR4", "weight": Decimal("50")},
            {"ticker": "VALE3", "weight": Decimal("50")},
        ],
    )
    resposta = sessao(pessoas.member).get(f"{LISTA}/{portfolio.public_id}")
    assert resposta.status_code == 200, resposta.content
    assert resposta.json()["portfolio"]["created_by"]["email"] == pessoas.admin.email
