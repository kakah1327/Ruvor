"""O contrato dos motivos do pedido sob demanda, do lado do backend (RF-18, V-13 do M1.6b).

A tela nao mostra o motivo cru: `frontend/src/content/motivos.ts` traduz cada um. Nenhum
conteiner ve o backend e o frontend juntos, e por isso a lista e escrita dos dois lados -- aqui
e em `frontend/tests/motivos.test.ts` -- e cada lado confere a sua contra ela:

- as constantes `REASON_*` de `apps.api.ondemand`, lidas por introspeccao do modulo: uma
  constante nova, ou um valor mudado, reprova;
- os dois motivos montados, `expired_reason()` e `apps.risk.tasks._short_series_reason(N)`;
- `apps.risk.config.MIN_SESSIONS == 503`, que o frontend copia em `risk/config.ts`.

Um motivo escrito como literal fora de `ondemand.py` e de `_short_series_reason` escapa a este
teste (Riscos da spec).
"""

from __future__ import annotations

import re
from datetime import timedelta

from pytest_django import Settings

from apps.api import ondemand
from apps.risk import config as risk_config
from apps.risk.tasks import _short_series_reason

MENSAGEM = (
    "mudou o contrato dos motivos do pedido — atualize "
    "`frontend/src/content/motivos.ts` e a lista do teste do frontend"
)

# A lista fechada do RF-18, sem os dois montados.
MOTIVOS_FIXOS = {
    "REASON_CALCULATED": "calculado",
    "REASON_COLLECT_FAILED": "falhou na coleta",
    "REASON_METRICS_FAILED": "falhou nas metricas",
    "REASON_OPENING_FAILED": "falhou na abertura",
    "REASON_RUN_FAILED": "a execucao falhou",
    "REASON_BROKER_REFUSED": "o broker recusou o pedido",
}


def test_as_constantes_reason_sao_exatamente_as_seis() -> None:
    encontradas = {
        nome: getattr(ondemand, nome)
        for nome in vars(ondemand)
        if nome.startswith("REASON_")
    }
    assert encontradas == MOTIVOS_FIXOS, MENSAGEM


def test_o_motivo_expirado_traz_o_prazo_configurado(settings: Settings) -> None:
    settings.RUVOR_ON_DEMAND_TIMEOUT = timedelta(minutes=45)
    motivo = ondemand.expired_reason()
    assert re.fullmatch(r"expirado \(\d+ min\)", motivo), MENSAGEM
    assert motivo == "expirado (45 min)", MENSAGEM


def test_o_motivo_serie_curta() -> None:
    assert _short_series_reason(12) == "serie curta (12 pregoes, minimo 503)", MENSAGEM


def test_o_minimo_de_pregoes_e_503() -> None:
    assert risk_config.MIN_SESSIONS == 503, MENSAGEM
