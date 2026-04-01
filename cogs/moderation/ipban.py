# cogs/moderation/ipban.py
import discord
from discord.ext import commands
import re
from config import EMOJIS, COLORS
from utils.helpers import send_and_delete
from utils.embeds import error_embed
from utils.checks import check_permission
import database as db

class IPBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def get_member_from_input(self, ctx, user_input):
        """جلب العضو من منشن أو ID"""
        if not user_input:
            return None
        
        clean_input = re.sub(r'[<@!>]', '', user_input)
        
        try:
            if clean_input.isdigit():
                return await ctx.guild.fetch_member(int(clean_input))
            return await commands.MemberConverter().convert(ctx, user_input)
        except:
            return None
    
    async def get_member_from_reply(self, ctx):
        """جلب العضو من الريبلاي"""
        if ctx.message.reference:
            try:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                return msg.author
            except:
                return None
        return None
    
    @commands.command(name="ipban", aliases=["banip", "حظر_ايبي"])
    @commands.has_permissions(administrator=True)
    @check_permission("ipban")
    async def ipban(self, ctx, *, user_input=None):
        """حظر IP - !ipban @user [reason]"""
        
        member = None
        
        if ctx.message.reference and not user_input:
            member = await self.get_member_from_reply(ctx)
        elif user_input:
            parts = user_input.split(maxsplit=1)
            member = await self.get_member_from_input(ctx, parts[0])
        
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if member == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot Ban", "You cannot ban yourself!"))
            return
        
        reason = "No reason provided"
        if user_input:
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                reason = parts[1]
        
        # تسجيل في قاعدة البيانات
        await db.add_ip_ban(member.id, ctx.guild.id, reason, ctx.author.id)
        
        # حظر العضو عادياً
        try:
            await member.ban(reason=f"IP BAN: {reason} - Banned by {ctx.author}")
            
            embed = discord.Embed(
                title=f"{EMOJIS['ban']} IP Ban",
                description=f"{member.mention} has been IP banned.",
                color=COLORS["ban"]
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await send_and_delete(ctx, embed)
        except Exception as e:
            await send_and_delete(ctx, error_embed("Ban Failed", f"Could not ban user. Error: {str(e)}"))

async def setup(bot):
    await bot.add_cog(IPBan(bot))