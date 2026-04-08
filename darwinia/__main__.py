"""
CLI entry point — python -m darwinia
"""

import argparse
import sys
import json
import os
from datetime import datetime, timezone

from darwinia._version import __version__

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _run_single_evolve(args, data_dir, data_file, json_mode):
    """Run evolution on a single data file. Returns results dict."""
    import numpy as np
    from .core.market import MarketEnvironment
    from .evolution.engine import EvolutionEngine

    market = MarketEnvironment(data_dir)
    candles = market.load_csv(data_file)
    if not json_mode:
        print(f"   Loaded {len(candles)} candles from {data_file}")

    config = {
        'population_size': args.population,
        'seed_ratio': 0.2,
        'arena_start_gen': args.arena_start,
        'output_dir': args.output,
    }

    engine = EvolutionEngine(config)
    engine.load_data(candles)

    def progress(gen, stats):
        if json_mode:
            return
        champ = stats['champion_fitness']
        avg = stats['avg_fitness']
        div = stats['genetic_diversity']
        filled = max(0, min(20, int(champ * 20)))
        bar = '█' * filled + '░' * (20 - filled)
        print(f"   Gen {gen:3d} | {bar} | champ={champ:.4f} avg={avg:.4f} div={div:.3f}")

    results = engine.run(generations=args.generations, callback=progress)
    engine.recorder.save_summary()
    engine.recorder.save_final_report(results)
    return results


def _print_macro_summary(signals, json_mode):
    """Print a summary of the generated macro regime overlay."""
    from collections import Counter
    from .macro.regime import MacroRegime

    counts = Counter(s.regime for s in signals)
    total = len(signals)
    if json_mode:
        return
    print(f"   Macro Regime Overlay: {total} days")
    for regime in MacroRegime:
        n = counts.get(regime, 0)
        pct = 100.0 * n / total if total else 0
        print(f"     {regime.value:12s}: {n:4d} days ({pct:5.1f}%)")
    print()


