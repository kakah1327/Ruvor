"""A série diária do VaR do PETR4 (Histórico e GARCH(1,1), 95% e 99%) na década do laboratório, para a Figura 2.

Roda no worker, dentro do `manage.py shell` (ver exportar.sh), e escreve o CSV na saída padrão. Usa a mesma
década, a mesma identidade e o mesmo `run_models` do laboratório; só os dois modelos baratos, que não têm
retratos, para não gravar nada em `gold`. As violações têm de bater com `gold.lab_result`.
"""
import sys, io
from engine.models import load_all_model_modules
from engine.backtesting import load_all_backtest_modules
from apps.assets.models import Asset
from apps.risk.decade import decade_of, valid_bars
from apps.risk.lab import identity_for, period_of_test
from apps.risk.compute import run_models
from apps.risk.snapshots import SnapshotKey
load_all_model_modules(); load_all_backtest_modules()
out = io.StringIO()
out.write("ticker;model;alpha;date;ret;var\n")
for t in ["PETR4"]:
    a = Asset.objects.get(ticker=t)
    d = decade_of(valid_bars(a)); ident = identity_for(a, d)
    key = SnapshotKey(asset=a, seed=ident.seed, engine_version=ident.engine_version, train_window_days=ident.train_window_days, first_price_date=ident.first_price_date, library_versions=ident.library_versions)
    res, _ = run_models(key, d.series, ["historical", "garch_1_1"], full=False)
    test = period_of_test(a, d)
    for r in res.runs:
        v = r.estimate.var_series
        for dt, val in v.items():
            out.write(f"{t};{r.model_name};{r.alpha};{dt.date() if hasattr(dt,'date') else dt};{test.get(dt, '')};{val}\n")
sys.stdout.write(out.getvalue())
