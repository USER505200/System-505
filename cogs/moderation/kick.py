# cogs/moderation/kick.py
import discord
from discord.ext import commands
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import kick_embed, error_embed

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="kick", aliases=["k", "طرد"])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, *, user_input=None):
        """طرد عضو - !kick @user [reason] أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if member == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot Kick", "You cannot kick yourself!"))
            return
        
        if member.guild_permissions.administrator:
            await send_and_delete(ctx, error_embed("Cannot Kick", "You cannot kick an administrator!"))
            return
        
        reason = "No reason provided"
        if user_input:
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                reason = parts[1]
        
        try:
            await member.kick(reason=f"{reason} - Kicked by {ctx.author}")
            embed = kick_embed(
                "User Kicked",
                f"{member.mention} has been kicked.\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}"
            )
            await send_and_delete(ctx, embed)
        except:
            await send_and_delete(ctx, error_embed("Permission Error", "I don't have permission to kick that user."))

async def setup(bot):
    await bot.add_cog(Kick(bot))