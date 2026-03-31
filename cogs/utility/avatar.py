# cogs/utility/avatar.py
import discord
from discord.ext import commands
from config import COLORS
from utils.helpers import get_member, send_permanent
from utils.embeds import error_embed

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="avatar", aliases=["a", "صورتي"])
    async def avatar(self, ctx, *, user_input=None):
        """عرض الصورة الشخصية - !avatar @user أو ريبلاي"""
        
        # لا نمسح رسالة المستخدم
        # await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            member = ctx.author
        
        embed = discord.Embed(
            title=f" {member.display_name}'s Avatar",
            color=COLORS["info"]
        )
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        
        # إرسال رسالة دائمة (لا تمسح)
        await send_permanent(ctx, embed)

async def setup(bot):
    await bot.add_cog(Avatar(bot))