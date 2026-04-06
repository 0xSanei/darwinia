"""
Skill Bridge — composability interface for Darwinia.

SkillBridge: lets external skills call Darwinia capabilities programmatically.
SkillRegistry: lets Darwinia discover and call external skills.

This module enables two-way interop between Darwinia and the broader
ClawHub / OpenClaw / Claude Code skill ecosystem.
"""

from __future__ import annotations

import copy
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from ..core.dna import AgentDNA
from ..personality.regime import RegimeDetector, MarketRegime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Integration template definitions
# ---------------------------------------------------------------------------

@dataclass
class IntegrationTemplate:
    """Describes how an external skill plugs into Darwinia."""

    name: str
    description: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    hook_point: str  # where in the pipeline this integration fires

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "hook_point": self.hook_point,
        }


# Built-in integration templates for known skills
INTEGRATION_TEMPLATES: Dict[str, IntegrationTemplate] = {
    "macro-liquidity": IntegrationTemplate(
        name="macro-liquidity",
        description=(
            "Pull macro liquidity signals (Fed Net Liquidity, SOFR, MOVE, "
            "Yen Carry) to bias evolution fitness weights. When liquidity is "
            "contracting, evolution penalizes aggressive strategies harder."
        ),
        input_schema={
            "fed_net_liquidity": "float — current Fed net liquidity in trillions",
            "sofr_rate": "float — SOFR overnight rate",
            "move_index": "float — MOVE treasury volatility index",
            "yen_carry_signal": "str — 'risk_on' | 'risk_off' | 'neutral'",
        },
        output_schema={
            "risk_multiplier": "float — scale factor for risk_appetite gene fitness",
            "aggression_penalty": "float — additional penalty for aggressive archetypes",
        },
        hook_point="pre_fitness_evaluation",
    ),
    "crypto-market-rank": IntegrationTemplate(
        name="crypto-market-rank",
        description=(
            "Auto-select trending assets for multi-asset evolution. Pulls "
            "top trending tokens, social hype ranks, and smart money inflow "
            "to decide which assets Darwinia should evolve strategies for."
        ),
        input_schema={
            "category": "str — 'trending' | 'smart_money' | 'social_hype' | 'meme'",
            "limit": "int — number of tokens to return",
            "chain": "str — optional chain filter (e.g. 'base', 'solana')",
        },
        output_schema={
            "tokens": "List[dict] — ranked tokens with symbol, rank, score",
            "recommended_pairs": "List[str] — trading pairs for evolution",
        },
        hook_point="pre_evolution_setup",
    ),
    "okx-dex-market": IntegrationTemplate(
        name="okx-dex-market",
        description=(
            "Fetch real-time on-chain price data (OHLCV candles, trade "
            "history) from OKX DEX aggregator. Provides live data feed "
            "for evolution and walk-forward validation."
        ),
        input_schema={
            "token_address": "str — token contract address",
            "chain": "str — chain identifier (e.g. 'base', 'solana')",
            "interval": "str — candle interval ('1m', '5m', '1h', '4h', '1d')",
            "limit": "int — number of candles to fetch",
        },
        output_schema={
            "candles": "np.ndarray — OHLCV array shape (N, 6)",
            "last_price": "float — most recent trade price",
            "volume_24h": "float — 24h trading volume in USD",
        },
        hook_point="data_ingestion",
    ),
}


# ---------------------------------------------------------------------------
# SkillBridge — inbound API (other skills call Darwinia)
# ---------------------------------------------------------------------------

