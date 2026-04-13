"""Tests for the regime detector module."""

import numpy as np
import pandas as pd
import pytest

from darwinia.regime.detector import RegimeDetector, RegimeLabel, RegimeResult, RegimeSegment


@pytest.fixture
def trending_up_data(tmp_path):
    """Strongly trending up data."""
    np.random.seed(42)
    prices = 100 * np.cumprod(1 + 0.003 + np.random.randn(300) * 0.002)
    df = pd.DataFrame({
        'timestamp': np.arange(300),
        'open': prices * 0.999,
        'high': prices * 1.003,
        'low': prices * 0.997,
        'close': prices,
        'volume': np.random.uniform(100, 1000, 300),
    })
    path = tmp_path / 'trend_up.csv'
    df.to_csv(path, index=False)
    return np.loadtxt(path, delimiter=',', skiprows=1)


@pytest.fixture
def volatile_data(tmp_path):
    """Highly volatile data."""
    np.random.seed(99)
    prices = 100 * np.cumprod(1 + np.random.randn(300) * 0.03)
    df = pd.DataFrame({
        'timestamp': np.arange(300),
        'open': prices * 0.99,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.uniform(100, 1000, 300),
    })
    path = tmp_path / 'volatile.csv'
    df.to_csv(path, index=False)
    return np.loadtxt(path, delimiter=',', skiprows=1)


@pytest.fixture
def flat_data(tmp_path):
    """Flat / low volatility data."""
    np.random.seed(7)
    prices = 100 + np.random.randn(300) * 0.1
    prices = np.maximum(prices, 50)
    df = pd.DataFrame({
        'timestamp': np.arange(300),
        'open': prices * 0.9999,
        'high': prices * 1.0001,
        'low': prices * 0.9999,
        'close': prices,
        'volume': np.random.uniform(100, 1000, 300),
    })
    path = tmp_path / 'flat.csv'
    df.to_csv(path, index=False)
    return np.loadtxt(path, delimiter=',', skiprows=1)


class TestRegimeSegment:

    def test_to_dict(self):
        seg = RegimeSegment(
            regime=RegimeLabel.TRENDING_UP, start_idx=0, end_idx=50,
            duration=51, avg_return=0.001, volatility=0.005,
        )
        d = seg.to_dict()
        assert d["regime"] == "trending_up"
        assert d["duration"] == 51


class TestRegimeResult:

    def test_to_dict_keys(self, trending_up_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(trending_up_data)
        d = result.to_dict()
        assert "total_candles" in d
        assert "distribution" in d
        assert "transition_matrix" in d
        assert "segments" in d

    def test_summary_renders(self, trending_up_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(trending_up_data)
        text = result.summary()
        assert "MARKET REGIME ANALYSIS" in text
        assert "Distribution" in text


class TestRegimeDetector:

    def test_labels_length_matches_candles(self, trending_up_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(trending_up_data)
        assert len(result.labels) == len(trending_up_data)

    def test_distribution_sums_to_one(self, trending_up_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(trending_up_data)
        total = sum(result.regime_distribution.values())
        assert abs(total - 1.0) < 1e-9

    def test_segments_cover_all_candles(self, trending_up_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(trending_up_data)
        total_duration = sum(s.duration for s in result.segments)
        assert total_duration == len(trending_up_data)

    def test_trending_data_detects_trend(self, trending_up_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(trending_up_data)
        # Should have trending_up in the distribution
        assert result.regime_distribution.get("trending_up", 0) > 0

    def test_volatile_data_detects_non_flat(self, volatile_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(volatile_data)
        # High-vol random walk should detect non-trivial regimes (mean-revert, high-vol, or trending)
        low_vol = result.regime_distribution.get("low_volatility", 0)
        assert low_vol < 1.0  # not 100% low-volatility

    def test_short_data_no_crash(self):
        """Data shorter than window should still return valid result."""
        candles = np.array([[i, 100, 101, 99, 100, 500] for i in range(5)], dtype=float)
        detector = RegimeDetector(window=20)
        result = detector.detect(candles)
        assert len(result.labels) == 5
        assert len(result.segments) == 1

    def test_transition_matrix_rows_sum_to_one(self, trending_up_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(trending_up_data)
        for from_regime, transitions in result.transition_matrix.items():
            total = sum(transitions.values())
            if total > 0:
                assert abs(total - 1.0) < 1e-9

    def test_custom_thresholds(self, trending_up_data):
        # Very loose thresholds — almost everything classified as low_vol
        detector = RegimeDetector(window=20, trend_threshold=5.0, vol_threshold=5.0)
        result = detector.detect(trending_up_data)
        assert len(result.labels) == len(trending_up_data)

    def test_stability_in_range(self, trending_up_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(trending_up_data)
        assert 0.0 < result.regime_stability <= 1.0

    def test_dominant_regime_exists(self, trending_up_data):
        detector = RegimeDetector(window=20)
        result = detector.detect(trending_up_data)
        assert result.dominant_regime in [r.value for r in RegimeLabel]
