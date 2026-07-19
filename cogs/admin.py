import logging

import discord
from discord import app_commands
from discord.ext import commands

from db.db import get_db
from utils.checks import is_admin
from utils.formatting import moderation_embed

logger = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="config", description="Configure server settings")
    @app_commands.describe(
        setting="Setting to change",
        value="New value (channel ID, role ID, or number)",
    )
    @app_commands.choices(setting=[
        app_commands.Choice(name="mod_log_channel", value="mod_log_channel_id"),
        app_commands.Choice(name="autorole", value="autorole_id"),
        app_commands.Choice(name="warn_kick_count", value="warn_kick_count"),
        app_commands.Choice(name="warn_ban_count", value="warn_ban_count"),
        app_commands.Choice(name="mute_role", value="mute_role_id"),
    ])
    @is_admin()
    async def config(
        self,
        interaction: discord.Interaction,
        setting: app_commands.Choice[str],
        value: str,
    ):
        async with get_db() as db:
            await db.execute(
                "INSERT INTO guilds (id) VALUES (?) ON CONFLICT(id) DO NOTHING",
                (interaction.guild_id,),
            )
            await db.execute(
                f"UPDATE guilds SET {setting.value} = ? WHERE id = ?",
                (int(value), interaction.guild_id),
            )
            await db.commit()

        embed = moderation_embed(
            title="✅ Configuration Updated",
            description=f"`{setting.name}` set to `{value}`",
            color=0x00FF00,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
