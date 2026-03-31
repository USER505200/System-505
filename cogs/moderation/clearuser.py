# cogs/moderation/clearuser.py
import discord
from discord.ext import commands
import re
from utils.helpers import send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission

class ClearUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="clearuser", aliases=["cu", "مسح_شخص"])
    @commands.has_permissions(manage_messages=True)
    @check_permission("clearuser")
    async def clearuser(self, ctx, amount: int = 50, *, user_input=None):
        """مسح رسائل شخص - !clearuser 20 @user أو ريبلاي"""
        
        member = None
        
        # جلب المستخدم من الريبلاي
        if ctx.message.reference:
            try:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                member = msg.author
            except:
                pass
        
        # جلب المستخدم من الإدخال
        if not member and user_input:
            # تنظيف المنشن
            clean_input = re.sub(r'[<@!>]', '', user_input.split()[0] if user_input.split() else user_input)
            try:
                if clean_input.isdigit():
                    member = await ctx.guild.fetch_member(int(clean_input))
                else:
                    member = await commands.MemberConverter().convert(ctx, user_input)
            except:
                pass
        
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if amount < 1:
            await send_and_delete(ctx, error_embed("Invalid Amount", "Amount must be at least 1."))
            return
        
        if amount > 100:
            amount = 100
        
        def is_user(m):
            return m.author == member
        
        try:
            deleted = await ctx.channel.purge(limit=amount, check=is_user)
            embed = success_embed(
                "Messages Deleted",
                f"Deleted {len(deleted)} messages from {member.mention}.\n**Channel:** {ctx.channel.mention}\n**Moderator:** {ctx.author.mention}"
            )
            await send_and_delete(ctx, embed)
        except Exception as e:
            await send_and_delete(ctx, error_embed("Permission Error", f"I don't have permission to delete messages. Error: {str(e)}"))

async def setup(bot):
    await bot.add_cog(ClearUser(bot))