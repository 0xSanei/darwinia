# DNA Encoding

## Gene Structure

Every agent has a 17-gene genome. All genes are floats in [0, 1].

### Signal Weights (5 genes)
Control what market signals the agent pays attention to:
- `weight_price_momentum`: Price rate of change
- `weight_volume`: Volume anomaly detection
- `weight_volatility`: Volatility regime signal
- `weight_mean_reversion`: Distance from moving average
- `weight_trend`: EMA crossover direction

### Thresholds (4 genes)
Control when the agent enters and exits:
- `entry_threshold`: Mapped to [0.05, 0.35] — signal strength needed to enter
- `exit_threshold`: Mapped to [-0.35, -0.05] — signal strength needed to exit
- `stop_loss_pct`: Mapped to [0%, 20%] — max loss before forced exit
- `take_profit_pct`: Mapped to [0%, 50%] — profit target

### Personality (5 genes)
Control behavioral traits:
- `risk_appetite`: 0=ultra conservative, 1=maximum risk
- `time_horizon`: 0=scalper (10 candles), 1=swing (200 candles)
- `contrarian_bias`: 0=pure trend follower, 1=pure contrarian
- `patience`: 0=instant action, 1=wait for confirmation
- `position_sizing`: 0=10% allocation, 1=100% allocation

### Adaptation (3 genes)
Control information processing:
- `regime_sensitivity`: How quickly it detects regime changes
- `memory_length`: How far back it looks
- `noise_filter`: How aggressively it filters noise

## Crossover

Uniform crossover: for each gene, 50/50 chance of inheriting from either parent.

## Mutation

Gaussian mutation: each gene has `mutation_rate` probability of being mutated.
Mutation adds `gauss(0, mutation_strength)` to the gene value, clamped to [0, 1].
