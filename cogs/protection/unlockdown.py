# cogs/protection/unlockdown.py
import discord
from discord.ext import commands
from utils.helpers import delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission

class Unlockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="unlockdown", aliases=["فتح_السيرفر"])
    @commands.has_permissions(administrator=True)
    @check_permission("unlockdown")
    async def unlockdown(self, ctx):
        """فتح السيرفر بعد القفل - !unlockdown"""
        
        await delete_command(ctx.message)
        
        lockdown_cog = self.bot.get_cog("Lockdown")
        if not lockdown_cog or not lockdown_cog.lockdown_status.get(ctx.guild.id, False):
            await send_and_delete(ctx, error_embed("Not Locked", "Server is not in lockdown mode."))
            return
        
        lockdown_cog.lockdown_status[ctx.guild.id] = False
        count = 0
        
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                try:
                    overwrite = channel.overwrites_for(ctx.guild.default_role)
                    overwrite.send_messages = None
                    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                    count += 1
                except:
                    pass
        
        embed = success_embed(
            "Server Unlocked",
            f"Server lockdown has been lifted.\n\n**Affected:** {count} channels\n**Initiated by:** {ctx.author.mention}"
        )
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(Unlockdown(bot))