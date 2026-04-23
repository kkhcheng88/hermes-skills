---
name: youtube-content
description: >
  Fetch YouTube video transcripts and transform them into structured content
  (chapters, summaries, threads, blog posts). Use when the user shares a YouTube
  URL or video link, asks to summarize a video, requests a transcript, or wants
  to extract and reformat content from any YouTube video.
---

# YouTube Content Tool

Extract transcripts from YouTube videos and convert them into useful formats.

## Setup

```bash
pip install youtube-transcript-api
```

## Helper Script

`SKILL_DIR` is the directory containing this SKILL.md file. The script accepts any standard YouTube URL format, short links (youtu.be), shorts, embeds, live links, or a raw 11-character video ID.

```bash
# JSON output with metadata
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Transcript Extraction — Two-Layer Approach

### Layer 1: youtube-transcript-api (preferred)
Fetches transcripts instantly without downloading. Works for videos with manual subtitles or auto-generated captions.

```bash
python3 SKILL_DIR/scripts/yt_transcript.py "VIDEO_URL"
python3 SKILL_DIR/scripts/yt_transcript.py VIDEO_ID --check-only
python3 SKILL_DIR/scripts/yt_transcript.py VIDEO_ID --lang zh-Hant,zh,en --json
```

### Layer 2: yt-dlp auto-subtitle download (fallback)
Downloads auto-generated VTT subtitle files when Layer 1 fails. **Requires JavaScript runtime** (deno recommended, or node with `--js-runtimes` flag).

```bash
python3 SKILL_DIR/scripts/yt_transcript.py VIDEO_ID  # auto-trys Layer 1 then Layer 2
```

### Check before following a channel

When adding a new YouTube channel, always check transcript availability first:

```python
from scripts.yt_transcript import check_availability
result = check_availability("VIDEO_ID")
# result['available']: True/False
# result['recommendation']: "Layer 1" / "Layer 2" / "skip"
```

If neither layer works (channel has captions disabled), **skip the channel** — no need to follow.

### Workflow

1. **Fetch** the transcript using the helper script with `--text-only --timestamps`.
2. **Validate**: confirm the output is non-empty and in the expected language. If empty, retry without `--language` to get any available transcript. If still empty, tell the user the video likely has transcripts disabled.
3. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
4. **Transform** into the requested output format. If the user did not specify a format, default to a summary.
5. **Verify**: re-read the transformed output to check for coherence, correct timestamps, and completeness before presenting.

## Pitfalls & Learnings

- **youtube-transcript-api v1.2+ API changed**: Use `YouTubeTranscriptApi().fetch(id)` and `.list(id)`, NOT the old `get_transcript()` or `list_transcripts()` static methods.
- **Some channels disable captions entirely**: No Layer 1 or Layer 2 will work. Skip these channels. Known examples: @stockruhigah, @老李玩钱, @TradingKey_ZH.
- **Cantonese videos**: Many HK YouTubers have `yue` or `yue-HK` auto-generated captions. Quality varies.
- **Layer 1 fails silently for some videos**: Even when auto-captions exist on YouTube, the API may not return them. Always fall back to Layer 2.
- **yt-dlp JS challenge solving**: Latest yt-dlp (2026+) requires a JS runtime for YouTube's challenge solver. Use `--js-runtimes node` (node is widely available) or install deno. Also add `--remote-components ejs:github` to download the challenge solver script — without it, yt-dlp may detect subtitles but fail to download them.
- **VTT deduplication**: Auto-generated VTT files often contain overlapping/repeated caption lines. When parsing VTT → plain text, deduplicate consecutive identical lines to avoid 2-3x repetition in output.

## Channel Config

Store monitored channels in `config/channels.yaml`:

```yaml
channels:
  - handle: "@ChannelHandle"
    name: "Short Name"
    category: market-news  # passive-income | investment-ideas | technical-knowledge | market-news
    report: true           # include in daily report?
    transcript: layer1
    language: zh-Hant, yue
