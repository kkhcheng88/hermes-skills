#!/usr/bin/env python3
"""
Check YouTube channels for new videos since last run.
Tracks processed video IDs in state file to avoid duplicates.

Usage:
  python3 check_new_videos.py --categories 1,2,3 [--hours 26]
  python3 check_new_videos.py --categories 4 [--hours 2]
  python3 check_new_videos.py --reset          # Clear state
"""

import subprocess, sys, json, os, argparse
from datetime import datetime, timezone

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(SKILL_DIR, "state", "seen_videos.json")

# ── Channel definitions (mirrors channels.yaml) ──
CHANNELS = {
    # Category 1: 被動收入 / 固收
    "@LouBestHK":      {"name": "LouBestHK",      "cat": 1, "desc": "港股ETF/派息分析"},
    "@25y.retirement":  {"name": "25y.retirement",  "cat": 1, "desc": "宏觀/退休投資"},
    # Category 2: 投資理念 / 基本面
    "@AhJu":           {"name": "AhJu",            "cat": 2, "desc": "AI/科技投資見解"},
    "@andyyan":        {"name": "andyyan",         "cat": 2, "desc": "交易心理學 (Mark Douglas)"},
    # Category 3: 技術知識 / 指標
    "@speculation":    {"name": "speculation",     "cat": 3, "desc": "產業鏈/灰產分析"},
    "@BacktestEverything": {"name": "BacktestEverything", "cat": 3, "desc": "量化回測/交易策略"},
    # Category 4: 市場新聞 (每日報告用)
    "@KelileoCUP":     {"name": "KelileoCUP",      "cat": 4, "desc": "港股/美股市場分析"},
    "@KoluniteVIP":    {"name": "KoluniteVIP",     "cat": 4, "desc": "加密貨幣市場分析"},
}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"processed": [], "last_check": None}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_recent_videos(handle, hours=26, max_videos=5):
    """Fetch recent videos from a YouTube channel using yt-dlp."""
    url = f"https://www.youtube.com/{handle}/videos"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "yt_dlp",
             "--flat-playlist", "--playlist-end", str(max_videos),
             "--dump-json", url],
            capture_output=True, text=True, timeout=60
        )
        videos = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                v = json.loads(line)
                vid = v.get("id") or v.get("url", "")
                title = v.get("title", "Unknown")
                upload_date = v.get("upload_date", "")  # YYYYMMDD
                duration = v.get("duration")  # seconds
                if vid and len(vid) == 11:
                    videos.append({
                        "id": vid,
                        "title": title,
                        "upload_date": upload_date,
                        "duration_sec": duration or 0,
                        "url": f"https://www.youtube.com/watch?v={vid}"
                    })
            except json.JSONDecodeError:
                continue
        return videos
    except Exception as e:
        print(f"  ⚠️ Error fetching {handle}: {e}", file=sys.stderr)
        return []

def main():
    parser = argparse.ArgumentParser(description="Check for new YouTube videos")
    parser.add_argument("--categories", default="1,2,3", help="Comma-separated category numbers (1-4)")
    parser.add_argument("--hours", type=int, default=26, help="Look back N hours for new videos")
    parser.add_argument("--reset", action="store_true", help="Clear seen videos state")
    parser.add_argument("--max-per-channel", type=int, default=5, help="Max videos to check per channel")
    args = parser.parse_args()

    if args.reset:
        save_state({"processed": [], "last_check": None})
        print("✅ State reset.")
        return

    categories = [int(c.strip()) for c in args.categories.split(",")]
    state = load_state()
    processed = set(state.get("processed", []))

    # Filter channels by category
    channels_to_check = {
        h: info for h, info in CHANNELS.items()
        if info["cat"] in categories
    }

    new_videos = []
    errors = []

    for handle, info in channels_to_check.items():
        videos = get_recent_videos(handle, hours=args.hours, max_videos=args.max_per_channel)
        if not videos and not any(v for v in videos):
            # Could be an error or just no recent videos
            pass

        for v in videos:
            if v["id"] not in processed:
                new_videos.append({
                    **v,
                    "channel_handle": handle,
                    "channel_name": info["name"],
                    "category": info["cat"],
                    "category_desc": info["desc"],
                })

    # Output results as JSON
    output = {
        "check_time": datetime.now(timezone.utc).isoformat(),
        "categories_checked": categories,
        "channels_checked": list(channels_to_check.keys()),
        "new_videos": new_videos,
        "total_new": len(new_videos),
        "state_last_check": state.get("last_check"),
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Mark all as processed
    for v in new_videos:
        processed.add(v["id"])
    save_state({"processed": list(processed), "last_check": state.get("last_check")})

if __name__ == "__main__":
    main()
