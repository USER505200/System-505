# cogs/moderation/mute.py
import discord
from discord.ext import commands
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import punishment_embed, error_embed

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="mute", aliases=["m", "كتم"])
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, *, user_input=None):
        """كتم عضو - !mute @user [reason] أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if member == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot Mute", "You cannot mute yourself!"))
            return
        
        # جلب أو إنشاء رتبة Muted
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                try:
                    await channel.set_permissions(muted_role, send_messages=False, add_reactions=False, speak=False)
                except:
                    pass
        
        if muted_role in member.roles:
            await send_and_delete(ctx, error_embed("Already Muted", f"{member.mention} is already muted."))
            return
        
        reason = "No reason provided"
        if user_input:
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                reason = parts[1]
        
        try:
            await member.add_roles(muted_role, reason=f"{reason} - Muted by {ctx.author}")
            embed = punishment_embed("mute", member, ctx.author, reason)
            await send_and_delete(ctx, embed)
        except:
            await send_and_delete(ctx, error_embed("Permission Error", "I don't have permission to mute that user."))

async def setup(bot):
    await bot.add_cog(Mute(bot))