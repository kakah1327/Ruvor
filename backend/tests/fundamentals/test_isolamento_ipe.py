"""O IPE fora do caminho do `import_fundamentals` (M3.2, RF-02b).

`cvm_url` aceita o IPE, mas `KINDS` — o intervalo da coleta do M3.1 — nao o inclui, e
`_current_versions` so devolve os tipos pedidos: uma versao corrente de `ipe` na `bronze`
nao pode chegar aos indices que o M3.1 le procurando `CD_CVM`.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from apps.assets.models import CollectionRun
from apps.fundamentals.cvm import IPE, cvm_url
from apps.fundamentals.importer import (
    FundamentalsImportFailed,
    run_import_fundamentals,
)
from apps.fundamentals.models import Company, CvmFile
from apps.fundamentals.zipdata import content_sha256
from tests.fundamentals.conftest import EOL, FakeCvm, serve_range
from tests.fundamentals.test_importer import add_stock, clock, lines

pytestmark = pytest.mark.django_db

SP = ZoneInfo("America/Sao_Paulo")
NOW_2025 = datetime(2025, 9, 30, 12, 0, tzinfo=SP)  # intervalo 2016..2025
YEAR = 2025  # o ano do zip de IPE posto na `bronze`

# O cabecalho do IPE, como a spec mede ("A fonte, medida"). A linha abaixo e montada no
# teste, nao copiada da CVM: basta que o membro exista e tenha uma linha, para que ler o
# indice do M3.1 nele levante `KeyError: 'CD_CVM'`.
IPE_HEADER = (
    "CNPJ_Companhia;Nome_Companhia;Codigo_CVM;Data_Referencia;Categoria;Tipo;Especie;"
    "Assunto;Data_Entrega;Tipo_Apresentacao;Protocolo_Entrega;Versao;Link_Download"
)
IPE_ROW = (
    "33.000.167/0001-01;PETROLEO BRASILEIRO S.A. PETROBRAS;9512;2025-09-19;"
    "Fato Relevante;;;Assunto de teste;2025-09-19;AP - Apresentacao;000000001;1;"
    "https://www.rad.cvm.gov.br/teste"
)


def ipe_zip(year: int) -> bytes:
    """Zip com o membro unico `ipe_cia_aberta_<ano>.csv`: o cabecalho e `IPE_ROW`."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
        text = EOL.join((IPE_HEADER, IPE_ROW)) + EOL
        target.writestr(f"ipe_cia_aberta_{year}.csv", text.encode("latin-1"))
    return buffer.getvalue()


def test_rf02b_cvm_url_aceita_o_ipe_e_recusa_o_desconhecido() -> None:
    assert cvm_url("ipe", 2026) == (
        "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_2026.zip"
    )
    with pytest.raises(ValueError, match="tipo de documento desconhecido"):
        cvm_url("xyz", 2026)


def test_rf02b_ipe_na_bronze_nao_chega_aos_indices_do_m31() -> None:
    # Uma acao cuja companhia nao tem `silver.company`: sem ela, `_pending()` seria vazio,
    # nenhum indice seria lido, e o teste passaria sem o filtro de `_current_versions`.
    add_stock("99999")
    fake = FakeCvm({}, {})
    serve_range(fake, NOW_2025, {})  # itr e dfp de 2016 a 2025, zips vazios
    run_import_fundamentals(fake, now=clock(NOW_2025))

    ipe_run = CollectionRun.objects.create(source="teste-ipe", started_at=NOW_2025)
    payload = ipe_zip(YEAR)
    CvmFile.objects.create(
        run=ipe_run,
        kind=IPE,
        year=YEAR,
        url=cvm_url(IPE, YEAR),
        http_status=200,
        last_modified="teste-ipe",
        content_sha256=content_sha256(payload),
        payload=payload,
    )
    assert not Company.objects.filter(code_cvm="99999").exists()

    serve_range(fake, NOW_2025, {})  # mesmo generation: tudo `nao modificado`
    failed: FundamentalsImportFailed | None = None
    try:
        report = run_import_fundamentals(fake, now=clock(NOW_2025))
    except FundamentalsImportFailed as exc:  # o relatorio, para a falha mostrar a linha
        failed, report = exc, exc.report

    assert [t for t in lines(report) if t.startswith("catalogo: FALHOU")] == []
    assert failed is None
    assert report.files, "a coleta nao pediu arquivo nenhum"
    assert {f.status for f in report.files} == {"nao modificado"}
    assert "catalogo: 0 companhias novas, 1 sem documento na cvm" in lines(report)
    assert ("head", IPE, YEAR) not in fake.calls
