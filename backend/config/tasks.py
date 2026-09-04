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


# Registro sem a sintaxe de decorador: o Celery nao publica tipos, e sob mypy estrito
# `@app.task` reprova com untyped-decorator. Aplicar o decorador como chamada registra a
# mesma tarefa sem suprimir erro nenhum no restante do arquivo.
ping = app.task(name="config.tasks.ping")(_ping)
