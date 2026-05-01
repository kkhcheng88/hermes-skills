---
name: macro-regime-report
description: 生成 Macro Regime Report（HTML infographic），使用 Fathom 風格，自動 deliver 到 Discord。觸發詞：macro report, macro regime, daily report, 市場報告, regime report, CIO report。
---

# Macro Regime Report Generator

生成 Karson 嘅 Macro Regime Report，格式為 Fathom 風格 HTML infographic，deliver 到 Discord。

## Template

Fathom 風格 template 喺：`~/Investment/templates/report1_fathom_template.html`

## Section 順序（固定，唔好改）

1. **CIO 判斷** — 核心結論 + 投資建議，唔限字數，可以 holistic
2. **高階思維分析** — Howard Marks 框架：一階共識、二階反面、三階推演。緊接 CIO
3. **新聞驅動分析（含深度分析）** — 按主題分組（美伊放一組、Fed 放一組），每組：事實 → 影響分析 → 資產關聯。新聞同深度分析合併，唔分開
4. **風險偏好** — VIX、SKEW、SPY、Russell 2000 數據表 + 詳細判定 elaboration
5. **全球資產表現** — SPY / QQQ / Russell 2000 各自獨立技術分析（RSI、SMA）。**VIX 同 SKEW 唔喺呢度**，淨喺上面風險偏好 section
6. **貨幣環境** — Treasury yields、credit spreads、DXY、Fed RRP、Oil 對通脹影響

## 關鍵規則（用戶反覆確認）

### 股指分析
- **SPY、QQQ、Russell 2000 三個都必須 always covered，各自獨立**，唔需要比較相對強弱
- SPY 同 QQQ 需要：RSI(14)、RSI(2)、SMA10/20/50、IV Rank
- Russell 2000 需要：RSI(14)、RSI(2)、SMA10/20/50

### VIX 分析
- **VIX 唔係 ticker，唔做 RSI/SMA**，只講 level + direction movement
- **IV Rank 係 SPY/QQQ 嘅指標，唔係 VIX 嘅**
- VIX 同 SKEW 只喺「風險偏好」section，唔喺「全球資產表現」

### 格式規則
- **唔用 emoji 符號（🟢⚖️🔴）代替判斷**，直接用文字講清楚，正式報告語氣
- **Section 名稱全部中文**：CIO 判斷、高階思維分析、新聞驅動分析、風險偏好、全球資產表現、貨幣環境
- 繁體中文（廣東話口語風格）

### 新聞處理
- 同類新聞分組（所有美伊相關一組、所有 Fed 相關一組）
- 每組新聞要講影響，唔好淨係列 fact
- 深度分析同新聞驅動分析合併，唔分開兩個 section

## Font / Mobile
- Base font: 16px（mobile readable）
- Body text in cards: 16-17px
- Mobile responsive @ 768px：單欄 layout，grid stack

## Data Sources

- **yfinance** — 股價、技術指標（RSI、SMA）
- **TradingKey Stock Score API** — 股票評分（macro report 主要用 yfinance）
- **TradingKey 週報** — 宏觀數據補充（CPI/PPI 實際 vs 預期、非農、消費者信心）。**僅用喺 Section 6 貨幣環境嘅綜合分析**，講「市場預期有冇改變」。已過時（10日+前）嘅數據唔重複引用，只有近期發布嘅先有參考價值
- **WallStreetCN** — 中文財經新聞

### Section 6 貨幣環境 — 指標層次

**表格層（量化指標）**：
- FedWatch / PolyMarket：市場對加息/減息嘅機率預期（核心指標）
- Treasury yields（2Y/10Y）、credit spreads、DXY、Fed RRP、Oil

**分析層（綜合敘述）**：
- CPI、PPI、非農就業、消費者信心等宏觀數據嘅影響，綜合講成一件事：「呢啲數據點樣影響市場對利率路徑嘅預期？」
- 只喺數據近期發布時引用，已過時嘅唔重複提

## Deliver to Discord

HTML report 用 `MEDIA:` 語法 send 到 Discord，唔轉 PDF：
```
send_message(target="discord:1495805538003583006", message="Summary text\nMEDIA:/path/to/report.html")
```

#investment channel：`discord:1495805538003583006`

## CRON Jobs

兩個 CRON job 已設定（HKT timezone）：
- **8am HKT**（`0 8 * * *`）— 美股收市後，用最新收市數據
- **7pm HKT**（`0 19 * * *`）— 美股開市前，用上日收市 + 亞洲時段

Skills attached：`wallstreetcn`、`tradingkey`、`stock-analysis`

## Design Style

**Fathom Information Design** — 科學敘事風格：
- 深海軍藍底（#0B1426）
- 淺字（#D4DCE8）
- 字體：Newsreader serif + DM Sans sans-serif
- 卡片式布局，border-radius: 10px
- accent 色：#4A90D9
- gold 色用於 policy 標籤

## Data Fetching Pitfalls

- **FedWatch (CME)**: `browser_navigate` to cmegroup.com often fails with `net::ERR_HTTP2_PROTOCOL_ERROR`. Fallback: use `curl` with HTTP/1.1 (`--http1.1`) or scrape via WSL Chrome headless, or use web_search to find cached FedWatch data
- **PolyMarket**: Use `/public-search?q=QUERY` endpoint (NOT `/events?title=QUERY` which returns irrelevant results)
- **WallStreetCN**: delegate_task with `web` toolset often times out (300s). Use direct Python script via write_file + terminal instead
- **yfinance**: Always use write_file + terminal pattern (not execute_code inline) to avoid string escaping issues
- **Parallel fetching**: delegate_task works well for yfinance + TradingKey (independent), but WallStreetCN should be fetched directly due to timeout risk

## Output File

HTML report 存喺：`~/Investment/reports/daily_macro_report.html`
Template 存喺：`~/Investment/templates/report1_fathom_template.html`
Markdown template：`~/Investment/templates/report1_macro_template.md`
