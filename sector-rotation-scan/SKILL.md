---
name: sector-rotation-scan
description: Scan US stock sectors for rotation signals, temperature mapping, and hidden gem identification using yfinance and matplotlib.
category: research
---

# Sector Rotation Scan

Generate sector temperature maps, value chain heat maps, and hidden gem analysis for US stock sectors.

## When to Use

- User asks about sector opportunities, rotation, or "what's hot"
- User wants to find "warm" sectors for positioning before the move
- User wants visual sector analysis charts

## Data Sources

- **yfinance** — price momentum, fundamentals (P/E, PEG, revenue growth, margins)
- **TradingKey API** — AI stock scoring, multi-dimensional analysis, analyst ratings (see tradingkey skill for full endpoint docs)
- Macro context: VIX from yfinance, weekly report from TradingKey

## Sector Temperature Classification

Classify by % from 52-week high:
- HOT: < 5% from 52H — Near ATH, may be overheated
- WARM: 5-15% from 52H — Has momentum, still has room
- COOL: 15-25% from 52H — In between
- COLD: > 25% from 52H — No capital attention

## Scan Metrics Per Symbol

- Current price, 1W%, 1M%, 3M% change
- % from 52-week high
- Volume ratio (5d avg / 20d avg) — flag if > 1.3
- Fundamentals: forward P/E, PEG, revenue growth, profit margin

## Value Chain Mapping (AI/Semi)

Cloud Capex (MSFT/GOOG/AMZN/META) → GPU (NVDA/AMD) → Foundry (TSM) → Equipment (ASML/AMAT/LRCX) → Memory (MU/SNDK) → Networking (AVGO/MRVL) → Optical (LITE/AAOI/COHR)

## Karson's Investment Framework (MUST check before recommendations)

- **Identity:** Macro/Regime-driven, NOT stock picker. Uses time × structure × probability.
- **Three layers:** ETH (optionality) / PMCC (low-freq engine, Short Call = right not obligation) / Safety (life OS)
- **Regime Matrix:** A(VIX≥25,F&G≤20)→LEAP↑ Call OFF / B(20-25)→HOLD / C(15-20)→Call ON Δ0.15-0.25 / D(Extreme Greed)→Reduce
- **Blacklist:** 0DTE / Follow KOL picks as core strategy / All-in bets / Prove-yourself trades / FOMO / Sell Call just for income
- **KOL rule:** Learn APPROACH/PSYCHOLOGY from KOLs (experienced players), stay objective (show wins hide losses), take as reference
- **Style:** Swing + Buy&Hold, NOT day trading
- **Goal:** Never need to endure a system he doesn't respect. 50K = psychological milestone not KPI.

## Hidden Gem Criteria

Within a hot/warm sector, find stocks with:
- TradingKey Score ≥ 7.5 (use `/quotes-base/diagnosis/v1/stock-score?route=nasdaq-{SYM}`)
- Strong momentum within sector (LEADER or strong #2, NEVER laggard — POET lesson)
- Lower PEG than sector peers (< 1 preferred)
- Higher revenue growth than peers
- Price has NOT yet caught up to sector momentum
- NOT already at 52W high (warm, not hot)

## Matplotlib Chart Generation — CRITICAL WORKAROUND

**Problem:** `execute_code` sandbox cannot install packages (externally-managed-environment).

**Solution:**
1. `pip install matplotlib --break-system-packages -q` (via terminal)
2. Write chart script to `/tmp/gen_charts.py`
3. Run via `terminal()` — NOT `execute_code()`
4. Save to `/tmp/chart_*.png`
5. Send via `send_message()` with `MEDIA:/tmp/chart_*.png`

Dark theme: `plt.style.use('dark_background')`, facecolor `#0f0f23`

## Output Format (Discord)

Discord text is hard to read for dense data. Always generate image charts.

1. Macro Regime header (VIX, regime A/B/C/D, SPY/QQQ status)
2. Sector Temperature Map (chart image)
3. Value Chain Heat Map (chart image)
4. Hidden Gem Analysis with TradingKey scores (chart + text)
5. TradingKey Score Dashboard (4-panel chart)
6. Rotation Risk warnings
7. Actionable picks with WARM/HOT/COLD labels + TradingKey rating/target

Send charts via `send_message()` with `MEDIA:/tmp/chart_*.png`.

## Key Lessons

- Don't chase HOT sectors — look for WARM with good fundamentals
- Within hot sector, pick LEADER or strong #2, never laggard (POET lesson: Karson held sector laggard while peers ran +168%)
- PEG < 1 in warm sector = potential hidden gem (MU PEG 0.26 vs SNDK ~1.5, SNDK ran +139% but MU fundamentals better)
- "Cheap relative to past high" != "good value" (anchoring bias — RGTI lesson)
- **Selection > Effort** — picking the right sector matters more than researching the wrong one deeply
- **Don't wait for "perfect pullback"** — hot sectors may never pull back (Memory sector: SNDK/MU kept climbing). Use tiered entry (buy 1/3, add if continues)
- **AI value chain money flow is predictable** — Cloud Capex → GPU → Equipment → Memory → Networking → Optical. If one layer is hot, the NEXT layer may warm up.
- **Don't follow AI price predictions** — Karson was burned by Copilot giving confident price targets (8.07-8.14) then making up post-hoc rationalizations. No price targets. Only regime-based direction.
- **MU vs SNDK case study** — peer within same sector can have drastically different performance. Always compare fundamentals (PEG, revenue growth) not just sector label.
