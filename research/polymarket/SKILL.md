---
name: polymarket
description: Query Polymarket prediction market data — search markets, get prices, orderbooks, and price history. Read-only via public REST APIs, no API key needed.
version: 1.0.0
author: Hermes Agent + Teknium
tags: [polymarket, prediction-markets, market-data, trading]
---

# Polymarket — Prediction Market Data

Query prediction market data from Polymarket using their public REST APIs.
All endpoints are read-only and require zero authentication.

See `references/api-endpoints.md` for the full endpoint reference with curl examples.

## When to Use

- User asks about prediction markets, betting odds, or event probabilities
- User wants to know "what are the odds of X happening?"
- User asks about Polymarket specifically
- User wants market prices, orderbook data, or price history
- User asks to monitor or track prediction market movements

## Key Concepts

- **Events** contain one or more **Markets** (1:many relationship)
- **Markets** are binary outcomes with Yes/No prices between 0.00 and 1.00
- Prices ARE probabilities: price 0.65 means the market thinks 65% likely
- `outcomePrices` field: JSON-encoded array like `["0.80", "0.20"]`
- `clobTokenIds` field: JSON-encoded array of two token IDs [Yes, No] for price/book queries
- `conditionId` field: hex string used for price history queries
- Volume is in USDC (US dollars)

## Three Public APIs

1. **Gamma API** at `gamma-api.polymarket.com` — Discovery, search, browsing
2. **CLOB API** at `clob.polymarket.com` — Real-time prices, orderbooks, history
3. **Data API** at `data-api.polymarket.com` — Trades, open interest

## Typical Workflow

When a user asks about prediction market odds:

1. **Search** using the Gamma API public-search endpoint with their query
2. **Parse** the response — extract events and their nested markets
3. **Present** market question, current prices as percentages, and volume
4. **Deep dive** if asked — use clobTokenIds for orderbook, conditionId for history

## Presenting Results

Format prices as percentages for readability:
- outcomePrices `["0.652", "0.348"]` becomes "Yes: 65.2%, No: 34.8%"
- Always show the market question and probability
- Include volume when available

Example: `"Will X happen?" — 65.2% Yes ($1.2M volume)`

## Parsing Double-Encoded Fields

The Gamma API returns `outcomePrices`, `outcomes`, and `clobTokenIds` as JSON strings
inside JSON responses (double-encoded). When processing with Python, parse them with
`json.loads(market['outcomePrices'])` to get the actual array.

## Rate Limits

Generous — unlikely to hit for normal usage:
- Gamma: 4,000 requests per 10 seconds (general)
- CLOB: 9,000 requests per 10 seconds (general)
- Data: 1,000 requests per 10 seconds (general)

## Pitfalls

- **Search endpoint**: Use `/public-search?q=QUERY` NOT `/events?title=QUERY`. The `title` parameter returns irrelevant results.
- **Correct pattern**: `GET https://gamma-api.polymarket.com/public-search?q=fed+rate`
- **Wrong pattern**: `GET https://gamma-api.polymarket.com/events?title=fed+rate` — returns unrelated events

## Limitations

- This skill is read-only — it does not support placing trades
- Trading requires wallet-based crypto authentication (EIP-712 signatures)
- Some new markets may have empty price history
- Geographic restrictions apply to trading but read-only data is globally accessible

## API Issues & Workarounds (Discovered 2026-04-26)

### Gamma API Search Broken
- `?_s=iran` and `/search?query=iran` endpoints return irrelevant results (MicroStrategy, Kraken IPO, etc.)
- Tag-based filtering (`?tag=politics`) works but returns generic events, not topic-specific
- **Workaround**: Use browser to load homepage, extract data from snapshot

### CLOB API Returns Stale Data
- `/markets` endpoint returns 1000+ old sports markets from 2023
- Not useful for current prediction market data
- **Workaround**: Use Gamma API events endpoint or browser snapshot

### Homepage Snapshot Contains Live Data
When APIs fail, navigate to `https://polymarket.com/` and extract from snapshot:
- Featured markets carousel shows current hot topics (Iran peace deal, etc.)
- Breaking news section shows trending markets with probabilities
- Example: "US x Iran permanent peace deal by June 30: 48%" visible in snapshot

### Geo-Blocking
- Website may show error page ("Go to home" button) for certain regions
- API endpoints still work for read-only access
- If both fail, use alternative data sources (TradingKey macro events, FedWatch)
