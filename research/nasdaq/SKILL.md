---
name: nasdaq
description: Scrape Nasdaq stock data pages — news headlines, press releases, institutional holdings, insider activity, and SEC filings. Uses Chrome Beta + Xvfb + Playwright (headed mode) to handle JS-rendered content. Each section has dedicated extraction logic and can fetch full article/press-release content by following links.
version: 1.0.0
notes: |
  ## Implementation Files

  - `scrape_nasdaq.py` — Main scraper
    - `scrape_news()` — News headlines with detail extraction
    - `scrape_press_releases()` — Press releases with detail extraction
    - `scrape_institutional_holdings()` — Ownership summary + holders table
    - `scrape_insider_activity()` — Transactions + shares traded
    - `scrape_sec_filings()` — Filings table with document links
    - `scrape_all()` — All sections in one call
    - `scrape_article_detail()` — Follow a news/press-release URL for full content

  Usage:
    xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
      python3 scrape_nasdaq.py TSLA --full --output data/companies/TSLA/nasdaq.json
---

# Nasdaq Stock Data Scraper

## Overview

Nasdaq provides comprehensive stock data across 5 sections:
- **News Headlines** — Recent news articles (external sources like Zacks, MarketBeat)
- **Press Releases** — Company press releases / PR newswire
- **Institutional Holdings** — Ownership summary, top holders, active positions
- **Insider Activity** — Insider transactions, shares traded
- **SEC Filings** — Recent SEC filings with document download links

## Important Notes

- **JS-rendered content** — All data loads via JavaScript after page load. Headless browser required.
- **Chrome Beta + Xvfb** — Always use headed mode (headless=False) via Xvfb virtual display
- **Wait for content** — Each section uses specific class selectors to detect when JS has loaded
- **Rate limiting** — Add delays between page navigations to avoid detection
- **News/Press URLs** — URLs are relative paths that need `https://www.nasdaq.com` prefix

## Data Coverage by Section

| Section | URL Pattern | Data Available |
|---------|------------|----------------|
| News | `/market-activity/stocks/{TICKER}/news-headlines` | Title, source, time, link to full article |
| Press Releases | `/market-activity/stocks/{TICKER}/press-releases` | Title, date, company PR content |
| Institutional Holdings | `/market-activity/stocks/{TICKER}/institutional-holdings` | Ownership %, holder count, top holders, active positions |
| Insider Activity | `/market-activity/stocks/{TICKER}/insider-activity` | Insider trades, shares bought/sold, dates |
| SEC Filings | `/market-activity/stocks/{TICKER}/sec-filings` | Form type, dates, document download links (HTML/PDF/XBRL/XLS) |

## Installation

```bash
pip install playwright
playwright install chromium
```

---

## scrape_nasdaq.py — Main Scraper

### Functions

#### `scrape_news(ticker: str, limit: int = 20) -> Dict`
Extracts news headlines. Each item has:
- `title` — Article headline
- `source` — Publisher (e.g., Zacks, MarketBeat)
- `time_ago` — Relative time (e.g., "2 days ago")
- `url` — Full URL to article on Nasdaq

#### `scrape_press_releases(ticker: str, limit: int = 20) -> Dict`
Extracts press releases. Each item has:
- `title` — Press release headline
- `date` — Publication date
- `url` — Full URL to press release on Nasdaq

#### `scrape_institutional_holdings(ticker: str) -> Dict`
Extracts:
- `ownership_summary` — Institutional ownership %, total shares, total value
- `holders_count` — Number of institutional holders
- `top_holders[]` — Holder name, shares, value, percentage of portfolio
- `active_positions[]` — Recent position changes (new/added/reduced/removed)

#### `scrape_insider_activity(ticker: str) -> Dict`
Extracts:
- `summary` — Brief overview text
- `transactions[]` — Insider name, action, transaction type, shares, price, date
- `shares_traded[]` — Insider name, total shares traded, date

