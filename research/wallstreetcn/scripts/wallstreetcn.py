#!/usr/bin/env python3
"""WallStreetCN 快讯/資訊 fetcher — CLI tool."""

import argparse
import json
import requests
from datetime import datetime, timezone, timedelta

API_BASE = "https://api-one.wallstcn.com/apiv1/content"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://wallstreetcn.com/live",
}

VALID_CHANNELS = [
    "global-channel",
    "a-stock-channel",
    "hk-stock-channel",
    "us-stock-channel",
    "forex-channel",
    "commodity-channel",
    "bond-channel",
]


def ts_to_hktime(ts: int) -> str:
    """Convert unix timestamp to HK time string."""
    dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
    return dt.strftime("%m-%d %H:%M")


def fetch_lives(channel: str, limit: int, cursor: str = None) -> dict:
    """Fetch live news (快讯)."""
    params = {"channel": channel, "limit": limit}
    if cursor:
        params["cursor"] = cursor
    resp = requests.get(f"{API_BASE}/lives", params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_articles(channel: str, limit: int) -> dict:
    """Fetch articles (資訊)."""
    params = {"channel": channel, "limit": limit}
    resp = requests.get(f"{API_BASE}/articles", params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def display_lives(data: dict) -> None:
    """Pretty-print live news items."""
    items = data.get("data", {}).get("items", [])
    if not items:
        print("No items found.")
        return
    for item in items:
        time_str = ts_to_hktime(item["display_time"])
        text = item.get("content_text", "").strip()
        author = item.get("author", {}).get("display_name", "")
        url = item.get("uri", "")
        prefix = f"[{time_str}]"
        if author:
            prefix += f" ({author})"
        print(f"{prefix} {text}")
        if url:
            print(f"  🔗 {url}")
        print()


def display_articles(data: dict) -> None:
    """Pretty-print articles."""
    items = data.get("data", {}).get("items", [])
    if not items:
        print("No items found.")
        return
    for item in items:
        time_str = ts_to_hktime(item["display_time"])
        title = item.get("title", "無標題")
        source = item.get("source_name", "")
        summary = item.get("content_short", "").strip()
        url = item.get("uri", "")
        print(f"[{time_str}] {title}")
        if source:
            print(f"  📰 來源: {source}")
        if summary:
            print(f"  {summary[:200]}")
        if url:
            print(f"  🔗 {url}")
        print()


def main():
    parser = argparse.ArgumentParser(description="WallStreetCN 快訊/資訊 fetcher")
    parser.add_argument(
        "--type", choices=["lives", "articles"], default="lives",
        help="Content type: lives (快讯) or articles (資訊)"
    )
    parser.add_argument(
        "--channel", choices=VALID_CHANNELS, default="global-channel",
        help="News channel"
    )
    parser.add_argument(
        "--limit", type=int, default=10,
        help="Number of items to fetch (max ~50)"
    )
    parser.add_argument(
        "--cursor", type=str, default=None,
        help="Pagination cursor (from previous response next_cursor)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output raw JSON instead of formatted text"
    )

    args = parser.parse_args()

    if args.type == "lives":
        data = fetch_lives(args.channel, args.limit, args.cursor)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            display_lives(data)
            next_cursor = data.get("data", {}).get("next_cursor")
            if next_cursor:
                print(f"--- next_cursor: {next_cursor} (use --cursor for more) ---")
    else:
        data = fetch_articles(args.channel, args.limit)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            display_articles(data)


if __name__ == "__main__":
    main()
