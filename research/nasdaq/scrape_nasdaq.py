#!/usr/bin/env python3
"""
Nasdaq Stock Data Scraper v2
Scrapes news, press releases, institutional holdings, insider activity, and SEC filings.

Data Sources:
- News: https://www.nasdaq.com/api/news/topic/articlebysymbol (REST API, no browser needed)
- Press Releases: https://www.nasdaq.com/api/news/topic/press_release (REST API, no browser needed)
- Institutional Holdings: Playwright with shadow DOM extraction
- Insider Activity: Playwright with shadow DOM extraction
- SEC Filings: https://api.nasdaq.com/api/company/{TICKER}/sec-filings (REST API)

Usage:
    python3 scrape_nasdaq.py ONDS                          # All data
    python3 scrape_nasdaq.py ONDS --news                    # News only
    python3 scrape_nasdaq.py ONDS --press-releases           # Press releases only
    python3 scrape_nasdaq.py ONDS --institutional            # Institutional holdings
    python3 scrape_nasdaq.py ONDS --insider                 # Insider activity
    python3 scrape_nasdaq.py ONDS --sec-filings             # SEC filings
    python3 scrape_nasdaq.py ONDS --output data/ONDS        # Save to directory
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("WARNING: playwright not installed. Run: pip install playwright && playwright install chromium")
    print("Browser-based sections (institutional/insider) will be skipped.")
    sync_playwright = None


# ─────────────────────────────────────────────────────────────
# NEWS — REST API
# ─────────────────────────────────────────────────────────────
def scrape_news(ticker, limit=50):
    """Fetch news headlines via Nasdaq REST API."""
    url = f"https://www.nasdaq.com/api/news/topic/articlebysymbol?q={ticker}|STOCKS&offset=0&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {"count": 0, "items": [], "error": str(e)}
    
    rows = data.get("data", {}).get("rows", [])
    items = []
    for row in rows[:limit]:
        items.append({
            "id": row.get("id"),
            "title": row.get("title", ""),
            "description": row.get("description", "")[:300],
            "publisher": row.get("publisher", ""),
            "ago": row.get("ago", ""),
            "created": row.get("created", ""),
            "url": f"https://www.nasdaq.com{row.get('url', '')}",
            "related_symbols": row.get("related_symbols", []),
        })
    
    return {"count": len(items), "items": items}


# ─────────────────────────────────────────────────────────────
# PRESS RELEASES — REST API
# ─────────────────────────────────────────────────────────────
def scrape_press_releases(ticker, limit=50):
    """Fetch press releases via Nasdaq REST API."""
    url = f"https://www.nasdaq.com/api/news/topic/press_release?q=symbol:{ticker.lower()}|assetclass:stocks&limit={limit}&offset=0"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {"count": 0, "items": [], "error": str(e)}
    
    rows = data.get("data", {}).get("rows", [])
    items = []
    for row in rows[:limit]:
        items.append({
            "id": row.get("id"),
            "title": row.get("title", ""),
            "ago": row.get("ago", ""),
            "created": row.get("created", ""),
            "url": f"https://www.nasdaq.com{row.get('url', '')}",
            "related_symbols": row.get("related_symbols", []),
        })
    
    return {"count": len(items), "items": items}


# ─────────────────────────────────────────────────────────────
# INSTITUTIONAL HOLDINGS — Playwright + shadow DOM
# ─────────────────────────────────────────────────────────────
def scrape_institutional_holdings(ticker):
    """Fetch institutional holdings via Playwright (shadow DOM extraction)."""
    if not sync_playwright:
        return {"error": "playwright not installed"}
    
    url = f"https://www.nasdaq.com/market-activity/stocks/{ticker}/institutional-holdings"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            executable_path="/usr/bin/google-chrome-beta",
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url, timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        
        # Wait for nsdq-table elements in shadow DOM
        try:
            page.wait_for_function(
                "document.querySelectorAll('nsdq-table').length > 0",
                timeout=15000
            )
        except:
            pass
        
        time.sleep(6)  # Allow JS to fully populate shadow DOMs
        
        # Extract from all nsdq-table shadow DOMs
        result = page.evaluate("""
            () => {
                const results = {};
                const nsdqTables = document.querySelectorAll('nsdq-table');
                
                nsdqTables.forEach((table, idx) => {
                    const shadow = table.shadowRoot;
                    if (!shadow) return;
                    
                    const headerCells = shadow.querySelectorAll('.table-header-cell');
                    const headers = Array.from(headerCells).map(c => c.textContent.trim());
                    
                    const rows = shadow.querySelectorAll('.table-row[data-row-index]');
                    const rowData = Array.from(rows).map(row => {
                        const cells = row.querySelectorAll('[part="table-cell"]');
                        return Array.from(cells).map(c => c.textContent.trim());
                    });
                    
                    const container = table.closest('[class*="institutional"]');
                    const containerClass = container ? container.className : 'unknown';
                    
                    results[idx] = { headers, rowData, rowCount: rows.length, containerClass };
                });
                
                return results;
            }
        """)
        
        browser.close()
    
    # Parse results into structured format
    parsed = {}
    for idx, table_data in result.items():
        cls = table_data.get("containerClass", "")
        headers = table_data.get("headers", [])
        rows = table_data.get("rowData", [])
        
        if "active-positions" in cls:
            parsed["active_positions"] = {
                "headers": headers,
                "rows": rows
            }
        elif "institutional-holders" in cls:
            parsed["top_holders"] = {
                "headers": headers,
                "rows": rows[:10]  # Top 10
            }
        elif "ownership-summary" in cls:
            parsed["ownership_summary"] = {
                "headers": headers,
                "rows": rows
            }
        else:
            parsed[f"table_{idx}"] = {
                "headers": headers,
                "rows": rows,
                "containerClass": cls
            }
    
    return parsed


# ─────────────────────────────────────────────────────────────
# INSIDER ACTIVITY — Playwright + shadow DOM
# ─────────────────────────────────────────────────────────────
def scrape_insider_activity(ticker):
    """Fetch insider activity via Playwright (shadow DOM extraction)."""
    if not sync_playwright:
        return {"error": "playwright not installed"}
    
    url = f"https://www.nasdaq.com/market-activity/stocks/{ticker}/insider-activity"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            executable_path="/usr/bin/google-chrome-beta",
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"]
        )
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url, timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        
        try:
            page.wait_for_function(
                "document.querySelectorAll('nsdq-table').length > 0",
                timeout=15000
            )
        except:
            pass
        
        time.sleep(6)
        
        result = page.evaluate("""
            () => {
                const results = {};
                const nsdqTables = document.querySelectorAll('nsdq-table');
                
                nsdqTables.forEach((table, idx) => {
                    const shadow = table.shadowRoot;
                    if (!shadow) return;
                    
                    const headerCells = shadow.querySelectorAll('.table-header-cell');
                    const headers = Array.from(headerCells).map(c => c.textContent.trim());
                    
                    const rows = shadow.querySelectorAll('.table-row[data-row-index]');
                    const rowData = Array.from(rows).map(row => {
                        const cells = row.querySelectorAll('[part="table-cell"]');
                        return Array.from(cells).map(c => c.textContent.trim());
                    });
                    
                    const container = table.closest('[class*="insider"]');
                    const containerClass = container ? container.className : 'unknown';
                    
                    results[idx] = { headers, rowData, rowCount: rows.length, containerClass };
                });
                
                return results;
            }
        """)
        
        browser.close()
    
    # Parse into structured format
    parsed = {}
    for idx, table_data in result.items():
        cls = table_data.get("containerClass", "")
        headers = table_data.get("headers", [])
        rows = table_data.get("rowData", [])
        
        if "shares-traded-table" in cls:
            parsed["shares_traded"] = {
                "headers": headers,
                "rows": rows
            }
        elif "transactions-table" in cls:
            parsed["top_trades"] = {
                "headers": headers,
                "rows": rows[:10]  # Top 10
            }
        elif "trades-table" in cls:
            parsed["insider_trades_summary"] = {
                "headers": headers,
                "rows": rows
            }
        else:
            parsed[f"table_{idx}"] = {
                "headers": headers,
                "rows": rows,
                "containerClass": cls
            }
    
    return parsed


# ─────────────────────────────────────────────────────────────
# SEC FILINGS — REST API
# ─────────────────────────────────────────────────────────────
def scrape_sec_filings(ticker, limit=50):
    """Fetch SEC filings via Nasdaq REST API."""
    url = f"https://api.nasdaq.com/api/company/{ticker}/sec-filings?limit={limit}&sortColumn=filed&sortOrder=desc&IsQuoteMedia=true"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {"count": 0, "filings": [], "error": str(e)}
    
    rows = data.get("data", {}).get("rows", [])
    filings = []
    latest_10k = None
    latest_10q = None
    
    for row in rows:
        view = row.get("view", {})
        form_type = row.get("formType", "")
        filed_date = row.get("filed", "")
        period = row.get("period", "")
        
        filing_entry = {
            "form_type": form_type,
            "filed_date": filed_date,
            "period": period,
            "html_link": view.get("htmlLink", ""),
            "doc_link": view.get("docLink", ""),
            "pdf_link": view.get("pdfLink", ""),
            "xbrl_link": view.get("xbrLink", ""),
            "xls_link": view.get("xlsLink", ""),
        }
        filings.append(filing_entry)
        
        # Track latest 10-K and 10-Q
        if form_type == "10-K" and not latest_10k:
            latest_10k = filing_entry
        elif form_type == "10-Q" and not latest_10q:
            latest_10q = filing_entry
    
    return {
        "count": len(filings),
        "filings": filings,
        "latest_10k": latest_10k,
        "latest_10q": latest_10q,
    }


# ─────────────────────────────────────────────────────────────
# FULL SCRAPE
# ─────────────────────────────────────────────────────────────
def scrape_all(ticker, output_dir=None):
    """Scrape all Nasdaq data for a ticker."""
    ticker = ticker.upper()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    results = {
        "ticker": ticker,
        "fetch_timestamp": timestamp,
        "source": "nasdaq.com"
    }
    
    print(f"Fetching news for {ticker}...")
    results["news"] = scrape_news(ticker, limit=50)
    print(f"  -> {results['news']['count']} news items")
    
    print(f"Fetching press releases for {ticker}...")
    results["press_releases"] = scrape_press_releases(ticker, limit=50)
    print(f"  -> {results['press_releases']['count']} press releases")
    
    print(f"Fetching institutional holdings for {ticker}...")
    results["institutional_holdings"] = scrape_institutional_holdings(ticker)
    print(f"  -> {len(results['institutional_holdings'])} tables")
    
    print(f"Fetching insider activity for {ticker}...")
    results["insider_activity"] = scrape_insider_activity(ticker)
    print(f"  -> {len(results['insider_activity'])} tables")
    
    print(f"Fetching SEC filings for {ticker}...")
    results["sec_filings"] = scrape_sec_filings(ticker, limit=50)
    print(f"  -> {results['sec_filings']['count']} filings")
    if results["sec_filings"].get("latest_10k"):
        print(f"  -> Latest 10-K: {results['sec_filings']['latest_10k']['filed_date']}")
    if results["sec_filings"].get("latest_10q"):
        print(f"  -> Latest 10-Q: {results['sec_filings']['latest_10q']['filed_date']}")
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{ticker}_nasdaq_v2.json")
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to {out_path}")
    
    return results


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Scrape Nasdaq stock data v2")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., ONDS)")
    parser.add_argument("--output", "-o", help="Output directory or file path")
    parser.add_argument("--news", action="store_true", help="News only")
    parser.add_argument("--press-releases", action="store_true", help="Press releases only")
    parser.add_argument("--institutional", action="store_true", help="Institutional holdings only")
    parser.add_argument("--insider", action="store_true", help="Insider activity only")
    parser.add_argument("--sec-filings", action="store_true", help="SEC filings only")
    parser.add_argument("--all", action="store_true", help="All sections (default)")
    
    args = parser.parse_args()
    ticker = args.ticker.upper()
    
    sections_only = args.news or args.press_releases or args.institutional or args.insider or args.sec_filings
    
    if not sections_only or args.all:
        result = scrape_all(ticker, output_dir=args.output)
    else:
        result = {"ticker": ticker, "fetch_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "source": "nasdaq.com"}
        
        if args.news:
            result["news"] = scrape_news(ticker, limit=50)
        if args.press_releases:
            result["press_releases"] = scrape_press_releases(ticker, limit=50)
        if args.institutional:
            result["institutional_holdings"] = scrape_institutional_holdings(ticker)
        if args.insider:
            result["insider_activity"] = scrape_insider_activity(ticker)
        if args.sec_filings:
            result["sec_filings"] = scrape_sec_filings(ticker, limit=50)
        
        if args.output:
            out_path = args.output if args.output.endswith('.json') else os.path.join(args.output, f"{ticker}_nasdaq_v2.json")
            os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Saved to {out_path}")
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
