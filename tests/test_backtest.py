"""Tests for the backtesting engine and performance metrics."""

import numpy as np
import pytest
from darwinia.core.dna import AgentDNA
from darwinia.core.types import TradeResult
from darwinia.backtest.metrics import PerformanceMetrics, compute_metrics
from darwinia.backtest.engine import BacktestEngine


def _make_candles(n=500, seed=42):
    """Generate synthetic candle data for testing."""
    np.random.seed(seed)
    prices = 100 * np.cumprod(1 + np.random.randn(n) * 0.005)
    return np.column_stack([
        np.arange(n),
        prices * 0.999,   # open
        prices * 1.005,   # high
        prices * 0.995,   # low
        prices,            # close
        np.random.uniform(100, 1000, n),  # volume
    ])


class TestPerformanceMetrics:

    def test_empty_trades(self):
        """No trades should return zeroed metrics."""
        m = compute_metrics([])
        assert m.num_trades == 0
        assert m.total_return == 0
        assert m.sharpe_ratio == 0
        assert len(m.equity_curve) == 1

    def test_single_winning_trade(self):
        """Single profitable trade."""
        trades = [TradeResult(
            entry_price=100, exit_price=110,
            pnl=100, pnl_pct=0.10,
            entry_time=0, exit_time=10, direction='long'
        )]
        m = compute_metrics(trades)
        assert m.num_trades == 1
        assert m.total_return == 100
        assert m.win_rate == 1.0
        assert m.best_trade == 100

    def test_single_losing_trade(self):
        """Single losing trade."""
        trades = [TradeResult(
            entry_price=100, exit_price=90,
            pnl=-100, pnl_pct=-0.10,
            entry_time=0, exit_time=10, direction='long'
        )]
        m = compute_metrics(trades)
        assert m.num_trades == 1
        assert m.total_return == -100
        assert m.win_rate == 0.0
        assert m.worst_trade == -100

    def test_mixed_trades(self):
        """Mix of wins and losses computes correct win rate and profit factor."""
        trades = [
            TradeResult(entry_price=100, exit_price=120, pnl=200, pnl_pct=0.20, entry_time=0, exit_time=10, direction='long'),
            TradeResult(entry_price=120, exit_price=110, pnl=-100, pnl_pct=-0.083, entry_time=10, exit_time=20, direction='long'),
            TradeResult(entry_price=110, exit_price=130, pnl=200, pnl_pct=0.18, entry_time=20, exit_time=30, direction='long'),
            TradeResult(entry_price=130, exit_price=125, pnl=-50, pnl_pct=-0.038, entry_time=30, exit_time=40, direction='long'),
        ]
        m = compute_metrics(trades)
        assert m.num_trades == 4
        assert m.win_rate == 0.5
        assert m.profit_factor > 1  # more profit than loss
        assert m.total_return == 250

    def test_drawdown(self):
        """Drawdown is computed from equity curve."""
        trades = [
            TradeResult(entry_price=100, exit_price=120, pnl=200, pnl_pct=0.20, entry_time=0, exit_time=10, direction='long'),
            TradeResult(entry_price=120, exit_price=100, pnl=-200, pnl_pct=-0.167, entry_time=10, exit_time=20, direction='long'),
            TradeResult(entry_price=100, exit_price=110, pnl=100, pnl_pct=0.10, entry_time=20, exit_time=30, direction='long'),
        ]
        m = compute_metrics(trades)
        assert m.max_drawdown == 200  # peak 10200 -> 10000
        assert m.max_drawdown_pct > 0

    def test_sharpe_and_sortino(self):
        """Sharpe and Sortino ratios are computed for multiple trades."""
        # Varying returns so std > 0
        pnls = [50, 30, 70, 20, 60, 40, 80, 10, 55, 45]
        pcts = [0.05, 0.03, 0.07, 0.02, 0.06, 0.04, 0.08, 0.01, 0.055, 0.045]
        trades = [
            TradeResult(entry_price=100, exit_price=100+p, pnl=p, pnl_pct=pcts[i],
                        entry_time=i*10, exit_time=(i+1)*10, direction='long')
            for i, p in enumerate(pnls)
        ]
        m = compute_metrics(trades)
        assert m.sharpe_ratio > 0  # all positive returns -> positive Sharpe
        # Sortino should be 0 with no negative returns
        assert m.sortino_ratio == 0

    def test_calmar_ratio(self):
        """Calmar ratio = annualized return / max drawdown pct."""
        trades = [
            TradeResult(entry_price=100, exit_price=120, pnl=200, pnl_pct=0.20, entry_time=0, exit_time=100, direction='long'),
            TradeResult(entry_price=120, exit_price=115, pnl=-50, pnl_pct=-0.042, entry_time=100, exit_time=200, direction='long'),
        ]
        m = compute_metrics(trades)
        assert m.calmar_ratio != 0

    def test_to_dict_keys(self):
        """to_dict returns all expected keys."""
        m = compute_metrics([])
        d = m.to_dict()
        expected_keys = {
            'total_return', 'total_return_pct', 'annualized_return',
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
            'max_drawdown', 'max_drawdown_pct', 'max_drawdown_duration',
            'num_trades', 'win_rate', 'profit_factor',
            'avg_win', 'avg_loss', 'best_trade', 'worst_trade',
            'avg_trade_duration',
        }
        assert set(d.keys()) == expected_keys

    def test_summary_string(self):
        """Summary produces non-empty formatted string."""
        trades = [TradeResult(
            entry_price=100, exit_price=110,
            pnl=100, pnl_pct=0.10,
            entry_time=0, exit_time=10, direction='long'
        )]
        m = compute_metrics(trades)
        s = m.summary()
        assert 'BACKTEST PERFORMANCE REPORT' in s
        assert 'Sharpe' in s
        assert 'Sortino' in s

    def test_avg_trade_duration(self):
        """Average trade duration computed from entry/exit times."""
        trades = [
            TradeResult(entry_price=100, exit_price=110, pnl=100, pnl_pct=0.10, entry_time=0, exit_time=5, direction='long'),
            TradeResult(entry_price=110, exit_price=120, pnl=100, pnl_pct=0.09, entry_time=10, exit_time=25, direction='long'),
        ]
        m = compute_metrics(trades)
        assert m.avg_trade_duration == 10.0  # (5 + 15) / 2


