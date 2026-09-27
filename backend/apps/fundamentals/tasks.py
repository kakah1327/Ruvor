"""As tarefas de fundamentos que o Beat agenda: a coleta da CVM e o calculo dos indicadores.

Molde literal de `apps/assets/tasks.py`: funcao com sublinhado, registrada com
`app.task(name=...)(funcao)` -- a funcao com sublinhado e o ponto que os testes
chamam e substituem; os tipos vem do `celery-types` (D-134). Os nomes de registro sao
contrato: e o de `rotina_fundamentos` que vai no `CELERY_BEAT_SCHEDULE` (RF-30).

- `importar_fundamentos` e `calcular_fundamentos` sao cascas sobre os comandos de
  `manage.py` (RF-28);
- `importar_fundamentos` **captura o `CommandError`** e devolve o que aconteceu: o
  `import_fundamentals` levanta quando uma companhia ou um arquivo falha, e o calculo tem
  de rodar sobre o que entrou (D-69). Qualquer outra excecao propaga -- a corrente so nao
  segue se a coleta nao chegou a rodar;
- `rotina_fundamentos` e o elo: o `beat_schedule` nao aceita `chain`, so nome de tarefa,
  entao a corrente coleta -> calculo e montada aqui (D-127). O segundo elo e **imutavel**
  (`.si()`): com `.s()`, o texto devolvido por `importar_fundamentos` chegaria como
  argumento posicional do `calcular_fundamentos`, que nao recebe nenhum.

`call_command` e `_enqueue` sao chamados pelo nome global **deste** modulo -- e onde os
testes os substituem. O `_enqueue` e proprio, nao o de `apps.assets.tasks`.
"""

from __future__ import annotations

from io import StringIO
from typing import Any

from celery import chain
from django.core.management import call_command
from django.core.management.base import CommandError

from config.celery import app


def _enqueue(signature: Any) -> None:
    """Enfileira. E o ponto que os testes substituem: nenhum deles fala com o Redis."""
    signature.apply_async()


def _importar_fundamentos() -> str:
    """Roda o `import_fundamentals` e devolve o que ele escreveu; nunca levanta `CommandError`."""
    buf = StringIO()
    try:
        call_command("import_fundamentals", stdout=buf)
    except CommandError as exc:
        return "FALHOU: " + str(exc)
    return buf.getvalue()


def _calcular_fundamentos() -> str:
    """Roda o `compute_fundamentals` e devolve o que ele escreveu."""
    buf = StringIO()
    call_command("compute_fundamentals", stdout=buf)
    return buf.getvalue()


def _rotina_fundamentos() -> None:
    """Enfileira a corrente: primeiro a coleta da CVM, depois o calculo dos indicadores."""
    _enqueue(chain(importar_fundamentos.s(), calcular_fundamentos.si()))


# Registro sem a sintaxe de decorador, como em `apps/assets/tasks.py`.
importar_fundamentos = app.task(name="apps.fundamentals.tasks.importar_fundamentos")(
    _importar_fundamentos
)
calcular_fundamentos = app.task(name="apps.fundamentals.tasks.calcular_fundamentos")(
    _calcular_fundamentos
)
rotina_fundamentos = app.task(name="apps.fundamentals.tasks.rotina_fundamentos")(
    _rotina_fundamentos
)
