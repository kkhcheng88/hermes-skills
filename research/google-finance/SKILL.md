---
name: google-finance
description: Fetch news headlines and full articles from Google Finance Beta (news aggregator). Use Chrome Beta + Xvfb + Playwright to browse to https://www.google.com/finance/beta/quote/SYMBOL:EXCHANGE, expand news with "Show more", collect article links, and read articles one by one. Complements yahoo skill for news coverage.
version: 1.0.0
metadata:
  hermes:
    tags: [stocks, news, research, google-finance]
---

# Google Finance News Skill

## Overview

Google Finance Beta aggregates news from multiple sources (Timothy Sykes, StocksToTrade, Benzinga, Insider Monkey, Investing.com, etc.) into one feed. This skill scrapes the news section directly from Google Finance Beta — no API key needed.

## Environment

- **Chrome Beta** (`/usr/bin/google-chrome-beta`) + **Xvfb** + **Playwright** (headed/non-headless mode)
- Always use `xvfb-run` wrapper — Google Finance Beta requires JavaScript rendering

## When to Use

- Need latest news headlines for a stock (small/mid-cap with thin coverage)
- Want to read full articles from aggregator sources without subscribing
- Use alongside `yahoo` skill for complete news picture

## Workflow

### Step 1 — Navigate to Google Finance Beta

```python
from playwright.sync_api import sync_playwright
import time, re

ticker = "ONDS"
exchange = "NASDAQ"  # or "NYSE"
url = f"https://www.google.com/finance/beta/quote/{ticker}:{exchange}"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
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
```

### Step 2 — Scroll to News Section & Click "Show more"

```python
    # Scroll down to news section
    page.mouse.wheel(0, 3000)
    time.sleep(2)

    # Expand all news with "Show more" button
    try:
        show_more = page.get_by_text("Show more")
        show_more.click(timeout=5000)
        time.sleep(3)
    except Exception as e:
        print(f"No 'Show more' button or already expanded: {e}")
```

### Step 3 — Extract All Article Links

```python
    # Get page HTML and extract article URLs
    body_html = page.content()
    
    # Extract direct article links (not Google redirects)
    article_links = re.findall(
        r'href="(https?://(?:www\.)?(?:timothysykes|stockstotrade|investing\.com|benzinga|insidermonkey|stocktwits|accesswire|cmoney|marketwatch)[^"]*)"',
        body_html
    )
    # Deduplicate while preserving order
    article_links = list(dict.fromkeys(article_links))
```

### Step 4 — Read Articles One by One

```python
    articles = []
    
    for i, url in enumerate(article_links):
        print(f"\n[{i+1}/{len(article_links)}] Reading: {url[:80]}")
        
        article_page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        try:
            article_page.goto(url, timeout=15000)
            time.sleep(3)
            
            title = article_page.title()
            text = article_page.inner_text('body')
            
            if len(text) < 200:
                print(f"  ⚠️ Blocked or empty page")
                article_page.close()
                continue
            
            # Clean up text (remove accessibility nav, footers)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            # Remove repetitive nav lines
            cleaned = [l for l in lines if l not in [
                'NEWS', 'BLOG', 'TRADING GUIDES', 'STOCKS', 'RESOURCES', 'ABOUT',
                'Watch Live', 'Press Alt+1 for screen-reader mode, Alt+0 to cancel',
                'Accessibility Screen-Reader Guide, Feedback, and Issue Reporting | New window'
            ]]
            
            content = '\n'.join(cleaned)
            
            articles.append({
                'source': url.split('/')[2].replace('www.', ''),
                'url': url,
                'title': title,
                'content': content[:5000]  # cap at 5000 chars
            })
            print(f"  ✅ OK — {len(content)} chars")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
        finally:
            article_page.close()
    
    browser.close()
```

## Known Source Reliability

| Source | Status | Notes |
|--------|--------|-------|
| timothysykes.com | ✅ | Always loads, full content |
| stockstotrade.com | ✅ | Always loads, full content |
| investing.com | ✅ | Loads but has paywall overlay (read text before sign-up prompt) |
| benzinga.com | ❌ | Timeout — skip |
| insidermonkey.com | ❌ | Timeout — skip |
| accesswire.com | ⚠️ | May work, test first |
| cmoney.com | ⚠️ | May work, test first |
| stocktwits.com | ⚠️ | May work, test first |

