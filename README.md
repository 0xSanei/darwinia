<p align="center">
  <h1 align="center">🧬 Darwinia</h1>
  <p align="center"><strong>Give your AI agent the power to evolve its own trading strategies.</strong></p>
  <p align="center">Trading agents that discover strategies through Darwinian selection and adversarial self-play — not human-written rules.</p>
</p>

<p align="center">
  <a href="https://github.com/0xSanei/darwinia/actions"><img src="https://img.shields.io/github/actions/workflow/status/0xSanei/darwinia/test.yml?style=flat-square&label=tests" alt="Tests"></a>
  <a href="https://github.com/0xSanei/darwinia/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.9+-blue?style=flat-square" alt="Python">
  <a href="docs/OPENCLAW.md"><img src="https://img.shields.io/badge/OpenClaw-skill-red?style=flat-square" alt="OpenClaw Skill"></a>
  <a href="https://claude.ai"><img src="https://img.shields.io/badge/Claude_Code-compatible-blueviolet?style=flat-square" alt="Claude Code"></a>
  <img src="https://img.shields.io/badge/genes-17-gold?style=flat-square" alt="17 Genes">
  <img src="https://img.shields.io/badge/attacks-6_types-red?style=flat-square" alt="6 Attack Types">
  <img src="https://img.shields.io/badge/tests-125_passing-brightgreen?style=flat-square" alt="125 Tests">
  <a href="https://colab.research.google.com/github/0xSanei/darwinia/blob/main/notebooks/quickstart.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open in Colab"></a>
</p>

<p align="center">
  <img src="docs/screenshots/demo.gif" alt="Darwinia Demo" width="700">
</p>

---

## For OpenClaw / Claude Code agents

```
Tell your agent:

"Install Darwinia and evolve a BTC trading strategy."
```

Darwinia ships as an [OpenClaw skill](.openclaw/SKILL.md) and [Claude Code skill](.claude/SKILL.md). Your agent can install it, run evolution, and report results — all through natural language.

<details>
<summary>Manual skill installation</summary>

**OpenClaw:**
```bash
mkdir -p ~/.openclaw/skills/darwinia
cp .openclaw/SKILL.md ~/.openclaw/skills/darwinia/SKILL.md
```

**Claude Code:** Auto-detected from `.claude/SKILL.md` in project root.

</details>

---

## The problem

You hand-code `RSI > 70 = sell`. Market regime changes. Strategy dies. You tweak parameters manually. Repeat forever.

## The Darwinia approach

50 agents with random DNA compete on real BTC data. The weak die. The strong breed. After 50 generations, survivors handle rug pulls, fake breakouts, and whipsaws — not because you told them to, but because **agents that couldn't handle these attacks didn't survive to reproduce**.

```
Before:  Human writes rules → Agent executes → Market changes → Strategy dies
After:   Human sets environment → Agents evolve → Survivors adapt → Patterns emerge
```

---

## Quick Start

```bash
git clone https://github.com/0xSanei/darwinia.git
cd darwinia
pip install -e ".[dev]"

# Evolve trading strategies (30 seconds)
python -m darwinia evolve -g 10

# Test champion against adversarial attacks
python -m darwinia arena

# Launch interactive dashboard
python -m darwinia dashboard
```

No API keys. No cloud. Just Python + numpy. BTC data included.

<details>
<summary><strong>Demo Output</strong> (click to expand)</summary>

**Evolution run:**
```
🧬 Darwinia — Evolution Engine
   Generations: 20 | Population: 30 | Data: BTC/USDT 1h (10,946 candles)

   Gen   0 | ██████░░░░░░░░░░░░░░ | champ=0.32 avg=0.04 div=1.56
   Gen   1 | █████████████░░░░░░░ | champ=0.69 avg=0.24 div=1.60
   Gen   2 | ███████████████████████████ | champ=1.35 avg=0.64 div=1.32
   Gen   5 | █████████████████████████████ | champ=1.46 avg=0.43 div=0.81
   Gen  12 | █████████████████████ | champ=1.09 avg=0.82 div=0.72
   Gen  13 | ████████████████████████ | champ=1.24 avg=0.64 div=0.57
   Gen  19 | ████████░░░░░░░░░░░░ | champ=0.42 avg=0.12 div=0.44

✅ Evolution complete! 16 patterns discovered.
```

**Adversarial arena test:**
```
⚔️ Darwinia — Adversarial Arena
   Testing evolved champion against targeted attacks...

   whipsaw              | PnL: +0.00% | ✅ survived
   fake_breakout        | PnL: +0.00% | ✅ survived
   pump_and_dump        | PnL: +0.00% | ✅ survived
   rug_pull             | PnL: -3.21% | ✅ survived
   slow_bleed           | PnL: -1.05% | ✅ survived

   Survival rate: 100.0%
```
</details>

