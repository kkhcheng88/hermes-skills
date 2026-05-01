---
name: stock-analysis
description: "Ad-hoc stock analysis: yfinance + ta + TradingKey (mandatory) + Agent frameworks (Lynch/Marks/Miller/Munger/Greenblatt). 5-layer pipeline for US stocks. Buy&hold ≤1yr."
version: 2.0.0
metadata:
  hermes:
    tags: [stocks, analysis, technical-analysis, fundamentals, yfinance, ta, options]
---

# Stock Analysis Pipeline

Ad-hoc stock analysis for any US ticker. 5-layer pipeline developed through iterative testing on AXTI, TSLA, MU, POET, AAOI, PFE, LLY, INTC.

Part of Karson's **Top-Down Workflow (MVP1)**:
- **Layer 1 (Macro)** → use `reports/` daily report for Regime context before analyzing any stock
- **Layer 2 (Sector)** → check Sector Temperature + Value Chain position before individual stock
- **Layer 3 (Stock)** → THIS SKILL. Apply 5-layer pipeline.

Full Agent Framework library: `~/Investment/agents/investors/` (11 agents as detailed .md files). Load relevant agent files for deeper analysis beyond the summary in this skill.

## Dependencies

```bash
pip install --break-system-packages yfinance ta beautifulsoup4 requests
```

## Pipeline (5 Layers — ALL mandatory)

### Layer 1: yfinance — Price, Fundamentals & Technicals

```python
import yfinance as yf
import ta

t = yf.Ticker("SYMBOL")
info = t.info
hist = t.history(period="1y")  # 1y for enough MA data
close, high, low = hist['Close'], hist['High'], hist['Low']
current = float(close.iloc[-1])
```

**Extract from `info`:** longName, sector, industry, marketCap, trailingPE, forwardPE, priceToBook, totalRevenue, grossMargins, profitMargins, operatingMargins, returnOnEquity, debtToEquity, currentRatio, freeCashflow, revenueGrowth, earningsGrowth, recommendationKey, targetMeanPrice/High/Low, numberOfAnalystOpinions, fiftyTwoWeekHigh/Low, averageVolume.

**Technical indicators (ta library):**
```python
rsi = ta.momentum.RSIIndicator(close, 14).rsi().iloc[-1]
macd = ta.trend.MACD(close)
macd_cross = "golden" if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] else "death"
bb = ta.volatility.BollingerBands(close, 20)
bb_pos = (current - bb.bollinger_lband().iloc[-1]) / (bb.bollinger_hband().iloc[-1] - bb.bollinger_lband().iloc[-1])
atr = ta.volatility.AverageTrueRange(high, low, close, 14).average_true_range().iloc[-1]
stoch = ta.momentum.StochasticOscillator(high, low, close)
ma20 = float(close.rolling(20).mean().iloc[-1])
ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
recent_low = float(low.tail(20).min())
recent_high = float(high.tail(20).max())
```

### Layer 2: TradingKey — AI Analysis (MANDATORY)

```python
import urllib.request, json

route = f"nasdaq-{symbol.lower()}"
url = f"https://api.tradingkey.com/quotes-base/diagnosis/v1/stock-score?route={route}"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
    'Referer': 'https://www.tradingkey.com/', 'Origin': 'https://www.tradingkey.com',
})
v = json.loads(urllib.request.urlopen(req, timeout=15).read())["value"]
```

> **Note (2026-04-22 verified)**: The correct response key is `v['score']` (not `v['payload']`). The API returns `{"value": {"score": {"totalScore": X, ...}}}`.

**Extract:**
- `v['score']['totalScore']` — 0-10 composite
- `v['score']['industryRank']` / `marketRank` — rankings
- 6 dimension scores: revenueForecasts, financialDiagnostics, priceMomentum, riskAssessment, institutionalRecognition, companyValuation
- `v['suggests']['stockSuggest']` — operational recommendation
- `v['labelList']` — highlights (labelType=1) and risks (labelType=2)
- `v['pressure']` / `v['support']` — resistance/support levels
- `v['companySentiment']` — sentiment score and heat
- `v['agencyRating']` — rating, targetPrice, priceSpace, total analysts

