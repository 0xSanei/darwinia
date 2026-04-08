"""Tests for the ensemble committee module."""

import numpy as np
import pytest
from darwinia.core.dna import AgentDNA
from darwinia.ensemble.committee import EnsembleAgent, EnsembleResult


def _make_candles(n=300):
    np.random.seed(42)
    prices = 100 * np.cumprod(1 + np.random.randn(n) * 0.005)
    return np.column_stack([
        np.arange(n), prices * 0.999, prices * 1.005,
        prices * 0.995, prices, np.random.uniform(100, 1000, n),
    ])


class TestEnsembleAgent:

    def test_create_ensemble(self):
        members = [AgentDNA() for _ in range(3)]
        ens = EnsembleAgent(members)
        assert len(ens.members) == 3

    def test_run_returns_results(self):
        members = [AgentDNA() for _ in range(3)]
        ens = EnsembleAgent(members)
        candles = _make_candles()
        results = ens.run(candles)
        assert isinstance(results, list)
        assert len(results) == 3

    def test_vote_majority(self):
        members = [AgentDNA() for _ in range(5)]
        ens = EnsembleAgent(members, voting_mode='majority')
        candles = _make_candles()
        window = candles[:50]
        result = ens.vote(window)
        assert isinstance(result, EnsembleResult)
        assert result.final_action in ('buy', 'sell', 'hold')
        assert 0 <= result.consensus_strength <= 1
        assert result.member_count == 5

    def test_vote_weighted(self):
        members = [AgentDNA(fitness=0.8), AgentDNA(fitness=0.2), AgentDNA(fitness=0.5)]
        ens = EnsembleAgent(members, voting_mode='weighted')
        candles = _make_candles()
        result = ens.vote(candles[:50])
        assert result.final_action in ('buy', 'sell', 'hold')

    def test_vote_unanimous(self):
        members = [AgentDNA() for _ in range(3)]
        ens = EnsembleAgent(members, voting_mode='unanimous')
        candles = _make_candles()
        result = ens.vote(candles[:50])
        # Unanimous: if not all agree, should be hold
        assert result.final_action in ('buy', 'sell', 'hold')

    def test_evaluate(self):
        members = [AgentDNA() for _ in range(3)]
        ens = EnsembleAgent(members)
        candles = _make_candles()
        result = ens.evaluate(candles)
        assert 'per_member' in result
        assert 'consensus' in result
        assert 'trades' in result
        assert len(result['per_member']) == 3

    def test_single_member(self):
        ens = EnsembleAgent([AgentDNA()])
        candles = _make_candles()
        result = ens.vote(candles[:50])
        assert result.consensus_strength == 1.0

    def test_different_voting_modes_produce_results(self):
        members = [AgentDNA() for _ in range(5)]
        candles = _make_candles()
        for mode in ['majority', 'weighted', 'unanimous']:
            ens = EnsembleAgent(members, voting_mode=mode)
            result = ens.vote(candles[:50])
            assert result.member_count == 5
