"""
Market Regime Detector — identifies the current market state.

Regimes:
- TRENDING_UP: strong upward momentum, low volatility relative to trend
- TRENDING_DOWN: strong downward momentum
- RANGING: low momentum, price oscillating around mean
- VOLATILE: high volatility regardless of direction
- BREAKOUT: transition from range to trend (high volume + momentum spike)

Agents with high regime_sensitivity adapt their behavior based on detected regime.
"""

import numpy as np
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class MarketRegime(Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"


@dataclass
class RegimeState:
    regime: MarketRegime
    confidence: float  # [0, 1]
    momentum: float    # raw momentum value
    volatility: float  # raw volatility value
    trend_strength: float  # [0, 1]


class RegimeDetector:
    """Detect market regime from price data."""

    def __init__(self, lookback: int = 50, vol_window: int = 20):
        self.lookback = lookback
        self.vol_window = vol_window
        self.history: List[RegimeState] = []

    def detect(self, candles: np.ndarray) -> RegimeState:
        """
        Detect current market regime from OHLCV candles.

        candles: numpy array with columns [timestamp, open, high, low, close, volume]
        """
        if len(candles) < self.lookback:
            return RegimeState(
                regime=MarketRegime.RANGING,
                confidence=0.0,
                momentum=0.0,
                volatility=0.0,
                trend_strength=0.0,
            )

        closes = candles[-self.lookback:, 4]
        volumes = candles[-self.lookback:, 5]

        momentum = self._calc_momentum(closes)
        volatility = self._calc_volatility(closes)
        trend_strength = self._calc_trend_strength(closes)
        volume_spike = self._calc_volume_spike(volumes)

        regime, confidence = self._classify(momentum, volatility, trend_strength, volume_spike)

        state = RegimeState(
            regime=regime,
            confidence=confidence,
            momentum=momentum,
            volatility=volatility,
            trend_strength=trend_strength,
        )
        self.history.append(state)
        return state

    def detect_series(self, candles: np.ndarray, step: int = 1) -> List[RegimeState]:
        """Detect regime for each position in the data."""
        states = []
        for i in range(self.lookback, len(candles), step):
            state = self.detect(candles[:i + 1])
            states.append(state)
        return states

    def get_regime_transitions(self) -> List[Dict]:
        """Find points where regime changed."""
        transitions = []
        for i in range(1, len(self.history)):
            if self.history[i].regime != self.history[i - 1].regime:
                transitions.append({
                    'index': i,
                    'from': self.history[i - 1].regime.value,
                    'to': self.history[i].regime.value,
                    'confidence': self.history[i].confidence,
                })
        return transitions

    def _calc_momentum(self, closes: np.ndarray) -> float:
        """Normalized rate of change."""
        if closes[0] == 0:
            return 0.0
        roc = (closes[-1] - closes[0]) / closes[0]
        return float(roc)

    def _calc_volatility(self, closes: np.ndarray) -> float:
        """Annualized volatility from recent returns."""
        if len(closes) < 2:
            return 0.0
        denominator = closes[:-1]
        if np.any(denominator == 0):
            return 0.0
        returns = np.diff(closes) / denominator
        return float(np.std(returns[-self.vol_window:]) * np.sqrt(252 * 24))  # hourly data

    def _calc_trend_strength(self, closes: np.ndarray) -> float:
        """R-squared of linear regression — how well price follows a line."""
        n = len(closes)
        x = np.arange(n)
        x_mean = x.mean()
        y_mean = closes.mean()

        ss_xy = np.sum((x - x_mean) * (closes - y_mean))
        ss_xx = np.sum((x - x_mean) ** 2)
        ss_yy = np.sum((closes - y_mean) ** 2)

        if ss_xx == 0 or ss_yy == 0:
            return 0.0

        r_squared = (ss_xy ** 2) / (ss_xx * ss_yy)
        return float(np.clip(r_squared, 0, 1))

    def _calc_volume_spike(self, volumes: np.ndarray) -> float:
        """Current volume relative to recent average."""
        if len(volumes) < 20:
            return 1.0
        avg = np.mean(volumes[-20:-1])
        if avg == 0:
            return 1.0
        return float(volumes[-1] / avg)

    def _classify(self, momentum: float, volatility: float,
                  trend_strength: float, volume_spike: float) -> tuple:
        """Classify regime from indicators."""

        # Breakout: high volume + emerging trend from low trend_strength
        if volume_spike > 2.0 and abs(momentum) > 0.03 and trend_strength > 0.3:
            confidence = min(1.0, volume_spike / 3.0 * trend_strength)
            return MarketRegime.BREAKOUT, confidence

        # Volatile: high volatility, weak trend
        if volatility > 0.8 and trend_strength < 0.4:
            confidence = min(1.0, volatility / 1.5)
            return MarketRegime.VOLATILE, confidence

        # Trending up: positive momentum + strong trend
        if momentum > 0.02 and trend_strength > 0.5:
            confidence = min(1.0, trend_strength * (1 + abs(momentum) * 10))
            return MarketRegime.TRENDING_UP, confidence

        # Trending down: negative momentum + strong trend
        if momentum < -0.02 and trend_strength > 0.5:
            confidence = min(1.0, trend_strength * (1 + abs(momentum) * 10))
            return MarketRegime.TRENDING_DOWN, confidence

        # Ranging: low momentum, low trend strength
        confidence = min(1.0, (1 - trend_strength) * (1 - abs(momentum) * 20))
        return MarketRegime.RANGING, max(0, confidence)
