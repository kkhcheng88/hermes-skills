# Kars (Hermes Agent) — Custom Skills Collection

This repo contains all custom-built skills for **Kars**, a personal AI assistant running on [Hermes Agent](https://github.com/NousResearch/hermes-agent) via WSL.

**Purpose:** Version-controlled backup + rebuild reference. If Kars needs to be rebuilt on a new machine, clone this repo and follow the setup instructions below.

---

## Skills Inventory

### 📊 Investment & Research

| Skill | Directory | Description |
|-------|-----------|-------------|
| **TradingKey** | `research/tradingkey/` | Stock scoring, multi-dimensional analysis, support/resistance from TradingKey API. Endpoint: `/quotes-base/diagnosis/v1/stock-score?route=nasdaq-{SYMBOL}` |
| **WallStreetCN** | `research/wallstreetcn/` | Real-time Chinese financial news from 华尔街见闻 |
| **Sector Rotation Scan** | `sector-rotation-scan/` | US sector rotation signals and temperature indicators |
| **Discord KOL** | `research/discord-kol/` | Discord investment KOL monitoring and YouTube transcript summarization |
| **GitHub Trending** | `research/github-trending/` | Daily GitHub trending repos analysis |
| **PMCC Position Analysis** | `research/pmcc-position-analysis/` | PMCC (Poor Man's Covered Call) position analysis |
| **Portfolio Charter Review** | `research/portfolio-charter-review/` | Portfolio vs investment charter alignment check |
| **Website SEO Review** | `research/website-seo-design-review/` | Website SEO and design analysis |
| **Stock Analysis** | `stock-analysis/` | Ad-hoc stock analysis framework |
| **YouTube Transcript Extractor** | `research/youtube-transcript-extractor/` | Extract YouTube video transcripts/subtitles via Puppeteer + Chrome debugging port |

### 🔄 Content & Automation

| Skill | Directory | Description |
|-------|-----------|-------------|
| **Content → NotebookLM** | `content-to-notebooklm/` | Multi-source content distillation via Google NotebookLM. Supports web, YouTube, PDF, WeChat articles. |
| **Facebook Page Scraper** | `facebook-page-scraper/` | Scrape public Facebook page posts using Playwright + cookies |

### 🔧 DevOps & Utilities

| Skill | Directory | Description |
|-------|-----------|-------------|
| **Hermes Gateway Troubleshooting** | `devops/hermes-gateway-troubleshooting/` | Debug and fix gateway connection issues |
| **Hermes Skills Audit** | `devops/hermes-skills-audit/` | Audit installed skills for health and dependencies |
| **Third-Party Skill Installer** | `devops/third-party-skill-installer/` | Install and manage third-party skills |

---

### 🔎 YouTube Transcript Extractor — Details

**Directory:** `research/youtube-transcript-extractor/`

**Features:**
- Search YouTube videos by keyword and extract transcripts (逐字稿)
- Batch extraction for multiple videos
- Uses Chrome DevTools Protocol (port 9222) for reliable extraction
- Supports both single video and search-based workflows

**Trigger Words:**
- 「提取 YouTube transcript」
- 「搜尋 YouTube 影片」
- 「提取字幕」
- 「YouTube 逐字稿」

**Usage:**
1. Start Chrome with remote debugging: `chrome --remote-debugging-port=9222`
2. Invoke the skill with a search query or video URL
3. Transcripts are extracted and saved as text files

**Core Tech:** Puppeteer automation + Chrome DevTools Protocol (CDP) on port 9222

---

## Setup (Rebuild Instructions)

### 1. Prerequisites

```bash
# Hermes Agent installed and configured
hermes --version

# Python 3.12+
python3 --version

# Git
git --version
```

### 2. Clone & Install Skills

```bash
# Clone this repo
git clone https://github.com/kkhcheng88/hermes-skills.git ~/.hermes/hermes-skills-backup

# Copy skills to Hermes skills directory
cp -r ~/.hermes/hermes-skills-backup/* ~/.hermes/skills/

# Install Python dependencies
pip install --break-system-packages -r ~/.hermes/hermes-skills-backup/requirements.txt

# Install Playwright browser (for Facebook scraper)
python3 -m playwright install chromium
```

### 3. Configuration

#### Environment Variables (`~/.hermes/.env`)

```bash
# TradingKey — no API key required (public API)
# WallStreetCN — check skill README for any required tokens
# NotebookLM — requires Google auth:
notebooklm login

# Facebook Page Scraper — requires cookies file:
# Place cookies.json at ~/.hermes/skills/facebook-page-scraper/cookies.json
```

#### MCP Server (WeChat/Feishu articles)

```bash
# Register the MCP server for WeChat article scraping
hermes mcp add weixin-reader --command python3 --args "~/.hermes/skills/content-to-notebooklm/feishu-read-mcp/src/server.py"
```

#### Verify Installation

```bash
# Check all skills loaded
hermes skills list

# Check dependencies
hermes doctor

# Test specific skills
python3 -c "import yfinance, ta, bs4, playwright, markitdown; print('All deps OK')"
```

### 4. Cron Jobs (if applicable)

The following cron jobs use these skills:

| Job | Schedule | Skills Used | Delivery |
|-----|----------|-------------|----------|
| YouTube KOL Summary | Daily 6pm HKT | discord-kol, youtube-content | Discord channels |
| GitHub Trending | Daily 6pm HKT | github-trending | Discord #github |
| Sector Rotation | Periodic | sector-rotation-scan | Discord |
| WallStreetCN News | As configured | wallstreetcn | Discord |

---

## Investment Framework Reference

When analyzing stocks, Kars uses the following pipeline:

### Data Collection (all 3 mandatory)
1. **yfinance** — Price, fundamentals, technicals (ta library)
2. **TradingKey** — Score, multi-dimensional ratings, support/resistance, sentiment
3. **Latest news** — Google News + yfinance news

### Agent Frameworks (applied in order)
1. **Lynch (PEG + Story)** — Primary for 1-year buy & hold horizon
2. **Marks (Cycle Positioning)** — Regime timing
3. **Miller (Contrarian + FCF)** — FCF yield plays
4. **Munger (Inversion)** — Pre-purchase risk check ("how do I lose money?")
5. **Greenblatt (Magic Formula)** — Emotion-free ranking

### Options Rules
- **PMCC** → SPY only
- **CSP systematic** → QQQ only
- **CSP individual stocks** → Only when IV high + willing to own

### Key Constraints
- Buy & Hold horizon: max 1 year
- Sectors: US tech, semiconductors, AI, energy + SPY/QQQ
- No: 0DTE, following KOL signals, revenge sizing, FOMO

---

## Skill Maintenance

When a skill is **majorly updated**, sync changes back to this repo:

```bash
cd ~/.hermes/hermes-skills-repo

# Copy updated skill
cp -r ~/.hermes/skills/<skill-name> ./

# Or for categorized skills:
cp -r ~/.hermes/skills/research/<skill-name> ./research/
cp -r ~/.hermes/skills/devops/<skill-name> ./devops/

# Commit & push
git add -A
git commit -m "update: <skill-name> — <brief description>"
git push origin master
```

---

## Excluded Skills (Not in This Repo)

These are upstream clones or environment-specific and NOT synced:

| Skill | Reason |
|-------|--------|
| `qiaomu-anything-to-notebooklm` | Upstream clone from GitHub (joeseesun) |

---

## Dependencies Quick Reference

| Package | Used By |
|---------|---------|
| yfinance | tradingkey, stock-analysis, sector-rotation-scan, pmcc |
| ta | stock-analysis (RSI, MACD, Bollinger, ATR) |
| beautifulsoup4 | discord-kol, wallstreetcn, website-seo |
| playwright | facebook-page-scraper |
| markitdown | content-to-notebooklm |
| notebooklm-py | content-to-notebooklm |
| fastmcp | content-to-notebooklm (MCP server) |
| youtube-transcript-api | discord-kol, youtube-content |
| puppeteer | youtube-transcript-extractor |
| pandas | everywhere |
| requests | tradingkey, wallstreetcn |

---

## License

Private — for personal use only.
