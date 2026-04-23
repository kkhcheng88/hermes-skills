#!/usr/bin/env python3
"""Retry failed images from ElliottWave batch processing."""

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
# Reorder: try nemotron first (less rate-limited), then gemma variants
VISION_MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
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


def download_image(url: str, timeout: int = 20) -> bytes | None:
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
                timeout=45,
            )
            data = resp.json()
            if "choices" in data:
                result = data["choices"][0]["message"]["content"]
                if result and result.strip() and result.strip().lower() != "none":
                    return result.strip()
        except Exception as e:
            print(f"    Model {model} error: {e}", file=sys.stderr)
        time.sleep(2)  # longer pause between fallbacks

    return None


def main():
    api_key = get_api_key()
    if not api_key:
        print("❌ No OPENROUTER_API_KEY found", file=sys.stderr)
        sys.exit(1)

    # Load failed IDs
    failed_path = SKILL_DIR / "failed_ids.json"
    with open(failed_path) as f:
        failed_ids = set(json.load(f))
    print(f"Failed IDs to retry: {len(failed_ids)}", file=sys.stderr)

    # Load export to get image URLs
    export_path = Path("/mnt/c/TradingView/Discord/ElliottWave_90d.json")
    with open(export_path, 'r', encoding='utf-8') as f:
        export_data = json.load(f)

    # Build retry list
    retry_list = []
    for msg in export_data.get("messages", []):
        msg_id = msg.get("id", "")
        if msg_id not in failed_ids:
            continue
        for att in msg.get("attachments", []):
            url = att.get("url", "")
            if any(ext in url.lower() for ext in [".jpg", ".png", ".jpeg", ".webp"]):
                retry_list.append({
                    "id": msg_id,
                    "timestamp": msg.get("timestamp", ""),
                    "author": msg.get("author", {}).get("nickname") or msg.get("author", {}).get("name", "Unknown"),
                    "content": msg.get("content", "").strip(),
                    "image_url": url,
                })
                break

    print(f"Retry list built: {len(retry_list)} images", file=sys.stderr)

    # Load existing KB
    kb_path = KB_DIR / "ElliottWave.json"
    with open(kb_path) as f:
        kb = json.load(f)

    success = 0
    failed = 0

    for i, item in enumerate(retry_list):
        print(f"[{i+1}/{len(retry_list)}] {item['id']} - {item['content'][:50]}", file=sys.stderr)

        img_bytes = download_image(item["image_url"])
        if not img_bytes:
            print(f"  ⚠️ Download failed (URL expired?)", file=sys.stderr)
            failed += 1
            time.sleep(3)
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

        # Save checkpoint every 10
        if (success + failed) % 10 == 0:
            with open(kb_path, 'w', encoding='utf-8') as f:
                json.dump(kb, f, ensure_ascii=False, indent=2)
            print(f"  💾 Saved checkpoint ({len(kb)} entries)", file=sys.stderr)

        time.sleep(4)  # 4s delay between images to avoid rate limits

    # Final save
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "channel": "ElliottWave",
        "retry_attempted": len(retry_list),
        "retry_success": success,
        "retry_failed": failed,
        "total_kb": len(kb),
    }))


if __name__ == "__main__":
    main()
