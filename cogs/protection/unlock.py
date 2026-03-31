# cogs/protection/unlock.py
import discord
from discord.ext import commands
from utils.helpers import delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission

class Unlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="unlock", aliases=["فتح"])
    @commands.has_permissions(administrator=True)
    @check_permission("unlock")
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """فتح روم معين - !unlock #channel"""
        
        await delete_command(ctx.message)
        
        channel = channel or ctx.channel
        
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = success_embed(
            "Channel Unlocked",
            f"{channel.mention} has been unlocked.\n**Moderator:** {ctx.author.mention}"
        )
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(Unlock(bot))