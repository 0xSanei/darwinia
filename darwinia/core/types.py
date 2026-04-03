"""Shared type definitions."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class TradeAction(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Signal:
    composite: float               # [-1, 1] final signal
    components: Dict[str, float]   # Individual signal values


@dataclass
class Position:
    direction: str
    entry_price: float
    size: float
    entry_time: float


@dataclass
class TradeResult:
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    entry_time: float
    exit_time: float
    direction: str = 'long'        # 'long' or 'short'


@dataclass
class FitnessScore:
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    survival_bonus: float          # Bonus for surviving adversarial attacks
    composite: float               # Final fitness score


@dataclass
class AttackScenario:
    name: str
    description: str
    pattern_type: str              # rug_pull, fake_breakout, sandwich, etc.
    difficulty: float              # 0-1
    candles: object                # numpy array of manipulated candles


@dataclass
class RoundResult:
    alpha_pnl: float
    trap_type: str
    survived: bool
    alpha_id: str
    generation: int


@dataclass
class DiscoveredPattern:
    name: str                      # Auto-generated name
    features: Dict[str, float]     # Feature importances
    predictive_power: float        # 0-1
    human_equivalent: Optional[str]  # Matching known indicator, if any
    discovered_by: str             # Agent ID
    generation: int
