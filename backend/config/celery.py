"""Aplicacao Celery do backend.

O `celery -A config worker` do alvo `worker`, a verificacao de vida desse servico e o
`from config.tasks import ping` executado no `web` dependem todos desta aplicacao.
"""

from __future__ import annotations

import os

from celery import Celery

# Antes de instanciar: sem isso o processo do worker nao sabe quais settings carregar e
# falha com uma mensagem que nao aponta para a causa.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("ruvor")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Registro em duas formas, que convivem.
#
# As tarefas dos apps entram por descoberta automatica: `autodiscover_tasks()` varre
# INSTALLED_APPS, que tem os quatro apps de dominio. Ela e preguicosa — so importa os
# `tasks.py` quando o worker parte, ou quando alguem chama
# `app.loader.import_default_modules()` — e por isso pode ficar aqui. Um import direto de
# `apps.*.tasks` neste modulo rodaria durante o carregamento das settings, antes de
# `django.setup()`, e derrubaria o processo com `AppRegistryNotReady`.
app.autodiscover_tasks()

# `config` nao esta em INSTALLED_APPS, entao a descoberta nao o alcanca: a tarefa de fumaca
# continua por import explicito, depois de a aplicacao existir. Nao e `include=[...]`, e o
# mecanismo importa: com `include=`, `app.tasks` so recebe a tarefa na finalizacao — o
# teste de registro reprovaria uma implementacao correta, e a "correcao" natural (importar
# config.tasks no proprio teste) o tornaria verdadeiro para qualquer implementacao.
import config.tasks  # noqa: E402, F401  (o efeito colateral do import e o objetivo)
