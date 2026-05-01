---
name: wsl-chrome-anti-detection
version: 2.0
description: Generic browser standard for ALL non-API web activities. Chrome Beta + Xvfb + Playwright headed mode is the default for any web scraping, content extraction, or browsing. This is NOT optional — if web_extract/web_search fails or returns empty/unauthorized, switch to browser immediately.
---

# WSL Chrome Anti-Detection — Generic Browser Standard

## Golden Rule

> **ALL non-API web activities MUST use Chrome Beta + Xvfb + Playwright (headed/non-headless mode).**
>
> If `web_search` or `web_extract` returns empty, blocked, 401, 403, or 429 — **DO NOT SKIP**. Switch to browser.

## When to Use

| Method | Use When |
|--------|----------|
| **Chrome Beta + Xvfb + Playwright** | Any website content, JS-rendered pages, article scraping, news feeds, dynamic content |
| API calls (yfinance, NewsAPI, etc.) | Structured data that doesn't require browsing |

## When to SWITCH to Browser

- `web_extract` returns `401 Unauthorized`, `403 Forbidden`, `429 Rate Limited`, or empty
- `web_search` returns sparse/irrelevant results
- Page requires JavaScript to render (SPA, lazy-loaded content)
- You need to click, scroll, interact with page elements
- **Never skip and report failure — always try browser first**

## Standard Launch Code

```python
from playwright.sync_api import sync_playwright
import time

url = "https://example.com"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,  # headed mode — NOT headless
        executable_path="/usr/bin/google-chrome-beta",
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
        ]
    )
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto(url, timeout=20000)
    time.sleep(5)
    
    content = page.inner_text('body')
    html = page.content()
    
    browser.close()
```

## Xvfb Wrapper (Always Required)

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" python3 script.py
```

**Do NOT use `headless=True`** — headless mode is more easily detected. Non-headless (headed) with Xvfb is the correct approach.

## Environment

- **Chrome Beta** (`/usr/bin/google-chrome-beta`)
- **Playwright** CLI with chromium browsers
- **Xvfb** for virtual display
- Run on **WSL2** (local Windows PC, not cloud)

## Known Site Reliability

| Site | Browser | API | Notes |
|------|---------|-----|-------|
| Google Finance Beta | ✅ | — | News aggregator, click "Show more" to expand |
| Yahoo Finance | ✅ | ✅ (yfinance) | Web scraping for transcripts/analysts |
| Timothy Sykes | ✅ | — | Full article content |
| StocksToTrade | ✅ | — | Full article content |
| Investing.com | ✅ | — | Has paywall overlay, read before prompt |
| Motley Fool | ✅ | — | Full earnings transcripts |
| SEC EDGAR | ✅ | ✅ | EFTS API available |
| Benzinga | ❌ | — | Timeout — skip |
| Insider Monkey | ❌ | — | Timeout — skip |
| Finviz | ❌ | — | Timeout |
| Seeking Alpha | ❌ | — | Requires login |
| Reddit | ❌ | — | reCAPTCHA Enterprise v3 — all automation blocked |

## Skills Using This Standard

These skills explicitly use Chrome Beta + Xvfb:

| Skill | Purpose |
|-------|---------|
| `yahoo` | Yahoo Finance web scraping (transcripts, analysts) |
| `google-finance` | Google Finance Beta news articles |
| `fool-transcript-scraper` | Motley Fool earnings transcripts |
| `edgar-sec-filing-workaround` | SEC filings extraction |
| `wsl-chrome-anti-detection` | This skill — source of truth |

## Key Insight: Browser Fingerprint > IP

The problem is NOT IP-based (Karson has residential IP). The problem is **browser fingerprint detection**:
- Headless Chrome → blocked
- Chrome with automation flags → blocked
- Chrome Beta + Xvfb (headed) → works on most sites
- Some sites (Reddit) block ALL automated browsers regardless of method

## Common Mistakes to Avoid

1. **"web_extract failed, I'll just skip"** → Wrong. Switch to browser immediately.
2. **Using headless=True** → Wrong. Use headless=False + Xvfb.
3. **Using web_extract for JS-rendered pages** → Wrong. Use browser.
4. **Not using Xvfb** → Without virtual display, headed Chrome won't work on WSL.
5. **Using `requests` or `urllib` for JS sites** → Wrong. These can't handle JS-rendered content.

## Reddit (Exception)

Reddit uses reCAPTCHA Enterprise v3 — ALL automated browsers get blocked regardless of method:
- Headless Chrome → blocked
- Chrome Beta + Xvfb → blocked
- undetected-chromedriver → blocked
- **Only manual Windows Chrome works**

For Reddit content, use the official Reddit API if needed.
