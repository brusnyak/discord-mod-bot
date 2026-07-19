from datetime import datetime, timezone

import discord


def moderation_embed(
    title: str,
    description: str,
    color: int = 0xFFA500,
    fields: list | None = None,
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    embed.set_footer(text="Moderation Bot")
    return embed
