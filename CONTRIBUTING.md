# Contributing to Darwinia

Darwinia welcomes contributions. Here's how to get started.

## Setup

```bash
git clone https://github.com/0xSanei/darwinia.git
cd darwinia
pip install -e ".[all]"
make test
```

## Development workflow

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Run `pytest tests/ -v` — all 84 tests must pass
4. Submit a PR with a clear description

## What to contribute

**High impact:**
- New adversarial attack types (see `darwinia/arena/adversary.py`)
- Custom fitness functions (see `examples/custom_fitness.py`)
- New seed archetypes in `darwinia/core/dna.py`
- Dashboard visualizations
- Domain adaptations (not just trading — any environment with a fitness function)

**Always welcome:**
- Bug fixes
- Test coverage improvements
- Documentation improvements
- Performance optimizations

## Architecture

```
darwinia/
├── core/          # DNA, agent, market environment — the primitives
├── evolution/     # Population, fitness, selection, breeding — the loop
├── arena/         # Adversarial attacks — the pressure
├── discovery/     # Pattern analysis — the insight
├── chronicle/     # History recording — the memory
├─��� personality/   # Profiling + regime detection — the context
├── knowledge/     # Pattern marketplace and knowledge exchange
├── data/          # Live data fetching (Binance, CoinGecko)
├── macro/         # Macro regime simulation and regime-aware fitness
├── integrations/  # Skill composability (SkillBridge, SkillRegistry)
└── validation/    # Walk-forward validation and gene ablation
```

The evolution engine is domain-agnostic. To adapt Darwinia to a new domain:
1. Define your agent (equivalent of `TradingAgent`)
2. Define your environment (equivalent of `MarketEnvironment`)
3. Define your fitness function (extend `FitnessEvaluator`)
4. Optionally define adversarial scenarios

## Code style

- Type hints on public functions
- Docstrings on classes and public methods
- Tests for new features
- No hardcoded secrets or API keys

## Reporting issues

Use [GitHub Issues](https://github.com/0xSanei/darwinia/issues). Include:
- What you expected
- What happened instead
- Steps to reproduce
- Python version and OS