class SkillBridge:
    """Programmatic interface for other skills to use Darwinia.

    Provides a clean dict-in / dict-out API so any skill (or agent)
    can invoke evolution, evaluate strategies, and query results
    without touching Darwinia internals.

    Example usage from another skill::

        from darwinia.integrations import SkillBridge

        bridge = SkillBridge()
        result = bridge.evolve({
            "generations": 20,
            "population_size": 30,
            "data_path": "data/btc_1h.csv",
        })
        champion = bridge.get_champion()
    """

    def __init__(self) -> None:
        self._engine = None
        self._last_results: Optional[dict] = None
        self._candles: Optional[np.ndarray] = None
        self._regime_detector = RegimeDetector()

    # -- core API ---------------------------------------------------------

    def evolve(self, config: dict) -> dict:
        """Run evolution with the given config and return results.

        Args:
            config: Evolution parameters. Supported keys:
                - generations (int): number of generations, default 20
                - population_size (int): agents per generation, default 30
                - data_path (str): path to CSV market data
                - data (np.ndarray): raw OHLCV array (alternative to data_path)
                - arena_start_gen (int): when to enable adversarial arena
                - seed_ratio (float): fraction of population seeded

        Returns:
            dict with keys: champion, evolution_summary, patterns,
            generations (list of per-gen stats).
        """
        from ..core.market import MarketEnvironment
        from ..evolution.engine import EvolutionEngine

        generations = config.get("generations", 20)
        pop_size = config.get("population_size", 30)
        arena_start = config.get("arena_start_gen", 5)
        seed_ratio = config.get("seed_ratio", 0.2)
        output_dir = config.get("output_dir", "output")

        engine_config = {
            "population_size": pop_size,
            "seed_ratio": seed_ratio,
            "arena_start_gen": arena_start,
            "output_dir": output_dir,
        }

        self._engine = EvolutionEngine(engine_config)

        # Load data from array or file path
        if "data" in config and config["data"] is not None:
            candles = np.asarray(config["data"])
        elif "data_path" in config:
            data_dir = os.path.dirname(config["data_path"]) or "."
            data_file = os.path.basename(config["data_path"])
            market = MarketEnvironment(data_dir)
            candles = market.load_csv(data_file)
        else:
            raise ValueError("config must include 'data' (ndarray) or 'data_path' (str)")

        self._candles = candles
        self._engine.load_data(candles)
        results = self._engine.run(generations=generations)
        self._last_results = results

        # Build return dict
        last_gen = results["generations"][-1] if results["generations"] else {}
        champion_dict = results["champions"][-1] if results["champions"] else {}

        return {
            "champion": champion_dict,
            "evolution_summary": {
                "generations_run": generations,
                "population_size": pop_size,
                "final_champion_fitness": round(last_gen.get("champion_fitness", 0), 4),
                "final_avg_fitness": round(last_gen.get("avg_fitness", 0), 4),
                "genetic_diversity": round(last_gen.get("genetic_diversity", 0), 4),
                "patterns_discovered": len(results.get("patterns_discovered", [])),
            },
            "patterns": results.get("patterns_discovered", []),
        }

    def get_champion(self, generation: int = -1) -> dict:
        """Get champion agent DNA and stats for a given generation.

        Args:
            generation: generation index (-1 for latest).

        Returns:
            dict with keys: id, generation, genes, fitness, lineage.

        Raises:
            RuntimeError: if no evolution has been run yet.
        """
        if self._last_results is None:
            raise RuntimeError("No evolution results available. Call evolve() first.")

        champions = self._last_results.get("champions", [])
        if not champions:
            raise RuntimeError("Evolution produced no champions.")

        try:
            champ = champions[generation]
        except IndexError:
            raise RuntimeError(
                f"Generation {generation} out of range. "
                f"Available: {len(champions)} generations."
            )
        return {
            "id": champ.get("id", "unknown"),
            "generation": champ.get("generation", 0),
            "genes": champ.get("genes", {}),
            "fitness": champ.get("fitness", 0.0),
            "lineage": champ.get("parent_ids", []),
        }

    def evaluate_strategy(self, dna: List[float]) -> dict:
        """Evaluate an arbitrary strategy DNA vector.

        Args:
            dna: list of 17 floats in [0, 1] — one per gene in GENE_FIELDS order.

        Returns:
            dict with keys: fitness, trades, risk_profile, genes.

        Raises:
            ValueError: if dna length != 17.
        """
        from ..core.agent import TradingAgent
        from ..evolution.fitness import FitnessEvaluator

        if len(dna) != len(AgentDNA.GENE_FIELDS):
            raise ValueError(
                f"DNA must have {len(AgentDNA.GENE_FIELDS)} genes, got {len(dna)}"
            )

        # Build AgentDNA from raw vector
        agent_dna = AgentDNA()
        for i, gene_name in enumerate(AgentDNA.GENE_FIELDS):
            setattr(agent_dna, gene_name, float(np.clip(dna[i], 0.0, 1.0)))

        result = {
            "genes": agent_dna.get_genes(),
            "gene_names": list(AgentDNA.GENE_FIELDS),
        }

        # If we have candles from a prior evolve(), evaluate fitness
        if self._candles is not None:
            agent = TradingAgent(agent_dna)
            trades = agent.run(self._candles)
            evaluator = FitnessEvaluator()
            score = evaluator.evaluate(trades)
            result["fitness"] = round(score.composite, 4)
            result["num_trades"] = score.num_trades
            result["sharpe_ratio"] = round(score.sharpe_ratio, 4)
            result["max_drawdown"] = round(score.max_drawdown, 4)
            result["win_rate"] = round(score.win_rate, 4)
        else:
            result["fitness"] = None
            result["note"] = "No market data loaded. Call evolve() first to enable fitness evaluation."

        return result

    def get_market_regime(self) -> dict:
        """Detect the current market regime from loaded data.

        Returns:
            dict with keys: regime, confidence, momentum, volatility,
            trend_strength.

        Raises:
            RuntimeError: if no market data is loaded.
        """
        if self._candles is None:
            raise RuntimeError("No market data loaded. Call evolve() first.")

        state = self._regime_detector.detect(self._candles)
        return {
            "regime": state.regime.value,
            "confidence": round(state.confidence, 4),
            "momentum": round(state.momentum, 4),
            "volatility": round(state.volatility, 4),
            "trend_strength": round(state.trend_strength, 4),
        }

    def get_integration_templates(self) -> Dict[str, dict]:
        """Return all built-in integration templates as dicts."""
        return {k: v.to_dict() for k, v in INTEGRATION_TEMPLATES.items()}


