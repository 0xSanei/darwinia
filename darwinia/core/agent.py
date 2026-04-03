"""
Trading Agent — interprets DNA genes into actual trading decisions.

The agent receives market data (OHLCV candles) and produces a sequence
of trade actions. It does NOT know it is being evolved — it simply
trades based on its DNA parameters.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional
from .dna import AgentDNA
from .types import TradeAction, Signal, Position, TradeResult


@dataclass
class AgentState:
    position: Optional[Position] = None
    cash: float = 10000.0
    trade_history: List[TradeResult] = None

    def __post_init__(self):
        if self.trade_history is None:
            self.trade_history = []


class TradingAgent:
    """
    Executes a trading strategy defined by its DNA.

    Gene interpretation:
    - Signal weights -> how much each indicator matters
    - Thresholds -> when to enter/exit
    - Personality -> position sizing, timing, direction bias
    """

    def __init__(self, dna: AgentDNA):
        self.dna = dna
        self.state = AgentState()

    def run(self, candles: np.ndarray) -> List[TradeResult]:
        """
        Run the agent through a series of candles.

        candles: numpy array with columns [timestamp, open, high, low, close, volume]
        Returns: list of completed trades
        """
        lookback = self._map_lookback()

        for i in range(lookback, len(candles)):
            window = candles[max(0, i - lookback):i + 1]
            signal = self._compute_signal(window)
            action = self._decide(signal, candles[i])

            if action == TradeAction.BUY:
                if self.state.position and self.state.position.direction == 'short':
                    self._close_position(candles[i])
                if self.state.position is None:
                    self._open_position(candles[i], 'long')
            elif action == TradeAction.SELL:
                if self.state.position and self.state.position.direction == 'long':
                    self._close_position(candles[i])
                if self.state.position is None:
                    self._open_position(candles[i], 'short')

            if self.state.position is not None:
                self._check_exits(candles[i])

        # Close any open position at end
        if self.state.position is not None:
            self._close_position(candles[-1])

        return self.state.trade_history

    def _compute_signal(self, window: np.ndarray) -> Signal:
        """Compute composite trading signal from DNA-weighted indicators."""
        closes = window[:, 4]  # Close prices
        volumes = window[:, 5]  # Volume

        momentum = self._calc_momentum(closes)
        vol_signal = self._calc_volume_signal(volumes)
        volatility = self._calc_volatility(closes)
        mean_rev = self._calc_mean_reversion(closes)
        trend = self._calc_trend(closes)

        weights = np.array([
            self.dna.weight_price_momentum,
            self.dna.weight_volume,
            self.dna.weight_volatility,
            self.dna.weight_mean_reversion,
            self.dna.weight_trend,
        ])
        signals = np.array([momentum, vol_signal, volatility, mean_rev, trend])

        weights = weights / (weights.sum() + 1e-8)

        composite = np.dot(weights, signals)
        if self.dna.contrarian_bias > 0.5:
            inversion = (self.dna.contrarian_bias - 0.5) * 2
            composite = composite * (1 - inversion) + (-composite) * inversion

        return Signal(
            composite=composite,
            components={
                'momentum': momentum,
                'volume': vol_signal,
                'volatility': volatility,
                'mean_reversion': mean_rev,
                'trend': trend,
            }
        )

    def _decide(self, signal: Signal, current_candle: np.ndarray) -> TradeAction:
        """Map signal to action using DNA thresholds + patience."""
        entry_thresh = self.dna.entry_threshold * 0.3 + 0.05   # [0.05, 0.35]
        exit_thresh = -(self.dna.exit_threshold * 0.3 + 0.05)  # [-0.35, -0.05]

        if signal.composite > entry_thresh:
            return TradeAction.BUY
        elif signal.composite < exit_thresh:
            return TradeAction.SELL
        else:
            return TradeAction.HOLD

    def _map_lookback(self) -> int:
        """Map time_horizon gene [0,1] to actual lookback period."""
        return int(10 + self.dna.time_horizon * 190)  # 10 to 200 candles

    def _calc_momentum(self, closes: np.ndarray) -> float:
        """Price momentum: rate of change normalized."""
        if len(closes) < 2:
            return 0.0
        idx = -10 if len(closes) >= 10 else 0
        roc = (closes[-1] - closes[idx]) / closes[idx]
        return float(np.clip(roc * 10, -1, 1))

    def _calc_volume_signal(self, volumes: np.ndarray) -> float:
        """Volume anomaly: current vs moving average."""
        if len(volumes) < 20:
            return 0.0
        avg = np.mean(volumes[-20:])
        if avg == 0:
            return 0.0
        ratio = volumes[-1] / avg - 1.0
        return float(np.clip(ratio, -1, 1))

    def _calc_volatility(self, closes: np.ndarray) -> float:
        """Volatility signal: high vol = bearish bias for conservatives."""
        if len(closes) < 20:
            return 0.0
        returns = np.diff(closes) / closes[:-1]
        vol = np.std(returns[-20:])
        return float(np.clip(-vol * 50 + 0.5, -1, 1))

    def _calc_mean_reversion(self, closes: np.ndarray) -> float:
        """Mean reversion: distance from moving average."""
        if len(closes) < 20:
            return 0.0
        ma = np.mean(closes[-20:])
        deviation = (closes[-1] - ma) / ma
        return float(np.clip(-deviation * 20, -1, 1))

    def _calc_trend(self, closes: np.ndarray) -> float:
        """Trend signal: EMA crossover direction."""
        if len(closes) < 50:
            return 0.0
        ema_fast = self._ema(closes, 12)
        ema_slow = self._ema(closes, 26)
        diff = (ema_fast - ema_slow) / ema_slow
        return float(np.clip(diff * 50, -1, 1))

    def _ema(self, data: np.ndarray, period: int) -> float:
        """Exponential moving average."""
        if len(data) < period:
            return float(np.mean(data))
        multiplier = 2 / (period + 1)
        ema = data[0]
        for val in data[1:]:
            ema = (val - ema) * multiplier + ema
        return float(ema)

    def _open_position(self, candle: np.ndarray, direction: str):
        """Open a new position."""
        price = candle[4]
        allocation = 0.1 + self.dna.position_sizing * 0.9
        size = (self.state.cash * allocation) / price

        self.state.position = Position(
            direction=direction,
            entry_price=price,
            size=size,
            entry_time=candle[0],
        )
        self.state.cash -= size * price

    def _close_position(self, candle: np.ndarray):
        """Close current position and record result."""
        if self.state.position is None:
            return

        price = candle[4]
        pos = self.state.position

        if pos.direction == 'long':
            pnl = (price - pos.entry_price) * pos.size
            pnl_pct = (price - pos.entry_price) / pos.entry_price
        else:
            pnl = (pos.entry_price - price) * pos.size
            pnl_pct = (pos.entry_price - price) / pos.entry_price

        self.state.cash += pos.size * pos.entry_price + pnl
        self.state.trade_history.append(TradeResult(
            entry_price=pos.entry_price,
            exit_price=price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            entry_time=pos.entry_time,
            exit_time=candle[0],
            direction=pos.direction,
        ))
        self.state.position = None

    def _check_exits(self, candle: np.ndarray):
        """Check stop loss and take profit."""
        if self.state.position is None:
            return

        pos = self.state.position
        current_price = candle[4]

        if pos.direction == 'long':
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price
        else:
            pnl_pct = (pos.entry_price - current_price) / pos.entry_price

        sl = self.dna.stop_loss_pct * 0.2
        tp = self.dna.take_profit_pct * 0.5

        if pnl_pct <= -sl:
            self._close_position(candle)
        elif pnl_pct >= tp:
            self._close_position(candle)
