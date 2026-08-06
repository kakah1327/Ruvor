"""Persistencia de resultados de experimentos, atras de uma interface.

Trocar SQLite por outro backend (Postgres, arquivo JSON etc.) implica so escrever uma
nova classe que implemente ExperimentRunRepository — web/ e cli.py nunca acessam
SQLAlchemy diretamente, so esta interface.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from varlab.experiments.runner import ExperimentResult

DEFAULT_DB_PATH = Path.home() / ".varlab" / "varlab.db"


class ExperimentRunRepository(ABC):
    @abstractmethod
    def save(self, result: ExperimentResult) -> int:
        """Persiste o resultado e retorna o id do run."""

    @abstractmethod
    def list_runs(self) -> list[dict]:
        """Lista runs salvos (metadados resumidos, mais recentes primeiro)."""

    @abstractmethod
    def get(self, run_id: int) -> dict | None:
        """Retorna o payload completo (config + ranking) de um run, ou None."""


class SQLiteExperimentRunRepository(ExperimentRunRepository):
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = self._make_engine()
        self._ensure_schema()

    def _make_engine(self):
        from sqlalchemy import create_engine

        return create_engine(f"sqlite:///{self.db_path}")

    def _ensure_schema(self) -> None:
        from sqlalchemy import text

        with self._engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS experiment_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        payload TEXT NOT NULL
                    )
                    """
                )
            )

    def save(self, result: ExperimentResult) -> int:
        from sqlalchemy import text

        payload = {
            "config": asdict(result.config),
            "ranking": result.ranking_table().to_dict(orient="records"),
        }
        with self._engine.begin() as conn:
            cursor = conn.execute(
                text(
                    "INSERT INTO experiment_runs (ticker, created_at, payload) "
                    "VALUES (:ticker, :created_at, :payload)"
                ),
                {
                    "ticker": result.config.ticker,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "payload": json.dumps(payload),
                },
            )
            return cursor.lastrowid

    def list_runs(self) -> list[dict]:
        from sqlalchemy import text

        with self._engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, ticker, created_at FROM experiment_runs ORDER BY id DESC")
            ).mappings()
            return [dict(row) for row in rows]

    def get(self, run_id: int) -> dict | None:
        from sqlalchemy import text

        with self._engine.connect() as conn:
            row = conn.execute(
                text("SELECT payload FROM experiment_runs WHERE id = :id"),
                {"id": run_id},
            ).fetchone()
            return json.loads(row[0]) if row else None
