"""M4.1, T3: gerar, listar e ler relatorio pelo servico (RF-05 a RF-07, RF-10, RF-12).

**Sem contexto de organizacao posto**: os servicos sao chamados direto, sem rota e sem
autenticador, e se escopam sozinhos com a organizacao de quem pede (V-11). O `autouse`
`cache_e_organizacao_limpos` de `tests/conftest.py` zera o contexto antes de cada teste, e os
testes conferem que ele continua vazio depois de cada chamada.

As conferencias contra o banco usam `Report.unscoped`, que dispensa o contexto: a lista fechada
de `CHAMADORES_DE_UNSCOPED` varre `apps/`, nao `tests/`.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import pytest
from django.utils import timezone

from apps.accounts import reports, services
from apps.accounts.errors import AccountError
from apps.accounts.models import Organization, Report, User
from apps.accounts.tenancy import current_organization_id, organization_scope
from apps.assets.models import Asset
from apps.risk.models import RiskRun
from tests.accounts.conftest import organizacao, usuario
from tests.accounts.risco_de_teste import (
    ativo,
    execucao,
    execucao_completa,
    resultado,
)

pytestmark = pytest.mark.django_db

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


def _erro(chamada: Callable[[], object]) -> AccountError:
    with pytest.raises(AccountError) as info:
        chamada()
    assert current_organization_id() is None  # o servico restaura o contexto no erro
    return info.value


def _gera(actor: User, ticker: object = "ITUB4") -> Report:
    report = services.generate_report(actor, ticker)
    assert current_organization_id() is None  # e na saida normal
    return report


def _conteudo(report: Report) -> dict[str, Any]:
    dados: dict[str, Any] = json.loads(bytes(report.content))
    return dados


def _admin(org: Organization, email: str = "adm@a.test") -> User:
    return usuario(org, email, role="admin", name="Ana Admin")


@pytest.fixture
def org_a() -> Organization:
    return organizacao("org-a")


@pytest.fixture
def admin(org_a: Organization) -> User:
    return _admin(org_a)


@pytest.fixture
def member(org_a: Organization) -> User:
    return usuario(org_a, "mem@a.test", role="member", name="Mauro Member")


@pytest.fixture
def itub4() -> Asset:
    return ativo("ITUB4")


@pytest.fixture
def run(itub4: Asset) -> RiskRun:
    return execucao_completa(itub4, timezone.now() - timedelta(hours=1))


# --- V-06: gerar -------------------------------------------------------------------------


def test_v06_a_linha_com_a_organizacao_e_a_pessoa(
    admin: User, org_a: Organization, itub4: Asset, run: RiskRun
) -> None:
    assert current_organization_id() is None
    report = _gera(admin)
    linha = Report.unscoped.get(pk=report.pk)
    assert linha.organization_id == org_a.pk
    assert linha.requested_by_id == admin.pk
    assert linha.asset_id == itub4.pk
    assert linha.risk_run_id == run.pk
    assert linha.kind == "asset_risk"
    assert linha.format_version == 1
    content = bytes(linha.content)
    assert linha.sha256 == hashlib.sha256(content).hexdigest()
    assert linha.size_bytes == len(content)
    dados = _conteudo(linha)
    assert dados["report_id"] == str(linha.public_id)
    assert isinstance(dados["generated_at"], str)
    assert datetime.fromisoformat(dados["generated_at"]) == linha.created_at
    assert dados["organization"] == {"slug": "org-a", "name": org_a.name}
    assert dados["requested_by"] == {"name": "Ana Admin"}
    assert len(dados["results"]) == 18


def test_v06_ticker_aparado_e_minusculo_acha_o_ativo(
    admin: User, itub4: Asset, run: RiskRun
) -> None:
    report = _gera(admin, " itub4 ")
    assert report.asset_id == itub4.pk
    assert _conteudo(report)["asset"]["ticker"] == "ITUB4"


@pytest.mark.parametrize("ticker", ["", "   ", None, 123], ids=repr)
def test_v06_ticker_invalido(admin: User, run: RiskRun, ticker: object) -> None:
    erro = _erro(lambda: services.generate_report(admin, ticker))
    assert erro.code == "invalid_parameter"
    assert list(erro.details["fields"]) == ["ticker"]
    assert erro.details["fields"]["ticker"]
    assert not Report.unscoped.exists()


def test_v06_ativo_inexistente(admin: User, run: RiskRun) -> None:
    erro = _erro(lambda: services.generate_report(admin, " xxxx3 "))
    assert erro.code == "asset_not_found"
    # a mesma mensagem e os mesmos `details` do `_asset` de `apps/api/views.py`
    assert erro.message == "Ativo XXXX3 não existe."
    assert erro.details == {"ticker": "XXXX3"}


def test_v06_sem_execucao_fechada(admin: User) -> None:
    ativo("PETR4")
    erro = _erro(lambda: services.generate_report(admin, "petr4"))
    assert erro.code == "risk_not_calculated"
    assert erro.message == "O risco de PETR4 ainda não foi calculado."
    assert erro.details == {"ticker": "PETR4"}
    # so uma `running` tambem nao basta
    execucao(Asset.objects.get(ticker="PETR4"), RiskRun.Status.RUNNING, timezone.now())
    erro = _erro(lambda: services.generate_report(admin, "PETR4"))
    assert erro.code == "risk_not_calculated"
    assert not Report.unscoped.exists()


def test_v06_uma_running_mais_nova_e_ignorada(
    admin: User, itub4: Asset, run: RiskRun
) -> None:
    mais_nova = execucao(itub4, RiskRun.Status.RUNNING, timezone.now())
    assert mais_nova.calculated_at > run.calculated_at
    report = _gera(admin)
    assert report.risk_run_id == run.pk
    assert _conteudo(report)["risk_run"]["id"] == run.pk


def test_v06_a_failed_gera(admin: User, itub4: Asset) -> None:
    falhou = execucao(itub4, RiskRun.Status.FAILED, timezone.now())
    resultado(falhou, "garch_1_1", "0.0500", var_latest=None, error="nao convergiu")
    report = _gera(admin)
    assert report.risk_run_id == falhou.pk
    dados = _conteudo(report)
    assert dados["risk_run"]["status"] == "failed"
    assert dados["results"][0]["error"] == "nao convergiu"


def test_v06_a_fechada_mais_nova_entre_as_fechadas(
    admin: User, itub4: Asset, run: RiskRun
) -> None:
    parcial = execucao(itub4, RiskRun.Status.PARTIAL, timezone.now())
    assert _gera(admin).risk_run_id == parcial.pk


def test_v06_gerar_duas_vezes_da_dois_relatorios(admin: User, run: RiskRun) -> None:
    primeiro = _gera(admin)
    segundo = _gera(admin)
    assert primeiro.pk != segundo.pk
    assert primeiro.public_id != segundo.public_id
    assert primeiro.sha256 != segundo.sha256
    assert Report.unscoped.count() == 2


def test_v06_os_resultados_na_ordem_do_risk(admin: User, run: RiskRun) -> None:
    dados = _conteudo(_gera(admin))
    ordem = [(r["model_name"], r["alpha"]) for r in dados["results"]]
    esperado = [
        (r.model_name, format(r.alpha, "f"))
        for r in run.results.order_by("model_name", "-alpha")
    ]
    assert ordem == esperado
    assert ordem[0] == ("caviar", "0.0500")
    assert ordem[1] == ("caviar", "0.0100")


# --- V-07: a foto nao muda -----------------------------------------------------------------


def test_v07_execucao_nova_nao_muda_o_relatorio(
    admin: User, itub4: Asset, run: RiskRun
) -> None:
    primeiro = _gera(admin)
    antes = bytes(Report.unscoped.get(pk=primeiro.pk).content)
    nova = execucao_completa(itub4, timezone.now())
    lido = services.get_report(admin, str(primeiro.public_id))
    assert current_organization_id() is None
    assert bytes(lido.content) == antes
    assert lido.risk_run_id == run.pk
    # e o relatorio novo e da execucao nova
    assert _gera(admin).risk_run_id == nova.pk


# --- o corpo `report` ------------------------------------------------------------------------


def test_report_body_lista_fechada(admin: User, run: RiskRun) -> None:
    report = services.get_report(admin, str(_gera(admin).public_id))
    corpo = services.report_body(report)
    assert set(corpo) == CORPO
    assert corpo["id"] == str(report.public_id)
    assert corpo["kind"] == "asset_risk"
    assert corpo["format_version"] == 1
    assert corpo["ticker"] == "ITUB4"
    assert corpo["as_of_date"] == "2026-09-25"
    assert corpo["risk_run_id"] == run.pk
    assert corpo["sha256"] == report.sha256
    assert corpo["size_bytes"] == report.size_bytes
    # o fuso do projeto, como o `DateTimeField` do DRF; o conteudo leva o mesmo instante em UTC
    assert corpo["created_at"] == timezone.localtime(report.created_at).isoformat()
    assert corpo["created_at"].endswith("-03:00")
    assert datetime.fromisoformat(corpo["created_at"]) == report.created_at
    assert _conteudo(report)["generated_at"].endswith("+00:00")
    assert corpo["requested_by"] == {"email": "adm@a.test", "name": "Ana Admin"}


def test_report_body_le_a_pessoa_atual_e_o_conteudo_nao_muda(
    admin: User, run: RiskRun
) -> None:
    gerado = _gera(admin)
    admin.name = "Ana Renomeada"
    admin.save(update_fields=["name"])
    lido = services.get_report(admin, str(gerado.public_id))
    assert services.report_body(lido)["requested_by"]["name"] == "Ana Renomeada"
    assert _conteudo(lido)["requested_by"] == {"name": "Ana Admin"}


# --- V-10: listar ---------------------------------------------------------------------------


def test_v10_so_os_da_organizacao_do_mais_novo_ao_mais_velho(
    admin: User, run: RiskRun
) -> None:
    feitos = [_gera(admin) for _ in range(3)]
    org_b = organizacao("org-b")
    de_b = _gera(_admin(org_b, "adm@b.test"))
    total, pagina = services.list_reports(admin)
    assert current_organization_id() is None
    assert total == 3
    assert [r.pk for r in pagina] == [r.pk for r in reversed(feitos)]
    total_b, pagina_b = services.list_reports(User.objects.get(email="adm@b.test"))
    assert (total_b, [r.pk for r in pagina_b]) == (1, [de_b.pk])


def test_v10_empate_no_created_at_desempata_pelo_id(
    admin: User, org_a: Organization, run: RiskRun
) -> None:
    instante = timezone.now()
    ids = []
    with organization_scope(org_a.pk):
        for _ in range(2):
            ids.append(
                Report.objects.create(
                    organization=org_a,
                    requested_by=admin,
                    created_at=instante,
                    kind=Report.Kind.ASSET_RISK,
                    format_version=1,
                    asset=run.asset,
                    risk_run=run,
                    content=b"{}",
                    sha256=hashlib.sha256(b"{}").hexdigest(),
                    size_bytes=2,
                ).pk
            )
    _, pagina = services.list_reports(admin)
    assert [r.pk for r in pagina] == sorted(ids, reverse=True)


def test_v10_paginacao_e_limites(admin: User, run: RiskRun) -> None:
    feitos = list(reversed([_gera(admin) for _ in range(3)]))
    total, pagina = services.list_reports(admin, limit=2, offset=1)
    assert total == 3
    assert [r.pk for r in pagina] == [feitos[1].pk, feitos[2].pk]
    assert [r.pk for r in services.list_reports(admin, limit=1)[1]] == [feitos[0].pk]
    assert len(services.list_reports(admin, limit=100)[1]) == 3
    assert services.list_reports(admin, offset=3) == (3, [])


@pytest.mark.parametrize(
    ("limit", "offset", "parametro", "mensagem"),
    [
        (0, 0, "limit", "`limit` vai de 1 a 100."),
        (101, 0, "limit", "`limit` vai de 1 a 100."),
        (10, -1, "offset", "`offset` não pode ser negativo."),
    ],
)
def test_v10_parametros_fora_da_faixa(
    admin: User, limit: int, offset: int, parametro: str, mensagem: str
) -> None:
    erro = _erro(lambda: services.list_reports(admin, limit=limit, offset=offset))
    assert erro.code == "invalid_parameter"
    assert erro.message == mensagem
    assert erro.details == {"parameter": parametro}


def test_v10_ticker_filtra(admin: User, run: RiskRun) -> None:
    execucao_completa(ativo("PETR4"), timezone.now() - timedelta(hours=1))
    do_itub4 = _gera(admin)
    do_petr4 = _gera(admin, "PETR4")
    assert services.list_reports(admin, ticker=" petr4 ") == (1, [do_petr4])
    assert services.list_reports(admin, ticker="ITUB4") == (1, [do_itub4])
    assert services.list_reports(admin, ticker="   ") == (0, [])
    assert services.list_reports(admin, ticker="VALE3") == (0, [])
    assert services.list_reports(admin, ticker=None)[0] == 2


def test_v10_a_lista_nao_le_o_conteudo(admin: User, run: RiskRun) -> None:
    _gera(admin)
    _, pagina = services.list_reports(admin)
    assert "content" in pagina[0].get_deferred_fields()
    assert set(services.report_body(pagina[0])) == CORPO


# --- V-11: isolar ---------------------------------------------------------------------------


def test_v11_outra_organizacao_nao_acha(admin: User, run: RiskRun) -> None:
    report = _gera(admin)
    de_fora = _admin(organizacao("org-b"), "adm@b.test")
    erro = _erro(lambda: services.get_report(de_fora, str(report.public_id)))
    assert (erro.code, erro.message, erro.details) == (
        "report_not_found",
        "Relatório não encontrado.",
        {},
    )
    assert services.list_reports(de_fora) == (0, [])


def test_v11_member_e_admin_leem_um_o_do_outro(
    admin: User, member: User, run: RiskRun
) -> None:
    da_admin = _gera(admin)
    do_member = _gera(member)
    assert services.get_report(member, str(da_admin.public_id)).pk == da_admin.pk
    assert services.get_report(admin, str(do_member.public_id)).pk == do_member.pk
    assert services.list_reports(member)[0] == 2
    assert services.list_reports(admin)[0] == 2


def test_v11_a_forma_canonica_acha(admin: User, run: RiskRun) -> None:
    report = _gera(admin)
    assert services.get_report(admin, str(report.public_id)).pk == report.pk
    assert current_organization_id() is None


@pytest.mark.parametrize(
    "forma",
    [
        "maiusculas",
        "sem_hifens",
        "entre_chaves",
        "urn",
        "abc",
        "inexistente",
        "vazio",
    ],
)
def test_v11_fora_da_forma_canonica_ou_inexistente(
    admin: User, run: RiskRun, forma: str
) -> None:
    report = _gera(admin)
    canonico = str(report.public_id)
    texto = {
        "maiusculas": canonico.upper(),
        "sem_hifens": report.public_id.hex,
        "entre_chaves": "{" + canonico + "}",
        "urn": f"urn:uuid:{canonico}",
        "abc": "abc",
        "inexistente": str(uuid.uuid4()),
        "vazio": "",
    }[forma]
    # as formas que o `uuid.UUID` aceitaria apontam para o mesmo relatorio
    if forma in {"maiusculas", "sem_hifens", "entre_chaves", "urn"}:
        assert uuid.UUID(texto) == report.public_id
    erro = _erro(lambda: services.get_report(admin, texto))
    assert (erro.code, erro.message, erro.details) == (
        "report_not_found",
        "Relatório não encontrado.",
        {},
    )


# --- a lista de estados fechados ------------------------------------------------------------


def test_closed_run_statuses_igual_a_da_api() -> None:
    from apps.api import views as api_views

    assert reports.CLOSED_RUN_STATUSES == tuple(
        str(status) for status in api_views.CLOSED_RUN_STATUSES
    )
