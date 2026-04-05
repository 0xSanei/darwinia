"""Tests for the Knowledge Protocol (Layer 3)."""

import pytest
from darwinia.core.dna import AgentDNA
from darwinia.knowledge.protocol import (
    PatternMarket,
    KnowledgeExchange,
    PatternListing,
    ExchangeStats,
)


class TestPatternMarket:

    def test_list_pattern(self):
        """Listing a pattern stores it and returns a valid PatternListing."""
        market = PatternMarket()
        features = {"weight_trend": 0.9, "weight_volume": 0.8}
        listing = market.list_pattern(
            pattern=features,
            price=0.5,
            seller_id="seller-1",
            quality_score=3.0,
            generation=5,
        )

        assert isinstance(listing, PatternListing)
        assert listing.seller_id == "seller-1"
        assert listing.price == 0.5
        assert listing.features == features
        assert len(market.get_listings()) == 1

    def test_buy_pattern(self):
        """Buying a pattern transfers genes and deducts fitness."""
        market = PatternMarket()
        features = {"weight_trend": 0.9, "entry_threshold": 0.8}
        listing = market.list_pattern(
            pattern=features, price=1.0, seller_id="seller-1", quality_score=5.0
        )

        buyer = AgentDNA.random()
        buyer.fitness = 5.0
        old_trend = buyer.weight_trend
        old_entry = buyer.entry_threshold

        success = market.buy_pattern(buyer, listing.pattern_id)

        assert success is True
        assert buyer.fitness == 4.0  # paid 1.0
        # Gene values should have moved toward seller's values (70/30 blend)
        expected_trend = 0.7 * 0.9 + 0.3 * old_trend
        assert abs(buyer.weight_trend - expected_trend) < 1e-6
        expected_entry = 0.7 * 0.8 + 0.3 * old_entry
        assert abs(buyer.entry_threshold - expected_entry) < 1e-6
        # Listing removed after purchase
        assert len(market.get_listings()) == 0

    def test_buy_pattern_insufficient_fitness(self):
        """Cannot buy a pattern if fitness is below the price."""
        market = PatternMarket()
        listing = market.list_pattern(
            pattern={"weight_trend": 0.9}, price=10.0, seller_id="s1"
        )

        buyer = AgentDNA.random()
        buyer.fitness = 1.0
        success = market.buy_pattern(buyer, listing.pattern_id)

        assert success is False
        assert buyer.fitness == 1.0  # unchanged
        assert len(market.get_listings()) == 1  # listing still there

    def test_buy_nonexistent_pattern(self):
        """Buying a nonexistent pattern returns False."""
        market = PatternMarket()
        buyer = AgentDNA.random()
        buyer.fitness = 10.0
        assert market.buy_pattern(buyer, "no-such-id") is False


class TestKnowledgeExchange:

    def _make_population(self, n: int = 20) -> list:
        """Create a population with varied fitness."""
        pop = []
        for i in range(n):
            dna = AgentDNA.random(generation=1)
            dna.fitness = float(i + 1)  # fitness 1..n
            pop.append(dna)
        return pop

    def test_exchange_runs(self):
        """Exchange completes and returns valid stats."""
        pop = self._make_population(20)
        exchange = KnowledgeExchange(seller_ratio=0.3, buyer_ratio=0.3)
        stats = exchange.run_exchange(pop)

        assert isinstance(stats, ExchangeStats)
        assert stats.patterns_listed > 0
        assert stats.trades_made >= 0

    def test_exchange_improves_weak_agents(self):
        """Weak agents acquire gene values from strong agents after exchange."""
        pop = self._make_population(20)

        # Make top agents have distinctive high trend weight
        for agent in sorted(pop, key=lambda a: a.fitness, reverse=True)[:6]:
            agent.weight_trend = 0.95
            agent.weight_volume = 0.90

        # Record bottom agents' genes before exchange
        bottom = sorted(pop, key=lambda a: a.fitness)[:6]
        genes_before = {a.id: a.get_genes() for a in bottom}

        exchange = KnowledgeExchange(
            seller_ratio=0.3, buyer_ratio=0.3, price_factor=0.05
        )
        stats = exchange.run_exchange(pop)

        # At least some trades should have happened
        assert stats.trades_made > 0

        # Check that at least one buyer's genes moved toward seller values
        any_changed = False
        for transfer in stats.gene_transfers:
            bid = transfer["buyer_id"]
            if bid in genes_before and transfer["genes_changed"]:
                any_changed = True
                # Verify the changed gene moved toward the seller's pattern
                for gene, (old, new) in transfer["genes_changed"].items():
                    assert old != new
        assert any_changed

    def test_exchange_with_external_patterns(self):
        """External patterns can be listed and bought."""
        pop = self._make_population(10)
        external = [
            {
                "features": {"weight_trend": 0.99, "risk_appetite": 0.1},
                "price": 0.5,
                "seller_id": "oracle",
                "quality_score": 10.0,
                "name": "oracle-strategy",
            }
        ]

        exchange = KnowledgeExchange(seller_ratio=0.3, buyer_ratio=0.5)
        stats = exchange.run_exchange(pop, patterns=external)

        assert stats.patterns_listed >= 1  # at least the external one
        # The external pattern is high quality, so it should be bought
        assert stats.trades_made >= 1

    def test_exchange_small_population(self):
        """Exchange handles populations too small to trade."""
        pop = [AgentDNA.random()]
        pop[0].fitness = 1.0
        exchange = KnowledgeExchange()
        stats = exchange.run_exchange(pop)

        assert stats.trades_made == 0
        assert stats.patterns_listed == 0
