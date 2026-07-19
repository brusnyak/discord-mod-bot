from discord import app_commands
from discord.ext import commands


def is_moderator():
    """Check if user has moderate_members or administrator permission."""
    async def predicate(interaction):
        return (
            interaction.user.guild_permissions.moderate_members
            or interaction.user.guild_permissions.administrator
        )
    return app_commands.check(predicate)


def is_admin():
    """Check if user has administrator permission."""
    async def predicate(interaction):
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)
