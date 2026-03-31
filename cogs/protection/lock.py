# cogs/protection/lock.py
import discord
from discord.ext import commands
from utils.helpers import delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission

class Lock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="lock", aliases=["قفل"])
    @commands.has_permissions(administrator=True)
    @check_permission("lock")
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """قفل روم معين - !lock #channel"""
        
        await delete_command(ctx.message)
        
        channel = channel or ctx.channel
        
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = success_embed(
            "Channel Locked",
            f"{channel.mention} has been locked. Only staff can send messages.\n**Moderator:** {ctx.author.mention}"
        )
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(Lock(bot))