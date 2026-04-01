# cogs/warns/resetwarn.py
import discord
from discord.ext import commands
from utils.helpers import get_member, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission
import database as db

class ResetWarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="resetwarn", aliases=["rw", "مسح_كل_التحذيرات"])
    @commands.has_permissions(administrator=True)
    @check_permission("resetwarn")
    async def resetwarn(self, ctx, *, user_input=None):
        """مسح كل التحذيرات - !resetwarn @user أو ريبلاي"""
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        warns_count = await db.get_warns_count(member.id, ctx.guild.id)
        
        if warns_count == 0:
            await send_and_delete(ctx, success_embed("No Warnings", f"{member.mention} has no warnings."))
            return
        
        await db.clear_warns(member.id, ctx.guild.id)
        
        await send_and_delete(ctx, success_embed(
            "All Warnings Cleared", 
            f"Cleared all {warns_count} warnings for {member.mention}."
        ))

async def setup(bot):
    await bot.add_cog(ResetWarn(bot))