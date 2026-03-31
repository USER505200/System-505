# cogs/fun/goodnight.py
import discord
from discord.ext import commands
import random
from config import COLORS, EMOJIS
from utils.helpers import get_member, delete_command, send_and_delete
from utils.checks import check_permission

class Goodnight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gifs = {
            "goodnight": "https://media.tenor.com/0t-dKzVlKhwAAAAi/goodnight-gif.gif"
        }
    
    @commands.command(name="goodnight", aliases=["gn", "تصبح_على_خير"])
    @check_permission("goodnight")
    async def goodnight(self, ctx, *, user_input=None):
        """أتمنى تصبح على خير - !goodnight @user أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        target = await get_member(ctx, user_input)
        
        if not target:
            target = ctx.author
        
        messages = [
            "Good night! Sleep tight! 🌙",
            "Sweet dreams! 💫",
            "Sleep well and wake up refreshed! 😴",
            "May your dreams be beautiful! ✨",
            "Rest well, tomorrow is a new day! 🌅",
            "Stars are watching over you! ⭐",
            "Dream of wonderful things! 🌈"
        ]
        
        embed = discord.Embed(
            title=f"{EMOJIS['marry']} Goodnight! 🌙",
            description=f"{ctx.author.mention} wishes {target.mention} a good night!\n\n*{random.choice(messages)}*",
            color=COLORS["info"]
        )
        embed.set_image(url=self.gifs["goodnight"])
        
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(Goodnight(bot))