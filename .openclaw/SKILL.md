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

## Important

- Simulation only. Does NOT execute real trades.
- Deterministic with same random seed (default: 42).
- Evolution engine is domain-agnostic — can evolve any agent behavior, not just trading.
