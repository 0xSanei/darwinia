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


def cmd_evolve(args):
    """Run evolution."""
    import numpy as np
    from .core.market import MarketEnvironment
    from .evolution.engine import EvolutionEngine

    json_mode = getattr(args, 'json', False)

    if not json_mode:
        print(f"🧬 Darwinia — Evolution Engine")
        print(f"   Generations: {args.generations}")
        print(f"   Population:  {args.population}")
        print(f"   Data:        {args.data}")
        print()

    # Load market data
    data_dir = os.path.dirname(args.data)
    data_file = os.path.basename(args.data)
    market = MarketEnvironment(data_dir)
    candles = market.load_csv(data_file)
    if not json_mode:
        print(f"   Loaded {len(candles)} candles")

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

    # Save results
    engine.recorder.save_summary()
    engine.recorder.save_final_report(results)

    if json_mode:
        # Build JSON output from actual results
        last_gen = results['generations'][-1] if results['generations'] else {}
        champion_dict = results['champions'][-1] if results['champions'] else {}

        # Top 5 agents from last generation's population snapshot
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
    p_evolve.add_argument("--json", action="store_true", help="Output results as JSON")
    p_evolve.set_defaults(func=cmd_evolve)

    # arena
    p_arena = subparsers.add_parser("arena", help="Test agent against adversary")
    p_arena.add_argument("-c", "--champion", help="Path to champion JSON file")
    p_arena.add_argument("-r", "--rounds", type=int, default=5, help="Rounds per test (default: 5)")
    p_arena.add_argument("--json", action="store_true", help="Output results as JSON")
    p_arena.set_defaults(func=cmd_arena)

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
