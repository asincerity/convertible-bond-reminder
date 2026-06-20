from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
import pandas as pd


class AssetType(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    LOF = "lof"
    FUND = "fund"


class Frequency(str, Enum):
    DAILY = "1d"
    MINUTE = "1m"


@dataclass(frozen=True)
class BarRecord:
    symbol: str
    asset_type: AssetType
    date: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0
    nav: Optional[float] = None
    adj_factor: float = 1.0
    dividend: float = 0.0
    split_ratio: float = 1.0
    is_suspended: bool = False


@dataclass
class Position:
    symbol: str
    quantity: int
    avg_price: float


@dataclass
class Trade:
    date: pd.Timestamp
    symbol: str
    side: str
    quantity: int
    price: float
    fee: float
    slippage: float


@dataclass
class BacktestConfig:
    initial_cash: float = 1_000_000
    commission_rate: float = 0.0003
    slippage_rate: float = 0.0002
    min_lot_size: int = 100
    t_plus_one: bool = True
    rebalance_frequency: int = 5
    max_position_weight: float = 0.2
    max_drawdown_limit: float = 0.2
    volatility_target: float = 0.2
    stop_loss: float = 0.08
    take_profit: float = 0.2
    benchmark_symbol: str = "000300.SH"
    signal_delay_days: int = 1
    liquidity_limit_ratio: float = 0.1
    metadata: Dict[str, str] = field(default_factory=dict)
