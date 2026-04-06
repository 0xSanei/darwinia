"""Tests for macro regime awareness module."""

import numpy as np
from darwinia.macro.regime import (
    MacroRegime,
    MacroSignal,
    MacroSimulator,
    MacroAwareFitness,
    LiquidityTrend,
    VolatilityLevel,
)


def test_regime_sequence_length():
    """Generated sequence should have exactly n_days entries."""
    sim = MacroSimulator(seed=42)
    for n in [1, 10, 100, 365]:
        seq = sim.generate_regime_sequence(n)
        assert len(seq) == n, f"Expected {n} signals, got {len(seq)}"


def test_regime_sequence_valid_types():
    """Every signal should have valid enum values."""
    sim = MacroSimulator(seed=7)
    seq = sim.generate_regime_sequence(200)
    for sig in seq:
        assert isinstance(sig.regime, MacroRegime)
        assert isinstance(sig.fed_liquidity_trend, LiquidityTrend)
        assert isinstance(sig.volatility_level, VolatilityLevel)
        assert isinstance(sig.timestamp, int)


def test_regime_transitions_are_gradual():
    """RISK_ON should not jump directly to RISK_OFF without TRANSITION."""
    sim = MacroSimulator(seed=123)
    seq = sim.generate_regime_sequence(500)
    for i in range(1, len(seq)):
        prev = seq[i - 1].regime
        curr = seq[i].regime
        if prev == MacroRegime.RISK_ON and curr != MacroRegime.RISK_ON:
            assert curr == MacroRegime.TRANSITION, (
                f"Day {i}: jumped from RISK_ON to {curr} without TRANSITION"
            )
        if prev == MacroRegime.RISK_OFF and curr != MacroRegime.RISK_OFF:
            assert curr == MacroRegime.TRANSITION, (
                f"Day {i}: jumped from RISK_OFF to {curr} without TRANSITION"
            )


def test_risk_off_penalty():
    """Agent with full position in RISK_OFF should score lower than cautious agent."""
    sim = MacroSimulator(seed=10)
    seq = sim.generate_regime_sequence(100)
    fitness = MacroAwareFitness()

    # Aggressive agent: always full position
    aggressive = [1.0] * len(seq)
    # Cautious agent: no position in RISK_OFF, full in RISK_ON, half in TRANSITION
    cautious = []
    for sig in seq:
        if sig.regime == MacroRegime.RISK_ON:
            cautious.append(1.0)
        elif sig.regime == MacroRegime.RISK_OFF:
            cautious.append(0.0)
        else:
            cautious.append(0.5)

    score_aggressive = fitness.evaluate(aggressive, seq, base_fitness=0.5)
    score_cautious = fitness.evaluate(cautious, seq, base_fitness=0.5)
    assert score_cautious > score_aggressive, (
        f"Cautious ({score_cautious:.4f}) should beat aggressive ({score_aggressive:.4f})"
    )


def test_risk_on_reward():
    """Agent with higher position in RISK_ON should score better."""
    # Create a pure RISK_ON sequence
    signals = [
        MacroSignal(MacroRegime.RISK_ON, LiquidityTrend.UP, VolatilityLevel.LOW, i)
        for i in range(50)
    ]
    fitness = MacroAwareFitness()

    full_pos = [1.0] * 50
    zero_pos = [0.0] * 50

    score_full = fitness.evaluate(full_pos, signals, base_fitness=0.0)
    score_zero = fitness.evaluate(zero_pos, signals, base_fitness=0.0)
    assert score_full > score_zero


def test_all_weather_beats_regime_blind():
    """An all-weather adaptive agent should score higher than a regime-blind one."""
    sim = MacroSimulator(seed=99)
    seq = sim.generate_regime_sequence(300)
    fitness = MacroAwareFitness()

    # Regime-blind: constant 0.5 position
    blind_decisions = [0.5] * len(seq)

    # All-weather: adapts to regime
    adaptive_decisions = []
    for sig in seq:
        if sig.regime == MacroRegime.RISK_ON:
            adaptive_decisions.append(0.9)
        elif sig.regime == MacroRegime.RISK_OFF:
            adaptive_decisions.append(0.1)
        else:
            adaptive_decisions.append(0.5)

    score_blind = fitness.evaluate(blind_decisions, seq, base_fitness=0.5)
    score_adaptive = fitness.evaluate(adaptive_decisions, seq, base_fitness=0.5)
    assert score_adaptive > score_blind, (
        f"Adaptive ({score_adaptive:.4f}) should beat blind ({score_blind:.4f})"
    )


def test_single_day():
    """Edge case: single day sequence should work without errors."""
    sim = MacroSimulator(seed=1)
    seq = sim.generate_regime_sequence(1)
    assert len(seq) == 1

    fitness = MacroAwareFitness()
    score = fitness.evaluate([0.5], seq, base_fitness=1.0)
    assert isinstance(score, float)


def test_all_same_regime():
    """Edge case: sequence where the regime never changes."""
    signals = [
        MacroSignal(MacroRegime.RISK_OFF, LiquidityTrend.DOWN, VolatilityLevel.HIGH, i)
        for i in range(100)
    ]
    fitness = MacroAwareFitness()

    # Low position should be rewarded in pure RISK_OFF
    score_low = fitness.evaluate([0.1] * 100, signals, base_fitness=0.0)
    score_high = fitness.evaluate([0.9] * 100, signals, base_fitness=0.0)
    assert score_low > score_high


def test_empty_sequence():
    """Edge case: empty sequence returns base_fitness unchanged."""
    fitness = MacroAwareFitness()
    score = fitness.evaluate([], [], base_fitness=0.42)
    assert score == 0.42


def test_mismatched_lengths_raises():
    """Mismatched decision/signal lengths should raise ValueError."""
    signals = [
        MacroSignal(MacroRegime.RISK_ON, LiquidityTrend.UP, VolatilityLevel.LOW, 0)
    ]
    fitness = MacroAwareFitness()
    try:
        fitness.evaluate([0.5, 0.5], signals)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
