---
name: hermes-skills-audit
description: Audit Hermes Agent skills — check dependency availability, install missing tools, and disable unused skills. Use when the user wants to clean up, optimize, or review their skills setup.
version: 1.0.0
author: Kars
---

# Hermes Skills Audit

Systematic approach to auditing, optimizing, and maintaining Hermes Agent skills.

## When to Use

- User asks to review/manage/clean up skills
- After a fresh Hermes install or migration
- Periodically to remove stale skills and install new dependencies

## Audit Process

### Step 1: Check API Keys

Read environment variables and the Hermes env file (under the hermes home directory, file `.env`) for required keys. Key skills and their required keys:

| Skill | Required Key(s) |
|-------|----------------|
| web_search | TAVILY_API_KEY |
| web_extract | FIRECRAWL_API_KEY |
| browser | BROWSERBASE_API_KEY + BROWSERBASE_PROJECT_ID |
| github-* | GITHUB_TOKEN or GH_TOKEN |
| notion | NOTION_API_KEY |
| linear | LINEAR_API_KEY |
| xitter | X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET |
| gif-search | TENOR_API_KEY |
| openhue | PHILIPS_HUE_BRIDGE_IP + PHILIPS_HUE_API_KEY |
| google-workspace | GOOGLE_OAUTH_CLIENT_ID + SECRET + REFRESH_TOKEN |
| himalaya (email) | SMTP_HOST/USER/PASS + IMAP_HOST/USER/PASS |
| tts | ELEVENLABS_API_KEY (or other TTS provider) |
| polymarket | POLYMARKET_API_KEY |

### Step 2: Check CLI Tools

Verify CLI availability with `which <cmd>`:

| Tool | Skills Enabled |
|------|---------------|
| `gh` | github-* (6 skills) |
| `jq` | gif-search, xitter, many curl-based skills |
| `himalaya` | himalaya (email) |
| `claude` | claude-code |
| `codex` | codex |
| `opencode` | opencode |
| `blogwatcher-cli` | blogwatcher |
| `nano-pdf` | nano-pdf |
| `gws` | google-workspace (fallback: Python client) |
| `mcporter` | mcporter |
| `ffmpeg` | media processing |
| `java` | minecraft-modpack-server |

### Step 3: Check Python Packages

Test imports in the Hermes venv (use `get_hermes_home()` from `hermes_constants` to locate the venv under the hermes home directory):

| Package | Skills Enabled |
|---------|---------------|
| `pptx` (from python-pptx) | powerpoint |
| `pymupdf` | ocr-and-documents (PDF) |
| `docx` (from python-docx) | ocr-and-documents (DOCX) |
| `pyfiglet` | ascii-art |
| `notion_client` | notion |
| `transformers` | mlops (HF models) |
| `diffusers` | stable-diffusion |
| `whisper` | whisper |
| `vllm` | serving-llms-vllm |
| `peft` | peft-fine-tuning |
| `trl` | fine-tuning-with-trl |
| `dspy` | dspy |
| `wandb` | weights-and-biases |
| `manim` | manim-video |

## Installing Dependencies

### ⚠️ No sudo Available

This environment (WSL2) does NOT have passwordless sudo. Use these alternatives:

**GitHub CLI (gh):**
```bash
# CRITICAL: Do NOT use `uv tool install gh` — that installs a Python wrapper (v0.0.4), NOT the real GitHub CLI
# Download the official binary from GitHub releases instead:
curl -sL -o /tmp/gh.tar.gz "https://github.com/cli/cli/releases/download/v2.67.0/gh_2.67.0_linux_amd64.tar.gz"
tar xzf /tmp/gh.tar.gz -C /tmp/
cp /tmp/gh_2.67.0_linux_amd64/bin/gh ~/.local/bin/gh
chmod +x ~/.local/bin/gh
```

**jq:**
```bash
curl -sL -o ~/.local/bin/jq "https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-linux-amd64"
chmod +x ~/.local/bin/jq
```

**Himalaya (email):**
```bash
# Get the latest version from https://api.github.com/repos/pimalaya/himalaya/releases/latest
curl -sL "https://github.com/pimalaya/himalaya/releases/download/v1.2.0/himalaya.x86_64-linux.tgz" | tar xz -C ~/.local/bin/
```

**Python packages (in Hermes venv):**
```bash
source <hermes_home>/hermes-agent/venv/bin/activate
python -m pip install <package_name>
```

### ⚠️ Known Pitfalls

- `uv tool install gh` installs a Python git wrapper (v0.0.4), NOT GitHub CLI. Always use the official binary.
- `npm install -g x-cli` installs a library with no binary — not a real CLI tool. X/Twitter skill relies on a hypothetical CLI that may not exist.
- `blogwatcher-cli` does not exist as an installable package (no PyPI, npm, or binary release found).
- `yaml.dump()` rewrites the Hermes config file completely — verify structure is preserved after editing. Use `patch` or targeted edits instead when possible.
- Ensure `~/.local/bin/` is in PATH.
- The Hermes config YAML is loaded via `hermes_cli.config.load_config()` and saved via `save_config()`. Use Python to edit it, not raw `yaml.dump()` which may reorder keys or change formatting.

## Disabling Skills

### Config Mechanism

Skills are disabled via the Hermes config (accessed through `hermes_cli.config`), under the `skills.disabled` key:

```yaml
skills:
  disabled:
    - skill-canonical-name
    - another-skill
```

Per-platform override is also supported:

```yaml
skills:
  platform_disabled:
    discord:
      - skill-name
    telegram:
      - skill-name
```

### ⚠️ Name Matching — CRITICAL

The disabled list uses the **frontmatter `name`** field from SKILL.md, NOT the directory name. Always verify by reading the frontmatter:

```bash
head -5 <hermes_home>/skills/<category>/<skill-dir>/SKILL.md
```

Known mismatches (directory → frontmatter):
| Directory Name | Frontmatter Name |
|---------------|-----------------|
| `vllm` | `serving-llms-vllm` |
| `audiocraft` | `audiocraft-audio-generation` |
| `segment-anything` | `segment-anything-model` |
| `stable-diffusion` | `stable-diffusion-image-generation` |
| `peft` | `peft-fine-tuning` |
| `trl-fine-tuning` | `fine-tuning-with-trl` |
| `lm-evaluation-harness` | `evaluating-llms-harness` |
| `creative-ideation` | `ideation` |
| `modal` | `modal-serverless-gpu` |

## Environment Notes

- **OS:** WSL2 Ubuntu 24.04
- **Python venv:** Under hermes home, `hermes-agent/venv/`
- **User bin:** `~/.local/bin/`
- **Config:** Under hermes home, `config.yaml`
- **Env vars:** Under hermes home, `.env`
- **Skills dir:** Under hermes home, `skills/`
- **Package manager:** `uv` available for tool installs
- **No sudo** — use direct binary downloads or pip/uv
