"""
Macro regime awareness for evolved trading agents.

Provides macro liquidity regime simulation and fitness adjustments
so that agents can learn to adapt position sizing to macro conditions.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List
import numpy as np


class MacroRegime(Enum):
    """Macro liquidity regime classification."""
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    TRANSITION = "transition"


class LiquidityTrend(Enum):
    """Direction of Fed liquidity flow."""
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class VolatilityLevel(Enum):
    """Macro volatility classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MacroSignal:
    """A single day's macro environment reading.

    Attributes:
        regime: Current macro regime classification.
        fed_liquidity_trend: Direction of Fed net liquidity.
        volatility_level: Current macro volatility bucket.
        timestamp: Day index (0-based).
    """
    regime: MacroRegime
    fed_liquidity_trend: LiquidityTrend
    volatility_level: VolatilityLevel
    timestamp: int


class MacroSimulator:
    """Generates synthetic macro regime sequences for evolution training.

    Produces realistic regime transitions where each regime persists
    for 20-60 days with gradual transitions between them.
    """

    def __init__(self, seed: int = None):
        """Initialize simulator with optional random seed.

        Args:
            seed: Random seed for reproducibility.
        """
        self.rng = np.random.RandomState(seed)

    def generate_regime_sequence(self, n_days: int) -> List[MacroSignal]:
        """Generate a sequence of macro signals spanning n_days.

        Regimes persist for 20-60 days. Transitions between RISK_ON and
        RISK_OFF go through a TRANSITION phase lasting 5-15 days.

        Args:
            n_days: Number of days to generate.

        Returns:
            List of MacroSignal, one per day.
        """
        if n_days <= 0:
            return []

        signals: List[MacroSignal] = []
        day = 0

        # Pick initial regime (not TRANSITION)
        current_regime = self.rng.choice([MacroRegime.RISK_ON, MacroRegime.RISK_OFF])

        while day < n_days:
            # Determine duration of current regime block
            if current_regime == MacroRegime.TRANSITION:
                duration = self.rng.randint(5, 16)  # 5-15 days
            else:
                duration = self.rng.randint(20, 61)  # 20-60 days

            # Cap to remaining days
            duration = min(duration, n_days - day)

            # Derive liquidity trend and volatility from regime
            for i in range(duration):
                liq_trend = self._liquidity_for_regime(current_regime)
                vol_level = self._volatility_for_regime(current_regime)
                signals.append(MacroSignal(
                    regime=current_regime,
                    fed_liquidity_trend=liq_trend,
                    volatility_level=vol_level,
                    timestamp=day,
                ))
                day += 1

            # Transition to next regime
            current_regime = self._next_regime(current_regime)

        return signals

    def _liquidity_for_regime(self, regime: MacroRegime) -> LiquidityTrend:
        """Derive liquidity trend from regime with some noise."""
        if regime == MacroRegime.RISK_ON:
            return self.rng.choice(
                [LiquidityTrend.UP, LiquidityTrend.FLAT],
                p=[0.7, 0.3],
            )
        elif regime == MacroRegime.RISK_OFF:
            return self.rng.choice(
                [LiquidityTrend.DOWN, LiquidityTrend.FLAT],
                p=[0.7, 0.3],
            )
        else:  # TRANSITION
            return self.rng.choice(list(LiquidityTrend))

    def _volatility_for_regime(self, regime: MacroRegime) -> VolatilityLevel:
        """Derive volatility level from regime with some noise."""
        if regime == MacroRegime.RISK_ON:
            return self.rng.choice(
                [VolatilityLevel.LOW, VolatilityLevel.MEDIUM],
                p=[0.6, 0.4],
            )
        elif regime == MacroRegime.RISK_OFF:
            return self.rng.choice(
                [VolatilityLevel.HIGH, VolatilityLevel.MEDIUM],
                p=[0.6, 0.4],
            )
        else:
            return VolatilityLevel.MEDIUM

    def _next_regime(self, current: MacroRegime) -> MacroRegime:
        """Determine next regime. Transitions are always gradual."""
        if current == MacroRegime.RISK_ON:
            return MacroRegime.TRANSITION
        elif current == MacroRegime.RISK_OFF:
            return MacroRegime.TRANSITION
        else:
            # Exit transition to either risk_on or risk_off
            return self.rng.choice([MacroRegime.RISK_ON, MacroRegime.RISK_OFF])


