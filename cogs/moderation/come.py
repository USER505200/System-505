# cogs/moderation/come.py
import discord
from discord.ext import commands
import re
from config import COLORS, EMOJIS
from utils.helpers import get_member, send_and_delete
from utils.embeds import error_embed, success_embed
from utils.checks import check_permission

class Come(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="come", aliases=["تعال", "جيب"])
    @check_permission("come")
    async def come(self, ctx, *, user_input=None):
        """
        إرسال دعوة للمستخدم مع رسالة مخصصة
        !come @user تعال الى الروم الفلاني
        أو بالريبلاي
        """
        
        member = None
        message_content = None
        
        # ========== الحالة 1: ريبلاي ==========
        if ctx.message.reference:
            try:
                ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                member = ref_msg.author
                
                if user_input:
                    message_content = user_input.strip()
                else:
                    message_content = "I need you here!"
            except:
                pass
        
        # ========== الحالة 2: منشن أو ID ==========
        elif user_input:
            parts = user_input.split(maxsplit=1)
            if len(parts) >= 1:
                member = await self.get_member_from_input(ctx, parts[0])
                if member:
                    message_content = parts[1] if len(parts) > 1 else "I need you here!"
        
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if member == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot Come", "You cannot send a come request to yourself!"))
            return
        
        if member.bot:
            await send_and_delete(ctx, error_embed("Cannot Come", "You cannot send a come request to a bot!"))
            return
        
        # إرسال الطلب في الخاص (بدون أزرار)
        await self.send_come_notification(member, ctx.author, ctx.channel, message_content)
        
        # تأكيد للمستخدم المرسل
        embed = success_embed(
            "✅ Request Sent!",
            f"Come request sent to {member.mention}!\n**Message:** {message_content}"
        )
        await send_and_delete(ctx, embed)
    
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
    
    async def send_come_notification(self, target, requester, channel, message):
        """إرسال إشعار في الخاص للمستخدم (بدون أزرار)"""
        
        embed = discord.Embed(
            title=f"🔔 {requester.display_name} is calling you!",
            description=f"**Message from {requester.mention}:**\n\n> {message}\n\n**Channel:** {channel.mention}\n**Server:** {channel.guild.name}\n\nPlease join {channel.mention} to respond.",
            color=COLORS["info"]
        )
        embed.set_footer(text=f"Sent by {requester.display_name}")
        
        try:
            await target.send(embed=embed)
        except discord.Forbidden:
            embed = error_embed(
                "Cannot Send DM",
                f"{target.mention} has DMs disabled. Cannot send come request."
            )
            await requester.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Come(bot))