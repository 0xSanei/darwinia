# Market Data

## BTC 1-Hour Candles

- **File**: `btc_1h.csv`
- **Source**: Binance public API (BTC/USDT)
- **Period**: 2024-01-01 to 2025-04-01
- **Candles**: ~10,946
- **Interval**: 1 hour

## Format

```
timestamp,open,high,low,close,volume
```

- `timestamp`: Unix timestamp in milliseconds
- `open/high/low/close`: Price in USDT
- `volume`: Trading volume in BTC
