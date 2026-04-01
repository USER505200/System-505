# cogs/moderation/lines.py
import discord
from discord.ext import commands
import re
from config import COLORS, EMOJIS
from utils.helpers import send_and_delete
from utils.embeds import error_embed, success_embed
from utils.checks import check_permission
import database as db

class Lines(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.image_url = "https://cdn.discordapp.com/attachments/1444544689092038666/1485578853756829809/IMG_20260323_104525.png?ex=69c3b21f&is=69c2609f&hm=d599a4cde606a75739cb450d3fc17209430399cdbabada81fa062ff594b03472&"
    
    @commands.command(name="line", aliases=["خط"])
    @commands.has_permissions(administrator=True)
    @check_permission("line")
    async def line_add(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        
        channels = await db.get_line_channels(ctx.guild.id)
        if str(channel.id) in channels:
            await send_and_delete(ctx, error_embed("Already Added", f"{channel.mention} is already in the lines system!"))
            return
        
        await db.add_line_channel(ctx.guild.id, channel.id)
        
        embed = success_embed(
            "✅ Channel Added!",
            f"{channel.mention} has been added to the lines system."
        )
        await send_and_delete(ctx, embed)
    
    @commands.command(name="lines", aliases=["خطوط"])
    @commands.has_permissions(administrator=True)
    @check_permission("lines")
    async def lines_list(self, ctx):
        channels = await db.get_line_channels(ctx.guild.id)
        
        if not channels:
            embed = error_embed("No Channels", "No channels have been added to the lines system yet.\nUse `!line #channel` to add one.")
            await send_and_delete(ctx, embed)
            return
        
        channel_list = []
        for ch_id in channels:
            channel = ctx.guild.get_channel(int(ch_id))
            if channel:
                channel_list.append(f"• {channel.mention} (`{channel.id}`)")
            else:
                channel_list.append(f"• Deleted Channel (`{ch_id}`)")
        
        embed = discord.Embed(
            title=f"📡 Lines System - {ctx.guild.name}",
            description="\n".join(channel_list),
            color=COLORS["info"]
        )
        embed.set_footer(text=f"Total: {len(channel_list)} channels")
        await send_and_delete(ctx, embed)
    
    @commands.command(name="removeline", aliases=["حذف_خط", "rl"])
    @commands.has_permissions(administrator=True)
    @check_permission("removeline")
    async def line_remove(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        
        channels = await db.get_line_channels(ctx.guild.id)
        if str(channel.id) not in channels:
            await send_and_delete(ctx, error_embed("Not Found", f"{channel.mention} is not in the lines system!"))
            return
        
        await db.remove_line_channel(ctx.guild.id, channel.id)
        
        embed = success_embed(
            "✅ Channel Removed!",
            f"{channel.mention} has been removed from the lines system."
        )
        await send_and_delete(ctx, embed)
    
    @commands.command(name="clearlines", aliases=["مسح_الخطوط", "cl"])
    @commands.has_permissions(administrator=True)
    @check_permission("clearlines")
    async def lines_clear(self, ctx):
        channels = await db.get_line_channels(ctx.guild.id)
        if not channels:
            await send_and_delete(ctx, error_embed("No Channels", "No channels in the lines system."))
            return
        
        await db.clear_line_channels(ctx.guild.id)
        
        embed = success_embed(
            "✅ All Channels Cleared!",
            f"Removed {len(channels)} channels from the lines system."
        )
        await send_and_delete(ctx, embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # تجاهل رسائل البوت
        if message.author.bot:
            return
        
        # جلب القنوات من قاعدة البيانات
        channels = await db.get_line_channels(message.guild.id)
        
        # إذا القناة الحالية في القائمة
        if str(message.channel.id) in channels:
            # أرسل رابط الصورة في نفس القناة (للاختبار)
            await message.channel.send(self.image_url)
            print(f"✅ Sent image to {message.channel.name}")

async def setup(bot):
    bot.add_cog(Lines(bot))