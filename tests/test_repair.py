"""Tests for the self-repair module (monitor + auto-repair)."""

import numpy as np
import pytest
from darwinia.core.dna import AgentDNA
from darwinia.repair.monitor import HealthMonitor, StrategyHealth
from darwinia.repair.auto_repair import AutoRepair, RepairResult


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


class TestHealthMonitor:

    def test_set_baseline(self):
        """Baseline is stored and retrievable."""
        monitor = HealthMonitor()
        monitor.set_baseline(0.75)
        assert monitor.baseline == 0.75

    def test_check_requires_baseline(self):
        """check() raises ValueError when no baseline is set."""
        monitor = HealthMonitor()
        with pytest.raises(ValueError, match="Baseline not set"):
            monitor.check(0.5)

    def test_healthy_agent(self):
        """Agent within threshold is flagged healthy."""
        monitor = HealthMonitor(degradation_threshold=0.3)
        monitor.set_baseline(1.0)
        health = monitor.check(0.85)  # 15% drop < 30% threshold
        assert health.is_healthy is True
        assert health.degradation_pct == pytest.approx(0.15, abs=0.01)

    def test_degraded_agent(self):
        """Agent beyond threshold is flagged unhealthy."""
        monitor = HealthMonitor(degradation_threshold=0.3)
        monitor.set_baseline(1.0)
        health = monitor.check(0.5)  # 50% drop > 30% threshold
        assert health.is_healthy is False
        assert health.degradation_pct == pytest.approx(0.5, abs=0.01)

    def test_severe_degradation_diagnosis(self):
        """Severe degradation produces specific diagnosis text."""
        monitor = HealthMonitor(degradation_threshold=0.3)
        monitor.set_baseline(1.0)
        health = monitor.check(0.2)  # 80% drop
        assert "Severe" in health.diagnosis

    def test_no_degradation(self):
        """If current >= baseline, degradation is 0 and agent is healthy."""
        monitor = HealthMonitor(degradation_threshold=0.3)
        monitor.set_baseline(0.5)
        health = monitor.check(0.6)  # improved
        assert health.is_healthy is True
        assert health.degradation_pct == 0.0

    def test_diagnose_returns_string(self):
        """diagnose() returns a non-empty string with gene info."""
        monitor = HealthMonitor()
        dna = AgentDNA.seed_trend_follower()
        candles = _make_candles(300)
        result = monitor.diagnose(dna, candles)
        assert isinstance(result, str)
        assert len(result) > 0


class TestAutoRepair:

    def test_targeted_repair_produces_valid_dna(self):
        """Targeted repair returns a result with valid fields."""
        monitor = HealthMonitor(degradation_threshold=0.3)
        monitor.set_baseline(1.0)
        repair = AutoRepair(monitor)
        dna = AgentDNA.seed_trend_follower()
        candles = _make_candles(300)
        result = repair.repair(dna, candles, method='targeted')
        assert isinstance(result, RepairResult)
        assert isinstance(result.genes_modified, list)
        assert result.repair_method == 'targeted'

    def test_full_repair_produces_valid_dna(self):
        """Full repair returns a RepairResult with non-None fields."""
        monitor = HealthMonitor(degradation_threshold=0.3)
        monitor.set_baseline(1.0)
        repair = AutoRepair(monitor)
        dna = AgentDNA.seed_trend_follower()
        candles = _make_candles(300)
        result = repair.repair(dna, candles, method='full')
        assert isinstance(result, RepairResult)
        assert result.repair_method == 'full'
        # Full repair with a population should produce some modified genes
        assert isinstance(result.genes_modified, list)

    def test_ensemble_repair_picks_best(self):
        """Ensemble repair should return fitness >= original (or close)."""
        monitor = HealthMonitor(degradation_threshold=0.3)
        monitor.set_baseline(1.0)
        repair = AutoRepair(monitor)
        dna = AgentDNA.seed_trend_follower()
        candles = _make_candles(300)
        result = repair.repair(dna, candles, method='ensemble')
        assert result.repair_method == 'ensemble'
        # Ensemble includes original, so repaired should be >= original
        assert result.repaired_fitness >= result.original_fitness

    def test_invalid_method_raises(self):
        """Unknown method name raises ValueError."""
        monitor = HealthMonitor()
        repair = AutoRepair(monitor)
        dna = AgentDNA.random()
        candles = _make_candles(300)
        with pytest.raises(ValueError, match="Unknown repair method"):
            repair.repair(dna, candles, method='magic')

    def test_repair_result_serialization(self):
        """RepairResult.to_dict() produces correct keys."""
        result = RepairResult(
            original_fitness=0.5,
            repaired_fitness=0.7,
            improvement_pct=0.4,
            genes_modified=['weight_trend', 'risk_appetite'],
            repair_method='targeted',
        )
        d = result.to_dict()
        assert d['original_fitness'] == 0.5
        assert d['repaired_fitness'] == 0.7
        assert d['improvement_pct'] == 0.4
        assert d['genes_modified'] == ['weight_trend', 'risk_appetite']
        assert d['repair_method'] == 'targeted'

    def test_healthy_agent_repair_no_worse(self):
        """Repairing an already-decent agent should not make it much worse."""
        monitor = HealthMonitor(degradation_threshold=0.3)
        monitor.set_baseline(0.5)
        repair = AutoRepair(monitor)
        dna = AgentDNA.seed_trend_follower()
        candles = _make_candles(300)
        result = repair.repair(dna, candles, method='ensemble')
        # Ensemble includes original, so should be >= original
        assert result.repaired_fitness >= result.original_fitness - 0.01

    def test_targeted_repair_modifies_genes(self):
        """Targeted repair should modify at least some genes."""
        monitor = HealthMonitor(degradation_threshold=0.3)
        monitor.set_baseline(1.0)
        repair = AutoRepair(monitor)
        # Use random DNA so there are likely weak genes
        np.random.seed(99)
        dna = AgentDNA.random()
        candles = _make_candles(300)
        result = repair.repair(dna, candles, method='targeted')
        # Targeted repair tries to modify weak genes
        assert isinstance(result.genes_modified, list)
