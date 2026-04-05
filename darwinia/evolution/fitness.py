"""
Fitness evaluation — how good is an agent's DNA?

Fitness is NOT just PnL. It's a composite of:
- Risk-adjusted returns (Sharpe-like)
- Drawdown penalty
- Win rate
- Consistency
- Adversarial survival bonus
"""

import numpy as np
from typing import List
from ..core.types import TradeResult, FitnessScore


class FitnessEvaluator:
    """Computes composite fitness scores from trade results."""

    def __init__(self, risk_free_rate: float = 0.0) -> None:
        self.risk_free_rate = risk_free_rate

    def evaluate(self, trades: List[TradeResult],
                 initial_capital: float = 10000.0,
                 survival_bonus: float = 0.0) -> FitnessScore:
        """Compute composite fitness from trade results."""

        if not trades:
            return FitnessScore(
                total_pnl=0, sharpe_ratio=0, max_drawdown=0,
                win_rate=0, num_trades=0, survival_bonus=survival_bonus,
                composite=-0.3 + survival_bonus * 0.10
            )

        pnls = [t.pnl for t in trades]
        pnl_pcts = [t.pnl_pct for t in trades]

        total_pnl = sum(pnls)
        win_rate = sum(1 for p in pnls if p > 0) / len(pnls)

        # Sharpe ratio
        if len(pnl_pcts) > 1 and np.std(pnl_pcts, ddof=1) > 0:
            sharpe = (np.mean(pnl_pcts) - self.risk_free_rate) / np.std(pnl_pcts, ddof=1)
            sharpe = float(np.clip(sharpe, -3, 3))  # Normalize to prevent dominating composite
        else:
            sharpe = 0.0

        # Max drawdown
        cumulative = np.cumsum(pnls) + initial_capital
        peak = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - peak) / peak
        max_dd = min(abs(min(drawdowns)), 1.0) if len(drawdowns) > 0 else 0

        # Composite fitness
        composite = (
            sharpe * 0.35 +
            (total_pnl / initial_capital) * 0.25 +
            win_rate * 0.15 +
            (1 - max_dd) * 0.15 +
            survival_bonus * 0.10
        )

        return FitnessScore(
            total_pnl=total_pnl,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            num_trades=len(trades),
            survival_bonus=survival_bonus,
            composite=composite,
        )