def cmd_evolve(args):
    """Run evolution."""
    json_mode = getattr(args, 'json', False)
    multi = getattr(args, 'multi', False)
    macro_enabled = getattr(args, 'macro', False)

    # Generate macro regime overlay if requested
    macro_signals = None
    if macro_enabled:
        from .macro.regime import MacroSimulator
        sim = MacroSimulator(seed=42)
        # Use generations * 10 as proxy for number of simulated days
        n_days = max(args.generations * 10, 100)
        macro_signals = sim.generate_regime_sequence(n_days)
        if not json_mode:
            print(f"   Macro mode enabled")
            _print_macro_summary(macro_signals, json_mode)

    if multi:
        # Multi-asset mode: auto-load all CSVs in data/ directory
        from .core.market import MarketEnvironment

        data_dir = os.path.dirname(args.data) or 'data'
        market = MarketEnvironment(data_dir)
        csv_files = market.list_available()
        if not csv_files:
            print("No CSV files found in data directory.")
            return

        if not json_mode:
            print(f"🧬 Darwinia — Multi-Asset Evolution")
            print(f"   Assets: {len(csv_files)} files in {data_dir}/")
            print(f"   Generations: {args.generations} | Population: {args.population}")
            print()

        all_results = {}
        for csv_file in csv_files:
            asset_name = os.path.splitext(csv_file)[0]
            if not json_mode:
                print(f"\n── {asset_name} {'─' * (50 - len(asset_name))}")
            results = _run_single_evolve(args, data_dir, csv_file, json_mode)
            last_gen = results['generations'][-1] if results['generations'] else {}
            champ_fitness = last_gen.get('champion_fitness', 0)
            all_results[asset_name] = {
                'fitness': champ_fitness,
                'results': results,
            }

        # Report best asset
        if not all_results:
            msg = "No results generated from any asset."
            if json_mode:
                print(json.dumps({"error": msg}))
            else:
                print(f"\n  {msg}")
            return
        best_asset = max(all_results, key=lambda k: all_results[k]['fitness'])
        if json_mode:
            output = {
                "multi_asset": True,
                "assets": {
                    name: {"champion_fitness": round(info['fitness'], 4)}
                    for name, info in all_results.items()
                },
                "best_asset": best_asset,
                "best_fitness": round(all_results[best_asset]['fitness'], 4),
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"\n{'═' * 55}")
            print(f"  Multi-Asset Results:")
            for name, info in sorted(all_results.items(), key=lambda x: x[1]['fitness'], reverse=True):
                marker = " ★" if name == best_asset else ""
                print(f"    {name:20s} fitness={info['fitness']:.4f}{marker}")
            print(f"\n  Best performer: {best_asset} ({all_results[best_asset]['fitness']:.4f})")
        return

    # Single-asset mode
    if not json_mode:
        print(f"🧬 Darwinia — Evolution Engine")
        print(f"   Generations: {args.generations}")
        print(f"   Population:  {args.population}")
        print(f"   Data:        {args.data}")
        print()

    data_dir = os.path.dirname(args.data) or '.'
    data_file = os.path.basename(args.data)
    results = _run_single_evolve(args, data_dir, data_file, json_mode)

    if json_mode:
        last_gen = results['generations'][-1] if results['generations'] else {}
        champion_dict = results['champions'][-1] if results['champions'] else {}

        pop_snapshot = last_gen.get('population_snapshot', [])
        top_agents = sorted(pop_snapshot, key=lambda a: a.get('fitness', 0), reverse=True)[:5]

        output = {
            "champion": champion_dict,
            "evolution_summary": {
                "generations_run": args.generations,
                "population_size": args.population,
                "final_champion_fitness": round(last_gen.get('champion_fitness', 0), 4),
                "final_avg_fitness": round(last_gen.get('avg_fitness', 0), 4),
                "genetic_diversity": round(last_gen.get('genetic_diversity', 0), 4),
                "patterns_discovered": len(results.get('patterns_discovered', [])),
            },
            "patterns": results.get('patterns_discovered', []),
            "top_agents": top_agents,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n✅ Evolution complete!")
        print(f"   Champions saved to: {args.output}/champions/")
        print(f"   Patterns discovered: {len(results['patterns_discovered'])}")
        print(f"   Final champion fitness: {results['champions'][-1].get('fitness', 'N/A')}")


def cmd_arena(args):
    """Run adversarial arena test."""
    from .core.dna import AgentDNA
    from .arena.arena import AdversarialArena

    json_mode = getattr(args, 'json', False)

    if not json_mode:
        print(f"⚔️ Darwinia — Adversarial Arena")

    if args.champion:
        try:
            with open(args.champion) as f:
                dna = AgentDNA.from_dict(json.load(f))
        except FileNotFoundError:
            msg = f"Champion file not found: {args.champion}"
            print(json.dumps({"error": msg}) if json_mode else f"   Error: {msg}")
            return
        except json.JSONDecodeError:
            msg = f"Invalid JSON in champion file: {args.champion}"
            print(json.dumps({"error": msg}) if json_mode else f"   Error: {msg}")
            return
        if not json_mode:
            print(f"   Testing champion: {dna.id}")
    else:
        dna = AgentDNA.seed_trend_follower()
        if not json_mode:
            print(f"   Testing seed: trend_follower")

    arena = AdversarialArena({'rounds_per_test': args.rounds})
    survival = arena.test_agent(dna, normal_data=None)

    if json_mode:
        rounds = []
        for r in arena.history:
            rounds.append({
                "attack": r.trap_type,
                "pnl": round(r.alpha_pnl, 4),
                "survived": r.survived,
            })
        output = {
            "agent_id": dna.id,
            "agent_dna": dna.to_dict(),
            "survival_rate": round(survival, 4),
            "rounds": rounds,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n   Survival rate: {survival:.1%}")
        for r in arena.history:
            status = "✅ survived" if r.survived else "❌ trapped"
            print(f"   {r.trap_type:20s} | PnL: {r.alpha_pnl:+.2%} | {status}")


def cmd_validate(args):
    """Run walk-forward validation."""
    import numpy as np
    from .core.market import MarketEnvironment
    from .validation.walk_forward import WalkForwardValidator

    json_mode = getattr(args, 'json', False)

    if not json_mode:
        print(f"🔬 Darwinia — Walk-Forward Validation")
        print(f"   Windows: {args.windows} | Generations per window: {args.generations}")
        print()

    data_dir = os.path.dirname(args.data) or '.'
    data_file = os.path.basename(args.data)
    market = MarketEnvironment(data_dir)
    candles = market.load_csv(data_file)
    if not json_mode:
        print(f"   Loaded {len(candles)} candles")

    config = {
        'population_size': args.population,
        'seed_ratio': 0.2,
        'arena_start_gen': 5,
        'output_dir': args.output,
    }

    def progress(window_id, phase, info):
        if json_mode:
            return
        print(f"   Window {window_id} [{phase}]: {info.get('candles', '?')} candles")

    validator = WalkForwardValidator(n_windows=args.windows)
    result = validator.validate(
        candles, config,
        generations=args.generations,
        callback=progress,
    )

    if json_mode:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"\n   Results:")
        for w in result.windows:
            deg_marker = "⚠️" if w.degradation > 0.5 else "✅"
            print(f"   Window {w.window_id}: train={w.train_fitness:.4f} test={w.test_fitness:.4f} "
                  f"degradation={w.degradation:+.4f} {deg_marker}")
        print(f"\n   Avg train:  {result.avg_train_fitness:.4f}")
        print(f"   Avg test:   {result.avg_test_fitness:.4f}")
        print(f"   Overfit:    {result.overfit_score:.1%}")
        robust = "✅ ROBUST" if result.is_robust else "⚠️ OVERFITTING DETECTED"
        print(f"   Verdict:    {robust}")


def cmd_explain(args):
    """Run gene ablation analysis."""
    from .core.dna import AgentDNA
    from .core.market import MarketEnvironment
    from .discovery.explainer import GeneExplainer

    json_mode = getattr(args, 'json', False)

    if not json_mode:
        print(f"🔍 Darwinia — Gene Ablation Analysis")

    if args.champion:
        try:
            with open(args.champion) as f:
                dna = AgentDNA.from_dict(json.load(f))
        except FileNotFoundError:
            msg = f"Champion file not found: {args.champion}"
            print(json.dumps({"error": msg}) if json_mode else f"   Error: {msg}")
            return
        except json.JSONDecodeError:
            msg = f"Invalid JSON in champion file: {args.champion}"
            print(json.dumps({"error": msg}) if json_mode else f"   Error: {msg}")
            return
        if not json_mode:
            print(f"   Agent: {dna.id}")
    else:
        dna = AgentDNA.seed_trend_follower()
        if not json_mode:
            print(f"   Agent: seed_trend_follower")

    data_dir = os.path.dirname(args.data) or '.'
    data_file = os.path.basename(args.data)
    market = MarketEnvironment(data_dir)
    candles = market.load_csv(data_file)
    # Use a representative slice
    candles = candles[:min(2000, len(candles))]

    explainer = GeneExplainer()
    result = explainer.explain(dna, candles)

    if json_mode:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"   Base fitness: {result.base_fitness:.4f}")
        print(f"   Risk profile: {result.risk_profile}")
        print(f"   Strategy: {result.strategy_summary}")
        print(f"\n   Gene Importance (top → bottom):")
        for a in result.ablations:
            bar = "█" * int(a.importance * 15)
            sign = "+" if a.fitness_drop > 0 else "-" if a.fitness_drop < 0 else " "
            print(f"   {a.gene_name:28s} {bar:15s} {sign}{abs(a.fitness_drop):.4f}")


