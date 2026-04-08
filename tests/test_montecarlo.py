"""Tests for the Monte Carlo simulation module."""

import numpy as np
import pandas as pd
import pytest
from darwinia.core.dna import AgentDNA
from darwinia.montecarlo.simulator import MonteCarloSimulator, MonteCarloResult


@pytest.fixture
def data_dir(tmp_path):
    np.random.seed(42)
    prices = 100 * np.cumprod(1 + np.random.randn(300) * 0.005)
    df = pd.DataFrame({
        'timestamp': np.arange(300),
        'open': prices * 0.999,
        'high': prices * 1.005,
        'low': prices * 0.995,
        'close': prices,
        'volume': np.random.uniform(100, 1000, 300),
    })
    df.to_csv(tmp_path / 'test.csv', index=False)
    return str(tmp_path)


class TestMonteCarloResult:

    def test_to_dict(self):
        r = MonteCarloResult(
            n_simulations=100, confidence_95=(-0.1, 0.2),
            confidence_99=(-0.15, 0.25), mean_return=0.05,
            median_return=0.04, worst_case=-0.3, best_case=0.5,
            probability_of_profit=0.65, return_distribution=[0.1]*10,
            sharpe_distribution=[1.0]*10,
        )
        d = r.to_dict()
        assert d['n_simulations'] == 100
        assert d['probability_of_profit'] == 0.65
        assert 'return_distribution' not in d

    def test_summary(self):
        r = MonteCarloResult(
            n_simulations=100, confidence_95=(-0.1, 0.2),
            confidence_99=(-0.15, 0.25), mean_return=0.05,
            median_return=0.04, worst_case=-0.3, best_case=0.5,
            probability_of_profit=0.65, return_distribution=[0.1]*10,
            sharpe_distribution=[1.0]*10,
        )
        s = r.summary()
        assert 'Monte Carlo' in s or 'MONTE CARLO' in s or 'simulations' in s.lower()


class TestMonteCarloSimulator:

    def test_bootstrap(self, data_dir):
        sim = MonteCarloSimulator(data_dir=data_dir, n_simulations=20)
        dna = AgentDNA()
        result = sim.run(dna, 'test.csv', method='bootstrap')
        assert isinstance(result, MonteCarloResult)
        assert result.n_simulations == 20
        assert len(result.return_distribution) == 20

    def test_noise(self, data_dir):
        sim = MonteCarloSimulator(data_dir=data_dir, n_simulations=20)
        dna = AgentDNA()
        result = sim.run(dna, 'test.csv', method='noise')
        assert result.n_simulations == 20

    def test_shuffle(self, data_dir):
        sim = MonteCarloSimulator(data_dir=data_dir, n_simulations=20)
        dna = AgentDNA()
        result = sim.run(dna, 'test.csv', method='shuffle')
        assert result.n_simulations == 20

    def test_probability_of_profit_range(self, data_dir):
        sim = MonteCarloSimulator(data_dir=data_dir, n_simulations=50)
        dna = AgentDNA()
        result = sim.run(dna, 'test.csv')
        assert 0 <= result.probability_of_profit <= 1

    def test_confidence_intervals(self, data_dir):
        sim = MonteCarloSimulator(data_dir=data_dir, n_simulations=50)
        dna = AgentDNA()
        result = sim.run(dna, 'test.csv')
        assert result.confidence_95[0] <= result.confidence_95[1]
        assert result.confidence_99[0] <= result.confidence_99[1]
        # 99% CI should be wider than 95%
        assert result.confidence_99[0] <= result.confidence_95[0]
