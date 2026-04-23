#!/usr/bin/env python3
"""
Discord KOL — Search the knowledge base.

Designed as a Python module for LLM use. Import and call directly:

    from discord_search import search_knowledge
    
    # By stock ticker
    results = search_knowledge(stocks=["TSLA"], days=30)
    
    # By keyword
    results = search_knowledge(query="美联储", days=60)
    
    # By author
    results = search_knowledge(author="皇者顺", days=7)
    
    # Combined
    results = search_knowledge(stocks=["NVDA"], query="业绩", days=90)

Each result: {id, source, channel, author, timestamp, content, stocks}
Returns max `limit` results, sorted newest first.
"""

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional

SKILL_DIR = Path(__file__).parent.parent
KB_DIR = SKILL_DIR / "knowledge"
CST = timezone(timedelta(hours=8))


def _load_all_kb() -> list:
    """Load all knowledge base files."""
    all_entries = []
    if not KB_DIR.exists():
        return all_entries
    for f in KB_DIR.glob("*.json"):
        channel_name = f.stem
        with open(f, 'r', encoding='utf-8') as fh:
            entries = json.load(fh)
            for e in entries:
                e['channel'] = channel_name
            all_entries.extend(entries)
    return all_entries


def _load_kb(channel: str) -> list:
    """Load a specific channel's KB."""
    kb_path = KB_DIR / f"{channel}.json"
    if not kb_path.exists():
        return []
    with open(kb_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)
        for e in entries:
            e['channel'] = channel
        return entries


def search_knowledge(
    channel: str = None,
    query: str = None,
    stocks: List[str] = None,
    author: str = None,
    days: int = None,
    limit: int = 20,
) -> List[dict]:
    """
    Search KOL knowledge base.
    
    Args:
        channel: Channel name (None = search all channels)
        query: Text to search in message content (case-insensitive)
        stocks: List of stock tickers to filter by (e.g. ["TSLA", "NVDA"])
        author: Author name substring match
        days: Only include messages from last N days
        limit: Max results to return
    
    Returns:
        List of matching entries, newest first.
    """
    entries = _load_kb(channel) if channel else _load_all_kb()
    
    # Date cutoff
    cutoff = None
    if days:
        cutoff_dt = datetime.now(CST) - timedelta(days=days)
        cutoff = cutoff_dt.isoformat()
    
    results = []
    stocks_upper = set(s.upper() for s in stocks) if stocks else None
    
    for entry in entries:
        # Date filter
        if cutoff:
            ts = entry.get('timestamp', '')
            if ts and ts < cutoff:
                continue
        
        # Author filter
        if author:
            entry_author = entry.get('author', '').lower()
            if author.lower() not in entry_author:
                continue
        
        # Stock filter
        if stocks_upper:
            entry_stocks = set(s.upper() for s in entry.get('stocks', []))
            if not entry_stocks.intersection(stocks_upper):
                continue
        
        # Text query filter
        if query:
            content = entry.get('content', '').lower()
            if query.lower() not in content:
                continue
        
        results.append(entry)
    
    results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return results[:limit]


def format_for_report(results: List[dict]) -> str:
    """Format search results into a readable block for report inclusion."""
    if not results:
        return ""
    
    lines = []
    for r in results:
        ts = r.get('timestamp', '')[:10]
        author = r.get('author', '?')
        content = r.get('content', '')[:300]
        stocks = ', '.join(r.get('stocks', []))
        
        line = f"[{ts}] {author}"
        if stocks:
            line += f" ({stocks})"
        line += f"\n  {content}"
        lines.append(line)
    
    return "\n\n".join(lines)


# ── CLI for quick testing ───────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", "-c")
    parser.add_argument("--query", "-q")
    parser.add_argument("--stocks", "-s", nargs="+")
    parser.add_argument("--author", "-a")
    parser.add_argument("--days", "-d", type=int)
    parser.add_argument("--limit", "-n", type=int, default=10)
    parser.add_argument("--format", action="store_true", help="Human-readable output")
    args = parser.parse_args()
    
    results = search_knowledge(
        channel=args.channel,
        query=args.query,
        stocks=args.stocks,
        author=args.author,
        days=args.days,
        limit=args.limit,
    )
    
    if args.format:
        print(format_for_report(results))
    else:
        print(f"Found {len(results)} results:\n")
        for r in results:
            ts = r.get('timestamp', '')[:16]
            author = r.get('author', '?')
            stocks = ', '.join(r.get('stocks', []))
            print(f"[{ts}] {author} {f'📈 {stocks}' if stocks else ''}")
            print(f"  {r.get('content', '')[:200]}\n")
