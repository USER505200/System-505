# cogs/jail/restoreroles.py
import discord
from discord.ext import commands
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission
import database as db

class RestoreRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="restoreroles", aliases=["restore", "استرجاع"])
    @commands.has_permissions(administrator=True)
    @check_permission("restoreroles")
    async def restoreroles(self, ctx, *, user_input=None):
        """استرجاع رتب محفوظة لعضو - !restore @user أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        saved_roles = await db.get_saved_roles(member.id, ctx.guild.id)
        
        if not saved_roles:
            await send_and_delete(ctx, error_embed("No Saved Roles", f"No saved roles found for {member.mention}."))
            return
        
        roles_to_add = []
        for role_id in saved_roles:
            role = ctx.guild.get_role(int(role_id))
            if role and role != ctx.guild.default_role:
                roles_to_add.append(role)
        
        try:
            await member.add_roles(*roles_to_add, reason=f"Restored by {ctx.author}")
            embed = success_embed(
                "Roles Restored",
                f"Restored {len(roles_to_add)} roles for {member.mention}.\n**Moderator:** {ctx.author.mention}"
            )
            await send_and_delete(ctx, embed)
        except Exception as e:
            await send_and_delete(ctx, error_embed("Restore Failed", f"Could not restore roles. Error: {str(e)}"))

async def setup(bot):
    await bot.add_cog(RestoreRoles(bot))