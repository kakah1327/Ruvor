"""As tarefas de coleta que o Beat agenda: o catalogo, os precos e a rotina diaria.

Molde de `config/tasks.py`: funcao com sublinhado, registrada com
`app.task(name=...)(funcao)` -- sob mypy estrito, `@app.task` reprova com
untyped-decorator. Os nomes de registro sao contrato: sao eles que vao no
`CELERY_BEAT_SCHEDULE`.

- `importar_ativos` e `importar_precos` sao cascas sobre os comandos de `manage.py`;
- `importar_precos` **captura o `CommandError`** e devolve o que aconteceu (RF-10): o
  `import_prices` levanta quando um ticker falha (D-54), e num encadeamento ingenuo um
  ticker ruim cancelaria o recalculo diario inteiro. Qualquer outra excecao propaga -- a
  corrente so nao segue se a ingestao nao chegou a rodar;
- `rotina_diaria` e o elo: o `beat_schedule` nao aceita `chain`, so nome de tarefa, entao
  a corrente preco -> risco e montada aqui. O segundo elo e **imutavel** (`.si()`): com
  `.s()`, o texto devolvido por `importar_precos` chegaria como `calculated_at_iso`, e o
  `datetime.fromisoformat` do recalculo estouraria.

`call_command` e `_enqueue` sao chamados pelo nome global **deste** modulo -- e onde os
testes os substituem. O `_enqueue` e proprio, nao o de `apps.risk.tasks`.
"""

from __future__ import annotations

from io import StringIO
from typing import Any

from celery import chain
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.risk.tasks import recalcular_cobertos
from config.celery import app


def _enqueue(signature: Any) -> None:
    """Enfileira. E o ponto que os testes substituem: nenhum deles fala com o Redis."""
    signature.apply_async()


def _importar_ativos() -> str:
    """Roda o `import_assets` e devolve o que ele escreveu."""
    buf = StringIO()
    call_command("import_assets", stdout=buf)
    return buf.getvalue()


def _importar_precos() -> str:
    """Roda o `import_prices` e devolve o que ele escreveu; nunca levanta `CommandError`."""
    buf = StringIO()
    try:
        call_command("import_prices", stdout=buf)
    except CommandError as exc:
        return "FALHOU: " + str(exc)
    return buf.getvalue()


def _rotina_diaria() -> None:
    """Enfileira a corrente: primeiro os precos, depois o recalculo dos ativos cobertos."""
    _enqueue(chain(importar_precos.s(), recalcular_cobertos.si()))


# Registro sem a sintaxe de decorador, como em `config/tasks.py`.
importar_ativos = app.task(name="apps.assets.tasks.importar_ativos")(_importar_ativos)
importar_precos = app.task(name="apps.assets.tasks.importar_precos")(_importar_precos)
rotina_diaria = app.task(name="apps.assets.tasks.rotina_diaria")(_rotina_diaria)
