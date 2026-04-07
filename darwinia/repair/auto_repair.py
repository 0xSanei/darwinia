"""
Auto-Repair — fix degraded trading strategies without full re-evolution.

Three repair methods:
  - targeted: ablation-guided repair of only the weakest genes
  - full: re-evolve from scratch with the original DNA as a seed
  - ensemble: create multiple mutant variants, pick the best
"""

import copy
import random
from dataclasses import dataclass
from typing import List

import numpy as np

from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from ..evolution.fitness import FitnessEvaluator
from ..discovery.explainer import GeneExplainer
from .monitor import HealthMonitor


@dataclass
class RepairResult:
    """Outcome of an auto-repair attempt."""
    original_fitness: float
    repaired_fitness: float
    improvement_pct: float
    genes_modified: List[str]
    repair_method: str

    def to_dict(self) -> dict:
        return {
            'original_fitness': round(self.original_fitness, 4),
            'repaired_fitness': round(self.repaired_fitness, 4),
            'improvement_pct': round(self.improvement_pct, 4),
            'genes_modified': self.genes_modified,
            'repair_method': self.repair_method,
        }


class AutoRepair:
    """
    Automatically repair a degraded trading agent's DNA.

    Uses the HealthMonitor for diagnosis, then applies one of three
    repair strategies to recover fitness.
    """

    def __init__(self, monitor: HealthMonitor) -> None:
        self.monitor = monitor
        self.fitness_eval = FitnessEvaluator()
        self.explainer = GeneExplainer()

    def repair(
        self,
        dna: AgentDNA,
        candles: np.ndarray,
        method: str = 'targeted',
    ) -> RepairResult:
        """
        Repair a degraded agent.

        Args:
            dna: The agent's current (degraded) DNA.
            candles: Market data for fitness evaluation.
            method: One of 'targeted', 'full', or 'ensemble'.

        Returns:
            RepairResult with before/after fitness and details.

        Raises:
            ValueError: If *method* is not recognised.
        """
        original_fitness = self._eval(dna, candles)

        if method == 'targeted':
            repaired_dna = self._targeted_repair(dna, candles)
        elif method == 'full':
            repaired_dna = self._full_repair(dna, candles)
        elif method == 'ensemble':
            repaired_dna = self._ensemble_repair(dna, candles)
        else:
            raise ValueError(f"Unknown repair method: {method!r}. Use 'targeted', 'full', or 'ensemble'.")

        repaired_fitness = self._eval(repaired_dna, candles)

        if original_fitness != 0:
            improvement_pct = (repaired_fitness - original_fitness) / abs(original_fitness)
        else:
            improvement_pct = repaired_fitness

        # Determine which genes changed
        genes_modified = [
            g for g in AgentDNA.GENE_FIELDS
            if getattr(dna, g) != getattr(repaired_dna, g)
        ]

        return RepairResult(
            original_fitness=original_fitness,
            repaired_fitness=repaired_fitness,
            improvement_pct=improvement_pct,
            genes_modified=genes_modified,
            repair_method=method,
        )

    # ------------------------------------------------------------------
    # Repair strategies
    # ------------------------------------------------------------------

    def _targeted_repair(self, dna: AgentDNA, candles: np.ndarray) -> AgentDNA:
        """
        Ablation-guided repair: find the weakest genes and re-randomise them.

        Genes whose removal *improves* fitness are considered harmful.
        Those genes are replaced with random values, then the best
        combination is kept.
        """
        ablations = self.explainer.ablate(dna, candles)

        # Genes where ablating improved fitness (fitness_drop < 0)
        weak_genes = [a.gene_name for a in ablations if a.fitness_drop < 0]
        if not weak_genes:
            # Nothing clearly harmful — perturb bottom-3 importance genes
            weak_genes = [a.gene_name for a in ablations[-3:]]

        best_dna = copy.deepcopy(dna)
        best_fitness = self._eval(best_dna, candles)

        # Try several random replacements for the weak genes
        for _ in range(10):
            candidate = copy.deepcopy(dna)
            for gene in weak_genes:
                setattr(candidate, gene, random.random())
            f = self._eval(candidate, candles)
            if f > best_fitness:
                best_fitness = f
                best_dna = candidate

        return best_dna

    def _full_repair(self, dna: AgentDNA, candles: np.ndarray) -> AgentDNA:
        """
        Re-evolve a small population seeded from the original DNA.

        Creates a micro-population of mutants, evaluates them, selects
        the best, and breeds for a few generations.
        """
        pop_size = 20
        generations = 10

        # Seed population: original + mutants
        population = [copy.deepcopy(dna)]
        for _ in range(pop_size - 1):
            mutant = dna.mutate(mutation_rate=0.4, mutation_strength=0.15)
            population.append(mutant)

        for _gen in range(generations):
            # Evaluate
            for agent in population:
                agent.fitness = self._eval(agent, candles)

            # Sort by fitness (descending)
            population.sort(key=lambda a: a.fitness, reverse=True)

            # Keep top half, breed rest
            half = max(2, pop_size // 2)
            parents = population[:half]
            next_gen = list(parents)

            while len(next_gen) < pop_size:
                p1 = random.choice(parents)
                p2 = random.choice(parents)
                child = p1.crossover(p2).mutate(mutation_rate=0.2, mutation_strength=0.1)
                next_gen.append(child)

            population = next_gen[:pop_size]

        # Final evaluation and pick best
        for agent in population:
            agent.fitness = self._eval(agent, candles)
        return max(population, key=lambda a: a.fitness)

    def _ensemble_repair(self, dna: AgentDNA, candles: np.ndarray) -> AgentDNA:
        """
        Create 3 mutant variants of the DNA, evaluate all, pick the best.
        """
        candidates = [copy.deepcopy(dna)]
        for _ in range(3):
            mutant = dna.mutate(mutation_rate=0.3, mutation_strength=0.12)
            candidates.append(mutant)

        for c in candidates:
            c.fitness = self._eval(c, candles)

        return max(candidates, key=lambda a: a.fitness)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _eval(self, dna: AgentDNA, candles: np.ndarray) -> float:
        """Evaluate agent fitness on the provided candle data."""
        agent = TradingAgent(dna)
        trades = agent.run(candles)
        return self.fitness_eval.evaluate(trades).composite
