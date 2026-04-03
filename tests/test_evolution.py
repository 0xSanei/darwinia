"""Tests for Evolution Engine."""

import random
import numpy as np
from darwinia.core.dna import AgentDNA
from darwinia.core.agent import TradingAgent
from darwinia.evolution.population import Population
from darwinia.evolution.fitness import FitnessEvaluator
from darwinia.evolution.engine import EvolutionEngine


def test_population_init():
    """Population should initialize with correct size."""
    pop = Population(size=20, seed_ratio=0.2)
    assert len(pop.agents) == 20
    assert pop.generation == 0


def test_agent_produces_trades():
    """TradingAgent should produce trades on synthetic data."""
    random.seed(42)
    np.random.seed(42)

    dna = AgentDNA.seed_aggressive()
    agent = TradingAgent(dna)

    # Generate synthetic uptrend data
    n = 300
    prices = 100 * np.cumprod(1 + np.random.randn(n) * 0.01)
    candles = np.column_stack([
        np.arange(n),           # timestamp
        prices * 0.999,         # open
        prices * 1.005,         # high
        prices * 0.995,         # low
        prices,                 # close
        np.random.uniform(100, 1000, n),  # volume
    ])

    trades = agent.run(candles)
    assert len(trades) > 0, "Agent should produce at least some trades"


def test_fitness_evaluator():
    """Fitness evaluator should return reasonable scores."""
    from darwinia.core.types import TradeResult

    trades = [
        TradeResult(entry_price=100, exit_price=110, pnl=100, pnl_pct=0.10,
                    entry_time=0, exit_time=1, direction='long'),
        TradeResult(entry_price=110, exit_price=105, pnl=-50, pnl_pct=-0.045,
                    entry_time=2, exit_time=3, direction='long'),
        TradeResult(entry_price=105, exit_price=115, pnl=100, pnl_pct=0.095,
                    entry_time=4, exit_time=5, direction='long'),
    ]

    evaluator = FitnessEvaluator()
    score = evaluator.evaluate(trades)

    assert score.total_pnl == 150
    assert score.win_rate > 0.5
    assert score.num_trades == 3
    assert score.composite != 0


def test_fitness_no_trades_penalty():
    """No trades should get mild penalty."""
    evaluator = FitnessEvaluator()
    score = evaluator.evaluate([])
    assert score.composite < 0


def test_evolution_fitness_improves():
    """Core test: fitness should improve over 20 generations."""
    random.seed(42)
    np.random.seed(42)

    # Load real market data
    from darwinia.core.market import MarketEnvironment
    import os

    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'btc_1h.csv')
    if not os.path.exists(data_path):
        # Generate synthetic data if real data not available
        n = 2000
        prices = 50000 * np.cumprod(1 + np.random.randn(n) * 0.005)
        candles = np.column_stack([
            np.arange(n),
            prices * 0.999,
            prices * 1.005,
            prices * 0.995,
            prices,
            np.random.uniform(100, 10000, n),
        ])
    else:
        market = MarketEnvironment(os.path.join(os.path.dirname(__file__), '..', 'data'))
        candles = market.load_csv('btc_1h.csv')

    config = {
        'population_size': 20,
        'seed_ratio': 0.3,
        'arena_start_gen': 999,  # No arena for this test
        'output_dir': 'output/test_run',
    }

    engine = EvolutionEngine(config)
    engine.load_data(candles)

    fitness_history = []

    def track_fitness(gen, stats):
        fitness_history.append(stats['champion_fitness'])

    engine.run(generations=20, callback=track_fitness)

    assert len(fitness_history) == 20

    # Check that later generations have better fitness than early ones
    early_avg = np.mean(fitness_history[:5])
    late_avg = np.mean(fitness_history[-5:])

    print(f"Early avg fitness: {early_avg:.4f}")
    print(f"Late avg fitness:  {late_avg:.4f}")

    assert late_avg >= early_avg, (
        f"Fitness should improve: early={early_avg:.4f}, late={late_avg:.4f}"
    )
