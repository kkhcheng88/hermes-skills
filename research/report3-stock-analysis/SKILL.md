---
name: report3-stock-analysis
description: 生成 Report 3（Layer 3）— 個股 + ETF 深度操作分析。由 Report 2 驅動，永遠出報告。觸發詞：report 3, layer 3, stock report, 個股報告, 操作建議。
---

# Report 3 — 個股 + ETF 深度操作（Layer 3）

Report 3 係三層漏斗嘅最窄口。Report 1 定 macro 前提，Report 2 揀戰場（Chain/Sector），Report 3 出具體操作建議。

## 與 Report 1/2 嘅關係

```
Report 1 (Macro Regime) — 前提
    ↓
Report 2 (Chain/Sector 溫度計) — 揀戰場
    ↓ 輸出：🔥/🌡️ Chain + 異常 Sector
Report 3 (個股 + ETF 操作) — 具體行動
```

**永遠出 Report 3，唔會 skip。** 即使全部 ❄️，都要出（做反向機會判斷）。

## Template

**Markdown**：直接生成，結構跟隨 Section 順序。存檔路徑：`~/Investment/reports/daily_report3_stock_analysis.md`

**HTML**：Fathom 深海軍藍風格（同 Report 1/2），template 存檔：`~/Investment/reports/daily_report3_stock_analysis.html`。HTML 版唔用 emoji，用色點/圖標代替。Discord 用 `MEDIA:` 語法發送 HTML attachment。

### 分段生成策略（重要！）

Report 3 內容量大，一次過生成會爆 context。必須分段生成再合併：

1. **Template**：`~/Investment/templates/report3_fathom_template.html`（CSS + 結構，固定唔變）
2. **Builder Script**：`~/Investment/reports/report3_builder.py`（Python，負責 save/merge fragments）
3. **生成順序**：

```
Step 1: 讀 Report 2 最新輸出 → 決定分析範圍
Step 2: save_fragment("s1_context", ...) + save_fragment("s2_cio", ...)
Step 3: 逐條 Chain 生成：
        save_fragment("s3_chain_AI", ...)
        save_fragment("s3_chain_MEM", ...)
        save_fragment("s3_chain_NRG", ...)
Step 4: save_fragment("s4_sector_XXX", ...)（如有異常 Sector）
Step 5: save_fragment("s5_cold", ...)
Step 6: save_fragment("s6_summary", ...)（操作總覽表）
Step 7: save_fragment("s7_risk", ...)
Step 8: merge_from_fragments() → 最終 HTML
```

**每條 Chain 最多 3-4 隻個股**（唔好貪多，focus 最有代表性嘅）。
**每個 fragment 控制喺 3000-4000 字以內**。
**Fragments 暫存目錄**：`~/Investment/reports/.report3_fragments/`
**每次生成前 clear_fragments()**。

## Section 順序（固定，唔好改）

1. **Context 連結** — R1 Regime 前提一句 + R2 熱門 Chain/異常 Sector 一句
2. **CIO 操作判斷** — 本週重心 + 倉位策略 + 整體風格（進攻/防守/觀望）+ 行動 trigger
3. **🔥/🌡️ Value Chain 展開** — 每條 Chain：相關 ETF + 3-5 隻個股深度分析 + 操作建議
4. **異常 Sector 展開** — R2 觸發異常嘅 Sector：相關 ETF + 個股 + 操作建議（頻率低過 Chain）
5. **❄️ Chain + Sector 掃描** — 全部掃，輕量 highlight（value trap vs 撈底，每條 2-3 句重點發現）
6. **操作總覽表** — 一頁表格：全部操作建議一目了然
7. **風險提醒 + 觸發條件** — 乜嘢情況要改變計劃

## 個股/ETF 來源

### Value Chain 個股揀選（每條 🔥/🌡️ Chain 3-5 隻）

| 維度 | 邏輯 | 唔揀乜 |
|------|------|---------|
| 行業代表性 | 每條 Chain 揀最具代表性嘅玩家（龙头 + 潛力股）| 唔揀 OTC / micro cap |
| TradingKey 評分 | 優先揀評分有變化或有爭議嘅（動態信號）| 唔淨係揀最高分 |
| Karson 風格匹配 | 左側交易：最近有回調嘅（有支撑位可講）| 唔揀已經飛到天上無回調嘅 |

