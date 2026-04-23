#!/usr/bin/env python3
"""
YouTube Transcript Extractor — Layer 1 + Layer 2 only.

Layer 1: youtube-transcript-api (instant, no download)
Layer 2: yt-dlp auto-generated subtitle download (fallback)

Usage:
  python3 yt_transcript.py "https://youtube.com/watch?v=VIDEO_ID"
  python3 yt_transcript.py VIDEO_ID --check-only
  python3 yt_transcript.py VIDEO_ID --lang zh-Hant,zh,en
"""

import argparse
import glob
import json
import re
import subprocess
import sys
import tempfile

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("ERROR: pip install youtube-transcript-api", file=sys.stderr)
    sys.exit(1)

ytt = YouTubeTranscriptApi()


def extract_video_id(url_or_id: str) -> str:
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    for p in [r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
              r'(?:embed/)([a-zA-Z0-9_-]{11})',
              r'(?:shorts/)([a-zA-Z0-9_-]{11})']:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    return url_or_id


def layer1_fetch(video_id: str, languages: list = None) -> dict:
    try:
        t = ytt.fetch(video_id, languages=languages) if languages else ytt.fetch(video_id)
        text = " ".join([s.text for s in t.snippets])
        return {"success": True, "method": "transcript-api", "text": text, "chars": len(text)}
    except Exception as e:
        return {"success": False, "method": "transcript-api", "error": str(e)[:150]}


def layer2_fetch(video_id: str, langs: str = "zh-Hant,zh,en") -> dict:
    try:
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(
                [sys.executable, '-m', 'yt_dlp',
                 '--write-auto-sub', '--sub-lang', langs,
                 '--skip-download', '--sub-format', 'vtt',
                 '-o', f'{d}/%(id)s.%(ext)s',
                 f'https://www.youtube.com/watch?v={video_id}'],
                capture_output=True, text=True, timeout=45
            )
            subs = glob.glob(f'{d}/*.vtt')
            if not subs:
                return {"success": False, "method": "yt-dlp", "error": "No auto-subtitle"}

            with open(subs[0], 'r') as f:
                lines = f.read().split('\n')

            seen, out = set(), []
            for line in lines:
                line = line.strip()
                if not line or line.startswith(('WEBVTT', 'Kind:', 'Language:')) or '-->' in line:
                    continue
                if line not in seen:
                    seen.add(line)
                    out.append(line)

            text = " ".join(out)
            return {"success": True, "method": "yt-dlp-auto-sub", "text": text, "chars": len(text)}
    except Exception as e:
        return {"success": False, "method": "yt-dlp", "error": str(e)[:150]}


def get_transcript(video_url_or_id: str, languages: list = None) -> dict:
    vid = extract_video_id(video_url_or_id)
    r = layer1_fetch(vid, languages)
    if r["success"]:
        return r
    r = layer1_fetch(vid)
    if r["success"]:
        return r
    lang_str = ",".join(languages) if languages else "zh-Hant,zh,en"
    r = layer2_fetch(vid, lang_str)
    if r["success"]:
        return r
    return {"success": False, "method": "none", "error": "No transcript available"}


def check_availability(video_url_or_id: str) -> dict:
    vid = extract_video_id(video_url_or_id)
    try:
        tl = ytt.list(vid)
        subs = [{"lang": t.language, "code": t.language_code, "auto": t.is_generated} for t in tl]
        return {"available": True, "subtitles": subs, "recommendation": "Layer 1"}
    except Exception:
        pass
    try:
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run(
                [sys.executable, '-m', 'yt_dlp', '--list-subs', '--skip-download',
                 f'https://www.youtube.com/watch?v={vid}'],
                capture_output=True, text=True, timeout=30
            )
            if 'auto' in r.stdout.lower() or 'vtt' in r.stdout.lower():
                return {"available": True, "subtitles": "auto-generated", "recommendation": "Layer 2"}
    except Exception:
        pass
    return {"available": False, "subtitles": [], "recommendation": "skip"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--check-only", action="store_true")
    p.add_argument("--lang")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    langs = args.lang.split(",") if args.lang else None

    if args.check_only:
        r = check_availability(args.video)
    else:
        r = get_transcript(args.video, langs)

    if args.json:
        if r.get("success") and len(r.get("text", "")) > 500:
            r["text"] = r["text"][:500] + "..."
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif r.get("success"):
        print(f"✅ {r['method']} ({r['chars']} chars)")
        print(r['text'][:1000])
    else:
        print(f"❌ {r.get('error', r.get('recommendation'))}")


if __name__ == "__main__":
    main()
