from __future__ import annotations

import pandas as pd


def ma(close: pd.DataFrame, window: int) -> pd.DataFrame:
    return close.rolling(window=window, min_periods=window).mean()


def macd(close: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = dif - dea
    return dif, dea, hist


def rsi(close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def kdj(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 9):
    ll = low.rolling(window=window, min_periods=window).min()
    hh = high.rolling(window=window, min_periods=window).max()
    rsv = (close - ll) / (hh - ll).replace(0, pd.NA) * 100
    k = rsv.ewm(alpha=1 / 3, adjust=False).mean()
    d = k.ewm(alpha=1 / 3, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def boll(close: pd.DataFrame, window: int = 20, num_std: float = 2.0):
    mid = close.rolling(window=window, min_periods=window).mean()
    std = close.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def atr(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    if not (high.columns.equals(low.columns) and high.columns.equals(close.columns)):
        raise ValueError("high, low, close must share identical columns")
    if not (high.index.equals(low.index) and high.index.equals(close.index)):
        raise ValueError("high, low, close must share identical index")

    prev_close = close.shift(1)
    tr_components = {
        "hl": (high - low),
        "hc": (high - prev_close).abs(),
        "lc": (low - prev_close).abs(),
    }
    # Dict-concat builds MultiIndex columns (component, symbol); groupby(level=1) takes max TR across hl/hc/lc per symbol.
    tr = pd.concat(tr_components, axis=1).groupby(level=1, axis=1).max()
    return tr.rolling(window=window, min_periods=window).mean()
