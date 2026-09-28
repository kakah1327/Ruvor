"""Tarefa de fumaca da fila: prova que o worker executa o que o web enfileira."""

from __future__ import annotations

import socket

from config.celery import app


def _ping() -> str:
    """Devolve o nome de host de quem executou.

    Nao e constante de proposito: com "pong", o criterio passaria com o worker
    desligado.
    """
    return socket.gethostname()


# Registro sem a sintaxe de decorador: a funcao com sublinhado e o ponto que os testes
# chamam e substituem. Os tipos da tarefa vem do `celery-types` (D-134).
ping = app.task(name="config.tasks.ping")(_ping)
