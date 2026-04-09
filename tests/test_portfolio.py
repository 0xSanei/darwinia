"""Tests for the portfolio allocator module."""

import numpy as np
import pandas as pd
import pytest

from darwinia.core.dna import AgentDNA
from darwinia.portfolio.allocator import PortfolioAllocator, AllocationResult


@pytest.fixture
def data_dir(tmp_path):
    np.random.seed(7)
    prices = 100 * np.cumprod(1 + np.random.randn(400) * 0.006)
    df = pd.DataFrame({
        'timestamp': np.arange(400),
        'open': prices * 0.999,
        'high': prices * 1.004,
        'low': prices * 0.996,
        'close': prices,
        'volume': np.random.uniform(100, 1000, 400),
    })
    df.to_csv(tmp_path / 'test.csv', index=False)
    return str(tmp_path)


@pytest.fixture
def members():
    np.random.seed(11)
    return [AgentDNA().mutate(mutation_rate=0.6, mutation_strength=0.3) for _ in range(4)]


class TestAllocationResult:

    def test_to_dict_roundtrip(self):
        r = AllocationResult(
            method="risk_parity",
            weights={"a": 0.3, "b": 0.7},
            expected_return=0.12,
            portfolio_volatility=0.04,
            portfolio_sharpe=3.0,
            diversification_ratio=1.2,
        )
        d = r.to_dict()
        assert d["method"] == "risk_parity"
        assert d["weights"]["a"] == 0.3
        assert d["weights"]["b"] == 0.7
        assert d["portfolio_sharpe"] == 3.0

    def test_summary_renders(self):
        r = AllocationResult(
            method="equal_weight",
            weights={"x": 0.5, "y": 0.5},
            expected_return=0.05,
            portfolio_volatility=0.02,
            portfolio_sharpe=2.5,
            diversification_ratio=1.1,
        )
        text = r.summary()
        assert "PORTFOLIO ALLOCATION" in text
        assert "equal_weight" in text
        assert "x" in text and "y" in text


class TestPortfolioAllocator:

    def test_invalid_method_raises(self, members, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        with pytest.raises(ValueError, match="Unknown method"):
            alloc.allocate(members, 'test.csv', method='garbage')

    def test_empty_members_raises(self, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        with pytest.raises(ValueError, match="at least one"):
            alloc.allocate([], 'test.csv')

    def test_equal_weight_sums_to_one(self, members, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        result = alloc.allocate(members, 'test.csv', method='equal_weight')
        weights = list(result.weights.values())
        assert abs(sum(weights) - 1.0) < 1e-9
        # all members get the same weight
        assert max(weights) - min(weights) < 1e-9

    def test_risk_parity_sums_to_one(self, members, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        result = alloc.allocate(members, 'test.csv', method='risk_parity')
        weights = list(result.weights.values())
        assert abs(sum(weights) - 1.0) < 1e-9
        assert all(w >= 0 for w in weights)

    def test_inverse_variance_sums_to_one(self, members, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        result = alloc.allocate(members, 'test.csv', method='inverse_variance')
        assert abs(sum(result.weights.values()) - 1.0) < 1e-9

    def test_kelly_sums_to_one(self, members, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        result = alloc.allocate(members, 'test.csv', method='kelly')
        assert abs(sum(result.weights.values()) - 1.0) < 1e-9
        assert all(w >= 0 for w in result.weights.values())

    def test_sharpe_weighted_sums_to_one(self, members, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        result = alloc.allocate(members, 'test.csv', method='sharpe_weighted')
        assert abs(sum(result.weights.values()) - 1.0) < 1e-9

    def test_member_metrics_populated(self, members, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        result = alloc.allocate(members, 'test.csv', method='risk_parity')
        assert len(result.member_metrics) == len(members)
        for m in result.member_metrics:
            assert 'agent_id' in m
            assert 'sharpe_ratio' in m
            assert 'num_trades' in m

    def test_diversification_ratio_at_least_one(self, members, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        result = alloc.allocate(members, 'test.csv', method='risk_parity')
        # Diversification ratio is >=1 by construction (Cauchy-Schwarz)
        # Allow small numerical slack.
        assert result.diversification_ratio >= 0.99

    def test_single_member_full_weight(self, members, data_dir):
        alloc = PortfolioAllocator(data_dir=data_dir)
        result = alloc.allocate([members[0]], 'test.csv', method='risk_parity')
        assert len(result.weights) == 1
        assert abs(list(result.weights.values())[0] - 1.0) < 1e-9

    def test_to_dict_serializable(self, members, data_dir):
        import json
        alloc = PortfolioAllocator(data_dir=data_dir)
        result = alloc.allocate(members, 'test.csv', method='equal_weight')
        # Should JSON-serialize without error
        json.dumps(result.to_dict())

    def test_kelly_fraction_respected(self, members, data_dir):
        alloc_full = PortfolioAllocator(data_dir=data_dir, kelly_fraction=1.0)
        alloc_half = PortfolioAllocator(data_dir=data_dir, kelly_fraction=0.5)
        # Both must produce valid normalized weights
        r1 = alloc_full.allocate(members, 'test.csv', method='kelly')
        r2 = alloc_half.allocate(members, 'test.csv', method='kelly')
        assert abs(sum(r1.weights.values()) - 1.0) < 1e-9
        assert abs(sum(r2.weights.values()) - 1.0) < 1e-9
