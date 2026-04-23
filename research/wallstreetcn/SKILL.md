---
name: wallstreetcn
description: Fetch real-time financial news from 华尔街见闻 (WallStreetCN) — live tickers (快讯) and articles (资讯). Chinese-language financial news source covering global markets.
version: 1.0
---

# WallStreetCN Skill

Fetch real-time Chinese-language financial news from 华尔街见闻 (WallStreetCN).

## Overview

Two modes of operation:
1. **Streaming (快讯)** — real-time breaking news, polled every 10 min
2. **Articles (资讯)** — in-depth reports with titles & summaries

Focus: Global macro, US stocks, commodities (gold, silver, oil), and sector/stock-specific events (earnings, results, announcements).

**Filter out:** Sports, entertainment, and other non-financial content.

## Content Filtering Rules

When processing news items, apply these filters:

### EXCLUDE (skip these)
- Sports (体育, 足球, 篮球, 世界杯, NBA, 联赛)
- Entertainment (娱乐, 明星, 综艺, 电影)
- Social/celebrity gossip
- Weather/natural disasters with no market impact

### INCLUDE (always capture)
- **Macro/Government**: 美联储, Fed, 利率, 加息, 降息, GDP, CPI, 通胀, 就业, 非农
- **Geopolitics**: 关税, 贸易战, 制裁, 冲突, 战争, 谈判, 停火, 封锁
- **Commodities**: 原油, 油价, 黄金, 白银, 大宗商品, OPEC, 霍尔木兹
- **Stock-specific**: 财报, 业绩, 营收, earnings, revenue, guidance, 分析师, 目标价, 评级
- **Sector**: 半导体, AI, 芯片, 新能源, 医药, 地产, 银行, 保险
- **Market moves**: 暴涨, 暴跌, 熔断, 新高, 破位, 盘前, 盘后
- **Policy**: 监管, 政策, 法规, 央行, SEC, CFTC

### AMBIGUOUS — let LLM decide
- Events that COULD impact markets but aren't clearly financial
- Regional events (e.g. local politics) that might affect specific sectors

## Watchlist (Optional)

A watchlist file at `config/watchlist.yaml` can specify stocks and sectors of interest.
When present, news items mentioning watchlist entries get flagged with 🔥 priority.

```yaml
# Example watchlist.yaml
stocks:
  - TSLA
  - NVDA
  - AAPL
  - MSFT
  - AMD
sectors:
  - AI
  - 半导体
  - 新能源
keywords:
  - 特斯拉
  - 英伟达
  - 光模块
```

## API Base

`https://api-one.wallstcn.com/apiv1/content/`

## Two Content Types

### 1. 快讯 (Live News / Breaking Tickers)

**Endpoint:** `GET /lives`
**Parameters:** `channel`, `limit`, `cursor` (pagination)
**Output:** Real-time one-liner news items, often without titles.

```
https://api-one.wallstcn.com/apiv1/content/lives?channel={CHANNEL}&limit={LIMIT}
```

### 2. 资讯 (Articles)

**Endpoint:** `GET /articles`
**Parameters:** `channel`, `limit`
**Output:** In-depth articles with titles, summaries, sources.

```
https://api-one.wallstcn.com/apiv1/content/articles?channel={CHANNEL}&limit={LIMIT}
```

## Available Channels

| Channel | Description |
|---------|-------------|
| `global-channel` | 全球 (Global) — default, 7x24快讯 |
| `a-stock-channel` | A股 (China A-shares) |
| `hk-stock-channel` | 港股 (Hong Kong stocks) |
| `us-stock-channel` | 美股 (US stocks) |
| `forex-channel` | 外汇 (Forex) |
| `commodity-channel` | 商品 (Commodities) |
| `bond-channel` | 债券 (Bonds) |

## Key Fields in Response

### Live News (`/lives`)
- `content_text` — Clean text (strip HTML from `content`)
- `display_time` — Unix timestamp
- `author.display_name` — Author name
- `channels` — Which channels this item belongs to
- `symbols` — Related stock symbols (often empty)
- `uri` — Link to the news item

