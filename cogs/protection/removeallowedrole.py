# cogs/protection/removeallowedrole.py
import discord
from discord.ext import commands
from utils.helpers import delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission
import database as db

class RemoveAllowedRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="removeallowedrole", aliases=["remove", "شيل_رتبة"])
    @commands.has_permissions(administrator=True)
    @check_permission("removeallowedrole")
    async def removeallowedrole(self, ctx, role_input=None):
        """إزالة رتبة من الصلاحيات - !remove @role"""
        
        await delete_command(ctx.message)
        
        if not role_input:
            await send_and_delete(ctx, error_embed("Missing Role", "Please mention a role or provide a role ID."))
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
        
        await db.remove_allowed_role(ctx.guild.id, role.id)
        
        embed = success_embed(
            "Role Removed",
            f"{role.mention} can no longer use bot commands."
        )
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(RemoveAllowedRole(bot))