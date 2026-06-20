from __future__ import annotations

import pandas as pd


def momentum(close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    return close / close.shift(window) - 1


def reversal(close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    return -(close / close.shift(window) - 1)


def volatility(close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    return close.pct_change().rolling(window=window, min_periods=window).std() * (252 ** 0.5)


def quality_proxy(returns: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    mean = returns.rolling(window=window, min_periods=window).mean()
    std = returns.rolling(window=window, min_periods=window).std().replace(0, pd.NA)
    return mean / std


def zscore(df: pd.DataFrame) -> pd.DataFrame:
    mean = df.mean(axis=1)
    std = df.std(axis=1).replace(0, pd.NA)
    return df.sub(mean, axis=0).div(std, axis=0)
