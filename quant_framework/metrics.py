from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass
class PerformanceMetrics:
    annual_return: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    win_rate: float


def compute_drawdown(equity_curve: pd.Series) -> pd.Series:
    peak = equity_curve.cummax()
    return (equity_curve - peak) / peak.replace(0, pd.NA)


def compute_metrics(returns: pd.Series, equity_curve: pd.Series, periods_per_year: int = 252) -> PerformanceMetrics:
    if len(returns) == 0:
        return PerformanceMetrics(0, 0, 0, 0, 0, 0)

    ann_return = (1 + returns).prod() ** (periods_per_year / max(len(returns), 1)) - 1
    vol = returns.std() * (periods_per_year ** 0.5)
    downside = returns[returns < 0].std() * (periods_per_year ** 0.5)
    sharpe = ann_return / vol if vol and vol > 0 else 0.0
    sortino = ann_return / downside if downside and downside > 0 else 0.0

    drawdown = compute_drawdown(equity_curve)
    max_dd = drawdown.min() if len(drawdown) > 0 else 0.0
    calmar = ann_return / abs(max_dd) if max_dd and max_dd < 0 else 0.0

    win_rate = (returns > 0).mean()
    return PerformanceMetrics(float(ann_return), float(sharpe), float(sortino), float(calmar), float(max_dd), float(win_rate))
