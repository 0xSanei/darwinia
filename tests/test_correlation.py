"""Tests for the correlation matrix module."""

import numpy as np
import pandas as pd
import pytest

from darwinia.core.dna import AgentDNA
from darwinia.correlation.matrix import CorrelationAnalyzer, CorrelationResult


@pytest.fixture
def data_dir(tmp_path):
    np.random.seed(42)
    prices = 100 * np.cumprod(1 + np.random.randn(400) * 0.005)
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
    np.random.seed(55)
    return [AgentDNA().mutate(mutation_rate=0.5, mutation_strength=0.3) for _ in range(4)]


class TestCorrelationResult:

    def test_to_dict_keys(self):
        matrix = np.eye(2)
        result = CorrelationResult(
            matrix=matrix, agent_ids=["a", "b"],
            avg_correlation=0.5,
            max_pair=("a", "b", 0.8),
            min_pair=("a", "b", 0.2),
            cluster_groups=[["a", "b"]],
            member_stats=[],
        )
        d = result.to_dict()
        assert "matrix" in d
        assert "avg_correlation" in d
        assert "max_pair" in d
        assert "cluster_groups" in d

    def test_summary_renders(self):
        matrix = np.array([[1.0, 0.5], [0.5, 1.0]])
        result = CorrelationResult(
            matrix=matrix, agent_ids=["abc", "xyz"],
            avg_correlation=0.5,
            max_pair=("abc", "xyz", 0.5),
            min_pair=("abc", "xyz", 0.5),
            cluster_groups=[["abc", "xyz"]],
            member_stats=[],
        )
        text = result.summary()
        assert "CORRELATION ANALYSIS" in text
        assert "abc" in text


class TestCorrelationAnalyzer:

    def test_less_than_2_raises(self, data_dir):
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        with pytest.raises(ValueError, match="at least 2"):
            analyzer.analyze([AgentDNA()], 'test.csv')

    def test_matrix_shape(self, members, data_dir):
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        result = analyzer.analyze(members, 'test.csv')
        n = len(members)
        assert result.matrix.shape == (n, n)

    def test_diagonal_is_one(self, members, data_dir):
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        result = analyzer.analyze(members, 'test.csv')
        for i in range(len(members)):
            assert abs(result.matrix[i, i] - 1.0) < 1e-9

    def test_matrix_symmetric(self, members, data_dir):
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        result = analyzer.analyze(members, 'test.csv')
        np.testing.assert_array_almost_equal(result.matrix, result.matrix.T)

    def test_correlations_in_range(self, members, data_dir):
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        result = analyzer.analyze(members, 'test.csv')
        assert np.all(result.matrix >= -1.0 - 1e-9)
        assert np.all(result.matrix <= 1.0 + 1e-9)

    def test_agent_ids_match(self, members, data_dir):
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        result = analyzer.analyze(members, 'test.csv')
        assert len(result.agent_ids) == len(members)
        for m, aid in zip(members, result.agent_ids):
            assert aid == m.id

    def test_cluster_groups_cover_all(self, members, data_dir):
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        result = analyzer.analyze(members, 'test.csv')
        all_ids = [aid for group in result.cluster_groups for aid in group]
        assert set(all_ids) == set(result.agent_ids)

    def test_member_stats_populated(self, members, data_dir):
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        result = analyzer.analyze(members, 'test.csv')
        assert len(result.member_stats) == len(members)
        for stat in result.member_stats:
            assert 'agent_id' in stat
            assert 'num_trades' in stat

    def test_to_dict_serializable(self, members, data_dir):
        import json
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        result = analyzer.analyze(members, 'test.csv')
        json.dumps(result.to_dict())

    def test_identical_strategies_high_correlation(self, data_dir):
        """Two identical DNAs should have correlation = 1."""
        dna = AgentDNA()
        dna2 = AgentDNA()
        dna2.id = "clone"
        # Copy all genes
        for gene in AgentDNA.GENE_FIELDS:
            setattr(dna2, gene, getattr(dna, gene))
        analyzer = CorrelationAnalyzer(data_dir=data_dir)
        result = analyzer.analyze([dna, dna2], 'test.csv')
        # Identical strategies produce identical trades → corr should be 1
        assert result.matrix[0, 1] >= 0.99