---

## How It Works

```
   Genesis Pool          Adversarial Arena         Pattern Discovery
   ┌──────────┐         ┌───────────────┐         ┌────────────────┐
   │ 50 agents │───────▶│ Alpha agent   │───────▶│ Analyze WHY     │
   │ with random│        │    vs         │        │ survivors won   │
   │ DNA + seeds│        │ Adversary     │        │                 │
   └──────────┘         │ (6 attacks)   │        │ → Discover new  │
                        └───────┬───────┘        │   market patterns│
                                │                └────────┬────────┘
                    ┌───────────▼───────────┐             │
                    │   NATURAL SELECTION    │◀────────────┘
                    │                       │
                    │ Top 20% survive       │
                    │ Crossover + Mutation   │
                    │ → Next Generation     │
                    └───────────────────────┘
```

Each generation: **Compete** → **Survive attacks** → **Select** → **Breed** → **Mutate** → **Discover**

### 17-Gene DNA

Every trading decision lives in a genome:

| Category | Genes | Controls |
|----------|-------|----------|
| **Signal** | 5 | What matters — momentum, volume, volatility, mean reversion, trend |
| **Threshold** | 4 | When to act — entry/exit triggers, stop loss, take profit |
| **Personality** | 5 | How to behave — risk appetite, time horizon, contrarian bias, patience, sizing |
| **Adaptation** | 3 | How to learn — regime sensitivity, memory length, noise filtering |

### Adversarial Arena

Most bots are tested against history. Darwinia agents are tested against an **adversary trying to destroy them**.

| Attack | What It Does | Who It Traps |
|--------|-------------|-------------|
| Rug Pull | Steady rise → sudden 90% crash | Trend followers without stops |
| Fake Breakout | Breaks resistance → immediate reversal | Breakout traders |
| Slow Bleed | Gradual decline + misleading bounces | Patient agents with loose stops |
| Whipsaw | Rapid alternating moves | Tight-stop agents |
| Volume Mirage | Volume spike, no follow-through | Volume-dependent strategies |
| Pump & Dump | Rapid pump → rapid dump | Momentum chasers |

The adversary **reads the agent's DNA** and picks attacks targeting its weaknesses. Over generations, this creates an arms race.

### Pattern Discovery

After each generation, Darwinia finds **what survivors agree on**:

- **Gene convergence**: All survivors evolved high noise filtering? That's a pattern.
- **Linked genes**: High risk appetite always paired with short time horizon? That's a combo.
- **Human mapping**: Evolved "high contrarian_bias" = mean reversion strategy.
- **Novel patterns**: Gene combos with no known human equivalent = new discovery.

---

## Results

50-generation evolution on 10,946 BTC/USDT 1h candles:

| Metric | Gen 0 | Gen 50 |
|--------|-------|--------|
| Champion Fitness | ~0.15 | ~0.75+ |
| Attack Survival | ~30% | 98-100% |
| Strategy Species | 1 (random) | 3-4 distinct |
| Patterns Found | 0 | 10-20 |

---

## Agent Integration

All commands support `--json` for machine-readable output:

```bash
python -m darwinia evolve -g 50 --json
```

```json
{
  "champion": {
    "id": "a3f2c1d8",
    "fitness": 1.35,
    "genes": {"weight_trend": 0.87, "stop_loss_pct": 0.04, "risk_appetite": 0.35}
  },
  "evolution_summary": {
    "generations_run": 50,
    "patterns_discovered": 16
  }
}
```

| Platform | Integration |
|----------|-------------|
| **OpenClaw** | `.openclaw/SKILL.md` — [integration guide](docs/OPENCLAW.md) |
| **Claude Code** | `.claude/SKILL.md` — auto-detected in project |
| **Any CLI agent** | `python -m darwinia evolve --json` |

---

## CLI Reference

```bash
python -m darwinia evolve -g 100 -p 80        # 100 gens, 80 agents
python -m darwinia evolve -d my_data.csv       # Custom data
python -m darwinia evolve --json               # JSON output for agents
python -m darwinia arena -c output/champions/champion_gen_0049.json
python -m darwinia arena -r 10 --json          # 10 rounds, JSON output
python -m darwinia validate -w 3 -g 20         # Walk-forward overfitting check
python -m darwinia explain -c champion.json    # Gene ablation analysis
python -m darwinia evolve --multi               # Multi-asset evolution (BTC+ETH+SOL)
python -m darwinia evolve --macro              # Macro-aware evolution (regime overlay)
python -m darwinia fetch ETHUSDT -i 4h -d 90   # Fetch live data from Binance
python -m darwinia fetch BTCUSD --source coingecko  # Fetch from CoinGecko
python -m darwinia scan                        # Discover trending crypto assets
python -m darwinia scan --volatile             # Most volatile assets
python -m darwinia scan --recommend            # Recommended pairs for evolution
python -m darwinia analytics -g 20 -p 50       # Population convergence & clustering
python -m darwinia tournament -n 8 -g 30       # Champion round-robin leaderboard
python -m darwinia repair -c champion.json     # Auto-detect and fix strategy degradation
python -m darwinia dashboard                   # Web UI
python -m darwinia info --json                 # System info as JSON
```

