# cogs/fun/ez.py
import discord
from discord.ext import commands
import asyncio
from config import COLORS, EMOJIS
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import error_embed, warning_embed
from utils.checks import check_permission

class EZ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gifs = {
            "ez": "https://media.tenor.com/xT5I5m5l2GgAAAAi/ez.gif"
        }
    
    @commands.command(name="ez", aliases=["ارزع"])
    @commands.has_permissions(administrator=True)
    @check_permission("ez")
    async def ez(self, ctx, *, user_input=None):
        """أمر ترول - !ez @user (يحتاج تأكيد) أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        target = await get_member(ctx, user_input)
        
        if not target:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention someone to use this on, reply to their message, or provide an ID."))
            return
        
        if target == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot EZ", "You cannot use this on yourself!"))
            return
        
        # نظام التأكيد
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "!ez"
        
        confirm_embed = warning_embed(
            "Confirmation Required",
            f"Are you sure you want to use `!ez` on {target.mention}?\nType `!ez` again within 10 seconds to confirm."
        )
        await send_and_delete(ctx, confirm_embed, delete_after=10)
        
        try:
            await self.bot.wait_for("message", timeout=10.0, check=check)
            
            messages = [
                "just demolished",
                "absolutely destroyed",
                "rekt",
                "got owned",
                "sent to the shadow realm",
                "got absolutely clapped"
            ]
            import random
            action = random.choice(messages)
            
            embed = discord.Embed(
                title=f"{EMOJIS['warning']} EZ! 🎯",
                description=f"{ctx.author.mention} {action} {target.mention}! Get rekt!",
                color=COLORS["error"]
            )
            embed.set_image(url=self.gifs.get("ez", "https://media.tenor.com/xT5I5m5l2GgAAAAi/ez.gif"))
            
            await send_and_delete(ctx, embed)
            
        except asyncio.TimeoutError:
            await send_and_delete(ctx, error_embed("Cancelled", "Command cancelled. No confirmation received."))

async def setup(bot):
    await bot.add_cog(EZ(bot))