```

## ⚠️ Cloud IP Blocking (CRITICAL)

YouTube blocks cloud/hosting provider IPs (Hetzner, AWS, GCP, Azure, etc.). This affects **both** transcript extraction layers AND browser access:

- **Layer 1 (transcript-api)**: `IP blocked` error — YouTube refuses all API requests
- **Layer 2 (yt-dlp)**: HTTP 429 Too Many Requests — same IP block
- **Browser**: Google CAPTCHA/sorry page redirect

**This means cron jobs running from cloud servers CANNOT fetch YouTube transcripts.**

### Workarounds

| Method | How | Effort |
|--------|-----|--------|
| **yt-dlp cookies** | Export `cookies.txt` from local browser (logged into YouTube), use `--cookies /path/to/cookies.txt` flag | Low — needs periodic refresh |
| **Residential proxy** | Bright Data, IPRoyal, etc. — proxy traffic through residential IPs | Medium — costs money |
| **Local fetch** | Run transcript fetch from non-cloud machine (e.g. WSL on user's PC), upload results | Low — but not automated |
| **Third-party API** | RapidAPI YouTube transcript services | Low — few $/month |

**Recommended**: Use `cookies.txt` from a logged-in browser session. Export with a browser extension (e.g. "Get cookies.txt LOCALLY"), then pass to yt-dlp:
```bash
yt-dlp --cookies cookies.txt --write-auto-sub --sub-lang zh-Hant ...
```

Note: Cookies expire when the YouTube session ends (logout, password change). Plan to refresh periodically.

### Local Fetch Script (for cloud-blocked environments)

When the agent runs on a cloud server, YouTube blocks ALL transcript methods (transcript-api, yt-dlp, browser). The workaround is fetching transcripts from a local machine.

**Script**: `~/.hermes/scripts/local_yt_check.py`

```bash
# Check Cat 1 channels, fetch transcripts via local IP
python3 ~/.hermes/scripts/local_yt_check.py --categories 1 --max-per-channel 3

