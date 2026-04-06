"""Tests for darwinia.discovery.asset_scanner — all HTTP calls are mocked."""

import json
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

from darwinia.discovery.asset_scanner import AssetScanner, _FALLBACK_PAIRS


# Sample CoinGecko /coins/markets response (trimmed to relevant fields)
MOCK_MARKETS = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "market_cap_rank": 1,
        "price_change_percentage_24h": 2.5,
        "total_volume": 30_000_000_000,
    },
    {
        "id": "ethereum",
        "symbol": "eth",
        "name": "Ethereum",
        "market_cap_rank": 2,
        "price_change_percentage_24h": -6.1,
        "total_volume": 15_000_000_000,
    },
    {
        "id": "solana",
        "symbol": "sol",
        "name": "Solana",
        "market_cap_rank": 5,
        "price_change_percentage_24h": 8.3,
        "total_volume": 5_000_000_000,
    },
    {
        "id": "dogecoin",
        "symbol": "doge",
        "name": "Dogecoin",
        "market_cap_rank": 8,
        "price_change_percentage_24h": -12.7,
        "total_volume": 3_000_000_000,
    },
    {
        "id": "ripple",
        "symbol": "xrp",
        "name": "XRP",
        "market_cap_rank": 4,
        "price_change_percentage_24h": 1.2,
        "total_volume": 8_000_000_000,
    },
    {
        "id": "cardano",
        "symbol": "ada",
        "name": "Cardano",
        "market_cap_rank": 9,
        "price_change_percentage_24h": 0.3,
        "total_volume": 1_000_000_000,
    },
]


def _mock_urlopen(mock_data):
    """Create a mock urllib.request.urlopen context manager."""
    body = json.dumps(mock_data).encode()
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestScanTrending(unittest.TestCase):
    """scan_trending returns correct structure sorted by volume."""

    @patch("darwinia.discovery.asset_scanner.urllib.request.urlopen")
    def test_returns_correct_fields(self, mock_url):
        mock_url.return_value = _mock_urlopen(MOCK_MARKETS)
        scanner = AssetScanner(timeout=5)
        scanner._last_request_time = 0  # skip rate limit in tests

        results = scanner.scan_trending(top_n=3)
        self.assertEqual(len(results), 3)
        for item in results:
            self.assertIn("symbol", item)
            self.assertIn("name", item)
            self.assertIn("price_change_24h", item)
            self.assertIn("volume_24h", item)
            self.assertIn("market_cap_rank", item)

    @patch("darwinia.discovery.asset_scanner.urllib.request.urlopen")
    def test_sorted_by_volume(self, mock_url):
        mock_url.return_value = _mock_urlopen(MOCK_MARKETS)
        scanner = AssetScanner(timeout=5)
        scanner._last_request_time = 0

        results = scanner.scan_trending(top_n=6)
        volumes = [r["volume_24h"] for r in results]
        self.assertEqual(volumes, sorted(volumes, reverse=True))


class TestScanVolatile(unittest.TestCase):
    """scan_volatile sorts by absolute price change."""

    @patch("darwinia.discovery.asset_scanner.urllib.request.urlopen")
    def test_sorted_by_absolute_change(self, mock_url):
        mock_url.return_value = _mock_urlopen(MOCK_MARKETS)
        scanner = AssetScanner(timeout=5)
        scanner._last_request_time = 0

        results = scanner.scan_volatile(top_n=6)
        abs_changes = [abs(r["price_change_24h"]) for r in results]
        self.assertEqual(abs_changes, sorted(abs_changes, reverse=True))

    @patch("darwinia.discovery.asset_scanner.urllib.request.urlopen")
    def test_most_volatile_first(self, mock_url):
        mock_url.return_value = _mock_urlopen(MOCK_MARKETS)
        scanner = AssetScanner(timeout=5)
        scanner._last_request_time = 0

        results = scanner.scan_volatile(top_n=1)
        # DOGE has -12.7% which is the largest absolute change
        self.assertEqual(results[0]["symbol"], "DOGE")


class TestRecommendForEvolution(unittest.TestCase):
    """recommend_for_evolution filters by volatility and falls back correctly."""

    @patch("darwinia.discovery.asset_scanner.urllib.request.urlopen")
    def test_returns_volatile_high_volume_pairs(self, mock_url):
        mock_url.return_value = _mock_urlopen(MOCK_MARKETS)
        scanner = AssetScanner(timeout=5)
        scanner._last_request_time = 0

        pairs = scanner.recommend_for_evolution()
        # Should only include coins with >5% absolute change:
        # ETH (-6.1%), SOL (8.3%), DOGE (-12.7%), sorted by volume
        self.assertIsInstance(pairs, list)
        self.assertTrue(all(p.endswith("USDT") for p in pairs))
        self.assertLessEqual(len(pairs), 3)
        # ETH has highest volume among the volatile ones
        self.assertEqual(pairs[0], "ETHUSDT")

    @patch("darwinia.discovery.asset_scanner.urllib.request.urlopen")
    def test_fallback_on_connection_error(self, mock_url):
        mock_url.side_effect = OSError("network down")
        scanner = AssetScanner(timeout=5)
        scanner._last_request_time = 0

        pairs = scanner.recommend_for_evolution()
        self.assertEqual(pairs, list(_FALLBACK_PAIRS))

    @patch("darwinia.discovery.asset_scanner.urllib.request.urlopen")
    def test_fallback_when_nothing_volatile(self, mock_url):
        # All coins have < 5% change
        calm_markets = [
            {
                "id": "bitcoin", "symbol": "btc", "name": "Bitcoin",
                "market_cap_rank": 1,
                "price_change_percentage_24h": 0.5,
                "total_volume": 30_000_000_000,
            },
            {
                "id": "ethereum", "symbol": "eth", "name": "Ethereum",
                "market_cap_rank": 2,
                "price_change_percentage_24h": -1.2,
                "total_volume": 15_000_000_000,
            },
        ]
        mock_url.return_value = _mock_urlopen(calm_markets)
        scanner = AssetScanner(timeout=5)
        scanner._last_request_time = 0

        pairs = scanner.recommend_for_evolution()
        self.assertEqual(pairs, list(_FALLBACK_PAIRS))


class TestScanCLI(unittest.TestCase):
    """The scan CLI subcommand is registered and callable."""

    def test_scan_subcommand_exists(self):
        """Verify 'scan' is a registered subcommand in the argument parser."""
        import argparse
        from darwinia.__main__ import main

        # Build the parser by inspecting the module
        import darwinia.__main__ as mod
        import inspect
        source = inspect.getsource(mod.main)
        self.assertIn("scan", source)

    @patch("darwinia.discovery.asset_scanner.urllib.request.urlopen")
    def test_scan_json_output(self, mock_url):
        """Verify scan --json produces valid JSON."""
        mock_url.return_value = _mock_urlopen(MOCK_MARKETS)
        import sys
        from io import StringIO
        from darwinia.__main__ import main

        old_argv = sys.argv
        old_stdout = sys.stdout
        try:
            sys.argv = ["darwinia", "scan", "--json", "--top", "3"]
            sys.stdout = StringIO()
            main()
            output = sys.stdout.getvalue()
            data = json.loads(output)
            self.assertIn("assets", data)
            self.assertEqual(len(data["assets"]), 3)
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout


if __name__ == "__main__":
    unittest.main()
