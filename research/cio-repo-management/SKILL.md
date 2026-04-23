---
name: cio-repo-management
description: Manage Karson's Investment repo (CIO Framework) — pull, read, analyze, edit, and push back to GitHub. Use when Karson wants to update investment charter files, review CIO framework docs, or sync the repo.
version: 1.0.0
author: Kars (Hermes Agent)
tags: [investment, CIO, GitHub, framework, charter]
related_skills: [portfolio-charter-review, stock-analysis, tradingkey, polymarket]
---

# CIO Investment Repo Management

Manage Karson's private Investment repo at `github.com/kkhcheng88/Investment`, cloned at `~/Investment`.

## When to Use
- Karson says "update the repo" or "改埋呢D and push"
- Karson shares new investment insights that should be incorporated into the CIO framework
- Karson asks to review or compare repo files with current understanding
- Periodic sync to pull latest changes Karson made from other devices

## Prerequisites
- GitHub auth configured (see github-auth skill)
- Repo cloned at `~/Investment`
- Git identity: `Kars (Hermes Agent)` / `kkhcheng88@users.noreply.github.com`

## Repo Structure

```
~/Investment/
├── ARCHITECTURE.md              # System architecture for CIO Agent
├── README.md
├── knowledge/
│   ├── CIO_CHARTER.md           # Investment charter (blacklist, asset roles, psychological gates, exit conditions, 50K definition)
│   ├── CIO_REGIME.md            # Macro Regime Matrix (Risk Appetite × Monetary Environment 寬鬆/中性/收緊)
│   ├── CIO_STRATEGIES.md        # Strategy toolbox (PMCC, Direct Equity, Sector ETF, Defensive) + risk management
│   ├── CIO_SECTOR_TEMPERATURE.md # 3-layer sector scoring (0-9) → ❄️/🌤️/🔥/🌡️
│   ├── CIO_KNOWLEDGE.md         # Master index — entry point for all files
│   ├── CIO_WATCHLIST.md         # Current monitoring status, watchlist, position tracking
│   ├── CIO_JOURNAL.md           # Trade journal, behavioral review, lessons
│   └── chains/
│       ├── CIO_VC_INDEX.md      # Value Chain index + maintenance rules
│       ├── CIO_VC_AI_SEMICONDUCTOR.md  # AI/Semi chain (no HBM — belongs to Memory chain)
│       ├── CIO_VC_OPTICAL.md
│       ├── CIO_VC_MEMORY.md     # Memory chain (includes HBM)
│       ├── CIO_VC_ENERGY.md
│       ├── CIO_VC_PRECIOUS_METALS.md
│       ├── CIO_VC_NUCLEAR.md
│       ├── CIO_VC_CYBERSECURITY.md
│       ├── CIO_VC_GLP1.md
│       ├── CIO_VC_RESHORING.md
│       └── CIO_VC_QUANTUM.md
└── agents/
    ├── AGENT_INDEX.md           # Agent library index + Regime × Agent mapping
    ├── investors/               # 11 Trader/Investor agent frameworks
    │   ├── AGENT_LYNCH.md       # 🥇 PEG + Story Test (primary)
    │   ├── AGENT_MARKS.md       # 🥇 Cycle Positioning + Second-Level Thinking (primary)
    │   ├── AGENT_GREENBLATT.md  # 🥈 Magic Formula (ROC + EY ranking)
    │   ├── AGENT_MUNGER.md      # 🥈 Inversion + Mental Models
    │   ├── AGENT_MILLER.md      # 🥈 Contrarian + FCF (SBC check)
    │   ├── AGENT_KLARMAN.md     # 🔧 Downside First + 40% MoS (extreme fear only)
    │   ├── AGENT_BUFFETT.md     # 🔧 Moat + Owner Earnings (>5yr reference)
    │   ├── AGENT_GRAHAM.md      # 🔧 Hard Quantitative Screens
    │   ├── AGENT_EINHORN.md     # 🔧 Catalyst + Forensic Accounting
    │   ├── AGENT_EVEILLARD.md   # 🔧 Global Value + Bubble Avoidance
    │   └── AGENT_WHITMAN.md     # 🔧 Distressed / Credit First
    └── KOL/                     # KOL agents (placeholder,待建)
        └── README.md
```

## Workflow

### 1. Pull Latest
```bash
cd ~/Investment && git pull origin master
```

### 2. Read & Analyze
- Read relevant files based on what Karson wants to update
- Always cross-reference with Kars' memory and fact_store for consistency
- Flag contradictions or gaps between repo and current understanding

### 3. Edit Files
- Use `patch` tool for targeted edits (not sed/awk)
- Maintain markdown table formatting (single `|` for tables, not `||`)
- Update changelog at bottom of each modified file with date + description
- Section numbering must stay consistent (renumber when inserting sections)

### 4. Commit & Push
Use gh CLI or git — see github-auth skill for authentication setup.

## Adding a New Lesson Learned

When Karson shares a new investment lesson/mistake, follow this **4-file update pattern** to ensure it's permanently embedded:

