"""
Auto-discovery of trending and volatile crypto assets for evolution training.
Uses CoinGecko public API (no API key required).
"""

import json
import urllib.request
import urllib.error
import urllib.parse
import time
from typing import List, Dict, Any

# CoinGecko public API base
_COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Default fallback pairs when API is unreachable
_FALLBACK_PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


class AssetScanner:
    """Scans public market data to find trending and volatile crypto assets."""

    def __init__(self, timeout: int = 15):
        """Initialize the scanner.

        Args:
            timeout: HTTP request timeout in seconds.
        """
        self.timeout = timeout
        self._last_request_time = 0.0
        self._min_interval = 1.5  # seconds between requests (CoinGecko rate limit)

    def _rate_limit(self) -> None:
        """Enforce minimum interval between API calls."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _fetch_markets(self, per_page: int = 50) -> List[Dict[str, Any]]:
        """Fetch top coins by market cap from CoinGecko /coins/markets.

        Args:
            per_page: Number of coins to fetch (max 250).

        Returns:
            List of coin market data dicts from CoinGecko.

        Raises:
            ConnectionError: If the API request fails.
        """
        self._rate_limit()
        params = urllib.parse.urlencode({
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": str(min(per_page, 250)),
            "page": "1",
            "sparkline": "false",
            "price_change_percentage": "24h",
        })
        url = f"{_COINGECKO_BASE}/coins/markets?{params}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "darwinia/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            raise ConnectionError(f"CoinGecko API request failed: {e}")

    def scan_trending(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Return trending crypto assets sorted by 24h volume.

        Args:
            top_n: Number of assets to return.

        Returns:
            List of dicts with keys: symbol, name, price_change_24h,
            volume_24h, market_cap_rank.
        """
        raw = self._fetch_markets(per_page=max(top_n * 2, 50))

        # Sort by volume descending
        raw.sort(key=lambda c: c.get("total_volume", 0) or 0, reverse=True)

        results = []
        for coin in raw[:top_n]:
            results.append({
                "symbol": (coin.get("symbol") or "").upper(),
                "name": coin.get("name", ""),
                "price_change_24h": coin.get("price_change_percentage_24h") or 0.0,
                "volume_24h": coin.get("total_volume") or 0,
                "market_cap_rank": coin.get("market_cap_rank") or 0,
            })
        return results

    def scan_volatile(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Return the most volatile assets sorted by absolute 24h price change.

        Volatile assets provide richer training signal for genetic evolution.

        Args:
            top_n: Number of assets to return.

        Returns:
            List of dicts with keys: symbol, name, price_change_24h,
            volume_24h, market_cap_rank.
        """
        raw = self._fetch_markets(per_page=max(top_n * 2, 50))

        # Sort by absolute price change descending
        raw.sort(
            key=lambda c: abs(c.get("price_change_percentage_24h") or 0.0),
            reverse=True,
        )

        results = []
        for coin in raw[:top_n]:
            results.append({
                "symbol": (coin.get("symbol") or "").upper(),
                "name": coin.get("name", ""),
                "price_change_24h": coin.get("price_change_percentage_24h") or 0.0,
                "volume_24h": coin.get("total_volume") or 0,
                "market_cap_rank": coin.get("market_cap_rank") or 0,
            })
        return results

    def recommend_for_evolution(self) -> List[str]:
        """Return recommended trading pairs for evolution training.

        Logic: pick top 3 coins by volume that have >5% absolute 24h change.
        Volatile, high-volume assets produce the best training data.
        Falls back to BTC, ETH, SOL if the API is unreachable.

        Returns:
            List of trading pair strings (e.g. ["BTCUSDT", "ETHUSDT"]).
        """
        try:
            raw = self._fetch_markets(per_page=50)
        except ConnectionError:
            return list(_FALLBACK_PAIRS)

        # Filter: absolute 24h change > 5%
        volatile = [
            c for c in raw
            if abs(c.get("price_change_percentage_24h") or 0.0) > 5.0
        ]

        if not volatile:
            return list(_FALLBACK_PAIRS)

        # Sort by volume descending, take top 3
        volatile.sort(key=lambda c: c.get("total_volume", 0) or 0, reverse=True)

        pairs = []
        for coin in volatile[:3]:
            symbol = (coin.get("symbol") or "").upper()
            pairs.append(f"{symbol}USDT")

        return pairs if pairs else list(_FALLBACK_PAIRS)
