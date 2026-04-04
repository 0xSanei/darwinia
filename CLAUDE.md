# Claude Code Instructions for Darwinia

## Project Type
Python evolutionary trading agent system. Genetic algorithms + adversarial arena.

## Commands
- `python -m darwinia evolve -g 50` — run evolution
- `python -m darwinia arena` — test against attacks
- `python -m darwinia dashboard` — Streamlit UI
- `pytest tests/ -v` — run 16 tests

## Code Style
- Python 3.9+, type hints, dataclasses
- numpy for numerics, no pandas in core
- All genes normalized to [0, 1]

## Key Architecture
- `darwinia/core/` — DNA, agent, market (foundation layer)
- `darwinia/evolution/` — population, fitness, engine (evolution layer)
- `darwinia/arena/` — adversary, arena (testing layer)
- `darwinia/discovery/` — pattern analyzer
- `darwinia/chronicle/` — recorder, speciation tracker

## Testing
```bash
pytest tests/ -v  # 16 tests: DNA, evolution, arena
```

## Adding Features
- New gene: add field to `AgentDNA` in `dna.py`, add to `GENE_FIELDS` list
- New attack: add to `ATTACK_TEMPLATES` in `adversary.py`
- New fitness component: modify `evaluate()` in `fitness.py`
- New indicator: add `_calc_*` method in `agent.py`, wire into `_compute_signal()`
