import datetime
import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import load_config
from db.db import get_db
from ops_webhook import send_to_ops_lab
from utils.checks import is_moderator
from utils.formatting import moderation_embed

logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="warn", description="Warn a user (adds to warning ladder)")
    @app_commands.describe(user="User to warn", reason="Reason for the warning")
    @is_moderator()
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        async with get_db() as db:
            await db.execute(
                "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
                (interaction.guild_id, user.id, interaction.user.id, reason),
            )
            await db.commit()

            # Count active warnings
            row = await db.execute_fetchall(
                "SELECT COUNT(*) as c FROM warnings WHERE guild_id = ? AND user_id = ? AND active = 1",
                (interaction.guild_id, user.id),
            )
            warn_count = row[0][0]

            # Check threshold
            config = await db.execute_fetchall(
                "SELECT warn_kick_count, warn_ban_count FROM guilds WHERE id = ?",
                (interaction.guild_id,),
            )
            kick_at = config[0][0] if config else 5
            ban_at = config[0][1] if config else 6

        action_taken = ""
        if warn_count >= ban_at:
            await user.ban(reason=f"Auto-ban: {warn_count} warnings")
            action_taken = f"\n⚠️ User banned ({warn_count}/{ban_at} warnings)"
        elif warn_count >= kick_at:
            await user.kick(reason=f"Auto-kick: {warn_count} warnings")
            action_taken = f"\n⚠️ User kicked ({warn_count}/{kick_at} warnings)"
        elif warn_count >= 4:
            await user.timeout(duration=datetime.timedelta(days=7), reason=f"Warning {warn_count}")
            action_taken = f"\n⚠️ 7-day timeout applied ({warn_count} warnings)"
        elif warn_count >= 3:
            await user.timeout(duration=datetime.timedelta(hours=24), reason=f"Warning {warn_count}")
            action_taken = f"\n⚠️ 24h timeout applied ({warn_count} warnings)"
        elif warn_count >= 2:
            await user.timeout(duration=datetime.timedelta(hours=1), reason=f"Warning {warn_count}")
            action_taken = f"\n⚠️ 1h timeout applied ({warn_count} warnings)"
        else:
            try:
                await user.send(f"⚠️ Warning: {reason}")
            except discord.Forbidden:
                pass

        embed = moderation_embed(
            title=f"⚠️ Warning | {user}",
            description=f"**Reason:** {reason}\n**Warnings:** {warn_count}{action_taken}",
            color=0xFFA500,
        )
        await interaction.response.send_message(embed=embed)

        # Push to ops-lab dashboard
        cfg = load_config()
        if cfg.bot_ops_webhook:
            send_to_ops_lab(
                webhook_url=cfg.bot_ops_webhook,
                event_id=f"warn_{interaction.id}",
                author_name=user.display_name,
                author_username=user.name,
                content=f"[Moderation] Warning #{warn_count}: {reason}",
            )

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(user="User to kick", reason="Reason for the kick")
    @is_moderator()
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        await user.kick(reason=reason)
        embed = moderation_embed(
            title=f"👢 Kick | {user}",
            description=f"**Reason:** {reason}",
            color=0xFF6600,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(user="User to ban", reason="Reason for the ban")
    @is_moderator()
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        await user.ban(reason=reason)
        embed = moderation_embed(
            title=f"🔨 Ban | {user}",
            description=f"**Reason:** {reason}",
            color=0xFF0000,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pardon", description="Remove the latest active warning for a user")
    @app_commands.describe(user="User to pardon")
    @is_moderator()
    async def pardon(self, interaction: discord.Interaction, user: discord.Member):
        async with get_db() as db:
            row = await db.execute_fetchall(
                "SELECT id FROM warnings WHERE guild_id = ? AND user_id = ? AND active = 1 ORDER BY created_at DESC LIMIT 1",
                (interaction.guild_id, user.id),
            )
            if not row:
                await interaction.response.send_message("No active warnings for this user.", ephemeral=True)
                return
            await db.execute("UPDATE warnings SET active = 0 WHERE id = ?", (row[0][0],))
            await db.commit()

        embed = moderation_embed(
            title=f"✅ Pardoned | {user}",
            description="Latest warning deactivated.",
            color=0x00FF00,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
