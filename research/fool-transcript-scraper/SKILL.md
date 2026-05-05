---
name: fool-transcript-scraper
version: "2.0"
description: Scrape earnings call transcripts from The Motley Fool using headed Playwright + Xvfb. Fool provides FREE transcripts unlike Yahoo Finance (paywalled).
tags: ["earnings", "transcripts", "motley-fool", "playwright"]
---

# Motley Fool Transcript Scraper

## Source
- **The Motley Fool** — free earnings call transcripts (no paywall unlike Yahoo Finance)
- Quote Page: `https://www.fool.com/quote/nasdaq/{ticker}/` (or `/quote/nyse/{ticker}/`)
- Transcript URL pattern: `https://www.fool.com/earnings/call-transcripts/YYYY/MM/DD/{ticker}-qX-YYYY-earnings-call-transcript/`

## Method

### Flow (Updated 2026-05-05)
1. Navigate to quote page: `https://www.fool.com/quote/nasdaq/{ticker}/`
2. Find News section
3. Click "Earnings Transcripts" tab
4. Extract transcript links from the list
5. Visit each transcript page and extract full text

### Command
```bash
# Basic usage - get latest transcript
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" python3 scrap_fool.py AXTI

# Get multiple transcripts
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" python3 scrap_fool.py AXTI --count 3
```

### Key Discovery
- **Fool transcripts are FREE** — Yahoo Finance transcripts need Silver/Gold subscription
- Yahoo earnings API: only 2,447 preview chars (paywalled)
- Fool: full 50k+ char transcripts + 32 takeaways for FREE
- **Correct entry point**: Quote page (`/quote/nasdaq/{ticker}/`), NOT `/earnings-call-transcripts/?ticker=`

## URL Structure

### Quote Page (Entry Point)
```
https://www.fool.com/quote/nasdaq/axti/
https://www.fool.com/quote/nyse/be/
```

The page will auto-redirect to the correct exchange (NYSE/NASDAQ).

### Transcript URL Pattern
```
https://www.fool.com/earnings/call-transcripts/2026/04/30/axt-axti-q1-2026-earnings-call-transcript/
```

Note: The ticker in URL may include company name prefix (e.g., `axt-axti` instead of just `axti`).

## Selectors

### Quote Page
- News section: `[class*="news"]`, `section:has-text("News")`
- Earnings Transcripts tab: `[role="tablist"] button:has-text("Earnings Transcripts")`, `a:has-text("transcript")`

### Transcript Page
```javascript
const selectors = [
    'article .article-content',
    'article .cauliflower',
    'article [data-testid="body"]',
    'article',
];
// Return first with text.length > 500
```

### Takeaways
```javascript
// After "Takeaways" h2, next <ul> contains bullets
// Filter: text.length > 30 AND contains ($ or % or billion or million)
```

## Output

### File
- `data/companies/{TICKER}/fool_scraped.json`

### Structure
```json
{
  "ticker": "AXTI",
  "fetch_date": "2026-05-05T13:00:00",
  "source": "motley_fool_web",
  "quote_page": "https://www.fool.com/quote/nasdaq/axti/",
  "transcript_links_found": ["https://..."],
  "transcripts": [
    {
      "url": "https://www.fool.com/earnings/call-transcripts/2026/04/30/axt-axti-q1-2026-earnings-call-transcript/",
      "title": "AXT Inc (AXTI) Q1 2026 Earnings Call Transcript",
      "date": "2026-04-30",
      "quarter": "Q1 2026",
      "transcript": "... (up to 50k chars)",
      "transcript_length": 45678,
      "takeaways": ["Revenue: $12.3M (+15%)", ...]
    }
  ]
}
```

## Known Issues / Limitations

### Exchange Detection
The script tries NASDAQ first, then detects NYSE from redirect. If your ticker is on NYSE, you may see a brief redirect.

### Transcript URL Variations
Fool uses inconsistent URL patterns:
- `{ticker}-q1-2026-earnings-call-transcript/`
- `{company-name}-{ticker}-q1-2026-earnings-call-transcript/`
- `{ticker}-q1-2026-earnings-transcript/`

The script extracts links from the page rather than constructing URLs.

### Rate Limiting
Fool may rate-limit automated requests. Use reasonable delays between requests.

## Comparison with Other Sources

| Source | Cost | Latest Transcript | Historical | Quality |
|--------|------|-------------------|------------|---------|
| **Motley Fool** | FREE | ✅ Full text | ✅ Up to 3+ years | Excellent |
| Yahoo Finance | Paid | Preview only | ❌ | Good |
| DefeatBeta | FREE | ✅ Full text | ✅ Best source | Good |

## Changelog
| Date | Version | Change |
|------|---------|--------|
| 2026-05-05 | 2.0 | Fixed URL flow: use quote page → News → Earnings Transcripts tab; added multi-transcript support |
| 2026-05-01 | 1.0 | Initial version |
