"""
Tests for darwinia.analytics.population.PopulationAnalyzer.
"""

import copy
import pytest
import numpy as np

from darwinia.core.dna import AgentDNA
from darwinia.analytics.population import PopulationAnalyzer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_population(n: int = 20, seed: int = 42) -> list:
    """Generate a random population for testing."""
    import random
    random.seed(seed)
    pop = []
    for i in range(n):
        agent = AgentDNA.random(generation=0)
        agent.fitness = random.uniform(0.0, 1.0)
        pop.append(agent)
    return pop


def _identical_population(n: int = 10) -> list:
    """Generate a population of identical agents."""
    template = AgentDNA()
    template.fitness = 0.5
    pop = []
    for _ in range(n):
        agent = copy.deepcopy(template)
        pop.append(agent)
    return pop


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGeneStatistics:

    def test_returns_correct_structure(self):
        pop = _random_population(20)
        analyzer = PopulationAnalyzer(pop)
        stats = analyzer.gene_statistics()

        assert isinstance(stats, dict)
        for gene in AgentDNA.GENE_FIELDS:
            assert gene in stats
            assert 'mean' in stats[gene]
            assert 'std' in stats[gene]
            assert 'min' in stats[gene]
            assert 'max' in stats[gene]

    def test_values_in_range(self):
        pop = _random_population(30)
        analyzer = PopulationAnalyzer(pop)
        stats = analyzer.gene_statistics()

        for gene, s in stats.items():
            assert 0.0 <= s['mean'] <= 1.0
            assert s['std'] >= 0.0
            assert s['min'] <= s['mean'] <= s['max']


class TestConvergenceScore:

    def test_range_zero_to_one(self):
        pop = _random_population(50)
        analyzer = PopulationAnalyzer(pop)
        score = analyzer.convergence_score()
        assert 0.0 <= score <= 1.0

    def test_identical_agents_full_convergence(self):
        pop = _identical_population(10)
        analyzer = PopulationAnalyzer(pop)
        score = analyzer.convergence_score()
        assert score == 1.0

    def test_single_agent_full_convergence(self):
        pop = [AgentDNA.random()]
        pop[0].fitness = 0.5
        analyzer = PopulationAnalyzer(pop)
        score = analyzer.convergence_score()
        assert score == 1.0


class TestClusterAgents:

    def test_correct_number_of_clusters(self):
        pop = _random_population(30)
        analyzer = PopulationAnalyzer(pop)
        clusters = analyzer.cluster_agents(n_clusters=3)

        # Should have at most 3 clusters (could be fewer if some are empty)
        assert 1 <= len(clusters) <= 3

    def test_all_agents_assigned(self):
        pop = _random_population(20)
        analyzer = PopulationAnalyzer(pop)
        clusters = analyzer.cluster_agents(n_clusters=3)

        all_ids = set()
        for cluster in clusters:
            all_ids.update(cluster)
        pop_ids = {a.id for a in pop}
        assert all_ids == pop_ids

    def test_single_agent_single_cluster(self):
        pop = [AgentDNA.random()]
        pop[0].fitness = 0.5
        analyzer = PopulationAnalyzer(pop)
        clusters = analyzer.cluster_agents(n_clusters=3)
        assert len(clusters) == 1
        assert len(clusters[0]) == 1


class TestDiversityMetrics:

    def test_structure(self):
        pop = _random_population(20)
        analyzer = PopulationAnalyzer(pop)
        div = analyzer.diversity_metrics()

        assert 'shannon_entropy' in div
        assert 'mean_entropy' in div
        assert 'effective_population_size' in div
        assert isinstance(div['shannon_entropy'], dict)

    def test_uniform_vs_concentrated(self):
        """A random (diverse) population should have higher entropy than
        a population where all agents share near-identical genes."""
        diverse_pop = _random_population(30, seed=7)
        concentrated_pop = _identical_population(30)

        div_diverse = PopulationAnalyzer(diverse_pop).diversity_metrics()
        div_concentrated = PopulationAnalyzer(concentrated_pop).diversity_metrics()

        assert div_diverse['mean_entropy'] > div_concentrated['mean_entropy']


class TestGeneCorrelations:

    def test_structure(self):
        pop = _random_population(30)
        analyzer = PopulationAnalyzer(pop)
        corr = analyzer.gene_correlations()

        assert 'matrix' in corr
        assert 'top_pairs' in corr
        assert isinstance(corr['top_pairs'], list)

    def test_diagonal_is_one(self):
        pop = _random_population(30)
        analyzer = PopulationAnalyzer(pop)
        corr = analyzer.gene_correlations()

        for gene in AgentDNA.GENE_FIELDS:
            assert corr['matrix'][gene][gene] == pytest.approx(1.0, abs=0.01)

    def test_small_population_returns_empty(self):
        pop = _random_population(2)
        analyzer = PopulationAnalyzer(pop)
        corr = analyzer.gene_correlations()
        assert corr['matrix'] == {}
        assert corr['top_pairs'] == []


class TestFitnessDistribution:

    def test_buckets_exist(self):
        pop = _random_population(20)
        analyzer = PopulationAnalyzer(pop)
        fdist = analyzer.fitness_distribution()

        assert 'buckets' in fdist
        assert 'mean' in fdist
        assert 'median' in fdist
        assert 'std' in fdist
        assert len(fdist['buckets']) > 0

    def test_bucket_counts_sum_to_population(self):
        pop = _random_population(25)
        analyzer = PopulationAnalyzer(pop)
        fdist = analyzer.fitness_distribution()

        total = sum(b['count'] for b in fdist['buckets'])
        assert total == len(pop)


class TestEdgeCases:

    def test_single_agent(self):
        agent = AgentDNA.random()
        agent.fitness = 0.42
        analyzer = PopulationAnalyzer([agent])

        result = analyzer.to_dict()
        assert result['population_size'] == 1
        assert result['convergence_score'] == 1.0

    def test_identical_agents(self):
        pop = _identical_population(15)
        analyzer = PopulationAnalyzer(pop)

        assert analyzer.convergence_score() == 1.0
        stats = analyzer.gene_statistics()
        for gene in AgentDNA.GENE_FIELDS:
            assert stats[gene]['std'] == pytest.approx(0.0, abs=1e-12)

    def test_empty_population_raises(self):
        with pytest.raises(ValueError):
            PopulationAnalyzer([])


class TestToDict:

    def test_all_keys_present(self):
        pop = _random_population(20)
        analyzer = PopulationAnalyzer(pop)
        d = analyzer.to_dict()

        expected_keys = {
            'population_size', 'gene_statistics', 'convergence_score',
            'diversity_metrics', 'gene_correlations', 'fitness_distribution',
            'clusters',
        }
        assert expected_keys == set(d.keys())

    def test_json_serializable(self):
        import json
        pop = _random_population(15)
        analyzer = PopulationAnalyzer(pop)
        d = analyzer.to_dict()
        # Should not raise
        serialized = json.dumps(d)
        assert isinstance(serialized, str)
