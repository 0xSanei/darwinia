"""Tests for AgentDNA."""

import random
from darwinia.core.dna import AgentDNA


def test_random_dna_genes_in_range():
    """All genes should be in [0, 1]."""
    random.seed(42)
    dna = AgentDNA.random()
    for gene in AgentDNA.GENE_FIELDS:
        val = getattr(dna, gene)
        assert 0.0 <= val <= 1.0, f"{gene} = {val} out of range"


def test_crossover_produces_valid_child():
    """Crossover should produce a child with valid genes and correct lineage."""
    random.seed(42)
    p1 = AgentDNA.random(generation=3)
    p2 = AgentDNA.random(generation=5)
    child = p1.crossover(p2)

    assert child.generation == 6  # max(3, 5) + 1
    assert p1.id in child.parent_ids
    assert p2.id in child.parent_ids

    for gene in AgentDNA.GENE_FIELDS:
        val = getattr(child, gene)
        assert 0.0 <= val <= 1.0


def test_mutation_stays_in_range():
    """Mutation should keep all genes in [0, 1]."""
    random.seed(42)
    dna = AgentDNA.random()
    mutated = dna.mutate(mutation_rate=1.0, mutation_strength=0.5)

    for gene in AgentDNA.GENE_FIELDS:
        val = getattr(mutated, gene)
        assert 0.0 <= val <= 1.0, f"{gene} = {val} out of range after mutation"


def test_mutation_logs_changes():
    """High mutation rate should produce mutation log entries."""
    random.seed(42)
    dna = AgentDNA.random()
    mutated = dna.mutate(mutation_rate=1.0, mutation_strength=0.1)
    assert len(mutated.mutation_log) > 0


def test_seed_archetypes():
    """Seed archetypes should have expected dominant traits."""
    trend = AgentDNA.seed_trend_follower()
    assert trend.weight_trend > 0.8
    assert trend.contrarian_bias < 0.2

    mean_rev = AgentDNA.seed_mean_reverter()
    assert mean_rev.weight_mean_reversion > 0.8
    assert mean_rev.contrarian_bias > 0.8

    conservative = AgentDNA.seed_conservative()
    assert conservative.risk_appetite < 0.2
    assert conservative.noise_filter > 0.8

    aggressive = AgentDNA.seed_aggressive()
    assert aggressive.risk_appetite > 0.8
    assert aggressive.position_sizing > 0.7


def test_serialization_roundtrip():
    """to_dict -> from_dict should preserve all data."""
    random.seed(42)
    dna = AgentDNA.random(generation=5)
    dna.fitness = 0.75
    dna.parent_ids = ['abc', 'def']

    d = dna.to_dict()
    restored = AgentDNA.from_dict(d)

    assert restored.id == dna.id
    assert restored.generation == dna.generation
    assert restored.fitness == dna.fitness
    assert restored.parent_ids == dna.parent_ids

    for gene in AgentDNA.GENE_FIELDS:
        assert abs(getattr(restored, gene) - getattr(dna, gene)) < 1e-10


def test_distance():
    """Identical DNA should have distance 0, different DNA > 0."""
    dna1 = AgentDNA()
    dna2 = AgentDNA()
    assert dna1.distance(dna2) == 0.0

    dna3 = AgentDNA.random()
    assert dna1.distance(dna3) > 0.0
