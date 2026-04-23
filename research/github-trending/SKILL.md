---
name: github-trending
description: Fetch GitHub trending repos (daily/weekly/monthly) and summarize what's hot. Use when Karson asks about trending repos, what's popular on GitHub, or wants a quick pulse on the dev community.
version: 1.0
---

# GitHub Trending Repos

Fetch and summarize GitHub trending repositories. No API key needed — scrapes the public trending page.

## Usage

```bash
# Daily trending (default)
python3 scripts/github_trending.py

# Weekly/monthly
python3 scripts/github_trending.py --since weekly
python3 scripts/github_trending.py --since monthly

# Filter by programming language
python3 scripts/github_trending.py --language python

# Filter by spoken language (repos with README/description primarily in that language)
python3 scripts/github_trending.py --spoken-language zh
python3 scripts/github_trending.py --spoken-language ja

# Shortcut: --chinese is same as --spoken-language zh
python3 scripts/github_trending.py --chinese

# JSON output
python3 scripts/github_trending.py --json --limit 5
```

## Output

Returns structured JSON with repo name, description, language, stars today, total stars, and URL.

## When to Use

- Karson asks "GitHub 今日有咩 trending?"
- Routine dev community check
- Looking for new tools/libraries to try

## Key Discoveries

- GitHub trending has **TWO separate filters**: Programming Language (URL path `/trending/{language}`) AND Spoken Language (query param `?spoken_language_code={code}`). They are independent!
- Chinese spoken language code: `zh` → URL: `github.com/trending?spoken_language_code=zh`
- Other codes: `en`, `ja`, `ko`, `de`, `fr`, etc. — standard ISO 639-1 codes
- The Spoken Language filter affects repos whose README/description is primarily in that language

## Dependencies

- `requests` + `beautifulsoup4` (installed in hermes-agent venv)
- Run with: `~/.hermes/hermes-agent/venv/bin/python3 scripts/github_trending.py`
