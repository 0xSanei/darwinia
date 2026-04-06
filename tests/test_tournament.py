"""Tests for Tournament Mode."""

import random
import numpy as np
from darwinia.core.dna import AgentDNA
from darwinia.arena.tournament import Tournament, TournamentResult


def test_add_contestant_and_run():
    """Tournament should accept contestants and produce results for each."""
    random.seed(42)
    np.random.seed(42)

    t = Tournament(rounds_per_match=3)
    agents = [AgentDNA.random() for _ in range(3)]
    for a in agents:
        t.add_contestant(a)

    results = t.run()
    assert len(results) == 3
    agent_ids = {r.agent_id for r in results}
    assert agent_ids == {a.id for a in agents}

    # Every result should have a rank assigned
    ranks = [r.rank for r in results]
    assert sorted(ranks) == [1, 2, 3]


def test_leaderboard_sorting():
    """Leaderboard should be sorted by survival_rate desc, then avg_pnl desc."""
    random.seed(42)
    np.random.seed(42)

    t = Tournament(rounds_per_match=3)
    # Use diverse archetypes so they get different survival rates
    agents = [
        AgentDNA.seed_trend_follower(),
        AgentDNA.seed_mean_reverter(),
        AgentDNA.seed_conservative(),
        AgentDNA.seed_aggressive(),
    ]
    for a in agents:
        t.add_contestant(a)

    t.run()
    leaderboard = t.get_leaderboard()
    assert len(leaderboard) == 4

    # Verify sorting: each entry should have survival >= next entry
    for i in range(len(leaderboard) - 1):
        curr = leaderboard[i]
        nxt = leaderboard[i + 1]
        assert (curr["survival_rate"], curr["avg_pnl"]) >= (
            nxt["survival_rate"],
            nxt["avg_pnl"],
        ), f"Leaderboard not sorted at position {i}"


def test_seed_archetypes_compete():
    """Trend follower, mean reverter, and scalper (aggressive) should all compete."""
    random.seed(123)
    np.random.seed(123)

    t = Tournament(rounds_per_match=3)
    trend = AgentDNA.seed_trend_follower()
    mean_rev = AgentDNA.seed_mean_reverter()
    scalper = AgentDNA.seed_aggressive()  # aggressive = scalper archetype

    t.add_contestant(trend)
    t.add_contestant(mean_rev)
    t.add_contestant(scalper)

    results = t.run()
    assert len(results) == 3

    # All agents should have participated in 2 matches each (round-robin with 3 agents)
    for r in results:
        total_games = r.wins + r.losses + r.draws
        assert total_games == 2, (
            f"Agent {r.agent_id} played {total_games} matches, expected 2"
        )


def test_single_agent_tournament():
    """Tournament with a single agent should still produce a valid result."""
    random.seed(42)
    np.random.seed(42)

    t = Tournament(rounds_per_match=3)
    solo = AgentDNA.seed_conservative()
    t.add_contestant(solo)

    results = t.run()
    assert len(results) == 1
    assert results[0].agent_id == solo.id
    assert results[0].rank == 1
    assert results[0].wins == 0
    assert results[0].losses == 0
    assert results[0].draws == 0


def test_get_matchup():
    """get_matchup should return details for a specific head-to-head pair."""
    random.seed(42)
    np.random.seed(42)

    t = Tournament(rounds_per_match=3)
    a = AgentDNA.seed_trend_follower()
    b = AgentDNA.seed_mean_reverter()
    t.add_contestant(a)
    t.add_contestant(b)

    t.run()

    matchup = t.get_matchup(a.id, b.id)
    assert matchup, "Matchup should not be empty"
    assert "agent_a" in matchup
    assert "agent_b" in matchup
    assert "survival_a" in matchup
    assert "survival_b" in matchup
    assert "pnl_a" in matchup
    assert "pnl_b" in matchup
    assert "winner" in matchup

    # Reverse lookup should also work
    matchup_rev = t.get_matchup(b.id, a.id)
    assert matchup_rev == matchup

    # Non-existent matchup
    empty = t.get_matchup("fake_id_1", "fake_id_2")
    assert empty == {}


def test_json_output_structure():
    """Leaderboard dicts should have the correct keys and types."""
    random.seed(42)
    np.random.seed(42)

    t = Tournament(rounds_per_match=3)
    for _ in range(3):
        t.add_contestant(AgentDNA.random())

    t.run()
    leaderboard = t.get_leaderboard()

    expected_keys = {"agent_id", "wins", "losses", "draws", "survival_rate", "avg_pnl", "rank"}
    for entry in leaderboard:
        assert set(entry.keys()) == expected_keys
        assert isinstance(entry["agent_id"], str)
        assert isinstance(entry["wins"], int)
        assert isinstance(entry["losses"], int)
        assert isinstance(entry["draws"], int)
        assert isinstance(entry["survival_rate"], float)
        assert isinstance(entry["avg_pnl"], float)
        assert isinstance(entry["rank"], int)
        assert entry["rank"] >= 1


def test_tournament_result_dataclass():
    """TournamentResult dataclass should serialize correctly."""
    r = TournamentResult(
        agent_id="test123",
        wins=3,
        losses=1,
        draws=0,
        survival_rate=0.75,
        avg_pnl=-0.0123,
        rank=2,
    )
    d = r.to_dict()
    assert d["agent_id"] == "test123"
    assert d["wins"] == 3
    assert d["losses"] == 1
    assert d["draws"] == 0
    assert d["survival_rate"] == 0.75
    assert d["avg_pnl"] == -0.0123
    assert d["rank"] == 2
