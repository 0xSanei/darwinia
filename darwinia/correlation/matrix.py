"""
Correlation Matrix — measure similarity between evolved strategies.

Runs multiple AgentDNA strategies on the same market data, extracts
their trade return series, and computes pairwise correlation. High
correlation means the strategies are redundant; low or negative
correlation means they diversify each other — critical input for
portfolio construction and ensemble selection.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from ..core.market import MarketEnvironment


@dataclass
class CorrelationResult:
    """Output of cross-strategy correlation analysis."""
    matrix: np.ndarray                       # NxN correlation matrix
    agent_ids: List[str]                     # ordered agent IDs
    avg_correlation: float                   # mean off-diagonal correlation
    max_pair: Tuple[str, str, float]         # most correlated pair
    min_pair: Tuple[str, str, float]         # least correlated pair
    cluster_groups: List[List[str]]          # agents grouped by high correlation
    member_stats: List[Dict]                 # per-agent trade stats

    def to_dict(self) -> Dict:
        return {
            "agent_ids": self.agent_ids,
            "matrix": [[round(float(v), 4) for v in row] for row in self.matrix],
            "avg_correlation": round(self.avg_correlation, 4),
            "max_pair": {
                "agents": [self.max_pair[0], self.max_pair[1]],
                "correlation": round(self.max_pair[2], 4),
            },
            "min_pair": {
                "agents": [self.min_pair[0], self.min_pair[1]],
                "correlation": round(self.min_pair[2], 4),
            },
            "cluster_groups": self.cluster_groups,
            "member_stats": self.member_stats,
        }

    def summary(self) -> str:
        n = len(self.agent_ids)
        lines = [
            f"{'─' * 56}",
            f"  STRATEGY CORRELATION ANALYSIS",
            f"{'─' * 56}",
            f"  Strategies: {n}",
            f"  Avg Correlation: {self.avg_correlation:+.4f}",
            f"  Most Similar:  {self.max_pair[0]} ↔ {self.max_pair[1]} ({self.max_pair[2]:+.4f})",
            f"  Most Diverse:  {self.min_pair[0]} ↔ {self.min_pair[1]} ({self.min_pair[2]:+.4f})",
            f"  Clusters:      {len(self.cluster_groups)}",
            f"{'─' * 56}",
        ]

        # ASCII heatmap
        if n <= 10:
            lines.append("  Correlation Heatmap:")
            header = "            " + "  ".join(f"{aid[:6]:>6}" for aid in self.agent_ids)
            lines.append(header)
            for i, aid in enumerate(self.agent_ids):
                row_str = f"  {aid[:8]:<10}"
                for j in range(n):
                    v = self.matrix[i, j]
                    cell = self._heat_char(v)
                    row_str += f"  {cell:>6}"
                lines.append(row_str)
            lines.append(f"  Legend: ■■=high ▓▓=mid ░░=low ··=neg")

        lines.append(f"{'─' * 56}")
        return "\n".join(lines)

    @staticmethod
    def _heat_char(v: float) -> str:
        if v >= 0.8:
            return "■■" + f"{v:+.2f}"[1:]
        elif v >= 0.4:
            return "▓▓" + f"{v:+.2f}"[1:]
        elif v >= 0.0:
            return "░░" + f"{v:+.2f}"[1:]
        else:
            return "··" + f"{v:+.2f}"[1:]


class CorrelationAnalyzer:
    """
    Compute pairwise correlation between evolved strategies.

    Each agent is run on the same candle data. Trade PnL percentages are
    binned into fixed time buckets (one per N candles) to create aligned
    return series. Pearson correlation is then computed pairwise.
    """

    def __init__(
        self,
        data_dir: str = "data",
        initial_capital: float = 10000.0,
        bucket_size: int = 50,
        cluster_threshold: float = 0.7,
    ) -> None:
        self.data_dir = data_dir
        self.initial_capital = initial_capital
        self.bucket_size = max(10, bucket_size)
        self.cluster_threshold = cluster_threshold

    def analyze(
        self,
        members: List[AgentDNA],
        data_file: str,
    ) -> CorrelationResult:
        """Run all members and compute correlation matrix."""
        if len(members) < 2:
            raise ValueError("Need at least 2 strategies for correlation analysis")

        market = MarketEnvironment(data_dir=self.data_dir)
        candles = market.load_csv(data_file)
        n_candles = len(candles)
        n_buckets = max(1, n_candles // self.bucket_size)

        # Run each agent and build bucketed return series
        return_vectors: List[np.ndarray] = []
        agent_ids: List[str] = []
        member_stats: List[Dict] = []

        for dna in members:
            agent = TradingAgent(dna)
            agent.state.cash = self.initial_capital
            trades = agent.run(candles)

            # Build per-bucket PnL using entry_time (candle index)
            bucket_pnl = np.zeros(n_buckets)
            for t in trades:
                # entry_time is the candle timestamp (index in our arrays)
                idx = int(t.entry_time) if t.entry_time < n_candles else 0
                bucket_idx = min(idx // self.bucket_size, n_buckets - 1)
                bucket_pnl[bucket_idx] += t.pnl_pct

            return_vectors.append(bucket_pnl)
            agent_ids.append(dna.id)
            total_pnl = sum(t.pnl_pct for t in trades) if trades else 0.0
            member_stats.append({
                "agent_id": dna.id,
                "num_trades": len(trades),
                "total_pnl_pct": round(total_pnl, 4),
            })

        # Compute correlation matrix
        n = len(members)
        matrix = np.eye(n)

        for i in range(n):
            for j in range(i + 1, n):
                corr = self._pearson(return_vectors[i], return_vectors[j])
                matrix[i, j] = corr
                matrix[j, i] = corr

        # Extract stats
        avg_corr, max_pair, min_pair = self._extract_pairs(matrix, agent_ids)

        # Simple clustering: group agents with corr > threshold
        clusters = self._cluster(matrix, agent_ids)

        return CorrelationResult(
            matrix=matrix,
            agent_ids=agent_ids,
            avg_correlation=avg_corr,
            max_pair=max_pair,
            min_pair=min_pair,
            cluster_groups=clusters,
            member_stats=member_stats,
        )

    def _pearson(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute Pearson correlation, handling degenerate cases."""
        if len(a) < 2 or len(b) < 2:
            return 0.0
        std_a = float(np.std(a))
        std_b = float(np.std(b))
        if std_a < 1e-10 or std_b < 1e-10:
            return 0.0
        corr = float(np.corrcoef(a, b)[0, 1])
        if np.isnan(corr):
            return 0.0
        return corr

    def _extract_pairs(
        self, matrix: np.ndarray, ids: List[str],
    ) -> Tuple[float, Tuple[str, str, float], Tuple[str, str, float]]:
        """Extract avg, max, and min correlation pairs."""
        n = matrix.shape[0]
        off_diag = []
        max_val = -2.0
        min_val = 2.0
        max_pair = (ids[0], ids[1] if n > 1 else ids[0], 0.0)
        min_pair = (ids[0], ids[1] if n > 1 else ids[0], 0.0)

        for i in range(n):
            for j in range(i + 1, n):
                v = float(matrix[i, j])
                off_diag.append(v)
                if v > max_val:
                    max_val = v
                    max_pair = (ids[i], ids[j], v)
                if v < min_val:
                    min_val = v
                    min_pair = (ids[i], ids[j], v)

        avg = float(np.mean(off_diag)) if off_diag else 0.0
        return avg, max_pair, min_pair

    def _cluster(self, matrix: np.ndarray, ids: List[str]) -> List[List[str]]:
        """Simple greedy clustering: group agents with correlation > threshold."""
        n = matrix.shape[0]
        assigned = [False] * n
        clusters = []

        for i in range(n):
            if assigned[i]:
                continue
            group = [ids[i]]
            assigned[i] = True
            for j in range(i + 1, n):
                if assigned[j]:
                    continue
                if float(matrix[i, j]) >= self.cluster_threshold:
                    group.append(ids[j])
                    assigned[j] = True
            clusters.append(group)

        return clusters
