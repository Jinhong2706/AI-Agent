---
name: finance
description: Use this skill when the user asks about stock prices, options, dividends, splits, ticker details, cryptocurrency prices, market caps, or any financial market data. Triggers include mentions of 'stock price', 'ticker', 'market data', 'options chain', 'dividends', 'crypto price', 'bitcoin price', or any request for financial market information.
---

# Financial Market Data

## Overview

Python libraries for querying financial market data are pre-installed with API keys already configured in the environment. Use them via the bash tool.

- **Polygon.io** — US equities, options, dividends, splits, ticker metadata
- **CoinGecko** — Cryptocurrency prices, market caps, historical data

---

## Polygon.io (Stocks & Options)

### Setup

```python
from polygon import RESTClient
import pandas as pd

client = RESTClient()  # API key is pre-configured via environment
```

### Aggregate Bars (OHLCV)

```python
# get_aggs returns a list directly
bars = client.get_aggs(
    ticker="AAPL",
    multiplier=1,
    timespan="day",       # "minute", "hour", "day", "week", "month"
    from_="2024-01-01",
    to="2024-12-31",
    adjusted=True,
    sort="asc",
    limit=50000,
)

# Convert to DataFrame
df = pd.DataFrame(bars)
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
print(df[["timestamp", "open", "high", "low", "close", "volume"]].head())

# list_aggs is the paginated iterator version (preferred for large date ranges)
for agg in client.list_aggs("AAPL", 1, "day", "2024-01-01", "2024-12-31", limit=50000):
    print(f"{agg.timestamp}: O={agg.open} H={agg.high} L={agg.low} C={agg.close} V={agg.volume}")
```

### Ticker Details

```python
details = client.get_ticker_details("AAPL")
print(f"Name: {details.name}")
print(f"Ticker: {details.ticker}")
print(f"Market Cap: {details.market_cap}")
print(f"Description: {details.description}")
print(f"SIC Description: {details.sic_description}")

# Historical snapshot
details = client.get_ticker_details("AAPL", date="2024-01-01")
```

### Last Quote (NBBO)

```python
quote = client.get_last_quote(ticker="AAPL")
print(f"Bid: {quote.bid_price} x {quote.bid_size}")
print(f"Ask: {quote.ask_price} x {quote.ask_size}")
```

### Options Contracts

```python
# list_options_contracts returns a paginated iterator
contracts = list(client.list_options_contracts(
    underlying_ticker="AAPL",
    contract_type="call",           # "call", "put"
    expiration_date="2024-12-20",   # exact date, or use _gte/_lte
    expired=False,
    order="asc",
    sort="ticker",
    limit=100,
))

for c in contracts[:5]:
    print(f"{c.ticker}: strike={c.strike_price}, exp={c.expiration_date}, type={c.contract_type}")
```

### Stock Splits

```python
for s in client.list_splits(ticker="NVDA"):
    print(f"{s.ticker} split on {s.execution_date}: {s.split_from}:{s.split_to}")
```

### Dividends

```python
for d in client.list_dividends(ticker="MSFT"):
    print(f"{d.ticker} ex-date={d.ex_dividend_date}: ${d.cash_amount}")
```

### Polygon Quick Reference

| Task | Method | Key Parameters |
|------|--------|---------------|
| Daily/intraday bars | `get_aggs` / `list_aggs` | `ticker`, `multiplier`, `timespan`, `from_`, `to` |
| Ticker metadata | `get_ticker_details` | `ticker`, `date` (optional) |
| Last NBBO quote | `get_last_quote` | `ticker` |
| Options chain | `list_options_contracts` | `underlying_ticker`, `contract_type`, `expiration_date` |
| Stock splits | `list_splits` | `ticker` |
| Dividends | `list_dividends` | `ticker` |

---

## CoinGecko (Cryptocurrency)

### Setup

```python
import requests
import os

BASE_URL = os.environ.get("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
```

### Current Prices

```python
# Simple price lookup for one or more coins
r = requests.get(f"{BASE_URL}/simple/price", params={
    "ids": "bitcoin,ethereum",
    "vs_currencies": "usd,eur",
    "include_market_cap": "true",
    "include_24hr_vol": "true",
    "include_24hr_change": "true",
    "include_last_updated_at": "true",
})
data = r.json()
print(f"BTC: ${data['bitcoin']['usd']}")
print(f"ETH: ${data['ethereum']['usd']}")
```

### Market Data (Top Coins)

```python
r = requests.get(f"{BASE_URL}/coins/markets", params={
    "vs_currency": "usd",
    "ids": "bitcoin,ethereum,solana",
    "order": "market_cap_desc",
    "per_page": 10,
    "page": 1,
    "sparkline": "false",
})
for coin in r.json():
    print(f"{coin['name']} ({coin['symbol'].upper()}): "
          f"${coin['current_price']:,.2f}, "
          f"mcap=${coin['market_cap']:,.0f}, "
          f"24h_change={coin['price_change_percentage_24h']:.2f}%")
```

### Historical Price Chart

```python
import pandas as pd

r = requests.get(f"{BASE_URL}/coins/bitcoin/market_chart", params={
    "vs_currency": "usd",
    "days": "30",
    "interval": "daily",
})
data = r.json()
prices = data["prices"]           # [[timestamp_ms, price], ...]
market_caps = data["market_caps"]  # [[timestamp_ms, mcap], ...]
volumes = data["total_volumes"]    # [[timestamp_ms, vol], ...]

df = pd.DataFrame(prices, columns=["timestamp", "price"])
df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
print(df[["date", "price"]].tail())
```

### Coin Details

```python
r = requests.get(f"{BASE_URL}/coins/bitcoin", params={
    "localization": "false",
    "tickers": "false",
    "community_data": "false",
    "developer_data": "false",
})
coin = r.json()
print(f"Name: {coin['name']}")
print(f"Symbol: {coin['symbol']}")
print(f"Current price: ${coin['market_data']['current_price']['usd']:,.2f}")
print(f"ATH: ${coin['market_data']['ath']['usd']:,.2f}")
```

### List All Coins

```python
r = requests.get(f"{BASE_URL}/coins/list")
coins = r.json()  # [{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}, ...]
```

### CoinGecko Quick Reference

| Task | Endpoint | Key Parameters |
|------|----------|---------------|
| Current prices | `/simple/price` | `ids`, `vs_currencies`, `include_market_cap` |
| Market data | `/coins/markets` | `vs_currency`, `ids`, `order`, `per_page` |
| Historical chart | `/coins/{id}/market_chart` | `vs_currency`, `days`, `interval` |
| Coin details | `/coins/{id}` | `localization`, `tickers` |
| All coin IDs | `/coins/list` | none |

---

## Important Notes

- No general internet access is available; only the Polygon and CoinGecko API proxies are accessible.
- API keys are pre-configured; do not set them manually.
- The Polygon `list_*` methods return paginated iterators; wrap in `list()` to get all results.
- For CoinGecko, all endpoints use `GET` requests; no authentication is required.
- For time-sensitive queries, data may be gated to a specific date via the `TIME_GATE` environment variable.