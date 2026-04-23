---
name: third-party-skill-installer
description: Install and adapt third-party GitHub skills (designed for Claude Code or other agents) into the Hermes skill system. Use when the user shares a GitHub repo URL of a skill/tool and asks to install it, or when encountering a SKILL.md designed for `~/.claude/skills/` that needs porting to `~/.hermes/skills/`.
version: 1.0.0
---

# Third-Party Skill Installer for Hermes

Adapt skills from Claude Code repos (`~/.claude/skills/`) or other agent frameworks to work with Hermes Agent (`~/.hermes/skills/`).

## Trigger

- User shares a GitHub repo URL and says "install this skill"
- You find a `SKILL.md` designed for Claude Code that needs porting
- A skill references `~/.claude/config.json` or Claude-specific paths

## Installation Steps

### 1. Clone the Repo

```bash
cd ~/.hermes/skills && git clone <repo-url> <skill-name>
```

### 2. Audit Dependencies

Check `requirements.txt`, `install.sh`, and any Python scripts for required packages.

```bash
# List all Python imports used
grep -rh '^\(import\|from\) ' ~/.hermes/skills/<skill-name>/*.py ~/.hermes/skills/<skill-name>/**/*.py 2>/dev/null | sort -u
```

### 3. Install Python Dependencies

WSL/Ubuntu systems use PEP 668 externally-managed Python. Use `--break-system-packages`:

```bash
pip3 install --break-system-packages <packages>
```

If the repo has a `requirements.txt`:
```bash
pip3 install --break-system-packages -r ~/.hermes/skills/<skill-name>/requirements.txt
```

For packages installed from git (e.g. `notebooklm-py`):
```bash
pip3 install --break-system-packages git+https://github.com/<user>/<repo>.git
```

### 4. Fix Bugs in Third-Party Code

Claude Code skills may have bugs when run outside their expected environment. Common issues:

- **Missing imports** — e.g. `Optional` from `typing` not imported
- **Path assumptions** — hardcoded `~/.claude/skills/` paths
- **Python version incompatibilities** — code written for 3.9 may need tweaks for 3.12

Test the server loads:
```bash
python3 -c "import sys; sys.path.insert(0, '<server_dir>'); from server import mcp; print('OK')"
```

### 5. Register MCP Servers

Claude Code skills often bundle MCP servers configured via `~/.claude/config.json`. In Hermes, use:

```bash
hermes mcp add <name> --command <cmd> --args "<arg1>" --args "<arg2>"
```

Then pipe `y` to confirm tool enabling:
```bash
echo "y" | hermes mcp add <name> --command <cmd> --args "<arg>"
```

Verify:
```bash
hermes mcp list
```

### 6. Rewrite SKILL.md for Hermes

Replace the Claude Code `SKILL.md` with a Hermes-compatible version:

**Keep from original:**
- Description and purpose
- Supported input types / content sources
- CLI commands and scripts (paths, arguments)
- Workflows and processing steps
- Environment variables needed

**Remove/replace:**
- Claude Code-specific paths (`~/.claude/skills/`)
- Claude Code MCP config instructions (`~/.claude/config.json`)
- Claude-specific trigger syntax (`/skill-name [input]`)
- References to Claude Code tools not available in Hermes

**Add for Hermes:**
- Proper YAML frontmatter (name, description, version, metadata)
- How to trigger in Hermes (natural language, not slash commands)
- MCP server name registered in Hermes
- Note about `/reset` needed after MCP tool changes

### 7. Verify

```bash
# Check skill is registered
hermes skills list | grep <skill-name>

# Check MCP server (if any)
hermes mcp list

# Run env check if the skill has one (may need path fixes)
python3 ~/.hermes/skills/<skill-name>/check_env.py
```

## Pitfalls

- **`check_env.py` often checks Claude paths** — don't trust its results for Hermes. Manually verify via `hermes mcp list` and `hermes skills list`.
- **MCP server auto-detection** — `hermes mcp add` will connect to the server and ask to enable tools. Pipe `y` to auto-confirm.
- **External MCP servers may timeout** — if the server is slow to start, the add command may timeout. Retry.
- **Some skills need browser auth** — `notebooklm login`, OAuth flows, etc. Flag these to the user.
- **Playwright needs chromium installed separately** — `python3 -m playwright install chromium`
