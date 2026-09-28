"""A tarefa de metricas da rotina diaria (RF-21): o elo entre os precos e o risco.

Molde de `apps/assets/tasks.py`: funcao com sublinhado, registrada com
`app.task(name=...)(funcao)` -- a funcao com sublinhado e o ponto que os testes chamam; os
tipos vem do `celery-types` (D-134). O nome de registro e contrato (D-89): e ele que a
`rotina_diaria` encadeia.

`calcular_metricas` **nao rompe o elo por ativo falho** (D-69), como `importar_precos` ja
nao rompe: `run_compute_metrics` grava cada ativo em transacao propria e so levanta
`MetricsFailed` depois do laco inteiro, entao os que calcularam ja estao gravados. A tarefa
captura **so** `MetricsFailed` e `InvalidTickers` e devolve `"FALHOU: ..."`; qualquer outra
excecao propaga -- o calculo nao chegou a rodar, e o risco nao deve seguir sobre isso.

`run_compute_metrics` e chamada pelo nome global **deste** modulo: e onde os testes a
substituem.
"""

from __future__ import annotations

from apps.analytics.compute import InvalidTickers, MetricsFailed, run_compute_metrics
from config.celery import app


def _calcular_metricas() -> str:
    """Calcula as metricas dos ativos com preco e devolve o relatorio; nunca levanta
    `MetricsFailed` nem `InvalidTickers`."""
    try:
        report = run_compute_metrics([])
    except MetricsFailed as exc:
        return "FALHOU: " + str(exc) + "\n" + exc.report.render()
    except InvalidTickers as exc:
        return "FALHOU: " + str(exc)
    return report.render()


# Registro sem a sintaxe de decorador, como em `apps/assets/tasks.py`.
calcular_metricas = app.task(name="apps.analytics.tasks.calcular_metricas")(
    _calcular_metricas
)
