"""
Walk-Forward Validation — prevents overfitting by testing on unseen data.

Traditional backtesting trains and tests on the same data. Walk-forward
splits time-series chronologically: train on past, test on future.

    ┌──────────────────┬────────────┐
    │   Training (70%)  │  Test (30%) │   Window 1
    ├──────────────────┬┼────────────┤
    │     shift →       │ Train (70%)│ Test (30%) │   Window 2
    └──────────────────┴────────────┴────────────┘

Each window trains a fresh population. The champion is then evaluated
on the unseen test window. If fitness degrades significantly, the
strategy is overfitting.
"""

import numpy as np
from typing import List, Optional, Callable
from dataclasses import dataclass

from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from ..evolution.fitness import FitnessEvaluator


@dataclass
class WalkForwardWindow:
    """Result of one walk-forward window."""
    window_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    train_fitness: float
    test_fitness: float
    degradation: float  # train_fitness - test_fitness
    champion: dict  # Serialized champion DNA


@dataclass
class WalkForwardResult:
    """Complete walk-forward validation result."""
    windows: List[WalkForwardWindow]
    avg_train_fitness: float
    avg_test_fitness: float
    avg_degradation: float
    overfit_score: float  # 0 = no overfit, 1 = complete overfit
    is_robust: bool  # True if avg degradation < threshold

    def to_dict(self) -> dict:
        return {
            'windows': [
                {
                    'window_id': w.window_id,
                    'train_range': [w.train_start, w.train_end],
                    'test_range': [w.test_start, w.test_end],
                    'train_fitness': round(w.train_fitness, 4),
                    'test_fitness': round(w.test_fitness, 4),
                    'degradation': round(w.degradation, 4),
                    'champion': w.champion,
                }
                for w in self.windows
            ],
            'avg_train_fitness': round(self.avg_train_fitness, 4),
            'avg_test_fitness': round(self.avg_test_fitness, 4),
            'avg_degradation': round(self.avg_degradation, 4),
            'overfit_score': round(self.overfit_score, 4),
            'is_robust': self.is_robust,
        }


class WalkForwardValidator:
    """
    Walk-forward validation for evolved trading agents.

    Splits market data into chronological train/test windows,
    runs evolution on train data, evaluates champion on test data.
    """

    def __init__(
        self,
        n_windows: int = 3,
        train_ratio: float = 0.7,
        overlap: float = 0.0,
        degradation_threshold: float = 0.5,
    ):
        self.n_windows = n_windows
        self.train_ratio = train_ratio
        self.overlap = overlap
        self.degradation_threshold = degradation_threshold
        self.fitness_eval = FitnessEvaluator()

    def validate(
        self,
        market_data: np.ndarray,
        evolution_config: dict,
        generations: int = 30,
        callback: Optional[Callable] = None,
    ) -> WalkForwardResult:
        """
        Run walk-forward validation.

        Args:
            market_data: Full OHLCV candle array
            evolution_config: Config for EvolutionEngine
            generations: Generations per window
            callback: Optional progress callback(window_id, phase, info)

        Returns:
            WalkForwardResult with per-window and aggregate metrics
        """
        from ..evolution.engine import EvolutionEngine

        total = len(market_data)
        window_size = total // self.n_windows
        step = int(window_size * (1 - self.overlap))

        windows: List[WalkForwardWindow] = []

        for i in range(self.n_windows):
            start = i * step
            end = min(start + window_size, total)
            if end - start < 100:
                break

            split = start + int((end - start) * self.train_ratio)
            train_data = market_data[start:split]
            test_data = market_data[split:end]

            if len(train_data) < 50 or len(test_data) < 20:
                continue

            if callback:
                callback(i, 'train', {'candles': len(train_data)})

            # Train: run evolution on train data
            engine = EvolutionEngine(evolution_config)
            engine.load_data(train_data)
            results = engine.run(generations=generations)

            # Get champion
            champion = max(engine.population.agents, key=lambda a: a.fitness)
            train_fitness = champion.fitness

            # Test: evaluate champion on unseen test data
            if callback:
                callback(i, 'test', {'candles': len(test_data)})

            test_fitness = self._evaluate_on_data(champion, test_data)

            degradation = train_fitness - test_fitness

            windows.append(WalkForwardWindow(
                window_id=i,
                train_start=start,
                train_end=split,
                test_start=split,
                test_end=end,
                train_fitness=train_fitness,
                test_fitness=test_fitness,
                degradation=degradation,
                champion=champion.to_dict(),
            ))

        if not windows:
            return WalkForwardResult(
                windows=[], avg_train_fitness=0, avg_test_fitness=0,
                avg_degradation=0, overfit_score=1.0, is_robust=False,
            )

        avg_train = np.mean([w.train_fitness for w in windows])
        avg_test = np.mean([w.test_fitness for w in windows])
        avg_deg = np.mean([w.degradation for w in windows])

        # Overfit score: how much fitness degrades out-of-sample
        if avg_train > 0:
            overfit_score = float(np.clip(avg_deg / avg_train, 0, 1))
        else:
            overfit_score = 0.0

        return WalkForwardResult(
            windows=windows,
            avg_train_fitness=float(avg_train),
            avg_test_fitness=float(avg_test),
            avg_degradation=float(avg_deg),
            overfit_score=overfit_score,
            is_robust=avg_deg < self.degradation_threshold,
        )

    def _evaluate_on_data(self, dna: AgentDNA, data: np.ndarray) -> float:
        """Evaluate a single agent on a data segment."""
        agent = TradingAgent(dna)
        trades = agent.run(data)
        fitness = self.fitness_eval.evaluate(trades)
        return fitness.composite