### ETF 來源

Report 2 嘅 23 隻 ETF（GICS 11 + 主題 12）加埋 SPY + QQQ = **25 隻 ETF**。ETF 放入對應 Chain/Sector section 內，唔另開獨立 section。

## 個股/ETF 分析 Card 格式

每隻個股/ETF 含以下內容：

```
═══ [NVDA] AI / 半導體 Chain ═══

📊 基本數據
   價格：$XXX | RSI(14)：XX | SMA10：$XX | SMA20：$XX | SMA50：$XX

⭐ TradingKey 評分：XX/10
   亮點：xxx
   風險：xxx
   輿情：XX（熱度：XX）
   分析師評級：HOLD / BUY | 目標價：$XX | 漲幅空間：XX%

📈 基本面（Lynch 視角）
   PEG：X.X | Revenue 增長：XX% | EPS 趨勢：↑/↓/→
   Story：一句話呢隻股嘅投資故事

📰 近期新聞（TradingKey SSR，6 篇最新）
   1. [source] title — 一句話影響
   2. ...

🔍 Agent 視角：【狀態：升溫】
   （2-3 句分析，蒸餾 agent 洞見，唔拋書包列 agent 名）

────────────────────────
🟢 操作建議
────────────────────────
📌 方向：買入 / 觀望 / 持有 / 減倉

📍 入場區（分批，never 1 shot）：
   第 1 批：$XX - $XX（佔目標倉位 40%）— 觸發條件：xxx
   第 2 批：$XX - $XX（佔目標倉位 35%）— 觸發條件：xxx
   第 3 批：$XX - $XX（佔目標倉位 25%）— 觸發條件：xxx

🛑 止損：$XX（跌破即走）
   理由：xxx（技術位/基本面變化）

🎯 目標價：
   第一目標：$XX — 理由：xxx
   第二目標：$XX — 理由：xxx

📊 倉位：X% of portfolio（分批）
   最大總投入：X%

⏰ 時間窗口：短期（1-2W）/ 中期（1-3M）/ 長期持有

💡 操作邏輯（完整段落，3-5 句，唔夠一句）：
   - Macro 前提：R1 嘅 regime 點樣影響呢隻股
   - Chain/Sector 位置：喺 R2 嘅 chain 入面扮演咩角色
   - 技術面依據：入場區/止損/目標點解咁定
   - 新聞催化/壓力：近期新聞點樣影響短期走勢
   - 風險收益比：最差情況虧 X%，最好情況賺 X%

⚠️ 最大風險：X%（相對入場價）
```

## 操作總覽表（Section 6）

一頁表格，全部操作建議一目了然：

| 個股/ETF | 方向 | 入場區（分批） | 止損 | 目標 | 倉位 | 來源 |
|----------|------|----------------|------|------|------|------|
| NVDA | 觀望 | — | — | — | — | AI/Semi Chain |
| AVGO | 買入 | $130/125/120 | $110 | $170/$190 | 3% | AI/Semi Chain |
| XLK | 持有 | — | $185 | $220 | 5% | Sector 異常 |
| SPY | 買入 | $530/520/510 | $495 | $570/$590 | 8% | Baseline |

## Agent Framework（按情境自動選擇）

蒸餾成分析視角，唔拋書包列 agent 名，但要保留每個視角嘅洞見。IC 式一句話結論。

| 情境 | Agent | 核心視角 | 適用場景 |
|------|-------|---------|---------|
| 過熱 | Marks + Miller + Eveillard | 係頂？定仲有空間？Cycle positioning | RSI 超買、連續創高、市場狂熱 |
| 過冷 | Klarman + Munger + Graham | 真撈底？定 value trap？Safety margin | 大幅回調、市場恐慌、被遺忘 |
| 升溫 | Lynch + Greenblatt + Marks | 真催化定 noise？Story 點？ | 開始有動能、新聞增多 |
| 內部分化 | Lynch + Buffett + Greenblatt | 邊類受益？邊類受壓？揀贏家 | 同一 Chain 內部表現分歧 |
| 通用 | Marks + Munger + Lynch | 基礎三件套 | 所有情況嘅 fallback |

