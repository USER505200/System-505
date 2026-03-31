# cogs/moderation/timeout.py
import discord
from discord.ext import commands
import re
import datetime
from config import EMOJIS, COLORS
from utils.helpers import send_and_delete
from utils.embeds import error_embed
from utils.checks import check_permission

class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="timeout", aliases=["to", "time", "x", "تايم"])
    @commands.has_permissions(moderate_members=True)
    @check_permission("timeout")
    async def timeout(self, ctx, duration=None, *, user_input=None):
        """تقييد عضو - !timeout @user [duration] (30s, 10m, 1h, 1d)"""
        
        member = None
        
        # طريقة 1: من الريبلاي
        if ctx.message.reference:
            try:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                member = msg.author
            except:
                pass
        
        # طريقة 2: من الإدخال
        if not member and user_input:
            # تنظيف المنشن
            clean_input = re.sub(r'[<@!>]', '', user_input.split()[0] if user_input.split() else user_input)
            try:
                if clean_input.isdigit():
                    member = await ctx.guild.fetch_member(int(clean_input))
                else:
                    member = await commands.MemberConverter().convert(ctx, user_input.split()[0])
            except:
                pass
        
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if member == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot Timeout", "You cannot timeout yourself!"))
            return
        
        # تحليل المدة
        timeout_seconds = 60  # افتراضي 1 دقيقة
        duration_text = "1 minute"
        
        if duration:
            match = re.match(r"(\d+)([smhd])", duration.lower())
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                if unit == "s":
                    timeout_seconds = value
                    duration_text = f"{value} second(s)"
                elif unit == "m":
                    timeout_seconds = value * 60
                    duration_text = f"{value} minute(s)"
                elif unit == "h":
                    timeout_seconds = value * 3600
                    duration_text = f"{value} hour(s)"
                elif unit == "d":
                    timeout_seconds = value * 86400
                    duration_text = f"{value} day(s)"
        
        # استخراج السبب
        reason = "No reason provided"
        if user_input:
            # إزالة المنشن من النص للحصول على السبب
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                # إذا كان هناك مدة، السبب بعد المدة
                if duration and len(parts) > 1:
                    reason = parts[1]
                elif not duration and len(parts) > 1:
                    reason = parts[1]
        
        try:
            timeout_until = discord.utils.utcnow() + datetime.timedelta(seconds=timeout_seconds)
            await member.timeout(timeout_until, reason=f"{reason} - Timed out by {ctx.author}")
            
            embed = discord.Embed(
                title=f"{EMOJIS['timeout']} User Timed Out",
                description=f"{member.mention} has been timed out.",
                color=COLORS["warning"]
            )
            embed.add_field(name="Duration", value=duration_text, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await send_and_delete(ctx, embed)
        except discord.Forbidden:
            await send_and_delete(ctx, error_embed("Permission Error", "I don't have permission to timeout members. Please give me the 'Moderate Members' permission."))
        except Exception as e:
            await send_and_delete(ctx, error_embed("Error", f"Could not timeout user. Error: {str(e)}"))

async def setup(bot):
    await bot.add_cog(Timeout(bot))