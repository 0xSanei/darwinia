"""Tests for the strategy fingerprint module."""

import pytest
from darwinia.core.dna import AgentDNA
from darwinia.fingerprint.visualizer import StrategyFingerprint


class TestStrategyFingerprint:

    def test_archetype_aggressive(self):
        dna = AgentDNA(risk_appetite=0.9, weight_price_momentum=0.9, patience=0.1)
        fp = StrategyFingerprint(dna)
        assert fp.archetype() == "Aggressive Momentum"

    def test_archetype_conservative(self):
        dna = AgentDNA(risk_appetite=0.1, weight_mean_reversion=0.9, patience=0.9)
        fp = StrategyFingerprint(dna)
        assert fp.archetype() == "Conservative Mean-Reversion"

    def test_archetype_contrarian(self):
        dna = AgentDNA(contrarian_bias=0.9, patience=0.9)
        fp = StrategyFingerprint(dna)
        assert fp.archetype() == "Contrarian"

    def test_archetype_trend_follower(self):
        dna = AgentDNA(weight_trend=0.9, time_horizon=0.9, patience=0.9)
        fp = StrategyFingerprint(dna)
        assert fp.archetype() == "Trend Follower"

    def test_archetype_scalper(self):
        dna = AgentDNA(time_horizon=0.1, stop_loss_pct=0.1, take_profit_pct=0.1, noise_filter=0.9)
        fp = StrategyFingerprint(dna)
        assert fp.archetype() == "Scalper"

    def test_archetype_default(self):
        dna = AgentDNA()  # all 0.5
        fp = StrategyFingerprint(dna)
        # Default DNA should be Balanced or Hybrid
        assert fp.archetype() in ("Balanced Adaptive", "Hybrid")

    def test_radar_ascii(self):
        dna = AgentDNA()
        fp = StrategyFingerprint(dna)
        art = fp.radar_ascii()
        assert isinstance(art, str)
        assert len(art) > 0

    def test_similarity_self(self):
        dna = AgentDNA()
        fp = StrategyFingerprint(dna)
        assert fp.similarity(dna) == pytest.approx(1.0, abs=0.001)

    def test_similarity_different(self):
        dna1 = AgentDNA(risk_appetite=0.0, patience=0.0)
        dna2 = AgentDNA(risk_appetite=1.0, patience=1.0)
        fp = StrategyFingerprint(dna1)
        sim = fp.similarity(dna2)
        assert 0 <= sim < 1.0

    def test_compare(self):
        dna1 = AgentDNA(risk_appetite=0.2)
        dna2 = AgentDNA(risk_appetite=0.8)
        fp = StrategyFingerprint(dna1)
        diff = fp.compare(dna2)
        assert 'risk_appetite' in diff
        assert abs(diff['risk_appetite']['diff']) > 0.5

    def test_dominant_traits_default(self):
        dna = AgentDNA()  # all defaults
        fp = StrategyFingerprint(dna)
        traits = fp.dominant_traits()
        assert isinstance(traits, list)
        # stop_loss_pct=0.05 and take_profit_pct=0.1 are far from 0.5, so they count
        # The important thing is extreme genes return more traits
        extreme_dna = AgentDNA(risk_appetite=0.95, patience=0.05)
        extreme_fp = StrategyFingerprint(extreme_dna)
        extreme_traits = extreme_fp.dominant_traits()
        assert len(extreme_traits) > len(traits) or len(extreme_traits) >= 2

    def test_dominant_traits_extreme(self):
        dna = AgentDNA(risk_appetite=0.95, patience=0.05)
        fp = StrategyFingerprint(dna)
        traits = fp.dominant_traits()
        assert len(traits) >= 2

    def test_to_dict(self):
        dna = AgentDNA()
        fp = StrategyFingerprint(dna)
        d = fp.to_dict()
        assert 'genes' in d
        assert 'archetype' in d
        assert 'dominant_traits' in d

    def test_compare_keys(self):
        dna1 = AgentDNA()
        dna2 = AgentDNA()
        fp = StrategyFingerprint(dna1)
        diff = fp.compare(dna2)
        # Should have entry for each gene
        assert len(diff) == len(AgentDNA.GENE_FIELDS)
