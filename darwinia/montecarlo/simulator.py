"""
Monte Carlo simulation for stress-testing evolved trading strategies.

Runs a strategy against many randomized variations of market data to
estimate robustness, confidence intervals, and probability of profit.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple

from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from ..core.market import MarketEnvironment
from ..backtest.metrics import compute_metrics


@dataclass
class MonteCarloResult:
    """Aggregated results from Monte Carlo simulation runs."""
    n_simulations: int = 0
    confidence_95: Tuple[float, float] = (0.0, 0.0)
    confidence_99: Tuple[float, float] = (0.0, 0.0)
    mean_return: float = 0.0
    median_return: float = 0.0
    worst_case: float = 0.0
    best_case: float = 0.0
    probability_of_profit: float = 0.0
    return_distribution: List[float] = field(default_factory=list)
    sharpe_distribution: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict, excluding distribution lists for compact output."""
        return {
            'n_simulations': self.n_simulations,
            'confidence_95': [round(self.confidence_95[0], 4), round(self.confidence_95[1], 4)],
            'confidence_99': [round(self.confidence_99[0], 4), round(self.confidence_99[1], 4)],
            'mean_return': round(self.mean_return, 4),
            'median_return': round(self.median_return, 4),
            'worst_case': round(self.worst_case, 4),
            'best_case': round(self.best_case, 4),
            'probability_of_profit': round(self.probability_of_profit, 4),
        }

    def summary(self) -> str:
        """Human-readable formatted output."""
        lines = [
            f"{'─' * 52}",
            f"  MONTE CARLO SIMULATION REPORT",
            f"  Simulations: {self.n_simulations}",
            f"{'─' * 52}",
            f"  Mean Return:         {self.mean_return:>+10.2%}",
            f"  Median Return:       {self.median_return:>+10.2%}",
            f"  Best Case:           {self.best_case:>+10.2%}",
            f"  Worst Case:          {self.worst_case:>+10.2%}",
            f"{'─' * 52}",
            f"  95% Confidence:      [{self.confidence_95[0]:>+.2%}, {self.confidence_95[1]:>+.2%}]",
            f"  99% Confidence:      [{self.confidence_99[0]:>+.2%}, {self.confidence_99[1]:>+.2%}]",
            f"  P(Profit):           {self.probability_of_profit:>10.2%}",
            f"{'─' * 52}",
        ]
        if self.sharpe_distribution:
            sharpes = np.array(self.sharpe_distribution)
            lines.insert(-1, f"  Median Sharpe:       {float(np.median(sharpes)):>10.4f}")
        return '\n'.join(lines)


