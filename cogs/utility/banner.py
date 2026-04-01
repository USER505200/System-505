# cogs/utility/banner.py
import discord
from discord.ext import commands
from config import COLORS
from utils.helpers import get_member, send_permanent
from utils.embeds import error_embed

class Banner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="banner", aliases=["bu", "بنر"])
    async def banner(self, ctx, *, user_input=None):
        """عرض البانر - !banner @user أو ريبلاي"""
        
        # لا نمسح رسالة المستخدم
        # await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            member = ctx.author
        
        user = await self.bot.fetch_user(member.id)
        
        if user.banner:
            embed = discord.Embed(
                title=f" {member.display_name}'s Banner",
                color=COLORS["info"]
            )
            embed.set_image(url=user.banner.url)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            await send_permanent(ctx, embed)
        else:
            await send_permanent(ctx, error_embed("No Banner", f"{member.mention} doesn't have a banner."))

async def setup(bot):
    await bot.add_cog(Banner(bot))