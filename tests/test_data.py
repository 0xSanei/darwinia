"""Tests for multi-asset support and data fetcher."""

import os
import tempfile
import numpy as np
from pathlib import Path

from darwinia.core.market import MarketEnvironment
from darwinia.data.fetcher import DataFetcher


def test_list_available():
    """list_available returns CSV filenames from data dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some dummy CSV files
        for name in ['btc_1h.csv', 'eth_1h.csv', 'readme.txt']:
            Path(tmpdir, name).touch()

        market = MarketEnvironment(tmpdir)
        available = market.list_available()
        assert available == ['btc_1h.csv', 'eth_1h.csv']
        assert 'readme.txt' not in available


def test_list_available_empty():
    """list_available returns empty list for nonexistent directory."""
    market = MarketEnvironment('/nonexistent/path/xyz')
    assert market.list_available() == []


def test_fetcher_binance_url_construction():
    """build_binance_url produces correct URL with query params."""
    fetcher = DataFetcher()
    url = fetcher.build_binance_url(symbol='ETHUSDT', interval='4h', limit=500)
    assert 'api.binance.com' in url
    assert 'symbol=ETHUSDT' in url
    assert 'interval=4h' in url
    assert 'limit=500' in url


def test_fetcher_binance_url_limit_cap():
    """Binance limit is capped at 1000."""
    fetcher = DataFetcher()
    url = fetcher.build_binance_url(limit=5000)
    assert 'limit=1000' in url


def test_save_csv_roundtrip():
    """Save and reload candles — data should survive the roundtrip."""
    fetcher = DataFetcher()

    # Create sample candles
    candles = np.array([
        [1704067200000, 42283.58, 42554.57, 42261.02, 42475.23, 1271.68108],
        [1704070800000, 42475.23, 42775.00, 42431.65, 42613.56, 1196.37856],
    ], dtype=float)

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, 'test_roundtrip.csv')
        fetcher.save_csv(candles, filepath)

        # Reload via MarketEnvironment
        market = MarketEnvironment(tmpdir)
        loaded = market.load_csv('test_roundtrip.csv')

        assert loaded.shape == candles.shape
        # Timestamps should match exactly (saved as int)
        np.testing.assert_array_equal(loaded[:, 0], candles[:, 0])
        # OHLCV should be close (rounding to 8 decimals)
        np.testing.assert_array_almost_equal(loaded[:, 1:], candles[:, 1:], decimal=5)


def test_save_csv_with_real_data():
    """Roundtrip using the actual btc_1h.csv file."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    btc_csv = data_dir / 'btc_1h.csv'
    if not btc_csv.exists():
        return  # skip if data file not present

    market = MarketEnvironment(str(data_dir))
    original = market.load_csv('btc_1h.csv')

    fetcher = DataFetcher()
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, 'btc_roundtrip.csv')
        fetcher.save_csv(original, filepath)

        market2 = MarketEnvironment(tmpdir)
        reloaded = market2.load_csv('btc_roundtrip.csv')

        assert reloaded.shape == original.shape
        np.testing.assert_array_almost_equal(reloaded, original, decimal=5)


def test_multi_asset_load():
    """load_multiple loads several CSVs and returns dict keyed by stem."""
    fetcher = DataFetcher()

    candles_a = np.array([
        [1000000, 100, 110, 90, 105, 500],
        [1003600, 105, 115, 95, 110, 600],
    ], dtype=float)
    candles_b = np.array([
        [1000000, 50, 55, 45, 52, 300],
    ], dtype=float)

    with tempfile.TemporaryDirectory() as tmpdir:
        fetcher.save_csv(candles_a, os.path.join(tmpdir, 'asset_a.csv'))
        fetcher.save_csv(candles_b, os.path.join(tmpdir, 'asset_b.csv'))

        market = MarketEnvironment(tmpdir)
        result = market.load_multiple(['asset_a.csv', 'asset_b.csv'])

        assert set(result.keys()) == {'asset_a', 'asset_b'}
        assert result['asset_a'].shape == (2, 6)
        assert result['asset_b'].shape == (1, 6)
        np.testing.assert_array_almost_equal(result['asset_a'][:, 0], [1000000, 1003600])
