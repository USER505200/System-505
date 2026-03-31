# cogs/jail/unjail.py
import discord
from discord.ext import commands
from config import COLORS, EMOJIS
from utils.helpers import get_member, delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission
import database as db

class Unjail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def get_jail_role(self, guild):
        """جلب رتبة السجن"""
        return discord.utils.get(guild.roles, name="Jailed")
    
    @commands.command(name="unjail", aliases=["uj", "فك_سجن"])
    @commands.has_permissions(administrator=True)
    @check_permission("unjail")
    async def unjail(self, ctx, *, user_input=None):
        """فك السجن عن عضو - !unjail @user أو ريبلاي"""
        
        await delete_command(ctx.message)
        
        member = await get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        jail_role = await self.get_jail_role(ctx.guild)
        
        if not jail_role or jail_role not in member.roles:
            await send_and_delete(ctx, error_embed("Not Jailed", f"{member.mention} is not jailed."))
            return
        
        # إلغاء أي مهمة جدولة
        task_key = f"{ctx.guild.id}_{member.id}"
        if hasattr(self.bot.get_cog("Jail"), "jail_tasks"):
            if task_key in self.bot.get_cog("Jail").jail_tasks:
                self.bot.get_cog("Jail").jail_tasks[task_key].cancel()
                del self.bot.get_cog("Jail").jail_tasks[task_key]
        
        # استرجاع الرتب المحفوظة
        saved_roles = await db.get_saved_roles(member.id, ctx.guild.id)
        
        roles_to_add = []
        for role_id in saved_roles:
            role = ctx.guild.get_role(int(role_id))
            if role and role != ctx.guild.default_role:
                roles_to_add.append(role)
        
        try:
            await member.remove_roles(jail_role, reason=f"Unjailed by {ctx.author}")
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason=f"Restored by {ctx.author}")
            
            await db.delete_saved_roles(member.id, ctx.guild.id)
            
            embed = success_embed(
                "User Unjailed",
                f"{member.mention} has been unjailed and their roles restored.\n**Moderator:** {ctx.author.mention}"
            )
            await send_and_delete(ctx, embed)
        except Exception as e:
            await send_and_delete(ctx, error_embed("Unjail Failed", f"Could not unjail {member.mention}. Error: {str(e)}"))

async def setup(bot):
    await bot.add_cog(Unjail(bot))