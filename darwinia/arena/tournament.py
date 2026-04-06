"""
Tournament Mode — round-robin competition between evolved champion agents.

Each agent faces adversarial attacks tuned to exploit THEIR specific weaknesses.
Agents are ranked by survival rate (primary) and average PnL (secondary).
"""

from dataclasses import dataclass, field
from itertools import combinations
from typing import List, Dict, Optional

import numpy as np

from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from .arena import AdversarialArena


@dataclass
class TournamentResult:
    """Result record for a single contestant in a tournament."""

    agent_id: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    survival_rate: float = 0.0
    avg_pnl: float = 0.0
    rank: int = 0

    def to_dict(self) -> dict:
        """Serialize to plain dict."""
        return {
            "agent_id": self.agent_id,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "survival_rate": round(self.survival_rate, 4),
            "avg_pnl": round(self.avg_pnl, 4),
            "rank": self.rank,
        }


class Tournament:
    """
    Round-robin tournament where agents compete head-to-head via adversarial arena.

    Each matchup pits two agents against the same set of adversarial scenarios
    targeted at each agent's weaknesses. The agent with higher survival rate
    wins the matchup; ties go to higher average PnL.
    """

    def __init__(self, rounds_per_match: int = 5):
        self.rounds_per_match = rounds_per_match
        self.contestants: Dict[str, AgentDNA] = {}
        self.results: List[TournamentResult] = []
        self.matchups: Dict[str, dict] = {}  # "id_a:id_b" -> matchup dict

    def add_contestant(self, dna: AgentDNA) -> None:
        """Register an agent DNA as a tournament contestant."""
        self.contestants[dna.id] = dna

    def run(self, verbose: bool = False) -> List[TournamentResult]:
        """
        Execute round-robin tournament.

        Each pair of agents faces adversarial attacks targeted at their own
        weaknesses. The agent with better survival rate wins the match.
        Ties are broken by average PnL.

        Returns results sorted by survival rate (desc), then avg_pnl (desc).
        """
        agent_ids = list(self.contestants.keys())
        n = len(agent_ids)

        # Per-agent accumulators
        stats: Dict[str, dict] = {
            aid: {"wins": 0, "losses": 0, "draws": 0,
                  "total_survival": 0.0, "total_pnl": 0.0, "match_count": 0}
            for aid in agent_ids
        }

        # Handle single-agent edge case
        if n < 2:
            if n == 1:
                aid = agent_ids[0]
                dna = self.contestants[aid]
                arena = AdversarialArena({"rounds_per_test": self.rounds_per_match})
                survival = arena.test_agent(dna, normal_data=None)
                pnl = self._calc_avg_pnl(arena)
                stats[aid]["total_survival"] = survival
                stats[aid]["total_pnl"] = pnl
                stats[aid]["match_count"] = 1
            self.results = self._build_results(stats)
            return self.results

        # Round-robin: every pair plays
        for id_a, id_b in combinations(agent_ids, 2):
            dna_a = self.contestants[id_a]
            dna_b = self.contestants[id_b]

            # Each agent runs through adversarial arena with attacks tuned to THEIR weaknesses
            arena_a = AdversarialArena({"rounds_per_test": self.rounds_per_match})
            survival_a = arena_a.test_agent(dna_a, normal_data=None)
            pnl_a = self._calc_avg_pnl(arena_a)

            arena_b = AdversarialArena({"rounds_per_test": self.rounds_per_match})
            survival_b = arena_b.test_agent(dna_b, normal_data=None)
            pnl_b = self._calc_avg_pnl(arena_b)

            # Determine winner
            if survival_a > survival_b:
                winner, loser = id_a, id_b
            elif survival_b > survival_a:
                winner, loser = id_b, id_a
            elif pnl_a > pnl_b:
                winner, loser = id_a, id_b
            elif pnl_b > pnl_a:
                winner, loser = id_b, id_a
            else:
                # True draw
                stats[id_a]["draws"] += 1
                stats[id_b]["draws"] += 1
                winner, loser = None, None

            if winner is not None:
                stats[winner]["wins"] += 1
                stats[loser]["losses"] += 1

            # Accumulate per-agent stats
            stats[id_a]["total_survival"] += survival_a
            stats[id_a]["total_pnl"] += pnl_a
            stats[id_a]["match_count"] += 1

            stats[id_b]["total_survival"] += survival_b
            stats[id_b]["total_pnl"] += pnl_b
            stats[id_b]["match_count"] += 1

            # Store matchup
            matchup_key = f"{id_a}:{id_b}"
            self.matchups[matchup_key] = {
                "agent_a": id_a,
                "agent_b": id_b,
                "survival_a": round(survival_a, 4),
                "survival_b": round(survival_b, 4),
                "pnl_a": round(pnl_a, 4),
                "pnl_b": round(pnl_b, 4),
                "winner": winner,
            }

            if verbose:
                w_label = winner if winner else "DRAW"
                print(
                    f"  {id_a} vs {id_b}: "
                    f"survival {survival_a:.1%} vs {survival_b:.1%} | "
                    f"pnl {pnl_a:+.2%} vs {pnl_b:+.2%} -> {w_label}"
                )

        self.results = self._build_results(stats)
        return self.results

    def get_leaderboard(self) -> List[dict]:
        """Return sorted leaderboard as list of dicts."""
        return [r.to_dict() for r in self.results]

    def get_matchup(self, agent_a: str, agent_b: str) -> dict:
        """
        Get head-to-head matchup result between two agents.

        Args:
            agent_a: ID of first agent.
            agent_b: ID of second agent.

        Returns:
            Dict with matchup details, or empty dict if matchup not found.
        """
        key1 = f"{agent_a}:{agent_b}"
        key2 = f"{agent_b}:{agent_a}"
        return self.matchups.get(key1, self.matchups.get(key2, {}))

    def _calc_avg_pnl(self, arena: AdversarialArena) -> float:
        """Calculate average PnL from arena history."""
        if not arena.history:
            return 0.0
        return float(np.mean([r.alpha_pnl for r in arena.history]))

    def _build_results(self, stats: Dict[str, dict]) -> List[TournamentResult]:
        """Build sorted TournamentResult list from accumulated stats."""
        results = []
        for aid, s in stats.items():
            mc = max(s["match_count"], 1)
            results.append(TournamentResult(
                agent_id=aid,
                wins=s["wins"],
                losses=s["losses"],
                draws=s["draws"],
                survival_rate=s["total_survival"] / mc,
                avg_pnl=s["total_pnl"] / mc,
            ))

        # Sort: survival_rate desc, then avg_pnl desc
        results.sort(key=lambda r: (r.survival_rate, r.avg_pnl), reverse=True)

        # Assign ranks
        for i, r in enumerate(results):
            r.rank = i + 1

        return results
