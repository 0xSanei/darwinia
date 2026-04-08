"""
Performance metrics for backtesting.

Computes standard quantitative finance metrics from trade results
and equity curve data.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from ..core.types import TradeResult


@dataclass
class PerformanceMetrics:
    """Complete performance report for a backtest run."""
    # Returns
    total_return: float = 0.0
    total_return_pct: float = 0.0
    annualized_return: float = 0.0

    # Risk-adjusted
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Drawdown
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown_duration: int = 0  # candles

    # Trade stats
    num_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_trade_duration: float = 0.0

    # Equity curve
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Serialize to dict (exclude curves for compact output)."""
        return {
            'total_return': round(self.total_return, 2),
            'total_return_pct': round(self.total_return_pct, 4),
            'annualized_return': round(self.annualized_return, 4),
            'sharpe_ratio': round(self.sharpe_ratio, 4),
            'sortino_ratio': round(self.sortino_ratio, 4),
            'calmar_ratio': round(self.calmar_ratio, 4),
            'max_drawdown': round(self.max_drawdown, 2),
            'max_drawdown_pct': round(self.max_drawdown_pct, 4),
            'max_drawdown_duration': self.max_drawdown_duration,
            'num_trades': self.num_trades,
            'win_rate': round(self.win_rate, 4),
            'profit_factor': round(self.profit_factor, 4),
            'avg_win': round(self.avg_win, 2),
            'avg_loss': round(self.avg_loss, 2),
            'best_trade': round(self.best_trade, 2),
            'worst_trade': round(self.worst_trade, 2),
            'avg_trade_duration': round(self.avg_trade_duration, 1),
        }

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"{'─' * 48}",
            f"  BACKTEST PERFORMANCE REPORT",
            f"{'─' * 48}",
            f"  Total Return:      ${self.total_return:>10.2f} ({self.total_return_pct:>+.2%})",
            f"  Annualized Return: {self.annualized_return:>+.2%}",
            f"{'─' * 48}",
            f"  Sharpe Ratio:      {self.sharpe_ratio:>10.4f}",
            f"  Sortino Ratio:     {self.sortino_ratio:>10.4f}",
            f"  Calmar Ratio:      {self.calmar_ratio:>10.4f}",
            f"{'─' * 48}",
            f"  Max Drawdown:      ${self.max_drawdown:>10.2f} ({self.max_drawdown_pct:>-.2%})",
            f"  DD Duration:       {self.max_drawdown_duration:>10d} candles",
            f"{'─' * 48}",
            f"  Trades:            {self.num_trades:>10d}",
            f"  Win Rate:          {self.win_rate:>10.2%}",
            f"  Profit Factor:     {self.profit_factor:>10.4f}",
            f"  Avg Win:           ${self.avg_win:>10.2f}",
            f"  Avg Loss:          ${self.avg_loss:>10.2f}",
            f"  Best Trade:        ${self.best_trade:>10.2f}",
            f"  Worst Trade:       ${self.worst_trade:>10.2f}",
            f"{'─' * 48}",
        ]
        return '\n'.join(lines)


def compute_metrics(
    trades: List[TradeResult],
    initial_capital: float = 10000.0,
    candles_per_year: float = 365 * 24,  # hourly candles default
    risk_free_rate: float = 0.04,
) -> PerformanceMetrics:
    """
    Compute full performance metrics from a list of trades.

    Args:
        trades: Completed trade results from agent run
        initial_capital: Starting capital
        candles_per_year: For annualization (365*24 for hourly, 365 for daily)
        risk_free_rate: Annual risk-free rate for Sharpe/Sortino
    """
    m = PerformanceMetrics()

    if not trades:
        m.equity_curve = [initial_capital]
        return m

    m.num_trades = len(trades)

    # Build equity curve from trade sequence
    equity = [initial_capital]
    for t in trades:
        equity.append(equity[-1] + t.pnl)
    m.equity_curve = equity

    # Returns
    m.total_return = equity[-1] - initial_capital
    m.total_return_pct = m.total_return / initial_capital

    # Annualized return
    total_candles = trades[-1].exit_time - trades[0].entry_time if len(trades) > 1 else 1
    years = max(total_candles / candles_per_year, 1e-6)
    if equity[-1] > 0 and initial_capital > 0:
        m.annualized_return = (equity[-1] / initial_capital) ** (1 / years) - 1
    else:
        m.annualized_return = -1.0

    # Per-trade PnL for ratio calculations
    pnls = np.array([t.pnl for t in trades])
    pnl_pcts = np.array([t.pnl_pct for t in trades])

    # Win/loss stats
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    m.win_rate = len(wins) / m.num_trades if m.num_trades > 0 else 0
    m.avg_win = float(wins.mean()) if len(wins) > 0 else 0
    m.avg_loss = float(losses.mean()) if len(losses) > 0 else 0
    m.best_trade = float(pnls.max()) if len(pnls) > 0 else 0
    m.worst_trade = float(pnls.min()) if len(pnls) > 0 else 0

    # Profit factor
    gross_profit = float(wins.sum()) if len(wins) > 0 else 0
    gross_loss = abs(float(losses.sum())) if len(losses) > 0 else 0
    m.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0

    # Drawdown analysis
    equity_arr = np.array(equity)
    running_max = np.maximum.accumulate(equity_arr)
    drawdowns = equity_arr - running_max
    m.max_drawdown = float(abs(drawdowns.min()))
    peak_at_max_dd = running_max[np.argmin(drawdowns)]
    m.max_drawdown_pct = m.max_drawdown / peak_at_max_dd if peak_at_max_dd > 0 else 0
    m.drawdown_curve = drawdowns.tolist()

    # Max drawdown duration (longest streak below peak)
    below_peak = equity_arr < running_max
    max_dur = 0
    cur_dur = 0
    for bp in below_peak:
        if bp:
            cur_dur += 1
            max_dur = max(max_dur, cur_dur)
        else:
            cur_dur = 0
    m.max_drawdown_duration = max_dur

    # Sharpe ratio (annualized)
    if len(pnl_pcts) > 1:
        excess_returns = pnl_pcts - (risk_free_rate / candles_per_year)
        std = np.std(pnl_pcts, ddof=1)
        if std > 0:
            m.sharpe_ratio = float(np.mean(excess_returns) / std * math.sqrt(min(m.num_trades, candles_per_year)))

    # Sortino ratio (penalizes only downside volatility)
    if len(pnl_pcts) > 1:
        downside = pnl_pcts[pnl_pcts < 0]
        if len(downside) > 0:
            downside_std = np.std(downside, ddof=1)
            if downside_std > 0:
                excess_mean = np.mean(pnl_pcts) - (risk_free_rate / candles_per_year)
                m.sortino_ratio = float(excess_mean / downside_std * math.sqrt(min(m.num_trades, candles_per_year)))

    # Calmar ratio (annualized return / max drawdown)
    if m.max_drawdown_pct > 0:
        m.calmar_ratio = m.annualized_return / m.max_drawdown_pct

    # Average trade duration
    durations = [t.exit_time - t.entry_time for t in trades]
    m.avg_trade_duration = float(np.mean(durations)) if durations else 0

    return m
