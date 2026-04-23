---
name: portfolio-charter-review
description: Analyze a user's portfolio holdings against their personal investment charter/framework to identify behavioral contradictions, concentration risks, and alignment gaps
category: research
triggers:
  - "portfolio review"
  - "holdings analysis"
  - "check my positions against my framework"
  - "am I following my investment rules"
  - "investment charter check"
  - "portfolio alignment"
---

# Portfolio Charter Review

Cross-reference a user's actual portfolio holdings against their personal investment charter/framework to identify behavioral contradictions, concentration risks, and alignment gaps.

## When to Use
- User shares their portfolio (CSV, list, or description) and wants holistic review
- User has an investment charter/identity document and wants to check if holdings match
- User asks "am I following my own rules?"
- Periodic portfolio audit against investment principles

## Prerequisites
- User's investment charter/framework documents (saved in `~/.hermes/investment-framework/` or similar)
- Portfolio holdings data (broker CSV export, or user-provided list)

## Workflow

### 1. Load Investment Charter
Read the user's investment framework documents:
- Investment Identity (who they are as investor)
- Allowed/Forbidden Behaviors (what they can/cannot do)
- Asset role definitions (e.g., ETH = optionality, PMCC = engine, safety layer = life OS)
- Macro regime behavior matrix
- Ultimate goals and exit conditions

Key files typically at: `~/.hermes/investment-framework/`

### 2. Parse Portfolio Holdings
From broker CSV or user description, extract:
- Ticker/symbol, quantity, current price, cost basis
- P/L (percentage and absolute)
- Asset type (stock, ETF, options)
- Currency if multi-currency

Calculate:
- Total portfolio value
- Total unrealized P/L
- Category/sector grouping
- Concentration percentages
- Biggest winners and losers

### 3. Charter Alignment Check
For EACH holding, ask:
- Is this position consistent with the user's stated investment identity?
- Does it violate any items in the forbidden list?
- Does it fit the defined asset role (e.g., is it macro-driven or speculative?)
- Is the risk profile appropriate for the user's stated risk tolerance?

Present as:
| Holding | Charter Alignment | Issue |
|---------|------------------|-------|
| TTD (-47%) | ⚠️ Single stock bet vs macro-driven identity | Thesis still valid? |
| RGTI 30C (-91%) | 🔴 Near forbidden list (short DTE speculative) | Consider closing |

### 4. Behavioral Contradiction Detection
Look for patterns:
- **Identity drift**: User says "macro/systematic" but holds speculative single stocks
- **Sunk cost holding**: Deep losers kept without clear macro thesis
- **Risk mismatch**: Position risk profile contradicts stated risk tolerance
- **Concentration risk**: Too much in one sector/theme without intentional allocation
- **Winner/loser ratio**: If only one position wins, that may indicate where their edge actually is

### 5. Honest, Direct Assessment
Per user preference: be objective, don't just flatter.
- State contradictions clearly
- Show the data (numbers don't lie)
- Reference specific charter clauses
- Offer actionable recommendations ranked by priority

### 6. Recommendations
Prioritize by:
1. Positions near/breaching forbidden list → immediate attention
2. Deep losers without thesis → evaluate exit
3. Identity contradictions → rebalance direction
4. Concentration adjustments → gradual

## Multi-Currency Note
Some users (e.g., HK-based) have both HKD and USD positions. Convert to single currency for analysis (use ~7.8 HKD/USD or current rate). Show both original and converted values.

## Pitfalls
- Don't assume you know the user's cost basis — confirm estimates or ask
- CSV exports may have BOM characters; handle encoding issues
- Options positions (spreads, PMCC) may appear as separate legs; group them logically
- "Holding because I don't want to realize loss" is common — surface it gently but directly
- User's charter may contradict itself — flag internal inconsistencies too
- Sandbox doesn't persist imports — always re-import pandas/yfinance
