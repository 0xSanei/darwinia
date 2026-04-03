# Darwinia Architecture

## System Overview

Darwinia is a three-layer ecosystem. Layer 1 is fully implemented.

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

## Layer 1: Evolution Engine

### Data Flow

```
Market Data (OHLCV)
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  Population  │────▶│ TradingAgent │──▶ Trades
│  (50 DNAs)   │     │ (per agent)  │
└─────────────┘     └──────────────┘
       │                    │
       │              ┌─────▼──────┐
       │              │  Fitness   │
       │              │ Evaluator  │
       │              └─────┬──────┘
       │                    │
       │    ┌───────────────▼───────────────┐
       │    │     Adversarial Arena          │
       │    │  (targeted attack scenarios)   │
       │    └───────────────┬───────────────┘
       │                    │
       │              ┌─────▼──────┐
       │              │ Selection  │
       │              │ + Breeding │
       │              └─────┬──────┘
       │                    │
       └────────────────────┘  (next generation)
```

### Key Design Decisions

1. **DNA in [0,1] range**: All genes are floats between 0 and 1. This makes crossover and mutation uniform across all gene types.

2. **Lazy imports**: Arena, Discovery, and Chronicle are lazily imported to avoid circular dependencies and allow running core evolution without all modules.

3. **Multiple data slices**: Each generation evaluates agents on 3 random slices of market data (seeded per generation for fairness). This reduces noise.

4. **Composite fitness**: Not just PnL. Sharpe ratio (35%), raw return (25%), win rate (15%), drawdown penalty (15%), survival bonus (10%).

5. **Targeted attacks**: The Adversary reads the Alpha's DNA to choose attacks that exploit specific weaknesses, creating a meaningful arms race.

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `core/dna.py` | Gene encoding, crossover, mutation, serialization |
| `core/agent.py` | Interpret DNA into trading decisions on OHLCV data |
| `core/market.py` | Load and serve market data |
| `evolution/population.py` | Initialize, select parents, breed next generation |
| `evolution/fitness.py` | Evaluate trade results into composite fitness |
| `evolution/engine.py` | Orchestrate the full evolution loop |
| `arena/adversary.py` | Generate targeted attack scenarios |
| `arena/arena.py` | Run agents against attacks, track history |
| `discovery/analyzer.py` | Analyze gene convergence and combinations |
| `chronicle/recorder.py` | Save generation data to JSON files |
| `chronicle/speciation.py` | Cluster agents into strategy species |
