import discord


def get_embed_for_userinfo(user_data: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"osu! Profile: {user_data['username']}",
        color=discord.Color.blue(),
        url=f"https://osu.ppy.sh/users/{user_data['osu_id']}"
    )
    embed.set_thumbnail(url=f"https://a.ppy.sh/{user_data['osu_id']}")
    embed.add_field(name="Osu! ID", value=user_data['osu_id'], inline=False)
    embed.add_field(name="PP", value=f"{user_data['pp']:.2f}", inline=False)
    embed.add_field(
        name="Elo Rating",
        value=f"{user_data['elo_rating']:.2f}",
        inline=False)
    embed.add_field(
        name="Matches Played",
        value=len(
            user_data['matches']),
        inline=False)
    active_value = ":red_circle: The player is inactive in scrims"
    if user_data['active']:
        active_value = ":green_circle: The player is active in scrims"
    embed.add_field(name="Activity:", value=active_value, inline=False)
    embed.set_footer(text="4unc Ky")
    return embed


def get_embed_for_roulette_stats(stats: dict, user: discord.User) -> discord.Embed:
    embed = discord.Embed(
        title=f"Рулетка-статистика: {user.display_name}",
        color=discord.Color.green()
    )
    embed.add_field(name="Круток", value=stats['rolls'], inline=True)
    embed.add_field(name="Выигрышей", value=stats['wins'], inline=True)
    embed.add_field(name="Winrate", value=f"{stats['winrate']:.2f}%", inline=True)
    embed.add_field(name="Текущий streak", value=stats['streak_current'], inline=True)
    embed.add_field(name="Достижения", value="\n".join(stats['achievements']) or "Нет достижений", inline=False)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    embed.set_footer(text="4unc Ky")
    return embed
