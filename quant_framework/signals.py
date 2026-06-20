from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass
class SignalConfig:
    buy_threshold: float = 0.5
    sell_threshold: float = -0.5
    decay: float = 0.8


def combine_factor_scores(factor_scores: Dict[str, pd.DataFrame], weights: Dict[str, float]) -> pd.DataFrame:
    if not factor_scores:
        raise ValueError("factor_scores is empty")

    first = next(iter(factor_scores.values()))
    score = pd.DataFrame(0.0, index=first.index, columns=first.columns)

    for name, frame in factor_scores.items():
        w = weights.get(name, 0.0)
        score = score.add(frame.fillna(0.0) * w, fill_value=0.0)

    return score


def normalize_signal_scores(raw_scores: pd.DataFrame) -> pd.DataFrame:
    rank = raw_scores.rank(axis=1, pct=True)
    return (rank - 0.5) * 2


def apply_signal_decay(signals: pd.DataFrame, decay: float) -> pd.DataFrame:
    alpha = 1 - decay
    return signals.fillna(0).ewm(alpha=alpha, adjust=False).mean()


def conflict_resolution(signals: pd.DataFrame) -> pd.DataFrame:
    return signals.clip(-1, 1)


def to_trading_signal(score: pd.DataFrame, config: SignalConfig) -> pd.DataFrame:
    normalized = normalize_signal_scores(score)
    decayed = apply_signal_decay(normalized, config.decay)
    clipped = conflict_resolution(decayed)

    out = pd.DataFrame(0, index=score.index, columns=score.columns)
    out[clipped >= config.buy_threshold] = 1
    out[clipped <= config.sell_threshold] = -1
    return out
