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
