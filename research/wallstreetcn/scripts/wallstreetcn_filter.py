#!/usr/bin/env python3
"""
WallStreetCN 智能过滤器 — 用于 streaming pipeline
功能：
  1. Poll 快讯 + 文章
  2. 去重（基于 ID + cursor）
  3. 分类过滤：金融相关 vs 非金融
  4. Watchlist 匹配：标记命中股票/行业
  5. 输出结构化 JSON，供 LLM 进一步判断重要性
"""

import argparse
import json
import os
import sys
import re
import yaml
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

API_BASE = "https://api-one.wallstcn.com/apiv1/content"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://wallstreetcn.com/live",
}

SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / "config"
STATE_DIR = SCRIPT_DIR.parent / "state"

# ─── Non-financial patterns to exclude ────────────────────────────
EXCLUDE_PATTERNS = [
    r'足球|篮球|世界杯|NBA|联赛|比赛|赛事|国家队|球员|教练',
    r'娱乐|明星|综艺|电影|电视剧|歌手|演员|偶像',
    r'八卦|绯闻|恋情|离婚|结婚|分手',
    r'天气|地震|台风|洪水(?!.*保险|.*基建)',
    r'体育',
]

# ─── Financial relevance patterns to include ──────────────────────
FINANCE_PATTERNS = [
    r'美联储|Fed|利率|加息|降息|GDP|CPI|通胀|就业|非农|央行|货币政策|财政',
    r'关税|贸易战|制裁|谈判|停火|封锁|冲突|战争|地缘|外交',
    r'原油|油价|黄金|白银|大宗商品|OPEC|天然气|铜|铝|铁矿石|农产品',
    r'能源|石油|燃油',
    r'美股|港股|A股|道琼斯|纳斯达克|标普|恒生|上证|深成',
    r'股票|个股|板块|行业|涨|跌|盘前|盘后|熔断|新高|破位',
    r'财报|业绩|营收|利润|guidance|earnings|revenue|盈利|亏损',
    r'分析师|评级|目标价|调升|调降|买入|卖出|持有',
    r'监管|政策|法规|SEC|CFTC|证监会|银保监',
    r'特斯拉|英伟达|苹果|微软|谷歌|亚马逊|Meta|TSLA|NVDA|AAPL',
    r'半导体|AI|芯片|新能源|电动车|光模块|云计算|机器人|自动驾驶',
    r'地产|银行|保险|医药|生物科技|光伏|储能',
    r'IPO|上市|并购|重组|增发|回购|分红|拆股|退市',
    r'基金|ETF|债券|国债|收益率|利差|信用',
]


