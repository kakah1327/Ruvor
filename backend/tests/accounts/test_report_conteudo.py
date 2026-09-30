"""M4.1, T2: o conteudo, os bytes e o CSV do relatorio (RF-03, RF-04, RF-09; V-04, V-05, V-09).

Os objetos sao gravados e **relidos do banco** antes de `build_content`: o texto de um decimal so
e igual ao do `/risk` com a escala da coluna, que so o `Decimal` lido do banco tem. A execucao e
relida com a `price_run` no `select_related`, como o servico vai le-la, e `build_content` roda
sem nenhuma consulta.

A falta de `E` num decimal e conferida **campo a campo**, nao nos bytes inteiros: ticker, nomes e
o texto de erro tem `E` legitimo.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts import reports
from apps.accounts.models import Organization, User
from apps.assets.models import Asset
from apps.risk.models import RiskResult, RiskRun
from tests.accounts.conftest import usuario
from tests.accounts.risco_de_teste import (
    MODELOS,
    NIVEIS,
    ativo,
    execucao,
    execucao_completa,
    resultado,
)
from tests.accounts.test_configuracao import _MODULOS_DA_FASE_2, _importa_drf

pytestmark = pytest.mark.django_db

ACCOUNTS_DIR = Path(__file__).resolve().parents[2] / "apps" / "accounts"

EMAIL = "pessoa.relatorio@acoes.test"
NOME = "Pessoa de Teste"

CHAVES_TOPO = {
    "format",
    "format_version",
    "report_id",
    "generated_at",
    "organization",
    "requested_by",
    "asset",
    "horizon_days",
    "risk_run",
    "results",
    "summary",
}
CHAVES_ORGANIZACAO = {"slug", "name"}
CHAVES_ATIVO = {"ticker", "name", "trading_name", "isin"}
CHAVES_EXECUCAO = {
    "id",
    "calculated_at",
    "finished_at",
    "status",
    "engine_version",
    "seed",
    "train_window_days",
    "as_of_date",
    "first_price_date",
    "price_count",
    "train_count",
    "test_count",
    "requested_models",
    "full_recompute",
    "price_run",
}
CHAVES_COLETA = {"id", "source", "started_at", "finished_at"}
# a ordem do RF-03
CAMPOS_RESULTADO = (
    "model_name",
    "model_category",
    "alpha",
    "hyperparameters",
    "var_latest",
    "var_mean",
    "violations",
    "expected_violations",
    "kupiec_passed",
    "kupiec_p_value",
    "christoffersen_passed",
    "christoffersen_p_value",
    "dq_passed",
    "dq_p_value",
    "adequate",
    "error",
)
CHAVES_NIVEL = {"alpha", "computed", "var_min", "var_max", "not_rejected"}

DECIMAIS_RESULTADO = (
    "alpha",
    "var_latest",
    "var_mean",
    "expected_violations",
    "kupiec_p_value",
    "christoffersen_p_value",
    "dq_p_value",
)
DECIMAIS_NIVEL = ("alpha", "var_min", "var_max")
PONTO_FIXO = re.compile(r"-?\d+\.\d+")

# O erro do `garchnet`, com virgula, aspas e quebra de linha: o CSV precisa po-lo entre aspas.
ERRO = 'falhou, com "aspas"\ne quebra de linha'

# V-04: os `var_latest` por nivel, escritos a mao; `None` e o modelo que falhou.
VAR_005: dict[str, str | None] = {
    "caviar": "0.0310",
    "egarch": "0.0250",
    "garch_1_1": "0.0240",
    "garchnet": None,
    "gru": "0.0199",
    "historical": "0.0234",
    "lstm": "0.0288",
    "monte_carlo": "0.0221",
    "parametric": "0.0230",
}
VAR_001: dict[str, str | None] = {
    "caviar": "0.0450",
    "egarch": "0.0401",
    "garch_1_1": "0.0399",
    "garchnet": None,
    "gru": "0.0512",
    "historical": "0.0377",
    "lstm": "0.0420",
    "monte_carlo": "0.0388",
    "parametric": "0.0366",
}
ADEQUADOS_005 = {"historical", "parametric"}


# --- montagem -----------------------------------------------------------------------------


def _com_erro(run: RiskRun, model_name: str, alpha: str) -> RiskResult:
    return resultado(
        run,
        model_name,
        alpha,
        hyperparameters={},
        var_latest=None,
        var_mean=None,
        violations=None,
        expected_violations=None,
        kupiec_passed=None,
        kupiec_p_value=None,
        christoffersen_passed=None,
        christoffersen_p_value=None,
        dq_passed=None,
        dq_p_value=None,
        basel_zone=None,
        adequate=None,
        error=ERRO,
    )


def _execucao_variada(asset: Asset, calculated_at: datetime) -> RiskRun:
    """A execucao `ok` com os 18 resultados, `var_latest` distintos, dois adequados no 5% e
    nenhum no 1%, e o `garchnet` com erro nos dois niveis."""
    run = execucao(asset, RiskRun.Status.OK, calculated_at)
    for model_name in MODELOS:
        for alpha, tabela in (("0.0500", VAR_005), ("0.0100", VAR_001)):
            var = tabela[model_name]
            if var is None:
                _com_erro(run, model_name, alpha)
            else:
                resultado(
                    run,
                    model_name,
                    alpha,
                    var_latest=Decimal(var),
                    adequate=alpha == "0.0500" and model_name in ADEQUADOS_005,
                )
    return run


def _organizacao() -> Organization:
    """Nome com acento, para os bytes provarem o `ensure_ascii=False`."""
    return Organization.objects.create(name="Ações Ltda", slug="acoes")


@pytest.fixture
def pessoa() -> User:
    return usuario(_organizacao(), EMAIL, name=NOME)


Montar = Callable[..., dict[str, Any]]


@pytest.fixture
def montar(pessoa: User, django_assert_num_queries: Callable[..., Any]) -> Montar:
    """Rele do banco a organizacao, o ativo, a execucao (com a `price_run`) e os resultados, na
    ordem do `/risk`, e chama `build_content` sem nenhuma consulta."""

    def _montar(
        run: RiskRun,
        *,
        report_id: uuid.UUID | None = None,
        generated_at: datetime | None = None,
    ) -> dict[str, Any]:
        org = Organization.objects.get(pk=pessoa.organization_id)
        lida = RiskRun.objects.select_related("asset", "price_run").get(pk=run.pk)
        resultados = list(
            RiskResult.objects.filter(run=lida).order_by("model_name", "-alpha")
        )
        with django_assert_num_queries(0):
            return reports.build_content(
                report_id=report_id or uuid.uuid4(),
                generated_at=generated_at or timezone.now(),
                organization=org,
                requester_name=pessoa.name,
                asset=lida.asset,
                run=lida,
                results=resultados,
            )

    return _montar


@pytest.fixture
def variada() -> RiskRun:
    return _execucao_variada(ativo("ITUB4"), timezone.now() - timedelta(hours=1))


# --- as listas de campos --------------------------------------------------------------------


def test_os_campos_de_resultado_e_do_csv() -> None:
    assert reports.RESULT_FIELDS == CAMPOS_RESULTADO
    assert reports.CSV_FIELDS == tuple(
        c for c in CAMPOS_RESULTADO if c != "hyperparameters"
    )
    assert (reports.FORMAT, reports.FORMAT_VERSION, reports.HORIZON_DAYS) == (
        "ruvor.asset_risk_report",
        1,
        1,
    )


# --- V-04: o conteudo -----------------------------------------------------------------------


def test_v04_as_chaves_e_so_elas(montar: Montar, variada: RiskRun) -> None:
    report_id = uuid.uuid4()
    conteudo = montar(variada, report_id=report_id)

    assert set(conteudo) == CHAVES_TOPO
    assert conteudo["format"] == "ruvor.asset_risk_report"
    assert conteudo["format_version"] == 1
    assert conteudo["horizon_days"] == 1
    assert conteudo["report_id"] == str(report_id)
    assert set(conteudo["organization"]) == CHAVES_ORGANIZACAO
    assert conteudo["organization"] == {"slug": "acoes", "name": "Ações Ltda"}
    assert conteudo["requested_by"] == {"name": NOME}
    assert set(conteudo["asset"]) == CHAVES_ATIVO
    assert conteudo["asset"] == {
        "ticker": "ITUB4",
        "name": "ITUB4 S.A.",
        "trading_name": "ITUB4",
        "isin": None,
    }
    assert set(conteudo["risk_run"]) == CHAVES_EXECUCAO
    assert conteudo["risk_run"]["id"] == variada.pk
    assert conteudo["risk_run"]["status"] == "ok"
    assert conteudo["risk_run"]["seed"] == 42
    assert conteudo["risk_run"]["as_of_date"] == "2026-09-25"
    assert conteudo["risk_run"]["first_price_date"] == "2016-09-26"
    assert conteudo["risk_run"]["requested_models"] == list(MODELOS)
    assert conteudo["risk_run"]["full_recompute"] is False
    assert set(conteudo["risk_run"]["price_run"]) == CHAVES_COLETA
    assert conteudo["risk_run"]["price_run"]["id"] == variada.price_run_id
    assert conteudo["risk_run"]["price_run"]["source"] == "yahoo_chart"
    for item in conteudo["results"]:
        assert tuple(item) == CAMPOS_RESULTADO
    for nivel in conteudo["summary"]:
        assert set(nivel) == CHAVES_NIVEL


def test_v04_sem_as_colunas_operacionais(montar: Montar, variada: RiskRun) -> None:
    conteudo = montar(variada)
    for item in conteudo["results"]:
        assert "basel_zone" not in item
        assert "reused_snapshots" not in item
        assert "trained_snapshots" not in item


def test_v04_o_email_nao_aparece_nos_bytes(
    montar: Montar, variada: RiskRun, pessoa: User
) -> None:
    b = reports.to_bytes(montar(variada))
    assert pessoa.email == EMAIL
    assert EMAIL.encode() not in b
    assert b"@" not in b
    assert NOME.encode() in b


def test_v04_dezoito_resultados_na_ordem_do_risk(
    montar: Montar, variada: RiskRun, client: Client
) -> None:
    conteudo = montar(variada)
    ordem = [(r["model_name"], r["alpha"]) for r in conteudo["results"]]
    assert len(ordem) == 18
    assert ordem == [(m, a) for m in MODELOS for a in NIVEIS]

    corpo = client.get("/api/v1/assets/ITUB4/risk").json()
    assert corpo["latest"]["id"] == variada.pk
    assert ordem == [(r["model_name"], r["alpha"]) for r in corpo["latest"]["results"]]


def test_v04_o_resumo_conferido_a_mao(montar: Montar, variada: RiskRun) -> None:
    conteudo = montar(variada)
    calculados = [
        "caviar",
        "egarch",
        "garch_1_1",
        "gru",
        "historical",
        "lstm",
        "monte_carlo",
        "parametric",
    ]
    assert conteudo["summary"] == [
        {
            "alpha": "0.0500",
            "computed": calculados,
            "var_min": "0.0199000000",
            "var_max": "0.0310000000",
            "not_rejected": ["historical", "parametric"],
        },
        {
            "alpha": "0.0100",
            "computed": calculados,
            "var_min": "0.0366000000",
            "var_max": "0.0512000000",
            "not_rejected": [],
        },
    ]


def test_v04_o_modelo_com_erro(montar: Montar, variada: RiskRun) -> None:
    conteudo = montar(variada)
    falhos = [r for r in conteudo["results"] if r["model_name"] == "garchnet"]
    assert len(falhos) == 2
    for item in falhos:
        assert item["var_latest"] is None
        assert item["adequate"] is None
        assert item["error"] == ERRO
        assert item["hyperparameters"] == {}
    for nivel in conteudo["summary"]:
        assert "garchnet" not in nivel["computed"]


def test_v04_nivel_sem_nenhum_calculado(montar: Montar) -> None:
    run = execucao(ativo("PETR4"), RiskRun.Status.PARTIAL, timezone.now())
    resultado(run, "historical", "0.0500", adequate=True)
    _com_erro(run, "historical", "0.0100")
    _com_erro(run, "parametric", "0.0100")

    conteudo = montar(run)
    assert conteudo["risk_run"]["status"] == "partial"
    assert conteudo["summary"] == [
        {
            "alpha": "0.0500",
            "computed": ["historical"],
            "var_min": "0.0234000000",
            "var_max": "0.0234000000",
            "not_rejected": ["historical"],
        },
        {
            "alpha": "0.0100",
            "computed": [],
            "var_min": None,
            "var_max": None,
            "not_rejected": [],
        },
    ]


def test_v04_hiperparametros_e_modelos_pedidos_como_vieram(montar: Montar) -> None:
    run = execucao(ativo("VALE3"), RiskRun.Status.OK, timezone.now())
    aninhado = {"window": 252, "layers": [64, 32], "extra": {"dropout": 0.2}}
    resultado(run, "lstm", "0.0500", hyperparameters=aninhado)

    conteudo = montar(run)
    assert conteudo["results"][0]["hyperparameters"] == aninhado
    assert conteudo["risk_run"]["requested_models"] == list(MODELOS)


# --- V-05: os bytes -------------------------------------------------------------------------


def _decimais(conteudo: dict[str, Any]) -> list[object]:
    valores: list[object] = []
    for item in conteudo["results"]:
        valores.extend(item[c] for c in DECIMAIS_RESULTADO)
    for nivel in conteudo["summary"]:
        valores.extend(nivel[c] for c in DECIMAIS_NIVEL)
    return valores


def test_v05_valor_p_zero_e_pequeno_em_ponto_fixo(montar: Montar) -> None:
    run = execucao(ativo("BBDC4"), RiskRun.Status.OK, timezone.now())
    resultado(run, "historical", "0.0500", kupiec_p_value=Decimal("0"))
    resultado(run, "historical", "0.0100", kupiec_p_value=Decimal("0.0000000012"))

    conteudo = montar(run)
    assert [r["kupiec_p_value"] for r in conteudo["results"]] == [
        "0.0000000000",
        "0.0000000012",
    ]
    valores = _decimais(conteudo)
    assert valores
    for valor in valores:
        assert valor is None or (
            isinstance(valor, str)
            and "E" not in valor.upper()
            and PONTO_FIXO.fullmatch(valor)
        ), valor


def test_v05_nenhum_decimal_com_e(montar: Montar, variada: RiskRun) -> None:
    for valor in _decimais(montar(variada)):
        assert valor is None or (
            isinstance(valor, str)
            and "E" not in valor.upper()
            and PONTO_FIXO.fullmatch(valor)
        ), valor


def test_v05_o_mesmo_texto_do_risk(montar: Montar, client: Client) -> None:
    run = execucao(
        ativo("ITUB4"), RiskRun.Status.OK, timezone.now() - timedelta(hours=1)
    )
    # os dois valores-p que o `str()` estragaria, e um VaR com dez casas, no mesmo ativo
    especiais: dict[tuple[str, str], dict[str, Any]] = {
        ("caviar", "0.0500"): {"kupiec_p_value": Decimal("0")},
        ("egarch", "0.0100"): {
            "dq_p_value": Decimal("0.0000000012"),
            "var_latest": Decimal("0.0283415120"),
        },
    }
    for model_name in MODELOS:
        for alpha in NIVEIS:
            resultado(run, model_name, alpha, **especiais.get((model_name, alpha), {}))

    conteudo = montar(run)
    corpo = client.get("/api/v1/assets/ITUB4/risk").json()
    assert corpo["latest"]["id"] == run.pk
    do_risk = corpo["latest"]["results"]
    assert len(do_risk) == len(conteudo["results"]) == 18
    for nosso, deles in zip(conteudo["results"], do_risk, strict=True):
        assert (nosso["model_name"], nosso["alpha"]) == (
            deles["model_name"],
            deles["alpha"],
        )
        for campo in DECIMAIS_RESULTADO:
            assert isinstance(nosso[campo], str), (nosso["model_name"], campo)
            assert nosso[campo] == deles[campo], (nosso["model_name"], campo)
    assert "0.0000000000" in {r["kupiec_p_value"] for r in conteudo["results"]}
    assert "0.0000000012" in {r["dq_p_value"] for r in conteudo["results"]}
    assert "0.0283415120" in {r["var_latest"] for r in conteudo["results"]}


def test_v05_instantes_em_utc(montar: Montar, variada: RiskRun) -> None:
    gerado = timezone.now()
    conteudo = montar(variada, generated_at=gerado)
    execucao_ = conteudo["risk_run"]
    coleta = execucao_["price_run"]
    instantes = {
        conteudo["generated_at"]: gerado,
        execucao_["calculated_at"]: variada.calculated_at,
        execucao_["finished_at"]: variada.finished_at,
        coleta["started_at"]: variada.price_run.started_at,
        coleta["finished_at"]: variada.price_run.finished_at,
    }
    assert len(instantes) == 5
    for texto, original in instantes.items():
        assert texto.endswith("+00:00"), texto
        assert datetime.fromisoformat(texto) == original


def test_v05_bytes_compactos_e_ordenados(montar: Montar, variada: RiskRun) -> None:
    b = reports.to_bytes(montar(variada))
    de_novo = json.loads(b)
    assert reports.to_bytes(de_novo) == b
    # independente de `to_bytes`: chaves ordenadas, sem espaco, UTF-8 cru
    assert (
        json.dumps(
            de_novo, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        == b
    )
    assert "Ações Ltda".encode() in b
    assert not b.endswith(b"\n")


def test_v05_deterministico(montar: Montar, variada: RiskRun) -> None:
    report_id = uuid.uuid4()
    gerado = timezone.now()
    primeiro = reports.to_bytes(
        montar(variada, report_id=report_id, generated_at=gerado)
    )
    segundo = reports.to_bytes(
        montar(variada, report_id=report_id, generated_at=gerado)
    )
    assert primeiro == segundo


def test_v05_hash_e_memoryview(montar: Montar, variada: RiskRun) -> None:
    b = reports.to_bytes(montar(variada))
    visto = memoryview(b)
    assert hashlib.sha256(visto).hexdigest() == hashlib.sha256(b).hexdigest()
    assert len(hashlib.sha256(b).hexdigest()) == 64
    assert reports.to_csv(visto) == reports.to_csv(b)


def test_v05_decimal_cru_levanta(montar: Montar, variada: RiskRun) -> None:
    conteudo = montar(variada)
    conteudo["results"][0]["var_latest"] = Decimal("0.0234")
    with pytest.raises(TypeError):
        reports.to_bytes(conteudo)


def test_build_content_nao_consulta_o_banco(montar: Montar, variada: RiskRun) -> None:
    """O `montar` ja o faz em volta de toda chamada; aqui, o CSV e os bytes tambem."""
    conteudo = montar(variada)
    with CaptureQueriesContext(connection) as consultas:
        reports.to_csv(reports.to_bytes(conteudo))
    assert len(consultas) == 0


# --- V-09, a parte da funcao: o CSV ---------------------------------------------------------


def test_v09_o_csv(montar: Montar, variada: RiskRun) -> None:
    b = reports.to_bytes(montar(variada))
    tabela = reports.to_csv(b)

    assert not tabela.startswith(b"\xef\xbb\xbf")
    texto = tabela.decode("utf-8")
    assert texto.endswith("\r\n")
    linhas = list(csv.reader(io.StringIO(texto, newline="")))
    assert tuple(linhas[0]) == reports.CSV_FIELDS
    assert len(linhas) == 1 + 18

    por_chave = {
        (linha[0], linha[2]): dict(zip(reports.CSV_FIELDS, linha, strict=True))
        for linha in linhas[1:]
    }
    ok = por_chave[("historical", "0.0500")]
    assert ok["var_latest"] == "0.0234000000"
    assert ok["expected_violations"] == "111.350000"
    assert ok["violations"] == "110"
    assert ok["kupiec_passed"] == "true"
    assert ok["christoffersen_passed"] == "false"
    assert ok["adequate"] == "true"
    assert ok["error"] == ""
    assert por_chave[("historical", "0.0100")]["adequate"] == "false"

    falho = por_chave[("garchnet", "0.0500")]
    assert falho["var_latest"] == ""
    assert falho["kupiec_passed"] == ""
    assert falho["adequate"] == ""
    assert falho["error"] == ERRO
    # o erro com virgula, aspas e quebra de linha sai entre aspas, com as aspas dobradas
    assert '"falhou, com ""aspas""\ne quebra de linha"' in texto


def test_v09_o_csv_segue_o_conteudo(montar: Montar, variada: RiskRun) -> None:
    conteudo = json.loads(reports.to_bytes(montar(variada)))
    ordem = [(r["model_name"], r["alpha"]) for r in conteudo["results"]]
    linhas = list(
        csv.reader(
            io.StringIO(reports.to_csv(reports.to_bytes(conteudo)).decode(), newline="")
        )
    )
    assert [(linha[0], linha[2]) for linha in linhas[1:]] == ordem
    for linha, item in zip(linhas[1:], conteudo["results"], strict=True):
        for campo, celula in zip(reports.CSV_FIELDS, linha, strict=True):
            valor = item[campo]
            esperado = (
                ""
                if valor is None
                else ("true" if valor else "false")
                if isinstance(valor, bool)
                else str(valor)
            )
            assert celula == esperado, campo


def test_v09_duas_chamadas_iguais(montar: Montar) -> None:
    run = execucao_completa(ativo("ABEV3"), timezone.now())
    b = reports.to_bytes(montar(run))
    assert reports.to_csv(b).count(b"\r\n") == 1 + 18
    assert reports.to_csv(b) == reports.to_csv(b)
    assert reports.to_csv(b) == reports.to_csv(bytes(b))


# --- o nome do arquivo ----------------------------------------------------------------------


def test_o_nome_do_arquivo() -> None:
    assert (
        reports.filename(
            "ITUB4", "2026-09-25", "1a2b3c4d-5e6f-7081-92a3-b4c5d6e7f809", "json"
        )
        == "ruvor-risco-ITUB4-2026-09-25-1a2b3c4d.json"
    )
    assert (
        reports.filename(
            "ITUB4", "2026-09-25", "1a2b3c4d-5e6f-7081-92a3-b4c5d6e7f809", "csv"
        )
        == "ruvor-risco-ITUB4-2026-09-25-1a2b3c4d.csv"
    )


# --- sem DRF --------------------------------------------------------------------------------


def test_reports_fica_na_fase_1_sem_drf() -> None:
    """`reports.py` fora de `_MODULOS_DA_FASE_2`: o `test_fase1_sem_drf` o guarda."""
    arquivo = ACCOUNTS_DIR / "reports.py"
    assert arquivo.is_file()
    assert "reports.py" not in _MODULOS_DA_FASE_2
    assert not _importa_drf(ast.parse(arquivo.read_text("utf-8")))
