# cogs/warns/checkwarn.py
import discord
from discord.ext import commands
from config import EMOJIS, COLORS
from utils.helpers import get_member, send_and_delete
from utils.embeds import error_embed
from utils.checks import check_permission
import database as db

class CheckWarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="checkwarn", aliases=["cw", "تحذيرات"])
    @check_permission("checkwarn")
    async def checkwarn(self, ctx, *, user_input=None):
        """عرض تحذيرات العضو - !checkwarn @user أو ريبلاي"""
        
        member = await get_member(ctx, user_input)
        if not member:
            if user_input:
                await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
                return
            member = ctx.author
        
        # جلب تحذيرات هذا المستخدم فقط
        warns = await db.get_warns(member.id, ctx.guild.id)
        warns_count = len(warns)
        
        if warns_count == 0:
            embed = discord.Embed(
                title=f"{EMOJIS['success']} No Warnings",
                description=f"{member.mention} has no warnings.",
                color=COLORS["success"]
            )
            await send_and_delete(ctx, embed)
            return
        
        # اختيار الإيموجي حسب عدد التحذيرات
        if warns_count >= 3:
            warn_emoji = EMOJIS["warn_3"]
        elif warns_count >= 2:
            warn_emoji = EMOJIS["warn_2"]
        else:
            warn_emoji = EMOJIS["warn_1"]
        
        embed = discord.Embed(
            title=f"{warn_emoji} Warnings for {member.display_name}",
            description=f"Total: **{warns_count}** warnings",
            color=COLORS["warning"]
        )
        
        for i, warn in enumerate(warns[:10]):  # عرض آخر 10 تحذيرات
            warn_id, reason, warned_by, warned_at = warn
            warned_by_user = ctx.guild.get_member(int(warned_by))
            warned_by_name = warned_by_user.mention if warned_by_user else f"User {warned_by}"
            
            embed.add_field(
                name=f"Warning #{warn_id}",
                value=f"**Reason:** {reason}\n**By:** {warned_by_name}\n**Date:** {warned_at[:19]}",
                inline=False
            )
        
        if warns_count > 10:
            embed.set_footer(text=f"And {warns_count - 10} more warnings...")
        
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(CheckWarn(bot))