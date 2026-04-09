"""
Portfolio Allocator — distribute capital across multiple evolved strategies.

Treats each AgentDNA as a sub-strategy and computes optimal capital weights
using classical portfolio theory: equal weight, Sharpe-weighted, risk parity,
inverse-variance, and fractional Kelly.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Literal

from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from ..core.market import MarketEnvironment
from ..backtest.metrics import compute_metrics


AllocationMethod = Literal[
    "equal_weight", "sharpe_weighted", "risk_parity", "inverse_variance", "kelly"
]


@dataclass
class AllocationResult:
    """Output of a portfolio allocation run."""
    method: str
    weights: Dict[str, float]                # agent_id -> weight in [0,1]
    expected_return: float                   # weighted mean return
    portfolio_volatility: float              # std of weighted return series
    portfolio_sharpe: float                  # weighted return series sharpe
    diversification_ratio: float             # weighted vol / portfolio vol
    member_metrics: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "method": self.method,
            "weights": {k: round(v, 4) for k, v in self.weights.items()},
            "expected_return": round(self.expected_return, 4),
            "portfolio_volatility": round(self.portfolio_volatility, 4),
            "portfolio_sharpe": round(self.portfolio_sharpe, 4),
            "diversification_ratio": round(self.diversification_ratio, 4),
            "member_metrics": self.member_metrics,
        }

    def summary(self) -> str:
        lines = [
            f"{'─' * 56}",
            f"  PORTFOLIO ALLOCATION — {self.method}",
            f"{'─' * 56}",
            f"  Expected Return:       {self.expected_return:>+10.2%}",
            f"  Portfolio Volatility:  {self.portfolio_volatility:>10.4f}",
            f"  Portfolio Sharpe:      {self.portfolio_sharpe:>10.4f}",
            f"  Diversification:       {self.diversification_ratio:>10.4f}",
            f"{'─' * 56}",
            f"  Allocation:",
        ]
        for agent_id, w in sorted(self.weights.items(), key=lambda x: -x[1]):
            bar_w = max(0, min(20, int(round(w * 20))))
            bar = "█" * bar_w + "░" * (20 - bar_w)
            lines.append(f"    {agent_id:<10} {bar} {w:>6.2%}")
        lines.append(f"{'─' * 56}")
        return "\n".join(lines)


class PortfolioAllocator:
    """
    Compute capital allocation weights across a list of evolved strategies.

    The allocator runs each member strategy on the same market data, derives
    a per-trade return series, then applies the chosen allocation method to
    compute weights. All methods produce non-negative weights summing to 1.
    """

    VALID_METHODS = (
        "equal_weight", "sharpe_weighted", "risk_parity",
        "inverse_variance", "kelly",
    )

    def __init__(
        self,
        data_dir: str = "data",
        initial_capital: float = 10000.0,
        risk_free_rate: float = 0.04,
        kelly_fraction: float = 0.5,
    ) -> None:
        self.data_dir = data_dir
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        self.kelly_fraction = kelly_fraction  # Half-Kelly is the standard prudent default

    def allocate(
        self,
        members: List[AgentDNA],
        data_file: str,
        method: AllocationMethod = "risk_parity",
    ) -> AllocationResult:
        """Run all members on the same data and compute allocation weights."""
        if not members:
            raise ValueError("Need at least one strategy to allocate")
        if method not in self.VALID_METHODS:
            raise ValueError(f"Unknown method '{method}'. Must be one of {self.VALID_METHODS}")

        market = MarketEnvironment(data_dir=self.data_dir)
        candles = market.load_csv(data_file)

        # Run each member, collect per-trade return series and metrics
        return_series: List[np.ndarray] = []
        member_metrics: List[Dict] = []
        ids: List[str] = []

        for dna in members:
            agent = TradingAgent(dna)
            agent.state.cash = self.initial_capital
            trades = agent.run(candles)
            metrics = compute_metrics(trades, initial_capital=self.initial_capital)
            pnl_pcts = np.array([t.pnl_pct for t in trades]) if trades else np.array([0.0])
            return_series.append(pnl_pcts)
            member_metrics.append({
                "agent_id": dna.id,
                "num_trades": len(trades),
                "total_return_pct": metrics.total_return_pct,
                "sharpe_ratio": metrics.sharpe_ratio,
                "max_drawdown_pct": metrics.max_drawdown_pct,
                "win_rate": metrics.win_rate,
            })
            ids.append(dna.id)

        # Compute raw weights per chosen method
        raw = self._compute_raw_weights(method, return_series, member_metrics)
        weights_arr = self._normalize(raw)

        weights = {ids[i]: float(weights_arr[i]) for i in range(len(ids))}

        # Portfolio statistics
        expected_return, port_vol, port_sharpe, div_ratio = self._portfolio_stats(
            weights_arr, return_series
        )

        return AllocationResult(
            method=method,
            weights=weights,
            expected_return=expected_return,
            portfolio_volatility=port_vol,
            portfolio_sharpe=port_sharpe,
            diversification_ratio=div_ratio,
            member_metrics=member_metrics,
        )

    # ─── Allocation methods ───────────────────────────────────────────────

    def _compute_raw_weights(
        self,
        method: str,
        return_series: List[np.ndarray],
        member_metrics: List[Dict],
    ) -> np.ndarray:
        n = len(return_series)

        if method == "equal_weight":
            return np.ones(n)

        if method == "sharpe_weighted":
            # Use only positive Sharpe ratios; if none positive, fall back to equal
            sharpes = np.array([max(m["sharpe_ratio"], 0.0) for m in member_metrics])
            if sharpes.sum() == 0:
                return np.ones(n)
            return sharpes

        if method == "inverse_variance":
            # Weight ∝ 1 / variance of returns
            variances = np.array([
                max(float(np.var(r, ddof=1)) if len(r) > 1 else 1e-6, 1e-6)
                for r in return_series
            ])
            return 1.0 / variances

        if method == "risk_parity":
            # Equal risk contribution: weight ∝ 1 / volatility
            vols = np.array([
                max(float(np.std(r, ddof=1)) if len(r) > 1 else 1e-6, 1e-6)
                for r in return_series
            ])
            return 1.0 / vols

        if method == "kelly":
            # Per-strategy Kelly: f* = mean / variance
            kellys = []
            for r in return_series:
                if len(r) < 2:
                    kellys.append(0.0)
                    continue
                mean = float(np.mean(r))
                var = float(np.var(r, ddof=1))
                if var <= 0 or mean <= 0:
                    kellys.append(0.0)
                else:
                    kellys.append((mean / var) * self.kelly_fraction)
            arr = np.array(kellys)
            if arr.sum() <= 0:
                # No edge across the board → equal weight as a safe fallback
                return np.ones(n)
            return arr

        raise ValueError(f"Unknown method: {method}")

    def _normalize(self, raw: np.ndarray) -> np.ndarray:
        """Normalize raw weights to sum to 1; clamp negatives to 0 first."""
        clamped = np.maximum(raw, 0.0)
        total = clamped.sum()
        if total <= 0:
            return np.ones(len(raw)) / len(raw)
        return clamped / total

    # ─── Portfolio statistics ─────────────────────────────────────────────

    def _portfolio_stats(
        self,
        weights: np.ndarray,
        return_series: List[np.ndarray],
    ):
        """Compute expected return, volatility, Sharpe, and diversification ratio."""
        # Per-strategy mean (sum of pnl_pct as a return proxy)
        means = np.array([float(np.sum(r)) for r in return_series])
        expected_return = float(np.dot(weights, means))

        # Build aligned return matrix for covariance: pad shorter series with zeros
        max_len = max(len(r) for r in return_series)
        if max_len < 2:
            return expected_return, 0.0, 0.0, 1.0

        matrix = np.zeros((max_len, len(return_series)))
        for i, r in enumerate(return_series):
            matrix[: len(r), i] = r

        cov = np.cov(matrix, rowvar=False)
        # Edge case: a single member or degenerate covariance
        if np.ndim(cov) == 0:
            port_var = float(cov) * weights[0] ** 2
        else:
            port_var = float(weights @ cov @ weights)

        port_vol = float(np.sqrt(max(port_var, 0.0)))

        # Sharpe of the weighted return series
        if port_vol > 0:
            port_sharpe = expected_return / port_vol
        else:
            port_sharpe = 0.0

        # Diversification ratio: weighted average vol / portfolio vol
        if np.ndim(cov) == 0:
            individual_vols = np.array([float(np.sqrt(max(cov, 0.0)))])
        else:
            individual_vols = np.sqrt(np.maximum(np.diag(cov), 0.0))
        weighted_vol = float(np.dot(weights, individual_vols))
        if port_vol > 0:
            div_ratio = weighted_vol / port_vol
        else:
            div_ratio = 1.0

        return expected_return, port_vol, port_sharpe, div_ratio
