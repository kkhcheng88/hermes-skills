#!/usr/bin/env python3
"""
Batch image vision analysis for Discord channel exports.
Downloads images, analyzes with OpenRouter free vision models, saves to KB.

Usage:
  python3 discord_vision_batch.py --channel ElliottWave --file /mnt/c/TradingView/Discord/ElliottWave_90d.json
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

SKILL_DIR = Path(__file__).parent.parent
KB_DIR = SKILL_DIR / "knowledge"

OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
VISION_MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-3-27b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "google/gemma-3-12b-it:free",
]

VISION_PROMPT = (
    "这是一张金融技术分析图表，请详细分析："
    "1) 这是什么品种（股票/商品/指数）？"
    "2) 使用了什么技术分析方法（Elliott Wave/趋势线/支撑阻力/Fibonacci）？"
    "3) 关键价位（支撑位、阻力位、目标价）？"
    "4) 分析师的观点是什么？"
    "请用中文简洁回答。"
)


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return ""


def download_image(url: str, timeout: int = 15) -> bytes | None:
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200 and len(resp.content) > 1000:
            return resp.content
    except Exception:
        pass
    return None


def analyze_image(img_bytes: bytes, api_key: str) -> str | None:
    img_b64 = base64.b64encode(img_bytes).decode()
    
    for model in VISION_MODELS:
        try:
            resp = requests.post(
                OPENROUTER_API,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]}],
                    "max_tokens": 600,
                },
                timeout=30,
            )
            data = resp.json()
            if "choices" in data:
                result = data["choices"][0]["message"]["content"]
                if result and result.strip() and result.strip().lower() != "none":
                    return result.strip()
        except Exception:
            pass
        time.sleep(1)  # brief pause between model fallbacks
    
    return None


def load_existing_processed(kb_path: Path) -> set:
    """Get set of message IDs already processed for vision."""
    if not kb_path.exists():
        return set()
    with open(kb_path) as f:
        kb = json.load(f)
    processed = set()
    for entry in kb:
        eid = entry.get("id", "")
        if eid.endswith("_vision"):
            # Extract original message ID
            orig_id = eid.replace("discord_", "").replace("_vision", "")
            processed.add(orig_id)
    return processed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--limit", type=int, default=0, help="Max images to process (0=all)")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between requests")
    args = parser.parse_args()
    
    api_key = get_api_key()
    if not api_key:
        print("❌ No OPENROUTER_API_KEY found", file=sys.stderr)
        sys.exit(1)
    
    kb_path = KB_DIR / f"{args.channel}.json"
    already_processed = load_existing_processed(kb_path)
    print(f"Already processed: {len(already_processed)} images", file=sys.stderr)
    
    # Load export
    with open(args.file, 'r', encoding='utf-8') as f:
        export_data = json.load(f)
    
    # Find messages with images not yet processed
    image_msgs = []
    for msg in export_data.get("messages", []):
        msg_id = msg.get("id", "")
        if msg_id in already_processed:
            continue
        
        for att in msg.get("attachments", []):
            url = att.get("url", "")
            if any(ext in url.lower() for ext in [".jpg", ".png", ".jpeg", ".webp"]):
                image_msgs.append({
                    "id": msg_id,
                    "timestamp": msg.get("timestamp", ""),
                    "author": msg.get("author", {}).get("nickname") or msg.get("author", {}).get("name", "Unknown"),
                    "content": msg.get("content", "").strip(),
                    "image_url": url,
                })
                break
    
    if args.limit > 0:
        image_msgs = image_msgs[:args.limit]
    
    print(f"Images to process: {len(image_msgs)}", file=sys.stderr)
    
    # Load KB
    if kb_path.exists():
        with open(kb_path) as f:
            kb = json.load(f)
    else:
        kb = []
    
    success = 0
    failed = 0
    
    for i, item in enumerate(image_msgs):
        print(f"[{i+1}/{len(image_msgs)}] {item['id']} - {item['content'][:50]}", file=sys.stderr)
        
        img_bytes = download_image(item["image_url"])
        if not img_bytes:
            print(f"  ⚠️ Download failed", file=sys.stderr)
            failed += 1
            time.sleep(args.delay)
            continue
        
        analysis = analyze_image(img_bytes, api_key)
        if analysis:
            kb.insert(0, {
                "id": f"discord_{item['id']}_vision",
                "source": "discord",
                "author": item["author"],
                "timestamp": item["timestamp"],
                "content": item["content"],
                "vision_analysis": analysis,
                "stocks": [],
                "has_image_analysis": True,
            })
            success += 1
            print(f"  ✅ ({len(analysis)} chars)", file=sys.stderr)
        else:
            failed += 1
            print(f"  ❌ Analysis failed", file=sys.stderr)
        
        # Save incrementally every 10 entries
        if (success + failed) % 10 == 0:
            with open(kb_path, 'w', encoding='utf-8') as f:
                json.dump(kb, f, ensure_ascii=False, indent=2)
            print(f"  💾 Saved checkpoint ({len(kb)} entries)", file=sys.stderr)
        
        time.sleep(args.delay)
    
    # Final save
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    
    # Print summary to stdout (for notification)
    print(json.dumps({
        "channel": args.channel,
        "processed": len(image_msgs),
        "success": success,
        "failed": failed,
        "total_kb": len(kb),
    }))


if __name__ == "__main__":
    main()
