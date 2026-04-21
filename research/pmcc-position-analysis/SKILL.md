---
name: pmcc-position-analysis
description: Analyze PMCC (Poor Man's Covered Call) positions with live options data, regime assessment, and scenario modeling
category: research
triggers:
  - "PMCC analysis"
  - "options position review"
  - "short call should I close"
  - "LEAP + short call"
---

# PMCC Position Analysis

Analyze Poor Man's Covered Call (PMCC) positions using real-time options data, regime assessment, and scenario modeling.

## When to Use
- User shares a PMCC position (Long LEAP + Short Call) and wants analysis
- User asks whether to close/roll/hold a Short Call
- User wants scenario analysis for their options position

## Workflow

### 1. Gather Position Data
Ask or confirm:
- Long LEAP: underlying, expiry, strike, estimated cost basis
- Short Call: underlying, expiry, strike, sell price, DTE
- Current market context (VIX, recent momentum)

### 2. Pull Live Data with yfinance
```python
import yfinance as yf
from datetime import datetime

spy = yf.Ticker("SPY")
chain = spy.option_chain("YYYY-MM-DD")
```
- Get bid/ask for both legs
- Calculate intrinsic value = max(SPY - LEAP strike, 0)
- Calculate extrinsic value = LEAP ask - intrinsic
- Get SC current ask, calculate unrealized loss

### 3. Momentum vs Strike Check
- Calculate required daily move to reach SC strike
- Compare with recent actual daily move
- Flag if momentum is faster than needed

### 4. Scenario Analysis Table
Build table at SC expiry with SPY scenarios (±5%, flat, at strike, past strike):
- LEAP value estimate (intrinsic + time-adjusted extrinsic)
- LEAP P/L vs cost basis
- SC P/L (premium received - intrinsic loss)
- Net P/L
- Cap status (whether SC gets assigned)

### 5. Regime Assessment
Map VIX/Fear & Greed to regime:
- A (VIX ≥25-30, F&G ≤20): LEAP add, SC OFF
- B (VIX 20-25, F&G 30-50): LEAP hold, SC optional
- C (VIX 15-20, F&G 50-70): SC ON (Δ 0.15-0.25)
- D (Extreme Greed): reduce exposure

Assess whether SC timing was regime-appropriate vs speed mismatch.

### 6. Recommendation
- If SC brings stress disproportionate to premium → recommend close SC only
- Calculate exact buyback cost and realized loss
- Compare SC loss vs LEAP unrealized gain to show proportionality
- Suggest future SC conditions (min VIX, min % OTM, min premium)

## Key Insights from Experience
- VIX 18-20 = thin premium environment; SC premiums may not compensate for cap risk
- SPX can move faster than regime suggests (speed mismatch vs system violation)
- If 99% of returns come from LEAP, SC component may not be worth the psychological cost
- User's "Short Call = right, not obligation" principle means SC OFF should be default state
- Small SC loss to close is noise vs LEAP gain — don't let sunk cost prevent good decisions

## Pitfalls
- Don't estimate LEAP cost basis without asking — confirm with user
- yfinance options data may not have exact strikes; find nearest available
- Extrinsic value decays non-linearly; simple time-ratio is rough estimate
- Sandbox environment doesn't persist imports — always re-import yfinance

## Lessons Learned (2026-04-20 Session)
- **VIX 18-20 is a thin premium environment**: When VIX compresses from 29→18, SC premiums are shallow ($1.90 for 45DTE 4% OTM on SPY). Risk/reward is poor — small cap income vs large upside sacrifice.
- **Speed mismatch vs system violation**: SPX rallying from 200MA to ATH in 2 weeks is faster than regime B→C transition implies. This is a timing issue, not a character flaw. Differentiate clearly.
- **Proportionality test**: If SC P/L is <2% of LEAP P/L, the SC component may not justify its psychological cost. Show this ratio to the user.
- **SC default state should be OFF**: Per user's charter "Short Call = right, not obligation", the default should be no SC unless specific conditions are met (VIX ≥22-25, strike ≥8-10% OTM, user genuinely wants income).
- **Momentum projection**: Always calculate required daily move to SC strike vs recent actual daily move. If actual >> required, flag proactively.
