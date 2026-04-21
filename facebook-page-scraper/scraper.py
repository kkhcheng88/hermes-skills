#!/usr/bin/env python3
"""
Facebook Page Post Scraper
Scrapes public page posts using Playwright with optional cookie authentication.

Usage:
    python3 scraper.py --page <page_name_or_url> [--cookies cookies.json] [--limit N] [--since YYYY-MM-DD]
    python3 scraper.py --config config.json

Output: JSON array of posts to stdout
"""

import argparse
import json
import os
import re
import sys
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_cookies(cookies_path: str) -> list:
    """Load cookies from JSON file (Netscape or JSON array format)."""
    with open(cookies_path, 'r') as f:
        content = f.read().strip()

    # Try JSON array format first
    try:
        cookies = json.loads(content)
        if isinstance(cookies, list):
            return cookies
    except json.JSONDecodeError:
        pass

    # Try Netscape format
    cookies = []
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 7:
            cookies.append({
                "domain": parts[0],
                "flag": parts[1] == "TRUE",
                "path": parts[2],
                "secure": parts[3] == "TRUE",
                "expires": int(parts[4]) if parts[4] != "0" else 0,
                "name": parts[5],
                "value": parts[6],
            })
    return cookies


def post_id(post_url: str) -> str:
    """Generate a stable ID for dedup."""
    return hashlib.md5(post_url.encode()).hexdigest()[:12]


def scrape_page(page_name: str, cookies_path: str = None, limit: int = 20,
                since: str = None, headless: bool = True) -> list:
    """
    Scrape posts from a Facebook page.
    
    Returns list of dicts: {id, page, text, time, url, images}
    """
    from playwright.sync_api import sync_playwright

    # Normalize page name
    page_name = page_name.replace("https://www.facebook.com/", "").replace("https://facebook.com/", "").strip("/")
    url = f"https://www.facebook.com/{page_name}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )

        # Load cookies if available
        if cookies_path and os.path.exists(cookies_path):
            cookies = load_cookies(cookies_path)
            context.add_cookies(cookies)
            print(f"Loaded {len(cookies)} cookies", file=sys.stderr)

        page = context.new_page()
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        time.sleep(5)

        # Dismiss any login modals
        try:
            close_btns = page.query_selector_all('[aria-label="Close"]')
            for btn in close_btns:
                btn.click()
                time.sleep(0.5)
        except:
            pass

        posts = []
        seen_texts = set()

        for scroll_round in range(10):
            # Extract visible post content
            body_text = page.inner_text('body')
            lines = body_text.split('\n')

            # Group lines into potential posts
            current_post = []
            for line in lines:
                line = line.strip()
                if not line:
                    if current_post:
                        text = ' '.join(current_post)
                        if len(text) > 30 and text not in seen_texts:
                            seen_texts.add(text)
                            posts.append({
                                "id": post_id(text[:100]),
                                "page": page_name,
                                "text": text,
                                "scraped_at": datetime.now().isoformat(),
                            })
                        current_post = []
                else:
                    current_post.append(line)

            if len(posts) >= limit:
                break

            # Scroll to load more
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(2)

            # Check if "See More" or login wall appeared
            if "log in" in page.inner_text('body').lower()[:500]:
                print("Hit login wall", file=sys.stderr)
                break

        browser.close()

    # Deduplicate and limit
    unique_posts = []
    seen = set()
    for post in posts:
        if post["id"] not in seen:
            seen.add(post["id"])
            unique_posts.append(post)

    return unique_posts[:limit]


def load_state(page_name: str) -> dict:
    """Load previous scrape state for dedup."""
    state_file = DATA_DIR / f"{page_name.replace('/', '_')}_state.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {"seen_ids": [], "last_scraped": None}


def save_state(page_name: str, state: dict):
    """Save scrape state."""
    state_file = DATA_DIR / f"{page_name.replace('/', '_')}_state.json"
    state["last_scraped"] = datetime.now().isoformat()
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Facebook Page Post Scraper")
    parser.add_argument("--page", required=True, help="Page name or URL (e.g., 'wsj' or 'https://facebook.com/wsj')")
    parser.add_argument("--cookies", default=None, help="Path to cookies JSON file")
    parser.add_argument("--limit", type=int, default=20, help="Max posts to scrape")
    parser.add_argument("--since", default=None, help="Only posts since YYYY-MM-DD")
    parser.add_argument("--new-only", action="store_true", help="Only return posts not seen before")
    args = parser.parse_args()

    # Default cookies path
    if not args.cookies:
        default_cookies = SKILL_DIR / "cookies.json"
        if default_cookies.exists():
            args.cookies = str(default_cookies)

    # Load state for dedup
    state = load_state(args.page) if args.new_only else None

    # Scrape
    posts = scrape_page(
        page_name=args.page,
        cookies_path=args.cookies,
        limit=args.limit,
        since=args.since,
    )

    # Filter new posts if requested
    if state and state["seen_ids"]:
        posts = [p for p in posts if p["id"] not in state["seen_ids"]]

    # Update state
    if state:
        state["seen_ids"] = list(set(state["seen_ids"] + [p["id"] for p in posts]))
        save_state(args.page, state)

    # Output
    print(json.dumps(posts, ensure_ascii=False, indent=2))
    print(f"\n# Scraped {len(posts)} posts from {args.page}", file=sys.stderr)


if __name__ == "__main__":
    main()
