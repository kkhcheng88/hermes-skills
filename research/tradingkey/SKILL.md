---
name: tradingkey
description: Fetch TradingKey's proprietary stock analysis and news — composite score, multi-dimensional ratings, buy/sell suggestions, highlights/risks, support/resistance, sentiment, and stock-specific news. No API key required. US stocks only (NASDAQ/NYSE). PRIMARY SOURCE for stock news. Data is English (API) + Chinese news (HTML). For price/fundamentals use yfinance instead.
version: 2.1.0
notes: |
  ## Implementation Files
  
  - `tradingkey_fetcher.py` — Production-ready Python module with `TradingKeyFetcher` class
    - `get_stock_analysis()` — Fetch score, dimensions, labels, support/resistance, sentiment, agency rating
    - `get_news(limit=6)` — Fetch stock-specific news from SSR HTML
    - `get_article_content(route)` — Fetch full article content
    - `fetch_all(save_dir)` — Fetch all data and optionally save to directory
    - `print_summary(data)` — Print human-readable summary
  
  Usage:
    python from tradingkey_fetcher import TradingKeyFetcher
    fetcher = TradingKeyFetcher("TSLA")
    data = fetcher.fetch_all(save_dir="data/companies/TSLA")
    fetcher.print_summary(data)
  
  CLI usage:
    python tradingkey_fetcher.py TSLA --save data/companies/TSLA
---

# TradingKey API Skill

## Overview

TradingKey (tradingkey.com) provides **proprietary stock analysis** that complements yfinance's price/fundamental data. Focus on what TradingKey uniquely offers: AI-generated scoring, multi-dimensional assessments, and curated news.

**No authentication required.** Base URL: `https://api.tradingkey.com`

**⚠️ Only US stocks supported.** Route format: `nasdaq-{symbol}` (lowercase). Examples: `nasdaq-tsla`, `nasdaq-aapl`, `nasdaq-nvda`.

---

## Endpoints

### 1. Stock Score + Analysis ⭐⭐⭐ (PRIMARY — ONE endpoint for everything)

```
GET /quotes-base/diagnosis/v1/stock-score?route=nasdaq-{SYMBOL}
```

**All data from `json.value`:**

#### 操作建議 (stockSuggest)
```
value.suggests.stockSuggest  — Full text operational recommendation
```
Example: *"Tesla Inc當前公司基本面數據相對非常健康，最新ESG揭露屬於行業領先水平。增長潛力很大..."*

#### 評分 (score)
```
value.score.totalScore       — Composite score (0-10 scale)
value.score.industryRank     — Rank within industry
value.score.industryTotal    — Total stocks in industry
value.score.marketRank       — Rank in entire market
value.score.marketTotal      — Total stocks in market
value.score.countDate        — Score date (YYYY-MM-DD)
```

#### 多維評測 (suggests — description per dimension)
Each dimension has a score + rank in `value.score` AND a descriptive text in `value.suggests`:

| Dimension | Score Key | Description Key | 中文 |
|-----------|-----------|-----------------|------|
| 盈利預測 | `revenueForecasts` | `revenueForecastsSuggest` | Earnings forecast analysis |
| 財務診斷 | `financialDiagnostics` | `financialSuggest` | Financial health analysis |
| 價格動量 | `priceMomentum` | `priceMomentumSuggest` | Price momentum analysis |
| 風險評估 | `riskAssessment` | `riskAssessmentSuggest` | Risk & macro analysis |
| 機構認可 | `institutionalRecognition` | `institutionalRecognitionSuggest` | Institutional holdings analysis |
| 公司估值 | `companyValuation` | `companyValuationSuggest` | Valuation analysis |

For each dimension, extract `value.score.{key}` for the numeric score and `value.suggests.{descriptionKey}` for the text summary.

**上期比對:** `value.lastScore` has same structure as `value.score` for period-over-period comparison.

#### 亮點 & 風險 (labelList)
```
value.labelList[] — Array of tags
  .labelType = 1  →  亮點 (positive)
  .labelType = 2  →  風險 (negative/risk)
  .title        — Tag name (e.g. "Institutional Buying", "Overvalued")
  .description  — Detail text
```

