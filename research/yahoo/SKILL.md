---
name: yahoo
description: Fetch Yahoo Finance data via yfinance API and web scraping — company info, analyst consensus, price targets, upgrades/downgrades, technical indicators, news, SEC filings, and earnings calls. Use for comprehensive US stock fundamental and technical analysis. Complements TradingKey for price/fundamentals data.
version: 1.0.0
notes: |
  ## Implementation Files
  
  - `fetch_yahoo.py` — yfinance API fetcher
    - `fetch_basic_info()` — Company info, price, valuation, profitability, financials, dividend
    - `fetch_analyst_consensus()` — Recommendations, price targets, upgrades/downgrades
    - `fetch_technical_indicators()` — SMA, EMA, RSI, MACD, Bollinger Bands (requires `ta` library)
    - `fetch_all()` — Fetch all data in one call
  
  - `scrap_yahoo_web.py` — Playwright web scraper for data not available via API
    - Top analysts with scores
    - Full upgrade/downgrade history with pagination
    - Earnings call transcripts
    - SEC filings (10-K, 10-Q, 8-K)
    - Company news
  
  Usage:
    python fetch_yahoo.py TSLA --full --output data/companies/TSLA/raw.json
    python scrap_yahoo_web.py TSLA
---

# Yahoo Finance Data Skill

## Overview

Yahoo Finance provides comprehensive stock data including:
- **Price data** — Current price, historical prices, 52-week range
- **Fundamentals** — P/E, market cap, revenue, earnings
- **Analyst data** — Consensus ratings, price targets, upgrades/downgrades
- **Technical indicators** — SMA, EMA, RSI, MACD (via `ta` library)
- **SEC filings** — 10-K, 10-Q, 8-K filings
- **Earnings calls** — Latest earnings call transcripts

## Data Sources

### 1. yfinance API (Primary)

**No authentication required.** Uses the unofficial Yahoo Finance API.

**Installation:**
```bash
pip install yfinance ta
```

### 2. Web Scraping (Secondary)

For data not available via API (analyst scores, earnings calls, SEC filings):
- Uses Playwright with Chromium
- Handles pagination for full history
- Requires: `pip install playwright && playwright install chromium`

---

## fetch_yahoo.py — API Data Fetcher

### Functions

#### `fetch_basic_info(ticker: str) -> Dict`
Returns:
- `company_name`, `sector`, `industry`, `description`, `employees`
- `price` — current, previous_close, 52-week range, moving averages
- `valuation` — market_cap, PE ratios, PEG, price-to-book, EV ratios
- `profitability` — margins, ROE, ROA, EPS
- `financials` — cash, debt, ratios, growth rates, FCF
- `dividend` — rate, yield, payout ratio

#### `fetch_analyst_consensus(ticker: str) -> Dict`
Returns:
- `recommendations[]` — Analyst recommendation history (strongBuy, buy, hold, sell, strongSell)
- `latest_recommendation` — Most recent consensus
- `bull_bear_ratio` — Bull/bear percentage breakdown
- `price_targets` — Low, mean, median, high target prices
- `upgrades_downgrades[]` — Full upgrade/downgrade history with firm, action, grades
- `upgrade_downgrade_trend` — Trend analysis (bullish/bearish/neutral)

#### `fetch_technical_indicators(ticker: str, period: str = "1y") -> Dict`
Returns:
- `sma_20`, `sma_50`, `sma_200` — Simple Moving Averages
- `ema_12`, `ema_26` — Exponential Moving Averages
- `rsi_14` — Relative Strength Index
- `macd` — MACD line, signal line, histogram
- `bollinger` — Upper, middle, lower bands
- `volume` — Current, 20d avg, 50d avg
- `price_position` — Current price vs SMAs

#### `fetch_all(ticker: str, include_technical: bool = False) -> Dict`
Combines all fetchers into single output.

### CLI Usage

```bash
# Basic info + analyst consensus
python fetch_yahoo.py TSLA

# Include technical indicators
python fetch_yahoo.py TSLA --full

# Custom output path
python fetch_yahoo.py TSLA --output data/companies/TSLA/raw.json
```

### Example Output Structure