**Lynch 為首選**（PEG + Story + Six Categories），配合 Karson 左側交易風格。

### Agent 詳細應用指引

| Agent | 核心原則 | Report 3 點樣用 |
|-------|---------|----------------|
| **Peter Lynch** | PEG < 1 低估、Story 比數字重要、Six categories（Slow Grower/Stalwart/Fast Grower/Cyclicals/Turnarounds/Asset Plays）| 首選框架：PEG + 投資故事 + 成長分類 |
| **Howard Marks** | Cycle positioning、Second-level thinking、風險感知 | 判斷個股處於 cycle 哪個位置，市場共識 vs 反面 |
| **Bill Miller** | Contrarian、FCF focus、Long-term horizon | 被市場拋棄但 FCF 穩健嘅個股 |
| **Charlie Munger** | Inversion thinking、Lollapalooza effect | 反過嚟睇：點解會虧？最差情況？ |
| **Seth Klarman** | Margin of safety、Disciplined value | 入場價要有足夠安全邊際 |
| **Joel Greenblatt** | Magic Formula（ROIC × Earnings Yield）| 量化篩選隱藏 gem |
| **Ben Graham** | Net-NET、Intrinsic value、Mr. Market | 最極端嘅 value 情境 |

## Section 5 ❄️ Chain + Sector 掃描

全部 10 條 Chain + 11 個 GICS Sector 都掃，但輕量處理。每條 2-3 句 highlight：

```
❄️ Quantum Computing — 暫時冇催化劑觸發
   Google/IBM 量子錯誤糾正進展唔夠商用，市場冇定價。
   Value trap 機率高 — 等實際商用突破先入場，唔 pre-price。
```

判斷邏輯用 Klarman + Munger 視角：
- Value Trap 指標：行業結構性衰退？定係週期性低谷？
- 撈底條件：要見到乜嘢先值得入場？

## 新聞策略

### Report 3 新聞

- **每隻個股**：TradingKey SSR scraping 6 篇最新相關新聞（有 title + description）
- **WallStreetCN**：scan 全部 Report，Report 3 亦要 scan
- **Internet search**：補充重大 breaking news

### Report 1/2 新聞（填補 NewsAPI gap）

- NewsAPI.org 免費 plan 有 ~1 天延遲
- 必須用 **WallStreetCN** + **internet search（web_search）** 補充過去 2 日新聞
- WallStreetCN 係三層 Report 嘅通用新聞底層，所有 Report 都應 scan

## 格式規則

- **Discord 文字版可用 emoji**（🔥🌡️❄️🔴🟡⚪），HTML 版唔用 emoji
- Agent 思想蒸餾成分析視角，唔拋書包列 Agent 名
- IC 式一句話結論（每個深度分析都要有）
- 繁體中文（廣東話口語風格）
- 操作建議邏輯必須完整段落（3-5 句），唔夠一句

## Data Sources

| 工具 | 用途 |
|------|------|
| yfinance | 個股/ETF 價格、RSI、SMA、基本面（PEG、Revenue、EPS）|
| TradingKey Stock Score API | 個股評分、操作建議、多維評測、壓力支撐、輿情、分析師評級 |
| TradingKey SSR scraping | 每隻個股 6 篇最新相關新聞 |
| WallStreetCN | 通用新聞底層，所有 Report 都 scan |
| internet search (web_search) | 補充重大 breaking news |

## Practical Execution Tips（實戰經驗）

### 1. Data Fetching Strategy

**唔用 delegate_task fetch data** — subagent 容易 timeout（300s limit）。改用直接 execute_code：

