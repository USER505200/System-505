# cogs/protection/lockdown.py
import discord
from discord.ext import commands
from utils.helpers import delete_command, send_and_delete
from utils.embeds import warning_embed, error_embed
from utils.checks import check_permission

class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lockdown_status = {}
    
    @commands.command(name="lockdown", aliases=["غلق"])
    @commands.has_permissions(administrator=True)
    @check_permission("lockdown")
    async def lockdown(self, ctx):
        """غلق السيرفر بالكامل - !lockdown"""
        
        await delete_command(ctx.message)
        
        if self.lockdown_status.get(ctx.guild.id, False):
            await send_and_delete(ctx, error_embed("Already Locked", "Server is already in lockdown mode."))
            return
        
        self.lockdown_status[ctx.guild.id] = True
        count = 0
        
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                try:
                    overwrite = channel.overwrites_for(ctx.guild.default_role)
                    overwrite.send_messages = False
                    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                    count += 1
                except:
                    pass
        
        embed = warning_embed(
            "🚨 SERVER LOCKDOWN 🚨",
            f"The server has been placed under lockdown.\n\n**Affected:** {count} channels\n**Initiated by:** {ctx.author.mention}\n\nOnly administrators can send messages."
        )
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(Lockdown(bot))