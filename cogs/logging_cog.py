import logging

import discord
from discord.ext import commands

from db.db import get_db
from utils.formatting import moderation_embed

logger = logging.getLogger(__name__)


class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _log_channel(self, guild_id: int) -> discord.TextChannel | None:
        async with get_db() as db:
            row = await db.execute_fetchall(
                "SELECT mod_log_channel_id FROM guilds WHERE id = ?", (guild_id,)
            )
        if not row or not row[0][0]:
            return None
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None
        return guild.get_channel(row[0][0])

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        channel = await self._log_channel(guild.id)
        if not channel:
            return
        embed = moderation_embed(
            title="🔨 Member Banned",
            description=f"{user} ({user.id})",
            color=0xFF0000,
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = await self._log_channel(member.guild.id)
        if not channel:
            return
        embed = moderation_embed(
            title="👋 Member Left",
            description=f"{member} ({member.id})",
            color=0x888888,
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        channel = await self._log_channel(message.guild.id)
        if not channel:
            return
        embed = moderation_embed(
            title="🗑️ Message Deleted",
            description=f"**Author:** {message.author}\n**Channel:** {message.channel.mention}\n**Content:** {message.content or '[non-text]'}",
            color=0xFFAA00,
        )
        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Logging(bot))
