"""Benchmark: compare seed archetype performance across market conditions."""
import json, time
import numpy as np
from darwinia.core.dna import AgentDNA
from darwinia.core.agent import TradingAgent
from darwinia.core.market import MarketEnvironment
from darwinia.evolution.fitness import FitnessEvaluator
from darwinia.arena.arena import AdversarialArena


def main():
    market = MarketEnvironment('data')
    candles = market.load_csv('btc_1h.csv')
    evaluator = FitnessEvaluator()

    archetypes = {
        'trend_follower': AgentDNA.seed_trend_follower(),
        'mean_reverter': AgentDNA.seed_mean_reverter(),
        'conservative': AgentDNA.seed_conservative(),
        'aggressive': AgentDNA.seed_aggressive(),
        'random': AgentDNA.random(generation=0),
    }

    results = {}
    print("Archetype Benchmark")
    print("=" * 70)

    for name, dna in archetypes.items():
        # Backtest fitness
        agent = TradingAgent(dna)
        trades = agent.run(candles[:2000])
        fitness = evaluator.evaluate(trades)

        # Arena survival
        arena = AdversarialArena({'rounds_per_test': 5})
        survival = arena.test_agent(dna, normal_data=None)

        results[name] = {
            'fitness': round(fitness.composite, 4),
            'sharpe': round(fitness.sharpe_ratio, 4),
            'max_drawdown': round(fitness.max_drawdown, 4),
            'win_rate': round(fitness.win_rate, 4),
            'trades': fitness.num_trades,
            'survival_rate': round(survival, 4),
        }

        print(f"{name:20s} | fitness={fitness.composite:+.4f} | sharpe={fitness.sharpe_ratio:+.4f} | "
              f"dd={fitness.max_drawdown:.2%} | wr={fitness.win_rate:.0%} | "
              f"trades={fitness.num_trades:3d} | survival={survival:.0%}")

    # Save results
    with open('benchmarks/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to benchmarks/results.json")


if __name__ == '__main__':
    main()
