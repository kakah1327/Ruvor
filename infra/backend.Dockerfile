FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /repo
COPY backend/pyproject.toml backend/pyproject.toml
COPY backend/config/__init__.py backend/config/__init__.py
COPY backend/apps/__init__.py backend/apps/__init__.py
COPY backend/apps/accounts/__init__.py backend/apps/accounts/__init__.py
COPY backend/apps/assets/__init__.py backend/apps/assets/__init__.py
COPY backend/apps/analytics/__init__.py backend/apps/analytics/__init__.py
RUN pip install --no-cache-dir -e "./backend[dev]"

FROM base AS web
WORKDIR /repo/backend
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS worker
COPY engine/pyproject.toml engine/pyproject.toml
COPY engine/src/engine/__init__.py engine/src/engine/__init__.py
RUN pip install --no-cache-dir -e "./engine[traditional,garch,ml]"
WORKDIR /repo/backend
CMD ["celery", "-A", "config", "worker", "--loglevel=info"]
