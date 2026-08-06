"""Cache local em parquet para evitar re-download repetido do mesmo ticker/periodo."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFAULT_CACHE_DIR = Path.home() / ".varlab" / "cache"


def _cache_path(ticker: str, start: str, end: str, cache_dir: Path) -> Path:
    safe_ticker = ticker.replace("^", "").replace("/", "_")
    return cache_dir / f"{safe_ticker}_{start}_{end}.parquet"


def load_cached(ticker: str, start: str, end: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> pd.DataFrame | None:
    path = _cache_path(ticker, start, end, cache_dir)
    if path.exists():
        return pd.read_parquet(path)
    return None


def save_cache(df: pd.DataFrame, ticker: str, start: str, end: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(ticker, start, end, cache_dir)
    df.to_parquet(path)