**⚠️ TradingKey is mandatory but NOT the bible.** Reference alongside other data. Sometimes its valuation score conflicts with fundamental analysis (e.g., AXTI scored 8.3/10 valuation but stock was 3x analyst target).

### Layer 3: Agent Frameworks (1-year horizon)

Karson's buy & hold horizon = max 1 year. **Buffett framework does NOT apply** (too long-term). Graham too conservative for growth stocks.

**Priority order (Lynch first):**

#### 🥇 Lynch (PEG + Story) — PRIMARY
```python
peg = fwd_pe / (earnings_growth * 100)  # if earnings_growth > 0
# PEG ≤ 1.0 → bullish
# PEG > 1.5 → reject
# No positive earnings → PEG N/A → check story only
```
- Classify: Slow Grower / Stalwart / Fast Grower / Cyclical / Turnaround / Asset Play
- **Story test**: can a non-finance person repeat the thesis in one sentence?
- Cyclicals: use cycle-averaged earnings, not trough PEG

#### 🥈 Marks (Cycle Positioning)
- 6-bucket cycle: early_bull → late_bear
- Second-level thinking: state consensus, then what consensus misses
- **Humility statement mandatory**: name what you DON'T know
- Credit leads equity: HY spreads, default rates

#### 🥈 Miller (Contrarian + FCF)
- Must be currently out-of-favor
- FCF yield (levered, post SBC)
- SBC ≥ 50% of FCF = reject
- Network effects: none/weak/moderate/strong

#### 🥉 Munger (Inversion)
- "How do I lose money?" — 3-5 specific ways
- Lollapalooza check: multiple reinforcing failure factors = high conviction to avoid
- Circle of competence: declining out-of-competence is correct behavior

#### 🥉 Greenblatt (Magic Formula)
- ROC = EBIT / (NWC + net fixed assets) ≥ 15%
- Earnings Yield = EBIT / EV ≥ 8%
- Pure rules-based — narrative does NOT override

**Lower priority (use situationally):**
- Graham — too conservative, rejects almost all growth stocks
- Klarman — only when VIX high / regime A
- Eveillard — bubble check for sectors

### Layer 4: News + Analyst Sentiment