# ---------------------------------------------------------------------------
# SkillRegistry — outbound calls (Darwinia calls other skills)
# ---------------------------------------------------------------------------

class SkillRegistry:
    """Registry for discovering and calling external skills from Darwinia.

    Allows Darwinia's evolution pipeline to pull data or signals from
    other skills in the ClawHub / OpenClaw ecosystem.

    Example::

        registry = SkillRegistry()

        # Register a macro liquidity provider
        registry.register("macro-liquidity", my_macro_func)

        # Later, during evolution:
        macro = registry.call("macro-liquidity", indicator="fed_net_liquidity")
    """

    def __init__(self) -> None:
        self._skills: Dict[str, Callable[..., dict]] = {}
        self._call_log: List[dict] = []

    def register(self, skill_name: str, endpoint: Callable[..., dict]) -> None:
        """Register an external skill endpoint.

        Args:
            skill_name: unique name for the skill (e.g. "macro-liquidity").
            endpoint: callable that accepts **kwargs and returns a dict.

        Raises:
            TypeError: if endpoint is not callable.
        """
        if not callable(endpoint):
            raise TypeError(f"endpoint must be callable, got {type(endpoint).__name__}")
        self._skills[skill_name] = endpoint
        logger.info("Registered skill: %s", skill_name)

    def unregister(self, skill_name: str) -> None:
        """Remove a registered skill.

        Args:
            skill_name: name of the skill to remove.

        Raises:
            KeyError: if skill_name is not registered.
        """
        if skill_name not in self._skills:
            raise KeyError(f"Skill '{skill_name}' is not registered")
        del self._skills[skill_name]

    def call(self, skill_name: str, **kwargs: Any) -> dict:
        """Call a registered skill by name.

        Args:
            skill_name: name of the skill to call.
            **kwargs: arguments forwarded to the skill endpoint.

        Returns:
            dict result from the skill endpoint.

        Raises:
            KeyError: if skill_name is not registered.
        """
        if skill_name not in self._skills:
            raise KeyError(f"Skill '{skill_name}' is not registered. Available: {self.list_skills()}")

        result = self._skills[skill_name](**kwargs)
        self._call_log.append({
            "skill": skill_name,
            "kwargs": {k: str(v) for k, v in kwargs.items()},
            "success": True,
        })
        return result

    def list_skills(self) -> List[str]:
        """List all registered skill names."""
        return sorted(self._skills.keys())

    def has_skill(self, skill_name: str) -> bool:
        """Check if a skill is registered."""
        return skill_name in self._skills

    def get_call_log(self) -> List[dict]:
        """Return the history of skill calls made through this registry."""
        return list(self._call_log)

    def get_template(self, skill_name: str) -> Optional[dict]:
        """Get the integration template for a known skill, if available.

        Args:
            skill_name: name of the skill.

        Returns:
            Template dict or None if no template exists.
        """
        tmpl = INTEGRATION_TEMPLATES.get(skill_name)
        return tmpl.to_dict() if tmpl else None

    def list_templates(self) -> List[str]:
        """List all built-in integration template names."""
        return sorted(INTEGRATION_TEMPLATES.keys())
