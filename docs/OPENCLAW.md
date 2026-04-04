# Darwinia × OpenClaw Integration Guide

## Overview

Darwinia is an OpenClaw skill that lets your agent **evolve trading strategies** through genetic algorithms and adversarial combat — no hand-coded rules needed.

## How it works

```
You (via WhatsApp/Telegram/Slack)
  → "Find me a strategy that survives market crashes"
    → OpenClaw triggers Darwinia skill
      → 50 agents × 50 generations of evolution
        → Champion tested against 6 adversarial attacks
          → Results summarized back to you
```

## Installation

### Option A: Manual install
```bash
git clone https://github.com/0xSanei/darwinia.git ~/darwinia
cd ~/darwinia && pip install -e .

mkdir -p ~/.openclaw/skills/darwinia
cp .openclaw/SKILL.md ~/.openclaw/skills/darwinia/SKILL.md
```

### Option B: Tell your agent
> "Install Darwinia from https://github.com/0xSanei/darwinia — it's a trading strategy evolution tool."

Your OpenClaw agent will handle the clone, install, and skill registration.

## Usage

Natural language through any OpenClaw channel:

- "Use Darwinia to evolve a BTC trading strategy"
- "Run 50 generations and show me the best strategy"
- "Test my strategy against rug pulls and fake breakouts"
- "What patterns did the evolved agents discover?"

Programmatic:
```bash
python -m darwinia evolve -g 50 --json   # Full evolution
python -m darwinia arena --json           # Adversarial test
python -m darwinia info --json            # System info
```

## What comes back

After evolution, the agent receives JSON with:
- **Champion DNA** — 17-gene strategy encoding
- **Fitness metrics** — Sharpe, returns, win rate, drawdown
- **Adversarial survival rate** — robustness against manipulation
- **Discovered patterns** — emergent trading rules with human-readable names

## Architecture Alignment

Darwinia aligns with the OpenClaw track requirements:

| Requirement | How Darwinia Implements It |
|-------------|--------------------------|
| Real-world applications | Evolved strategies trade on real BTC market data |
| Multi-step agent workflows | Perceive > Decide > Trade > Survive > Breed > Evolve |
| Tool integrations | Market data, backtesting engine, scenario generation |
| Evaluation & testing | Adversary Agent IS the evaluation system |
| Dev tools & extensions | Evolution framework is reusable for any domain |

## Security

- Runs entirely locally. No external API calls, no data exfiltration.
- Does NOT execute real trades. Simulation only.
- File access limited to reading included CSV data and writing to `output/`.
- No env vars or API keys required.

## Works well with

- **Web search** — Fetch latest data, then evolve strategies on it
- **Notifications** — Alerts when high-fitness strategy discovered
- **Scheduling** — Nightly evolution on updated data
- **Analysis** — Post-process discovered patterns