```python
# TradingKey API — 用 curl 最快
from hermes_tools import terminal
import json

stocks = ["NVDA", "AVGO", "TSM", "MU", "CVX", "XOM"]
results = {}
for sym in stocks:
    url = f"https://api.tradingkey.com/quotes-base/diagnosis/v1/stock-score?route=nasdaq-{sym.lower()}"
    cmd = f'curl -s -H "User-Agent: Mozilla/5.0" -H "Accept: application/json" -H "Referer: https://www.tradingkey.com/" "{url}"'
    r = terminal(cmd, timeout=20)
    if r["exit_code"] == 0:
        data = json.loads(r["output"])
        results[sym] = data.get("value", {})
```

### 2. yfinance Script File Approach

**唔用 inline Python 喺 execute_code** — 字符 escaping 會出 SyntaxError。改用：

1. `write_file` 寫 Python script 到 `~/Investment/reports/.report3_data/fetch_yf.py`
2. `terminal("python3 ~/Investment/reports/.report3_data/fetch_yf.py")` 執行

```python
# fetch_yf.py 內容
import yfinance as yf, json, pandas as pd
symbols = ["NVDA", "AVGO", "TSM", "MU", "CVX", "XOM", "SMH", "DRAM", "XOP", "XLE"]
results = {}
for sym in symbols:
    tk = yf.Ticker(sym)
    hist = tk.history(period="3mo")
    # RSI/SMA calculation...
    results[sym] = {"price": ..., "rsi14": ..., ...}
with open("yfinance.json", "w") as f:
    json.dump(results, f)
```

### 3. Fragment Generation Workflow

```
Step 1: terminal("python3 ~/Investment/reports/report3_builder.py clear")
Step 2: execute_code 生成 S1 + S2 fragments → save to .report3_fragments/
Step 3: execute_code 生成 S3 Chain fragments（每條 Chain 一個 fragment）
Step 4: execute_code 生成 S4 + S5 + S6 + S7 fragments
Step 5: execute_code merge all fragments → final MD
Step 6: execute_code convert MD to HTML（簡化版 CSS OK，唔一定要用 template）
Step 7: send_message with MEDIA: HTML attachment
```

### 4. HTML Generation Shortcuts

**時間壓力下唔用 template substitution** — 直接用簡化版 inline CSS：

```python
html = f"""<!DOCTYPE html>
<html><head><style>
  body {{ background: #0B1426; color: #D4DCE8; max-width: 900px; }}
  h2 {{ color: #4A90D9; }} table {{ width: 100%; }}
</style></head><body>
{md_content_converted}
</body></html>"""
```

完整 Fathom template 可以喺非緊急情況下用，但 cron job 時間緊迫時簡化版 OK。

## CRON Jobs

Report 3 排喺 Report 2 之後（需要 R2 輸出決定分析範圍）：

```
8:00 HKT  → Report 1（Macro Regime）
8:30 HKT  → Report 2（Chain/Sector）
9:00 HKT  → Report 3（個股 + ETF 操作）

19:00 HKT → Report 1
19:30 HKT → Report 2
20:00 HKT → Report 3
```

Skills attached：`tradingkey`、`stock-analysis`、`wallstreetcn`

### CRON Prompt 要點

CRON prompt 必須指示 Agent：
1. 先 `clear_fragments()`（清舊 data）
2. 讀 Report 2 最新 MD/HTML 決定分析範圍
3. 逐 section 用 `save_fragment()` 生成（每條 Chain 一個 fragment）
4. 最後 `merge_from_fragments()` 合併
5. `send_message` 發送 HTML attachment 到 Discord

Builder script 用法（喺 execute_code 或 terminal 呼叫）：
```python
from hermes_tools import terminal
# 清 fragments
terminal("python3 ~/Investment/reports/report3_builder.py clear")
# Merge all fragments
terminal("python3 ~/Investment/reports/report3_builder.py merge '2026-04-23' 'Risk-On+中性偏寬' '🔥AI/半導體 🔥Memory 🌡️能源'")
```

## Deliver to Discord

HTML 版本（推薦，同 Report 1/2 Fathom 風格）：
```
send_message(target="discord:1495805538003583006", message="Report 3 — 個股 + ETF 深度操作（{date}）\nMEDIA:~/Investment/reports/daily_report3_stock_analysis.html")
```

#investment channel：`discord:1495805538003583006`
