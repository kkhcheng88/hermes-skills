#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIO Engine - The Motley Fool Earnings Transcript Scraper
==========================================================
Method: Playwright with headed Chrome + Xvfb (same as scrap_yahoo_web.py)
Strategy: DOM scraping for earnings call transcripts

Usage:
    python scrap_fool.py MSFT
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")

OUTPUT_DIR = "data/companies"


def get_fool_urls(ticker: str) -> dict:
    """Generate The Motley Fool URLs for a ticker"""
    base = f"https://www.fool.com/earnings/call-transcripts"
    search = f"https://www.fool.com/earnings-call-transcripts/?ticker={ticker}"
    return {
        "listing": search,
        "base": base,
    }


async def scrape_fool_transcript(page, ticker: str) -> dict:
    """Scrape earnings call transcript from The Motley Fool"""
    print(f"Scraping Fool transcript for {ticker}...")
    
    urls = get_fool_urls(ticker)
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
        "source": "motley_fool_web",
        "transcripts": [],
    }
    
    try:
        # Navigate to the listing page to find the latest transcript URL
        await page.goto(urls["listing"], wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)  # Wait for JS to render
        
        # Extract all transcript links for this ticker
        transcript_links = await page.evaluate(f"""() => {{
            const links = document.querySelectorAll('article a[href*="{ticker.lower()}"]');
            const results = [];
            links.forEach(a => {{
                const href = a.href;
                if (href.includes('/earnings/call-transcripts/') || href.includes('/earnings-call-transcripts/')) {{
                    results.push(href);
                }}
            }});
            return [...new Set(results)];
        }}""")
        
        print(f"  Found {len(transcript_links)} transcript links")
        
        if not transcript_links:
            # Try alternate approach - search page for transcript URLs
            transcript_links = await page.evaluate(f"""() => {{
                const allLinks = document.querySelectorAll('a[href]');
                const results = [];
                allLinks.forEach(a => {{
                    const href = a.href;
                    if (href.includes('earnings') && href.includes('{ticker}') && href.includes('transcript')) {{
                        results.push(href);
                    }}
                }});
                return [...new Set(results)];
            }}""")
            print(f"  Alt approach found {len(transcript_links)} transcript links")
        
        # Get the most recent transcript
        if transcript_links:
            latest_url = transcript_links[0]
            print(f"  Fetching latest transcript: {latest_url}")
            
            await page.goto(latest_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)
            
            # Extract title and metadata
            title = await page.title()
            date_match = re.search(r'(\w+ \d+, \d{4})', await page.inner_text('main'))
            date_str = date_match.group(1) if date_match else ""
            
            # Extract full transcript text - try multiple selectors
            transcript_text = await page.evaluate("""() => {
                // Try multiple selectors for the article body
                const selectors = [
                    'article .article-content',
                    'article .cauliflower',
                    'article [data-testid="body"]',
                    'article .entry-content',
                    'article .post-content',
                    'article main',
                    '[role="main"] article',
                    '.article-body',
                    '.earnings-transcript',
                    'article',
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        const text = el.innerText.trim();
                        if (text.length > 500) return text;
                    }
                }
                // Last resort: all text in main
                const main = document.querySelector('main');
                if (main) return main.innerText;
                return document.body.innerText;
            }""")
            
            # Extract Takeaways - they come after "Takeaways" heading
            takeaways = await page.evaluate("""() => {
                const headings = document.querySelectorAll('h2, h3, [class*="heading"]');
                let takeawaysEl = null;
                for (const h of headings) {
                    if (h.innerText.toLowerCase().includes('takeaway')) {
                        // Walk up to find section, then get following content
                        let parent = h.closest('section') || h.parentElement;
                        // Get the next sibling element
                        let next = h.nextElementSibling;
                        if (next && next.tagName === 'UL') {
                            const items = next.querySelectorAll('li');
                            const results = [];
                            items.forEach(li => {
                                const strong = li.querySelector('strong');
                                const text = li.innerText.trim();
                                // Filter: skip pure names (no numbers/stats) and short items
                                if (text.length > 30 && (text.includes('$') || text.includes('%') || text.includes('billion') || text.includes('million'))) {
                                    results.push(text);
                                }
                            });
                            if (results.length > 0) return results;
                        }
                    }
                }
                return [];
            }""")
            
            result["transcripts"].append({
                "url": latest_url,
                "title": title,
                "date": date_str,
                "transcript": transcript_text[:50000],  # Cap at 50k chars
                "transcript_length": len(transcript_text),
                "takeaways": takeaways,
            })
            
            print(f"  Got transcript: {len(transcript_text)} chars, {len(takeaways)} takeaways")
            
    except Exception as e:
        print(f"  Error: {e}")
        result["error"] = str(e)
    
    return result


async def scrape_all(ticker: str) -> dict:
    """Main scrape function"""
    if not HAS_PLAYWRIGHT:
        return {"error": "Playwright not installed"}
    
    output_dir = os.path.join(OUTPUT_DIR, ticker.upper())
    os.makedirs(output_dir, exist_ok=True)
    
    result = {}
    
    async with async_playwright() as p:
        # Launch headed (non-headless) Chromium like scrap_yahoo_web.py
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Set extra headers to look more like a real browser
        await page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        
        try:
            result = await scrape_fool_transcript(page, ticker.upper())
        finally:
            await browser.close()
    
    # Save to file
    output_path = os.path.join(output_dir, "fool_scraped.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_path}")
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scrap_fool.py <TICKER>")
        sys.exit(1)
    
    ticker = sys.argv[1].upper().strip()
    result = asyncio.run(scrape_all(ticker))
    print(f"\nResult: {json.dumps(result, indent=2)[:2000]}")
