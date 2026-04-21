---
name: hermes-gateway-troubleshooting
description: Start and troubleshoot the Hermes messaging gateway (Discord, Telegram, Slack, etc.)
---

# Hermes Gateway - Start & Troubleshoot

## Starting the Gateway

Preferred method:
```bash
hermes gateway
```

Alternative:
```bash
source venv/bin/activate && python -m gateway.run
```

## Where Logs Go

The gateway does NOT produce stdout output. Check logs instead:
- `~/.hermes/logs/gateway.log` -- platform connection events
- `~/.hermes/logs/errors.log` -- warnings and shutdown diagnostics
- `~/.hermes/logs/agent.log` -- agent conversation activity

## Discord Config Checklist

1. `.env` file needs:
   - `DISCORD_BOT_TOKEN` -- bot token from Discord Developer Portal
   - `DISCORD_ALLOWED_USERS` -- comma-separated Discord user IDs
   - `DISCORD_HOME_CHANNEL` -- default channel ID

2. `config.yaml` discord section (optional):
   - `require_mention: true` -- bot only responds when @mentioned
   - `auto_thread: true` -- creates threads for conversations

3. Verify connection: logs should show `[Discord] Connected as <BotName>#<Discriminator>` and `[Discord] Synced N slash command(s)`.

## Multi-Process Conflict Detection

The gateway has a built-in conflict detector that warns about other running hermes processes. If it detects `hermes chat` or another gateway running, it may shut down after ~30 seconds with a message like:
```
Shutdown diagnostic -- other hermes processes running
```

**Important diagnostic pitfall:** When conflict detection triggers, the gateway dies silently — `gateway.log` will NOT show new entries. Instead, check `~/.hermes/logs/errors.log` for the "Shutdown diagnostic" message listing the conflicting PIDs. If you restart the gateway and `gateway.log` hasn't updated after 10+ seconds, immediately check `errors.log`.

Workaround: either stop other hermes sessions first, or the gateway may coexist depending on the version. The most common conflict is a running `hermes` CLI chat session (the interactive terminal session). You must exit the CLI chat before the gateway can stay alive.

## Restarting the Gateway After Config Changes

When you change config (e.g. `require_mention`), the gateway needs a restart:
1. Kill the process (find PID via `ps aux | grep "hermes gateway"`)
2. Wait a moment for clean shutdown (`sleep 2`)
3. Start again: `hermes gateway`
4. Verify reconnection in `~/.hermes/logs/gateway.log` -- look for `[Discord] Connected as ...`

## Common Issues

- **Bot not appearing online**: Gateway process likely died. Check `~/.hermes/logs/errors.log`.
- **No stdout at all**: Expected behavior. Always check log files.
- **Permission errors**: Ensure bot has proper permissions in the Discord server/channel.
- **Slash commands not showing**: May need to re-invite the bot with `applications.commands` scope.
