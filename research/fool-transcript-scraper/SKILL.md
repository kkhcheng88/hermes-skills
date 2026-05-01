---
name: fool-transcript-scraper
version: "1.0"
description: Scrape earnings call transcripts from The Motley Fool using headed Playwright + Xvfb. Fool provides FREE transcripts unlike Yahoo Finance (paywalled).
tags: ["earnings", "transcripts", "motley-fool", "playwright"]
---

# Motley Fool Transcript Scraper

## Source
- **The Motley Fool** — free earnings call transcripts (no paywall unlike Yahoo Finance)
- Listing: `https://www.fool.com/earnings-call-transcripts/?ticker={TICKER}`
- Transcript: `https://www.fool.com/earnings/call-transcripts/YYYY/MM/DD/ticker-qX-YYYY-earnings-transcript/`

## Method
**Headed Chromium via Xvfb** — fool.com detects headless browsers, must use headed mode.

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" python3 scrap_fool.py MSFT
```

## Key Discovery
- **Fool transcripts are FREE** — Yahoo Finance transcripts need Silver/Gold subscription
- Yahoo earnings API: only 2,447 preview chars (paywalled)
- Fool: full 50k+ char transcripts + 32 takeaways for FREE

## Known Issues / Limitations

### Listing Page URL Extraction (2026-05-01)
The `article a[href*="ticker"]` DOM query on the listing page often returns 0 results or the listing page itself (with `#` fragment) rather than actual transcript URLs. Root cause: Fool's listing page uses JS-based lazy loading that may not complete within the current 3-second wait, or the selector anchors are dynamically rendered.

**Workaround**: 
1. First use the EDGAR EFTS search API to find filing dates (see `edgar-sec-filing-workaround` skill)
2. Then construct the direct transcript URL: `https://www.fool.com/earnings/call-transcripts/YYYY/MM/DD/ticker-qX-YYYY-earnings-transcript/`
3. If 404, try alternate patterns:
   - `https://www.fool.com/earnings/call-transcripts/YYYY/MM/DD/ticker-inc-ticker-qX-YYYY-earnings/`
   - `https://www.fool.com/earnings/call-transcripts/YYYY/MM/DD/ticker-qX-YYYY/`
4. Test all URL variants with HEAD request first before scraping

### Fool URL Patterns (verified 2026-05-01)
Common patterns that return 404 for recent tickers — always verify with HEAD before scraping:
```
https://www.fool.com/earnings/call-transcripts/YYYY/MM/DD/axti-q1-2026-earnings-transcript/  → 404
https://www.fool.com/earnings/call-transcripts/YYYY/MM/DD/axt-inc-axti-q1-2026-earnings/   → 404
```

## Output
- `transcript` — Full text (up to 50k chars)
- `takeaways` — 32 bullet points with metrics ($ / % / billion)
- `title` / `date` — Metadata

## Selector (transcript body)
```javascript
const selectors = [
    'article .article-content',
    'article .cauliflower',
    'article',
];
// Return first with text.length > 500
```

## Selector (takeaways)
```javascript
// After "Takeaways" h2, next <ul> contains bullets
// Filter: text.length > 30 AND contains ($ or % or billion or million)
```

## Example Output MSFT Q3 FY2026
| Metric | Value |
|--------|-------|
| Revenue | $82.9B (+18%) |
| Azure | +31-33% |
| AI ARR | $37B (+123%) |
| Copilot Seats | 20M (+250%) |
| CapEx FY2026 | ~$190B |
