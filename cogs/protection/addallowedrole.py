# cogs/protection/addallowedrole.py
import discord
from discord.ext import commands
from utils.helpers import delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission
import database as db

class AddAllowedRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="addallowedrole", aliases=["add", "اضف_رتبة"])
    @commands.has_permissions(administrator=True)
    @check_permission("addallowedrole")
    async def addallowedrole(self, ctx, role_input=None):
        """إضافة رتبة مسموح لها باستخدام الأوامر - !add @role"""
        
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
        
        await db.add_allowed_role(ctx.guild.id, role.id)
        
        embed = success_embed(
            "Role Added",
            f"{role.mention} can now use bot commands."
        )
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(AddAllowedRole(bot))