#### 壓力支撐
```
value.pressure  — Resistance price level
value.support   — Support price level
```

#### 公司輿情
```
value.companySentiment.companySentiment  — Sentiment score (-1 to 1, negative=bearish, positive=bullish)
value.companySentiment.companyHot        — Heat/hype score (0-100)
```

#### 分析師評級
```
value.agencyRating.rating      — Consensus rating (e.g. "HOLD", "BUY")
value.agencyRating.targetPrice  — Average target price
value.agencyRating.priceSpace   — Upside/downside % from current price
value.agencyRating.total        — Number of analysts
```

#### 其他
```
value.industryName  — Industry name (e.g. "Automobiles & Auto Parts")
value.companyDesc   — HTML company description (use yfinance longBusinessSummary instead)
```

---

### 2. Stock-Specific News ⭐⭐ (SSR HTML scraping)

**⚠️ There is NO dedicated API endpoint for stock-specific news.** The `/op/content/v1/articles/hot` API returns generic hot articles across all stocks (only 3-4 TSLA-related out of 50), and adding `route`, `symbols`, or `instrument` params does NOT filter by stock.

**The only way to get stock-specific news** is to scrape the SSR-embedded JSON from the stock page HTML:

```
GET https://www.tradingkey.com/zh-hant/markets/stocks/nasdaq-{SYMBOL}
```

Extract the `newsRelatedArticleData` JSON object from the HTML `<script>` tag. It contains:
- `list[]` — Array of article objects (6 articles pre-loaded by SSR)
- `total` — Total count of related articles (e.g. "121" for TSLA)

**Each article in `list[]`:**
- `id` — Article ID
- `title` — Article headline (full text)
- `description` — Article summary (full text, ~100-200 chars) ✅ Unlike the hot API, descriptions ARE populated here
- `route` — URL slug → full URL: `https://www.tradingkey.com/zh-hant/analysis/stocks/us-stock/{route}`
- `publishAt` — Unix timestamp
- `source` — Source (e.g. "TradingKey")
- `author` — Author name
- `coverImage` — Thumbnail URL
- `topic` — Topic category (e.g. "us-stock")
- `class` — Article class (e.g. "FEATURED")

**Extraction method:**
```python
import urllib.request, json, re

def tradingkey_stock_news(symbol="TSLA"):
    route = f"nasdaq-{symbol.lower()}"
    url = f"https://www.tradingkey.com/zh-hant/markets/stocks/{route}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html',
    })
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8')
    
    # Extract newsRelatedArticleData from SSR HTML
    marker = '"newsRelatedArticleData":{'
    idx = html.find(marker)
    if idx == -1:
        return {"list": [], "total": "0"}
    
    # Find matching closing brace
    start = idx + len(marker) - 1  # include the opening {
    depth = 0
    i = start
    for i in range(start, len(html)):
        if html[i] == '{': depth += 1
        if html[i] == '}':
            depth -= 1
            if depth == 0: break
    
    json_str = html[start:i+1]
    return json.loads(json_str)

news = tradingkey_stock_news("TSLA")
for a in news["list"]:
    print(f"[{a['source']}] {a['title']}")
    print(f"  {a['description'][:80]}...")
```

**Limitations:**
- Only **6 articles** are SSR pre-loaded (out of potentially 100+ total)
- No pagination API available — scrolling the page doesn't trigger additional news API calls
- For full article content, use `web_extract` on the article URL

### 3. Generic Hot News (limited usefulness)

```
GET /op/content/v1/articles/hot?size=20&page=1&category=STOCK
```

Returns hot articles across ALL stocks. **Filter client-side** by checking `symbols` array for target stock. Only 3-4 articles per stock typically. **`description` field is always empty.** Prefer Method 2 (SSR scraping) for stock-specific news.

---

## Usage Patterns

