---
name: defeatbeta
description: Fetch comprehensive stock data from defeatbeta-api — price history, valuation ratios (PE, PB, PS, PEG), profitability (ROE, ROA, ROIC, WACC), DCF analysis, earnings call transcripts, SEC filings, news, and quarterly financial statements. Use as alternative/supplement to yfinance for batch fundamental analysis. Data lags ~1 week — not suitable for real-time use.
version: 1.0.0
notes: |
  ## Implementation Files

  - `fetch_defeatbeta.py` — Main API fetcher
    - `fetch_price()` — Historical price DataFrame
    - `fetch_fundamentals()` — Market cap, PE, PB, PS, PEG, beta
    - `fetch_profitability()` — ROE, ROA, ROIC, ROCE, WACC
    - `fetch_growth()` — Revenue YoY growth, quarterly/annual
    - `fetch_financials()` — Quarterly/annual income, balance, cash flow
    - `fetch_transcripts()` — Earnings call transcripts
    - `fetch_news()` — News list
    - `fetch_sec_filings()` — SEC filings
    - `fetch_dcf()` — Generate DCF Excel model
    - `fetch_all()` — All data in one call

  Usage:
    python fetch_defeatbeta.py NVDA --full --output data/companies/NVDA/raw.json
---

# defeatbeta API Data Skill

## Overview

defeatbeta-api provides comprehensive stock data via DuckDB-cached data source:
- **Price history** — Daily OHLCV from 2010
- **Valuation ratios** — PE (TTM, forward), PB, PS, PEG, market cap
- **Profitability** — ROE, ROA, ROIC, ROCE, WACC
- **Growth** — Revenue YoY growth (quarterly + annual)
- **DCF model** — Generates Excel DCF with assumptions
- **Earnings transcripts** — Full call transcripts
- **SEC filings** — 10-K, 10-Q, 8-K, 144, S-8
- **News** — Market news items

## Data Source

**No authentication required.** Uses defeatbeta-api library.

**Installation:**
```bash
pip install defeatbeta-api
```

**Note:** Data is cached in DuckDB and updated periodically (~weekly). Latest update: 2026-04-24. **Not suitable for real-time data.**

---

## fetch_defeatbeta.py — API Data Fetcher

### Functions

#### `fetch_price(ticker: str) -> Dict`
Returns historical price DataFrame with columns: `report_date`, `close_price`.

#### `fetch_fundamentals(ticker: str) -> Dict`
Returns:
- `market_cap` — Latest market cap
- `ttm_pe`, `forward_pe` — P/E ratios
- `pb_ratio`, `ps_ratio` — Price-to-book, price-to-sales
- `peg_ratio` — PEG ratio
- `beta` — Stock beta
- `enterprise_value`, `ev_to_ebitda`, `ev_to_revenue`
- `dividends`, `splits`, `shares`

#### `fetch_profitability(ticker: str) -> Dict`
Returns:
- `roe` — Return on equity (quarterly)
- `roa` — Return on assets
- `roic` — Return on invested capital
- `roce` — Return on capital employed
- `wacc` — Weighted average cost of capital (22 columns)
- `debt_to_equity` — Leverage ratio

#### `fetch_growth(ticker: str) -> Dict`
Returns:
- `quarterly_revenue_yoy_growth` — Quarterly YoY growth
- `annual_revenue_growth` — Annual revenue growth

#### `fetch_financials(ticker: str) -> Dict`
Returns:
- `quarterly_income_statement`
- `quarterly_balance_sheet`
- `quarterly_cash_flow`
- `annual_income_statement`
- `annual_balance_sheet`
- `annual_cash_flow`
- `revenue_by_segment`, `revenue_by_product`, `revenue_by_geography`

#### `fetch_transcripts(ticker: str) -> Dict`
Returns earnings call transcripts:
- `transcript_count` — Total available
- `get_transcript(year, quarter)` — Fetch specific transcript
- Each transcript: full text from earnings call

#### `fetch_news(ticker: str) -> Dict`
Returns news items:
- `news_count` — Total available
- `get_news_list()` — List of news items

#### `fetch_sec_filings(ticker: str) -> Dict`
Returns SEC filings DataFrame:
- `form_type` — 10-K, 10-Q, 8-K, 144, S-8
- `filing_date`
- `accession_number`

#### `fetch_dcf(ticker: str, output_dir: str = "/tmp/defeatbeta/dcf") -> Dict`
Generates DCF Excel model:
- Output: `{output_dir}/{TICKER}.xlsx`
- Contains: assumptions, projections, valuation

#### `fetch_all(ticker: str, output_dir: str = "/tmp/defeatbeta") -> Dict`
Combines all fetchers into single output.

### CLI Usage

```bash
# Basic data
python fetch_defeatbeta.py NVDA

# Full data
python fetch_defeatbeta.py NVDA --full --output data/companies/NVDA/

# DCF only
python fetch_defeatbeta.py NVDA --dcf

# Transcripts
python fetch_defeatbeta.py NVDA --transcripts
```

### Example Output Structure

```json
{
  "ticker": "NVDA",
  "fetch_date": "2026-05-02",
  "data_source": "defeatbeta-api v0.0.52",
  "latest_data_update": "2026-04-24",
  "price": {
    "shape": [6856, 2],
    "columns": ["report_date", "close_price"],
    "date_range": ["2010-01-04", "2026-04-24"],
    "latest_close": 112.50
  },
  "fundamentals": {
    "market_cap": 5060000000000,
    "ttm_pe": 42.5,
    "forward_pe": 38.2,
    "pb_ratio": 45.2,
    "ps_ratio": 35.1,
    "peg_ratio": 2.1
  },
  "profitability": {
    "roe_latest": 0.311,
    "roa": 0.185,
    "roic": 0.289,
    "wacc": 0.238
  },
  "growth": {
    "quarterly_revenue_yoy_growth_latest": 0.7321
  },
  "sec_filings": {
    "count": 2222
  },
  "transcripts": {
    "count": 80
  },
  "news": {
    "count": 9305
  }
}
```

---

## Limitations

1. **Data lag** — Latest update is ~1 week old (2026-04-24 vs 2026-05-02). NOT suitable for real-time.
2. **Windows not supported** — Requires WSL or Linux/Docker
3. **DuckDB cache** — Data stored locally in `~/.defeatbeta/`
4. **DCF output** — Requires `openpyxl` for Excel generation
5. **quarterly_income_statement bug** — Has pandas column access bug in v0.0.52

### Recommended Use

- **DO:** Batch historical analysis, fundamental screening, DCF modeling, transcript analysis
- **DON'T:** Real-time price checks, same-day earnings reactions, live data needs

### Complementary Data Sources

| Source | Use Case | Advantage |
|--------|----------|-----------|
| yfinance | Real-time prices, analyst data | Up-to-date |
| defeatbeta | Historical fundamentals, DCF | Comprehensive |
| TradingKey | Proprietary scores, news | Real-time news |
| Motley Fool | Full earnings transcripts | Complete Q&A |
| SEC.gov | Raw SEC filings | Official source |

---

## Dependencies

```txt
defeatbeta-api>=0.0.52
openpyxl>=3.0.0  # For DCF Excel output
pandas>=1.5.0
```
