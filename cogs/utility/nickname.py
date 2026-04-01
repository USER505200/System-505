# cogs/utility/nickname.py
import discord
from discord.ext import commands
from config import EMOJIS, COLORS
from utils.helpers import send_and_delete
from utils.embeds import error_embed, success_embed
from utils.checks import check_permission
import re

class Nickname(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="nickname", aliases=["nick", "n", "اسم"])
    @commands.has_permissions(manage_nicknames=True)
    @check_permission("nickname")
    async def nickname(self, ctx, *, user_input=None):
        """تغيير النيك نيم - !nick @user [اسم] أو ريبلاي n اسم"""
        
        member = None
        new_nickname = None
        
        # ========== الحالة 1: ريبلاي ==========
        if ctx.message.reference:
            try:
                ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                member = ref_msg.author
                
                # استخراج الاسم الجديد
                if user_input and user_input.strip():
                    new_nickname = user_input.strip()
                else:
                    new_nickname = None
            except Exception as e:
                print(f"Reply error in nickname: {e}")
        
        # ========== الحالة 2: منشن أو ID ==========
        elif user_input:
            parts = user_input.split(maxsplit=1)
            if len(parts) >= 1:
                member = await self.get_member_from_input(ctx, parts[0])
                if member:
                    new_nickname = parts[1] if len(parts) > 1 else None
        
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        # منع تغيير نيك الأدمن
        if member.guild_permissions.administrator and not ctx.author.guild_permissions.administrator:
            await send_and_delete(ctx, error_embed("Cannot Change", "You cannot change an administrator's nickname!"))
            return
        
        # التحقق من صلاحيات البوت
        if not ctx.guild.me.guild_permissions.manage_nicknames:
            await send_and_delete(ctx, error_embed("Bot Permission", "I don't have permission to change nicknames!"))
            return
        
        try:
            old_nick = member.display_name
            
            if new_nickname is None or new_nickname.strip() == "":
                # حذف النيك نيم
                await member.edit(nick=None, reason=f"Nickname reset by {ctx.author}")
                embed = success_embed(
                    "Nickname Reset",
                    f"{member.mention}'s nickname has been reset to their original name.\n**Old:** {old_nick}"
                )
            else:
                # تغيير النيك نيم
                await member.edit(nick=new_nickname, reason=f"Nickname changed by {ctx.author}")
                embed = success_embed(
                    "Nickname Changed",
                    f"{member.mention}'s nickname has been changed.\n**Old:** {old_nick}\n**New:** {new_nickname}"
                )
            
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await send_and_delete(ctx, embed)
            
        except Exception as e:
            await send_and_delete(ctx, error_embed("Failed", f"Could not change nickname. Error: {str(e)}"))
    
    async def get_member_from_input(self, ctx, user_input):
        """جلب العضو من منشن أو ID"""
        try:
            if user_input.isdigit():
                return await ctx.guild.fetch_member(int(user_input))
            clean_input = re.sub(r'[<@!>]', '', user_input)
            if clean_input.isdigit():
                return await ctx.guild.fetch_member(int(clean_input))
            return await commands.MemberConverter().convert(ctx, user_input)
        except:
            return None

async def setup(bot):
    await bot.add_cog(Nickname(bot))