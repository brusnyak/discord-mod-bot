# Discord Moderation Bot

Warn/kick/ban moderation ladder, auto-moderation, ticket system, auto-role, and audit logging — all in one Discord bot. Designed for community servers that need structured moderation without third-party bots.

## Architecture

```mermaid
graph TB
    User([Member]) -- message / slash command --> DC[Discord Gateway]
    Mod([Moderator]) -- "/warn, /kick, /ban" --> DC
    Admin([Server Admin]) -- "/setup, /tickets" --> DC

    DC --> Bot[discord.py<br//>Bot Client]
    Bot --> CMD[CommandTree<br/>& Slash Commands]
    Bot --> EVT[Event Listeners]

    CMD --> ModCog[Moderation Cog<br/>&nbsp;warn/kick/ban/mute]
    CMD --> AdminCog[Admin Cog<br/>&nbsp;setup/config/purge]
    CMD --> TicketCog[Ticket System<br/>&nbsp;open/close/claim]

    EVT --> AutoMod[Auto-Mod<br/>&nbsp;spam/links/words]
    EVT --> AutoRole[Auto-Role<br/>&nbsp;join roles]
    EVT --> Audit[Audit Logger<br/>&nbsp;mod actions → channel]

    ModCog --> DB[(SQLite<br/>&nbsp;warnings<br/>&nbsp;mod logs<br/>&nbsp;tickets)]
    TicketCog --> DB
    AutoMod --> DB
    AdminCog --> DB

    AutoMod --> AI[OpenRouter LLM<br/>&nbsp;(optional content check)]
    AI -.->|optional| AutoMod

    ModCog --> Webhook[Ops Webhook<br/>&nbsp;POST to dashboard]
    AdminCog --> Webhook

    style User fill:#e1f5fe
    style Mod fill:#fff3e0
    style Admin fill:#fce4ec
    style DC fill:#e8f5e9
    style DB fill:#fce4ec
```

## Tech Stack

- **Runtime:** Python 3.11+
- **Framework:** discord.py (v2.x, slash commands)
- **Database:** SQLite (single-file)
- **AI moderation:** OpenRouter (optional, LLM-based content analysis)
- **Deploy:** systemd service on Ubuntu

## Features

| Feature | Details |
|---------|---------|
| Moderation ladder | Warn (3 strikes) → mute → kick → ban, configurable thresholds |
| Slash commands | Full `/warn`, `/kick`, `/ban`, `/mute`, `/unmute`, `/purge` |
| Auto-moderation | Spam detection, link filtering, word filters |
| Ticket system | Users open tickets, mods claim/close, persistent threads |
| Auto-role | Assign roles on member join |
| Audit logging | All mod actions logged to a dedicated channel |
| LLM moderation | Optional OpenRouter integration for content analysis |
| Case system | Each infraction tracked with ID, timestamp, evidence |
| Ops webhook | Mod actions posted to external dashboard |

## Setup

```bash
# 1. Clone and install
git clone <repo-url>
cd discord-mod-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Set DISCORD_BOT_TOKEN, TEST_GUILD_ID, BOT_OPS_WEBHOOK_URL (optional)
# Set OPENROUTER_API_KEY (optional, for LLM moderation)

# 3. Run
python -m main
```

### Production (systemd)

```bash
sudo cp deploy/discord-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now discord-bot
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Bot token from Discord Developer Portal |
| `TEST_GUILD_ID` | No | Guild ID for global slash command registration |
| `BOT_OPS_WEBHOOK_URL` | No | Ops dashboard webhook |
| `OPENROUTER_API_KEY` | No | API key for LLM-powered content moderation |
| `OPENROUTER_MODEL` | No | Model override, default: openrouter/free |

## Slash Commands

| Command | Permission | Description |
|---------|-----------|-------------|
| `/warn <user> [reason]` | Kick Members | Issue warning (3rd = auto mute) |
| `/kick <user> [reason]` | Kick Members | Kick member |
| `/ban <user> [reason] [days]` | Ban Members | Ban member, optional message delete days |
| `/mute <user> <duration> [reason]` | Moderate Members | Time-out member |
| `/unmute <user>` | Moderate Members | Remove time-out |
| `/purge <count>` | Manage Messages | Bulk delete messages |
| `/ticket [user]` | Manage Channels | Open a mod ticket |
| `/ticket close` | None | Close your ticket |
| `/setup` | Administrator | Configure auto-role, log channel, thresholds |

## Project Structure

```
discord-mod-bot/
├── main.py              # Entry point, bot setup
├── config.py            # Config from env vars
├── ops_webhook.py       # Dashboard event posting
├── cogs/
│   ├── moderation.py    # Warn/kick/ban/mute ladder
│   ├── admin.py         # Setup, config, purge
│   ├── automod.py       # Spam/links/word filters
│   ├── tickets.py       # Ticket open/close/claim
│   ├── autorole.py      # Join role assignment
│   └── logging_cog.py   # Audit log to channel
├── utils/
│   ├── checks.py        # Permission helpers
│   └── formatting.py    # Embed builders
├── db/
│   ├── db.py            # SQLite connection, queries
│   └── schema.sql       # Table definitions
└── deploy/              # systemd service file
```
