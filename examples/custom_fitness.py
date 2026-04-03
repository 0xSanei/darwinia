"""Example: customizing the fitness function."""

import numpy as np
from darwinia.core.types import TradeResult, FitnessScore
from darwinia.evolution.fitness import FitnessEvaluator


class ConservativeFitness(FitnessEvaluator):
    """Custom fitness that heavily penalizes drawdowns."""

    def evaluate(self, trades, initial_capital=10000.0, survival_bonus=0.0):
        base = super().evaluate(trades, initial_capital, survival_bonus)

        # Override composite: drawdown penalty is 40% weight
        if trades:
            composite = (
                base.sharpe_ratio * 0.25 +
                (base.total_pnl / initial_capital) * 0.15 +
                base.win_rate * 0.10 +
                (1 - base.max_drawdown) * 0.40 +  # Heavy drawdown penalty
                survival_bonus * 0.10
            )
        else:
            composite = base.composite

        return FitnessScore(
            total_pnl=base.total_pnl,
            sharpe_ratio=base.sharpe_ratio,
            max_drawdown=base.max_drawdown,
            win_rate=base.win_rate,
            num_trades=base.num_trades,
            survival_bonus=base.survival_bonus,
            composite=composite,
        )


if __name__ == '__main__':
    # Demo: compare standard vs conservative fitness
    trades = [
        TradeResult(100, 120, 200, 0.20, 0, 1, 'long'),
        TradeResult(120, 90, -300, -0.25, 2, 3, 'long'),
        TradeResult(90, 110, 200, 0.22, 4, 5, 'long'),
    ]

    standard = FitnessEvaluator()
    conservative = ConservativeFitness()

    s1 = standard.evaluate(trades)
    s2 = conservative.evaluate(trades)

    print(f"Standard fitness:     {s1.composite:.4f}")
    print(f"Conservative fitness: {s2.composite:.4f}")
    print(f"Max drawdown:         {s1.max_drawdown:.2%}")
