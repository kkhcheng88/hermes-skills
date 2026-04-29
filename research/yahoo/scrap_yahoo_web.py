# -*- coding: utf-8 -*-
"""
CIO Engine - Yahoo Finance Web Scraper
======================================
Method: Playwright with Chrome
Strategy: 1) Check for API first, 2) DOM scraping if no API

Features:
- Analyst ratings with dates
- Analyst scores (Overall, Direction, Price)
- Upgrades/Downgrades history (with pagination)
- Company news
- Full analyst upgrade/downgrade history

Usage:
    python engine/scripts/scrap_yahoo_web.py TSLA
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Try to import playwright
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")


# ============================================================
# Configuration
# ============================================================

YAHOO_BASE_URL = "https://finance.yahoo.com/quote"
DEFAULT_OUTPUT_DIR = "data/companies"


# ============================================================
# Yahoo Finance URLs
# ============================================================

def get_yahoo_urls(ticker: str) -> Dict[str, str]:
    """Generate all Yahoo Finance URLs for a ticker"""
    base = f"{YAHOO_BASE_URL}/{ticker}"
    return {
        "summary": f"{base}/",
        "analyst": f"{base}/analyst-insights/",
        "news": f"{base}/news/",
        "financials": f"{base}/financials/",
        "statistics": f"{base}/statistics/",
        "holders": f"{base}/holders/",
        "options": f"{base}/options/",
        "earnings_calls": f"{base}/earnings-calls/",
        "sec_filings": f"{base}/sec-filing/",
    }


# ============================================================
# API Detection
# ============================================================

async def detect_api(page, ticker: str) -> Dict[str, Any]:
    """Detect Yahoo Finance API endpoints from network requests"""
    print("Detecting API endpoints...")
    
    api_endpoints = []
    
    def handle_request(request):
        url = request.url
        if any(pattern in url for pattern in ['query', 'v1', 'v2', 'finance', 'quote', 'api']):
            api_endpoints.append({
                "url": url.split('?')[0],
                "method": request.method,
                "resource_type": request.resource_type,
            })
    
    page.on("request", handle_request)
    
    urls = get_yahoo_urls(ticker)
    try:
        await page.goto(urls["analyst"], wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"  Navigation timeout, continuing: {e}")
    
    await asyncio.sleep(3)
    
    unique_apis = {}
    for api in api_endpoints:
        base_url = api["url"]
        if base_url not in unique_apis:
            unique_apis[base_url] = api
    
    result = {
        "total_requests": len(api_endpoints),
        "unique_api_endpoints": list(unique_apis.values())[:20],
    }
    
    print(f"  Found {len(unique_apis)} unique API endpoints")
    return result


# ============================================================
# DOM Scraping - Analyst Data
# ============================================================

async def scrape_analyst_data(page, ticker: str) -> Dict[str, Any]:
    """Scrape analyst data from Yahoo Finance"""
    print("Scraping analyst data...")
    
    urls = get_yahoo_urls(ticker)
    try:
        await page.goto(urls["analyst"], wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"  Navigation timeout: {e}")
    await asyncio.sleep(3)
    
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
        "source": "yahoo_finance_web",
    }
    
    # 1. Top Analysts Table
    print("  Scraping Top Analysts table...")
    try:
        top_analysts = await page.evaluate('''() => {
            const rows = document.querySelectorAll('table tbody tr');
            const analysts = [];
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 7) {
                    analysts.push({
                        firm: cells[0]?.innerText?.trim(),
                        overall_score: cells[1]?.innerText?.trim(),
                        direction_score: cells[2]?.innerText?.trim(),
                        price_score: cells[3]?.innerText?.trim(),
                        rating: cells[4]?.innerText?.trim(),
                        price_target: cells[5]?.innerText?.trim(),
                        date: cells[6]?.innerText?.trim(),
                    });
                }
            });
            return analysts;
        }''')
        result["top_analysts"] = top_analysts
        print(f"    Found {len(top_analysts)} top analysts")
    except Exception as e:
        result["top_analysts_error"] = str(e)
        print(f"    Error: {e}")
    
    # 2. Upgrades & Downgrades (with pagination)
    print("  Scraping Upgrades & Downgrades (with pagination)...")
    try:
        all_upgrades = []
        seen = set()
        
        # Helper to extract table rows
        async def extract_rows():
            return await page.evaluate('''() => {
                const rows = document.querySelectorAll('table tbody tr');
                const items = [];
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 3) {
                        const action = cells[0]?.innerText?.trim();
                        const change = cells[1]?.innerText?.trim();
                        const date = cells[2]?.innerText?.trim();
                        if (action && change && action !== 'Action') {
                            items.push({
                                action: action,
                                change: change,
                                date: date,
                            });
                        }
                    }
                });
                return items;
            }''')
        
        # Extract first page
        first_page = await extract_rows()
        for item in first_page:
            key = (item.get('change', ''), item.get('date', ''))
            if key not in seen:
                seen.add(key)
                all_upgrades.append(item)
        
        # Try to click "More Upgrades & Downgrades" button (pagination)
        max_clicks = 10
        clicked_count = 0
        for i in range(max_clicks):
            try:
                more_button = None
                # Try different selectors for "More" button
                try:
                    more_button = await page.query_selector('button:has-text("More Upgrades")')
                except:
                    pass
                if not more_button:
                    try:
                        more_button = await page.query_selector('button:has-text("More")')
                    except:
                        pass
                
                if more_button:
                    try:
                        is_visible = await more_button.is_visible()
                        is_disabled = await more_button.is_disabled()
                    except:
                        is_visible = False
                        is_disabled = True
                    
                    if is_visible and not is_disabled:
                        print(f"    Clicking 'More' button (page {i+1})...")
                        await more_button.click()
                        await asyncio.sleep(2)
                        clicked_count += 1
                        
                        new_rows = await extract_rows()
                        new_items = 0
                        for item in new_rows:
                            key = (item.get('change', ''), item.get('date', ''))
                            if key not in seen:
                                seen.add(key)
                                all_upgrades.append(item)
                                new_items += 1
                        
                        if new_items == 0:
                            print(f"    No new items, stopping pagination")
                            break
                    else:
                        break
                else:
                    break
            except Exception as e:
                print(f"    Click error (page {i+1}): {e}")
                break
        
        result["upgrades_downgrades"] = all_upgrades
        result["upgrades_page_count"] = clicked_count + 1
        print(f"    Found {len(all_upgrades)} upgrades/downgrades across {clicked_count + 1} pages")
    except Exception as e:
        result["upgrades_downgrades_error"] = str(e)
        print(f"    Error: {e}")
    
    # 3. Analyst Price Targets
    print("  Scraping Price Targets...")
    try:
        price_targets = await page.evaluate('''() => {
            const targets = {};
            const bodyText = document.body.innerText;
            const lowMatch = bodyText.match(/Low\\s*[\\$]?([\\d,\\.]+)/);
            const meanMatch = bodyText.match(/Average\\s*[\\$]?([\\d,\\.]+)/);
            const highMatch = bodyText.match(/High\\s*[\\$]?([\\d,\\.]+)/);
            
            return {
                low: lowMatch ? lowMatch[1] : null,
                mean: meanMatch ? meanMatch[1] : null,
                high: highMatch ? highMatch[1] : null,
            };
        }''')
        result["price_targets"] = price_targets
    except Exception as e:
        result["price_targets_error"] = str(e)
    
    return result


# ============================================================
# DOM Scraping - News
# ============================================================

async def scrape_news(page, ticker: str, limit: int = 10) -> Dict[str, Any]:
    """Scrape recent news from Yahoo Finance"""
    print("Scraping news...")
    
    urls = get_yahoo_urls(ticker)
    try:
        await page.goto(urls["news"], wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"  Navigation timeout: {e}")
    await asyncio.sleep(3)
    
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
    }
    
    try:
        news = await page.evaluate('''(limit) => {
            const items = [];
            const selectors = [
                'li.js-stream-content',
                'div.news-item',
                'a[href*="/news/"]',
                'h3 a[href*="/news/"]',
            ];
            
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    elements.forEach((el, i) => {
                        if (i < limit) {
                            const link = el.tagName === 'A' ? el : el.querySelector('a');
                            const title = el.innerText?.trim().split('\\n')[0];
                            if (title && title.length > 10) {
                                items.push({
                                    title: title,
                                    link: link?.href,
                                });
                            }
                        }
                    });
                    if (items.length > 0) break;
                }
            }
            return items;
        }''', limit)
        
        valid_news = [n for n in news if n.get('title') and n.get('link')]
        result["news"] = valid_news[:limit]
        print(f"    Found {len(valid_news)} news items")
    except Exception as e:
        result["news_error"] = str(e)
        print(f"    Error: {e}")
    
    return result


# ============================================================
# DOM Scraping - Earnings Calls
# ============================================================

async def scrape_earnings_calls(page, ticker: str) -> Dict[str, Any]:
    """Scrape earnings call history from Yahoo Finance"""
    print("Scraping earnings calls...")
    
    urls = get_yahoo_urls(ticker)
    try:
        await page.goto(urls["earnings_calls"], wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"  Navigation timeout: {e}")
    await asyncio.sleep(3)
    
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
        "source": "yahoo_finance_web",
    }
    
    # Extract earnings call data - Get latest URL and fetch transcript content
    latest_url = None
    try:
        # First, find the latest earnings call URL
        url_data = await page.evaluate(r"""() => {
            const links = document.querySelectorAll('a');
            
            for (const link of links) {
                const href = link.getAttribute('href') || '';
                const text = link.innerText || '';
                
                // Match URL pattern
                const match = href.match(/quote\/([A-Z]+)\/earnings\/([A-Z]+)-Q([1-4])-(\d{4})-earnings_call-(\d+)\.html/i);
                if (match) {
                    const parent = link.closest('li') || link.parentElement;
                    const parentText = parent ? parent.innerText : '';
                    const timeMatch = parentText.match(/(\d+\s+(days?|months?|years?)\s+ago|last\s+year)/i);
                    
                    return {
                        quarter: 'Q' + match[3],
                        fiscal_year: match[4],
                        period: 'Q' + match[3] + ' FY' + match[4],
                        time_ago: timeMatch ? timeMatch[0] : 'unknown',
                        url: href.startsWith('http') ? href : 'https://finance.yahoo.com' + href,
                    };
                }
            }
            return null;
        }""")
        
        if url_data:
            latest_url = url_data['url']
            result["earnings_calls"] = [url_data]
            print(f"    Found latest earnings call: {url_data['period']} ({url_data['time_ago']})")
        
    except Exception as e:
        print(f"    Error finding earnings call URL: {e}")
    
    # If we found a URL, visit it and get the transcript content
    if latest_url:
        try:
            print(f"    Fetching transcript from {latest_url}...")
            await page.goto(latest_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)
            
            # Extract transcript content
            transcript_content = await page.evaluate(r"""() => {
                const body = document.body;
                const text = body.innerText;
                
                // Get transcript section - look for content after "earnings call"
                const idx = text.indexOf('earnings call');
                if (idx > 0 && idx < text.length - 100) {
                    return text.substring(idx, Math.min(idx + 50000, text.length));
                }
                
                // Fallback: return last portion
                return text.substring(Math.max(0, text.length - 50000));
            }""")
            
            if transcript_content and len(transcript_content) > 100:
                result["earnings_calls"][0]["transcript"] = transcript_content
                result["earnings_calls"][0]["transcript_length"] = len(transcript_content)
                print(f"    Got transcript: {len(transcript_content)} chars")
            else:
                print(f"    No transcript content found")
                
        except Exception as e:
            print(f"    Error fetching transcript: {e}")
    
    # Try to extract EPS and revenue estimates    # Try to extract EPS and revenue estimates
    try:
        estimates = await page.evaluate('''() => {
            const data = {};
            
            // Look for EPS data
            const epsPatterns = [
                /EPS\\s*([\\$]?[\\d]+\\.[\\d]+)/gi,
                /Earnings\\s*per\\s*Share[\\s:]*([\\$]?[\\d]+\\.[\\d]+)/gi,
            ];
            
            // Look for revenue data
            const revPatterns = [
                /Revenue[\\s:]*\\$?([\\d,]+\\.?[\\d]*\\s*[BMbt])/gi,
                /Sales[\\s:]*\\$?([\\d,]+\\.?[\\d]*\\s*[BMbt])/gi,
            ];
            
            const bodyText = document.body.innerText;
            
            const epsValues = [];
            for (const pattern of epsPatterns) {
                let match;
                while ((match = pattern.exec(bodyText)) !== null) {
                    epsValues.push(match[1]);
                }
            }
            
            const revValues = [];
            for (const pattern of revPatterns) {
                let match;
                while ((match = pattern.exec(bodyText)) !== null) {
                    revValues.push(match[1]);
                }
            }
            
            return {
                eps_estimates: epsValues.slice(0, 10),
                revenue_estimates: revValues.slice(0, 10),
            };
        }''')
        
        result["estimates"] = estimates
    except Exception as e:
        result["estimates_error"] = str(e)
    
    return result


# ============================================================
# DOM Scraping - SEC Filings
# ============================================================

async def scrape_sec_filings(page, ticker: str) -> Dict[str, Any]:
    """Scrape SEC filings from Yahoo Finance"""
    print("Scraping SEC filings...")
    
    urls = get_yahoo_urls(ticker)
    try:
        await page.goto(urls["sec_filings"], wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"  Navigation timeout: {e}")
    await asyncio.sleep(3)
    
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
        "source": "yahoo_finance_web",
    }
    
    # Extract SEC filings - Only recent 10-Q, 10-K, 8-K, ARS, S-8 in past 3 months
    try:
        filings = await page.evaluate('''() => {
            const filings = [];
            const targetFormTypes = ['10-K', '10-Q', '8-K', 'ARS', 'S-8'];
            
            // Calculate 3 months ago
            const now = new Date();
            const threeMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
            
            // Find all links that contain SEC filing info
            const links = document.querySelectorAll('a');
            
            for (const link of links) {
                const href = link.getAttribute('href') || '';
                const text = link.innerText || '';
                
                // Check if this link is a SEC filing link
                // Format: "/sec-filing/TSLA/0001104659-26-048779_1318605"
                if (href.includes('/sec-filing/')) {
                    // Parse the text: "S-8 : Offering Registrations\\nApril 27, 2026"
                    const lines = text.split(/\\r?\\n/);
                    if (lines.length >= 2) {
                        const formLine = lines[0].trim();
                        const dateLine = lines[1].trim();
                        
                        // Check if it's a target form type
                        let formType = null;
                        for (const type of targetFormTypes) {
                            if (formLine.startsWith(type)) {
                                formType = type;
                                break;
                            }
                        }
                        
                        if (formType) {
                            // Parse date
                            const dateMatch = dateLine.match(/^(January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},?\\s+(\\d{4})$/i);
                            
                            if (dateMatch) {
                                const filingDate = new Date(dateLine);
                                
                                // Check if within past 3 months
                                if (filingDate >= threeMonthsAgo) {
                                    const description = formLine.substring(formType.length).replace(/^\\s*[:\\s]+/, '').trim();
                                    
                                    filings.push({
                                        form_type: formType,
                                        description: description || '',
                                        date: dateLine,
                                        url: href.startsWith('http') ? href : 'https://finance.yahoo.com' + href,
                                        source: 'yahoo_finance',
                                    });
                                }
                            }
                        }
                    }
                }
            }
            
            // Remove duplicates
            const seen = new Set();
            return filings.filter(f => {
                const key = f.form_type + f.date;
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            });
        }''')
        
        result["filings"] = filings
        print(f"    Found {len(filings)} SEC filing entries")
        
        # Fallback: extract from text if table is empty
        if len(filings) == 0:
            print("    Trying fallback text extraction...")
            fallback = await page.evaluate('''() => {
                const bodyText = document.body.innerText;
                const filings = [];
                
                // Common SEC form types
                const formTypes = [
                    '10-K', '10-Q', '8-K', 'DEF 14A', 'SC 13G', 'SC 13D',
                    'S-1', 'S-3', 'S-4', 'Form 4', 'Form 3',
                    'Form 144', 'Form 13F', '13F-HR'
                ];
                
                // Look for form type followed by date
                for (const formType of formTypes) {
                    const regex = new RegExp(formType + '[\\\\s\\\\-]+(\\\\d{1,2}[\\\\/]\\\\d{1,2}[\\\\/]\\\\d{2,4})', 'gi');
                    let match;
                    while ((match = regex.exec(bodyText)) !== null) {
                        filings.push({
                            form_type: formType,
                            date: match[1],
                            description: 'Extracted from page text',
                            source: 'text_fallback',
                        });
                    }
                }
                
                return filings.slice(0, 50);
            }''')
            
            if fallback and len(fallback) > 0:
                result["filings_fallback"] = fallback
                print(f"    Fallback found {len(fallback)} entries")
        
    except Exception as e:
        result["filings_error"] = str(e)
        print(f"    Error: {e}")
    
    # Try to get filing links
    try:
        filing_links = await page.evaluate('''() => {
            const links = [];
            const anchors = document.querySelectorAll('a[href*="sec.gov"], a[href*="SEC"]');
            
            anchors.forEach(a => {
                const href = a.href;
                const text = a.innerText?.trim();
                if (href && text && text.length > 0 && text.length < 100) {
                    links.push({
                        form_type: text,
                        url: href,
                    });
                }
            });
            
            return links;
        }''')
        
        if filing_links:
            result["filing_links"] = filing_links
    except Exception as e:
        result["filing_links_error"] = str(e)
    
    return result


# ============================================================
# Main Scraper
# ============================================================

async def scrape_all(ticker: str, include_news: bool = True, include_earnings: bool = True, include_sec: bool = True) -> Dict[str, Any]:
    """Scrape all data from Yahoo Finance"""
    print(f"\n=== Yahoo Finance scrape for {ticker} ===")
    
    if not HAS_PLAYWRIGHT:
        return {"error": "Playwright not installed"}
    
    result = {
        "ticker": ticker,
        "fetch_date": datetime.now().isoformat(),
        "source": "yahoo_finance_web",
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            result["api_detection"] = await detect_api(page, ticker)
            result["analyst"] = await scrape_analyst_data(page, ticker)
            
            if include_news:
                result["news"] = await scrape_news(page, ticker)
            
            if include_earnings:
                result["earnings_calls"] = await scrape_earnings_calls(page, ticker)
            
            if include_sec:
                result["sec_filings"] = await scrape_sec_filings(page, ticker)
            
        finally:
            await browser.close()
    
    print(f"\n=== Scrape complete for {ticker} ===")
    
    return result


# ============================================================
# CLI Entry Point
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python scrap_yahoo_web.py <TICKER> [--no-news] [--no-earnings] [--no-sec]")
        print("  --no-news: Skip news scraping")
        print("  --no-earnings: Skip earnings calls scraping")
        print("  --no-sec: Skip SEC filings scraping")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    include_news = "--no-news" not in sys.argv
    include_earnings = "--no-earnings" not in sys.argv
    include_sec = "--no-sec" not in sys.argv
    
    result = asyncio.run(scrape_all(
        ticker,
        include_news=include_news,
        include_earnings=include_earnings,
        include_sec=include_sec
    ))
    
    output_dir = os.path.join(DEFAULT_OUTPUT_DIR, ticker)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "web_scraped.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nData saved to: {output_path}")
    
    # Display analyst summary
    if result.get("analyst", {}).get("top_analysts"):
        analysts = result["analyst"]["top_analysts"]
        print(f"\nTop Analysts: {len(analysts)}")
        if analysts:
            latest = analysts[0]
            print(f"  Latest: {latest.get('firm')} - {latest.get('rating')} (${latest.get('price_target')}) on {latest.get('date')}")
    
    if result.get("analyst", {}).get("upgrades_downgrades"):
        upgrades = result["analyst"]["upgrades_downgrades"]
        page_count = result["analyst"].get("upgrades_page_count", "?")
        print(f"\nUpgrades/Downgrades: {len(upgrades)} (across {page_count} pages)")
    
    # Display earnings calls summary
    if result.get("earnings_calls", {}).get("earnings_calls"):
        calls = result["earnings_calls"]["earnings_calls"]
        print(f"\nEarnings Calls: {len(calls)} entries")
    
    # Display SEC filings summary
    if result.get("sec_filings", {}).get("filings"):
        filings = result["sec_filings"]["filings"]
        print(f"\nSEC Filings: {len(filings)} entries")


if __name__ == "__main__":
    # Fix Windows encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    main()
