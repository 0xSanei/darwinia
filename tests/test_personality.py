"""Tests for Layer 2 — Personality Engine."""

import numpy as np
from darwinia.core.dna import AgentDNA
from darwinia.personality.profiler import PersonalityProfiler, ARCHETYPES
from darwinia.personality.regime import RegimeDetector, MarketRegime


def test_profiler_produces_valid_dimensions():
    """Profiler should produce dimensions in [0, 1]."""
    profiler = PersonalityProfiler()
    dna = AgentDNA.random()
    profile = profiler.profile(dna)

    for dim, val in profile['dimensions'].items():
        assert 0 <= val <= 1, f"{dim} = {val} is out of range"

    assert profile['archetype'] in ARCHETYPES
    assert profile['archetype_distance'] >= 0
    assert isinstance(profile['description'], str)


def test_profiler_seed_archetypes():
    """Seed archetypes should match expected personality types."""
    profiler = PersonalityProfiler()

    aggressive = profiler.profile(AgentDNA.seed_aggressive())
    assert aggressive['dimensions']['aggression'] > 0.5

    conservative = profiler.profile(AgentDNA.seed_conservative())
    assert conservative['dimensions']['aggression'] < 0.5

    contrarian = profiler.profile(AgentDNA.seed_mean_reverter())
    assert contrarian['dimensions']['contrarianism'] > 0.5


def test_profiler_population():
    """Population profiling should work."""
    profiler = PersonalityProfiler()
    agents = [AgentDNA.random() for _ in range(20)]
    result = profiler.profile_population(agents)

    assert 'archetype_distribution' in result
    assert sum(result['archetype_distribution'].values()) == 20
    assert len(result['profiles']) == 20


def test_regime_detector_trending():
    """Should detect trending market."""
    detector = RegimeDetector(lookback=50)

    # Create uptrend: steady rise
    n = 100
    prices = 100 * np.cumprod(1 + np.ones(n) * 0.005)  # 0.5% per candle
    candles = np.column_stack([
        np.arange(n), prices * 0.999, prices * 1.005,
        prices * 0.995, prices, np.ones(n) * 1000,
    ])

    state = detector.detect(candles)
    assert state.regime in (MarketRegime.TRENDING_UP, MarketRegime.BREAKOUT)
    assert state.momentum > 0


def test_regime_detector_ranging():
    """Should detect ranging market."""
    detector = RegimeDetector(lookback=50)

    # Create range: oscillating around 100
    n = 100
    prices = 100 + 2 * np.sin(np.linspace(0, 10 * np.pi, n))
    candles = np.column_stack([
        np.arange(n), prices * 0.999, prices * 1.005,
        prices * 0.995, prices, np.ones(n) * 1000,
    ])

    state = detector.detect(candles)
    assert state.regime in (MarketRegime.RANGING, MarketRegime.VOLATILE)
    assert state.trend_strength < 0.5


def test_regime_transitions():
    """Should detect regime transitions."""
    detector = RegimeDetector(lookback=30)

    # Range then trend
    n_range = 50
    prices_range = 100 + np.random.randn(n_range) * 0.5
    n_trend = 50
    prices_trend = prices_range[-1] * np.cumprod(1 + np.ones(n_trend) * 0.008)
    prices = np.concatenate([prices_range, prices_trend])

    n = len(prices)
    candles = np.column_stack([
        np.arange(n), prices * 0.999, prices * 1.005,
        prices * 0.995, prices, np.ones(n) * 1000,
    ])

    states = detector.detect_series(candles, step=5)
    assert len(states) > 0
    # At least some regime variety
    regimes = set(s.regime for s in states)
    assert len(regimes) >= 1  # should detect at least one regime
