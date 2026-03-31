# cogs/fun/divorce.py
import discord
from discord.ext import commands
from config import COLORS, EMOJIS
from utils.helpers import send_permanent
from utils.embeds import error_embed, warning_embed
from utils.checks import check_permission
import database as db

class Divorce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="divorce", aliases=["طلاق"])
    @check_permission("divorce")
    async def divorce(self, ctx):
        """الطلاق - !divorce"""
        
        partner_id = await db.get_married(ctx.author.id, ctx.guild.id)
        
        if not partner_id:
            await send_permanent(ctx, error_embed("Not Married", "You are not married to anyone."))
            return
        
        partner = ctx.guild.get_member(int(partner_id))
        partner_name = partner.mention if partner else f"<@{partner_id}>"
        
        await db.divorce(ctx.author.id, ctx.guild.id)
        
        embed = warning_embed(
            "Divorced 💔",
            f"{ctx.author.mention} and {partner_name} are now divorced.\n\n*Better luck next time!*"
        )
        await send_permanent(ctx, embed)

async def setup(bot):
    await bot.add_cog(Divorce(bot))