# cogs/warns/warn.py
import discord
from discord.ext import commands
import datetime
from config import EMOJIS, COLORS
from utils.helpers import get_member, send_and_delete
from utils.embeds import error_embed
from utils.checks import check_permission
import database as db

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="warn", aliases=["w", "تحذير", "ت"])
    @commands.has_permissions(kick_members=True)
    @check_permission("warn")
    async def warn(self, ctx, *, user_input=None):
        """إضافة تحذير - !warn @user [reason]"""
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if member == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot Warn", "You cannot warn yourself!"))
            return
        
        reason = "No reason provided"
        if user_input:
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                reason = parts[1]
        
        await db.add_warn(member.id, ctx.guild.id, reason, ctx.author.id)
        warns_count = await db.get_warns_count(member.id, ctx.guild.id)
        
        # اختيار الإيموجي
        if warns_count >= 3:
            warn_emoji = EMOJIS["warn_3"]
        elif warns_count >= 2:
            warn_emoji = EMOJIS["warn_2"]
        else:
            warn_emoji = EMOJIS["warn_1"]
        
        embed = discord.Embed(
            title=f"{warn_emoji} User Warned",
            description=f"{member.mention} has been warned.",
            color=COLORS["warning"]
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warnings", value=str(warns_count), inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        await send_and_delete(ctx, embed)
        
        # نظام العقوبات المتدرج - من التحذير الثالث
        timeout_seconds = None
        timeout_text = None
        
        if warns_count == 3:
            timeout_seconds = 10
            timeout_text = "10 seconds"
        elif warns_count == 4:
            timeout_seconds = 60
            timeout_text = "1 minute"
        elif warns_count == 5:
            timeout_seconds = 300
            timeout_text = "5 minutes"
        elif warns_count == 6:
            timeout_seconds = 600
            timeout_text = "10 minutes"
        elif warns_count == 7:
            timeout_seconds = 1800
            timeout_text = "30 minutes"
        elif warns_count == 8:
            timeout_seconds = 3600
            timeout_text = "1 hour"
        elif warns_count >= 9:
            timeout_seconds = 86400
            timeout_text = "24 hours"
        
        if timeout_seconds:
            try:
                timeout_until = discord.utils.utcnow() + datetime.timedelta(seconds=timeout_seconds)
                await member.timeout(timeout_until, reason=f"{warns_count} warnings - Auto timeout")
                
                timeout_embed = discord.Embed(
                    title=f"{EMOJIS['timeout']} Auto Timeout",
                    description=f"{member.mention} has been timed out for **{timeout_text}** due to reaching **{warns_count}** warnings.",
                    color=COLORS["warning"]
                )
                await send_and_delete(ctx, timeout_embed)
            except discord.Forbidden:
                error_msg = error_embed("Permission Error", "I don't have permission to timeout members. Please give me the 'Moderate Members' permission.")
                await send_and_delete(ctx, error_msg)
            except Exception as e:
                print(f"Timeout failed: {e}")

async def setup(bot):
    await bot.add_cog(Warn(bot))