**Multi-source approach (try in order, don't stop at the first empty result):**

```python
# 1. yfinance news (often returns N/A for small-caps)
news = yf.Ticker("SYMBOL").news

# 2. NewsAPI (free tier: 100 req/day, register at https://newsapi.org)
import urllib.request, json, os
api_key = os.environ.get("NEWS_API_KEY", "a211e3c6f30f46fe86948b32c326ee71")
url = f"https://newsapi.org/v2/everything?q={SYMBOL}+stock&apiKey={api_key}&language=en&sortBy=publishedAt&pageSize=15"
arts = json.loads(urllib.request.urlopen(url, timeout=10).read()).get("articles", [])
for a in arts:
    print(f"Title: {a['title']} | Source: {a['source']['name']} | Date: {a['publishedAt'][:10]}")
    print(f"Desc: {a.get('description','')}")

# 3. Google News RSS (no API key needed)
import xml.etree.ElementTree as ET
rss_url = f"https://news.google.com/rss/search?q={SYMBOL}+stock&hl=en-US&gl=US&ceid=US:en"
root = ET.fromstring(urllib.request.urlopen(rss_url, timeout=10).read())
for item in root.findall(".//item")[:10]:
    print(item.find("title").text)
```

**Analyst data (3-step fallback chain):**

```python
# Step 1: yfinance.info (fastest, often sufficient)
info = yf.Ticker("SYMBOL").info
target_mean = info.get("targetMeanPrice")
target_high = info.get("targetHighPrice")
target_low = info.get("targetLowPrice")
rec_key = info.get("recommendationKey")  # e.g. "buy", "hold"
fwd_pe = info.get("forwardPE")
eps_current = info.get("epsCurrentYear")
eps_forward = info.get("epsForward")

# Step 2: NewsAPI for published analyst reports
# (many financial sites publish analyst price targets as news articles)
url2 = f"https://newsapi.org/v2/everything?q={SYMBOL}+analyst+target+price&apiKey={api_key}&language=en&sortBy=relevancy&pageSize=10"

# Step 3: Web scraping (for detailed ratings breakdown)
# Finviz: https://finviz.com/quote.ashx?t=SYMBOL  (no auth needed)
# Extract: "Target Price" pattern, "WallStreet analysts" count, recommendation bars
```

**Small-cap / low-coverage stocks (common patterns):**
- yfinance.news → often returns N/A or empty list
- yfinance.info → analyst fields return N/A
- NewsAPI → may return 0 results for obscure tickers
- yfinance.recommendations endpoint → returns empty
- Yahoo Finance internal API → rate-limited (429) frequently
- Solution: Use NewsAPI as primary, web scraping as backup, accept data gaps

**Analyst sentiment synthesis for moat/regime framework:**
- Classify sentiment per moat dimension (B2/C1 etc.) rather than just overall
- Flag: "現價 > 分析師目標價均值" as a warning signal
- Flag: wide analyst target range ($28-$90) as high uncertainty indicator
- Note: Small-cap stocks often have <5 analyst coverage = not statistically meaningful

## Key Learnings (from testing on 8 stocks)
Cross-reference all layers. Flag conflicts (e.g., TradingKey says buy but agents say avoid).

---

## Options Rules (STRICT — always follow)

- **PMCC** → SPY ONLY
- **CSP systematic** → QQQ ONLY
- **Sell Put (individual stocks)** → ALL 3 conditions must be met:
  1. IV is high (good premium)
  2. Genuinely want to own the stock (willing to be assigned)
  3. Premium justifies the risk
- For non-SPY/QQQ: show options chain data but DON'T recommend PMCC/CSP

---

## Analysis Output Format

```
📊 [SYMBOL] — [Company Name] | $[Price] | MCap: $[X]B/M

【Lynch — PEG + Story】
  分類: [Fast Grower/Cyclical/Turnaround/etc.]
  PEG: [X.XX] ✅/❌
  Story test: [one sentence thesis]
  Verdict: [BULLISH/NEUTRAL/REJECT]

【Marks — Cycle】
  Cycle: [bucket position]
  Key signals: [...]
  Second-level: [what consensus misses]
  Humility: [what I don't know]
  Verdict: [...]

【Miller — Contrarian + FCF】
  Contrarian test: [yes/no]
  FCF yield: [X.X%]
  Verdict: [...]

【Munger — Inversion】
  How to lose money: [3-5 ways]
  Lollapalooza: [X/5 factors]
  Verdict: [...]

【Greenblatt — Magic Formula】
  ROC: [X%] | EY: [X%]
  Verdict: [...]

⭐ TradingKey: [X.XX/10] | 行業 [X/Y] | 市場 [X/Y]
  Highlights: [...]
  Risks: [...]
  Analyst: [Rating] | PT: $[X] | 空間: [X%]

📐 技術面: RSI [X] | MACD [cross] | 趨勢 [up/down]
  支撐: $[X] | 壓力: $[X]

🎯 最終 Verdict + 行動建議
```

---

## Key Learnings (from testing on 8 stocks)

| Stock | Lesson |
|-------|--------|
| AXTI | Story was stronger than agent frameworks suggested — TradingKey caught what yfinance missed ($1.2→$78 momentum has AI optical interconnect story) |
| AAOI | Similar to AXTI but with real revenue ($455M). Institutional SELLING while retail buys = late cycle signal |
| TSLA | 8/10 agents reject at current valuation. Only Lynch story test passes. Wait for $200 |
| MU | Lynch PEG 0.02 + Greenblatt top rank. Best quantitative score. But DRAM cycle risk — watch spot price |
| PFE | Miller contrarian FCF yield 8.6%. Value trap risk if no catalyst. Seagen pipeline = potential re-rate |
| LLY | Lynch PEG 0.42 = best GARP score in the group. GLP-1 mid-cycle adoption |

**Pattern discovered:** For AI/semiconductor supply chain stocks (AXTI, AAOI, POET), traditional value frameworks (Buffett, Graham, Greenblatt) all reject them, but Lynch story test + Marks cycle positioning capture the opportunity. Must supplement with TradingKey to catch the narrative.
