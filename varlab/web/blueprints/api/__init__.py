"""API JSON do VaR Lab — unico blueprint web depois da migracao para React.

O frontend (frontend/) e um consumidor totalmente desacoplado desta API, assim como o
CLI (varlab/cli.py) e os testes (tests/). Nenhum destes 3 consumidores conhece
detalhes de implementacao dos outros — so o contrato JSON abaixo.
"""
from __future__ import annotations

import csv
import io
import json

from flask import Blueprint, Response, abort, current_app, jsonify

from varlab.backtesting import list_backtests
from varlab.models import list_models

bp = Blueprint("api", __name__)


def _repo():
    from varlab.storage.repository import SQLiteExperimentRunRepository

    return SQLiteExperimentRunRepository()


@bp.route("/config")
def config():
    return jsonify(
        {
            "tickers": current_app.config["DEFAULT_TICKERS"],
            "alphas": current_app.config["DEFAULT_ALPHAS"],
        }
    )


@bp.route("/models")
def models():
    return jsonify(list_models())


@bp.route("/backtests")
def backtests():
    return jsonify(list_backtests())


@bp.route("/results")
def results_list():
    return jsonify(_repo().list_runs())


@bp.route("/results/<int:run_id>")
def results_detail(run_id: int):
    payload = _repo().get(run_id)
    if payload is None:
        abort(404)
    return jsonify(payload)


@bp.route("/results/<int:run_id>/download.csv")
def results_download_csv(run_id: int):
    payload = _repo().get(run_id)
    if payload is None:
        abort(404)

    rows = payload["ranking"]
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=varlab_run_{run_id}_ranking.csv"},
    )


@bp.route("/results/<int:run_id>/download.json")
def results_download_json(run_id: int):
    payload = _repo().get(run_id)
    if payload is None:
        abort(404)

    return Response(
        json.dumps(payload, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=varlab_run_{run_id}.json"},
    )