### Complete stock analysis (single API call):
```python
import urllib.request, json, time

def tradingkey_analysis(symbol="TSLA"):
    route = f"nasdaq-{symbol.lower()}"
    url = f"https://api.tradingkey.com/quotes-base/diagnosis/v1/stock-score?route={route}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Referer': 'https://www.tradingkey.com/',
        'Origin': 'https://www.tradingkey.com',
    })
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    return data["value"]

v = tradingkey_analysis("TSLA")

# 操作建議
print(v["suggests"]["stockSuggest"])

# 評分
s = v["score"]
print(f"總分: {s['totalScore']}/10  行業: {s['industryRank']}/{s['industryTotal']}  市場: {s['marketRank']}/{s['marketTotal']}")

# 多維評測 (score + description)
dims = [
    ("盈利預測", "revenueForecasts", "revenueForecastsSuggest"),
    ("財務診斷", "financialDiagnostics", "financialSuggest"),
    ("價格動量", "priceMomentum", "priceMomentumSuggest"),
    ("風險評估", "riskAssessment", "riskAssessmentSuggest"),
    ("機構認可", "institutionalRecognition", "institutionalRecognitionSuggest"),
    ("公司估值", "companyValuation", "companyValuationSuggest"),
]
for label, score_key, desc_key in dims:
    score = v["score"].get(score_key, "N/A")
    desc = v["suggests"].get(desc_key, "")
    print(f"{label}: {score}/10 — {desc[:100]}")

# 亮點 & 風險
for item in v["labelList"]:
    tag = "✅" if item["labelType"] == 1 else "⚠️"
    print(f"{tag} {item['title']}: {item['description']}")

# 壓力支撐
print(f"壓力: {v['pressure']}  支撐: {v['support']}")

# 公司輿情
cs = v["companySentiment"]
print(f"輿情: {cs['companySentiment']}  熱度: {cs['companyHot']}")

# 分析師評級
ar = v["agencyRating"]
print(f"評級: {ar['rating']}  目標價: {ar['targetPrice']}  漲幅空間: {ar['priceSpace']}%  分析師數: {ar['total']}")
```

### Stock-specific news (SSR HTML scraping):
```python
import urllib.request, json

def tradingkey_stock_news(symbol="TSLA"):
    route = f"nasdaq-{symbol.lower()}"
    url = f"https://www.tradingkey.com/zh-hant/markets/stocks/{route}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html',
    })
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8')
    
    # Extract newsRelatedArticleData from SSR HTML
    marker = '"newsRelatedArticleData":{'
    idx = html.find(marker)
    if idx == -1:
        return {"list": [], "total": "0"}
    
    start = idx + len(marker) - 1
    depth = 0
    for i in range(start, len(html)):
        if html[i] == '{': depth += 1
        if html[i] == '}':
            depth -= 1
            if depth == 0: break
    
    json_str = html[start:i+1]
    return json.loads(json_str)

news = tradingkey_stock_news("TSLA")
for a in news["list"]:
    print(f"[{a['source']}] {a['title']}")
    print(f"  {a['description'][:100]}...")
```

---

---

## Weekly Market Report (美股投資週報) ⭐⭐⭐ NEW

TradingKey publishes a weekly market report every Sunday covering the full US market.

**URL pattern:** `https://www.tradingkey.com/zh-hant/tools/market-update/us-stock-market-this-week-{YYYYMMDD}`

### Fetching the latest report

```python
import urllib.request, json, re
from datetime import datetime

def tradingkey_weekly_report(date_str=None):
    """
    Fetch TradingKey weekly market report.
    date_str: 'YYYYMMDD' format, or None for latest.
    """
    if date_str is None:
        # Find latest from the list page
        list_url = "https://www.tradingkey.com/zh-hant/tools/market-update"
        req = urllib.request.Request(list_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
        dates = sorted(set(re.findall(r'us-stock-market-this-week-(\d{8})', html)), reverse=True)
        date_str = dates[0] if dates else datetime.now().strftime('%Y%m%d')
    
    url = f"https://www.tradingkey.com/zh-hant/tools/market-update/us-stock-market-this-week-{date_str}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
    
    # Extract weeklyReport JSON from SSR
    idx = html.find('"weeklyReport":{')
    if idx == -1:
        return None
    
    start = idx
    depth = 0
    for i in range(idx, len(html)):
        if html[i] == '{': depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    
    data = json.loads('{' + html[start:end] + '}')
    return data['weeklyReport']
```

