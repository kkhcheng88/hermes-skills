---
name: skills-health-check
description: Audit installed skills for dependency readiness. Check which skills have their required API keys, CLI tools, Python packages, and config. Identify broken, redundant, and missing skills. Install useful dependencies and disable unused skills.
version: 1.0.0
author: Kars (auto-generated)
---

# Skills Health Check & Cleanup

Audit the full skills inventory, identify what works and what doesn't, install missing dependencies, and disable irrelevant skills.

## When to Use

- User asks "what skills do I have", "which skills actually work", "can you review your skills"
- After a fresh Hermes install or major upgrade
- When the user wants to clean up or optimize their skills setup

## Phase 1: Dependency Audit

Check three categories of dependencies simultaneously:

### 1. API Keys
Check common env vars from the running process environment and from ~/.hermes/.env for credential presence (value masked, not logged).

### 2. CLI Tools (via `shutil.which`)
Common tools: gh, jq, himalaya, mcporter, gws, nano-pdf, blogwatcher-cli, ffmpeg, magick, docker, java, hamelnb, claude, codex, opencode

### 3. Python Packages (via `importlib`)
Common packages: pptx (installed as python-pptx), pymupdf, docx, pyfiglet, notion_client, transformers, vllm, diffusers, whisper, dspy, wandb, manim

### 4. Config Check
Read the Hermes config file to see current disabled skills list and platform overrides.

## Phase 2: Skills Directory Mapping

Skills live under `~/.hermes/skills/` as directories with SKILL.md files.

**CRITICAL: Directory name does not equal skill name.** The actual skill name comes from the YAML frontmatter `name:` field in each SKILL.md. Always read frontmatter when checking disabled status.

Example mismatch:
- Directory: `~/.hermes/skills/mlops/inference/vllm/SKILL.md`
- Frontmatter: `name: serving-llms-vllm`
- Disabled list must use `serving-llms-vllm`, NOT `vllm`

## Phase 3: Categorize Skills

| Status | Meaning |
|--------|---------|
| Fully available | All dependencies met |
| Partially available | Some deps missing, basic functionality works |
| Unavailable | Critical dependency missing |

## Phase 4: Install Missing Dependencies

### No-sudo Installation Methods (WSL safe)

| Tool | Method |
|------|--------|
| gh (GitHub CLI) | Download binary from GitHub releases tar.gz, extract, copy to ~/.local/bin/ |
| jq | Download static binary from GitHub releases to ~/.local/bin/ |
| himalaya | Download from GitHub releases (org: pimalaya/himalaya) |
| Python packages | Activate Hermes venv, then `python -m pip install <pkg>` |

**Pitfall: `uv tool install gh` installs a Python wrapper (gh==0.0.4), NOT the real GitHub CLI.** Always use the binary release instead.

**Pitfall: `python-pptx` imports as `pptx`, not `python_pptx`.**

**Pitfall: If `pip` is not found in venv, run `python -m ensurepip` first.**

## Phase 5: Disable Unused Skills

Use the built-in disable mechanism in config.yaml `skills.disabled` list.

The matching code is in `tools/skills_tool.py` - it uses `frontmatter.get("name", skill_dir.name)` to match against the disabled list.

### Per-Platform Disable
Also supports `skills.platform_disabled.<platform>` for platform-specific overrides.

## Phase 6: Verify

After changes, verify:
1. Config file preserves all sections after modification (check with patch mode, not full rewrite)
2. All frontmatter names match disabled list entries
3. CLI tools are on PATH (~/.local/bin should be in PATH)
4. Python packages import correctly in the Hermes venv

## Pitfalls

1. **Full config rewrite can corrupt config.yaml** - use `patch` mode for targeted edits to the skills section only, not `yaml.dump` on the entire file. This preserves custom_providers, discord config, security settings, etc.
2. **Sandbox env vars are empty** - `execute_code` runs in an isolated sandbox that does not inherit the Hermes environment. Run dependency checks from the main agent context instead.
3. **Skills take effect on next session** - the skills list is loaded at startup, not hot-reloaded mid-conversation.
