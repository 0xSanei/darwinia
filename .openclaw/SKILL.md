---
name: darwinia
description: Evolve trading strategies through genetic algorithms and adversarial combat. Run Darwinian selection on BTC data to discover battle-tested strategies. No API keys, no cloud.
version: 1.0.0
author: 0xSanei
tags:
  - trading
  - evolution
  - genetic-algorithm
  - adversarial
  - backtesting
  - crypto
homepage: https://github.com/0xSanei/darwinia
metadata:
  openclaw:
    emoji: "🧬"
    requires:
      bins:
        - python3
    install:
      - kind: command
        command: "pip install git+https://github.com/0xSanei/darwinia.git"
        bins: [python3]
        label: "Install Darwinia via pip"
---

# Darwinia — The Self-Evolving Agent Ecosystem

Darwinia evolves trading strategies through natural selection. 50 agents compete on real BTC market data, the weak die, the strong breed. After 50 generations, survivors handle rug pulls, fake breakouts, and whipsaws — because agents that couldn't survive didn't reproduce.

## When to use this skill

- User asks to "find a good trading strategy" or "optimize trading parameters"
- User wants to stress-test a strategy against adversarial market conditions
- User asks about genetic algorithms applied to trading
- User wants to discover market patterns automatically
- User says "evolve", "darwinia", "genetic trading", or "adversarial test"

## Commands

### Quick evolution (~30 seconds)
```bash
python -m darwinia evolve -g 10 --json
```

### Full evolution with adversarial arena (~3 minutes)
```bash
python -m darwinia evolve -g 50 --json
```

### Test champion against 6 attack types
```bash
python -m darwinia arena --json
```

### System info
```bash
python -m darwinia info --json
```

### Interactive dashboard
```bash
python -m darwinia dashboard
```

Always use `--json` when calling programmatically.

## Interpreting results

Key JSON fields after `evolve --json`:

- `champion.fitness`: Risk-adjusted score. >1.0 = outperforms buy-and-hold.
- `champion.genes`: 17 floats [0,1] encoding the full trading strategy.
- `evolution_summary.patterns_discovered`: Number of emergent trading rules found.
- `patterns`: Emergent trading rules discovered by agents (not pre-programmed).

## How to explain results to user

- **Fitness > 1.0** → Champion outperforms buy-and-hold on risk-adjusted basis
- **High genetic diversity** → Population hasn't converged yet, more generations may help
- **Discovered patterns** → Trading rules the agents found on their own

## Installation

```bash
git clone https://github.com/0xSanei/darwinia.git
cd darwinia
pip install -e ".[dev]"
```

No API keys. No cloud. Pure Python + numpy. BTC/USDT 1h data (10,946 candles) included.

## Composability

Darwinia exposes a two-way composability interface so it can interoperate with other ClawHub / OpenClaw skills.

### Other skills call Darwinia (SkillBridge API)

```python
from darwinia.integrations import SkillBridge

bridge = SkillBridge()

# Run evolution and get results as a dict
result = bridge.evolve({
    "generations": 20,
    "population_size": 30,
    "data_path": "data/btc_1h.csv",
})

# Get the champion agent
champion = bridge.get_champion()  # latest generation
champion = bridge.get_champion(generation=10)  # specific generation

# Evaluate any arbitrary strategy DNA (17 floats)
score = bridge.evaluate_strategy([0.8, 0.5, 0.3, 0.5, 0.9, 0.6, 0.4, 0.05, 0.1,
                                   0.4, 0.7, 0.1, 0.7, 0.5, 0.6, 0.5, 0.8])

# Detect current market regime
regime = bridge.get_market_regime()
# => {"regime": "trending_up", "confidence": 0.82, ...}
```

### Darwinia calls other skills (SkillRegistry)

```python
from darwinia.integrations import SkillRegistry

registry = SkillRegistry()

# Register an external skill endpoint
registry.register("macro-liquidity", my_macro_function)
registry.register("crypto-market-rank", my_ranking_function)

# Call registered skills
macro = registry.call("macro-liquidity", indicator="fed_net_liquidity")
trending = registry.call("crypto-market-rank", category="trending", limit=10)

# List available skills
print(registry.list_skills())
```

### Example pipeline: macro-liquidity -> Darwinia -> evolved strategy

```python
from darwinia.integrations import SkillBridge, SkillRegistry

registry = SkillRegistry()
registry.register("macro-liquidity", get_macro_signals)

# 1. Pull macro context
macro = registry.call("macro-liquidity")

# 2. Adjust evolution config based on macro regime
config = {
    "generations": 50,
    "population_size": 50,
    "data_path": "data/btc_1h.csv",
}
if macro.get("yen_carry_signal") == "risk_off":
    config["seed_ratio"] = 0.4  # more conservative seeds

# 3. Evolve
bridge = SkillBridge()
result = bridge.evolve(config)

# 4. Output champion strategy
champion = bridge.get_champion()
print(f"Best fitness: {champion['fitness']}")
print(f"Market regime: {bridge.get_market_regime()['regime']}")
```

Built-in integration templates available for: `macro-liquidity`, `crypto-market-rank`, `okx-dex-market`.

## Important

- Simulation only. Does NOT execute real trades.
- Deterministic with same random seed (default: 42).
- Evolution engine is domain-agnostic — can evolve any agent behavior, not just trading.