class MonteCarloSimulator:
    """
    Stress-test a trading strategy by running it against many
    randomized variations of market data.
    """

    VALID_METHODS = ('bootstrap', 'noise', 'shuffle')

    def __init__(
        self,
        data_dir: str = 'data',
        n_simulations: int = 1000,
        initial_capital: float = 10000.0,
    ) -> None:
        self.data_dir = data_dir
        self.n_simulations = n_simulations
        self.initial_capital = initial_capital
        self._rng = np.random.default_rng()

    def run(
        self,
        dna: AgentDNA,
        data_file: str,
        method: str = 'bootstrap',
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation.

        Args:
            dna: The strategy DNA to test.
            data_file: CSV filename to load from data_dir.
            method: One of 'bootstrap', 'noise', 'shuffle'.

        Returns:
            MonteCarloResult with aggregated statistics.
        """
        if method not in self.VALID_METHODS:
            raise ValueError(f"Unknown method '{method}'. Must be one of {self.VALID_METHODS}")

        # Load original market data
        market = MarketEnvironment(data_dir=self.data_dir)
        candles = market.load_csv(data_file)

        # Pick the randomization function
        randomize = {
            'bootstrap': self._bootstrap,
            'noise': self._noise,
            'shuffle': self._shuffle,
        }[method]

        returns: List[float] = []
        sharpes: List[float] = []

        for _ in range(self.n_simulations):
            sim_candles = randomize(candles)
            agent = TradingAgent(dna)
            agent.state.cash = self.initial_capital
            trades = agent.run(sim_candles)
            metrics = compute_metrics(trades, initial_capital=self.initial_capital)
            returns.append(metrics.total_return_pct)
            sharpes.append(metrics.sharpe_ratio)

        return self._build_result(returns, sharpes)

    def _bootstrap(self, candles: np.ndarray) -> np.ndarray:
        """
        Block bootstrap: resample candles with replacement in blocks.
        Block size = 20 candles. Preserves local temporal structure.
        """
        n = len(candles)
        # Adaptive block size: at least 1, at most 20, scale with data length
        block_size = max(1, min(20, n // 5))
        n_blocks = max(n // block_size, 1)

        # Number of valid block start indices
        max_start = n - block_size
        if max_start < 0:
            max_start = 0

        # Sample block start indices with replacement
        starts = self._rng.integers(0, max_start + 1, size=n_blocks)

        blocks = [candles[s:s + block_size] for s in starts]
        result = np.concatenate(blocks, axis=0)

        # Fix timestamps to be sequential
        result = result.copy()
        result[:, 0] = np.arange(len(result), dtype=float)
        return result

    def _noise(self, candles: np.ndarray) -> np.ndarray:
        """
        Add random noise to OHLC prices.
        Noise std = 0.5% of each price value. Volume unchanged.
        """
        result = candles.copy()
        # Columns 1-4 are O, H, L, C
        ohlc = result[:, 1:5]
        noise_std = ohlc * 0.005  # 0.5% of price
        noise = self._rng.normal(0, 1, size=ohlc.shape) * noise_std
        ohlc_noisy = ohlc + noise

        # Ensure prices stay positive — use relative floor (10% of min price)
        price_floor = max(ohlc.min() * 0.1, 1e-8)
        ohlc_noisy = np.maximum(ohlc_noisy, price_floor)

        # Maintain OHLC consistency: high >= open,close; low <= open,close
        opens = ohlc_noisy[:, 0]
        closes = ohlc_noisy[:, 3]
        highs = np.maximum(ohlc_noisy[:, 1], np.maximum(opens, closes))
        lows = np.minimum(ohlc_noisy[:, 2], np.minimum(opens, closes))
        ohlc_noisy[:, 1] = highs
        ohlc_noisy[:, 2] = lows

        result[:, 1:5] = ohlc_noisy
        return result

    def _shuffle(self, candles: np.ndarray) -> np.ndarray:
        """
        Shuffle returns and reconstruct prices.
        Computes per-candle returns, shuffles them, then rebuilds
        OHLC from the shuffled return sequence.
        """
        n = len(candles)
        if n < 2:
            return candles.copy()

        closes = candles[:, 4]
        # Compute log returns
        log_returns = np.diff(np.log(np.maximum(closes, 1e-8)))

        # Shuffle returns
        shuffled_returns = log_returns.copy()
        self._rng.shuffle(shuffled_returns)

        # Reconstruct close prices from shuffled returns
        new_closes = np.empty(n)
        new_closes[0] = closes[0]
        new_closes[1:] = closes[0] * np.exp(np.cumsum(shuffled_returns))

        # Reconstruct OHLC using original ratios relative to close
        result = candles.copy()
        old_closes = np.maximum(closes, 1e-8)
        scale = new_closes / old_closes

        result[:, 1] *= scale  # Open
        result[:, 2] *= scale  # High
        result[:, 3] *= scale  # Low
        result[:, 4] = new_closes  # Close
        # Volume stays the same, timestamps stay the same

        # Ensure positivity and OHLC consistency
        price_floor = max(candles[:, 4].min() * 0.1, 1e-8)
        result[:, 1:5] = np.maximum(result[:, 1:5], price_floor)
        # high >= max(open, close), low <= min(open, close)
        result[:, 2] = np.maximum(result[:, 2], np.maximum(result[:, 1], result[:, 4]))
        result[:, 3] = np.minimum(result[:, 3], np.minimum(result[:, 1], result[:, 4]))
        return result

    def _build_result(
        self,
        returns: List[float],
        sharpes: List[float],
    ) -> MonteCarloResult:
        """Build MonteCarloResult from collected simulation outputs."""
        ret_arr = np.array(returns)
        n = len(ret_arr)

        sorted_ret = np.sort(ret_arr)

        # Percentile-based confidence intervals
        ci_95 = (float(np.percentile(sorted_ret, 2.5)), float(np.percentile(sorted_ret, 97.5)))
        ci_99 = (float(np.percentile(sorted_ret, 0.5)), float(np.percentile(sorted_ret, 99.5)))

        return MonteCarloResult(
            n_simulations=n,
            confidence_95=ci_95,
            confidence_99=ci_99,
            mean_return=float(np.mean(ret_arr)),
            median_return=float(np.median(ret_arr)),
            worst_case=float(ret_arr.min()),
            best_case=float(ret_arr.max()),
            probability_of_profit=float(np.sum(ret_arr > 0) / n) if n > 0 else 0.0,
            return_distribution=returns,
            sharpe_distribution=sharpes,
        )
