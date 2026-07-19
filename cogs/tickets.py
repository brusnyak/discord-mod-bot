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

TICKET_CATEGORY_NAME = "Tickets"


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ticket", description="Open a support ticket")
    @app_commands.describe(reason="Brief description of your issue")
    async def ticket_open(self, interaction: discord.Interaction, reason: str = "Support request"):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name.lower()}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket for {interaction.user} ({interaction.user.id}): {reason}",
        )

        async with get_db() as db:
            await db.execute(
                "INSERT INTO tickets (guild_id, user_id, channel_id, status) VALUES (?, ?, ?, 'open')",
                (guild.id, interaction.user.id, channel.id),
            )
            await db.commit()

        embed = moderation_embed(
            title="🎫 Ticket Created",
            description=f"{interaction.user.mention}, your ticket is in {channel.mention}.",
            color=0x00AAFF,
            fields=[("Reason", reason, False)],
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        await channel.send(
            f"{interaction.user.mention} Ticket opened: **{reason}**\n"
            f"A moderator will be with you shortly. Use `/ticket_close` to close."
        )

    @app_commands.command(name="ticket_close", description="Close the current ticket channel")
    @is_moderator()
    async def ticket_close(self, interaction: discord.Interaction):
        async with get_db() as db:
            row = await db.execute_fetchall(
                "SELECT id FROM tickets WHERE channel_id = ? AND status = 'open'",
                (interaction.channel_id,),
            )
            if row:
                await db.execute(
                    "UPDATE tickets SET status = 'closed', closed_at = datetime('now') WHERE id = ?",
                    (row[0][0],),
                )
                await db.commit()

        embed = moderation_embed(
            title="🔒 Ticket Closed",
            description=f"This channel will be deleted shortly.",
            color=0x888888,
        )
        await interaction.response.send_message(embed=embed)

        # Delete after 30 seconds
        await discord.utils.get(interaction.guild.text_channels, id=interaction.channel_id).delete(
            delay=30
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
