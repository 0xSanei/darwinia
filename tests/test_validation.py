"""Tests for walk-forward validation and gene ablation."""

import numpy as np
import pytest
from darwinia.core.dna import AgentDNA
from darwinia.validation.walk_forward import WalkForwardValidator
from darwinia.discovery.explainer import GeneExplainer


def _make_candles(n=500):
    """Generate synthetic candle data for testing."""
    np.random.seed(42)
    prices = 100 * np.cumprod(1 + np.random.randn(n) * 0.005)
    return np.column_stack([
        np.arange(n),
        prices * 0.999,   # open
        prices * 1.005,   # high
        prices * 0.995,   # low
        prices,            # close
        np.random.uniform(100, 1000, n),  # volume
    ])


class TestWalkForward:

    def test_validator_runs(self):
        candles = _make_candles(1000)
        config = {'population_size': 10, 'seed_ratio': 0.2, 'arena_start_gen': 999}
        validator = WalkForwardValidator(n_windows=2)
        result = validator.validate(candles, config, generations=3)
        assert len(result.windows) == 2
        assert 0 <= result.overfit_score <= 1

    def test_validator_returns_correct_structure(self):
        candles = _make_candles(1000)
        config = {'population_size': 10, 'seed_ratio': 0.2, 'arena_start_gen': 999}
        validator = WalkForwardValidator(n_windows=2)
        result = validator.validate(candles, config, generations=3)
        d = result.to_dict()
        assert 'windows' in d
        assert 'avg_train_fitness' in d
        assert 'overfit_score' in d
        assert 'is_robust' in d

    def test_validator_respects_train_test_split(self):
        candles = _make_candles(1000)
        config = {'population_size': 10, 'seed_ratio': 0.2, 'arena_start_gen': 999}
        validator = WalkForwardValidator(n_windows=2, train_ratio=0.7)
        result = validator.validate(candles, config, generations=3)
        for w in result.windows:
            assert w.train_end == w.test_start  # No gap/overlap


class TestExplainer:

    def test_ablation_runs(self):
        candles = _make_candles(300)
        dna = AgentDNA.seed_trend_follower()
        explainer = GeneExplainer()
        results = explainer.ablate(dna, candles)
        assert len(results) == len(AgentDNA.GENE_FIELDS)

    def test_ablation_importance_normalized(self):
        candles = _make_candles(300)
        dna = AgentDNA.seed_trend_follower()
        explainer = GeneExplainer()
        results = explainer.ablate(dna, candles)
        for r in results:
            assert 0 <= r.importance <= 1.0

    def test_explain_produces_report(self):
        candles = _make_candles(300)
        dna = AgentDNA.seed_trend_follower()
        explainer = GeneExplainer()
        report = explainer.explain(dna, candles)
        assert report.agent_id == dna.id
        assert report.strategy_summary
        assert report.risk_profile in ('Conservative', 'Moderate', 'Aggressive')
        assert len(report.ablations) == 17

    def test_explain_to_dict(self):
        candles = _make_candles(300)
        dna = AgentDNA.seed_aggressive()
        explainer = GeneExplainer()
        report = explainer.explain(dna, candles)
        d = report.to_dict()
        assert 'ablations' in d
        assert 'strategy_summary' in d
        assert 'risk_profile' in d

    def test_compare_multiple_agents(self):
        candles = _make_candles(300)
        agents = [AgentDNA.seed_trend_follower(), AgentDNA.seed_mean_reverter()]
        explainer = GeneExplainer()
        results = explainer.compare(agents, candles)
        assert len(results) == 2
