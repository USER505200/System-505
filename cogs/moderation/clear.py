# cogs/moderation/clear.py
import discord
from discord.ext import commands
from utils.helpers import delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="clear", aliases=["c", "مسح"])
    @commands.has_permissions(manage_messages=True)
    @check_permission("clear")
    async def clear(self, ctx, amount: int = 5):
        """مسح رسائل - !clear 10"""
        
        await delete_command(ctx.message)
        
        if amount < 1:
            await send_and_delete(ctx, error_embed("Invalid Amount", "Amount must be at least 1."))
            return
        
        if amount > 100:
            amount = 100
        
        try:
            deleted = await ctx.channel.purge(limit=amount)
            embed = success_embed(
                "Messages Deleted",
                f"Deleted {len(deleted)} messages.\n**Channel:** {ctx.channel.mention}\n**Moderator:** {ctx.author.mention}"
            )
            await send_and_delete(ctx, embed)
        except:
            await send_and_delete(ctx, error_embed("Permission Error", "I don't have permission to delete messages."))

async def setup(bot):
    await bot.add_cog(Clear(bot))