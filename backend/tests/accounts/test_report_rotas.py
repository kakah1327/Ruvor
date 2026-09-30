"""M4.1, T4: as rotas de relatorio (RF-05 a RF-09, RF-11; V-06, V-08 a V-11, V-13 a V-15).

A sessao entra por `force_login` -- nunca `force_authenticate`, que deixa o pedido sem a
organizacao no contexto. A chave entra por `Bearer`, criada pelo servico do M4.2.

**A organizacao do V-08 tem U+2028 no nome**: o `JSONRenderer` do DRF escapa esse caractere e
devolve, fora isso, os mesmos bytes que `reports.to_bytes`. Sem ele no conteudo, trocar o
`HttpResponse` do download por um `Response` passaria na comparacao de bytes.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts import reports, services
from apps.accounts.models import Organization, Report, User
from apps.accounts.tenancy import organization_scope
from apps.assets.models import Asset
from apps.risk.models import RiskRun
from tests.accounts.conftest import organizacao, usuario
from tests.accounts.risco_de_teste import ativo, execucao, execucao_completa

pytestmark = pytest.mark.django_db

LISTA = "/api/v1/reports"
CORPO = {
    "id",
    "kind",
    "format_version",
    "ticker",
    "as_of_date",
    "risk_run_id",
    "sha256",
    "size_bytes",
    "created_at",
    "requested_by",
}
# LINE SEPARATOR: o `JSONRenderer` o escapa, e `to_bytes` nao (V-08)
U2028 = chr(0x2028)
NAO_ACHOU = {
    "error": {
        "code": "report_not_found",
        "message": "Relatório não encontrado.",
        "details": {},
    }
}


def _iso(instante: datetime) -> str:
    """O instante como a API o devolve: no fuso de `TIME_ZONE`, com deslocamento -- o molde
    de `tests/api/test_risco.py`."""
    return timezone.localtime(instante).isoformat()


def _sessao(user: User, *, csrf: bool = False) -> APIClient:
    cliente = APIClient(enforce_csrf_checks=csrf)
    cliente.force_login(user)
    return cliente


def _chave(user: User) -> APIClient:
    segredo = services.create_api_key(user, name="leitura", ip=None)[1]
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {segredo}")
    return cliente


def _gera(cliente: APIClient, ticker: object = "ITUB4") -> dict[str, Any]:
    resposta = cliente.post(LISTA, {"ticker": ticker}, format="json")
    assert resposta.status_code == 201, resposta.content
    corpo: dict[str, Any] = resposta.json()["report"]
    return corpo


def _erro(resposta: Any, status: int, codigo: str) -> dict[str, Any]:
    assert resposta.status_code == status, resposta.content
    assert resposta["Content-Type"] == "application/json"
    corpo: dict[str, Any] = resposta.json()
    assert set(corpo) == {"error"}
    assert set(corpo["error"]) == {"code", "message", "details"}
    assert corpo["error"]["code"] == codigo
    return corpo


def _linha(report_id: str) -> Report:
    return Report.unscoped.get(public_id=uuid.UUID(report_id))


@pytest.fixture
def org_a() -> Organization:
    return organizacao("org-a")


@pytest.fixture
def admin(org_a: Organization) -> User:
    return usuario(org_a, "adm@a.test", role="admin", name="Ana Admin")


@pytest.fixture
def member(org_a: Organization) -> User:
    return usuario(org_a, "mem@a.test", role="member", name="Mauro Member")


@pytest.fixture
def itub4() -> Asset:
    return ativo("ITUB4")


@pytest.fixture
def run(itub4: Asset) -> RiskRun:
    return execucao_completa(itub4, timezone.now() - timedelta(hours=1))


# --- V-06: gerar pela rota ------------------------------------------------------------------


def test_v06_gera_e_devolve_o_corpo(admin: User, run: RiskRun) -> None:
    corpo = _gera(_sessao(admin), " itub4 ")
    assert set(corpo) == CORPO
    linha = _linha(corpo["id"])
    assert corpo["id"] == str(linha.public_id)
    assert corpo["kind"] == "asset_risk"
    assert corpo["format_version"] == 1
    assert corpo["ticker"] == "ITUB4"
    assert corpo["as_of_date"] == "2026-09-25"
    assert corpo["risk_run_id"] == run.pk
    assert corpo["sha256"] == linha.sha256
    assert corpo["size_bytes"] == linha.size_bytes
    assert corpo["created_at"] == _iso(linha.created_at)
    assert corpo["created_at"].endswith("-03:00")
    assert corpo["requested_by"] == {"email": "adm@a.test", "name": "Ana Admin"}


@pytest.mark.parametrize(
    "corpo",
    [{}, {"ticker": ""}, {"ticker": "   "}, {"ticker": 123}, {"ticker": None}],
    ids=repr,
)
def test_v06_ticker_invalido(
    admin: User, run: RiskRun, corpo: dict[str, Any], debug: bool
) -> None:
    resposta = _sessao(admin).post(LISTA, corpo, format="json")
    erro = _erro(resposta, 400, "invalid_parameter")
    assert list(erro["error"]["details"]["fields"]) == ["ticker"]
    assert not Report.unscoped.exists()


def test_v06_corpo_que_nao_e_objeto(admin: User, run: RiskRun, debug: bool) -> None:
    resposta = _sessao(admin).post(LISTA, ["ITUB4"], format="json")
    _erro(resposta, 400, "invalid_parameter")
    assert not Report.unscoped.exists()


def test_v06_ativo_inexistente_igual_ao_do_risk(admin: User, debug: bool) -> None:
    cliente = _sessao(admin)
    corpo = _erro(
        cliente.post(LISTA, {"ticker": "xxxx3"}, format="json"), 404, "asset_not_found"
    )
    do_risk = cliente.get("/api/v1/assets/XXXX3/risk")
    assert do_risk.status_code == 404
    assert corpo == do_risk.json()
    assert corpo["error"]["details"] == {"ticker": "XXXX3"}


def test_v06_risco_nao_calculado(admin: User, itub4: Asset, debug: bool) -> None:
    execucao(itub4, RiskRun.Status.RUNNING, timezone.now())
    corpo = _erro(
        _sessao(admin).post(LISTA, {"ticker": "ITUB4"}, format="json"),
        409,
        "risk_not_calculated",
    )
    assert corpo["error"] == {
        "code": "risk_not_calculated",
        "message": "O risco de ITUB4 ainda não foi calculado.",
        "details": {"ticker": "ITUB4"},
    }
    assert not Report.unscoped.exists()


# --- V-08: o original, byte a byte ------------------------------------------------------------


@pytest.fixture
def org_u2028() -> Organization:
    return Organization.objects.create(
        name=f"Acme{U2028}Ltda", slug="acme-ltda", is_personal=False
    )


@pytest.fixture
def de_u2028(org_u2028: Organization) -> User:
    return usuario(org_u2028, "ana@acme.test", role="admin", name="Ana")


def test_v08_o_json_sao_os_bytes_guardados(de_u2028: User, run: RiskRun) -> None:
    cliente = _sessao(de_u2028)
    corpo = _gera(cliente)
    content = bytes(_linha(corpo["id"]).content)
    assert U2028.encode() in content  # o caractere que o renderizador escaparia
    resposta = cliente.get(f"{LISTA}/{corpo['id']}/json")
    assert resposta.status_code == 200
    assert resposta.content == content
    assert not hasattr(resposta, "data")  # o `HttpResponse` da view, nao um `Response`
    assert resposta["Content-Type"] == "application/json"
    nome = f"ruvor-risco-ITUB4-2026-09-25-{corpo['id'][:8]}.json"
    assert resposta["Content-Disposition"] == f'attachment; filename="{nome}"'
    assert hashlib.sha256(resposta.content).hexdigest() == corpo["sha256"]


@pytest.mark.parametrize(
    ("sufixo", "accept"),
    [("json", "application/octet-stream"), ("csv", "text/csv"), ("json", "text/csv")],
)
def test_v08_o_accept_nao_barra_o_download(
    admin: User, run: RiskRun, sufixo: str, accept: str
) -> None:
    cliente = _sessao(admin)
    corpo = _gera(cliente)
    resposta = cliente.get(f"{LISTA}/{corpo['id']}/{sufixo}", HTTP_ACCEPT=accept)
    assert resposta.status_code == 200, resposta.content


def test_v08_erro_no_download_sai_em_json(admin: User, debug: bool) -> None:
    resposta = _sessao(admin).get(f"{LISTA}/{uuid.uuid4()}/csv", HTTP_ACCEPT="text/csv")
    assert _erro(resposta, 404, "report_not_found") == NAO_ACHOU


# --- V-09: a tabela, do conteudo guardado -----------------------------------------------------


def test_v09_o_csv_e_o_do_conteudo(admin: User, itub4: Asset, run: RiskRun) -> None:
    cliente = _sessao(admin)
    corpo = _gera(cliente)
    rota = f"{LISTA}/{corpo['id']}/csv"
    resposta = cliente.get(rota)
    assert resposta.status_code == 200
    assert resposta["Content-Type"] == "text/csv; charset=utf-8"
    nome = f"ruvor-risco-ITUB4-2026-09-25-{corpo['id'][:8]}.csv"
    assert resposta["Content-Disposition"] == f'attachment; filename="{nome}"'
    assert resposta.content == reports.to_csv(_linha(corpo["id"]).content)
    linhas = list(csv.reader(io.StringIO(resposta.content.decode("utf-8"))))
    assert linhas[0] == list(reports.CSV_FIELDS)
    assert len(linhas) == 19
    # uma execucao nova do ativo nao muda o CSV do relatorio velho
    execucao_completa(itub4, timezone.now())
    assert cliente.get(rota).content == resposta.content


def test_v09_o_csv_nao_le_o_banco_de_risco(
    admin: User, org_a: Organization, run: RiskRun
) -> None:
    resultado = run.results.order_by("model_name", "-alpha").first()
    assert resultado is not None
    content = reports.to_bytes(
        {
            "results": [
                {
                    **{campo: None for campo in reports.RESULT_FIELDS},
                    "model_name": resultado.model_name,
                    "alpha": format(resultado.alpha, "f"),
                    "var_latest": "0.9999",
                    "violations": 7,
                    "adequate": True,
                }
            ]
        }
    )
    with organization_scope(org_a.pk):
        linha = Report.objects.create(
            organization=org_a,
            requested_by=admin,
            created_at=timezone.now(),
            kind=Report.Kind.ASSET_RISK,
            format_version=1,
            asset=run.asset,
            risk_run=run,
            content=content,
            sha256=hashlib.sha256(content).hexdigest(),
            size_bytes=len(content),
        )
    assert resultado.var_latest != 0  # o banco de risco tem outro numero
    resposta = _sessao(admin).get(f"{LISTA}/{linha.public_id}/csv")
    assert resposta.status_code == 200
    linhas = list(csv.reader(io.StringIO(resposta.content.decode("utf-8"))))
    assert len(linhas) == 2
    celulas = dict(zip(linhas[0], linhas[1], strict=True))
    assert celulas["var_latest"] == "0.9999"
    assert celulas["violations"] == "7"
    assert celulas["adequate"] == "true"
    assert celulas["var_mean"] == ""


# --- V-10 e V-11: listar e isolar ---------------------------------------------------------------


def test_v10_lista_os_da_organizacao_do_mais_novo_ao_mais_velho(
    admin: User, run: RiskRun
) -> None:
    cliente = _sessao(admin)
    feitos = [_gera(cliente)["id"] for _ in range(3)]
    _gera(_sessao(usuario(organizacao("org-b"), "adm@b.test", role="admin")))
    resposta = cliente.get(LISTA)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert (corpo["count"], corpo["limit"], corpo["offset"]) == (3, 50, 0)
    assert [r["id"] for r in corpo["results"]] == list(reversed(feitos))
    assert all(set(r) == CORPO for r in corpo["results"])
    pagina = cliente.get(LISTA, {"limit": 1, "offset": 1}).json()
    assert (pagina["count"], pagina["limit"], pagina["offset"]) == (3, 1, 1)
    assert [r["id"] for r in pagina["results"]] == [feitos[1]]


def test_v10_filtro_por_ticker(admin: User, run: RiskRun) -> None:
    execucao_completa(ativo("PETR4"), timezone.now() - timedelta(hours=1))
    cliente = _sessao(admin)
    _gera(cliente)
    do_petr4 = _gera(cliente, "PETR4")["id"]
    corpo = cliente.get(LISTA, {"ticker": " petr4 "}).json()
    assert (corpo["count"], [r["id"] for r in corpo["results"]]) == (1, [do_petr4])
    assert cliente.get(LISTA, {"ticker": "VALE3"}).json()["count"] == 0


@pytest.mark.parametrize(
    ("consulta", "parametro"),
    [
        ({"limit": "0"}, "limit"),
        ({"limit": "101"}, "limit"),
        ({"limit": "abc"}, "limit"),
        ({"offset": "-1"}, "offset"),
        ({"offset": "1.5"}, "offset"),
    ],
)
def test_v10_limites(
    admin: User, consulta: dict[str, str], parametro: str, debug: bool
) -> None:
    corpo = _erro(_sessao(admin).get(LISTA, consulta), 400, "invalid_parameter")
    assert corpo["error"]["details"] == {"parameter": parametro}


@pytest.mark.parametrize("sufixo", ["", "/json", "/csv"])
def test_v11_outra_organizacao_inexistente_e_nao_uuid_dao_o_mesmo_404(
    admin: User, run: RiskRun, sufixo: str, debug: bool
) -> None:
    alheio = _gera(_sessao(admin))["id"]
    de_fora = _sessao(usuario(organizacao("org-b"), "adm@b.test", role="admin"))
    for report_id in (alheio, str(uuid.uuid4()), "abc", alheio.upper()):
        resposta = de_fora.get(f"{LISTA}/{report_id}{sufixo}")
        assert _erro(resposta, 404, "report_not_found") == NAO_ACHOU, report_id
    assert de_fora.get(LISTA).json()["count"] == 0


def test_v11_member_e_admin_leem_um_o_do_outro(
    admin: User, member: User, run: RiskRun
) -> None:
    da_admin = _gera(_sessao(admin))["id"]
    do_member = _gera(_sessao(member))["id"]
    for leitor, report_id in ((member, da_admin), (admin, do_member)):
        cliente = _sessao(leitor)
        for sufixo in ("", "/json", "/csv"):
            resposta = cliente.get(f"{LISTA}/{report_id}{sufixo}")
            assert resposta.status_code == 200, (leitor.email, sufixo)
        assert cliente.get(LISTA).json()["count"] == 2


def test_v07_a_leitura_devolve_o_corpo(admin: User, run: RiskRun) -> None:
    cliente = _sessao(admin)
    gerado = _gera(cliente)
    resposta = cliente.get(f"{LISTA}/{gerado['id']}")
    assert resposta.status_code == 200
    assert resposta.json() == {"report": gerado}


# --- V-13: a chave e o anonimo --------------------------------------------------------------------


def test_v13_a_chave_lista_le_e_baixa_so_os_da_organizacao(
    admin: User, run: RiskRun
) -> None:
    gerado = _gera(_sessao(admin))
    de_fora = _gera(_sessao(usuario(organizacao("org-b"), "adm@b.test", role="admin")))
    chave = _chave(admin)
    lista = chave.get(LISTA)
    assert lista.status_code == 200
    assert [r["id"] for r in lista.json()["results"]] == [gerado["id"]]
    for sufixo in ("", "/json", "/csv"):
        assert chave.get(f"{LISTA}/{gerado['id']}{sufixo}").status_code == 200, sufixo
        resposta = chave.get(f"{LISTA}/{de_fora['id']}{sufixo}")
        assert _erro(resposta, 404, "report_not_found") == NAO_ACHOU
    assert (
        json.loads(chave.get(f"{LISTA}/{gerado['id']}/json").content)["report_id"]
        == (gerado["id"])
    )


def test_v13_a_chave_nao_gera(admin: User, run: RiskRun, debug: bool) -> None:
    resposta = _chave(admin).post(LISTA, {"ticker": "ITUB4"}, format="json")
    _erro(resposta, 403, "api_key_not_allowed")
    assert not Report.unscoped.exists()


@pytest.mark.parametrize(
    ("metodo", "sufixo"),
    [
        ("get", ""),
        ("post", ""),
        ("get", "/{id}"),
        ("get", "/{id}/json"),
        ("get", "/{id}/csv"),
    ],
)
def test_v13_anonimo_recebe_401(
    admin: User, run: RiskRun, metodo: str, sufixo: str, debug: bool
) -> None:
    report_id = _gera(_sessao(admin))["id"]
    rota = LISTA + sufixo.replace("{id}", report_id)
    anonimo = APIClient()
    if metodo == "post":
        resposta = anonimo.post(rota, {"ticker": "ITUB4"}, format="json")
    else:
        resposta = anonimo.get(rota)
    _erro(resposta, 401, "not_authenticated")
    assert Report.unscoped.count() == 1


# --- V-14: CSRF -----------------------------------------------------------------------------------


def test_v14_gerar_exige_csrf(admin: User, run: RiskRun, debug: bool) -> None:
    cliente = _sessao(admin, csrf=True)
    sem_token = cliente.post(LISTA, {"ticker": "ITUB4"}, format="json")
    assert sem_token.status_code == 403, sem_token.content
    assert not Report.unscoped.exists()
    assert cliente.get("/api/v1/auth/csrf").status_code == 204
    token = cliente.cookies["csrftoken"].value
    com_token = cliente.post(
        LISTA, {"ticker": "ITUB4"}, format="json", HTTP_X_CSRFTOKEN=token
    )
    assert com_token.status_code == 201, com_token.content
    assert Report.unscoped.count() == 1
