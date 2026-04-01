# cogs/utility/userinfo.py
import discord
from discord.ext import commands
from config import COLORS, EMOJIS
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import error_embed
from utils.checks import check_permission
import database as db

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="userinfo", aliases=["ui", "معلومات_عضو"])
    @check_permission("userinfo")
    async def userinfo(self, ctx, *, user_input=None):
        """عرض معلومات العضو - !userinfo @user أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            member = ctx.author
        
        # جلب التحذيرات
        warns_count = await db.get_warns_count(member.id, ctx.guild.id)
        
        # جلب الزواج
        married_to = await db.get_married(member.id, ctx.guild.id)
        married_text = f"<@{married_to}>" if married_to else "None"
        
        # اختيار الإيموجي للتحذيرات
        if warns_count >= 3:
            warn_emoji = EMOJIS["warn_3"]
        elif warns_count >= 2:
            warn_emoji = EMOJIS["warn_2"]
        elif warns_count >= 1:
            warn_emoji = EMOJIS["warn_1"]
        else:
            warn_emoji = "✅"
        
        embed = discord.Embed(
            title=f"{EMOJIS['info']} User Info - {member.display_name}",
            color=member.color if member.color != discord.Color.default() else COLORS["info"]
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M"), inline=True)
        embed.add_field(name="Joined Discord", value=member.created_at.strftime("%Y-%m-%d %H:%M"), inline=True)
        embed.add_field(name=f"{warn_emoji} Warnings", value=warns_count, inline=True)
        embed.add_field(name=f"{EMOJIS['marry']} Married To", value=married_text, inline=True)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        
        # عرض الرتب (أول 5 رتب)
        roles_list = [r.mention for r in member.roles[1:6]]
        if roles_list:
            embed.add_field(name="Roles", value=", ".join(roles_list) + ("..." if len(member.roles) > 6 else ""), inline=False)
        
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(UserInfo(bot))