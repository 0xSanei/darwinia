"""
Evolution Engine — orchestrates the full evolutionary loop.

Each generation:
1. Evaluate all agents on market data
2. (Optional) Run adversarial arena rounds
3. Compute fitness
4. Select parents
5. Breed next generation
6. Record chronicle
"""

import numpy as np
from typing import Optional, Callable
from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from .population import Population
from .fitness import FitnessEvaluator


class EvolutionEngine:

    def __init__(self, config: dict):
        self.config = config
        self.population = Population(
            size=config.get('population_size', 50),
            seed_ratio=config.get('seed_ratio', 0.2)
        )
        self.fitness_eval = FitnessEvaluator()
        self.arena = None  # Lazy init when needed
        self.pattern_analyzer = None  # Lazy init when needed
        self.recorder = None  # Lazy init when needed
        self.market_data = None

    def _init_arena(self):
        """Lazy init arena to avoid circular imports."""
        if self.arena is None:
            from ..arena.arena import AdversarialArena
            self.arena = AdversarialArena(self.config.get('arena', {}))

    def _init_pattern_analyzer(self):
        """Lazy init pattern analyzer."""
        if self.pattern_analyzer is None:
            from ..discovery.analyzer import PatternAnalyzer
            self.pattern_analyzer = PatternAnalyzer()

    def _init_recorder(self):
        """Lazy init recorder."""
        if self.recorder is None:
            from ..chronicle.recorder import EvolutionRecorder
            self.recorder = EvolutionRecorder(self.config.get('output_dir', 'output'))

    def load_data(self, candles: np.ndarray):
        """Load market data for backtesting."""
        self.market_data = candles

    def run(self, generations: int = 100,
            callback: Optional[Callable] = None) -> dict:
        """Run the full evolution."""
        self._init_recorder()

        results = {
            'generations': [],
            'champions': [],
            'patterns_discovered': [],
        }

        for gen in range(generations):
            stats = self._run_generation(gen)
            results['generations'].append(stats)
            results['champions'].append(stats['champion'].to_dict())

            if callback:
                callback(gen, stats)

        # Final pattern discovery on all survivors
        self._init_pattern_analyzer()
        final_patterns = self.pattern_analyzer.analyze_survivors(
            survivors=[a for a in self.population.agents if a.fitness > 0],
            market_data=self.market_data
        )
        results['patterns_discovered'] = [p.__dict__ for p in final_patterns]

        return results

    def _run_generation(self, gen_num: int) -> dict:
        """Execute one generation cycle."""
        data_slices = self._get_data_slices(num_slices=3)

        for agent_dna in self.population.agents:
            all_trades = []
            for data_slice in data_slices:
                agent = TradingAgent(agent_dna)
                trades = agent.run(data_slice)
                all_trades.extend(trades)

            # Optional adversarial rounds
            survival_bonus = 0.0
            if gen_num >= self.config.get('arena_start_gen', 5):
                self._init_arena()
                survival_bonus = self.arena.test_agent(agent_dna, data_slices[0])

            fitness = self.fitness_eval.evaluate(
                all_trades,
                survival_bonus=survival_bonus
            )
            agent_dna.fitness = fitness.composite

        parents = self.population.select_parents(method='tournament')

        champion = max(self.population.agents, key=lambda a: a.fitness)
        avg_fitness = np.mean([a.fitness for a in self.population.agents])

        stats = {
            'generation': gen_num,
            'champion': champion,
            'champion_fitness': champion.fitness,
            'avg_fitness': float(avg_fitness),
            'min_fitness': min(a.fitness for a in self.population.agents),
            'max_fitness': max(a.fitness for a in self.population.agents),
            'genetic_diversity': self._calc_diversity(),
            'population_snapshot': [a.to_dict() for a in self.population.agents],
        }

        if self.recorder:
            self.recorder.record_generation(stats)

        self.population.breed_next_generation(parents)

        return stats

    def _get_data_slices(self, num_slices: int = 3) -> list:
        """Get multiple overlapping slices for robust fitness evaluation."""
        if self.market_data is None:
            raise ValueError("No market data loaded. Call load_data() first.")
        total = len(self.market_data)
        slice_size = min(500, max(100, total // 3))

        rng = np.random.RandomState(seed=self.population.generation * 42)

        slices = []
        for _ in range(num_slices):
            start = rng.randint(0, total - slice_size)
            slices.append(self.market_data[start:start + slice_size])

        return slices

    def _calc_diversity(self) -> float:
        """Calculate genetic diversity of the population."""
        if len(self.population.agents) < 2:
            return 0.0

        distances = []
        agents = self.population.agents
        for i in range(min(20, len(agents))):
            for j in range(i + 1, min(20, len(agents))):
                distances.append(agents[i].distance(agents[j]))

        return float(np.mean(distances)) if distances else 0.0