def cmd_fetch(args):
    """Fetch market data from exchange APIs."""
    from .data.fetcher import DataFetcher

    json_mode = getattr(args, 'json', False)
    fetcher = DataFetcher()

    source = args.source.lower()
    if not json_mode:
        print(f"📡 Darwinia — Data Fetcher")
        print(f"   Source:   {source}")

    try:
        if source == 'binance':
            if not json_mode:
                print(f"   Symbol:   {args.symbol}")
                print(f"   Interval: {args.interval}")
                print(f"   Limit:    {args.limit}")
            candles = fetcher.fetch_binance(
                symbol=args.symbol,
                interval=args.interval,
                limit=args.limit,
            )
            filename = f"{args.symbol.lower()}_{args.interval}.csv"
        elif source == 'coingecko':
            coin_id = args.symbol.lower()
            if not json_mode:
                print(f"   Coin:     {coin_id}")
                print(f"   Days:     {args.limit}")
            candles = fetcher.fetch_coingecko(
                coin_id=coin_id,
                days=args.limit,
            )
            filename = f"{coin_id}_{args.limit}d.csv"
        else:
            print(f"Unknown source: {source}. Use 'binance' or 'coingecko'.")
            return

        # Save to data/ directory
        filepath = os.path.join('data', filename)
        fetcher.save_csv(candles, filepath)

        if json_mode:
            output = {
                "source": source,
                "candles": len(candles),
                "file": filepath,
                "columns": ["timestamp", "open", "high", "low", "close", "volume"],
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"\n   Fetched {len(candles)} candles")
            print(f"   Saved to: {filepath}")

    except (ConnectionError, ValueError) as e:
        if json_mode:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"\n   Error: {e}")


def cmd_scan(args):
    """Scan for trending or volatile crypto assets."""
    from .discovery.asset_scanner import AssetScanner

    json_mode = getattr(args, 'json', False)
    scanner = AssetScanner()

    try:
        if args.recommend:
            pairs = scanner.recommend_for_evolution()
            if json_mode:
                print(json.dumps({"recommended_pairs": pairs}, indent=2))
            else:
                print("Recommended pairs for evolution:")
                for p in pairs:
                    print(f"  {p}")
            return

        if args.volatile:
            assets = scanner.scan_volatile(top_n=args.top)
            label = "Most Volatile"
        else:
            assets = scanner.scan_trending(top_n=args.top)
            label = "Trending"

        if json_mode:
            print(json.dumps({"assets": assets, "mode": label.lower()}, indent=2))
        else:
            print(f"{label} Assets (top {args.top}):")
            print(f"  {'Rank':<6}{'Symbol':<10}{'Name':<20}{'24h %':>10}{'Volume':>18}")
            print(f"  {'─' * 64}")
            for a in assets:
                chg = a['price_change_24h']
                sign = '+' if chg >= 0 else ''
                vol = f"${a['volume_24h']:,.0f}"
                print(f"  {a['market_cap_rank']:<6}{a['symbol']:<10}{a['name']:<20}"
                      f"{sign}{chg:>9.2f}%{vol:>18}")

    except ConnectionError as e:
        if json_mode:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"Error: {e}")


def cmd_tournament(args):
    """Run tournament between evolved champion agents."""
    from .core.dna import AgentDNA
    from .arena.tournament import Tournament

    json_mode = getattr(args, 'json', False)
    top_n = args.top
    generations = args.generations
    population = args.population
    rounds = args.rounds

    if not json_mode:
        print(f"Tournament Mode")
        print(f"   Evolving population for {generations} generations...")

    # Evolve a population to get champions
    from .core.market import MarketEnvironment
    from .evolution.engine import EvolutionEngine

    data_dir = os.path.dirname(args.data) or '.'
    data_file = os.path.basename(args.data)
    market = MarketEnvironment(data_dir)
    candles = market.load_csv(data_file)

    config = {
        'population_size': population,
        'seed_ratio': 0.2,
        'arena_start_gen': min(5, generations // 2),
        'output_dir': args.output,
    }

    engine = EvolutionEngine(config)
    engine.load_data(candles)

    def progress(gen, stats):
        if json_mode:
            return
        champ = stats['champion_fitness']
        avg = stats['avg_fitness']
        filled = max(0, min(20, int(champ * 20)))
        bar = chr(9608) * filled + chr(9617) * (20 - filled)
        print(f"   Gen {gen:3d} | {bar} | champ={champ:.4f} avg={avg:.4f}")

    results = engine.run(generations=generations, callback=progress)

    # Take top N agents from final population
    final_agents = sorted(
        engine.population.agents, key=lambda a: a.fitness, reverse=True
    )
    champions = final_agents[:top_n]

    if not json_mode:
        print(f"\n   Top {len(champions)} champions selected. Running tournament...")

    # Run tournament
    tournament = Tournament(rounds_per_match=rounds)
    for dna in champions:
        tournament.add_contestant(dna)

    tournament.run(verbose=not json_mode)
    leaderboard = tournament.get_leaderboard()

    if json_mode:
        output = {
            "tournament": {
                "contestants": len(champions),
                "rounds_per_match": rounds,
                "generations_evolved": generations,
            },
            "leaderboard": leaderboard,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'=' * 65}")
        print(f"  TOURNAMENT LEADERBOARD")
        print(f"{'=' * 65}")
        print(
            f"  {'Rank':<6}{'Agent':<10}{'W':>4}{'L':>4}{'D':>4}"
            f"{'Survival':>12}{'Avg PnL':>12}"
        )
        print(f"  {'-' * 58}")
        for entry in leaderboard:
            rank_str = f"#{entry['rank']}"
            survival_str = f"{entry['survival_rate']:.1%}"
            pnl_str = f"{entry['avg_pnl']:+.2%}"
            print(
                f"  {rank_str:<6}{entry['agent_id']:<10}"
                f"{entry['wins']:>4}{entry['losses']:>4}{entry['draws']:>4}"
                f"{survival_str:>12}{pnl_str:>12}"
            )
        print(f"{'=' * 65}")


def cmd_dashboard(args):
    """Launch Streamlit dashboard."""
    import subprocess
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'app.py')
    dashboard_path = os.path.abspath(dashboard_path)
    print(f"🧬 Launching Darwinia Dashboard...")
    subprocess.run(["streamlit", "run", dashboard_path, "--server.headless", "true"])


