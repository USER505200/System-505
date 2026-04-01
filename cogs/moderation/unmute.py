import discord
from discord.ext import commands
import re
from config import COLORS, EMOJIS
from utils.helpers import send_and_delete
from utils.embeds import error_embed, success_embed
from utils.checks import check_permission

class Unmute(commands.Cog):
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
            clean_input = re.sub(r'[<@!>]', '', user_input.split()[0] if user_input.split() else user_input)
            try:
                if clean_input.isdigit():
                    return await ctx.guild.fetch_member(int(clean_input))
                return await commands.MemberConverter().convert(ctx, user_input)
            except:
                return None
        return None
    
    @commands.command(name="unmute", aliases=["um", "فك_كتم"])
    @commands.has_permissions(manage_roles=True)
    @check_permission("unmute")
    async def unmute(self, ctx, *, user_input=None):
        member = await self.get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role or muted_role not in member.roles:
            await send_and_delete(ctx, error_embed("Not Muted", f"{member.mention} is not muted."))
            return
        try:
            await member.remove_roles(muted_role, reason=f"Unmuted by {ctx.author}")
            embed = success_embed("User Unmuted", f"{member.mention} has been unmuted.")
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await send_and_delete(ctx, embed)
        except:
            await send_and_delete(ctx, error_embed("Permission Error", "I don't have permission to unmute that user."))

async def setup(bot):
    await bot.add_cog(Unmute(bot))