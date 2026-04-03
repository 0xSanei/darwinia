"""Adversarial arena example — test agents against attack scenarios."""

import random
import numpy as np
from darwinia.core.dna import AgentDNA
from darwinia.arena.arena import AdversarialArena


def main():
    random.seed(42)
    np.random.seed(42)

    arena = AdversarialArena({'rounds_per_test': 5})

    # Create test agents
    archetypes = {
        'Trend Follower': AgentDNA.seed_trend_follower(),
        'Mean Reverter': AgentDNA.seed_mean_reverter(),
        'Conservative': AgentDNA.seed_conservative(),
        'Aggressive': AgentDNA.seed_aggressive(),
        'Random': AgentDNA.random(),
    }

    # Dummy normal data for reference
    n = 200
    prices = 100 * np.cumprod(1 + np.random.randn(n) * 0.005)
    normal_data = np.column_stack([
        np.arange(n), prices * 0.999, prices * 1.005,
        prices * 0.995, prices, np.random.uniform(100, 1000, n),
    ])

    print("=== Adversarial Arena Results ===\n")

    for name, dna in archetypes.items():
        survival = arena.test_agent(dna, normal_data)
        print(f"{name:20s} | Survival Rate: {survival:.0%}")

    print("\n=== Attack Success by Type ===\n")
    for attack_type, results in arena.adversary.attack_success_history.items():
        if results:
            success_rate = sum(results) / len(results)
            print(f"{attack_type:20s} | Success: {success_rate:.0%} ({len(results)} tests)")


if __name__ == '__main__':
    main()