def cmd_analytics(args):
    """Run population analytics."""
    from .core.dna import AgentDNA
    from .analytics.population import PopulationAnalyzer

    json_mode = getattr(args, 'json', False)
    pop_size = args.population
    generations = args.generations

    if not json_mode:
        print(f"Darwinia -- Population Analytics")
        print(f"   Generations: {generations} | Population: {pop_size}")
        print()

    # Build a population via quick random evolution (selection + mutation)
    population = [AgentDNA.random(generation=0) for _ in range(pop_size)]

    for gen in range(generations):
        # Simple tournament selection + mutation to create realistic population
        population.sort(key=lambda a: a.fitness, reverse=True)
        # Assign synthetic fitness based on gene coherence
        for agent in population:
            genes = agent.get_genes()
            vals = list(genes.values())
            # Fitness = reward agents whose signal weights align with personality
            signal_sum = sum(vals[:5])
            personality_sum = sum(vals[9:14])
            agent.fitness = (signal_sum + personality_sum) / 10.0 + 0.1 * (1.0 - abs(vals[5] - vals[6]))

        # Selection: keep top half, breed next gen
        half = max(2, pop_size // 2)
        parents = population[:half]
        next_gen = list(parents)
        import random as _rnd
        while len(next_gen) < pop_size:
            p1 = _rnd.choice(parents)
            p2 = _rnd.choice(parents)
            child = p1.crossover(p2).mutate(mutation_rate=0.2, mutation_strength=0.08)
            child.generation = gen + 1
            next_gen.append(child)
        population = next_gen[:pop_size]

    # Final fitness assignment
    for agent in population:
        genes = agent.get_genes()
        vals = list(genes.values())
        signal_sum = sum(vals[:5])
        personality_sum = sum(vals[9:14])
        agent.fitness = (signal_sum + personality_sum) / 10.0 + 0.1 * (1.0 - abs(vals[5] - vals[6]))

    analyzer = PopulationAnalyzer(population)

    if json_mode:
        print(json.dumps(analyzer.to_dict(), indent=2))
    else:
        conv = analyzer.convergence_score()
        print(f"   Convergence score: {conv:.4f}")
        print()

        div = analyzer.diversity_metrics()
        print(f"   Mean Shannon entropy: {div['mean_entropy']:.4f}")
        print(f"   Effective population size: {div['effective_population_size']:.1f}")
        print()

        corr = analyzer.gene_correlations()
        if corr['top_pairs']:
            print(f"   Top gene correlations:")
            for pair in corr['top_pairs'][:5]:
                sign = '+' if pair['correlation'] >= 0 else ''
                print(f"     {pair['gene_a']:25s} <-> {pair['gene_b']:25s}  {sign}{pair['correlation']:.4f}")
            print()

        clusters = analyzer.cluster_agents()
        print(f"   Clusters ({len(clusters)}):")
        for i, cluster in enumerate(clusters):
            print(f"     Cluster {i}: {len(cluster)} agents")

        fdist = analyzer.fitness_distribution()
        print(f"\n   Fitness: mean={fdist['mean']:.4f}  median={fdist['median']:.4f}  std={fdist['std']:.4f}")


def cmd_repair(args):
    """Check strategy health and auto-repair if degraded."""
    import numpy as np
    from .core.dna import AgentDNA
    from .core.market import MarketEnvironment
    from .core.agent import TradingAgent
    from .evolution.fitness import FitnessEvaluator
    from .repair.monitor import HealthMonitor
    from .repair.auto_repair import AutoRepair

    json_mode = getattr(args, 'json', False)
    method = getattr(args, 'method', 'targeted')

    if not json_mode:
        print(f"Darwinia -- Self-Repair")

    # Load champion DNA
    if args.champion:
        try:
            with open(args.champion) as f:
                dna = AgentDNA.from_dict(json.load(f))
        except FileNotFoundError:
            msg = f"Champion file not found: {args.champion}"
            print(json.dumps({"error": msg}) if json_mode else f"   Error: {msg}")
            return
        except json.JSONDecodeError:
            msg = f"Invalid JSON in champion file: {args.champion}"
            print(json.dumps({"error": msg}) if json_mode else f"   Error: {msg}")
            return
        if not json_mode:
            print(f"   Agent: {dna.id}")
    else:
        dna = AgentDNA.seed_trend_follower()
        if not json_mode:
            print(f"   Agent: seed_trend_follower")

    # Load market data
    data_dir = os.path.dirname(args.data) or '.'
    data_file = os.path.basename(args.data)
    market = MarketEnvironment(data_dir)
    candles = market.load_csv(data_file)
    candles = candles[:min(2000, len(candles))]

    if not json_mode:
        print(f"   Data: {len(candles)} candles from {data_file}")
        print()

    # Evaluate current fitness
    fitness_eval = FitnessEvaluator()
    agent = TradingAgent(dna)
    trades = agent.run(candles)
    current_fitness = fitness_eval.evaluate(trades).composite

    # Health check — use stored fitness as baseline, fall back to current
    monitor = HealthMonitor(degradation_threshold=0.3)
    baseline = dna.fitness if dna.fitness > 0 else current_fitness
    monitor.set_baseline(baseline)
    health = monitor.check(current_fitness)

    if not json_mode:
        status = "HEALTHY" if health.is_healthy else "DEGRADED"
        print(f"   Health Check:")
        print(f"     Baseline fitness:  {health.fitness_baseline:.4f}")
        print(f"     Current fitness:   {health.fitness_current:.4f}")
        print(f"     Degradation:       {health.degradation_pct:.1%}")
        print(f"     Status:            {status}")
        print(f"     Diagnosis:         {health.diagnosis}")
        print()

    if health.is_healthy:
        if not json_mode:
            print(f"   Agent is healthy. No repair needed.")
        if json_mode:
            print(json.dumps({
                "health": {
                    "baseline": round(baseline, 4),
                    "current": round(current_fitness, 4),
                    "degradation_pct": round(health.degradation_pct, 4),
                    "is_healthy": True,
                },
                "repair": None,
            }, indent=2))
        return

    # Diagnose
    if not json_mode:
        print(f"   Diagnosing...")
        diagnosis = monitor.diagnose(dna, candles)
        print(f"   {diagnosis}")
        print()

    # Repair
    if not json_mode:
        print(f"   Repairing (method={method})...")

    auto_repair = AutoRepair(monitor)
    result = auto_repair.repair(dna, candles, method=method)

    if json_mode:
        output = {
            "health": {
                "baseline": round(baseline, 4),
                "current": round(current_fitness, 4),
                "degradation_pct": round(health.degradation_pct, 4),
                "is_healthy": False,
            },
            "repair": result.to_dict(),
        }
        print(json.dumps(output, indent=2))
    else:
        sign = "+" if result.improvement_pct >= 0 else ""
        print(f"\n   Repair Result:")
        print(f"     Original fitness:  {result.original_fitness:.4f}")
        print(f"     Repaired fitness:  {result.repaired_fitness:.4f}")
        print(f"     Improvement:       {sign}{result.improvement_pct:.1%}")
        print(f"     Genes modified:    {len(result.genes_modified)}")
        if result.genes_modified:
            print(f"     Modified genes:    {', '.join(result.genes_modified)}")
        print(f"     Method:            {result.repair_method}")


def cmd_backtest(args):
    """Run backtest with full performance metrics."""
    from .backtest.engine import BacktestEngine
    from .core.dna import AgentDNA

    json_mode = getattr(args, 'json', False)
    data_file = os.path.basename(args.data)
    data_dir = os.path.dirname(args.data) or 'data'

    # Load champion DNA
    dna = _load_champion_dna(args)

    engine = BacktestEngine(data_dir=data_dir)

    if args.multi:
        if not json_mode:
            print("\n🧬 Darwinia Backtest — Multi-Asset")
            print(f"   Strategy: {dna.id}\n")
        result = engine.multi_asset(dna)
        if json_mode:
            # Strip non-serializable fields
            print(json.dumps({
                'mode': result['mode'],
                'assets_tested': result['assets_tested'],
                'avg_sharpe': result['avg_sharpe'],
                'avg_return_pct': result['avg_return_pct'],
                'results': result['results'],
            }, indent=2))
        else:
            print(f"   Assets tested: {result['assets_tested']}")
            print(f"   Avg Sharpe:    {result['avg_sharpe']:.4f}")
            print(f"   Avg Return:    {result['avg_return_pct']:+.2%}")
            print()
            for r in result['results']:
                if 'error' in r:
                    print(f"   ✗ {r['asset']}: {r['error']}")
                else:
                    m = r['metrics']
                    print(f"   ✓ {r['asset']}: Sharpe={m['sharpe_ratio']:.4f} Return={m['total_return_pct']:+.2%} Trades={m['num_trades']}")
        return

    if args.walk_forward:
        if not json_mode:
            print(f"\n🧬 Darwinia Backtest — Walk-Forward ({args.windows} windows)")
            print(f"   Data: {data_file} | Strategy: {dna.id}\n")
        result = engine.walk_forward(dna, data_file, n_windows=args.windows)
        if json_mode:
            print(json.dumps({
                'mode': result['mode'],
                'n_windows': result['n_windows'],
                'total_trades': result['total_trades'],
                'aggregate': result['aggregate'].to_dict(),
                'windows': result['windows'],
            }, indent=2))
        else:
            for w in result['windows']:
                m = w['metrics']
                print(f"   Window {w['window']}: Sharpe={m['sharpe_ratio']:.4f} Return={m['total_return_pct']:+.2%} Trades={w['num_trades']}")
            print(f"\n{result['aggregate'].summary()}")
        return

    # Single-pass backtest
    if not json_mode:
        print(f"\n🧬 Darwinia Backtest")
        print(f"   Data: {data_file} | Strategy: {dna.id}")
        if args.train_ratio > 0:
            print(f"   Out-of-sample: {1 - args.train_ratio:.0%}\n")
        else:
            print(f"   Mode: full dataset\n")

    result = engine.run(dna, data_file, train_ratio=args.train_ratio)

    if json_mode:
        print(json.dumps({
            'asset': result['asset'],
            'label': result['label'],
            'candles': result['candles'],
            'metrics': result['metrics'].to_dict(),
            'num_trades': len(result['trades']),
        }, indent=2))
    else:
        print(result['metrics'].summary())


def _load_champion_dna(args):
    """Load champion DNA from file or create default."""
    from .core.dna import AgentDNA

    def _parse_dna(data):
        dna = AgentDNA()
        genes = data.get('genes', data)  # support both flat and nested format
        for gene in AgentDNA.GENE_FIELDS:
            if gene in genes:
                val = genes[gene]
                if isinstance(val, (int, float)):
                    setattr(dna, gene, float(val))
        if 'id' in data:
            dna.id = data['id']
        if 'dna' in data and 'id' in data['dna']:
            dna.id = data['dna']['id']
        return dna

    champion_path = getattr(args, 'champion', None)
    if champion_path and os.path.exists(champion_path):
        try:
            with open(champion_path) as f:
                data = json.load(f)
            return _parse_dna(data)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"   Warning: failed to load {champion_path}: {e}")
            print(f"   Falling back to default DNA")

    # Try to find latest champion in output/
    output_dir = getattr(args, 'output', 'output')
    champion_file = os.path.join(output_dir, 'champion.json')
    if os.path.exists(champion_file):
        try:
            with open(champion_file) as f:
                data = json.load(f)
            return _parse_dna(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # Default DNA
    return AgentDNA()


def cmd_export(args):
    """Export evolved strategy as portable JSON."""
    from .core.dna import AgentDNA

    json_mode = getattr(args, 'json', False)
    dna = _load_champion_dna(args)

    export_data = {
        'format': 'darwinia-strategy-v1',
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'dna': {
            'id': dna.id,
            'generation': dna.generation,
            'fitness': dna.fitness,
            'genes': dna.get_genes(),
        },
        'metadata': {
            'gene_count': len(AgentDNA.GENE_FIELDS),
            'gene_fields': AgentDNA.GENE_FIELDS,
        },
    }

    # Save to file
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    filename = f"strategy_{dna.id}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w') as f:
        json.dump(export_data, f, indent=2)

    if json_mode:
        print(json.dumps({
            'exported': filepath,
            'strategy_id': dna.id,
            'format': 'darwinia-strategy-v1',
            'genes': dna.get_genes(),
        }, indent=2))
    else:
        print(f"\n🧬 Darwinia Strategy Export")
        print(f"   Strategy ID: {dna.id}")
        print(f"   Generation:  {dna.generation}")
        print(f"   Fitness:     {dna.fitness:.4f}")
        print(f"   Genes:       {len(AgentDNA.GENE_FIELDS)}")
        print(f"   Saved to:    {filepath}")
        print(f"\n   Import with: python -m darwinia backtest -c {filepath}")


def cmd_ensemble(args):
    """Run ensemble committee evaluation."""
    from .ensemble.committee import EnsembleAgent
    from .core.dna import AgentDNA
    from .core.market import MarketEnvironment

    json_mode = getattr(args, 'json', False)
    data_file = os.path.basename(args.data)
    data_dir = os.path.dirname(args.data) or 'data'

    market = MarketEnvironment(data_dir)
    candles = market.load_csv(data_file)

    # Create ensemble from diverse mutated DNAs
    members = []
    for i in range(args.size):
        dna = AgentDNA()
        dna = dna.mutate(mutation_rate=0.5, mutation_strength=0.3)
        members.append(dna)

    ensemble = EnsembleAgent(members, voting_mode=args.mode)

    if not json_mode:
        print(f"\n🧬 Darwinia Ensemble — {args.size} members, {args.mode} voting")
        print(f"   Data: {data_file} | {len(candles)} candles\n")

    result = ensemble.evaluate(candles)

    if json_mode:
        print(json.dumps({
            'members': len(result['per_member']),
            'voting_mode': args.mode,
            'per_member': result['per_member'],
            'consensus': result['consensus'],
        }, indent=2, default=str))
    else:
        print(f"   Members: {len(result['per_member'])}")
        consensus = result['consensus']
        avg_cons = consensus.get('avg_consensus_strength', consensus.get('mean_consensus', 0))
        print(f"   Consensus strength: {avg_cons:.4f}")
        print()
        for ms in result['per_member']:
            agent_id = ms.get('agent_id', ms.get('dna_id', '?'))
            print(f"   Agent {agent_id}: {ms['num_trades']} trades, PnL=${ms['total_pnl']:.2f}")


def cmd_montecarlo(args):
    """Run Monte Carlo stress test."""
    from .montecarlo.simulator import MonteCarloSimulator

    json_mode = getattr(args, 'json', False)
    data_file = os.path.basename(args.data)
    data_dir = os.path.dirname(args.data) or 'data'

    dna = _load_champion_dna(args)
    sim = MonteCarloSimulator(data_dir=data_dir, n_simulations=args.simulations)

    if not json_mode:
        print(f"\n🧬 Darwinia Monte Carlo — {args.simulations} simulations ({args.method})")
        print(f"   Data: {data_file} | Strategy: {dna.id}\n")

    result = sim.run(dna, data_file, method=args.method)

    if json_mode:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.summary())


