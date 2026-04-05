"""
CLI entry point — python -m darwinia
"""

import argparse
import sys
import json
import os

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


def cmd_evolve(args):
    """Run evolution."""
    json_mode = getattr(args, 'json', False)
    multi = getattr(args, 'multi', False)

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
        with open(args.champion) as f:
            dna = AgentDNA.from_dict(json.load(f))
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

    data_dir = os.path.dirname(args.data)
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
        with open(args.champion) as f:
            dna = AgentDNA.from_dict(json.load(f))
        if not json_mode:
            print(f"   Agent: {dna.id}")
    else:
        dna = AgentDNA.seed_trend_follower()
        if not json_mode:
            print(f"   Agent: seed_trend_follower")

    data_dir = os.path.dirname(args.data)
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


def cmd_dashboard(args):
    """Launch Streamlit dashboard."""
    import subprocess
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'app.py')
    dashboard_path = os.path.abspath(dashboard_path)
    print(f"🧬 Launching Darwinia Dashboard...")
    subprocess.run(["streamlit", "run", dashboard_path, "--server.headless", "true"])


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

    info = {
        "name": "Darwinia",
        "version": "1.0.0",
        "description": "The Self-Evolving Agent Ecosystem",
        "genes": 17,
        "attack_types": 6,
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
        print(f"  Version: 1.0.0")
        print(f"  Data:    {candle_count:,} candles from {len(data_files)} file(s)")
        print(f"  Genes:   17 | Attack types: 6")
        print()
        print("  Commands:")
        print("    python -m darwinia evolve     Run evolution")
        print("    python -m darwinia arena      Test against adversary")
        print("    python -m darwinia dashboard  Launch web dashboard")
        print("    python -m darwinia info       System info")
        print()
        print("  GitHub: https://github.com/0xSanei/darwinia")


def main():
    parser = argparse.ArgumentParser(
        prog="darwinia",
        description="Darwinia — The Self-Evolving Agent Ecosystem"
    )
    subparsers = parser.add_subparsers(dest="command")

    # evolve
    p_evolve = subparsers.add_parser("evolve", help="Run evolution")
    p_evolve.add_argument("-g", "--generations", type=int, default=50, help="Number of generations (default: 50)")
    p_evolve.add_argument("-p", "--population", type=int, default=50, help="Population size (default: 50)")
    p_evolve.add_argument("-d", "--data", default="data/btc_1h.csv", help="Path to market data CSV")
    p_evolve.add_argument("-o", "--output", default="output", help="Output directory")
    p_evolve.add_argument("--arena-start", type=int, default=5, help="Generation to start adversarial arena (default: 5)")
    p_evolve.add_argument("--multi", action="store_true", help="Auto-load all CSVs in data/ and evolve on each")
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
