# Nasdaq Stock Data Scraper

## Trigger
When user asks to fetch data from Nasdaq for a stock ticker — news, press releases, institutional holdings, insider activity, or SEC filings.

## Data Sources (5 sections)

| Section | Method | API/URL |
|---------|--------|---------|
| News Headlines | REST API | `https://www.nasdaq.com/api/news/topic/articlebysymbol?q={TICKER}\|STOCKS&offset=0&limit=50` |
| Press Releases | REST API | `https://www.nasdaq.com/api/news/topic/press_release?q=symbol:{ticker}\|assetclass:stocks&limit=50&offset=0` |
| Institutional Holdings | Playwright + shadow DOM | `https://www.nasdaq.com/market-activity/stocks/{TICKER}/institutional-holdings` |
| Insider Activity | Playwright + shadow DOM | `https://www.nasdaq.com/market-activity/stocks/{TICKER}/insider-activity` |
| SEC Filings | REST API | `https://api.nasdaq.com/api/company/{TICKER}/sec-filings?limit=50&sortColumn=filed&sortOrder=desc` |

## Usage

```bash
# All sections
python3 scrape_nasdaq.py ONDS

# Individual sections
python3 scrape_nasdaq.py ONDS --news
python3 scrape_nasdaq.py ONDS --press-releases
python3 scrape_nasdaq.py ONDS --institutional
python3 scrape_nasdaq.py ONDS --insider
python3 scrape_nasdaq.py ONDS --sec-filings

# Save output
python3 scrape_nasdaq.py ONDS --output /path/to/data/
```

## Key Implementation Notes

### News & Press Releases (REST API — no browser needed)
- Direct HTTP GET, no Playwright required
- Returns up to 50 items per call
- News API: `https://www.nasdaq.com/api/news/topic/articlebysymbol?q={TICKER}|STOCKS&offset=0&limit=50`
- Press Release API: `https://www.nasdaq.com/api/news/topic/press_release?q=symbol:{ticker}|assetclass:stocks&limit=50&offset=0`
- User-Agent header required

### Institutional Holdings & Insider Activity (Playwright required)
- Nasdaq uses custom web component `<nsdq-table>` with **shadow DOM**
- Data is stored in `table.shadowRoot` — cannot be accessed by normal DOM queries
- Must use `page.evaluate()` with JavaScript to extract:
  ```javascript
  page.evaluate("""
    () => {
      const results = {};
      const nsdqTables = document.querySelectorAll('nsdq-table');
      nsdqTables.forEach((table, idx) => {
        const shadow = table.shadowRoot;
        if (!shadow) return;
        // ... extract headers and rows from shadow DOM
      });
      return results;
    }
  """)
  ```
- Key container classes for classification:
  - Institutional: `institutional-holders`, `active-positions`, `ownership-summary`
  - Insider: `shares-traded-table`, `transactions-table`, `insider-trades-summary`
- `nsdq-table` elements exist immediately but data populates after ~6 seconds
- Use `time.sleep(6)` before extraction, or `wait_for_function` on `document.querySelectorAll('nsdq-table').length > 0`

### SEC Filings
- REST API: `https://api.nasdaq.com/api/company/{TICKER}/sec-filings?limit=50&sortColumn=filed&sortOrder=desc&IsQuoteMedia=true`
- Accept: `application/json` header
- Returns last 50 filings with HTML/DOC/PDF/XBRL links
- 10-K and 10-Q links extracted separately (latest per type)
- HTML link preferred: `view.htmlLink` (easier to parse than PDF)

## Output Structure

```json
{
  "ticker": "ONDS",
  "fetch_timestamp": "2026-05-02 02:44:00",
  "source": "nasdaq.com",
  "news": {
    "count": 50,
    "items": [{"id", "title", "description", "publisher", "ago", "created", "url", "related_symbols"}]
  },
  "press_releases": {
    "count": 50,
    "items": [{"id", "title", "ago", "created", "url", "related_symbols"}]
  },
  "institutional_holdings": {
    "active_positions": {"headers": [...], "rows": [[...], ...]},
    "top_holders": {"headers": [...], "rows": [[...], ...]}  // Top 10
  },
  "insider_activity": {
    "shares_traded": {"headers": [...], "rows": [[...], ...]},
    "top_trades": {"headers": [...], "rows": [[...], ...]}  // Top 10
  },
  "sec_filings": {
    "count": 50,
    "filings": [{"form_type", "filed_date", "period", "html_link", "doc_link", "pdf_link", "xbrl_link"}],
    "latest_10k": {...},  // HTML link preferred
    "latest_10q": {...}   // null if none in 50
  }
}
```

## Dependencies
```bash
pip install playwright
playwright install chromium
```

## Chrome Path
`/usr/bin/google-chrome-beta` — use headed=False with Xvfb or headed=True for anti-detection.
