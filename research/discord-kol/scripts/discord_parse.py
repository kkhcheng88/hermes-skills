#!/usr/bin/env python3
"""
Discord KOL — Parse DiscordChatExporter JSON into knowledge base.
Handles both clean JSON and truncated files gracefully.

Usage:
  from discord_parse import parse_and_save
  stats = parse_and_save("path/to/export.json", "ChannelName")
"""

import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
KB_DIR = SKILL_DIR / "knowledge"
CST = timezone(timedelta(hours=8))

# ── Stock ticker detection ──────────────────────────────────────────
STOCK_TICKERS = re.compile(
    r'\b(TSLA|NVDA|AAPL|MSFT|META|GOOGL|AMZN|AMD|NFLX|CRM|AVGO|'
    r'INTC|QCOM|TXN|MU|AMAT|LRCX|KLAC|MRVL|SNPS|CDNS|PLTR|NOW|CRWD|'
    r'BA|DIS|JPM|GS|MS|BAC|C|WFC|V|MA|PYPL|SQ|UBER|LYFT|ABNB|'
    r'BABA|JD|PDD|NIO|XPEV|LI|BIDU|'
    r'COIN|MARA|RIOT|MSTR|'
    r'SPY|QQQ|IWM|DIA|VTI|VOO|ARKK|ARKW|IGV|XLF|XLE|XLK|SMH|'
    r'GLD|SLV|USO|UNG|DBC|'
    r'SPX|NDX|DJI)\b',
    re.IGNORECASE
)

# ── Financial relevance (coarse filter) ─────────────────────────────
FINANCIAL_SIGNALS = [
    '美股', '港股', '股票', '个股', '板块', '行业',
    '财报', '业绩', '营收', '利润', 'earnings', 'revenue', 'guidance',
    '美联储', 'Fed', '加息', '降息', '利率', 'CPI', 'GDP', '通胀',
    '原油', '油价', '黄金', '白银', '铜', '天然气', 'OPEC',
    '买入', '卖出', '持有', '目标价', '评级', '分析师', 'call', 'put',
    '暴涨', '暴跌', '新高', '破位', '回调', '反弹', '抄底',
    '多头', '空头', 'bullish', 'bearish', 'short squeeze',
    '盘前', '盘后', 'IPO', '并购', '回购', '分红', '拆股',
    '半导体', '芯片', 'AI', '新能源', '自动驾驶', '光模块', 'cybersecurity',
    '特斯拉', '英伟达', '苹果', '微软', '谷歌', '亚马逊',
    '期权', 'IV', 'premium', 'delta', 'gamma', 'theta',
    '止损', '止盈', '仓位', '建仓', '加仓', '减仓', '清仓',
]

EXCLUDE_PATTERNS = re.compile(
    r'(世界杯|NBA|足球|篮球|比赛|联赛|体育|娱乐|明星|综艺|电影)'
)


def _extract_messages(filepath: str) -> list:
    """Extract messages from DiscordChatExporter JSON, handling truncation."""
    filepath = Path(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try standard JSON first
    try:
        data = json.loads(content)
        return data.get('messages', [])
    except json.JSONDecodeError:
        pass
    
    # Fallback: brace-count extraction for truncated files
    msg_start = content.find('"messages": [')
    if msg_start == -1:
        return []
    
    chunk = content[msg_start + len('"messages": '):]
    messages = []
    depth, obj_start = 0, None
    
    for i, char in enumerate(chunk):
        if char == '{':
            if depth == 0:
                obj_start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and obj_start is not None:
                try:
                    messages.append(json.loads(chunk[obj_start:i+1]))
                except json.JSONDecodeError:
                    pass
                obj_start = None
    
    return messages


def _extract_stocks(text: str) -> list:
    return list(set(m.upper() for m in STOCK_TICKERS.findall(text)))


def _is_financial(text: str) -> bool:
    if EXCLUDE_PATTERNS.search(text):
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in FINANCIAL_SIGNALS)


def parse_messages(messages: list) -> list:
    """Filter and index messages into KB entries."""
    entries = []
    for msg in messages:
        content = msg.get('content', '').strip()
        if not content or len(content) < 10:
            continue
        if msg.get('type', 'Default') != 'Default':
            continue
        
        stocks = _extract_stocks(content)
        if not stocks and not _is_financial(content):
            continue
        
        author = msg.get('author', {})
        entries.append({
            "id": f"discord_{msg.get('id', '')}",
            "source": "discord",
            "author": author.get('nickname') or author.get('name', 'Unknown'),
            "timestamp": msg.get('timestamp', ''),
            "content": content[:2000],
            "stocks": stocks,
        })
    return entries


def parse_and_save(filepath: str, channel_name: str) -> dict:
    """Parse export file and merge into knowledge base. Returns stats."""
    KB_DIR.mkdir(parents=True, exist_ok=True)
    
    messages = _extract_messages(filepath)
    new_entries = parse_messages(messages)
    
    # Load existing KB
    kb_path = KB_DIR / f"{channel_name}.json"
    existing = []
    existing_ids = set()
    if kb_path.exists():
        with open(kb_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        existing_ids = {e['id'] for e in existing}
    
    # Merge
    added = 0
    for entry in new_entries:
        if entry['id'] not in existing_ids:
            existing.append(entry)
            existing_ids.add(entry['id'])
            added += 1
    
    existing.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    return {"total": len(existing), "new": added, "messages_parsed": len(messages)}
