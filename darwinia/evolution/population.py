"""
Population management — initialization, selection, breeding.
"""

import random
from typing import List
from ..core.dna import AgentDNA


class Population:

    def __init__(self, size: int = 50, seed_ratio: float = 0.2):
        self.size = size
        self.agents: List[AgentDNA] = []
        self.generation = 0
        self._init_population(seed_ratio)

    def _init_population(self, seed_ratio: float):
        """Initialize with a mix of seeded archetypes and random DNA."""
        num_seeds = max(4, int(self.size * seed_ratio))

        seeds = [
            AgentDNA.seed_trend_follower(),
            AgentDNA.seed_mean_reverter(),
            AgentDNA.seed_conservative(),
            AgentDNA.seed_aggressive(),
        ]

        while len(seeds) < num_seeds:
            base = random.choice(seeds[:4])
            seeds.append(base.mutate(mutation_rate=0.3, mutation_strength=0.2))

        randoms = [AgentDNA.random() for _ in range(self.size - len(seeds))]
        self.agents = seeds + randoms

    def select_parents(self, method: str = 'tournament', k: int = 3) -> List[AgentDNA]:
        """Select parents for next generation."""
        if method == 'tournament':
            return self._tournament_select(k)
        elif method == 'elite':
            return self._elite_select()
        else:
            raise ValueError(f"Unknown selection method: {method}")

    def _tournament_select(self, k: int) -> List[AgentDNA]:
        """Tournament selection — pick k random, take the best."""
        parents = []
        num_parents = self.size // 2

        for _ in range(num_parents):
            contestants = random.sample(self.agents, min(k, len(self.agents)))
            winner = max(contestants, key=lambda a: a.fitness)
            parents.append(winner)

        return parents

    def _elite_select(self) -> List[AgentDNA]:
        """Top 20% survive directly."""
        sorted_agents = sorted(self.agents, key=lambda a: a.fitness, reverse=True)
        elite_count = max(2, self.size // 5)
        return sorted_agents[:elite_count]

    def breed_next_generation(self, parents: List[AgentDNA],
                              elite_count: int = 2,
                              mutation_rate: float = 0.15) -> List[AgentDNA]:
        """Create next generation through crossover + mutation."""
        next_gen = []
        self.generation += 1

        # Elite from full population (not just parents) to preserve best
        sorted_all = sorted(self.agents, key=lambda a: a.fitness, reverse=True)
        for elite in sorted_all[:elite_count]:
            elite_copy = AgentDNA.from_dict(elite.to_dict())
            elite_copy.generation = self.generation
            next_gen.append(elite_copy)

        # Guard: need at least 2 parents for crossover
        if len(parents) < 2:
            parents = parents * 2 if parents else sorted_all[:2]

        while len(next_gen) < self.size:
            p1, p2 = random.sample(parents, 2)
            child = p1.crossover(p2)
            child = child.mutate(mutation_rate=mutation_rate)
            child.generation = self.generation
            next_gen.append(child)

        self.agents = next_gen[:self.size]
        return self.agents