### Step 1: CIO_CHARTER.md — 歷史教訓庫
- Add as `### 教訓 #N — [標題]` under 「五、歷史教訓庫」section
- Required fields: 情境、錯誤本質、CIO 規則（actionable rule, not just description）
- Rules must be checkable — CIO should be able to verify compliance with a yes/no question
- Update changelog at bottom

### Step 2: CIO_JOURNAL.md — 教訓提煉區
- Add formal覆盤 entry under 「教訓提煉區」
- Required fields: 日期、標的、情境、錯誤本質、CIO 規則、心理覆盤、行為模式
- 行為模式 should describe the repeating pattern (e.g., 入場 → Drawdown → 止損 → 火箭升)

### Step 3: CIO_CHARTER.md Blacklist — 檢查是否需要更新
- Review the Blacklist section (「四、永久禁止清單」) — does this lesson warrant a new blacklist entry?
- Examples: IPO 首日交易 (Lesson #5), 0DTE/超短期 options (Lesson #4)
- If yes, add with brief reason referencing the lesson
- Not every lesson needs a blacklist entry — only behavioral patterns, not one-off mistakes

### Step 4: fact_store — Persistent Reminder
- Add fact with entity `Karson investment lessons` so it surfaces in future sessions
- Tags: `investment,lesson,cio-charter`

### Step 5: Commit & Push
- Commit message format: `feat: add Lesson #N [title]`
- Include summary of all files changed
- Always push immediately after commit — Karson accesses repo from multiple devices

### Step 6: Verify Blacklist & Rule Consistency
- After adding a new lesson + CIO rule, check that existing lessons don't contradict the new rule
- If the new rule is a generalization of an older rule (e.g., "IPO first-day ban" generalizes "event-driven trade ban"), note the relationship

### Current Lessons (as of 2026-04-23)
| # | Title | Core Rule |
|---|-------|-----------|
| 1 | POET Laggard Trap | Sector 啱 ≠ 個股啱，Warm sector 只選 leader |
| 2 | RGTI Cold Sector Hope | 唔喺 cold sector 等待 warming（偵測 ≠ 預測） |
| 3 | POET Long Option Trap | 禁止 Long Option (6M+) 左側交易，Option 只限 2-3M 短期催化劑 |
| 4 | GOOGL Short Option Trap | Short Option 壓力極大，需即時監控；唔擅長 → Blacklist |
| 5 | FIGMA IPO FOMO Trap | IPO 首日交易列入 Blacklist；暗盤飆升 = 內部人出貨；等 3-6 個月 |
| 6 | TTD KOL 跟單風控失衡 | KOL 個股最多 10% 倉位；越跌越買設硬性上限；比例比選股更重要 |

## Key Design Decisions
- **CIO is advisor, not portfolio manager**: Watchlist tracks candidate/position status, NOT actual position sizes. Karson decides sizing.
- **Cold sector research**: Only for knowledge updates (Layer 0), must be labeled "⚠️ 純研究，非入場建議"
- **HBM belongs to Memory chain only**: Not duplicated in AI/Semiconductor chain
- **50K target**: 50K HKD passive monthly income OR 5.5M HKD net worth
- **Monetary Environment**: FOMC statement is master signal. Mixed signals → use forward guidance as primary, FedWatch/Polymarket/M2 as sanity check
- **Psychological safety gate**: No rigid recovery timeline; CIO asks "你準備好未?" at next Advisory

## Pitfalls
- Markdown tables: use single `|` separator, not `||` (common patch mistake — double pipes break rendering)
- Always update changelog section when modifying files
- Don't modify Layer 0 (core beliefs) without Karson's explicit approval
- Git identity must be set per-repo (`cd ~/Investment && git config user.name/user.email`) — not global, to avoid conflicts
- HBM belongs to Memory chain only — do NOT duplicate in AI/Semiconductor chain
- When creating agent files: directory is `agents/investors/` (not `agents/` directly) — KOL agents go under `agents/KOL/`
- KOL names: always verify with Karson before recording. Known KOLs: 王者順（順哥）— not 王者神

## Agent Framework Library

Agent files live in `agents/investors/`. Each agent has a consistent structure:
1. **Hard gates** — quantitative thresholds that must pass (any fail = reject)
2. **Falsification condition** — what evidence would overturn the bullish thesis
3. **DO NOT guardrails** — explicit prohibitions
4. **Confidence calibration** — tiered criteria for High/Medium/Low
5. **Structured output** — consistent template for verdicts

Pipeline order for stock analysis: Lynch → Marks → Miller → Munger → Greenblatt
- Lynch (PEG + Story Test) is primary screening — one-sentence test, industry ranking, consumer visibility
- Marks (Cycle Positioning) maps to Regime — 6-bucket cycle ↔ descriptive regime names (not ABCD to avoid cross-reference)
- Buffett dropped from primary (5-10yr horizon doesn't fit Karson's 1yr max)
- Klarman only for extreme fear + easing regime
