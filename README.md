# Darwinia — The Self-Evolving Agent Ecosystem

> What if trading agents weren't coded — but evolved?

Darwinia is an ecosystem where autonomous agents develop trading strategies through **Darwinian evolution** and **adversarial self-play**. Instead of a human writing rules, agents compete, breed, and mutate over hundreds of generations — discovering market patterns that no human programmed.

After 100 generations, Darwinia's evolved agents have survived every known market attack pattern — rug pulls, fake breakouts, sandwich attacks, slow bleeds — not because someone told them about these dangers, but because **they evolved defenses through combat**.

## How It Works

### The Evolution Loop

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

1. **Compete**: 50 agents trade on historical market data
2. **Survive**: Agents face adversarial attack scenarios (rug pulls, fake breakouts, etc.)
3. **Select**: Top performers are selected as parents
4. **Breed**: Parents combine DNA through crossover
5. **Mutate**: Random mutations introduce novelty
6. **Discover**: The system analyzes WHY winners won — what patterns did they exploit?

### Agent DNA

Every trading decision is encoded in a **17-gene genome**:

| Gene Category | Genes | What It Controls |
|--------------|-------|-----------------|
| **Signal Weights** | 5 genes | What the agent pays attention to (momentum, volume, volatility, mean reversion, trend) |
| **Thresholds** | 4 genes | When the agent acts (entry/exit triggers, stop loss, take profit) |
| **Personality** | 5 genes | How the agent behaves (risk appetite, time horizon, contrarian bias, patience, position sizing) |
| **Adaptation** | 3 genes | How the agent processes information (regime sensitivity, memory length, noise filtering) |

These genes are inherited, combined, and mutated across generations — just like biological evolution.

### Adversarial Arena

Most trading bots are tested against historical data. Darwinia agents are tested against an **adversary that's trying to destroy them**.

The Adversary Agent generates targeted attack scenarios:

| Attack | Description | Exploits |
|--------|-------------|----------|
| Rug Pull | Steady rise then sudden 90% crash | Trend followers who don't set stops |
| Fake Breakout | Breaks resistance then immediate reversal | Breakout traders |
| Slow Bleed | Gradual decline with misleading bounces | Patient agents with loose stops |
| Whipsaw | Rapid alternating movements | Agents with tight stops |
| Volume Mirage | Fake volume spike, no follow-through | Volume-dependent strategies |
| Pump & Dump | Rapid pump then equally rapid dump | Momentum chasers |

**The attacks are targeted**: the Adversary reads the Alpha's DNA and chooses attacks that exploit its specific weaknesses. Trend followers get fake breakouts. Momentum chasers get pump-and-dumps.

Over generations, this creates an **arms race**: agents evolve stronger defenses, the adversary evolves more creative attacks.

### Pattern Discovery

After each generation, Darwinia analyzes the survivors to understand **what they learned**:

- **Gene convergence**: Did all survivors develop similar traits? (e.g., every successful agent evolved high noise filtering)
- **Gene combinations**: Are certain gene pairs always linked? (e.g., high risk appetite + short time horizon)
- **Human equivalents**: Does an evolved pattern match a known trading concept? (e.g., evolved "high contrarian_bias" = human "mean reversion strategy")
- **Novel patterns**: Did agents discover something new? (gene combinations with no known human equivalent)

## Quick Start

```bash
git clone https://github.com/0xSanei/darwinia.git
cd darwinia
pip install -r requirements.txt

# Run evolution (50 generations, 50 agents)
make evolve GENERATIONS=50

# Launch interactive dashboard
make dashboard

# Run adversarial arena battles
make arena
```

## Architecture

```
darwinia/
├── core/          # DNA encoding, trading agent, market environment
├── evolution/     # Population management, fitness, selection, breeding
├── arena/         # Adversarial attack generation and combat
├── discovery/     # Pattern analysis and auto-naming
├── chronicle/     # Evolution history recording and reporting
└── utils/         # Configuration, logging, data loading

dashboard/         # Streamlit visualization (4 interactive pages)
```

### Three-Layer Ecosystem Design

```
┌──────────────────────────────────────────────────────────┐
│  LAYER 3: KNOWLEDGE PROTOCOL                   [v2]      │
│  Agents trade discovered patterns with each other         │
├──────────────────────────────────────────────────────────┤
│  LAYER 2: PERSONALITY ENGINE                   [v2]      │
│  Quantified trading personalities + Regime switching      │
├──────────────────────────────────────────────────────────┤
│  LAYER 1: EVOLUTION ENGINE              [Implemented]     │
│  Genetic algorithm + Adversarial arena + Pattern discovery │
└──────────────────────────────────────────────────────────┘
```

Layer 1 is fully implemented. Layers 2 and 3 represent the designed future of the ecosystem.

## Key Results

After a typical 50-generation evolution on BTC 1-hour data (10,946 candles):

- **Fitness improvement**: Champion fitness increases 3-5x from generation 0 to 50
- **Attack survival**: Survival rate against adversarial attacks rises from ~30% (gen 0) to ~98-100% (gen 50)
- **Convergence**: The population converges on 3-4 distinct "species" of trading strategy
- **Discovery**: Agents typically discover 10-20 statistically significant patterns, many mapping to known human trading concepts

## Visualization

The Streamlit dashboard provides four interactive views:

1. **Evolution**: Fitness curves, population diversity, gene distributions over time
2. **Family Tree**: Interactive ancestry tree of champion agents
3. **Arms Race**: Attack survival rates and adversarial co-evolution
4. **Discoveries**: Agent-discovered patterns vs. known human indicators

## OpenClaw Integration

Darwinia can be used as an OpenClaw skill for strategy development:

```bash
openclaw install github.com/0xSanei/darwinia
```

Then ask your OpenClaw agent:
- "Evolve a trading strategy for BTC using the last 6 months of data"
- "What patterns did the evolved agents discover?"
- "Which attack types are my strategy most vulnerable to?"

## Design Philosophy

Traditional quant approaches design strategies from theory. Darwinia discovers strategies from evolution. The human's role shifts from **strategy author** to **environment designer** — you define the market data, the fitness function, and the attack patterns. The agents find the strategies.

## License

MIT