class MacroAwareFitness:
    """Adjusts fitness scores based on how well agents adapt to macro regimes.

    Rewards agents that:
    - Reduce position size during RISK_OFF
    - Increase position size during RISK_ON
    - React to regime changes (not regime-blind)

    Penalizes agents that ignore macro conditions entirely.
    """

    def __init__(
        self,
        regime_weight: float = 0.3,
        adaptation_bonus: float = 0.15,
    ):
        """Initialize macro-aware fitness evaluator.

        Args:
            regime_weight: Weight of regime-alignment score in final fitness.
            adaptation_bonus: Bonus for agents that demonstrate regime adaptation.
        """
        self.regime_weight = regime_weight
        self.adaptation_bonus = adaptation_bonus

    def evaluate(
        self,
        agent_decisions: List[float],
        macro_signals: List[MacroSignal],
        base_fitness: float = 0.0,
    ) -> float:
        """Compute macro-adjusted fitness score.

        Args:
            agent_decisions: Position sizes per day (0.0 = no position,
                1.0 = full position). Length must match macro_signals.
            macro_signals: Macro regime signals per day.
            base_fitness: Base fitness score from standard evaluator.

        Returns:
            Macro-adjusted composite fitness score.
        """
        n = len(macro_signals)
        if n == 0:
            return base_fitness

        if len(agent_decisions) != n:
            raise ValueError(
                f"agent_decisions length ({len(agent_decisions)}) must match "
                f"macro_signals length ({n})"
            )

        decisions = np.array(agent_decisions, dtype=float)

        # Score regime alignment: reward low positions in RISK_OFF,
        # high positions in RISK_ON
        alignment_scores = np.zeros(n)
        for i, sig in enumerate(macro_signals):
            pos = decisions[i]
            if sig.regime == MacroRegime.RISK_ON:
                # Reward higher positions (0->-1, 1->+1)
                alignment_scores[i] = 2.0 * pos - 1.0
            elif sig.regime == MacroRegime.RISK_OFF:
                # Reward lower positions (0->+1, 1->-1)
                alignment_scores[i] = 1.0 - 2.0 * pos
            else:
                # TRANSITION: moderate positions are best (0.5 -> +1)
                alignment_scores[i] = 1.0 - 2.0 * abs(pos - 0.5)

        regime_score = float(np.mean(alignment_scores))

        # Adaptation detection: does the agent change behavior across regimes?
        adaptation_score = self._measure_adaptation(decisions, macro_signals)

        composite = (
            base_fitness
            + self.regime_weight * regime_score
            + self.adaptation_bonus * adaptation_score
        )
        return composite

    def _measure_adaptation(
        self,
        decisions: np.ndarray,
        signals: List[MacroSignal],
    ) -> float:
        """Measure whether agent adapts position sizing to regimes.

        Returns a score in [-1, 1]. Positive means the agent differentiates
        between regimes. Negative means it does the opposite of what it should.

        Args:
            decisions: Array of position sizes.
            signals: Corresponding macro signals.

        Returns:
            Adaptation score between -1 and 1.
        """
        risk_on_positions = []
        risk_off_positions = []

        for i, sig in enumerate(signals):
            if sig.regime == MacroRegime.RISK_ON:
                risk_on_positions.append(decisions[i])
            elif sig.regime == MacroRegime.RISK_OFF:
                risk_off_positions.append(decisions[i])

        if not risk_on_positions or not risk_off_positions:
            return 0.0

        avg_on = float(np.mean(risk_on_positions))
        avg_off = float(np.mean(risk_off_positions))

        # Difference between avg position in RISK_ON vs RISK_OFF.
        # Positive = agent sizes up in RISK_ON, down in RISK_OFF (good).
        diff = avg_on - avg_off
        return float(np.clip(diff, -1.0, 1.0))
