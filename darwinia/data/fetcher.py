"""
Fetch OHLCV data from public APIs (no API key needed).
Uses only stdlib (urllib) — no external HTTP dependencies.
"""

import json
import csv
import time
import urllib.request
import urllib.error
import urllib.parse
import numpy as np
from pathlib import Path


class DataFetcher:
    """Fetch OHLCV data from public APIs."""

    SOURCES = {
        'binance': 'https://api.binance.com/api/v3/klines',
        'coingecko': 'https://api.coingecko.com/api/v3/coins/{}/ohlc',
    }

    def fetch_binance(self, symbol='BTCUSDT', interval='1h', limit=1000) -> np.ndarray:
        """Fetch from Binance public API. Returns OHLCV numpy array.

        Columns: [timestamp, open, high, low, close, volume]
        """
        params = urllib.parse.urlencode({
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': min(limit, 1000),
        })
        url = f"{self.SOURCES['binance']}?{params}"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'darwinia/1.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            raise ConnectionError(f"Binance API request failed: {e}")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ConnectionError(f"Failed to parse Binance response: {e}")

        if not data:
            raise ValueError("Binance returned empty data")

        # Binance kline format: [open_time, open, high, low, close, volume, ...]
        rows = []
        for kline in data:
            if not isinstance(kline, (list, tuple)) or len(kline) < 6:
                continue  # skip malformed candles
            try:
                rows.append([
                    float(kline[0]),   # timestamp
                    float(kline[1]),   # open
                    float(kline[2]),   # high
                    float(kline[3]),   # low
                    float(kline[4]),   # close
                    float(kline[5]),   # volume
                ])
            except (ValueError, TypeError):
                continue  # skip candles with non-numeric values
        return np.array(rows, dtype=float)

    def fetch_coingecko(self, coin_id='bitcoin', days=30) -> np.ndarray:
        """Fetch from CoinGecko (no API key). Returns OHLCV numpy array.

        Note: CoinGecko OHLC endpoint returns [timestamp, open, high, low, close].
        Volume is set to 0 since this endpoint doesn't provide it.
        """
        url = self.SOURCES['coingecko'].format(coin_id)
        params = urllib.parse.urlencode({
            'vs_currency': 'usd',
            'days': str(days),
        })
        full_url = f"{url}?{params}"

        try:
            req = urllib.request.Request(full_url, headers={'User-Agent': 'darwinia/1.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            raise ConnectionError(f"CoinGecko API request failed: {e}")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ConnectionError(f"Failed to parse CoinGecko response: {e}")

        if not data:
            raise ValueError("CoinGecko returned empty data")

        # CoinGecko OHLC format: [timestamp, open, high, low, close]
        rows = []
        for candle in data:
            if not isinstance(candle, (list, tuple)) or len(candle) < 5:
                continue
            try:
                rows.append([
                    float(candle[0]),  # timestamp
                    float(candle[1]),  # open
                    float(candle[2]),  # high
                    float(candle[3]),  # low
                    float(candle[4]),  # close
                    0.0,               # volume (not provided)
                ])
            except (ValueError, TypeError):
                continue
        return np.array(rows, dtype=float)

    def save_csv(self, candles: np.ndarray, filepath: str):
        """Save fetched data as CSV compatible with MarketEnvironment."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            for row in candles:
                writer.writerow([
                    int(row[0]),
                    round(row[1], 8),
                    round(row[2], 8),
                    round(row[3], 8),
                    round(row[4], 8),
                    round(row[5], 8),
                ])

    def build_binance_url(self, symbol='BTCUSDT', interval='1h', limit=1000) -> str:
        """Build the Binance API URL (useful for testing)."""
        params = urllib.parse.urlencode({
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': min(limit, 1000),
        })
        return f"{self.SOURCES['binance']}?{params}"