### Data structure

```json
{
  "isLocked": true/false,
  "info": {
    "route": "/tools/market-update/us-stock-market-this-week-20260420",
    "summary": "投資要點摘要...",
    "weekPeriod": "2026-04-20"
  },
  "content": {
    "market": "上週市場回顧與分析（詳細全文）",
    "industry": "行業漲幅榜分析（詳細全文）",
    "stocks": "公司漲幅分析（詳細全文）"
  },
  "data": {
    "index": [
      {"symbol": "DJI", "name": "道瓊斯股指", "price": 49447.44, "changePercentage": 3.19},
      {"symbol": "PSY", "name": "標普500股指", "price": 7126.05, "changePercentage": 4.54},
      {"symbol": "IXIC", "name": "納斯達克指數", "price": 24468.48, "changePercentage": 6.84},
      {"symbol": "HSI", "name": "恒生指數", "price": 26160.33, "changePercentage": 1.03}
      // ... 9 major indices total
    ],
    "industry": [
      {"stockInfo": {"symbol": "LIST1088", "name": "客運服務", "route": "..."}, "changePercentage": 5.76},
      // Top 5 performing sectors
    ],
    "stocks": [
      {"stockInfo": {"symbol": "APP", "name": "Applovin Corp", "route": "nasdaq-app"}, "changePercentage": 14.31},
      // Top 5 performing stocks
    ],
    "macroEvent": [
      {"publishAt": "1776169800", "countryCode": "US", "title": "美國核心生產者物價指數年率 (三月)", "previous": "3.9%", "forecast": "4.2%", "actual": "3.8%"},
      // Key economic data releases
    ],
    "earningsRelease": [...],  // Upcoming/near-term earnings
    "dividends": [...],         // Dividend events
    "split": [...]              // Stock split events
  },
  "stockDiagnosis": {
    "totalScore": [...],       // Top 5 highest-scored stocks
    "increaseScore": [...]     // Top 5 biggest score improvements
  },
  "weeklyFollow": {
    "title": "本週關注摘要",
    "macroEvent": [...],       // This week's macro events
    "earningsRelease": [...]   // This week's earnings
  }
}
```

### Key fields for report generation

| Section | Field | Description |
|---------|-------|-------------|
| **投資要點** | `info.summary` | One-paragraph market summary |
| **市場回顧** | `content.market` | Full market analysis text |
| **行業漲幅** | `content.industry` | Sector performance analysis |
| **行業數據** | `data.industry[]` | Top 5 sectors with % change |
| **公司漲幅** | `content.stocks` | Top stock analysis text |
| **公司數據** | `data.stocks[]` | Top 5 stocks with % change |
| **宏觀數據** | `data.macroEvent[]` | Key economic indicators (actual vs forecast) |
| **指數表現** | `data.index[]` | Major index weekly performance |
| **下週預告** | `weeklyFollow` | Upcoming week's events |

---

## Recommended Workflow

For comprehensive US stock analysis, combine **yfinance** + **TradingKey**:

1. **yfinance** — Price, fundamentals, financials, company profile, historical data
2. **TradingKey `/quotes-base/diagnosis/v1/stock-score`** — Score, multi-dimensional analysis, suggestions, highlights/risks, sentiment, analyst rating
3. **TradingKey SSR scraping** — Fetch stock page HTML, extract `newsRelatedArticleData` for 6 stock-specific news articles with descriptions

---

## Limitations

1. **US stocks only** — No HK/China stock support
2. **No real-time prices** — 15-minute delayed data; use yfinance for live quotes
3. **News: no dedicated API endpoint** — Stock-specific news is SSR-embedded in HTML (`newsRelatedArticleData`), only 6 articles pre-loaded, no pagination. Generic hot news API (`/op/content/v1/articles/hot`) returns all stocks mixed together with empty descriptions
4. **No auth required** — API could change or be restricted anytime
5. **companyDesc is raw HTML** — Use yfinance `longBusinessSummary` instead
