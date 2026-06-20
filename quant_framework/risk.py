from __future__ import annotations

import pandas as pd


def cap_position_weights(weights: pd.Series, max_weight: float) -> pd.Series:
    capped = weights.clip(upper=max_weight, lower=-max_weight)
    gross = capped.abs().sum()
    if gross > 1:
        capped = capped / gross
    return capped


def apply_drawdown_guard(equity_curve: pd.Series, current_weights: pd.Series, max_drawdown_limit: float) -> pd.Series:
    peak = equity_curve.cummax()
    dd = (equity_curve - peak) / peak.replace(0, pd.NA)
    if dd.iloc[-1] <= -max_drawdown_limit:
        return pd.Series(0.0, index=current_weights.index)
    return current_weights


def apply_volatility_target(weights: pd.Series, rolling_vol: pd.Series, target_vol: float) -> pd.Series:
    portfolio_vol = (weights.abs() * rolling_vol.reindex(weights.index).fillna(0)).sum()
    if portfolio_vol <= 0:
        return weights
    scale = min(1.0, target_vol / portfolio_vol)
    return weights * scale


def apply_stop_rules(entry_prices: pd.Series, current_prices: pd.Series, weights: pd.Series, stop_loss: float, take_profit: float) -> pd.Series:
    pnl = (current_prices - entry_prices) / entry_prices.replace(0, pd.NA)
    stop_mask = pnl <= -stop_loss
    tp_mask = pnl >= take_profit
    adjusted = weights.copy()
    adjusted[stop_mask | tp_mask] = 0.0
    return adjusted
