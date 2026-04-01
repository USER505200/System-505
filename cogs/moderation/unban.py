# cogs/moderation/unban.py
import discord
from discord.ext import commands
import re
from config import EMOJIS, COLORS
from utils.helpers import send_and_delete
from utils.embeds import error_embed, success_embed
from utils.checks import check_permission

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="unban", aliases=["ub", "فك_حظر"])
    @commands.has_permissions(ban_members=True)
    @check_permission("unban")
    async def unban(self, ctx, *, user_input=None):
        """فك الحظر عن عضو - !unban user_id أو !unban @user"""
        
        user_id = None
        user_name = None
        
        # جلب المستخدم من الريبلاي
        if ctx.message.reference and not user_input:
            try:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                user_id = msg.author.id
                user_name = msg.author.name
            except:
                pass
        
        # جلب المستخدم من الإدخال
        if not user_id and user_input:
            # تنظيف المنشن
            clean_input = re.sub(r'[<@!>]', '', user_input.split()[0] if user_input.split() else user_input)
            if clean_input.isdigit():
                user_id = int(clean_input)
            else:
                # محاولة جلب المستخدم من الاسم
                banned_users = [entry async for entry in ctx.guild.bans()]
                for ban_entry in banned_users:
                    if user_input.lower() in ban_entry.user.name.lower():
                        user_id = ban_entry.user.id
                        user_name = ban_entry.user.name
                        break
        
        if not user_id:
            await send_and_delete(ctx, error_embed("Invalid User", "Please provide a user ID, mention a user, or reply to a banned user's message."))
            return
        
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}")
            
            embed = success_embed(
                "User Unbanned",
                f"{user.mention if user else f'User ID: {user_id}'} has been unbanned.\n**Moderator:** {ctx.author.mention}"
            )
            await send_and_delete(ctx, embed)
        except Exception as e:
            await send_and_delete(ctx, error_embed("Unban Failed", f"Could not unban user. Error: {str(e)}"))

async def setup(bot):
    await bot.add_cog(Unban(bot))