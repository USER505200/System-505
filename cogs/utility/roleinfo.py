# cogs/utility/roleinfo.py
import discord
from discord.ext import commands
from config import COLORS, EMOJIS
from utils.helpers import delete_command, send_and_delete
from utils.embeds import error_embed
from utils.checks import check_permission

class RoleInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="roleinfo", aliases=["ri", "معلومات_الرتبة"])
    @check_permission("roleinfo")
    async def roleinfo(self, ctx, *, role_input=None):
        """عرض معلومات الرتبة - !roleinfo @role"""
        
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
        
        embed = discord.Embed(
            title=f"{EMOJIS['info']} {role.name} - Role Info",
            color=role.color if role.color != discord.Color.default() else COLORS["info"]
        )
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Mentionable", value="✅ Yes" if role.mentionable else "❌ No", inline=True)
        embed.add_field(name="Hoist (Display Separate)", value="✅ Yes" if role.hoist else "❌ No", inline=True)
        embed.add_field(name="Created", value=role.created_at.strftime("%Y-%m-%d"), inline=True)
        
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(RoleInfo(bot))