def cmd_benchmark(args):
    """Compare strategy against baselines."""
    from .benchmark.baselines import BenchmarkSuite

    json_mode = getattr(args, 'json', False)
    data_file = os.path.basename(args.data)
    data_dir = os.path.dirname(args.data) or 'data'

    dna = _load_champion_dna(args)
    suite = BenchmarkSuite(data_dir=data_dir)

    if not json_mode:
        print(f"\n🧬 Darwinia Benchmark — Strategy vs Baselines")
        print(f"   Data: {data_file} | Strategy: {dna.id}\n")

    result = suite.run(dna, data_file)

    if json_mode:
        output = {
            'evolved': result['evolved'].to_dict(),
            'baselines': [b.to_dict() for b in result['baselines']],
            'ranking': [r.to_dict() for r in result['ranking']],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"   {'Strategy':<25} {'Return':>10} {'Sharpe':>10} {'MaxDD':>10} {'WinRate':>10}")
        print(f"   {'─' * 65}")
        for r in result['ranking']:
            marker = " ◀" if r.strategy_name == "evolved" else ""
            print(f"   {r.strategy_name:<25} {r.total_return_pct:>+9.2%} {r.sharpe_ratio:>10.4f} {r.max_drawdown_pct:>9.2%} {r.win_rate:>10.2%}{marker}")


