"""
Benchmark comparison module.

Compares an evolved strategy against common baseline strategies
to contextualize performance.
"""

import random
from dataclasses import dataclass, asdict
from typing import List, Dict

import numpy as np

from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from ..core.market import MarketEnvironment
from ..core.types import TradeResult
from ..backtest.metrics import compute_metrics


@dataclass
class BenchmarkResult:
    """Summary result for a single strategy."""
    strategy_name: str
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    num_trades: int

    def to_dict(self) -> Dict:
        return asdict(self)


def _make_trade(entry_price: float, exit_price: float,
                entry_time: float, exit_time: float,
                size: float = 1.0) -> TradeResult:
    """Helper to build a TradeResult for a long trade of given size."""
    pnl = (exit_price - entry_price) * size
    pnl_pct = (exit_price - entry_price) / entry_price if entry_price > 0 else 0.0
    return TradeResult(
        entry_price=entry_price,
        exit_price=exit_price,
        pnl=pnl,
        pnl_pct=pnl_pct,
        entry_time=entry_time,
        exit_time=exit_time,
        direction='long',
    )


def _result_from_trades(name: str, trades: List[TradeResult],
                        initial_capital: float) -> BenchmarkResult:
    """Compute metrics and wrap into a BenchmarkResult."""
    m = compute_metrics(trades, initial_capital=initial_capital)
    return BenchmarkResult(
        strategy_name=name,
        total_return=m.total_return,
        total_return_pct=m.total_return_pct,
        sharpe_ratio=m.sharpe_ratio,
        max_drawdown_pct=m.max_drawdown_pct,
        win_rate=m.win_rate,
        num_trades=m.num_trades,
    )


# ---------------------------------------------------------------------------
# Baseline strategies — each returns List[TradeResult]
# ---------------------------------------------------------------------------

def buy_and_hold(candles: np.ndarray, initial_capital: float) -> List[TradeResult]:
    """Buy at first candle open, sell at last candle close. Single trade."""
    entry_price = candles[0, 1]   # open
    exit_price = candles[-1, 4]   # close
    entry_time = candles[0, 0]
    exit_time = candles[-1, 0]
    size = initial_capital / entry_price if entry_price > 0 else 0.0
    return [_make_trade(entry_price, exit_price, entry_time, exit_time, size)]


def random_trader(candles: np.ndarray, initial_capital: float) -> List[TradeResult]:
    """Random buy/sell at each candle with 5% probability. Seed=42."""
    rng = random.Random(42)
    trades: List[TradeResult] = []
    in_position = False
    entry_price = 0.0
    entry_time = 0.0
    size = 0.0

    for i in range(len(candles)):
        price = candles[i, 4]  # close
        ts = candles[i, 0]

        if not in_position:
            if rng.random() < 0.05:
                entry_price = price
                entry_time = ts
                size = initial_capital / price if price > 0 else 0.0
                in_position = True
        else:
            if rng.random() < 0.05:
                trades.append(_make_trade(entry_price, price, entry_time, ts, size))
                initial_capital += (price - entry_price) * size
                in_position = False

    # Close open position at end
    if in_position:
        price = candles[-1, 4]
        ts = candles[-1, 0]
        trades.append(_make_trade(entry_price, price, entry_time, ts, size))

    return trades


def mean_reversion(candles: np.ndarray, initial_capital: float) -> List[TradeResult]:
    """Buy when price drops >2% below 20-period SMA, sell when >2% above."""
    period = 20
    threshold = 0.02
    trades: List[TradeResult] = []
    in_position = False
    entry_price = 0.0
    entry_time = 0.0
    size = 0.0
    capital = initial_capital

    closes = candles[:, 4]

    for i in range(period, len(candles)):
        sma = closes[i - period:i].mean()
        price = closes[i]
        ts = candles[i, 0]

        if not in_position:
            if price < sma * (1 - threshold):
                entry_price = price
                entry_time = ts
                size = capital / price if price > 0 else 0.0
                in_position = True
        else:
            if price > sma * (1 + threshold):
                trades.append(_make_trade(entry_price, price, entry_time, ts, size))
                capital += (price - entry_price) * size
                in_position = False

    # Close open position at end
    if in_position:
        price = closes[-1]
        ts = candles[-1, 0]
        trades.append(_make_trade(entry_price, price, entry_time, ts, size))

    return trades


