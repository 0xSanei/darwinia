<p align="center">
  <h1 align="center">🧬 Darwinia</h1>
  <p align="center"><strong>The Self-Evolving Agent Ecosystem</strong></p>
  <p align="center">Trading agents that evolve through Darwinian selection and adversarial self-play</p>
</p>

<p align="center">
  <a href="https://github.com/0xSanei/darwinia/actions"><img src="https://img.shields.io/github/actions/workflow/status/0xSanei/darwinia/test.yml?style=flat-square&label=tests" alt="Tests"></a>
  <a href="https://github.com/0xSanei/darwinia/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.9+-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/genes-17-gold?style=flat-square" alt="17 Genes">
  <img src="https://img.shields.io/badge/attacks-6_types-red?style=flat-square" alt="6 Attack Types">
  <img src="https://img.shields.io/badge/tests-22_passing-brightgreen?style=flat-square" alt="22 Tests">
  <img src="https://img.shields.io/badge/status-alpha-orange?style=flat-square" alt="Alpha">
</p>

---

## What if trading agents weren't coded — but evolved?

**Without Darwinia**: You hand-code RSI > 70 = sell. Market changes. Strategy dies.

**With Darwinia**: 50 agents compete on real BTC data. The weak die. The strong breed. After 50 generations, survivors handle rug pulls, fake breakouts, whipsaws — not because you told them to, but because **agents that couldn't handle these attacks didn't survive to reproduce**.

## Quick Start

```bash
git clone https://github.com/0xSanei/darwinia.git
cd darwinia
pip install -e ".[dev]"

# Run 50 generations of evolution on BTC data
python -m darwinia evolve -g 50

# Test a champion against adversarial attacks
python -m darwinia arena

# Launch the interactive dashboard
python -m darwinia dashboard
```

30 seconds to first evolution run. No API keys. No cloud. Just Python + numpy.

<details>
<summary><strong>📺 Demo Output</strong> (click to expand)</summary>

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

## How It Works

```
   Genesis Pool          Adversarial Arena         Pattern Discovery
   ┌──────────┐         ┌───────────────┐         ┌────────────────┐
   │ 50 agents │───────▶│ Alpha agent   │───────▶│ Analyze WHY     │
   │ with random│        │    vs         │        │ survivors won   │
   │ DNA + seeds│        │ Adversary     │        │                 │
   └──────────┘         │ (attacks)     │        │ → Discover new  │
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

Each generation:

1. **Compete**: 50 agents trade on historical BTC candles
2. **Survive**: Agents face targeted adversarial attacks
3. **Select**: Top performers are selected as parents
4. **Breed**: Parents combine DNA through uniform crossover
5. **Mutate**: Gaussian mutations introduce novelty
6. **Discover**: System analyzes WHY winners won

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

## Results

50-generation evolution on 10,946 BTC/USDT 1h candles:

| Metric | Gen 0 | Gen 50 |
|--------|-------|--------|
| Champion Fitness | ~0.15 | ~0.75+ |
| Attack Survival | ~30% | 98-100% |
| Strategy Species | 1 (random) | 3-4 distinct |
| Patterns Found | 0 | 10-20 |

## Architecture

```
darwinia/
├── core/          # DNA, agent, market environment
├── evolution/     # Population, fitness, selection, breeding
├── arena/         # Adversarial attacks and combat
├── discovery/     # Pattern analysis and naming
├── chronicle/     # History recording and species tracking
├── personality/   # Personality profiling + market regime detection
└── __main__.py    # CLI entry point

dashboard/         # Streamlit visualization (4 pages)
scripts/           # Competitor monitoring, utilities
```

### Three Layers

| Layer | Status | What It Does |
|-------|--------|-------------|
| **Evolution Engine** | ✅ Implemented | Genetic algorithm + adversarial arena + pattern discovery |
| **Personality Engine** | ✅ Implemented | Quantified trading personalities + market regime detection |
| **Knowledge Protocol** | 🔮 Designed | Agents trade discovered patterns with each other |

## CLI Reference

```bash
python -m darwinia evolve -g 100 -p 80        # 100 gens, 80 agents
python -m darwinia evolve -d my_data.csv       # Custom data
python -m darwinia arena -c output/champions/champion_gen_0049.json
python -m darwinia arena -r 10                 # 10 rounds
python -m darwinia dashboard                   # Web UI
python -m darwinia info                        # Project info
```

## Dashboard

Four interactive views:

- **Evolution**: Fitness curves + population diversity + gene distributions
- **Family Tree**: Champion ancestry treemap
- **Arms Race**: Attack survival + diversity tradeoff scatter
- **Discoveries**: Convergence radar + linked gene pairs

## OpenClaw Integration

```bash
openclaw install github.com/0xSanei/darwinia
```

Ask your agent: *"Evolve a BTC strategy"*, *"What patterns did agents discover?"*, *"Test my strategy against rug pulls"*

## Design Philosophy

Traditional quant: human designs strategy from theory.
Darwinia: human designs the **environment**. Agents discover the strategy.

Your role shifts from **strategy author** to **environment designer** — define the data, the fitness function, the attacks. Let evolution find the rest.

## License

MIT
