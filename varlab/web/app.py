"""Application factory. O Flask agora e so uma API JSON (blueprint `api`) consumida por
3 clientes independentes: o frontend React (frontend/), o CLI (varlab/cli.py) e os
testes. Em producao, depois de `npm run build`, o Flask tambem serve os arquivos
estaticos gerados em frontend/dist — assim da pra rodar tudo com 1 processo so.
"""
from __future__ import annotations

from pathlib import Path

from flask import Flask, send_from_directory

from varlab.backtesting import load_all_backtest_modules
from varlab.models import load_all_model_modules
from varlab.web.config import get_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


def create_app(env: str | None = None) -> Flask:
    static_folder = str(FRONTEND_DIST) if FRONTEND_DIST.exists() else None
    app = Flask(__name__, static_folder=static_folder, static_url_path="")
    app.config.from_object(get_config(env))

    # Popula os registries uma vez, na inicializacao da app.
    load_all_model_modules()
    load_all_backtest_modules()

    from flask_cors import CORS

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from varlab.web.blueprints.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    if static_folder:
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_react(path: str):
            target = FRONTEND_DIST / path
            if path and target.is_file():
                return send_from_directory(FRONTEND_DIST, path)
            return send_from_directory(FRONTEND_DIST, "index.html")

    return app
