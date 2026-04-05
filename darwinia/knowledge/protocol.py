"""
Knowledge Protocol (Layer 3) — agents trade discovered patterns with each other.

Provides a marketplace where fit agents can sell their gene patterns to
less fit agents, enabling knowledge transfer beyond breeding/crossover.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from ..core.dna import AgentDNA


@dataclass
class PatternListing:
    """A pattern listed for sale on the market."""
    pattern_id: str
    pattern_name: str
    seller_id: str
    features: Dict[str, float]  # gene values that define this pattern
    quality_score: float  # predictive power / fitness of seller
    price: float  # fitness cost to buyer
    generation: int


@dataclass
class ExchangeStats:
    """Summary of a knowledge exchange round."""
    trades_made: int = 0
    patterns_listed: int = 0
    avg_fitness_before: float = 0.0
    avg_fitness_after: float = 0.0
    gene_transfers: List[Dict] = field(default_factory=list)


class PatternMarket:
    """Marketplace where agents list and buy discovered patterns."""

    def __init__(self) -> None:
        self.listings: Dict[str, PatternListing] = {}

    def list_pattern(
        self,
        pattern: Dict[str, float],
        price: float,
        seller_id: str,
        quality_score: float = 0.0,
        pattern_name: str = "",
        generation: int = 0,
    ) -> PatternListing:
        """List a discovered pattern for sale."""
        pid = str(uuid.uuid4())[:8]
        listing = PatternListing(
            pattern_id=pid,
            pattern_name=pattern_name or f"pattern-{pid}",
            seller_id=seller_id,
            features=dict(pattern),
            quality_score=quality_score,
            price=price,
            generation=generation,
        )
        self.listings[pid] = listing
        return listing

    def buy_pattern(self, buyer_dna: AgentDNA, pattern_id: str) -> bool:
        """
        Buy a pattern: inject seller's gene values into buyer's DNA.

        The buyer pays with fitness points and receives a partial gene
        transfer — only the genes specified in the pattern's features.
        Returns True if the purchase succeeded.
        """
        listing = self.listings.get(pattern_id)
        if listing is None:
            return False

        if buyer_dna.fitness < listing.price:
            return False

        # Pay fitness cost
        buyer_dna.fitness -= listing.price

        # Inject seller's gene values (partial transfer)
        for gene_name, gene_value in listing.features.items():
            if gene_name in AgentDNA.GENE_FIELDS:
                old_val = getattr(buyer_dna, gene_name)
                # Blend: 70% seller pattern, 30% buyer original
                blended = 0.7 * gene_value + 0.3 * old_val
                setattr(buyer_dna, gene_name, float(np.clip(blended, 0.0, 1.0)))

        # Remove listing after purchase
        del self.listings[pattern_id]
        return True

    def get_listings(self) -> List[PatternListing]:
        """Return all active listings sorted by quality descending."""
        return sorted(
            self.listings.values(),
            key=lambda l: l.quality_score,
            reverse=True,
        )

    def clear(self) -> None:
        """Remove all listings."""
        self.listings.clear()


class KnowledgeExchange:
    """
    Orchestrates pattern trading between agents after evolution.

    Top agents list their gene patterns; bottom agents buy them.
    This creates knowledge flow from fit to unfit agents.
    """

    def __init__(
        self,
        seller_ratio: float = 0.3,
        buyer_ratio: float = 0.3,
        price_factor: float = 0.1,
        pattern_genes: Optional[List[str]] = None,
    ) -> None:
        self.seller_ratio = seller_ratio
        self.buyer_ratio = buyer_ratio
        self.price_factor = price_factor
        # Which genes to include in patterns (default: signal + threshold genes)
        self.pattern_genes = pattern_genes or [
            "weight_price_momentum", "weight_volume", "weight_volatility",
            "weight_mean_reversion", "weight_trend",
            "entry_threshold", "exit_threshold",
            "stop_loss_pct", "take_profit_pct",
        ]
        self.market = PatternMarket()

    def run_exchange(
        self,
        population: List[AgentDNA],
        patterns: Optional[List[Dict]] = None,
    ) -> ExchangeStats:
        """
        Run a knowledge exchange round.

        Args:
            population: list of AgentDNA (must have fitness set)
            patterns: optional pre-discovered patterns to list;
                      if None, extracts patterns from top agents' genes

        Returns:
            ExchangeStats with trade details
        """
        self.market.clear()
        stats = ExchangeStats()

        if len(population) < 4:
            return stats

        sorted_pop = sorted(population, key=lambda a: a.fitness, reverse=True)
        n = len(sorted_pop)
        n_sellers = max(1, int(n * self.seller_ratio))
        n_buyers = max(1, int(n * self.buyer_ratio))

        sellers = sorted_pop[:n_sellers]
        buyers = sorted_pop[-n_buyers:]

        # Record pre-exchange fitness for buyers
        stats.avg_fitness_before = float(np.mean([b.fitness for b in buyers]))

        # Sellers list their patterns
        for seller in sellers:
            features = {g: getattr(seller, g) for g in self.pattern_genes
                        if g in AgentDNA.GENE_FIELDS}
            price = max(0.01, seller.fitness * self.price_factor)
            self.market.list_pattern(
                pattern=features,
                price=price,
                seller_id=seller.id,
                quality_score=seller.fitness,
                pattern_name=f"strategy-{seller.id}",
                generation=seller.generation,
            )

        # Also list any externally discovered patterns
        if patterns:
            for p in patterns:
                self.market.list_pattern(
                    pattern=p.get("features", {}),
                    price=p.get("price", 0.1),
                    seller_id=p.get("seller_id", "external"),
                    quality_score=p.get("quality_score", 0.5),
                    pattern_name=p.get("name", "external-pattern"),
                    generation=p.get("generation", 0),
                )

        stats.patterns_listed = len(self.market.listings)

        # Buyers attempt to purchase the best available pattern
        for buyer in buyers:
            available = self.market.get_listings()
            if not available:
                break

            # Pick the best affordable listing
            for listing in available:
                if listing.seller_id == buyer.id:
                    continue  # don't buy own pattern
                if buyer.fitness >= listing.price:
                    genes_before = buyer.get_genes()
                    success = self.market.buy_pattern(buyer, listing.pattern_id)
                    if success:
                        stats.trades_made += 1
                        genes_after = buyer.get_genes()
                        changed = {
                            g: (genes_before[g], genes_after[g])
                            for g in genes_before
                            if abs(genes_before[g] - genes_after[g]) > 1e-6
                        }
                        stats.gene_transfers.append({
                            "buyer_id": buyer.id,
                            "seller_id": listing.seller_id,
                            "genes_changed": changed,
                        })
                        break

        stats.avg_fitness_after = float(np.mean([b.fitness for b in buyers]))
        return stats