#### `scrape_sec_filings(ticker: str, page: int = 1, rows_per_page: int = 50) -> Dict`
Extracts SEC filings with:
- `company` — Company name
- `form_type` — 8-K, 10-K, 10-Q, 424B7, DEF 14A, ARS, D, etc.
- `filing_date` — Date filed
- `acceptance_date` — Date accepted
- `documents[]` — Download links for HTML, DOC, PDF, XBRL, XLS formats

#### `scrape_article_detail(page, url: str) -> Dict`
Navigates to a news/press-release URL and extracts full article content:
- `url` — The article URL
- `title` — Article title
- `content` — Full text content (first ~5000 chars)
- `published_date` — Publication date if available

#### `scrape_all(ticker: str, output_dir: str = None) -> Dict`
Runs all scrapers and combines results. Optionally saves to JSON file.

### CLI Usage

```bash
# Scrape all sections
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  python3 scrape_nasdaq.py ONDS

# Scrape specific sections
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  python3 scrape_nasdaq.py ONDS --news --press-releases

# With full article detail extraction (follows links)
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  python3 scrape_nasdaq.py ONDS --full --include-details

# Custom output
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  python3 scrape_nasdaq.py ONDS --output data/companies/ONDS/nasdaq.json
```

### Example Output Structure

```json
{
  "ticker": "ONDS",
  "fetch_date": "2026-05-02",
  "source": "nasdaq.com",
  "news": {
    "count": 10,
    "items": [
      {
        "title": "Ondas Sees Massive Backlog Jump: Growth Signal or Execution Risk?",
        "source": "Zacks",
        "time_ago": "2 days ago",
        "url": "https://www.nasdaq.com/articles/ondas-sees-massive-backlog-jump-growth-signal-or-execution-risk"
      }
    ]
  },
  "press_releases": {
    "count": 10,
    "items": [
      {
        "title": "Ondas to Report First Quarter 2026 Financial Results on May 14, 2026",
        "date": "1 day ago",
        "url": "https://www.nasdaq.com/press-release/ondas-report-first-quarter-2026-financial-results-may-14-2026-8-30-am-et"
      }
    ]
  },
  "institutional_holdings": {
    "ownership_summary": "32.96% institutional ownership, 483M shares, $1,597M value",
    "holders_count": "323 Institutional Holders",
    "top_holders": [
      {"holder": "Vanguard", "shares": "12.5M", "value": "$45.2M", "percentage": "2.6%"}
    ]
  },
  "insider_activity": {
    "transactions": [
      {"insider": "John Smith", "action": "Buy", "shares": "10,000", "price": "$2.50", "date": "04/15/2026"}
    ]
  },
  "sec_filings": {
    "count": 14,
    "filings": [
      {
        "company": "Ondas Inc",
        "form_type": "8-K",
        "filing_date": "04/29/2026",
        "documents": ["https://app.quotemedia.com/data/downloadFiling?..."]
      }
    ]
  }
}
```

---

## Limitations

1. **JS rendering required** — Cannot use simple HTTP requests or web_extract
2. **Rate limiting** — Add `time.sleep(2)` between page navigations
3. **Dynamic class names** — Nasdaq uses Jupiter22 framework classes like `jupiter22-c-article-list__item`
4. **Content may shift** — Class names may change if Nasdaq redesigns their frontend
5. **No authentication** — Public pages only, no premium data
6. **Document downloads** — SEC filing documents are on quotemedia.com, not Nasdaq directly

### CSS Selector Reference

| Section | Container Selector | Item Selector |
|---------|-------------------|---------------|
| News | `.jupiter22-c-article-list` | `.jupiter22-c-article-list__item` |
| Press Releases | `.jupiter22-c-article-list` | `.jupiter22-c-article-list__item.press-release` |
| Institutional | `.jupiter22-institutional-holdings` | `.jupiter22-institutional-holdings__institutional-holders-table tbody tr` |
| Insider | `.jupiter22-insider-activity` | `.insider-transactions-table tbody tr` |
| SEC Filings | `.jupiter22-c-sec-filings-table` | `.jupiter22-c-sec-filings-table__row` |

---

## Dependencies

```txt
playwright>=1.40.0
```

Install Playwright browsers:
```bash
playwright install chromium
```
