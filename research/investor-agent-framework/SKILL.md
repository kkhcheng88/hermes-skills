---
name: investor-agent-framework
description: Create structured investor/analyst agent prompt files with consistent structure — hard gates, falsification conditions, steelman, confidence calibration, and structured output. Use when building new analyst agents for stock screening or investment analysis.
version: 1.0.0
author: Kars (Hermes Agent)
tags: [investment, agent, framework, screening, analysis]
related_skills: [cio-repo-management, stock-analysis, tradingkey]
---

# Investor Agent Framework Builder

Create structured analyst agent prompt files following the FinceptTerminal pattern, adapted for Karson's Investment repo (`~/Investment/agents/`).

## When to Use
- Adding a new investor/analyst agent to the agent library
- Karson references a new investment methodology to encode
- Creating KOL agent templates

## Directory Structure
- Investor agents: `~/Investment/agents/investors/AGENT_{NAME}.md`
- KOL agents: `~/Investment/agents/KOL/AGENT_{NAME}.md`
- Index: `~/Investment/agents/AGENT_INDEX.md` (update when adding new agents)

## Agent File Template (6 Sections)

Every agent file MUST follow this structure:

### 1. Header +定位
- Which tier: 🥇首選 / 🥈輔助 / 🔧特殊用途
- Core philosophy (one quote from the investor)
- Applicable regime / conditions (when to use, when NOT to use)

### 2. Quantitative Hard Gates
- Specific numeric thresholds (PEG ≤ 1.0, ROC ≥ 15%, MoS ≥ 40%, etc.)
- ANY fail = reject (strict binary)
- Include formula definitions

### 3. Qualitative Tests
- Explain in plain Cantonese what each concept actually means
- Provide good vs bad examples (表格對比)
- Map to Karson's known lessons (e.g., POET laggard trap)

### 4. DO NOT (禁止清單)
- Explicit prohibitions
- Common failure modes

### 5. Falsification Condition + Confidence Calibration
- What evidence would overturn the bullish thesis
- Tiered confidence: High (0.7-0.9) / Medium (0.5-0.7) / Low (0.3-0.5) / Reject

### 6. Structured Output Template
- Consistent `## {Agent} 判斷` section
- Each field labeled with pass/fail indicator

## Naming Conventions
- Use descriptive regime names (極度恐慌/修復期/正常/極度貪婪), NOT ABCD letters
- Avoid cross-referencing between agent files — each should be self-contained
- Use Traditional Chinese (繁體中文) with English technical terms

## Pitfalls
- Don't create agents that duplicate existing ones — check `AGENT_INDEX.md` first
- Buffett-style (>5yr) agents should be marked as reference only, not primary
- Always include `Falsification Condition` — agents without it are incomplete
- Markdown tables use single `|`, never `||`
