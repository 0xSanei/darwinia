"""
Backtesting engine — run evolved strategies against historical data
with walk-forward windows and full performance analysis.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

from ..core.dna import AgentDNA
from ..core.agent import TradingAgent
from ..core.market import MarketEnvironment
from .metrics import PerformanceMetrics, compute_metrics


class BacktestEngine:
    """
    Run a strategy (AgentDNA) against market data with configurable
    train/test splits and performance reporting.

    Supports:
    - Single-pass backtest on full data
    - Walk-forward backtest with rolling windows
    - Multi-asset backtest across all available CSVs
    - Comparative backtest (multiple strategies, same data)
    """

    def __init__(
        self,
        data_dir: str = 'data',
        initial_capital: float = 10000.0,
        candles_per_year: float = 365 * 24,
    ):
        self.market = MarketEnvironment(data_dir)
        self.initial_capital = initial_capital
        self.candles_per_year = candles_per_year

    def run(
        self,
        dna: AgentDNA,
        data_file: str,
        train_ratio: float = 0.0,
    ) -> Dict:
        """
        Run backtest on a single asset.

        Args:
            dna: Strategy DNA to test
            data_file: CSV file in data directory
            train_ratio: If > 0, split data and test only on unseen portion

        Returns:
            Dict with metrics, trades, and metadata
        """
        candles = self.market.load_csv(data_file)

        if train_ratio > 0:
            split = int(len(candles) * train_ratio)
            test_candles = candles[split:]
            label = f"out-of-sample ({1 - train_ratio:.0%})"
        else:
            test_candles = candles
            label = "full dataset"

        agent = TradingAgent(dna)
        agent.state.cash = self.initial_capital
        trades = agent.run(test_candles)
        metrics = compute_metrics(trades, self.initial_capital, self.candles_per_year)

        return {
            'asset': Path(data_file).stem,
            'label': label,
            'candles': len(test_candles),
            'metrics': metrics,
            'trades': trades,
            'dna_id': dna.id,
        }

    def walk_forward(
        self,
        dna: AgentDNA,
        data_file: str,
        n_windows: int = 5,
        train_pct: float = 0.7,
    ) -> Dict:
        """
        Walk-forward backtest with rolling windows.

        Divides data into overlapping windows, each with a train/test split.
        Reports per-window and aggregate metrics.
        """
        candles = self.market.load_csv(data_file)
        total = len(candles)
        window_size = total // n_windows
        step = max(1, (total - window_size) // max(1, n_windows - 1))

        window_results = []
        all_trades = []

        for i in range(n_windows):
            start = i * step
            end = min(start + window_size, total)
            window = candles[start:end]

            train_end = int(len(window) * train_pct)
            test_data = window[train_end:]

            if len(test_data) < 10:
                continue

            agent = TradingAgent(dna)
            agent.state.cash = self.initial_capital
            trades = agent.run(test_data)
            metrics = compute_metrics(trades, self.initial_capital, self.candles_per_year)

            window_results.append({
                'window': i + 1,
                'test_candles': len(test_data),
                'metrics': metrics.to_dict(),
                'num_trades': len(trades),
            })
            all_trades.extend(trades)

        # Aggregate metrics across all windows
        agg_metrics = compute_metrics(all_trades, self.initial_capital, self.candles_per_year)

        return {
            'asset': Path(data_file).stem,
            'mode': 'walk-forward',
            'n_windows': n_windows,
            'windows': window_results,
            'aggregate': agg_metrics,
            'total_trades': len(all_trades),
        }

    def compare(
        self,
        dna_list: List[AgentDNA],
        data_file: str,
        labels: Optional[List[str]] = None,
    ) -> Dict:
        """
        Compare multiple strategies on the same data.
        Returns ranked results by Sharpe ratio.
        """
        results = []
        for i, dna in enumerate(dna_list):
            label = labels[i] if labels and i < len(labels) else f"strategy_{dna.id}"
            r = self.run(dna, data_file)
            results.append({
                'label': label,
                'dna_id': dna.id,
                'metrics': r['metrics'].to_dict(),
                'num_trades': len(r['trades']),
            })

        # Rank by Sharpe
        results.sort(key=lambda x: x['metrics']['sharpe_ratio'], reverse=True)
        for rank, r in enumerate(results):
            r['rank'] = rank + 1

        return {
            'asset': Path(data_file).stem,
            'mode': 'comparative',
            'strategies': len(dna_list),
            'results': results,
        }

    def multi_asset(
        self,
        dna: AgentDNA,
    ) -> Dict:
        """
        Run a strategy across all available assets.
        Tests generalization — a good strategy works on multiple markets.
        """
        available = self.market.list_available()
        if not available:
            return {'error': 'No data files found', 'results': []}

        results = []
        for f in available:
            try:
                r = self.run(dna, f)
                results.append({
                    'asset': r['asset'],
                    'metrics': r['metrics'].to_dict(),
                    'num_trades': len(r['trades']),
                })
            except Exception as e:
                results.append({
                    'asset': Path(f).stem,
                    'error': str(e),
                })

        # Rank by Sharpe
        valid = [r for r in results if 'metrics' in r]
        valid.sort(key=lambda x: x['metrics']['sharpe_ratio'], reverse=True)

        avg_sharpe = np.mean([r['metrics']['sharpe_ratio'] for r in valid]) if valid else 0
        avg_return = np.mean([r['metrics']['total_return_pct'] for r in valid]) if valid else 0

        return {
            'mode': 'multi-asset',
            'assets_tested': len(available),
            'assets_succeeded': len(valid),
            'avg_sharpe': round(float(avg_sharpe), 4),
            'avg_return_pct': round(float(avg_return), 4),
            'results': results,
        }
