# OpenClaw Integration

Darwinia can be used as a skill within the OpenClaw agent framework.

## Installation

```bash
openclaw install github.com/0xSanei/darwinia
```

## Usage

Once installed, your OpenClaw agent can:

### Evolve Strategies
```
"Evolve a trading strategy for BTC using the last 6 months of data"
```
This runs the evolution engine with default parameters and returns the champion agent's DNA.

### Analyze Patterns
```
"What patterns did the evolved agents discover?"
```
Returns discovered patterns with their predictive power and human equivalents.

### Test Robustness
```
"Which attack types are my strategy most vulnerable to?"
```
Runs the adversarial arena against a specific DNA configuration.

## Architecture Alignment

Darwinia aligns with the OpenClaw track requirements:

| Requirement | How Darwinia Implements It |
|-------------|--------------------------|
| Real-world applications | Evolved strategies trade on real BTC market data |
| Multi-step agent workflows | Perceive > Decide > Trade > Survive > Breed > Evolve |
| Tool integrations | Market data, backtesting engine, scenario generation |
| Evaluation & testing | Adversary Agent IS the evaluation system |
| Dev tools & extensions | Evolution framework is reusable for any domain |
