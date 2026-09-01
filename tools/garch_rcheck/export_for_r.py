"""Exporta os retornos de treino (mesma janela padrao da plataforma, 252 dias uteis) e os
parametros GARCH(1,1)/EGARCH estimados pelo `arch` (Python), para comparar lado a lado com
o `rugarch` (R) via rugarch_check.R — item "4. Verificacao cruzada com R" da Matriz de
Validacao da Etapa 2.

Uso: python tools/garch_rcheck/export_for_r.py [--ticker PETR4.SA] [--start 2015-01-01] [--end 2024-12-31]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.data.preprocessing import fetch_returns
from engine.data.providers.yfinance_provider import YFinanceProvider
from engine.models.garch.egarch import EgarchVaR
from engine.models.garch.garch_1_1 import Garch11VaR

OUT_DIR = Path(__file__).parent
TRAIN_WINDOW_DAYS = 252


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="PETR4.SA")
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2024-12-31")
    args = parser.parse_args()

    returns = fetch_returns(YFinanceProvider(), args.ticker, args.start, args.end)
    train_returns = returns.iloc[:TRAIN_WINDOW_DAYS]

    csv_path = OUT_DIR / "train_returns.csv"
    train_returns.rename("return").to_csv(csv_path, index_label="date")
    print(f"Retornos de treino ({len(train_returns)} obs, {args.ticker}) salvos em {csv_path}")

    params = {}
    for name, model_cls in [("garch_1_1", Garch11VaR), ("egarch", EgarchVaR)]:
        model = model_cls().fit(train_returns)
        params[name] = {
            "params": model.result_.params.to_dict(),
            "loglikelihood": model.result_.loglikelihood,
            "convergence_flag": int(model.result_.convergence_flag),
        }

    json_path = OUT_DIR / "python_arch_params.json"
    json_path.write_text(json.dumps(params, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Parametros estimados pelo arch (Python) salvos em {json_path}")
    print(json.dumps(params, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
