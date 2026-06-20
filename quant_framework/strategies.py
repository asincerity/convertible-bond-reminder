from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional

import pandas as pd

from . import factors, indicators
from .signals import SignalConfig, combine_factor_scores, to_trading_signal


class BaseStrategy(ABC):
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        raise NotImplementedError


@dataclass
class TrendFollowingStrategy(BaseStrategy):
    short_window: int = 20
    long_window: int = 60

    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        close = data["close"]
        short_ma = indicators.ma(close, self.short_window)
        long_ma = indicators.ma(close, self.long_window)
        signal = pd.DataFrame(0, index=close.index, columns=close.columns)
        signal[short_ma > long_ma] = 1
        signal[short_ma < long_ma] = -1
        return signal


@dataclass
class MeanReversionStrategy(BaseStrategy):
    window: int = 20
    z_threshold: float = 1.5

    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        close = data["close"]
        rolling_mean = close.rolling(self.window).mean()
        rolling_std = close.rolling(self.window).std().replace(0, pd.NA)
        z = (close - rolling_mean) / rolling_std
        signal = pd.DataFrame(0, index=close.index, columns=close.columns)
        signal[z <= -self.z_threshold] = 1
        signal[z >= self.z_threshold] = -1
        return signal


@dataclass
class CrossSectionalScoringStrategy(BaseStrategy):
    top_n: int = 5
    bottom_n: int = 0
    signal_config: SignalConfig = field(default_factory=SignalConfig)

    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        close = data["close"]
        ret = close.pct_change()

        factor_scores = {
            "momentum": factors.momentum(close, 20),
            "reversal": factors.reversal(close, 5),
            # Prefer lower volatility assets in cross-sectional ranking.
            "volatility": -factors.volatility(close, 20),
            "quality": factors.quality_proxy(ret, 60),
        }
        combined = combine_factor_scores(factor_scores, {"momentum": 0.4, "reversal": 0.2, "volatility": 0.2, "quality": 0.2})
        score_signal = to_trading_signal(combined, self.signal_config)

        final_signal = pd.DataFrame(0, index=score_signal.index, columns=score_signal.columns)
        for dt in score_signal.index:
            row = combined.loc[dt].dropna().sort_values(ascending=False)
            if len(row) == 0:
                continue
            long_syms = row.head(self.top_n).index
            final_signal.loc[dt, long_syms] = 1
            if self.bottom_n > 0:
                short_syms = row.tail(self.bottom_n).index
                final_signal.loc[dt, short_syms] = -1

        return final_signal.where(final_signal != 0, score_signal)


@dataclass
class MultiStrategyBlender(BaseStrategy):
    strategies: Dict[str, BaseStrategy]
    weights: Dict[str, float]
    switch_condition: Optional[pd.Series] = None

    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        base_shape = data["close"]
        combined = pd.DataFrame(0.0, index=base_shape.index, columns=base_shape.columns)

        for name, strategy in self.strategies.items():
            s = strategy.generate_signals(data).reindex_like(base_shape).fillna(0)
            combined += s * self.weights.get(name, 0.0)

        if self.switch_condition is not None:
            cond = self.switch_condition.reindex(base_shape.index).fillna(False)
            combined.loc[~cond] = 0

        out = pd.DataFrame(0, index=base_shape.index, columns=base_shape.columns)
        out[combined > 0.2] = 1
        out[combined < -0.2] = -1
        return out
