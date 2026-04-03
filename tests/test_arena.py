"""Tests for Adversarial Arena."""

import random
import numpy as np
from darwinia.core.dna import AgentDNA
from darwinia.arena.adversary import AdversaryAgent
from darwinia.arena.arena import AdversarialArena


def test_adversary_generates_valid_candles():
    """Attack scenarios should produce valid OHLCV candles."""
    random.seed(42)
    np.random.seed(42)

    adversary = AdversaryAgent()
    for attack_type in adversary.ATTACK_TEMPLATES:
        scenario = adversary.generate_attack()
        candles = scenario.candles

        assert len(candles) > 0, f"Attack {attack_type} produced empty candles"
        assert candles.shape[1] == 6, "Candles should have 6 columns"
        assert np.all(candles[:, 4] > 0), "Close prices should be positive"


def test_targeted_attack_selection():
    """Targeted attacks should exploit DNA weaknesses."""
    random.seed(42)

    adversary = AdversaryAgent()

    trend_dna = AgentDNA.seed_trend_follower()
    attacks = [adversary._choose_targeted_attack(trend_dna) for _ in range(20)]
    assert 'fake_breakout' in attacks or 'whipsaw' in attacks

    momentum_dna = AgentDNA.seed_aggressive()
    attacks = [adversary._choose_targeted_attack(momentum_dna) for _ in range(20)]
    assert 'pump_and_dump' in attacks or 'rug_pull' in attacks


def test_arena_returns_survival_bonus():
    """Arena should return a float between 0 and 1."""
    random.seed(42)
    np.random.seed(42)

    arena = AdversarialArena({'rounds_per_test': 3})
    dna = AgentDNA.seed_conservative()

    # Dummy normal data
    n = 200
    prices = 100 * np.cumprod(1 + np.random.randn(n) * 0.005)
    normal_data = np.column_stack([
        np.arange(n), prices * 0.999, prices * 1.005,
        prices * 0.995, prices, np.random.uniform(100, 1000, n),
    ])

    bonus = arena.test_agent(dna, normal_data)
    assert 0.0 <= bonus <= 1.0
    assert len(arena.history) == 3


def test_arms_race_data():
    """Arms race data should be structured correctly."""
    random.seed(42)
    np.random.seed(42)

    arena = AdversarialArena({'rounds_per_test': 2})

    n = 200
    prices = 100 * np.cumprod(1 + np.random.randn(n) * 0.005)
    normal_data = np.column_stack([
        np.arange(n), prices * 0.999, prices * 1.005,
        prices * 0.995, prices, np.random.uniform(100, 1000, n),
    ])

    for _ in range(3):
        dna = AgentDNA.random()
        arena.test_agent(dna, normal_data)

    data = arena.get_arms_race_data()
    assert isinstance(data, dict)
