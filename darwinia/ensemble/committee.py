"""
Ensemble Committee — combines multiple evolved AgentDNA strategies
into a voting committee for consensus-based trading decisions.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Literal

from darwinia.core.dna import AgentDNA
from darwinia.core.agent import TradingAgent
from darwinia.core.types import TradeAction, TradeResult, Signal


@dataclass
class EnsembleResult:
    member_votes: List[Dict]          # [{agent_id, action, signal_strength, fitness}, ...]
    final_action: str                 # "buy" / "sell" / "hold"
    consensus_strength: float         # 0-1, how strongly the committee agrees
    member_count: int


VotingMode = Literal["majority", "weighted", "unanimous"]


class EnsembleAgent:
    """
    Runs a committee of TradingAgents derived from different AgentDNA instances.
    Aggregates their signals via configurable voting to produce consensus decisions.
    """

    def __init__(
        self,
        members: List[AgentDNA],
        voting_mode: VotingMode = "majority",
    ) -> None:
        if not members:
            raise ValueError("Committee requires at least one member")
        self.members = members
        self.voting_mode = voting_mode

    def run(self, candles: np.ndarray) -> List[List[TradeResult]]:
        """
        Run every member agent independently on the full candle dataset.
        Returns a list of TradeResult lists, one per member.
        """
        all_results: List[List[TradeResult]] = []
        for dna in self.members:
            agent = TradingAgent(dna)
            trades = agent.run(candles)
            all_results.append(trades)
        return all_results

    def vote(self, window: np.ndarray) -> EnsembleResult:
        """
        Get each member's signal on a candle window and aggregate via voting.

        window: numpy array slice with columns [timestamp, open, high, low, close, volume]
        Returns: EnsembleResult with the committee's consensus decision.
        """
        votes: List[Dict] = []
        for dna in self.members:
            agent = TradingAgent(dna)
            signal = agent._compute_signal(window)
            action = agent._decide(signal, window[-1])
            votes.append({
                "agent_id": dna.id,
                "action": action.value,
                "signal_strength": signal.composite,
                "fitness": dna.fitness,
            })

        final_action = self._aggregate_votes(votes)
        consensus_strength = self._calc_consensus(votes, final_action)

        return EnsembleResult(
            member_votes=votes,
            final_action=final_action,
            consensus_strength=consensus_strength,
            member_count=len(self.members),
        )

    def evaluate(self, candles: np.ndarray) -> Dict:
        """
        Run all members, collect trade results and consensus metrics.
        Returns dict with 'trades' (combined TradeResult list),
        'per_member' stats, and 'consensus' metrics from sampled votes.
        """
        all_results = self.run(candles)

        # Combine all trades
        combined_trades: List[TradeResult] = []
        per_member: List[Dict] = []
        for dna, trades in zip(self.members, all_results):
            combined_trades.extend(trades)
            total_pnl = sum(t.pnl for t in trades)
            win_count = sum(1 for t in trades if t.pnl > 0)
            per_member.append({
                "agent_id": dna.id,
                "fitness": dna.fitness,
                "num_trades": len(trades),
                "total_pnl": total_pnl,
                "win_rate": win_count / len(trades) if trades else 0.0,
            })

        # Sample consensus metrics by voting on periodic windows
        lookback = max(
            int(50 + dna.time_horizon * 150) for dna in self.members
        )
        sample_interval = max(1, (len(candles) - lookback) // 20)
        consensus_samples: List[float] = []
        action_counts = {"buy": 0, "sell": 0, "hold": 0}

        for i in range(lookback, len(candles), sample_interval):
            window = candles[max(0, i - lookback): i + 1]
            result = self.vote(window)
            consensus_samples.append(result.consensus_strength)
            action_counts[result.final_action] += 1

        avg_consensus = (
            float(np.mean(consensus_samples)) if consensus_samples else 0.0
        )

        return {
            "trades": combined_trades,
            "per_member": per_member,
            "consensus": {
                "avg_consensus_strength": avg_consensus,
                "action_distribution": action_counts,
                "num_samples": len(consensus_samples),
            },
        }

    def _aggregate_votes(self, votes: List[Dict]) -> str:
        """Aggregate member votes into a final action based on voting mode."""
        if self.voting_mode == "unanimous":
            return self._unanimous_vote(votes)
        elif self.voting_mode == "weighted":
            return self._weighted_vote(votes)
        else:
            return self._majority_vote(votes)

    def _majority_vote(self, votes: List[Dict]) -> str:
        """Simple majority: action with most votes wins. Ties broken by signal strength."""
        counts: Dict[str, int] = {"buy": 0, "sell": 0, "hold": 0}
        signal_sums: Dict[str, float] = {"buy": 0.0, "sell": 0.0, "hold": 0.0}
        for v in votes:
            counts[v["action"]] += 1
            signal_sums[v["action"]] += abs(v.get("signal_strength", 0))

        max_count = max(counts.values())
        winners = [a for a, c in counts.items() if c == max_count]

        if len(winners) == 1:
            return winners[0]
        # Tie: pick the action with stronger aggregate signal conviction
        return max(winners, key=lambda a: signal_sums[a]) if any(signal_sums[w] > 0 for w in winners) else "hold"

    def _weighted_vote(self, votes: List[Dict]) -> str:
        """Fitness-weighted voting: each member's vote is scaled by its fitness."""
        scores: Dict[str, float] = {"buy": 0.0, "sell": 0.0, "hold": 0.0}
        for v in votes:
            weight = max(v["fitness"], 0.0)
            scores[v["action"]] += weight

        total = sum(scores.values())
        if total == 0:
            # All zero fitness, fall back to majority
            return self._majority_vote(votes)

        best_action = max(scores, key=scores.get)
        return best_action

    def _unanimous_vote(self, votes: List[Dict]) -> str:
        """Unanimous: all members must agree, otherwise hold."""
        actions = {v["action"] for v in votes}
        if len(actions) == 1:
            return actions.pop()
        return "hold"

    def _calc_consensus(self, votes: List[Dict], final_action: str) -> float:
        """
        Measure how strongly the committee agrees on the final action.
        Returns float in [0, 1]. 1.0 = perfect agreement.
        For weighted mode, uses fitness-weighted agreement.
        """
        if not votes:
            return 0.0

        if self.voting_mode == "weighted":
            total_weight = sum(max(v["fitness"], 0.0) for v in votes)
            if total_weight == 0:
                # Fall back to unweighted
                agreeing = sum(1 for v in votes if v["action"] == final_action)
                return agreeing / len(votes)
            agreeing_weight = sum(max(v["fitness"], 0.0) for v in votes if v["action"] == final_action)
            return agreeing_weight / total_weight

        agreeing = sum(1 for v in votes if v["action"] == final_action)
        return agreeing / len(votes)
