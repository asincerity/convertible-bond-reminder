from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from .execution import ExecutionConstraints, clip_order_by_liquidity
from .metrics import PerformanceMetrics, compute_metrics
from .models import BacktestConfig, Trade
from .risk import apply_drawdown_guard, apply_stop_rules, apply_volatility_target, cap_position_weights


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    benchmark_curve: pd.Series
    returns: pd.Series
    holdings: pd.DataFrame
    trades: pd.DataFrame
    metrics: PerformanceMetrics


class BacktestEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.constraints = ExecutionConstraints(
            min_lot_size=config.min_lot_size,
            t_plus_one=config.t_plus_one,
            liquidity_limit_ratio=config.liquidity_limit_ratio,
        )

    def run(self, data: Dict[str, pd.DataFrame], signals: pd.DataFrame, benchmark: pd.Series | None = None) -> BacktestResult:
        close = data["close"].sort_index()
        volume = data.get("volume", pd.DataFrame(1e9, index=close.index, columns=close.columns)).reindex_like(close).fillna(0)
        returns = close.pct_change().fillna(0)

        signal = signals.reindex_like(close).fillna(0)
        signal = signal.shift(self.config.signal_delay_days).fillna(0)

        cash = self.config.initial_cash
        holdings = pd.DataFrame(0.0, index=close.index, columns=close.columns)
        current_weight = pd.Series(0.0, index=close.columns)
        entry_price = pd.Series(0.0, index=close.columns)

        equity_values: List[float] = []
        trade_log: List[Trade] = []

        for i, dt in enumerate(close.index):
            px = close.loc[dt]
            port_value = cash + (current_weight * (cash if i == 0 else equity_values[-1])).sum()

            if i % self.config.rebalance_frequency == 0:
                target = signal.loc[dt]
                target = cap_position_weights(target, self.config.max_position_weight)

                hist_equity = pd.Series(equity_values, index=close.index[:i]) if i > 0 else pd.Series([self.config.initial_cash], index=[dt])
                target = apply_drawdown_guard(hist_equity, target, self.config.max_drawdown_limit)
                target = apply_volatility_target(target, returns.loc[:dt].tail(20).std(), self.config.volatility_target)
                reference_entry = entry_price.where(entry_price > 0, px)
                target = apply_stop_rules(reference_entry, px, target, self.config.stop_loss, self.config.take_profit)

                current_equity = equity_values[-1] if i > 0 else self.config.initial_cash
                target_notional = (target - current_weight) * current_equity
                target_notional = clip_order_by_liquidity(target_notional, px, volume.loc[dt], self.config.liquidity_limit_ratio)

                for symbol in close.columns:
                    notional = target_notional.get(symbol, 0.0)
                    if abs(notional) < 1e-9 or px[symbol] <= 0:
                        continue

                    qty = int(abs(notional) / px[symbol] / self.config.min_lot_size) * self.config.min_lot_size
                    if qty <= 0:
                        continue

                    side = "BUY" if notional > 0 else "SELL"
                    traded_notional = qty * px[symbol]
                    fee = traded_notional * self.config.commission_rate
                    slippage = traded_notional * self.config.slippage_rate

                    cash += (-traded_notional if side == "BUY" else traded_notional) - fee - slippage
                    delta_weight = (traded_notional / max(current_equity, 1e-9)) * (1 if side == "BUY" else -1)
                    current_weight[symbol] += delta_weight
                    if side == "BUY":
                        entry_price[symbol] = px[symbol]

                    trade_log.append(
                        Trade(
                            date=dt,
                            symbol=symbol,
                            side=side,
                            quantity=qty,
                            price=float(px[symbol]),
                            fee=float(fee),
                            slippage=float(slippage),
                        )
                    )

            current_weight = current_weight.fillna(0)
            holdings.loc[dt] = current_weight
            daily_ret = (holdings.loc[dt] * returns.loc[dt]).sum()
            equity = (equity_values[-1] if i > 0 else self.config.initial_cash) * (1 + daily_ret)
            equity_values.append(equity + cash * 0.0)

        equity_curve = pd.Series(equity_values, index=close.index, name="equity")
        strategy_returns = equity_curve.pct_change().fillna(0)

        if benchmark is None:
            benchmark_curve = (1 + close.iloc[:, 0].pct_change().fillna(0)).cumprod() * self.config.initial_cash
        else:
            benchmark_curve = benchmark.reindex(close.index).ffill().fillna(method="bfill")

        metrics = compute_metrics(strategy_returns, equity_curve)
        trades_df = pd.DataFrame([t.__dict__ for t in trade_log])

        return BacktestResult(
            equity_curve=equity_curve,
            benchmark_curve=benchmark_curve,
            returns=strategy_returns,
            holdings=holdings,
            trades=trades_df,
            metrics=metrics,
        )
