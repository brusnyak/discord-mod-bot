import logging

import discord
from discord.ext import commands

from db.db import get_db

logger = logging.getLogger(__name__)


class AutoRole(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        async with get_db() as db:
            row = await db.execute_fetchall(
                "SELECT autorole_id FROM guilds WHERE id = ?", (member.guild.id,)
            )

        if not row or not row[0][0]:
            return

        role = member.guild.get_role(row[0][0])
        if role:
            try:
                await member.add_roles(role, reason="Auto-role on join")
                logger.info("Assigned role %s to %s in %s", role.name, member, member.guild.name)
            except discord.Forbidden:
                logger.warning("Cannot assign role %s — insufficient permissions", role.name)


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRole(bot))
