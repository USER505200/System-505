# cogs/protection/addrole.py
import discord
from discord.ext import commands
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission

class AddRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="addrole", aliases=["ar", "رول"])
    @commands.has_permissions(manage_roles=True)
    @check_permission("addrole")
    async def addrole(self, ctx, role_input=None, *, user_input=None):
        """إضافة رتبة لعضو - !addrole @role @user أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        if not role_input:
            await send_and_delete(ctx, error_embed("Missing Role", "Please mention a role."))
            return
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        # جلب الرتبة
        try:
            if role_input.isdigit():
                role = ctx.guild.get_role(int(role_input))
            else:
                role = await commands.RoleConverter().convert(ctx, role_input)
        except:
            await send_and_delete(ctx, error_embed("Invalid Role", "Could not find that role."))
            return
        
        if role in member.roles:
            await send_and_delete(ctx, error_embed("Already Has Role", f"{member.mention} already has {role.mention}."))
            return
        
        try:
            await member.add_roles(role, reason=f"Added by {ctx.author}")
            embed = success_embed(
                "Role Added",
                f"Added {role.mention} to {member.mention}.\n**Moderator:** {ctx.author.mention}"
            )
            await send_and_delete(ctx, embed)
        except:
            await send_and_delete(ctx, error_embed("Permission Error", "I don't have permission to add that role."))

async def setup(bot):
    await bot.add_cog(AddRole(bot))