def cmd_fingerprint(args):
    """Show strategy DNA fingerprint."""
    from .fingerprint.visualizer import StrategyFingerprint

    json_mode = getattr(args, 'json', False)
    dna = _load_champion_dna(args)
    fp = StrategyFingerprint(dna)

    if json_mode:
        print(json.dumps(fp.to_dict(), indent=2))
    else:
        print(f"\n🧬 Darwinia Strategy Fingerprint")
        print(f"   ID: {dna.id} | Archetype: {fp.archetype()}\n")
        print(fp.radar_ascii())
        traits = fp.dominant_traits()
        if traits:
            print(f"\n   Dominant traits:")
            for t in traits:
                print(f"     • {t}")


def cmd_info(args):
    """Show project info."""
    import glob as glob_mod

    json_mode = getattr(args, 'json', False)

    project_root = os.path.join(os.path.dirname(__file__), '..')
    data_dir = os.path.join(project_root, 'data')
    data_files = glob_mod.glob(os.path.join(data_dir, '*.csv'))
    candle_count = 0
    for f in data_files:
        try:
            with open(f) as fh:
                candle_count += sum(1 for _ in fh) - 1
        except Exception:
            pass

    # Count tests
    test_dir = os.path.join(project_root, 'tests')
    test_count = 0
    if os.path.isdir(test_dir):
        for tf in glob_mod.glob(os.path.join(test_dir, 'test_*.py')):
            try:
                with open(tf) as fh:
                    test_count += sum(1 for line in fh if line.strip().startswith('def test_'))
            except Exception:
                pass

    info = {
        "name": "Darwinia",
        "version": __version__,
        "description": "The Self-Evolving Agent Ecosystem",
        "genes": 17,
        "attack_types": 6,
        "commands": 19,
        "modules": ["core", "evolution", "arena", "discovery", "chronicle",
                     "personality", "knowledge", "data", "macro", "integrations",
                     "analytics", "validation", "repair", "backtest",
                     "ensemble", "montecarlo", "benchmark", "fingerprint"],
        "tests": test_count,
        "data_candles": candle_count,
        "data_files": [os.path.basename(f) for f in data_files],
        "python_version": sys.version,
        "status": "ready",
    }

    if json_mode:
        print(json.dumps(info, indent=2))
    else:
        print("🧬 Darwinia — The Self-Evolving Agent Ecosystem")
        print()
        print(f"  Version:  {__version__}")
        print(f"  Modules:  {len(info['modules'])} | Tests: {test_count}")
        print(f"  Data:     {candle_count:,} candles from {len(data_files)} file(s)")
        print(f"  Genes:    17 | Attack types: 6")
        print()
        print("  Commands:")
        print("    evolve      Run genetic evolution          arena       Adversarial stress test")
        print("    validate    Walk-forward overfit check     explain     Gene ablation analysis")
        print("    fetch       Download live market data      scan        Discover trending assets")
        print("    analytics   Population statistics          tournament  Champion round-robin")
        print("    backtest    Full performance analysis      export      Export strategy as JSON")
        print("    ensemble    Multi-agent committee vote     montecarlo  Monte Carlo stress test")
        print("    benchmark   Compare against baselines      fingerprint Strategy DNA fingerprint")
        print("    repair      Self-repair degraded agents    dashboard   Streamlit web UI")
        print("    info        System info")
        print()
        print("  GitHub: https://github.com/0xSanei/darwinia")