def load_watchlist() -> dict:
    watchlist_path = CONFIG_DIR / "watchlist.yaml"
    if not watchlist_path.exists():
        return {"stocks": [], "sectors": [], "keywords": [], "threshold": "normal"}
    with open(watchlist_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state() -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path = STATE_DIR / "streaming_state.json"
    if state_path.exists():
        with open(state_path, "r") as f:
            return json.load(f)
    return {"seen_ids": [], "last_cursor": None}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path = STATE_DIR / "streaming_state.json"
    state["seen_ids"] = state["seen_ids"][-500:]
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def is_excluded(text: str) -> bool:
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def is_financial(text: str) -> bool:
    for pattern in FINANCE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def match_watchlist(text: str, watchlist: dict) -> list:
    hits = []
    text_lower = text.lower()
    for stock in watchlist.get("stocks", []):
        if stock.lower() in text_lower:
            hits.append(f"stock:{stock}")
    for keyword in watchlist.get("keywords", []):
        if keyword.lower() in text_lower:
            hits.append(f"keyword:{keyword}")
    for sector in watchlist.get("sectors", []):
        if sector.lower() in text_lower:
            hits.append(f"sector:{sector}")
    return hits


def classify_item(text: str, watchlist: dict) -> dict:
    if is_excluded(text):
        return {"relevance": "skip", "category": "skip", "watchlist_hits": [], "reason": "non-financial"}

    wl_hits = match_watchlist(text, watchlist)

    if not is_financial(text) and not wl_hits:
        return {"relevance": "low", "category": "unknown", "watchlist_hits": [], "reason": "no-financial-pattern"}

    category = "general"
    relevance = "medium"

    if re.search(r'美联储|Fed|加息|降息|非农|CPI|GDP|央行|利率', text):
        category = "macro"; relevance = "high"
    elif re.search(r'战争|冲突|制裁|封锁|停火|霍尔木兹|OPEC|地缘', text):
        category = "geopolitics"; relevance = "high"
    elif re.search(r'油价|原油|黄金|白银|大宗商品', text):
        category = "commodity"; relevance = "high"
    elif re.search(r'财报|业绩|营收|earnings|revenue|盈利|guidance', text):
        category = "stock"; relevance = "high"
    elif re.search(r'美股|道琼斯|纳斯达克|标普|盘前|盘后|暴涨|暴跌|熔断|新高', text):
        category = "market"; relevance = "high"
    elif re.search(r'半导体|AI|芯片|新能源|电动车|光模块', text):
        category = "sector"; relevance = "medium"

    if wl_hits:
        relevance = "high"

    return {"relevance": relevance, "category": category, "watchlist_hits": wl_hits, "reason": "classified"}


def fetch_lives(channel: str, limit: int, cursor: str = None) -> dict:
    params = {"channel": channel, "limit": limit}
    if cursor:
        params["cursor"] = cursor
    resp = requests.get(f"{API_BASE}/lives", params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_articles(channel: str, limit: int) -> dict:
    params = {"channel": channel, "limit": limit}
    resp = requests.get(f"{API_BASE}/articles", params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def ts_to_hktime(ts: int) -> str:
    dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
    return dt.strftime("%m-%d %H:%M")


def main():
    parser = argparse.ArgumentParser(description="WallStreetCN 智能过滤器")
    parser.add_argument("--type", choices=["lives", "articles"], default="lives")
    parser.add_argument("--channels", nargs="+",
                        default=["global-channel", "us-stock-channel", "commodity-channel"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--min-relevance", choices=["high", "medium", "low"], default="medium")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-state", action="store_true")

    args = parser.parse_args()
    watchlist = load_watchlist()
    state = load_state() if not args.no_state else {"seen_ids": [], "last_cursor": None}
    seen_ids = set(state["seen_ids"])

    relevance_order = {"high": 3, "medium": 2, "low": 1, "skip": 0}
    min_rel = relevance_order[args.min_relevance]

    all_items = []

    for channel in args.channels:
        if args.type == "lives":
            data = fetch_lives(channel, args.limit, state.get("last_cursor"))
            items = data.get("data", {}).get("items", [])
            next_cursor = data.get("data", {}).get("next_cursor")
        else:
            data = fetch_articles(channel, args.limit)
            items = data.get("data", {}).get("items", [])
            next_cursor = None

        for item in items:
            item_id = str(item.get("id", ""))
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            text = item.get("content_text", item.get("content_short", ""))
            title = item.get("title", "")
            full_text = f"{title} {text}".strip()

            classification = classify_item(full_text, watchlist)

            if relevance_order.get(classification["relevance"], 0) >= min_rel:
                all_items.append({
                    "id": item_id,
                    "time": ts_to_hktime(item["display_time"]),
                    "timestamp": item["display_time"],
                    "text": text[:500],
                    "title": title,
                    "source": item.get("source_name", ""),
                    "url": item.get("uri", ""),
                    "channel": channel,
                    "classification": classification,
                })

        if next_cursor and args.type == "lives":
            state["last_cursor"] = next_cursor

    all_items.sort(key=lambda x: x["timestamp"], reverse=True)

    state["seen_ids"] = list(seen_ids)
    save_state(state)

    if args.json:
        print(json.dumps(all_items, ensure_ascii=False, indent=2))
    else:
        if not all_items:
            print("✅ No new relevant items.")
            return

        print(f"📰 Found {len(all_items)} relevant items:\n")
        for item in all_items:
            cls = item["classification"]
            priority = "🔥" if cls["watchlist_hits"] else "📌" if cls["relevance"] == "high" else "📰"
            cat = f"[{cls['category']}]"
            print(f"{priority} {cat} {item['time']}")
            if item["title"]:
                print(f"   {item['title']}")
            print(f"   {item['text'][:200]}")
            if cls["watchlist_hits"]:
                print(f"   🔥 Watchlist: {', '.join(cls['watchlist_hits'])}")
            if item["url"]:
                print(f"   🔗 {item['url']}")
            print()


if __name__ == "__main__":
    main()