## Output Structure

```python
{
    "ticker": "ONDS",
    "exchange": "NASDAQ",
    "fetch_date": "2026-05-01T22:00:00",
    "source": "google_finance_beta",
    "articles": [
        {
            "source": "timothysykes.com",
            "url": "https://www.timothysykes.com/news/...",
            "title": "ONDS Stock Draws Traders As Defense Contracts...",
            "content": "Full article text (first 5000 chars)..."
        },
        ...
    ],
    "summary": {
        "total_found": 7,
        "successfully_read": 4,
        "blocked": ["benzinga.com", "insidermonkey.com"]
    }
}
```

## Full Script Template

```python
#!/usr/bin/env python3
"""google_finance_news.py — Fetch news from Google Finance Beta"""

from playwright.sync_api import sync_playwright
import time, re, json, sys

def fetch_google_finance_news(ticker, exchange="NASDAQ", max_articles=10):
    url = f"https://www.google.com/finance/beta/quote/{ticker}:{exchange}"
    
    articles = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
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
        
        # Scroll to news section
        page.mouse.wheel(0, 3000)
        time.sleep(2)
        
        # Expand all news
        try:
            page.get_by_text("Show more").click(timeout=5000)
            time.sleep(3)
        except:
            pass
        
        # Extract article links
        body_html = page.content()
        article_links = re.findall(
            r'href="(https?://(?:www\.)?(?:timothysykes|stockstotrade|investing\.com|benzinga|insidermonkey|stocktwits|accesswire|cmoney|marketwatch)[^"]*)"',
            body_html
        )
        article_links = list(dict.fromkeys(article_links))[:max_articles]
        
        print(f"Found {len(article_links)} article URLs")
        
        for i, url in enumerate(article_links):
            print(f"\n[{i+1}/{len(article_links)}] {url[:70]}")
            
            article_page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            try:
                article_page.goto(url, timeout=15000)
                time.sleep(3)
                
                text = article_page.inner_text('body')
                if len(text) < 200:
                    print(f"  ⚠️ Blocked/empty")
                    article_page.close()
                    continue
                
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                skip_phrases = ['NEWS', 'BLOG', 'TRADING GUIDES', 'STOCKS', 'RESOURCES', 
                               'ABOUT', 'Watch Live', 'Press Alt+1', 'Accessibility Screen-Reader']
                cleaned = [l for l in lines if not any(s in l for s in skip_phrases)]
                
                articles.append({
                    'source': url.split('/')[2].replace('www.', ''),
                    'url': url,
                    'title': article_page.title(),
                    'content': '\n'.join(cleaned)[:5000]
                })
                print(f"  ✅ {len(cleaned)} chars")
                
            except Exception as e:
                print(f"  ❌ {e}")
            finally:
                article_page.close()
        
        browser.close()
    
    return {
        'ticker': ticker,
        'exchange': exchange,
        'fetch_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'source': 'google_finance_beta',
        'articles': articles,
        'summary': {
            'total_found': len(article_links),
            'successfully_read': len(articles)
        }
    }

if __name__ == '__main__':
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'ONDS'
    exchange = sys.argv[2] if len(sys.argv) > 2 else 'NASDAQ'
    
    result = fetch_google_finance_news(ticker, exchange)
    
    output_file = f"data/companies/{ticker}/google_finance_news.json"
    import os
    os.makedirs(f"data/companies/{ticker}", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Saved to {output_file}")
    print(f"   Articles read: {result['summary']['successfully_read']}/{result['summary']['total_found']}")
```

## Usage

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  python3 google_finance_news.py ONDS NASDAQ

xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  python3 google_finance_news.py AAPL NYSE
```

## Notes

- **No API key** — pure browser automation
- **Some sources timeout** (Benzinga, Insider Monkey) — skip and continue, not fatal
- **Investing.com has paywall** — read text before the sign-up prompt appears
- **Always use headed mode with Xvfb** — headless may miss JS-rendered content
