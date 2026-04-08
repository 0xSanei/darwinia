"""Tests for the benchmark baselines module."""

import numpy as np
import pandas as pd
import pytest
from darwinia.core.dna import AgentDNA
from darwinia.benchmark.baselines import BenchmarkSuite, BenchmarkResult


@pytest.fixture
def data_dir(tmp_path):
    np.random.seed(42)
    prices = 100 * np.cumprod(1 + np.random.randn(500) * 0.005)
    df = pd.DataFrame({
        'timestamp': np.arange(500),
        'open': prices * 0.999,
        'high': prices * 1.005,
        'low': prices * 0.995,
        'close': prices,
        'volume': np.random.uniform(100, 1000, 500),
    })
    df.to_csv(tmp_path / 'test.csv', index=False)
    return str(tmp_path)


class TestBenchmarkResult:

    def test_to_dict(self):
        r = BenchmarkResult(
            strategy_name='test', total_return=100, total_return_pct=0.1,
            sharpe_ratio=1.5, max_drawdown_pct=0.05, win_rate=0.6, num_trades=10,
        )
        d = r.to_dict()
        assert d['strategy_name'] == 'test'
        assert d['sharpe_ratio'] == 1.5


class TestBenchmarkSuite:

    def test_run_returns_all_baselines(self, data_dir):
        suite = BenchmarkSuite(data_dir=data_dir)
        dna = AgentDNA()
        result = suite.run(dna, 'test.csv')
        assert 'evolved' in result
        assert 'baselines' in result
        assert 'ranking' in result
        assert isinstance(result['evolved'], BenchmarkResult)
        # Should have 5 baselines
        assert len(result['baselines']) == 5

    def test_baselines_are_named(self, data_dir):
        suite = BenchmarkSuite(data_dir=data_dir)
        dna = AgentDNA()
        result = suite.run(dna, 'test.csv')
        names = {b.strategy_name for b in result['baselines']}
        expected = {'buy_and_hold', 'random_trader', 'mean_reversion', 'momentum', 'dca'}
        assert names == expected

    def test_ranking_sorted_by_sharpe(self, data_dir):
        suite = BenchmarkSuite(data_dir=data_dir)
        dna = AgentDNA()
        result = suite.run(dna, 'test.csv')
        sharpes = [r.sharpe_ratio for r in result['ranking']]
        assert sharpes == sorted(sharpes, reverse=True)

    def test_buy_and_hold_single_trade(self, data_dir):
        suite = BenchmarkSuite(data_dir=data_dir)
        dna = AgentDNA()
        result = suite.run(dna, 'test.csv')
        bah = next(b for b in result['baselines'] if b.strategy_name == 'buy_and_hold')
        assert bah.num_trades >= 1

    def test_evolved_in_ranking(self, data_dir):
        suite = BenchmarkSuite(data_dir=data_dir)
        dna = AgentDNA()
        result = suite.run(dna, 'test.csv')
        names = [r.strategy_name for r in result['ranking']]
        assert 'evolved' in names

    def test_all_results_have_fields(self, data_dir):
        suite = BenchmarkSuite(data_dir=data_dir)
        dna = AgentDNA()
        result = suite.run(dna, 'test.csv')
        for r in result['ranking']:
            assert hasattr(r, 'total_return')
            assert hasattr(r, 'sharpe_ratio')
            assert hasattr(r, 'win_rate')