def main():
    parser = argparse.ArgumentParser(
        prog="darwinia",
        description="Darwinia — The Self-Evolving Agent Ecosystem"
    )
    parser.add_argument('--version', action='version', version=f'darwinia {__version__}')
    subparsers = parser.add_subparsers(dest="command")

    # evolve
    p_evolve = subparsers.add_parser("evolve", help="Run evolution")
    p_evolve.add_argument("-g", "--generations", type=int, default=50, help="Number of generations (default: 50)")
    p_evolve.add_argument("-p", "--population", type=int, default=50, help="Population size (default: 50)")
    p_evolve.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_evolve.add_argument("-o", "--output", default="output", help="Output directory")
    p_evolve.add_argument("--arena-start", type=int, default=5, help="Generation to start adversarial arena (default: 5)")
    p_evolve.add_argument("--multi", action="store_true", help="Auto-load all CSVs in data/ and evolve on each")
    p_evolve.add_argument("--macro", action="store_true", help="Enable macro regime overlay with MacroAwareFitness")
    p_evolve.add_argument("--json", action="store_true", help="Output results as JSON")
    p_evolve.set_defaults(func=cmd_evolve)

    # arena
    p_arena = subparsers.add_parser("arena", help="Test agent against adversary")
    p_arena.add_argument("-c", "--champion", help="Path to champion JSON file")
    p_arena.add_argument("-r", "--rounds", type=int, default=5, help="Rounds per test (default: 5)")
    p_arena.add_argument("--json", action="store_true", help="Output results as JSON")
    p_arena.set_defaults(func=cmd_arena)

    # validate
    p_val = subparsers.add_parser("validate", help="Walk-forward validation (overfit detection)")
    p_val.add_argument("-w", "--windows", type=int, default=3, help="Number of walk-forward windows (default: 3)")
    p_val.add_argument("-g", "--generations", type=int, default=20, help="Generations per window (default: 20)")
    p_val.add_argument("-p", "--population", type=int, default=30, help="Population size (default: 30)")
    p_val.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_val.add_argument("-o", "--output", default="output", help="Output directory")
    p_val.add_argument("--json", action="store_true", help="Output results as JSON")
    p_val.set_defaults(func=cmd_validate)

    # explain
    p_exp = subparsers.add_parser("explain", help="Gene ablation analysis (explainability)")
    p_exp.add_argument("-c", "--champion", help="Path to champion JSON file")
    p_exp.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_exp.add_argument("--json", action="store_true", help="Output results as JSON")
    p_exp.set_defaults(func=cmd_explain)

    # fetch
    p_fetch = subparsers.add_parser("fetch", help="Fetch market data from exchange APIs")
    p_fetch.add_argument("-s", "--symbol", default="BTCUSDT", help="Trading pair or coin ID (default: BTCUSDT)")
    p_fetch.add_argument("-i", "--interval", default="1h", help="Candle interval for Binance (default: 1h)")
    p_fetch.add_argument("-l", "--limit", type=int, default=1000, help="Number of candles / days (default: 1000)")
    p_fetch.add_argument("--source", default="binance", choices=["binance", "coingecko"], help="Data source (default: binance)")
    p_fetch.add_argument("--json", action="store_true", help="Output results as JSON")
    p_fetch.set_defaults(func=cmd_fetch)

    # scan
    p_scan = subparsers.add_parser("scan", help="Discover trending/volatile assets for evolution")
    p_scan.add_argument("--volatile", action="store_true", help="Sort by volatility instead of volume")
    p_scan.add_argument("--recommend", action="store_true", help="Show recommended pairs for evolution")
    p_scan.add_argument("--top", type=int, default=5, help="Number of assets to show (default: 5)")
    p_scan.add_argument("--json", action="store_true", help="Output results as JSON")
    p_scan.set_defaults(func=cmd_scan)

    # tournament
    p_tourn = subparsers.add_parser("tournament", help="Run tournament between evolved champions")
    p_tourn.add_argument("-n", "--top", type=int, default=5, help="Number of top agents for tournament (default: 5)")
    p_tourn.add_argument("-g", "--generations", type=int, default=50, help="Evolution generations (default: 50)")
    p_tourn.add_argument("-p", "--population", type=int, default=50, help="Population size (default: 50)")
    p_tourn.add_argument("-r", "--rounds", type=int, default=5, help="Rounds per match (default: 5)")
    p_tourn.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_tourn.add_argument("-o", "--output", default="output", help="Output directory")
    p_tourn.add_argument("--json", action="store_true", help="Output results as JSON")
    p_tourn.set_defaults(func=cmd_tournament)

    # analytics
    p_analytics = subparsers.add_parser("analytics", help="Population analytics and statistics")
    p_analytics.add_argument("-g", "--generations", type=int, default=10, help="Generations to evolve (default: 10)")
    p_analytics.add_argument("-p", "--population", type=int, default=50, help="Population size (default: 50)")
    p_analytics.add_argument("--json", action="store_true", help="Output results as JSON")
    p_analytics.set_defaults(func=cmd_analytics)

    # repair
    p_repair = subparsers.add_parser("repair", help="Check strategy health and auto-repair")
    p_repair.add_argument("-c", "--champion", help="Path to champion JSON file")
    p_repair.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_repair.add_argument("--method", default="targeted", choices=["targeted", "full", "ensemble"],
                          help="Repair method (default: targeted)")
    p_repair.add_argument("--json", action="store_true", help="Output results as JSON")
    p_repair.set_defaults(func=cmd_repair)

    # backtest
    p_bt = subparsers.add_parser("backtest", help="Backtest a strategy with full performance metrics")
    p_bt.add_argument("-c", "--champion", help="Path to champion JSON file")
    p_bt.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_bt.add_argument("--walk-forward", action="store_true", help="Use walk-forward windows instead of single pass")
    p_bt.add_argument("-w", "--windows", type=int, default=5, help="Number of walk-forward windows (default: 5)")
    p_bt.add_argument("--multi", action="store_true", help="Test across all available assets")
    p_bt.add_argument("--train-ratio", type=float, default=0.0, help="Train/test split ratio (default: 0 = full data)")
    p_bt.add_argument("--json", action="store_true", help="Output results as JSON")
    p_bt.set_defaults(func=cmd_backtest)

    # export
    p_export = subparsers.add_parser("export", help="Export evolved strategy as portable JSON")
    p_export.add_argument("-c", "--champion", help="Path to champion JSON file")
    p_export.add_argument("-o", "--output", default="output", help="Output directory")
    p_export.add_argument("--format", default="json", choices=["json"], help="Export format (default: json)")
    p_export.add_argument("--json", action="store_true", help="Output results as JSON")
    p_export.set_defaults(func=cmd_export)

    # ensemble
    p_ens = subparsers.add_parser("ensemble", help="Run ensemble committee of multiple strategies")
    p_ens.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_ens.add_argument("-s", "--size", type=int, default=5, help="Number of committee members (default: 5)")
    p_ens.add_argument("--mode", default="majority", choices=["majority", "weighted", "unanimous"],
                       help="Voting mode (default: majority)")
    p_ens.add_argument("--json", action="store_true", help="Output results as JSON")
    p_ens.set_defaults(func=cmd_ensemble)

    # montecarlo
    p_mc = subparsers.add_parser("montecarlo", help="Monte Carlo stress test")
    p_mc.add_argument("-c", "--champion", help="Path to champion JSON file")
    p_mc.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_mc.add_argument("-n", "--simulations", type=int, default=500, help="Number of simulations (default: 500)")
    p_mc.add_argument("--method", default="bootstrap", choices=["bootstrap", "noise", "shuffle"],
                      help="Randomization method (default: bootstrap)")
    p_mc.add_argument("--json", action="store_true", help="Output results as JSON")
    p_mc.set_defaults(func=cmd_montecarlo)

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Compare strategy against baselines")
    p_bench.add_argument("-c", "--champion", help="Path to champion JSON file")
    p_bench.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_bench.add_argument("--json", action="store_true", help="Output results as JSON")
    p_bench.set_defaults(func=cmd_benchmark)

    # fingerprint
    p_fp = subparsers.add_parser("fingerprint", help="Show strategy DNA fingerprint")
    p_fp.add_argument("-c", "--champion", help="Path to champion JSON file")
    p_fp.add_argument("--json", action="store_true", help="Output results as JSON")
    p_fp.set_defaults(func=cmd_fingerprint)

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Launch Streamlit dashboard")
    p_dash.set_defaults(func=cmd_dashboard)

    # info
    p_info = subparsers.add_parser("info", help="Show project info")
    p_info.add_argument("--json", action="store_true", help="Output results as JSON")
    p_info.set_defaults(func=cmd_info)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        cmd_info(args)


if __name__ == "__main__":
    main()
