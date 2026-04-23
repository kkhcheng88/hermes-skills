#!/usr/bin/env python3
"""
Discord KOL — Export messages via DiscordChatExporter + auto-parse into KB.

Usage:
  python3 discord_export.py --token TOKEN --channel-id ID --channel-name NAME [--days N]
  
  Or import and call:
  from discord_export import export_channel
  export_channel(token, channel_id, channel_name, days=14)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
KB_DIR = SKILL_DIR / "knowledge"
STATE_DIR = SKILL_DIR / "state"
EXPORT_DIR = Path("/mnt/c/TradingView/Discord")

CLI_PATH = r"C:\Game\DiscordChatExporter\DiscordChatExporter.Cli.exe"
CST = timezone(timedelta(hours=8))


def export_channel(token: str, channel_id: str, channel_name: str,
                   days: int = 30, output_dir: Path = None) -> str:
    """
    Export Discord channel messages and parse into knowledge base.
    Returns path to the exported JSON file.
    """
    output_dir = output_dir or EXPORT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{channel_name}.json"
    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
    
    # Run DiscordChatExporter via cmd.exe (WSL → Windows)
    cmd = [
        "cmd.exe", "/c",
        CLI_PATH, "export",
        "-t", token,
        "-c", channel_id,
        "-f", "Json",
        "-o", str(output_file),
        "--after", after_date,
    ]
    
    print(f"📤 Exporting {channel_name} (last {days} days)...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    
    stdout = result.stdout.decode('utf-8', errors='replace')
    stderr = result.stderr.decode('utf-8', errors='replace')
    
    if result.returncode != 0:
        print(f"  ❌ Export failed: {stderr[:300]}", file=sys.stderr)
        return None
    
    print(f"  ✅ Exported to {output_file}", file=sys.stderr)
    
    # Auto-parse into knowledge base
    from discord_parse import parse_and_save
    stats = parse_and_save(str(output_file), channel_name)
    print(f"  📚 KB: {stats['new']} new, {stats['total']} total entries", file=sys.stderr)
    
    return str(output_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="Discord token")
    parser.add_argument("--channel-id", required=True)
    parser.add_argument("--channel-name", required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    
    export_channel(args.token, args.channel_id, args.channel_name, args.days,
                   Path(args.output_dir) if args.output_dir else None)


if __name__ == "__main__":
    main()
