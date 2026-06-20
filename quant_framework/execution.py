from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass
class ExecutionConstraints:
    min_lot_size: int = 100
    t_plus_one: bool = True
    up_limit: float = 0.1
    down_limit: float = 0.1
    liquidity_limit_ratio: float = 0.1


def executable_mask(close: pd.DataFrame, prev_close: pd.DataFrame, is_suspended: pd.DataFrame, volume: pd.DataFrame, constraints: ExecutionConstraints) -> pd.DataFrame:
    up_limit_price = prev_close * (1 + constraints.up_limit)
    down_limit_price = prev_close * (1 - constraints.down_limit)
    limit_locked = (close >= up_limit_price) | (close <= down_limit_price)
    low_liquidity = volume <= 0
    return ~(is_suspended | limit_locked | low_liquidity)


def clip_order_by_liquidity(target_notional: pd.Series, price: pd.Series, volume: pd.Series, liquidity_limit_ratio: float) -> pd.Series:
    volume_cap = volume * liquidity_limit_ratio
    notional_cap = volume_cap * price
    return target_notional.clip(lower=-notional_cap, upper=notional_cap)