def momentum(candles: np.ndarray, initial_capital: float) -> List[TradeResult]:
    """Buy when 10-period momentum > 0 and volume above average, sell when momentum < 0."""
    period = 10
    trades: List[TradeResult] = []
    in_position = False
    entry_price = 0.0
    entry_time = 0.0
    size = 0.0
    capital = initial_capital

    closes = candles[:, 4]
    volumes = candles[:, 5]

    for i in range(period, len(candles)):
        mom = closes[i] - closes[i - period]
        avg_vol = volumes[i - period:i].mean()
        vol = volumes[i]
        price = closes[i]
        ts = candles[i, 0]

        if not in_position:
            if mom > 0 and vol > avg_vol:
                entry_price = price
                entry_time = ts
                size = capital / price if price > 0 else 0.0
                in_position = True
        else:
            if mom < 0:
                trades.append(_make_trade(entry_price, price, entry_time, ts, size))
                capital += (price - entry_price) * size
                in_position = False

    # Close open position at end
    if in_position:
        price = closes[-1]
        ts = candles[-1, 0]
        trades.append(_make_trade(entry_price, price, entry_time, ts, size))

    return trades


def dca(candles: np.ndarray, initial_capital: float, interval: int = 20) -> List[TradeResult]:
    """Buy fixed amount every N candles, sell all at end."""
    num_buys = len(candles) // interval
    if num_buys == 0:
        num_buys = 1
    amount_per_buy = initial_capital / num_buys

    trades: List[TradeResult] = []
    exit_price = candles[-1, 4]
    exit_time = candles[-1, 0]

    for k in range(num_buys):
        idx = k * interval
        if idx >= len(candles):
            break
        price = candles[idx, 4]  # close
        ts = candles[idx, 0]
        size = amount_per_buy / price if price > 0 else 0.0
        trades.append(_make_trade(price, exit_price, ts, exit_time, size))

    return trades


# ---------------------------------------------------------------------------
# BenchmarkSuite
# ---------------------------------------------------------------------------

class BenchmarkSuite:
    """Run an evolved strategy against baseline strategies."""

    BASELINES = {
        'buy_and_hold': buy_and_hold,
        'random_trader': random_trader,
        'mean_reversion': mean_reversion,
        'momentum': momentum,
        'dca': dca,
    }

    def __init__(self, data_dir: str = 'data', initial_capital: float = 10000.0):
        self.data_dir = data_dir
        self.initial_capital = initial_capital
        self.market = MarketEnvironment(data_dir=data_dir)

    def run(self, dna: AgentDNA, data_file: str) -> Dict:
        """
        Run evolved strategy and all baselines on the same data.

        Returns dict with keys:
            evolved   - BenchmarkResult for the evolved strategy
            baselines - list of BenchmarkResult for each baseline
            ranking   - all results sorted by sharpe_ratio descending
        """
        candles = self.market.load_csv(data_file)

        # Run evolved strategy
        agent = TradingAgent(dna)
        agent.state.cash = self.initial_capital
        evolved_trades = agent.run(candles)
        evolved_result = _result_from_trades(
            'evolved', evolved_trades, self.initial_capital
        )

        # Run baselines
        baseline_results: List[BenchmarkResult] = []
        for name, fn in self.BASELINES.items():
            trades = fn(candles, self.initial_capital)
            result = _result_from_trades(name, trades, self.initial_capital)
            baseline_results.append(result)

        # Ranking by sharpe ratio descending
        all_results = [evolved_result] + baseline_results
        ranking = sorted(all_results, key=lambda r: r.sharpe_ratio, reverse=True)

        return {
            'evolved': evolved_result,
            'baselines': baseline_results,
            'ranking': ranking,
        }
