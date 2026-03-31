# cogs/protection/block.py
import discord
from discord.ext import commands
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission
import database as db

class Block(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="block", aliases=["حظر_بوت"])
    @commands.has_permissions(administrator=True)
    @check_permission("block")
    async def block(self, ctx, *, user_input=None):
        """حظر مستخدم من استخدام البوت - !block @user أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if member == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot Block", "You cannot block yourself from the bot!"))
            return
        
        if await db.is_blocked(member.id, ctx.guild.id):
            await send_and_delete(ctx, error_embed("Already Blocked", f"{member.mention} is already blocked from using the bot."))
            return
        
        await db.block_user(member.id, ctx.guild.id, ctx.author.id)
        
        embed = success_embed(
            "User Blocked",
            f"{member.mention} has been blocked from using the bot.\n**Blocked by:** {ctx.author.mention}"
        )
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(Block(bot))