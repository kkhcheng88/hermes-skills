---
name: stock-analysis
description: "Ad-hoc stock analysis: yfinance + ta + TradingKey (mandatory) + Agent frameworks (Lynch/Marks/Miller/Munger/Greenblatt). 5-layer pipeline for US stocks. Buy&hold ≤1yr."
version: 1.0.0
metadata:
  hermes:
    tags: [stocks, analysis, technical-analysis, fundamentals, yfinance, ta, options]
---

# Stock Analysis (yfinance + ta)

Ad-hoc stock analysis for any ticker. Uses `yfinance` for data and `ta` library for technical indicators.

## Dependencies

```bash
pip install yfinance ta
```

## Pipeline (5 layers)

### Layer 1: yfinance — Price & Fundamentals
Use `yf.Ticker("SYMBOL")` for company info, fundamentals, analyst consensus, options chain.

### Layer 2: ta library — Technical Indicators
RSI, MACD, Bollinger Bands, ATR, Stochastic, MA20/MA50 cross, support/resistance.

### Layer 3: TradingKey — AI Analysis (MANDATORY reference)

```python
import urllib.request, json

route = f"nasdaq-{symbol.lower()}"
url = f"https://api.tradingkey.com/quotes-base/diagnosis/v1/stock-score?route={route}"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'Referer': 'https://www.tradingkey.com/',
    'Origin': 'https://www.tradingkey.com',
})
data = json.loads(urllib.request.urlopen(req, timeout=15).read())["value"]
```

Extract: totalScore, industryRank, 6 dimension scores + descriptions, highlights/risks (labelList), support/resistance, sentiment, analyst rating, operational suggestion.

**TradingKey is mandatory but not the bible** — reference alongside other data, don't treat as sole source of truth.

### Layer 4: Agent Frameworks (FinceptTerminal-inspired)

Karson's buy & hold horizon = max 1 year. Buffett long-term framework NOT applicable.

**Priority order:**
1. **Lynch (PEG + Story)** — PRIMARY. PEG = fwd P/E ÷ EPS growth. ≤1.0 bullish, >1.5 reject. Story test: can non-finance person repeat thesis?
2. **Marks (Cycle)** — 6-bucket cycle positioning. Second-level thinking. Humility statement.
3. **Miller (Contrarian + FCF)** — out-of-favor test, FCF yield, SBC/FCF <50%.
4. **Munger (Inversion)** — "how to lose money?" 3-5 ways, lollapalooza check.
5. **Greenblatt (Magic Formula)** — ROC ≥15%, EY ≥8%, pure rules-based.

Lower priority: Graham (too conservative), Klarman (VIX high only), Buffett (horizon too long).

### Layer 5: News
yfinance `t.news` + Google News RSS for recent coverage.

## Analysis Output Structure

```
📊 [SYMBOL] 完整分析

🏢 公司簡介
  名稱, Sector, Industry, 市值, 員工數

📈 股價資訊
  現價, 52週高/低, 50MA, 200MA

💰 基本面
  P/E (TTM + Forward), P/B, Revenue, Gross/Net Margin, Debt/Equity, Current Ratio

🎯 Analyst 共識
  Recommendation, Mean/High/Low PT, # Analysts

📐 技術分析
  RSI(14), MACD + Signal + 金叉/死叉, Bollinger Bands (Upper/Middle/Lower)
  ATR(14), Stochastic K/D
  支撐/壓力 (20日), MA20/MA50 趨勢, 黃金交叉/死亡交叉

📋 期權鏈 (如適用)
  最近 3 個到期日嘅 ATM calls — Bid/Ask/IV/Volume
```

## Code Template

```python
import yfinance as yf
import pandas as pd
import ta

ticker = yf.Ticker("SYMBOL")
info = ticker.info
hist = ticker.history(period="6mo")

# Fundamentals from info dict
price = info.get('currentPrice', info.get('regularMarketPrice'))
pe = info.get('trailingPE')
fpe = info.get('forwardPE')
pb = info.get('priceToBook')
revenue = info.get('totalRevenue', 0) / 1e6
gross_margin = info.get('grossMargins', 0) * 100
net_margin = info.get('profitMargins', 0) * 100
de_ratio = info.get('debtToEquity')

# Technical analysis
close = hist['Close']
high = hist['High']
low = hist['Low']
current = float(close.iloc[-1])

rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
macd_ind = ta.trend.MACD(close)
macd_val = macd_ind.macd().iloc[-1]
signal_val = macd_ind.macd_signal().iloc[-1]
bb = ta.volatility.BollingerBands(close, window=20)
atr = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1]
stoch = ta.momentum.StochasticOscillator(high, low, close)

# Support/Resistance
recent_low = float(low.tail(20).min())
recent_high = float(high.tail(20).max())
ma20 = float(close.rolling(20).mean().iloc[-1])
ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
```

## Karson's Option Rules (ALWAYS FOLLOW)

- **PMCC** → SPY only
- **CSP systematic** → QQQ only
- **Sell Put (其他股)** → ONLY when all 3 conditions met:
  1. IV is high (good premium)
  2. He actually wants to own the stock (willing to be assigned)
  3. Premium justifies the risk
- For non-SPY/QQQ stocks: show options data but don't recommend PMCC/CSP unless conditions met

## ta Library Quick Reference

| Indicator | Code | Interpretation |
|-----------|------|----------------|
| RSI(14) | `ta.momentum.RSIIndicator(close, 14).rsi()` | >70 overbought, <30 oversold |
| MACD | `ta.trend.MACD(close)` | `.macd()`, `.macd_signal()`, `.macd_diff()` |
| Bollinger | `ta.volatility.BollingerBands(close, 20)` | `.bollinger_hband()`, `.bollinger_mavg()`, `.bollinger_lband()` |
| ATR | `ta.volatility.AverageTrueRange(high, low, close, 14)` | `.average_true_range()` — volatility measure |
| Stochastic | `ta.momentum.StochasticOscillator(high, low, close)` | `.stoch()`, `.stoch_signal()` |
| SMA | `close.rolling(N).mean()` | Simple moving average |
| EMA | `ta.trend.EMAIndicator(close, N).ema_indicator()` | Exponential moving average |
