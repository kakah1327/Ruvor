"""Prova que a tarefa de fumaca esta registrada, sem tocar em Redis.

Este modulo importa **so** `config`. Importar `config.tasks` aqui registraria a tarefa
pelo proprio teste, e a assercao passaria a valer para qualquer implementacao — inclusive
uma que nunca registrasse nada no arranque do worker.
"""

from celery import Celery

import config


def test_config_expoe_a_aplicacao_celery() -> None:
    assert isinstance(config.celery_app, Celery)


def test_ping_esta_registrada_ao_importar_config() -> None:
    assert "config.tasks.ping" in config.celery_app.tasks
