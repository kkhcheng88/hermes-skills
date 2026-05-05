#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CIO Engine - The Motley Fool Earnings Transcript Scraper
==========================================================
Method: Playwright with headed Chrome
Strategy: Navigate to quote page → Click "Earnings Transcripts" button → Extract links

Discovery (2026-05-05):
- The correct flow: /quote/nasdaq/{ticker}/ → Click "Earnings Transcripts" button
- Button selector: button with text "Earnings Transcripts"
- Transcript links are in format: /earnings/call-transcripts/YYYY/MM/DD/...

Usage:
    python scrap_fool.py AXTI
    python scrap_fool.py AXTI --count 3
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


def get_fool_quote_url(ticker: str, exchange: str = "nasdaq") -> str:
    """Generate The Motley Fool quote page URL for a ticker"""
    return f"https://www.fool.com/quote/{exchange.lower()}/{ticker.lower()}/"


async def scrape_fool_transcripts(page, ticker: str, count: int = 1) -> dict:
    """Scrape earnings call transcripts from The Motley Fool
    
    Flow:
    1. Go to quote page: /quote/nasdaq/{ticker}/
    2. Click "Earnings Transcripts" button (not a link!)
    3. Wait for content to load
    4. Extract transcript links from the list
    5. Visit each transcript page and extract full text
    """
    print(f"Scraping Fool transcripts for {ticker} (max {count})...")
    
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
        "source": "motley_fool_web",
        "quote_page": "",
        "transcripts": [],
    }
    
    try:
        # Step 1: Navigate to quote page
        quote_url = get_fool_quote_url(ticker, "nasdaq")
        print(f"  Step 1: Navigating to quote page: {quote_url}")
        
        await page.goto(quote_url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)  # Wait for page to fully render
        
        result["quote_page"] = page.url
        print(f"  Quote page loaded: {page.url}")
        
        # Step 2: Click "Earnings Transcripts" button
        print(f"  Step 2: Looking for 'Earnings Transcripts' button...")
        
        # Use text-based selector for the button
        earnings_button = page.get_by_role("button", name="Earnings Transcripts")
        
        if await earnings_button.count() > 0:
            print(f"  Found 'Earnings Transcripts' button, clicking...")
            await earnings_button.click()
            await asyncio.sleep(3)  # Wait for content to load
            print(f"  Clicked, waiting for content...")
        else:
            # Fallback: try finding by text content
            print(f"  Button not found via role, trying text selector...")
            button_found = await page.evaluate("""() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.innerText.includes('Earnings Transcripts')) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            }""")
            
            if button_found:
                print(f"  Found and clicked button via text search")
                await asyncio.sleep(3)
            else:
                result["error"] = "Could not find 'Earnings Transcripts' button"
                print(f"  ERROR: Button not found")
                return result
        
        # Step 3: Extract transcript links
        print(f"  Step 3: Extracting transcript links...")
        
        transcript_links = await page.evaluate("""() => {
            const links = [];
            // Look for all links that contain /earnings/call-transcripts/
            const allLinks = document.querySelectorAll('a[href]');
            allLinks.forEach(a => {
                const href = a.href;
                if (href.includes('/earnings/call-transcripts/')) {
                    if (!links.includes(href)) {
                        links.push(href);
                    }
                }
            });
            return links;
        }""")
        
        print(f"  Found {len(transcript_links)} transcript links")
        result["transcript_links_found"] = transcript_links
        
        # Step 4: Visit each transcript page and extract content
        transcripts_to_fetch = transcript_links[:count] if transcript_links else []
        
        for i, transcript_url in enumerate(transcripts_to_fetch):
            print(f"  Step 4.{i+1}: Fetching transcript from: {transcript_url}")
            
            try:
                await page.goto(transcript_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)
                
                title = await page.title()
                
                # Extract date from URL
                date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', transcript_url)
                if date_match:
                    date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                else:
                    date_str = ""
                
                # Extract quarter info from URL
                quarter_match = re.search(r'-q(\d)-(\d{4})', transcript_url.lower())
                if quarter_match:
                    quarter_str = f"Q{quarter_match.group(1)} {quarter_match.group(2)}"
                else:
                    quarter_str = ""
                
                # Extract full transcript text
                transcript_text = await page.evaluate("""() => {
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
                    const main = document.querySelector('main');
                    if (main) return main.innerText;
                    return document.body.innerText;
                }""")
                
                # Extract Takeaways
                takeaways = await page.evaluate("""() => {
                    const headings = document.querySelectorAll('h2, h3, [class*="heading"]');
                    for (const h of headings) {
                        if (h.innerText.toLowerCase().includes('takeaway')) {
                            let next = h.nextElementSibling;
                            if (next && next.tagName === 'UL') {
                                const items = next.querySelectorAll('li');
                                const results = [];
                                items.forEach(li => {
                                    const text = li.innerText.trim();
                                    if (text.length > 30 && 
                                        (text.includes('$') || text.includes('%') || 
                                         text.includes('billion') || text.includes('million'))) {
                                        results.push(text);
                                    }
                                });
                                if (results.length > 0) return results;
                            }
                        }
                    }
                    return [];
                }""")
                
                transcript_data = {
                    "url": transcript_url,
                    "title": title,
                    "date": date_str,
                    "quarter": quarter_str,
                    "transcript": transcript_text[:50000],
                    "transcript_length": len(transcript_text),
                    "takeaways": takeaways,
                }
                
                result["transcripts"].append(transcript_data)
                print(f"    Got {len(transcript_text)} chars, {len(takeaways)} takeaways")
                
            except Exception as e:
                print(f"    Error fetching transcript: {e}")
                result["transcripts"].append({
                    "url": transcript_url,
                    "error": str(e),
                })
        
        if not transcript_links:
            result["error"] = "No transcript links found after clicking button"
            print(f"  No transcript links found")
        
    except Exception as e:
        print(f"  Error: {e}")
        result["error"] = str(e)
    
    return result


async def scrape_all(ticker: str, count: int = 1) -> dict:
    """Main scrape function"""
    if not HAS_PLAYWRIGHT:
        return {"error": "Playwright not installed"}
    
    output_dir = os.path.join(OUTPUT_DIR, ticker.upper())
    os.makedirs(output_dir, exist_ok=True)
    
    result = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        
        try:
            result = await scrape_fool_transcripts(page, ticker.upper(), count)
        finally:
            await browser.close()
    
    output_path = os.path.join(output_dir, "fool_scraped.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_path}")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Motley Fool earnings transcripts")
    parser.add_argument("ticker", help="Stock ticker symbol")
    parser.add_argument("--count", type=int, default=1, help="Number of transcripts to fetch (default: 1)")
    
    args = parser.parse_args()
    
    ticker = args.ticker.upper().strip()
    result = asyncio.run(scrape_all(ticker, args.count))
    
    if result.get("transcripts"):
        print(f"\n=== Summary ===")
        print(f"Ticker: {ticker}")
        print(f"Transcripts fetched: {len(result['transcripts'])}")
        for t in result["transcripts"]:
            if "error" not in t:
                print(f"  - {t.get('quarter', t.get('date', 'unknown'))}: {t['transcript_length']} chars")
    else:
        print(f"\nNo transcripts fetched. Error: {result.get('error', 'unknown')}")
