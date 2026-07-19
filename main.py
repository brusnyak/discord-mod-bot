#!/usr/bin/env python3
"""
Discord Moderation Bot — warn/kick/ban ladder, auto-mod, tickets, auto-role, audit logging.

Run:
    DISCORD_BOT_TOKEN=... python -m main
"""
import logging
import json
import sys
import urllib.error
import urllib.request

import discord
from discord import app_commands
from discord.ext import commands

from config import load_config
from db.db import get_db
from db.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("discord.gateway").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True


def main():
    cfg = load_config()
    if not cfg.bot_token:
        logger.error("DISCORD_BOT_TOKEN is not set")
        sys.exit(1)

    bot = commands.Bot(command_prefix="!", intents=INTENTS, help_command=None)

    @bot.tree.command(name="help", description="Show what this demo moderation bot can do")
    async def help_command(interaction: discord.Interaction):
        await interaction.response.send_message(help_text(), ephemeral=True)

    @bot.tree.command(name="status", description="Show moderation bot status")
    async def status_command(interaction: discord.Interaction):
        await interaction.response.send_message(
            "Moderation bot is online. Slash commands are synced for this server.",
            ephemeral=True,
        )

    @bot.tree.command(name="ask", description="Ask the moderation assistant")
    @app_commands.describe(question="Question about moderation, rules, or server operations")
    async def ask_command(interaction: discord.Interaction, question: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        answer = await ask_llm(cfg, question, interaction.user.display_name)
        await interaction.followup.send(answer, ephemeral=True)

    @bot.tree.command(name="demo_incident", description="Run a safe moderation workflow demo")
    @app_commands.describe(kind="Demo incident type")
    @app_commands.choices(kind=[
        app_commands.Choice(name="spam burst", value="spam"),
        app_commands.Choice(name="mass mentions", value="mentions"),
        app_commands.Choice(name="profanity", value="profanity"),
    ])
    async def demo_incident(interaction: discord.Interaction, kind: app_commands.Choice[str]):
        reasons = {
            "spam": "Spam burst: 6 messages inside 10 seconds",
            "mentions": "Mass mentions: 6 users mentioned in one message",
            "profanity": "Profanity match in public channel",
        }
        reason = reasons[kind.value]
        async with get_db() as db:
            await db.execute(
                "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
                (interaction.guild_id, interaction.user.id, bot.user.id if bot.user else 0, f"[demo] {reason}"),
            )
            await db.commit()
            row = await db.execute_fetchall(
                "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ? AND active = 1",
                (interaction.guild_id, interaction.user.id),
            )
        warn_count = row[0][0]
        next_action = "DM warning only"
        if warn_count >= 5:
            next_action = "Would kick at configured threshold"
        elif warn_count >= 4:
            next_action = "Would apply 7-day timeout"
        elif warn_count >= 3:
            next_action = "Would apply 24-hour timeout"
        elif warn_count >= 2:
            next_action = "Would apply 1-hour timeout"

        embed = discord.Embed(
            title="Moderation Workflow Demo",
            description="Safe simulation. No message was deleted and no member was punished.",
            color=0x2F80ED,
        )
        embed.add_field(name="Detected", value=reason, inline=False)
        embed.add_field(name="Action ladder", value=next_action, inline=False)
        embed.add_field(name="Active warnings for you", value=str(warn_count), inline=True)
        embed.add_field(name="Stored", value="Warning row written to SQLite", inline=True)
        embed.add_field(
            name="Try next",
            value="Run `/demo_incident` again, then `/pardon user:@you` to remove the latest warning.",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return
        text = message.content.strip().lower()
        if text in {"/help", "!help", "help"}:
            await message.reply(help_text())
            return
        if bot.user and bot.user in message.mentions:
            prompt = message.content.replace(bot.user.mention, "").strip()
            if not prompt:
                await message.reply(
                    "I handle moderation workflows: `/demo_incident`, `/ticket`, `/warn`, `/pardon`, `/config`, and auto-mod. Ask me a moderation question or use `/ask`."
                )
                return
            async with message.channel.typing():
                await message.reply(await ask_llm(cfg, prompt, message.author.display_name))
            return
        if text in {"hey", "hi", "hello", "hey there"}:
            await message.reply("I can moderate this server. Try `/help`, `/ticket`, or `/warn @user reason`.")
            return
        await bot.process_commands(message)

    @bot.event
    async def on_ready():
        await init_db()
        logger.info("Database initialized.")

        # Load cogs
        await bot.load_extension("cogs.moderation")
        await bot.load_extension("cogs.automod")
        await bot.load_extension("cogs.tickets")
        await bot.load_extension("cogs.autorole")
        await bot.load_extension("cogs.logging_cog")
        await bot.load_extension("cogs.admin")
        logger.info("All cogs loaded.")

        # Sync commands
        if cfg.test_guild_id:
            guild = discord.Object(id=cfg.test_guild_id)
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            logger.info("Commands synced to test guild %s", cfg.test_guild_id)
        else:
            await bot.tree.sync()
            logger.info("Global commands synced.")

        logger.info("Bot ready as %s", bot.user)

    bot.run(cfg.bot_token, log_handler=None)


def help_text() -> str:
    return (
        "Discord moderation demo\n\n"
        "Try these slash commands:\n"
        "- `/help` - this guide\n"
        "- `/status` - bot health\n"
        "- `/ask question:...` - chat with the moderation assistant\n"
        "- `/demo_incident kind:...` - safe proof flow: detect -> warn record -> action ladder\n"
        "- `/ticket reason:...` - create a private support ticket\n"
        "- `/ticket_close` - close the current ticket channel\n"
        "- `/warn user:... reason:...` - add a warning and apply the warning ladder\n"
        "- `/pardon user:...` - remove the latest active warning\n"
        "- `/config setting:... value:...` - configure mod log, autorole, thresholds\n\n"
        "Auto-mod also watches for spam bursts, mass mentions, invite spam, and profanity."
    )


async def ask_llm(cfg, question: str, user_name: str) -> str:
    if not cfg.openrouter_api_key:
        return (
            "LLM mode is not configured. Add `OPENROUTER_API_KEY` to the project root or bot `.env`; "
            "the moderation commands still work."
        )

    import asyncio

    def _call():
        payload = {
            "model": cfg.openrouter_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Piligrim, a Discord moderation operations assistant. "
                        "Answer in 3-6 short lines. Speak as this bot, not as a generic adviser. "
                        "Use the bot's actual capabilities: /demo_incident, /ticket, /warn, /pardon, /config, "
                        "spam/mass-mention/profanity auto-mod, SQLite warning history, and mod-log events. "
                        "Do not recommend other bots. Do not claim you performed an action unless the user used a command."
                    ),
                },
                {
                    "role": "user",
                    "content": f"{user_name} asks: {question}",
                },
            ],
            "temperature": 0.3,
            "max_tokens": 350,
        }
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {cfg.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/yegor/jobiz",
                "X-Title": "Jobiz Discord Moderation Demo",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.warning("OpenRouter moderation assistant failed: %s", exc)
            return "LLM mode failed for this request. The moderation commands are still online."

    return await asyncio.get_running_loop().run_in_executor(None, _call)


if __name__ == "__main__":
    main()
