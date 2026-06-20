from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd

from .models import AssetType


REQUIRED_COLUMNS = ["symbol", "date", "open", "high", "low", "close", "volume"]
OPTIONAL_COLUMNS_DEFAULTS = {
    "amount": 0.0,
    "nav": np.nan,
    "adj_factor": 1.0,
    "dividend": 0.0,
    "split_ratio": 1.0,
    "is_suspended": False,
    "asset_type": AssetType.STOCK.value,
}


@dataclass
class DataValidationIssue:
    column: str
    message: str


class MarketDataModel:
    """Unified OHLCV+NAV data model with validation and adjustment handling."""

    @staticmethod
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result.columns = [c.lower() for c in result.columns]

        missing = [c for c in REQUIRED_COLUMNS if c not in result.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        for col, default in OPTIONAL_COLUMNS_DEFAULTS.items():
            if col not in result.columns:
                result[col] = default

        result["date"] = pd.to_datetime(result["date"])
        result = result.sort_values(["symbol", "date"]).reset_index(drop=True)
        return result

    @staticmethod
    def validate(df: pd.DataFrame, abnormal_jump_threshold: float = 0.3) -> List[DataValidationIssue]:
        issues: List[DataValidationIssue] = []

        for col in ["open", "high", "low", "close", "volume"]:
            if (df[col] < 0).any():
                issues.append(DataValidationIssue(col, "negative value detected"))

        invalid_ohlc = (df["high"] < df["low"]) | (df["open"] < df["low"]) | (df["open"] > df["high"]) | (df["close"] < df["low"]) | (df["close"] > df["high"])
        if invalid_ohlc.any():
            issues.append(DataValidationIssue("ohlc", "inconsistent OHLC relationship"))

        if df["date"].isna().any():
            issues.append(DataValidationIssue("date", "missing date values"))

        if df["symbol"].isna().any():
            issues.append(DataValidationIssue("symbol", "missing symbol values"))

        grouped = df.groupby("symbol", sort=False)
        for symbol, group in grouped:
            if group["date"].duplicated().any():
                issues.append(DataValidationIssue("date", f"duplicate date for symbol {symbol}"))

            returns = group["close"].pct_change().abs()
            if (returns > abnormal_jump_threshold).any():
                threshold_pct = abnormal_jump_threshold * 100
                issues.append(DataValidationIssue("close", f"abnormal jump (>{threshold_pct:.1f}%) for symbol {symbol}"))

        return issues

    @staticmethod
    def apply_adjustments(df: pd.DataFrame, price_columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
        result = df.copy()
        if price_columns is None:
            price_columns = ["open", "high", "low", "close"]

        for col in price_columns:
            result[col] = result[col] * result["adj_factor"]

        split_ratio = result["split_ratio"].replace(0, 1)
        for col in price_columns:
            result[col] = result[col] - result["dividend"]
            result[col] = result[col] / split_ratio
        return result

    @staticmethod
    def to_wide_close(df: pd.DataFrame) -> pd.DataFrame:
        return df.pivot(index="date", columns="symbol", values="close").sort_index()

    @staticmethod
    def to_wide_volume(df: pd.DataFrame) -> pd.DataFrame:
        return df.pivot(index="date", columns="symbol", values="volume").sort_index()
