# Darwinia — Installation Guide

## One-Line Install

```bash
git clone https://github.com/0xSanei/darwinia.git && cd darwinia && pip install -e ".[dev]"
```

Requirements: Python 3.9+. No API keys, no cloud, ~50MB disk.
Data (10,946 BTC/USDT 1h candles) included in repo.

## Verify

```bash
python -m darwinia info
```

## For OpenClaw

```bash
mkdir -p ~/.openclaw/skills/darwinia
cp .openclaw/SKILL.md ~/.openclaw/skills/darwinia/SKILL.md
```

Then: "Use Darwinia to evolve a trading strategy."

## For Claude Code

Auto-detected from `.claude/SKILL.md` in project root.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: numpy` | `pip install numpy` |
| `FileNotFoundError: data/btc_1h.csv` | `make data` |
| Dashboard won't load | `pip install streamlit plotly` |
