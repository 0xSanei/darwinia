---
name: darwinia
description: Evolve trading strategies through genetic algorithms and adversarial combat. No API keys, no cloud — pure Python + numpy.
version: 1.0.0
author: 0xSanei
homepage: https://github.com/0xSanei/darwinia
---

# Darwinia — Self-Evolving Trading Agent Ecosystem

Evolves trading strategies through natural selection. 50 agents with random DNA compete on BTC data. Weak die, strong breed. Survivors handle rug pulls, fake breakouts, whipsaws.

## When to use

- User asks to find, optimize, or evolve a trading strategy
- User wants adversarial stress-testing of trading logic
- User mentions "darwinia", "evolve strategy", or "adversarial test"

## Setup

```bash
git clone https://github.com/0xSanei/darwinia.git && cd darwinia && pip install -e ".[dev]"
```

## Commands

| Command | Time | Purpose |
|---------|------|---------|
| `python -m darwinia evolve -g 10 --json` | ~30s | Quick demo |
| `python -m darwinia evolve -g 50 --json` | ~3min | Full evolution + adversarial arena |
| `python -m darwinia arena --json` | ~30s | Test champion against 6 attacks |
| `python -m darwinia info --json` | instant | Version and capabilities |
| `python -m darwinia dashboard` | — | Streamlit interactive dashboard |

Always use `--json` for programmatic calls.

## Key output fields

- `champion.fitness`: >1.0 = outperforms buy-and-hold
- `champion.genes`: 17 floats [0,1] encoding full strategy
- `evolution_summary.patterns_discovered`: count of emergent rules
- `patterns`: Emergent rules discovered by agents (not pre-programmed)

## 17-gene DNA

Signal (5): momentum, volume, volatility, mean_reversion, trend
Threshold (4): entry, exit, stop_loss, take_profit
Personality (5): risk_appetite, time_horizon, contrarian_bias, patience, position_sizing
Adaptation (3): regime_sensitivity, memory_length, noise_filter

## 6 adversarial attacks

rug_pull, fake_breakout, slow_bleed, whipsaw, volume_mirage, pump_and_dump
Arena reads agent DNA to find weaknesses and generates targeted scenarios.

## Composability

Darwinia provides a two-way composability interface for cross-skill interop.

### Inbound: other skills call Darwinia (SkillBridge)

```python
from darwinia.integrations import SkillBridge

bridge = SkillBridge()
result = bridge.evolve({"generations": 20, "population_size": 30, "data_path": "data/btc_1h.csv"})
champion = bridge.get_champion()
score = bridge.evaluate_strategy([0.5] * 17)
regime = bridge.get_market_regime()
```

Methods: `evolve(config) -> dict`, `get_champion(gen) -> dict`, `evaluate_strategy(dna) -> dict`, `get_market_regime() -> dict`

### Outbound: Darwinia calls other skills (SkillRegistry)

```python
from darwinia.integrations import SkillRegistry

registry = SkillRegistry()
registry.register("macro-liquidity", my_func)
result = registry.call("macro-liquidity", indicator="fed_net_liquidity")
print(registry.list_skills())
```

### Pipeline example: macro-liquidity -> Darwinia -> strategy

Pull macro signals, bias evolution config, evolve, output champion. Built-in templates for: `macro-liquidity`, `crypto-market-rank`, `okx-dex-market`.

## Simulation only — does NOT execute real trades.
