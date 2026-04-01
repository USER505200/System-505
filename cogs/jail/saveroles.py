# cogs/jail/saveroles.py
import discord
from discord.ext import commands
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission
import database as db

class SaveRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="saveroles", aliases=["save", "حفظ"])
    @commands.has_permissions(administrator=True)
    @check_permission("saveroles")
    async def saveroles(self, ctx, *, user_input=None):
        """حفظ رتب عضو يدوياً - !save @user أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        current_roles = [role.id for role in member.roles if role != ctx.guild.default_role]
        await db.save_roles(member.id, ctx.guild.id, current_roles)
        
        embed = success_embed(
            "Roles Saved",
            f"Saved {len(current_roles)} roles for {member.mention}.\n**Moderator:** {ctx.author.mention}"
        )
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(SaveRoles(bot))