### Articles (`/articles`)
- `title` — Article headline
- `content_short` — Summary / description
- `source_name` — News source (e.g. 新华社, 央视新闻)
- `display_time` — Unix timestamp
- `categories` — Category tags
- `symbols` — Related stock symbols
- `uri` — Link to full article

## Pagination

Live news supports cursor-based pagination. Response includes `data.next_cursor`.
Pass it as `&cursor={next_cursor}` to fetch older items.

## Required Headers

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://wallstreetcn.com/live'
}
```

## Usage Examples

### Fetch latest 10 global breaking news
```python
import requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://wallstreetcn.com/live'
}
resp = requests.get(
    'https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=10',
    headers=headers
)
data = resp.json()
for item in data['data']['items']:
    print(f"[{item['display_time']}] {item['content_text']}")
```

### Fetch latest 5 US stock articles
```python
resp = requests.get(
    'https://api-one.wallstcn.com/apiv1/content/articles?channel=us-stock-channel&limit=5',
    headers=headers
)
data = resp.json()
for item in data['data']['items']:
    print(f"{item['title']} - {item['source_name']}")
    print(f"  {item['content_short'][:120]}")
```

## Scripts

### `scripts/wallstreetcn.py` — 基本 fetcher
```bash
python3 scripts/wallstreetcn.py --channel global-channel --limit 10
python3 scripts/wallstreetcn.py --type articles --channel us-stock-channel --limit 5
```

### `scripts/wallstreetcn_filter.py` — 智能過濾器 (streaming pipeline 用)
```bash
# 只睇 high relevance items（重大事件、watchlist 命中）
python3 scripts/wallstreetcn_filter.py --min-relevance high --limit 30

# 埋 medium relevance（行業新聞、一般市場動態）
python3 scripts/wallstreetcn_filter.py --min-relevance medium --limit 30

# JSON output（for LLM processing）
python3 scripts/wallstreetcn_filter.py --min-relevance high --limit 50 --json

# 忽略 state（每次重新 fetch 全部）
python3 scripts/wallstreetcn_filter.py --no-state --limit 20

# 指定 channels
python3 scripts/wallstreetcn_filter.py --channels global-channel commodity-channel --limit 20
```

**Filter 特點：**
- 自動排除非金融內容（體育、娛樂等）
- 自動分類：macro / geopolitics / commodity / stock / market / sector
- Watchlist 命中標 🔥，重大事件標 📌
- State 去重：自動記住已見過嘅 ID，唔會重複推送

## Streaming Pipeline Workflow

### Layer 1: 每 10 分鐘 streaming
```bash
# Cron job 指令：
python3 ~/.hermes/skills/research/wallstreetcn/scripts/wallstreetcn_filter.py \
  --channels global-channel us-stock-channel commodity-channel \
  --min-relevance high --limit 20
```
1. Poll 3 個 channel
2. Filter 非金融 + 低相關
3. 只返回 high relevance（macro、geopolitics、commodity、watchlist 命中）
4. Cron job 用 LLM 進一步判斷 → 推 Discord

### Layer 2: 每日報告（美股開市前 ~21:00 HKT）
```bash
# 補掃全日
python3 ~/.hermes/skills/research/wallstreetcn/scripts/wallstreetcn_filter.py \
  --no-state --min-relevance medium --limit 50

# 撈深度文章
python3 ~/.hermes/skills/research/wallstreetcn/scripts/wallstreetcn.py \
  --type articles --channel global-channel --limit 10
python3 ~/.hermes/skills/research/wallstreetcn/scripts/wallstreetcn.py \
  --type articles --channel us-stock-channel --limit 10
```
1. 用 `--no-state` 重新 fetch 全日快訊
2. 撈埋 articles（深度報導）
3. 全部喂入 LLM → 生成結構化市場報告

## Limitations

- API returns max ~50 items per request (use cursor for more)
- `symbols` field is often empty — no per-stock filtering via API
- Some articles are paywalled (VIP / paid content)
- No full-text search API exposed — only channel-based filtering
- Timezone: All timestamps are Unix epoch (UTC), display as needed

## Python Script

A helper script is available at `scripts/wallstreetcn.py` in this skill directory.
Run it to quickly fetch and display news:

```bash
python3 ~/.hermes/skills/wallstreetcn/scripts/wallstreetcn.py --channel global-channel --type lives --limit 10
```
