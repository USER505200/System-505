# cogs/utility/botinfo.py
import discord
from discord.ext import commands
from config import COLORS, EMOJIS
from utils.helpers import delete_command, send_and_delete
from utils.checks import check_permission

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="botinfo", aliases=["bi", "معلومات_البوت"])
    @check_permission("botinfo")
    async def botinfo(self, ctx):
        """عرض معلومات البوت"""
        
        await delete_command(ctx.message)
        
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title=f"{EMOJIS['info']} Bot Information",
            color=COLORS["info"]
        )
        embed.add_field(name="Name", value=self.bot.user.name, inline=True)
        embed.add_field(name="ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Ping", value=f"{latency}ms", inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=sum(g.member_count for g in self.bot.guilds), inline=True)
        embed.add_field(name="Commands", value=len(self.bot.commands), inline=True)
        embed.set_footer(text=f"Prefix: {self.bot.command_prefix}")
        
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(BotInfo(bot))