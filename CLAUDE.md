# Claude Code Instructions for Darwinia

## Project Type
Python evolutionary trading agent system. Genetic algorithms + adversarial arena.

## Commands
- `python -m darwinia evolve -g 50` — run evolution
- `python -m darwinia evolve --multi` — multi-asset evolution
- `python -m darwinia evolve --macro` — macro-aware evolution
- `python -m darwinia arena` — test against attacks
- `python -m darwinia validate` — walk-forward overfitting check
- `python -m darwinia explain` — gene ablation analysis
- `python -m darwinia fetch` — fetch live data from Binance/CoinGecko
- `python -m darwinia scan` — discover trending/volatile assets
- `python -m darwinia dashboard` — Streamlit UI
- `python -m darwinia info` — system info
- `pytest tests/ -v` — run 84 tests

## Code Style
- Python 3.9+, type hints, dataclasses
- numpy for numerics, no pandas in core
- All genes normalized to [0, 1]
- All text in English (no Chinese)

## Key Architecture
- `darwinia/core/` — DNA, agent, market (foundation layer)
- `darwinia/evolution/` — population, fitness, engine (evolution loop)
- `darwinia/arena/` — adversary, arena (adversarial testing)
- `darwinia/discovery/` — pattern analyzer, gene explainer, asset scanner
- `darwinia/chronicle/` — recorder, speciation tracker
- `darwinia/personality/` — profiling + regime detection
- `darwinia/knowledge/` — Layer 3: pattern marketplace
- `darwinia/data/` — live data fetching (Binance, CoinGecko)
- `darwinia/macro/` — macro regime simulation + regime-aware fitness
- `darwinia/integrations/` — skill composability (SkillBridge, SkillRegistry)
- `darwinia/validation/` — walk-forward validation

## Testing
```bash
pytest tests/ -v  # 84 tests across 10 test files
```

## Adding Features
- New gene: add field to `AgentDNA` in `dna.py`, add to `GENE_FIELDS` list
- New attack: add to `ATTACK_TEMPLATES` in `adversary.py`
- New fitness component: modify `evaluate()` in `fitness.py`
- New indicator: add `_calc_*` method in `agent.py`, wire into `_compute_signal()`
- New data source: add method to `DataFetcher` in `data/fetcher.py`
- New skill integration: add template to `SkillRegistry` in `integrations/skill_bridge.py`
