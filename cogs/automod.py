import logging
import time

import discord
from discord.ext import commands

from db.db import get_db
from config import load_config
from ops_webhook import send_to_ops_lab

logger = logging.getLogger(__name__)

RATE_LIMIT = (5, 10)  # 5 messages in 10 seconds

PROFANITY_LIST = [
    "fuck", "shit", "asshole", "bitch", "damn",
    "cunt", "motherfucker", "dickhead",
]

MASS_MENTION_THRESHOLD = 5


class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.msg_times: dict[int, list[float]] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        author_id = message.author.id
        now = time.time()

        # Rate limiting
        self.msg_times.setdefault(author_id, []).append(now)
        self.msg_times[author_id] = [t for t in self.msg_times[author_id] if now - t < RATE_LIMIT[1]]

        if len(self.msg_times[author_id]) > RATE_LIMIT[0]:
            await message.delete()
            await self._auto_warn(message.author, message.guild, "Spam (rate limit exceeded)")
            return

        # Mass mention detection
        if len(message.mentions) > MASS_MENTION_THRESHOLD:
            await message.delete()
            await self._auto_warn(message.author, message.guild, "Mass mention")
            return

        # Profanity filter
        content_lower = message.content.lower()
        for word in PROFANITY_LIST:
            if word in content_lower:
                await message.delete()
                await self._auto_warn(message.author, message.guild, f"Profanity: {word}")
                return

    async def _auto_warn(self, user: discord.Member, guild: discord.Guild, reason: str):
        async with get_db() as db:
            await db.execute(
                "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
                (guild.id, user.id, self.bot.user.id, reason),
            )
            await db.commit()

        try:
            await user.send(f"⚠️ Auto-mod warning: {reason}")
        except discord.Forbidden:
            pass

        # Push to ops-lab dashboard
        cfg = load_config()
        if cfg.bot_ops_webhook:
            send_to_ops_lab(
                webhook_url=cfg.bot_ops_webhook,
                event_id=f"automod_{int(time.time())}",
                author_name=user.display_name,
                author_username=user.name,
                content=f"[AutoMod] {reason}",
            )

        logger.info("Auto-mod warn %s in %s: %s", user, guild.name, reason)


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))
