---
name: discord-kol
description: Searchable KOL knowledge base from Discord channels. Export messages via DiscordChatExporter, parse into indexed KB, then search by topic/stock/author when generating reports.
version: 2.1
---

# Discord KOL Knowledge Base

Build a searchable knowledge base of financial analysis from Discord KOL channels, for reference during daily report generation.

## Architecture

```
DiscordChatExporter (Windows CLI, called via cmd.exe)
  ↓ JSON export (per channel)
Parser → extract financial messages, tag with stocks/topics
  ↓
Knowledge Base: knowledge/{channel}.json
  ↓
Search (by stock / keyword / author / date range)
  ↓
Feed relevant entries into LLM for report generation

Optional: Vision analysis for image-heavy channels
  ↓ images → OpenRouter free vision models → vision_analysis field
```

## Prerequisites

- DiscordChatExporter at `C:\Game\DiscordChatExporter\DiscordChatExporter.Cli.exe` (accessible from WSL via cmd.exe)
- Discord token (user or bot token)
- Channel IDs of KOL channels you've joined
- (Optional) OpenRouter API key for image vision analysis

## Workflow

### 1. Export — Run periodically (weekly or before report generation)

```bash
python3 scripts/discord_export.py \
  --token "YOUR_TOKEN" \
  --channel-id 1082918342031069254 \
  --channel-name RoyalFlush \
  --days 14
```

Calls DiscordChatExporter via cmd.exe, exports last N days, auto-parses into KB.
Incremental: skips messages already in KB.
Use shorter windows (14-90 days) to avoid JSON truncation on large channels.

### 2. Search — Used during report generation

```python
import sys; sys.path.insert(0, '/path/to/discord-kol/scripts')
from discord_search import search_knowledge, format_for_report

results = search_knowledge(stocks=["TSLA"], days=30)
results = search_knowledge(channel="ElliottWave", query="波浪", days=60)
print(format_for_report(results))
```

### 3. Image Vision Analysis (Opt-in per channel)

Not all channels need image processing. Default: OFF. Only enable when user requests.

```bash
OPENROUTER_API_KEY="sk-..." python3 scripts/discord_vision_batch.py \
  --channel ElliottWave \
  --file /mnt/c/TradingView/Discord/ElliottWave_90d.json \
  --delay 2.5
```

Free vision models via OpenRouter (fallback chain when rate-limited):
- google/gemma-4-31b-it:free (best)
- google/gemma-3-27b-it:free
- nvidia/nemotron-nano-12b-v2-vl:free
- google/gemma-3-12b-it:free

## Two Use Cases

**A. Recent Monitoring** — export last 30-90 days, for routine stock analysis
**B. Long-term Distillation** — export months/years from prolific KOLs, extract methodology

Current default: Use case A (recent 3 months).

## Key Lessons Learned

- Large exports (>1000 msgs over long periods) may produce truncated JSON → use shorter windows
- discord_parse.py handles truncation via brace-counting fallback
- DiscordChatExporter runs from WSL via cmd.exe (no .NET on WSL needed)
- Export timeout: 300s recommended for 90-day exports
- Chinese chars in stdout are garbled (encoding issue) but harmless
- Vision batch needs PYTHONUNBUFFERED=1 for real-time logging in background
- Background process output capture can be unreliable → redirect to log file

### 3. Vision Batch — Analyze chart images with AI (OPTIONAL, per-channel opt-in)

Not all channels need image processing. Only enable for channels where KOLs share valuable chart images (e.g., Elliott Wave analysis).

```bash
# Process all images in a channel export
PYTHONUNBUFFERED=1 OPENROUTER_API_KEY="sk-..." \
  python3 scripts/discord_vision_batch.py \
  --channel ElliottWave \
  --file /mnt/c/TradingView/Discord/ElliottWave_90d.json \
  --delay 2.5

# Process only first N images (for testing)
python3 scripts/discord_vision_batch.py --channel ElliottWave --file ... --limit 5
```

**Models:** Uses free OpenRouter vision models with fallback chain:
1. `google/gemma-4-31b-it:free` (primary, best quality)
2. `google/gemma-3-27b-it:free`
3. `nvidia/nemotron-nano-12b-v2-vl:free` (fallback)
4. `google/gemma-3-12b-it:free`

**Rate limits:** ~15 sec/image with fallback. ~500 images takes ~2 hours.

**Output:** Adds entries with `has_image_analysis: true` and `vision_analysis` field to KB.

**Channels with image processing enabled:**
- ✅ ElliottWave (波浪理論學習) — Elliott Wave charts
- ❌ Others by default — only enable when Karson requests

## Scripts

- `scripts/discord_export.py` — Export + auto-parse (main entry point)
- `scripts/discord_parse.py` — Parse JSON export → KB (handles truncation)
- `scripts/discord_search.py` — Search KB (importable as Python module)
- `scripts/discord_vision_batch.py` — Batch image analysis with free vision models

## Image Processing (Opt-in)

**By default, images are NOT processed.** Only channels explicitly configured will have images analyzed via vision model.

To enable image processing for a channel, use `--images` flag during export, or run the vision batch script separately:

```bash
# Vision batch — analyze all images in an exported channel
python3 scripts/discord_vision_batch.py \
  --channel ElliottWave \
  --file /mnt/c/TradingView/Discord/ElliottWave_90d.json \
  --delay 2.5
```

Uses **OpenRouter free vision models** (google/gemma-4-31b-it:free primary, nvidia/nemotron-nano-12b-v2-vl:free fallback). Requires `OPENROUTER_API_KEY` in env.

Channels with image processing enabled:
- ElliottWave (波浪理論學習) — Elliott Wave chart analysis

### 4. Multi-Round Vision Retry Strategy (Proven Workflow)

When initial batch has high failure rate (~50%), use this progressive retry approach:

1. **First retry**: Switch model order — if primary was Gemma, try Nemotron first (less rate-limited)
2. **Second retry**: Switch back to Gemma 4 31B (better analysis quality)
3. **Final retry**: **Re-export the channel** to get fresh Discord CDN URLs (they expire), then retry remaining failures with best model

Results from ElliottWave channel (Apr 2026):
- Round 1 (original batch): 268/542 success
- Round 2 (Nemotron): +94
- Round 3 (Gemma 4 31B): +96  
- Round 4 (Gemma): +51
- Round 5 (re-export + Gemma): +33
- **Final: 542/548 = 98.9% success rate**

Key insight: **Re-exporting the channel is critical** for the final push — Discord CDN URLs expire, so only a fresh export gives valid image URLs for the last stubborn failures.

Scripts:
- `scripts/discord_vision_retry.py` — reads `failed_ids.json`, retries from export file
- To re-export: use `discord_export.py` with same token/channel, then re-run retry

## Limitations