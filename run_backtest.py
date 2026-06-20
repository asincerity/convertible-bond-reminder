#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from quant_framework.backtest import BacktestEngine
from quant_framework.config import dump_default_config, load_backtest_config
from quant_framework.data import MarketDataModel
from quant_framework.experiment import ExperimentTracker
from quant_framework.report import save_reports
from quant_framework.strategies import CrossSectionalScoringStrategy, MeanReversionStrategy, MultiStrategyBlender, TrendFollowingStrategy


def generate_demo_data(days: int = 300, symbols: list[str] | None = None) -> pd.DataFrame:
    if symbols is None:
        symbols = ["600000.SH", "510300.SH", "160706.OF"]

    np.random.seed(42)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    rows = []

    for symbol in symbols:
        base = 10 + np.random.rand() * 30
        rets = np.random.normal(0.0005, 0.02, len(dates))
        close = base * np.cumprod(1 + rets)
        high = close * (1 + np.random.uniform(0, 0.02, len(dates)))
        low = close * (1 - np.random.uniform(0, 0.02, len(dates)))
        open_ = (high + low) / 2
        volume = np.random.randint(1_000_000, 10_000_000, len(dates))

        for i, dt in enumerate(dates):
            rows.append(
                {
                    "symbol": symbol,
                    "date": dt,
                    "open": open_[i],
                    "high": high[i],
                    "low": low[i],
                    "close": close[i],
                    "volume": volume[i],
                    "asset_type": "fund" if symbol.endswith(".OF") else "stock",
                    "adj_factor": 1.0,
                    "dividend": 0.0,
                    "split_ratio": 1.0,
                    "is_suspended": False,
                }
            )
    return pd.DataFrame(rows)


def build_strategy(name: str):
    if name == "trend":
        return TrendFollowingStrategy()
    if name == "mean_reversion":
        return MeanReversionStrategy()
    if name == "blend":
        return MultiStrategyBlender(
            strategies={"trend": TrendFollowingStrategy(), "mr": MeanReversionStrategy(), "cross": CrossSectionalScoringStrategy()},
            weights={"trend": 0.4, "mr": 0.3, "cross": 0.3},
        )
    return CrossSectionalScoringStrategy()


def main():
    parser = argparse.ArgumentParser(description="Stock and fund technical analysis and quantitative backtesting framework example")
    parser.add_argument("--config", default="configs/backtest.yaml")
    parser.add_argument("--data", help="CSV data path with unified OHLCV schema")
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--strategy", default="blend", choices=["cross_section", "trend", "mean_reversion", "blend"])
    parser.add_argument("--init-config", action="store_true", help="Create default config and exit")
    args = parser.parse_args()

    if args.init_config:
        dump_default_config(args.config)
        print(f"Default configuration created: {args.config}")
        return

    cfg = load_backtest_config(args.config)

    if args.data:
        raw = pd.read_csv(args.data)
    else:
        raw = generate_demo_data()

    data = MarketDataModel.normalize(raw)
    issues = MarketDataModel.validate(data)
    if issues:
        print("Data quality warnings:")
        for issue in issues:
            print(f"- [{issue.column}] {issue.message}")

    adj_data = MarketDataModel.apply_adjustments(data)

    close = MarketDataModel.to_wide_close(adj_data)
    volume = MarketDataModel.to_wide_volume(adj_data)

    strategy = build_strategy(args.strategy)
    signals = strategy.generate_signals({"close": close, "volume": volume})

    engine = BacktestEngine(cfg)
    result = engine.run({"close": close, "volume": volume}, signals)

    tracker = ExperimentTracker()
    run_dir = tracker.start_run(
        name=args.strategy,
        config={"strategy": args.strategy, "config": cfg.__dict__, "output": args.output},
    )
    tracker.log_metrics(run_dir, result.metrics)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_reports(result.equity_curve, result.benchmark_curve, result.holdings, result.trades, result.metrics, str(out_dir))

    print("Backtest complete, core metrics:")
    print(json.dumps(result.metrics.__dict__, ensure_ascii=False, indent=2))
    print(f"Experiment directory: {run_dir}")
    print(f"Output directory: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
