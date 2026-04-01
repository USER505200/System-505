# cogs/warns/removewarn.py
import discord
from discord.ext import commands
from utils.helpers import get_member, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission
import database as db

class RemoveWarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="removewarn", aliases=["rw1", "مسح_تحذير_واحد"])
    @commands.has_permissions(kick_members=True)
    @check_permission("removewarn")
    async def removewarn(self, ctx, *, user_input=None):
        """حذف تحذير - !removewarn @user [warn_id] أو ريبلاي"""
        
        # استخراج المستخدم و ID التحذير
        parts = user_input.split() if user_input else []
        if not parts:
            await send_and_delete(ctx, error_embed("Missing Arguments", "Usage: `!removewarn @user [warn_id]`"))
            return
        
        member = await get_member(ctx, parts[0])
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        warns = await db.get_warns(member.id, ctx.guild.id)
        if not warns:
            await send_and_delete(ctx, success_embed("No Warnings", f"{member.mention} has no warnings."))
            return
        
        # تحديد ID التحذير
        warn_id = None
        if len(parts) > 1 and parts[1].isdigit():
            warn_id = int(parts[1])
        
        # إذا لم يحدد ID، نحذف آخر تحذير
        if warn_id is None:
            warn_id = warns[0][0]
        
        # التحقق من أن التحذير موجود لهذا المستخدم
        warn_exists = False
        for w in warns:
            if w[0] == warn_id:
                warn_exists = True
                break
        
        if not warn_exists:
            await send_and_delete(ctx, error_embed("Warning Not Found", f"Warning #{warn_id} not found for {member.mention}."))
            return
        
        await db.remove_warn(warn_id, ctx.guild.id)
        
        # جلب العدد الجديد
        new_count = await db.get_warns_count(member.id, ctx.guild.id)
        
        await send_and_delete(ctx, success_embed(
            "Warning Removed", 
            f"Removed warning #{warn_id} for {member.mention}.\nNow has {new_count} warnings."
        ))

async def setup(bot):
    await bot.add_cog(RemoveWarn(bot))