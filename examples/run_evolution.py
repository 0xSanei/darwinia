"""Basic evolution example — evolve trading agents on BTC data."""

import random
import numpy as np
from darwinia.core.market import MarketEnvironment
from darwinia.evolution.engine import EvolutionEngine


def main():
    random.seed(42)
    np.random.seed(42)

    # Load market data
    market = MarketEnvironment('data')
    candles = market.load_csv('btc_1h.csv')
    print(f"Loaded {len(candles)} candles")

    # Configure evolution
    config = {
        'population_size': 50,
        'seed_ratio': 0.2,
        'arena': {'rounds_per_test': 3},
        'arena_start_gen': 5,
        'output_dir': 'output',
    }

    engine = EvolutionEngine(config)
    engine.load_data(candles)

    def progress(gen, stats):
        print(
            f"Gen {gen:3d} | "
            f"Champion: {stats['champion_fitness']:+.4f} | "
            f"Avg: {stats['avg_fitness']:+.4f} | "
            f"Diversity: {stats['genetic_diversity']:.3f}"
        )

    # Run evolution
    results = engine.run(generations=50, callback=progress)
    engine.recorder.save_summary()
    engine.recorder.save_final_report(results)

    print(f"\nEvolution complete!")
    print(f"Patterns discovered: {len(results['patterns_discovered'])}")
    print(f"Results saved to output/")


if __name__ == '__main__':
    main()