## Dashboard

Four interactive views built with Streamlit:

| Evolution | Family Tree |
|:---------:|:-----------:|
| ![Evolution](docs/screenshots/evolution.png) | ![Family Tree](docs/screenshots/family_tree.png) |
| Fitness metrics + population stats | Champion ancestry treemap |

| Arms Race | Discoveries |
|:---------:|:-----------:|
| ![Arms Race](docs/screenshots/arms_race.png) | ![Discoveries](docs/screenshots/discoveries.png) |
| Fitness under adversarial pressure | Emergent patterns table |

---

## Architecture

```
darwinia/
├── core/          # DNA, agent, market environment
├── evolution/     # Population, fitness, selection, breeding
├── arena/         # Adversarial attacks and combat
├── discovery/     # Pattern analysis and naming
├── chronicle/     # History recording and species tracking
├── personality/   # Personality profiling + market regime detection
├── knowledge/     # Layer 3: Pattern marketplace and knowledge exchange
├── data/          # Live data fetching (Binance, CoinGecko)
├── macro/         # Macro regime simulation and regime-aware fitness
├── integrations/  # Skill composability layer (SkillBridge, SkillRegistry)
├── analytics/     # Population statistics, clustering, diversity metrics
├── repair/        # Self-repair: health monitoring + auto-fix degraded strategies
└── __main__.py    # CLI entry point (13 commands)

dashboard/         # Streamlit visualization (4 pages)
scripts/           # Competitor monitoring, utilities
```

### Validation & Explainability

**Walk-Forward Validation** splits data chronologically (train on past, test on future). If fitness degrades out-of-sample, the strategy is overfitting.

```bash
python -m darwinia validate -w 3 --json
```

**Gene Ablation** zeroes each gene one at a time and measures fitness drop. Genes that cause the biggest drop are the most important — proving the agent found real signal, not noise.

```bash
python -m darwinia explain -c champion.json --json
```

### Macro-Aware Evolution

Standard backtests ignore macro conditions. With `--macro`, Darwinia generates a regime overlay (risk-on, risk-off, transition) and rewards agents that adapt position sizing to macro state. Agents that go full-size during risk-off get penalized. Agents that scale down survive.

```bash
python -m darwinia evolve --macro --json
```

### Asset Auto-Discovery

Instead of hardcoding which asset to train on, `scan` finds high-volume volatile assets — the best training data for genetic evolution.

```bash
python -m darwinia scan --recommend --json
```

### Self-Repair

Strategies degrade as markets shift. `repair` monitors fitness drift and applies targeted fixes — re-randomizing only the weakest genes instead of re-evolving from scratch.

```bash
python -m darwinia repair -c champion.json --method targeted --json
```

Three repair modes: `targeted` (fix weak genes via ablation), `full` (re-evolve from seed), `ensemble` (mutate 3 variants, pick best).

### Skill Composability

Darwinia exposes a `SkillBridge` API for other ClawHub skills to call it programmatically, and a `SkillRegistry` for Darwinia to call external skills (macro-liquidity, crypto-market-rank, okx-dex-market). This makes Darwinia a composable building block in multi-skill agent workflows.

### Three Layers

| Layer | Status | What It Does |
|-------|--------|-------------|
| **Evolution Engine** | ✅ Implemented | Genetic algorithm + adversarial arena + pattern discovery |
| **Personality Engine** | ✅ Implemented | Quantified trading personalities + market regime detection |
| **Knowledge Protocol** | ✅ Implemented | Agents trade discovered patterns through a marketplace |

---

## Beyond Trading

The evolution engine is **domain-agnostic**. The DNA → Fitness → Selection → Breed cycle works for any agent behavior that can be scored. This release targets crypto trading, but the framework applies to portfolio optimization, risk tuning, resource allocation, game strategy — any domain where you can define a fitness function.

---

## Development

```bash
make setup       # Install dependencies
make test        # Run 125 tests
make evolve      # Run 50 generations
make arena       # Adversarial arena
make dashboard   # Streamlit dashboard
```

## Design Philosophy

Traditional quant: human designs strategy from theory.
Darwinia: human designs the **environment**. Agents discover the strategy.

Your role shifts from **strategy author** to **environment designer** — define the data, the fitness function, the attacks. Let evolution find the rest.

## License

MIT
