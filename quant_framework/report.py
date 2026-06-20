from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

from .metrics import PerformanceMetrics, compute_drawdown


def build_summary(metrics: PerformanceMetrics, strategy_name: str) -> Dict[str, float]:
    d = asdict(metrics)
    d["strategy"] = strategy_name
    return d


def save_reports(equity_curve: pd.Series, benchmark_curve: pd.Series, holdings: pd.DataFrame, trades: pd.DataFrame, metrics: PerformanceMetrics, output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pd.DataFrame([build_summary(metrics, "default")]).to_csv(out / "summary.csv", index=False)
    holdings.to_csv(out / "holdings.csv")
    trades.to_csv(out / "trades.csv", index=False)

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    equity_curve.plot(ax=axes[0], label="strategy")
    benchmark_curve.plot(ax=axes[0], label="benchmark")
    axes[0].legend()
    axes[0].set_title("Net Value Curve")

    compute_drawdown(equity_curve).plot(ax=axes[1], color="red", label="drawdown")
    axes[1].legend()
    axes[1].set_title("Drawdown")

    fig.tight_layout()
    fig.savefig(out / "performance.png", dpi=120)
    plt.close(fig)
