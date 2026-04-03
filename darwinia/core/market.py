"""
Market data loader and environment wrapper.
Provides normalized OHLCV data to agents and manages data splitting.
"""

import numpy as np
import pandas as pd
from pathlib import Path


class MarketEnvironment:
    """Loads and serves market data for agent evaluation."""

    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.candles = None  # numpy array [timestamp, O, H, L, C, V]

    def load_csv(self, filename: str) -> np.ndarray:
        """Load OHLCV data from CSV."""
        path = self.data_dir / filename
        df = pd.read_csv(path)

        # Normalize column names
        col_map = {}
        for col in df.columns:
            lower = col.lower().strip()
            if 'time' in lower or 'date' in lower:
                col_map[col] = 'timestamp'
            elif lower in ('open', 'o'):
                col_map[col] = 'open'
            elif lower in ('high', 'h'):
                col_map[col] = 'high'
            elif lower in ('low', 'l'):
                col_map[col] = 'low'
            elif lower in ('close', 'c'):
                col_map[col] = 'close'
            elif lower in ('volume', 'vol', 'v'):
                col_map[col] = 'volume'

        df = df.rename(columns=col_map)
        required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")

        self.candles = df[required].values.astype(float)
        return self.candles

    def get_train_test_split(self, train_ratio: float = 0.8) -> tuple:
        """Split data into training and test sets."""
        split_idx = int(len(self.candles) * train_ratio)
        return self.candles[:split_idx], self.candles[split_idx:]
