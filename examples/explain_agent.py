"""Gene ablation example — understand WHY an agent works."""
from darwinia.core.dna import AgentDNA
from darwinia.core.market import MarketEnvironment
from darwinia.discovery.explainer import GeneExplainer


def main():
    market = MarketEnvironment('data')
    candles = market.load_csv('btc_1h.csv')[:2000]

    archetypes = {
        'Trend Follower': AgentDNA.seed_trend_follower(),
        'Mean Reverter': AgentDNA.seed_mean_reverter(),
        'Conservative': AgentDNA.seed_conservative(),
        'Aggressive': AgentDNA.seed_aggressive(),
    }

    explainer = GeneExplainer()
    for name, dna in archetypes.items():
        report = explainer.explain(dna, candles)
        print(f"\n{'='*50}")
        print(f"{name} (fitness: {report.base_fitness:.4f})")
        print(f"Risk: {report.risk_profile}")
        print(f"Strategy: {report.strategy_summary}")
        print(f"Top genes: {', '.join(report.top_genes[:3])}")


if __name__ == '__main__':
    main()
