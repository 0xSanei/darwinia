# Darwinia — Instructions for AI Agents

This file tells AI agents (Claude Code, Cursor, OpenClaw, etc.) how to use Darwinia.

## What Is Darwinia?

An evolutionary trading agent ecosystem. You don't write strategies — you evolve them. Agents with 17-gene DNA compete on real market data, face adversarial attacks, and only the fittest survive to breed.

## Quick Commands

```bash
# Install
pip install -e ".[dev]"

# Run evolution (default: 50 gens, 50 agents, BTC 1h data)
python -m darwinia evolve

# Custom evolution
python -m darwinia evolve -g 100 -p 80 --arena-start 10

# Test a specific champion against attacks
python -m darwinia arena -c output/champions/champion_gen_0049.json -r 10

# Launch visualization dashboard
python -m darwinia dashboard

# Run tests
pytest tests/ -v
```

## Key Files

| Path | Purpose |
|------|---------|
| `darwinia/core/dna.py` | 17-gene DNA definition + crossover/mutation |
| `darwinia/core/agent.py` | Trading agent that interprets DNA into decisions |
| `darwinia/core/market.py` | Market data loader (CSV) |
| `darwinia/evolution/engine.py` | Main evolution loop orchestrator |
| `darwinia/evolution/fitness.py` | Composite fitness scoring (Sharpe, drawdown, win rate) |
| `darwinia/evolution/population.py` | Selection + breeding |
| `darwinia/arena/adversary.py` | 6 attack types targeting agent weaknesses |
| `darwinia/arena/arena.py` | Arena runner, survival scoring |
| `darwinia/discovery/analyzer.py` | Gene convergence + correlation analysis |
| `darwinia/chronicle/recorder.py` | JSON snapshot recorder |
| `darwinia/chronicle/speciation.py` | K-means species clustering |
| `darwinia/__main__.py` | CLI entry point |
| `data/btc_1h.csv` | 10,946 BTC/USDT 1h candles (2024-01 to 2025-04) |

## Common Tasks

### "Evolve a trading strategy for BTC"
```bash
python -m darwinia evolve -g 50
# Results in output/champions/ and output/evolution_summary.json
```

### "What patterns did the agents discover?"
```bash
# After evolution, check:
cat output/final_report.json | python -m json.tool | grep -A5 "patterns_discovered"
```

### "Which attack is my strategy weakest against?"
```bash
python -m darwinia arena -c output/champions/champion_gen_0049.json -r 20
# Look for attacks with lowest PnL or ❌ markers
```

### "Run with custom market data"
```bash
# CSV must have columns: timestamp, open, high, low, close, volume
python -m darwinia evolve -d path/to/your_data.csv
```

### "Modify the fitness function"
Edit `darwinia/evolution/fitness.py`. The composite weights are:
- Sharpe ratio: 35%
- Total return: 25%
- Win rate: 15%
- Drawdown penalty: 15%
- Adversarial survival: 10%

### "Add a new attack type"
Edit `darwinia/arena/adversary.py`, add to `ATTACK_TEMPLATES` dict. Each attack has phases with type, length, and magnitude.

## Architecture Overview

```
Evolution Engine (engine.py)
    │
    ├── Population (population.py) — manages 50 agents
    │       ├── DNA (dna.py) — 17 genes per agent
    │       └── Selection — tournament + elite
    │
    ├── Fitness (fitness.py) — composite scoring
    │       └── TradingAgent (agent.py) — interprets DNA → trades
    │
    ├── Arena (arena.py) — adversarial survival testing
    │       └── Adversary (adversary.py) — 6 targeted attacks
    │
    ├── Discovery (analyzer.py) — pattern extraction
    │
    └── Chronicle (recorder.py) — JSON snapshots + species tracking
```

## Constraints

- All genes are floats in [0, 1] — normalized for uniform crossover
- Market data must be OHLCV format (6 columns)
- No external API calls during evolution — pure local computation
- Python 3.9+ required, numpy is the only hard dependency
