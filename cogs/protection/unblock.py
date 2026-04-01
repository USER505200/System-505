# cogs/protection/unblock.py
import discord
from discord.ext import commands
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission
import database as db

class Unblock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="unblock", aliases=["الغاء_حظر_بوت"])
    @commands.has_permissions(administrator=True)
    @check_permission("unblock")
    async def unblock(self, ctx, *, user_input=None):
        """إلغاء حظر مستخدم من البوت - !unblock @user أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if not await db.is_blocked(member.id, ctx.guild.id):
            await send_and_delete(ctx, error_embed("Not Blocked", f"{member.mention} is not blocked from using the bot."))
            return
        
        await db.unblock_user(member.id, ctx.guild.id)
        
        embed = success_embed(
            "User Unblocked",
            f"{member.mention} can now use the bot again.\n**Unblocked by:** {ctx.author.mention}"
        )
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(Unblock(bot))