#!/usr/bin/env python3
"""Fetch GitHub trending repos + Chinese-authored repos via search API."""

import argparse
import json
import re
import sys

import requests
from bs4 import BeautifulSoup


def fetch_trending(since: str = "daily", language: str = "", spoken_language: str = "", limit: int = 25) -> list[dict]:
    """Scrape GitHub trending page."""
    url = "https://github.com/trending"
    if language:
        url += f"/{language.lower()}"

    params = {"since": since}
    if spoken_language:
        params["spoken_language_code"] = spoken_language
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
    }

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article.Box-row")

    repos = []
    for article in articles[:limit]:
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        full_name = h2.get("href", "").strip("/")

        p = article.select_one("p")
        desc = p.get_text(strip=True) if p else ""

        lang_span = article.select_one("[itemprop='programmingLanguage']")
        lang = lang_span.get_text(strip=True) if lang_span else ""

        star_links = article.select("a.Link--muted")
        total_stars = ""
        for link in star_links:
            if "/stargazers" in link.get("href", ""):
                total_stars = link.get_text(strip=True).replace(",", "")
                break

        today_span = article.select_one("span.d-inline-block.float-sm-right")
        stars_today = ""
        if today_span:
            match = re.search(r"([\d,]+)\s+stars?\s+today", today_span.get_text(strip=True))
            if match:
                stars_today = match.group(1).replace(",", "")

        repos.append({
            "name": full_name,
            "description": desc,
            "language": lang,
            "stars_today": int(stars_today) if stars_today else 0,
            "total_stars": int(total_stars) if total_stars else 0,
            "url": f"https://github.com/{full_name}",
        })

    return repos


def fetch_chinese_repos(limit: int = 20) -> list[dict]:
    """Fetch hot repos with Chinese descriptions via GitHub search API."""
    url = "https://api.github.com/search/repositories"
    # Search for repos created in last 30 days with Chinese characters
    params = {
        "q": "stars:>20 pushed:>2026-04-01 language:NOT+generated",
        "sort": "stars",
        "order": "desc",
        "per_page": 100,
    }
    headers = {"Accept": "application/vnd.github.v3+json"}
    gh_token = _get_gh_token()
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Filter for repos with Chinese in name or description
    chinese_repos = []
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')

    for item in data.get("items", []):
        name = item.get("full_name", "")
        desc = item.get("description") or ""
        readme = ""

        if chinese_pattern.search(name) or chinese_pattern.search(desc):
            chinese_repos.append({
                "name": name,
                "description": desc,
                "language": item.get("language") or "",
                "stars_today": 0,
                "total_stars": item.get("stargazers_count", 0),
                "url": item.get("html_url", ""),
                "forks": item.get("forks_count", 0),
                "topics": item.get("topics", []),
            })
            if len(chinese_repos) >= limit:
                break

    # If not enough, also try a more targeted Chinese query
    if len(chinese_repos) < limit:
        params["q"] = "星星:>30 pushed:>2026-01-01 in:description"
        try:
            resp2 = requests.get(url, params=params, headers=headers, timeout=30)
            for item in resp2.json().get("items", []):
                name = item.get("full_name", "")
                if any(r["name"] == name for r in chinese_repos):
                    continue
                desc = item.get("description") or ""
                chinese_repos.append({
                    "name": name,
                    "description": desc,
                    "language": item.get("language") or "",
                    "stars_today": 0,
                    "total_stars": item.get("stargazers_count", 0),
                    "url": item.get("html_url", ""),
                    "forks": item.get("forks_count", 0),
                    "topics": item.get("topics", []),
                })
                if len(chinese_repos) >= limit:
                    break
        except Exception:
            pass

    return chinese_repos


def _get_gh_token() -> str:
    """Try to get GitHub token from gh CLI or env."""
    import os
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        import subprocess
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def fetch_readme_summary(repo_name: str) -> str:
    """Fetch first ~300 chars of README for a repo."""
    try:
        url = f"https://raw.githubusercontent.com/{repo_name}/main/README.md"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 404:
            url = f"https://raw.githubusercontent.com/{repo_name}/master/README.md"
            resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            text = resp.text
            # Strip markdown formatting noise, get first meaningful paragraph
            lines = text.split("\n")
            meaningful = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("![") or line.startswith("```"):
                    continue
                meaningful.append(line)
                if len(" ".join(meaningful)) > 300:
                    break
            return " ".join(meaningful)[:400]
    except Exception:
        pass
    return ""


def format_output(repos: list[dict], as_json: bool = False, with_readme: bool = False) -> str:
    """Format repos for display."""
    if as_json:
        return json.dumps(repos, ensure_ascii=False, indent=2)

    if not repos:
        return "No trending repos found."

    lines = []
    for i, r in enumerate(repos, 1):
        stars_info = f"⭐ +{r['stars_today']}" if r.get("stars_today") else f"⭐ {r['total_stars']}"
        lang = f" [{r['language']}]" if r.get("language") else ""
        lines.append(f"{i}. **{r['name']}**{lang} {stars_info}")
        if r.get("description"):
            lines.append(f"   {r['description'][:150]}")
        if with_readme:
            readme = fetch_readme_summary(r["name"])
            if readme:
                lines.append(f"   📖 {readme[:200]}")
        lines.append(f"   🔗 {r['url']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub trending repos")
    parser.add_argument("--since", default="daily", choices=["daily", "weekly", "monthly"])
    parser.add_argument("--language", default="", help="Filter by programming language")
    parser.add_argument("--spoken-language", default="", help="Filter by spoken language (e.g. zh, en, ja)")
    parser.add_argument("--chinese", action="store_true", help="Shortcut for --spoken-language zh")
    parser.add_argument("--limit", type=int, default=25, help="Max repos to return")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--readme", action="store_true", help="Include README summaries")
    args = parser.parse_args()

    if args.chinese:
        args.spoken_language = "zh"

    repos = fetch_trending(args.since, args.language, args.spoken_language, args.limit)

    print(format_output(repos, args.json, args.readme))


if __name__ == "__main__":
    main()
