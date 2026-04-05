"""Walk-forward validation example — detect overfitting."""
from darwinia.core.market import MarketEnvironment
from darwinia.validation.walk_forward import WalkForwardValidator


def main():
    market = MarketEnvironment('data')
    candles = market.load_csv('btc_1h.csv')

    config = {'population_size': 30, 'seed_ratio': 0.2, 'arena_start_gen': 5}
    validator = WalkForwardValidator(n_windows=3)
    result = validator.validate(candles, config, generations=15)

    # Print results...
    for w in result.windows:
        print(f"Window {w.window_id}: train={w.train_fitness:.4f} test={w.test_fitness:.4f} deg={w.degradation:+.4f}")
    print(f"\nOverfit score: {result.overfit_score:.1%}")
    print(f"Robust: {result.is_robust}")


if __name__ == '__main__':
    main()
