# cogs/utility/serverinfo.py
import discord
from discord.ext import commands
from config import COLORS, EMOJIS
from utils.helpers import delete_command, send_and_delete
from utils.checks import check_permission

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="serverinfo", aliases=["si", "معلومات_السيرفر"])
    @check_permission("serverinfo")
    async def serverinfo(self, ctx):
        """عرض معلومات السيرفر"""
        
        await delete_command(ctx.message)
        
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"{EMOJIS['info']} {guild.name} - Server Info",
            color=COLORS["info"]
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="Boost Count", value=guild.premium_subscription_count or 0, inline=True)
        
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))