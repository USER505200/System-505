import discord
from discord.ext import commands
import re
from config import COLORS, EMOJIS
from utils.helpers import send_and_delete
from utils.embeds import error_embed
from utils.checks import check_permission

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def get_member(self, ctx, user_input=None):
        if ctx.message.reference and not user_input:
            try:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                return msg.author
            except:
                return None
        if user_input:
            clean = re.sub(r'[<@!>]', '', user_input.split()[0] if user_input.split() else user_input)
            try:
                if clean.isdigit():
                    return await ctx.guild.fetch_member(int(clean))
                return await commands.MemberConverter().convert(ctx, user_input)
            except:
                return None
        return None
    
    @commands.command(name="ban", aliases=["b", "حظر"])
    @commands.has_permissions(ban_members=True)
    @check_permission("ban")
    async def ban(self, ctx, *, user_input=None):
        member = await self.get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply, or provide ID."))
            return
        if member == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot Ban", "You cannot ban yourself!"))
            return
        reason = "No reason provided"
        if user_input:
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                reason = parts[1]
        try:
            await member.ban(reason=f"{reason} - Banned by {ctx.author}")
            embed = discord.Embed(title=f"{EMOJIS['ban']} User Banned", description=f"{member.mention} banned.", color=COLORS["ban"])
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention)
            await send_and_delete(ctx, embed)
        except:
            await send_and_delete(ctx, error_embed("Permission Error", "Can't ban that user."))

async def setup(bot):
    await bot.add_cog(Ban(bot))