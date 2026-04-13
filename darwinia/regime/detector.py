"""
Regime Detector — classify market states from price data.

Uses a rolling-window statistical approach to label each candle window
as one of: trending_up, trending_down, mean_reverting, high_volatility,
or low_volatility. No external HMM library needed — pure numpy.

Evolved agents can condition their behavior on detected regimes,
enabling adaptive strategies that shift between momentum and
mean-reversion depending on the market state.
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


class RegimeLabel(Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    MEAN_REVERTING = "mean_reverting"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class RegimeSegment:
    """A contiguous block of candles sharing the same regime."""
    regime: RegimeLabel
    start_idx: int
    end_idx: int
    duration: int
    avg_return: float
    volatility: float

    def to_dict(self) -> Dict:
        return {
            "regime": self.regime.value,
            "start_idx": self.start_idx,
            "end_idx": self.end_idx,
            "duration": self.duration,
            "avg_return": round(self.avg_return, 6),
            "volatility": round(self.volatility, 6),
        }


@dataclass
class RegimeResult:
    """Full output of regime detection."""
    labels: List[RegimeLabel]
    segments: List[RegimeSegment]
    regime_distribution: Dict[str, float]
    transition_matrix: Dict[str, Dict[str, float]]
    dominant_regime: str
    regime_stability: float  # avg segment length / total length

    def to_dict(self) -> Dict:
        return {
            "total_candles": len(self.labels),
            "num_segments": len(self.segments),
            "dominant_regime": self.dominant_regime,
            "regime_stability": round(self.regime_stability, 4),
            "distribution": {k: round(v, 4) for k, v in self.regime_distribution.items()},
            "transition_matrix": {
                k: {k2: round(v2, 4) for k2, v2 in v.items()}
                for k, v in self.transition_matrix.items()
            },
            "segments": [s.to_dict() for s in self.segments],
        }

    def summary(self) -> str:
        lines = [
            f"{'─' * 56}",
            f"  MARKET REGIME ANALYSIS",
            f"{'─' * 56}",
            f"  Candles:    {len(self.labels)}",
            f"  Segments:   {len(self.segments)}",
            f"  Dominant:   {self.dominant_regime}",
            f"  Stability:  {self.regime_stability:.4f}",
            f"{'─' * 56}",
            f"  Distribution:",
        ]
        for regime, pct in sorted(self.regime_distribution.items(), key=lambda x: -x[1]):
            bar_w = max(0, min(20, int(round(pct * 20))))
            bar = "█" * bar_w + "░" * (20 - bar_w)
            lines.append(f"    {regime:<20} {bar} {pct:>6.1%}")
        lines.append(f"{'─' * 56}")
        return "\n".join(lines)


class RegimeDetector:
    """
    Classify market data into regimes using rolling statistical features.

    Algorithm:
    1. Compute rolling returns, volatility, and trend strength.
    2. Use z-score thresholds to assign regime labels per window.
    3. Merge consecutive same-label windows into segments.
    4. Build transition matrix and distribution stats.
    """

    def __init__(
        self,
        window: int = 20,
        trend_threshold: float = 1.0,
        vol_threshold: float = 1.0,
    ) -> None:
        self.window = max(5, window)
        self.trend_threshold = trend_threshold
        self.vol_threshold = vol_threshold

    def detect(self, candles: np.ndarray) -> RegimeResult:
        """
        Run regime detection on OHLCV candles.

        candles: numpy array with columns [timestamp, open, high, low, close, volume]
        Returns RegimeResult.
        """
        closes = candles[:, 4].astype(float)
        n = len(closes)

        if n < self.window + 1:
            label = RegimeLabel.LOW_VOLATILITY
            labels = [label] * n
            seg = RegimeSegment(
                regime=label, start_idx=0, end_idx=n - 1,
                duration=n, avg_return=0.0, volatility=0.0,
            )
            return RegimeResult(
                labels=labels, segments=[seg],
                regime_distribution={label.value: 1.0},
                transition_matrix={}, dominant_regime=label.value,
                regime_stability=1.0,
            )

        # Compute log returns
        log_returns = np.diff(np.log(np.maximum(closes, 1e-10)))

        # Rolling features
        labels: List[RegimeLabel] = [RegimeLabel.LOW_VOLATILITY] * self.window

        # Global stats for z-scoring
        global_vol = float(np.std(log_returns)) if len(log_returns) > 1 else 1e-6
        global_vol = max(global_vol, 1e-8)

        for i in range(self.window, n):
            window_returns = log_returns[max(0, i - self.window): i]
            if len(window_returns) < 2:
                labels.append(RegimeLabel.LOW_VOLATILITY)
                continue

            mean_ret = float(np.mean(window_returns))
            local_vol = float(np.std(window_returns, ddof=1))

            # Trend strength: mean return z-scored against global volatility
            trend_z = mean_ret / global_vol

            # Volatility z-score: local vol vs global vol
            vol_z = (local_vol - global_vol) / max(global_vol, 1e-8)

            # Hurst-like mean reversion: autocorrelation of returns
            if len(window_returns) > 2:
                autocorr = float(np.corrcoef(window_returns[:-1], window_returns[1:])[0, 1])
                if np.isnan(autocorr):
                    autocorr = 0.0
            else:
                autocorr = 0.0

            # Decision tree for regime classification
            label = self._classify(trend_z, vol_z, autocorr)
            labels.append(label)

        # Build segments
        segments = self._build_segments(labels, log_returns, closes)

        # Distribution
        total = len(labels)
        distribution: Dict[str, float] = {}
        for lbl in RegimeLabel:
            count = sum(1 for l in labels if l == lbl)
            distribution[lbl.value] = count / total

        # Dominant
        dominant = max(distribution, key=distribution.get)

        # Transition matrix
        transitions = self._build_transitions(labels)

        # Stability: avg segment length / total
        avg_seg_len = np.mean([s.duration for s in segments]) if segments else total
        stability = avg_seg_len / total

        return RegimeResult(
            labels=labels,
            segments=segments,
            regime_distribution=distribution,
            transition_matrix=transitions,
            dominant_regime=dominant,
            regime_stability=stability,
        )

    def _classify(self, trend_z: float, vol_z: float, autocorr: float) -> RegimeLabel:
        """Classify a single window into a regime label."""
        # Strong mean reversion signal
        if autocorr < -0.3:
            return RegimeLabel.MEAN_REVERTING

        # High or low volatility
        if vol_z > self.vol_threshold:
            # High vol with a trend direction
            if trend_z > self.trend_threshold * 0.5:
                return RegimeLabel.TRENDING_UP
            elif trend_z < -self.trend_threshold * 0.5:
                return RegimeLabel.TRENDING_DOWN
            return RegimeLabel.HIGH_VOLATILITY

        if vol_z < -self.vol_threshold:
            return RegimeLabel.LOW_VOLATILITY

        # Trend-based
        if trend_z > self.trend_threshold:
            return RegimeLabel.TRENDING_UP
        if trend_z < -self.trend_threshold:
            return RegimeLabel.TRENDING_DOWN

        # Default: check weaker signals
        if abs(autocorr) > 0.15 and autocorr < 0:
            return RegimeLabel.MEAN_REVERTING

        return RegimeLabel.LOW_VOLATILITY

    def _build_segments(
        self, labels: List[RegimeLabel], log_returns: np.ndarray, closes: np.ndarray,
    ) -> List[RegimeSegment]:
        """Merge consecutive same-label candles into segments."""
        if not labels:
            return []

        segments = []
        start = 0
        current = labels[0]

        for i in range(1, len(labels)):
            if labels[i] != current:
                seg = self._make_segment(current, start, i - 1, log_returns, closes)
                segments.append(seg)
                start = i
                current = labels[i]

        # Final segment
        segments.append(self._make_segment(current, start, len(labels) - 1, log_returns, closes))
        return segments

    def _make_segment(
        self, regime: RegimeLabel, start: int, end: int,
        log_returns: np.ndarray, closes: np.ndarray,
    ) -> RegimeSegment:
        duration = end - start + 1
        # Safely slice returns (returns array is 1 shorter than closes)
        ret_start = max(0, start - 1)
        ret_end = min(len(log_returns), end)
        seg_returns = log_returns[ret_start:ret_end] if ret_end > ret_start else np.array([0.0])
        avg_return = float(np.mean(seg_returns)) if len(seg_returns) > 0 else 0.0
        volatility = float(np.std(seg_returns, ddof=1)) if len(seg_returns) > 1 else 0.0

        return RegimeSegment(
            regime=regime, start_idx=start, end_idx=end,
            duration=duration, avg_return=avg_return, volatility=volatility,
        )

    def _build_transitions(self, labels: List[RegimeLabel]) -> Dict[str, Dict[str, float]]:
        """Build regime transition probability matrix."""
        all_regimes = [r.value for r in RegimeLabel]
        counts: Dict[str, Dict[str, int]] = {
            r: {r2: 0 for r2 in all_regimes} for r in all_regimes
        }

        for i in range(len(labels) - 1):
            counts[labels[i].value][labels[i + 1].value] += 1

        # Normalize to probabilities
        result: Dict[str, Dict[str, float]] = {}
        for from_regime, transitions in counts.items():
            total = sum(transitions.values())
            if total > 0:
                result[from_regime] = {k: v / total for k, v in transitions.items()}
            else:
                result[from_regime] = {k: 0.0 for k in transitions}

        return result
