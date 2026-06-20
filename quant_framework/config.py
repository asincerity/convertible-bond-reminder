from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

import yaml

from .models import BacktestConfig


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_backtest_config(path: str) -> BacktestConfig:
    cfg = load_config(path)
    backtest = cfg.get("backtest", {})
    return BacktestConfig(**backtest)


def dump_default_config(path: str) -> None:
    default = {"backtest": asdict(BacktestConfig())}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(default, f, sort_keys=False, allow_unicode=True)
