# Changelog

All notable changes to Darwinia are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [1.3.0] - 2026-04-08

### Added
- Ensemble committee system — multi-agent voting with majority, weighted, and unanimous modes
- Monte Carlo stress testing — bootstrap, noise injection, and return shuffling (configurable N simulations)
- Benchmark baselines — compare evolved strategies against Buy-and-Hold, Random, Mean Reversion, Momentum, and DCA
- Strategy fingerprint — ASCII radar chart visualization, archetype classification, dominant trait detection, cosine similarity comparison
- `ensemble`, `montecarlo`, `benchmark`, `fingerprint` CLI commands

### Changed
- CLI now has 19 commands (up from 15)
- 18 modules total (added ensemble, montecarlo, benchmark, fingerprint)
- 176 tests (up from 140)

## [1.2.0] - 2026-04-08

### Added
- Backtesting engine with full quantitative performance metrics (Sharpe, Sortino, Calmar, max drawdown, profit factor, win rate)
- Walk-forward backtesting with rolling windows for stability analysis
- Multi-asset backtesting to test strategy generalization across markets
- Comparative backtesting to rank multiple strategies on the same data
- Strategy export/import as portable JSON (`darwinia-strategy-v1` format)
- `backtest` CLI command with `--walk-forward`, `--multi`, `--train-ratio` flags
- `export` CLI command for strategy serialization

### Changed
- CLI now has 15 commands (up from 13)
- Info command updated with new command listing

## [1.1.0] - 2026-04-07

### Added
- Population analytics with convergence scoring, clustering, and diversity metrics
- Tournament mode for champion round-robin competition with leaderboard
- Macro-aware evolution with regime detection (risk-on, risk-off, transition overlay)
- Asset auto-discovery via `scan` command (trending, volatile, recommended pairs)
- Skill composability layer with SkillBridge and SkillRegistry for multi-skill agent workflows
- Multi-asset evolution (`--multi` flag) to train across all CSVs in data directory
- Live data fetching from Binance and CoinGecko via `fetch` command
- Layer 3 Knowledge Protocol for trading discovered patterns through a marketplace
- Archetype benchmarks comparing all seed strategies

### Changed
- `info` command now displays all 12 available commands
- README updated with full CLI reference, architecture diagram, and badge counts

### Fixed
- Hardened error handling across CLI commands
- Fixed Windows path resolution bug in data loading

## [1.0.0] - 2026-04-04

### Added
- Core genetic algorithm engine with 17-gene DNA and natural selection
- Adversarial arena with 6 attack types (rug pull, fake breakout, slow bleed, whipsaw, volume mirage, pump & dump)
- Pattern discovery system that identifies gene convergence and linked-gene combos
- Walk-forward validation for overfitting detection
- Gene ablation explainability system
- Layer 2 Personality Engine with quantified trading personalities and market regime detection
- CLI entry point with `evolve`, `arena`, `validate`, `explain`, and `dashboard` commands
- `--json` output flag on all commands for agent integration
- Streamlit dashboard with 4 interactive views (evolution, family tree, arms race, discoveries)
- OpenClaw and Claude Code skill integration
- Colab quickstart notebook for one-click demo
- Animated demo GIF
- CI pipeline with coverage reporting and CLI smoke tests
- Comprehensive test suite
- pyproject.toml with full metadata and entry points
- BTC/USDT 1h sample data included
