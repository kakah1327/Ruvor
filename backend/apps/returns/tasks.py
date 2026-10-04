"""A tarefa do retorno na rotina diaria (M5.1, RF-12): o quinto e ultimo elo da corrente.

Molde de `apps/analytics/tasks.py`: funcao com sublinhado, registrada com
`app.task(name=...)(funcao)` -- a funcao com sublinhado e o ponto que os testes chamam; os
tipos vem do `celery-types` (D-134). O nome de registro e contrato (D-89).

**`calcular_retornos` nunca levanta**: e o elo que pode faltar, e fica depois do risco
justamente para que a falha dele nao rompa o recalculo do risco (D-91, que a D-191
estende). Qualquer excecao e registrada no log e vira `"FALHOU: ..."`. Roda **junto** do
risco, nao depois: o `recalcular_cobertos` so enfileira as aberturas e devolve.

`run_compute_returns` e chamada pelo nome global **deste** modulo: e onde os testes a
substituem.
"""

from __future__ import annotations

import logging

from apps.returns.compute import ReturnsFailed, run_compute_returns
from config.celery import app

logger = logging.getLogger(__name__)


def _calcular_retornos() -> str:
    """Valida os modelos de retorno dos ativos com preco e devolve o relatorio; nunca
    levanta."""
    try:
        report = run_compute_returns([])
    except ReturnsFailed as exc:
        logger.exception("retorno: ativos com falha")
        return "FALHOU: " + str(exc) + "\n" + exc.report.render()
    except Exception as exc:
        logger.exception("retorno: o calculo nao rodou")
        return f"FALHOU: {type(exc).__name__}: {exc}"
    return report.render()


# Registro sem a sintaxe de decorador, como em `apps/analytics/tasks.py`.
calcular_retornos = app.task(name="apps.returns.tasks.calcular_retornos")(
    _calcular_retornos
)