```json
{
  "ticker": "TSLA",
  "fetch_date": "2026-04-29T12:00:00",
  "data_source": "yfinance",
  "basic": {
    "ticker": "TSLA",
    "company_name": "Tesla, Inc.",
    "sector": "Consumer Cyclical",
    "industry": "Auto Manufacturers",
    "price": {
      "current": 250.50,
      "52week_low": 138.80,
      "52week_high": 299.29
    },
    "valuation": {
      "market_cap": 800000000000,
      "trailing_pe": 45.2,
      "forward_pe": 38.5
    }
  },
  "analyst": {
    "latest_recommendation": {
      "strongBuy": 10,
      "buy": 15,
      "hold": 8,
      "sell": 2,
      "strongSell": 0
    },
    "price_targets": {
      "low": 150,
      "mean": 265,
      "high": 350
    }
  }
}
```

---

## scrap_yahoo_web.py — Web Scraper

### Functions

#### `scrape_analyst_data(page, ticker: str) -> Dict`
Scrapes from `/analyst-insights/` page:
- `top_analysts[]` — Firm, overall/direction/price scores, rating, target, date
- `upgrades_downgrades[]` — Full history with pagination (up to 10 pages)
- `price_targets` — Low, mean, high from page text

#### `scrape_news(page, ticker: str, limit: int = 10) -> Dict`
Scrapes from `/news/` page:
- `news[]` — Title, link for recent news items

#### `scrape_earnings_calls(page, ticker: str) -> Dict`
Scrapes from `/earnings-calls/` page:
- `earnings_calls[]` — Latest call with quarter, fiscal year, URL
- `transcript` — Full transcript text (up to 50,000 chars)
- `estimates` — EPS and revenue estimates extracted from transcript

#### `scrape_sec_filings(page, ticker: str) -> Dict`
Scrapes from `/sec-filing/` page:
- `filings[]` — Recent 10-K, 10-Q, 8-K, ARS, S-8 filings (past 3 months)
- Each filing: form_type, description, date, URL

#### `scrape_all(ticker: str, ...) -> Dict`
Combines all scrapers into single output.

### CLI Usage

```bash
# Full scrape
python scrap_yahoo_web.py TSLA

# Skip certain sections
python scrap_yahoo_web.py TSLA --no-news --no-earnings --no-sec
```

### Example Output Structure

```json
{
  "ticker": "TSLA",
  "fetch_date": "2026-04-29T12:00:00",
  "source": "yahoo_finance_web",
  "analyst": {
    "top_analysts": [
      {
        "firm": "Morgan Stanley",
        "overall_score": "4.5",
        "direction_score": "4.8",
        "price_score": "4.2",
        "rating": "Overweight",
        "price_target": "$280"
      }
    ],
    "upgrades_downgrades": [
      {
        "action": "Upgraded",
        "change": "Equal-Weight → Overweight",
        "date": "Apr 15, 2026"
      }
    ]
  },
  "earnings_calls": [
    {
      "quarter": "Q1",
      "fiscal_year": "2026",
      "period": "Q1 FY2026",
      "url": "https://finance.yahoo.com/quote/TSLA/earnings/...",
      "transcript": "Operator: Good afternoon. Welcome to Tesla's First Quarter 2026..."
    }
  ],
  "sec_filings": [
    {
      "form_type": "10-Q",
      "description": "Quarterly Report",
      "date": "April 25, 2026",
      "url": "https://finance.yahoo.com/sec-filing/TSLA/..."
    }
  ]
}
```

---

## Recommended Workflow

For comprehensive stock analysis, combine multiple data sources:

1. **fetch_yahoo.py** — Price, fundamentals, analyst consensus, technicals
2. **scrap_yahoo_web.py** — Analyst scores, earnings calls, SEC filings
3. **TradingKey** — Proprietary scoring, multi-dimensional analysis, news

### Example Integration

```python
# Step 1: Get fundamental data from yfinance
from fetch_yahoo import fetch_all
data = fetch_all("TSLA", include_technical=True)

# Step 2: Get analyst scores and earnings calls from web
# (Run separately due to async)
# python scrap_yahoo_web.py TSLA

# Step 3: Get TradingKey analysis
from tradingkey_fetcher import TradingKeyFetcher
tk = TradingKeyFetcher("TSLA")
tk_data = tk.fetch_all()
```

---

## Limitations

1. **yfinance API** — Unofficial API, may break if Yahoo changes their backend
2. **Rate limiting** — Heavy usage may trigger rate limits
3. **Web scraper** — Requires Playwright + Chromium installation
4. **No real-time data** — 15-minute delayed prices
5. **Earnings transcripts** — May not be available for all stocks
6. **SEC filings** — Only recent filings (past 3 months)

---

## Dependencies

```txt
yfinance>=0.2.0
ta>=0.10.0  # For technical indicators
playwright>=1.40.0  # For web scraping
```

Install Playwright browsers:
```bash
playwright install chromium
```
