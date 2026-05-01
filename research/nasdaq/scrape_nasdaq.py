#!/usr/bin/env python3
"""
Nasdaq Stock Data Scraper
Scrape news, press releases, institutional holdings, insider activity, and SEC filings.
Uses Chrome Beta + Xvfb + Playwright headed mode.
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


TICKER = None

def make_url(path):
    """Convert relative path to full URL."""
    if path.startswith("http"):
        return path
    return f"https://www.nasdaq.com{path}"


def wait_for_content(page, selector, timeout=15000):
    """Wait for JS content to load."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except:
        return False


def scrape_news(page, limit=20):
    """Scrape news headlines."""
    url = f"https://www.nasdaq.com/market-activity/stocks/{TICKER}/news-headlines"
    page.goto(url, timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    
    if not wait_for_content(page, ".jupiter22-c-article-list__item", timeout=15000):
        return {"count": 0, "items": []}
    
    time.sleep(2)  # Extra settle time for JS
    
    items = []
    article_items = page.query_selector_all(".jupiter22-c-article-list__item")
    
    for item in article_items[:limit]:
        try:
            link_el = item.query_selector("a")
            full_text = item.inner_text().strip()
            
            link = ""
            if link_el:
                href = link_el.get_attribute("href") or ""
                link = make_url(href)
            
            # Parse: "STOCKS\nOndas Sees Massive Backlog Jump... \n2 days ago • Zacks"
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            
            category = lines[0] if lines else ""
            time_ago = ""
            source = ""
            title = full_text  # fallback
            
            # Extract time_ago and source from text
            time_match = re.search(r'(\d+\s+(?:day|hour|week|month)s?\s+ago)', full_text, re.IGNORECASE)
            if time_match:
                time_ago = time_match.group(1)
            
            source_match = re.search(r'•\s*([^\n•]+)$', full_text)
            if source_match:
                source = source_match.group(1).strip()
            
            # Title is usually the middle content
            for line in lines[1:]:
                if 'ago' not in line.lower() and len(line) > 20:
                    title = line
                    break
            
            # Clean title
            title = re.sub(r'\d+\s+(?:day|hour|week|month)s?\s+ago\s*•.*', '', title).strip()
            
            items.append({
                "title": title,
                "category": category,
                "source": source,
                "time_ago": time_ago,
                "url": link
            })
        except Exception as e:
            pass
    
    return {"count": len(items), "items": items}


def scrape_press_releases(page, limit=20):
    """Scrape press releases."""
    url = f"https://www.nasdaq.com/market-activity/stocks/{TICKER}/press-releases"
    page.goto(url, timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    
    if not wait_for_content(page, ".jupiter22-c-article-list__item.press-release", timeout=15000):
        return {"count": 0, "items": []}
    
    time.sleep(2)
    
    items = []
    pr_items = page.query_selector_all(".jupiter22-c-article-list__item.press-release")
    
    for item in pr_items[:limit]:
        try:
            link_el = item.query_selector("a")
            full_text = item.inner_text().strip()
            
            link = ""
            if link_el:
                href = link_el.get_attribute("href") or ""
                link = make_url(href)
            
            # Parse: "The Camera Is the New Sensor... \n1 day ago"
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            
            title = lines[0] if lines else full_text
            date = ""
            
            date_match = re.search(r'(\d+\s+(?:day|hour|week|month|min)s?\s+ago)', full_text, re.IGNORECASE)
            if date_match:
                date = date_match.group(1)
            
            # Clean title
            title = re.sub(r'\d+\s+(?:day|hour|week|month|min)s?\s+ago', '', title).strip()
            
            items.append({
                "title": title,
                "date": date,
                "url": link
            })
        except Exception as e:
            pass
    
    return {"count": len(items), "items": items}


def scrape_institutional_holdings(page):
    """Scrape institutional holdings."""
    url = f"https://www.nasdaq.com/market-activity/stocks/{TICKER}/institutional-holdings"
    page.goto(url, timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    
    if not wait_for_content(page, ".jupiter22-institutional-holdings", timeout=15000):
        return {"error": "Content did not load"}
    
    time.sleep(3)  # Tables may need extra time
    
    data = {}
    
    # Ownership summary
    summary = page.query_selector(".jupiter22-institutional-holdings__ownership-summary")
    if summary:
        data["ownership_summary"] = summary.inner_text()[:500]
    
    # Holders count
    count_el = page.query_selector(".institutional-holders-count")
    if count_el:
        data["holders_count"] = count_el.inner_text().strip()
    
    # Top holders table
    holder_rows = []
    table = page.query_selector(".jupiter22-institutional-holdings__institutional-holders-table tbody tr")
    if table:
        rows = page.query_selector_all(".jupiter22-institutional-holdings__institutional-holders-table tbody tr")
        for row in rows[:25]:
            cells = row.query_selector_all("td")
            if len(cells) >= 4:
                holder_rows.append({
                    "holder": cells[0].inner_text().strip(),
                    "shares": cells[1].inner_text().strip(),
                    "value": cells[2].inner_text().strip(),
                    "percentage": cells[3].inner_text().strip(),
                })
    data["top_holders"] = holder_rows
    
    # Active positions
    active_positions = []
    active_table_selector = ".jupiter22-institutional-holdings__active-positions-table tbody tr"
    if page.query_selector(active_table_selector):
        rows = page.query_selector_all(active_table_selector)
        for row in rows[:15]:
            cells = row.query_selector_all("td")
            if len(cells) >= 4:
                active_positions.append({
                    "holder": cells[0].inner_text().strip(),
                    "action": cells[1].inner_text().strip(),
                    "shares": cells[2].inner_text().strip(),
                    "date": cells[3].inner_text().strip(),
                })
    data["active_positions"] = active_positions
    
    return data


def scrape_insider_activity(page):
    """Scrape insider activity."""
    url = f"https://www.nasdaq.com/market-activity/stocks/{TICKER}/insider-activity"
    page.goto(url, timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    
    if not wait_for_content(page, ".jupiter22-insider-activity", timeout=15000):
        return {"error": "Content did not load"}
    
    time.sleep(3)  # Tables need extra time
    
    data = {}
    
    # Summary
    summary = page.query_selector(".insider-trades-text")
    if summary:
        data["summary"] = summary.inner_text()[:500]
    
    # Transactions table
    transactions = []
    tx_selector = ".insider-transactions-table tbody tr"
    if page.query_selector(tx_selector):
        rows = page.query_selector_all(tx_selector)
        for row in rows[:25]:
            cells = row.query_selector_all("td")
            if len(cells) >= 6:
                transactions.append({
                    "insider": cells[0].inner_text().strip(),
                    "action": cells[1].inner_text().strip(),
                    "type": cells[2].inner_text().strip(),
                    "shares": cells[3].inner_text().strip(),
                    "price": cells[4].inner_text().strip(),
                    "date": cells[5].inner_text().strip(),
                })
    data["transactions"] = transactions
    
    # Shares traded
    shares_traded = []
    traded_selector = ".insider-shares-traded-table tbody tr"
    if page.query_selector(traded_selector):
        rows = page.query_selector_all(traded_selector)
        for row in rows[:15]:
            cells = row.query_selector_all("td")
            if len(cells) >= 3:
                shares_traded.append({
                    "insider": cells[0].inner_text().strip(),
                    "shares_traded": cells[1].inner_text().strip(),
                    "date": cells[2].inner_text().strip(),
                })
    data["shares_traded"] = shares_traded
    
    return data


def scrape_sec_filings(page, page_num=1, rows_per_page=50):
    """Scrape SEC filings."""
    url = f"https://www.nasdaq.com/market-activity/stocks/{TICKER}/sec-filings?page={page_num}&rows_per_page={rows_per_page}"
    page.goto(url, timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    
    if not wait_for_content(page, ".jupiter22-c-sec-filings-table", timeout=15000):
        return {"count": 0, "filings": [], "error": "Content did not load"}
    
    time.sleep(2)
    
    filings = []
    table = page.query_selector(".jupiter22-c-sec-filings-table")
    
    if table:
        rows = page.query_selector_all(".jupiter22-c-sec-filings-table tbody tr")
        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 4:
                # Extract document links
                doc_links = []
                for a in cells[4].query_selector_all("a"):
                    href = a.get_attribute("href") or ""
                    if href:
                        doc_links.append(href)
                
                filings.append({
                    "company": cells[0].inner_text().strip(),
                    "form_type": cells[1].inner_text().strip(),
                    "filing_date": cells[2].inner_text().strip(),
                    "acceptance_date": cells[3].inner_text().strip(),
                    "documents": doc_links
                })
    
    return {"count": len(filings), "filings": filings}


def scrape_article_detail(page, url):
    """Navigate to a news/press-release URL and extract full content."""
    full_url = make_url(url)
    page.goto(full_url, timeout=30000)
    page.wait_for_load_state("domcontentloaded")
    
    time.sleep(3)  # Wait for article to fully render
    
    content = ""
    title = ""
    published_date = ""
    
    try:
        page.wait_for_selector("article", timeout=10000)
    except:
        pass
    
    article = page.query_selector("article")
    if article:
        content = article.inner_text()[:5000]
    
    # Try to get title from h1
    h1 = page.query_selector("h1")
    if h1:
        title = h1.inner_text().strip()
    
    # Try to get published date
    date_selectors = [
        "[class*='publish']",
        "[class*='date']",
        "time",
        "[class*='timestamp']"
    ]
    for sel in date_selectors:
        el = page.query_selector(sel)
        if el:
            text = el.inner_text().strip()
            if text and len(text) > 5:
                published_date = text
                break
    
    return {
        "url": full_url,
        "title": title,
        "published_date": published_date,
        "content": content
    }


def scrape_all(ticker, include_details=False, output_dir=None):
    """Scrape all Nasdaq data for a ticker."""
    global TICKER
    TICKER = ticker.upper()
    
    results = {
        "ticker": TICKER,
        "fetch_date": "2026-05-02",  # Would use datetime.now().isoformat()
        "source": "nasdaq.com"
    }
    
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
        
        # Scrape each section
        print("Scraping news...")
        results["news"] = scrape_news(page, limit=20)
        
        print("Scraping press releases...")
        time.sleep(2)
        results["press_releases"] = scrape_press_releases(page, limit=20)
        
        print("Scraping institutional holdings...")
        time.sleep(2)
        results["institutional_holdings"] = scrape_institutional_holdings(page)
        
        print("Scraping insider activity...")
        time.sleep(2)
        results["insider_activity"] = scrape_insider_activity(page)
        
        print("Scraping SEC filings...")
        time.sleep(2)
        results["sec_filings"] = scrape_sec_filings(page)
        
        # Optionally follow first few items to get full content
        if include_details:
            print("Fetching article details...")
            
            # News details
            if results["news"].get("items"):
                news_details = []
                for item in results["news"]["items"][:3]:
                    time.sleep(2)
                    detail = scrape_article_detail(page, item["url"])
                    news_details.append(detail)
                results["news"]["details"] = news_details
            
            # Press release details
            if results["press_releases"].get("items"):
                pr_details = []
                for item in results["press_releases"]["items"][:3]:
                    time.sleep(2)
                    detail = scrape_article_detail(page, item["url"])
                    pr_details.append(detail)
                results["press_releases"]["details"] = pr_details
        
        browser.close()
    
    # Save to file
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{TICKER}_nasdaq.json")
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Saved to {output_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Scrape Nasdaq stock data")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., ONDS)")
    parser.add_argument("--output", help="Output directory or file path (.json)")
    parser.add_argument("--news", action="store_true", help="Scrape news only")
    parser.add_argument("--press-releases", action="store_true", help="Scrape press releases only")
    parser.add_argument("--institutional", action="store_true", help="Scrape institutional holdings only")
    parser.add_argument("--insider", action="store_true", help="Scrape insider activity only")
    parser.add_argument("--sec-filings", action="store_true", help="Scrape SEC filings only")
    parser.add_argument("--include-details", action="store_true", help="Fetch full article/press-release content")
    parser.add_argument("--full", action="store_true", help="Scrape all sections")
    
    args = parser.parse_args()
    
    ticker = args.ticker.upper()
    
    if args.full or not any([args.news, args.press_releases, args.institutional, args.insider, args.sec_filings]):
        # Scrape everything
        output_dir = os.path.dirname(args.output) if args.output and args.output.endswith('.json') else args.output
        result = scrape_all(ticker, include_details=args.include_details, output_dir=output_dir)
    else:
        # Scrape specific sections
        result = {"ticker": ticker, "fetch_date": "2026-05-02", "source": "nasdaq.com"}
        
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
            
            if args.news:
                result["news"] = scrape_news(page)
            if args.press_releases:
                result["press_releases"] = scrape_press_releases(page)
            if args.institutional:
                result["institutional_holdings"] = scrape_institutional_holdings(page)
            if args.insider:
                result["insider_activity"] = scrape_insider_activity(page)
            if args.sec_filings:
                result["sec_filings"] = scrape_sec_filings(page)
            
            browser.close()
    
    print(json.dumps(result, indent=2))
    
    # Save if output specified
    if args.output:
        output_dir = os.path.dirname(args.output) if args.output else None
        output_file = args.output if args.output.endswith('.json') else os.path.join(args.output, f"{ticker}_nasdaq.json")
        if output_dir and not args.output.endswith('.json'):
            os.makedirs(output_dir, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