# Check all categories
python3 ~/.hermes/scripts/local_yt_check.py --all
```

**How it works:**
1. Uses yt-dlp `--flat-playlist` to list recent videos (works from any IP)
2. Layer 1: `youtube-transcript-api` with explicit language codes (works from residential IPs)
3. Layer 2: yt-dlp subtitle download with `--js-runtimes node --remote-components ejs:github` (fallback)
4. Saves results to `~/.hermes/scripts/yt_output/latest.json`
5. Auto-tracks processed video IDs in state file

**Key finding**: youtube-transcript-api works from residential IPs even when yt-dlp's subtitle download returns 429. They use different YouTube endpoints.

**Prerequisites on local machine:**\n```bash\npip3 install yt-dlp youtube-transcript-api --break-system-packages\n```\n\n## Channel-Specific Summary Rules\n\nWhen generating summaries for investment channels, apply Karson's content preferences:\n\n**Content rules (all channels):**\n- ✅ Focus on: analysis, updates, insights, risk warnings, price targets, directional views, catalysts\n- ❌ Skip: static facts (ETF entry thresholds, basic product descriptions, fund size) — these aren't news\n- 💰 Fund flow → briefly mention, don't elaborate\n- Tone: direct, concise, like briefing a friend\n- Format: use bullet points and line breaks aggressively — never write long paragraphs. Each distinct point on its own line with •\n\n**Channel-specific rules:**\n- **@speculation (Cat 3, zh-Hans subtitles)**: MUST include TradingView indicator SETUP (parameters, timeframe, conditions) and the LOGIC behind why it works. This is the ONLY channel covering indicator setups. Language list MUST include `zh-Hans` (not just `zh-Hant`).\n- **@BacktestEverything (Cat 3, English)**: MUST include backtest SETUP (stocks tested, date range, criteria, number of trades) alongside results.\n- **@AhJu & @andyyan (Cat 2)**: Videos are infrequent — give FULL detail (6-10 sentences). MUST include lessons learned, key takeaways, stories/examples from the video.\n- **Cat 4 (KelileoCUP, KoluniteVIP)**: Investment-focused ONLY — extract tickers, target prices, buy/sell views. Skip videos with no investment-specific content entirely.\n\n## youtube-transcript-api Language Codes (IMPORTANT)\n\nThe API defaults to `en` if no languages specified. For Chinese/Cantonese content, ALWAYS pass explicit languages:\n\n```python\nfrom youtube_transcript_api import YouTubeTranscriptApi\nytt = YouTubeTranscriptApi()\ntranscript = ytt.fetch(\"VIDEO_ID\", languages=['zh-Hant','zh-Hans','zh','yue','zh-HK','en'])\n```\n\n**Known language patterns:**\n- @speculation: `zh-Hans` (Simplified Chinese manual subtitles)\n- @LouBestHK: `zh-Hant` (Traditional Chinese manual subtitles)\n- @AhJu, @andyyan: `yue` or `yue-HK` (Cantonese auto-captions)\n- @BacktestEverything: `en` (English auto-captions)\n- @KelileoCUP: `zh-Hant`, `yue`\n- @KoluniteVIP: `zh`\n\nWithout explicit language codes, all Chinese/Cantonese videos return `NoTranscriptFound` even when captions exist.

## Error Handling

- **Transcript disabled**: tell the user; suggest they check if subtitles are available on the video page.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user.
- **Dependency missing**: run `pip install youtube-transcript-api` and retry.
- **429 / IP blocked**: YouTube cloud IP block — use cookies.txt or proxy workaround (see above).

## Troubleshooting: "Why No New Videos?"

When user asks why no new YouTube content, diagnose in this order:

### Step 1: Check Cron Jobs
```bash
# List all cron jobs, find YouTube-related ones
# Look at: last_run_at, last_status, next_run_at
```
Key things to verify:
- `enabled: true` and `state: scheduled`
- `last_status: ok` (not error)
- `last_run_at` timestamp is recent
- `next_run_at` is correct

### Step 2: Check Local Crontab
```bash
crontab -l | grep youtube
# OR check the full crontab
```
Verify local scripts are scheduled:
- Cat 4: `:55 * * * *` (hourly)
- Cat 1-3: `30 17 * * *` (daily 5:30pm)

### Step 3: Check Logs
```bash
# Hourly Cat 4 logs
tail -30 ~/.hermes/logs/yt_hourly.log

# Daily Cat 1-3 logs
tail -30 ~/.hermes/logs/yt_daily.log
```
Look for:
- `"total_new": 0` — means system working, just no new content
- Errors or exceptions — system issue
- `processed=True` — videos already seen

### Step 4: Check State File
```bash
cat ~/.hermes/skills/media/youtube-content/state/seen_videos.json
```
Verify:
- `last_check` timestamp is recent
- `processed` list contains video IDs

### Step 5: Check Channel Config
```bash
head -32 ~/.hermes/scripts/local_yt_check.py
```
Lists all monitored channels and their categories.

### Common Scenarios

| Symptom | Diagnosis |
|---------|-----------|
| `"total_new": 0` in logs | ✅ System working, channels just haven't uploaded |
| No recent `last_run_at` | Cron job not running — check if enabled |
| `last_status: error` | Job failed — check gateway logs |
| State file old `last_check` | Local script not running — check crontab |
| Channels show but no videos found | YouTube rate limiting or IP block |

### Quick Status Summary (for user response)
After diagnosis, give user:
1. **System status**: Running/Not running
2. **Last check time**: When was the most recent check
3. **Result**: How many new videos found (0 = no new content)
4. **Next check**: When is the next scheduled check
5. **Monitored channels**: Brief list of what's being watched

## Channel Monitoring (New Video Detection)

### check_new_videos.py

Detects new videos from configured channels since last check. Uses yt-dlp `--flat-playlist` (fast, no download). Tracks processed video IDs in a state file to avoid duplicates.

```bash
# Check categories 1-3 (passive income, investment ideas, technical knowledge)
python3 SKILL_DIR/scripts/check_new_videos.py --categories 1,2,3 --hours 26

# Check category 4 only (market news)
python3 SKILL_DIR/scripts/check_new_videos.py --categories 4 --hours 2

# Reset state (clear seen video IDs)
python3 SKILL_DIR/scripts/check_new_videos.py --reset
```

Output is JSON:
```json
{
  "check_time": "2026-04-20T04:00:00+08:00",
  "new_videos": [
    {
      "id": "VIDEO_ID",
      "title": "Video Title",
      "url": "https://youtube.com/watch?v=VIDEO_ID",
      "channel_handle": "@ChannelName",
      "channel_name": "ShortName",
      "category": 1,
      "duration_sec": 1800
    }
  ],
  "total_new": 1
}
```

### State Tracking

State stored at `state/seen_videos.json`. The script auto-marks videos as processed after output. To re-process a video, reset state or manually remove its ID from the JSON file.

### Cron Job Setup Pattern

Two cron job types for YouTube monitoring:

**Daily digest (Cat 1-3)** — general insight summaries:
- Schedule: `0 4 * * *` (HKT 12pm)
- Check window: `--hours 26` (buffer for timezone)
- Output: 3-8 sentence summaries per video, grouped by category
- Max length: 1800 chars (Discord limit)

**Hourly investment alert (Cat 4)** — ticker/price extraction only:
- Schedule: `0 * * * *` (every hour)
- Check window: `--hours 2`
- Output: Only videos with specific tickers, buy/sell views, or target prices
- Skip videos with no investment-specific content
- Max length: 1500 chars

**Cron prompt must:**
1. Run `check_new_videos.py` first
2. If `total_new == 0`, output nothing (hourly) or brief "no new videos" (daily)
3. For each new video, fetch transcript via `yt_transcript.py VIDEO_ID --text-only`
4. Layer 1 fails → retry without `--text-only` (auto-falls back to Layer 2)
5. Generate summaries from transcript content
6. Deliver to origin (Discord thread)

**Known channels with transcripts:**
| Channel | Category | Method | Language |
|---------|----------|--------|----------|
| @LouBestHK | 1 (passive-income) | Layer 1 | zh-Hant, yue |
| @25y.retirement | 1 (passive-income) | Layer 1 | zh-HK, yue |
| @AhJu | 2 (investment-ideas) | Layer 1 | yue-HK, yue |
| @andyyan | 2 (investment-ideas) | Layer 1 | yue |
| @speculation | 3 (technical-knowledge) | Layer 1 | zh-Hans |
| @BacktestEverything | 3 (technical-knowledge) | Layer 1 | en |
| @KelileoCUP | 4 (market-news) | Layer 1 | zh-Hant, yue |
| @KoluniteVIP | 4 (market-news) | Layer 1 | zh |

**Channels skipped (no transcripts):** @stockruhigah, @老李玩钱, @TradingKey_ZH

### ⚠️ State File Conflict Between Cloud and Local Scripts

`check_new_videos.py` and `local_yt_check.py` share the **same state file** (`state/seen_videos.json`). This causes a critical issue:

**Problem**: The cloud cron job runs `check_new_videos.py`, detects new videos, but then fails to fetch transcripts (IP blocked). Despite transcript failure, videos get marked as "processed" in the shared state. When `local_yt_check.py` later runs on the local machine, it sees these videos as already processed and skips them — losing the transcripts permanently.

**Workaround**: Don't run `check_new_videos.py` from the cloud if you intend to fetch transcripts locally. Instead, let `local_yt_check.py` handle both detection AND transcript fetch. The cloud cron should only read `yt_output/latest.json` and format the report.

**Recommended architecture for hourly Cat 4:**
```
Local crontab (WSL):
  0 * * * * python3 ~/.hermes/scripts/local_yt_check.py --categories 4 --max-per-channel 3

Cloud cron (Hermes):
  Reads ~/.hermes/scripts/yt_output/latest.json
  Formats investment alerts → sends to Discord Market thread
```

### Channel-Specific Summary Rules

When generating summaries for these channels, apply special focus:

- **@speculation (Cat 3, zh-Hans subtitles)**: MUST include the TradingView indicator SETUP (parameters, timeframe, conditions) and the LOGIC behind why it works. This is the only channel covering indicator setups — capture the technical detail. Language list MUST include `zh-Hans`.
- **@BacktestEverything (Cat 3)**: MUST include the backtest SETUP (stocks tested, date range, criteria, number of trades) alongside results. The setup context is essential.

Two transcript scripts exist with different CLIs:
- `fetch_transcript.py` — accepts URL, has `--text-only` and `--timestamps` flags
- `yt_transcript.py` — accepts video ID, has `--json` and `--lang` flags, NO `--text-only`

For cron workflows, use `fetch_transcript.py URL --text-only` or `local_yt_check.py` (handles everything end-to-end).

## Full Automation Architecture (Cloud + Local)

When running YouTube monitoring as cron jobs on a cloud server that's IP-blocked by YouTube:

```
Local machine (WSL) crontab:
  :55 every hour  → local_yt_check.py --categories 4 → latest_hourly.json
  11:30am daily   → local_yt_check.py --categories 1,2,3 → latest_daily.json

Cloud cron (Hermes):
  :00 every hour  → reads latest_hourly.json → investment alerts → Discord Market thread
  12:00pm daily   → reads latest_daily.json → summaries → 3 category threads
```

**Critical**: Local crontab MUST run 5-30 minutes BEFORE cloud cron to avoid race conditions. Example:\n```cron\n# Local crontab (WSL)\n55 * * * * python3 ~/.hermes/scripts/local_yt_check.py --categories 4 --max-per-channel 3\n30 3 * * * python3 ~/.hermes/scripts/local_yt_check.py --categories 1,2,3 --max-per-channel 3\n```\n\n**Output file naming**: `local_yt_check.py` auto-saves to `latest_hourly.json` (Cat 4 only) or `latest_daily.json` (Cat 1-3). Cloud cron reads the appropriate file based on its schedule.\n\n**Discord thread routing** (Karson's #youtube channel `1495531924473643158`):\n| Category | Thread Name | Thread ID |\n|----------|-------------|-----------|\n| Cat 1 (被動收入) | Passive Income | `1495537396291342520` |\n| Cat 2 (投資理念) | General | `1495532312266539109` |\n| Cat 3 (技術知識) | Technical | `1495532355623059648` |\n| Cat 4 (市場新聞) | Market | `1495532415597416460` |\n\nCloud cron uses `send_message` with target `discord:1495531924473643158:THREAD_ID`. Set deliver to `local` (not `origin`) to prevent auto-delivery to the wrong place.

### youtube-transcript-api Language Codes (IMPORTANT)

The API defaults to `en` if no languages specified. For Chinese/Cantonese content, ALWAYS pass explicit languages:

```python
from youtube_transcript_api import YouTubeTranscriptApi
ytt = YouTubeTranscriptApi()
transcript = ytt.fetch("VIDEO_ID", languages=['zh-Hant','zh','yue','zh-HK','en'])
```

Without this, all Chinese videos return `NoTranscriptFound` even when captions exist.

### Summary Content Rules (Karson's preference)

When generating video summaries for investment channels:
- ✅ Focus on: analysis, updates, insights, risk warnings, price targets, directional views, catalysts
- ❌ Skip: static facts (ETF entry thresholds, basic product descriptions, fund size) — these aren't news
- 💰 Fund flow → briefly mention, don't elaborate
- Each video: 3-6 sentences, Traditional Chinese (繁體中文)
- Tone: direct, concise, like briefing a friend
