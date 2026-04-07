"""
Strategy Health Monitor — detect when an evolved agent's performance degrades.

Compares current fitness against a stored baseline. When degradation exceeds
a threshold, the monitor flags the strategy as unhealthy and provides a
gene-level diagnosis using ablation analysis.
"""

import copy
from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..core.dna import AgentDNA
from ..discovery.explainer import GeneExplainer


@dataclass
class StrategyHealth:
    """Health check result for an evolved trading strategy."""
    fitness_current: float
    fitness_baseline: float
    degradation_pct: float
    is_healthy: bool
    diagnosis: str


class HealthMonitor:
    """
    Monitors an evolved agent's fitness over time and detects degradation.

    When current fitness drops more than ``degradation_threshold`` (as a
    fraction of the baseline), the strategy is considered unhealthy.
    """

    def __init__(self, degradation_threshold: float = 0.3) -> None:
        """
        Args:
            degradation_threshold: Fraction of baseline fitness drop that
                triggers a repair.  0.3 means >30% drop = unhealthy.
        """
        self.degradation_threshold = degradation_threshold
        self._baseline: Optional[float] = None

    def set_baseline(self, fitness: float) -> None:
        """Record the 'healthy' fitness level after initial evolution."""
        self._baseline = fitness

    @property
    def baseline(self) -> Optional[float]:
        return self._baseline

    def check(self, current_fitness: float) -> StrategyHealth:
        """
        Compare *current_fitness* against the stored baseline.

        Returns:
            StrategyHealth with degradation percentage and healthy flag.

        Raises:
            ValueError: If no baseline has been set yet.
        """
        if self._baseline is None:
            raise ValueError("Baseline not set. Call set_baseline() first.")

        if self._baseline == 0:
            degradation_pct = 0.0 if current_fitness >= 0 else 1.0
        else:
            degradation_pct = max(0.0, (self._baseline - current_fitness) / abs(self._baseline))

        is_healthy = degradation_pct <= self.degradation_threshold

        if is_healthy:
            diagnosis = "Strategy operating within normal parameters."
        elif degradation_pct > 0.6:
            diagnosis = "Severe degradation detected. Full re-evolution recommended."
        else:
            diagnosis = "Moderate degradation detected. Targeted repair recommended."

        return StrategyHealth(
            fitness_current=current_fitness,
            fitness_baseline=self._baseline,
            degradation_pct=degradation_pct,
            is_healthy=is_healthy,
            diagnosis=diagnosis,
        )

    def diagnose(self, dna: AgentDNA, candles: np.ndarray) -> str:
        """
        Identify which genes degraded most via ablation analysis.

        Uses GeneExplainer to rank genes by importance, then reports
        which ones contribute least (potential weak points).

        Args:
            dna: The agent's current DNA.
            candles: Recent market data for evaluation.

        Returns:
            Human-readable diagnosis string listing weak genes.
        """
        explainer = GeneExplainer()
        result = explainer.explain(dna, candles)

        # Genes with negative fitness_drop when ablated = removing them helps
        weak_genes = [
            a.gene_name for a in result.ablations
            if a.fitness_drop < 0
        ]
        # Also note genes with near-zero importance
        inert_genes = [
            a.gene_name for a in result.ablations
            if abs(a.fitness_drop) < 0.001 and a.gene_name not in weak_genes
        ]

        parts = []
        if weak_genes:
            parts.append(f"Harmful genes (removing improves fitness): {', '.join(weak_genes[:5])}")
        if inert_genes:
            parts.append(f"Inert genes (no measurable effect): {', '.join(inert_genes[:5])}")
        if result.top_genes:
            parts.append(f"Core genes (most important): {', '.join(result.top_genes[:5])}")

        return " | ".join(parts) if parts else "No clear gene-level issues identified."
