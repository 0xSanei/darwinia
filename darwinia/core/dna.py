"""
Agent DNA — the genetic code of a trading strategy.

Each gene is a float in [0, 1] range for uniform crossover/mutation.
The TradingAgent interprets DNA genes into actual trading parameters.
"""

import copy
import random
import uuid
from dataclasses import dataclass, field
from typing import ClassVar, List, Dict
from datetime import datetime, timezone


@dataclass
class AgentDNA:
    # === SIGNAL GENES (what the agent pays attention to) ===
    weight_price_momentum: float = 0.5
    weight_volume: float = 0.5
    weight_volatility: float = 0.5
    weight_mean_reversion: float = 0.5
    weight_trend: float = 0.5

    # === THRESHOLD GENES (when the agent acts) ===
    entry_threshold: float = 0.6
    exit_threshold: float = 0.4
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.1

    # === PERSONALITY GENES (how the agent behaves) ===
    risk_appetite: float = 0.5
    time_horizon: float = 0.5
    contrarian_bias: float = 0.5
    patience: float = 0.5
    position_sizing: float = 0.5

    # === ADAPTATION GENES (how the agent learns within lifetime) ===
    regime_sensitivity: float = 0.5
    memory_length: float = 0.5
    noise_filter: float = 0.5

    # === LINEAGE (not genes — metadata) ===
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutation_log: List[str] = field(default_factory=list)
    birth_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fitness: float = 0.0

    # List of gene field names (exclude metadata)
    GENE_FIELDS: ClassVar[List[str]] = [
        'weight_price_momentum', 'weight_volume', 'weight_volatility',
        'weight_mean_reversion', 'weight_trend',
        'entry_threshold', 'exit_threshold', 'stop_loss_pct', 'take_profit_pct',
        'risk_appetite', 'time_horizon', 'contrarian_bias', 'patience',
        'position_sizing', 'regime_sensitivity', 'memory_length', 'noise_filter'
    ]

    def get_genes(self) -> Dict[str, float]:
        """Return only gene values as dict."""
        return {f: getattr(self, f) for f in self.GENE_FIELDS}

    def crossover(self, other: 'AgentDNA') -> 'AgentDNA':
        """Sexual reproduction — uniform crossover."""
        child = AgentDNA()
        child.generation = max(self.generation, other.generation) + 1
        child.parent_ids = [self.id, other.id]

        for gene in self.GENE_FIELDS:
            if random.random() < 0.5:
                setattr(child, gene, getattr(self, gene))
            else:
                setattr(child, gene, getattr(other, gene))

        return child

    def mutate(self, mutation_rate: float = 0.15, mutation_strength: float = 0.1) -> 'AgentDNA':
        """Gaussian mutation on random genes."""
        mutated = copy.deepcopy(self)

        for gene in self.GENE_FIELDS:
            if random.random() < mutation_rate:
                old_val = getattr(mutated, gene)
                delta = random.gauss(0, mutation_strength)
                new_val = max(0.0, min(1.0, old_val + delta))
                setattr(mutated, gene, new_val)
                mutated.mutation_log.append(
                    f"Gen{self.generation}: {gene} {old_val:.3f}->{new_val:.3f}"
                )

        return mutated

    def distance(self, other: 'AgentDNA') -> float:
        """Genetic distance — Euclidean distance in gene space."""
        return sum(
            (getattr(self, g) - getattr(other, g)) ** 2
            for g in self.GENE_FIELDS
        ) ** 0.5

    def to_dict(self) -> dict:
        """Serialize for JSON storage."""
        return {
            'id': self.id,
            'generation': self.generation,
            'genes': self.get_genes(),
            'parent_ids': self.parent_ids,
            'mutation_log': self.mutation_log,
            'fitness': self.fitness,
            'birth_time': self.birth_time,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'AgentDNA':
        """Deserialize from JSON."""
        dna = cls(**d.get('genes', {}))
        dna.id = d['id']
        dna.generation = d['generation']
        dna.parent_ids = d.get('parent_ids', [])
        dna.mutation_log = d.get('mutation_log', [])
        dna.fitness = d.get('fitness', 0.0)
        dna.birth_time = d.get('birth_time', dna.birth_time)
        return dna

    @classmethod
    def random(cls, generation: int = 0) -> 'AgentDNA':
        """Generate a fully random DNA."""
        dna = cls()
        dna.generation = generation
        for gene in cls.GENE_FIELDS:
            setattr(dna, gene, random.random())
        return dna

    @classmethod
    def seed_trend_follower(cls) -> 'AgentDNA':
        """Pre-configured seed: trend following archetype."""
        dna = cls()
        dna.weight_trend = 0.9
        dna.weight_price_momentum = 0.8
        dna.contrarian_bias = 0.1
        dna.patience = 0.7
        dna.time_horizon = 0.7
        dna.risk_appetite = 0.4
        return dna

    @classmethod
    def seed_mean_reverter(cls) -> 'AgentDNA':
        """Pre-configured seed: mean reversion archetype."""
        dna = cls()
        dna.weight_mean_reversion = 0.9
        dna.weight_volatility = 0.7
        dna.contrarian_bias = 0.9
        dna.patience = 0.3
        dna.time_horizon = 0.3
        dna.risk_appetite = 0.5
        return dna

    @classmethod
    def seed_conservative(cls) -> 'AgentDNA':
        """Pre-configured seed: conservative/defensive archetype."""
        dna = cls()
        dna.risk_appetite = 0.1
        dna.stop_loss_pct = 0.2
        dna.position_sizing = 0.2
        dna.noise_filter = 0.9
        dna.patience = 0.9
        return dna

    @classmethod
    def seed_aggressive(cls) -> 'AgentDNA':
        """Pre-configured seed: aggressive/momentum archetype."""
        dna = cls()
        dna.risk_appetite = 0.9
        dna.weight_price_momentum = 0.9
        dna.weight_volume = 0.8
        dna.position_sizing = 0.8
        dna.patience = 0.1
        dna.time_horizon = 0.2
        return dna