class TestBacktestEngine:

    @pytest.fixture
    def data_dir(self, tmp_path):
        """Create a temp dir with synthetic CSV data."""
        import pandas as pd
        candles = _make_candles(300)
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df.to_csv(tmp_path / 'test_btc.csv', index=False)
        df.to_csv(tmp_path / 'test_eth.csv', index=False)
        return str(tmp_path)

    def test_single_backtest(self, data_dir):
        """Single-pass backtest returns metrics."""
        engine = BacktestEngine(data_dir=data_dir)
        dna = AgentDNA()
        result = engine.run(dna, 'test_btc.csv')
        assert 'metrics' in result
        assert result['asset'] == 'test_btc'
        assert isinstance(result['metrics'], PerformanceMetrics)

    def test_backtest_with_split(self, data_dir):
        """Train/test split produces out-of-sample results."""
        engine = BacktestEngine(data_dir=data_dir)
        dna = AgentDNA()
        result = engine.run(dna, 'test_btc.csv', train_ratio=0.7)
        assert 'out-of-sample' in result['label']
        assert result['candles'] < 300  # only test portion

    def test_walk_forward(self, data_dir):
        """Walk-forward produces per-window and aggregate results."""
        engine = BacktestEngine(data_dir=data_dir)
        dna = AgentDNA()
        result = engine.walk_forward(dna, 'test_btc.csv', n_windows=3)
        assert result['mode'] == 'walk-forward'
        assert len(result['windows']) <= 3
        assert isinstance(result['aggregate'], PerformanceMetrics)

    def test_multi_asset(self, data_dir):
        """Multi-asset test runs across all available CSVs."""
        engine = BacktestEngine(data_dir=data_dir)
        dna = AgentDNA()
        result = engine.multi_asset(dna)
        assert result['mode'] == 'multi-asset'
        assert result['assets_tested'] == 2
        assert result['assets_succeeded'] == 2

    def test_compare(self, data_dir):
        """Comparative backtest ranks strategies by Sharpe."""
        engine = BacktestEngine(data_dir=data_dir)
        dna1 = AgentDNA(risk_appetite=0.2)
        dna2 = AgentDNA(risk_appetite=0.8)
        result = engine.compare([dna1, dna2], 'test_btc.csv', labels=['conservative', 'aggressive'])
        assert result['mode'] == 'comparative'
        assert len(result['results']) == 2
        assert result['results'][0]['rank'] == 1
        assert result['results'][1]['rank'] == 2
