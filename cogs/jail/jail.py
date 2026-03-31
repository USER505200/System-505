# cogs/jail/jail.py
import discord
from discord.ext import commands
import asyncio
import re
from config import COLORS, EMOJIS
from utils.helpers import send_and_delete
from utils.embeds import error_embed, success_embed
from utils.checks import check_permission
import database as db

class Jail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jail_tasks = {}
    
    async def get_member(self, ctx, user_input=None):
        """جلب العضو من منشن أو ريبلاي أو ID"""
        if ctx.message.reference and not user_input:
            try:
                msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                return msg.author
            except:
                return None
        
        if user_input:
            try:
                if user_input.isdigit():
                    return await ctx.guild.fetch_member(int(user_input))
                return await commands.MemberConverter().convert(ctx, user_input)
            except:
                return None
        return None
    
    async def get_jail_role(self, guild):
        """جلب أو إنشاء رتبة السجن"""
        jail_role = discord.utils.get(guild.roles, name="Jailed")
        if not jail_role:
            jail_role = await guild.create_role(
                name="Jailed",
                color=discord.Color.dark_gray(),
                reason="Auto-created for jail system"
            )
            for channel in guild.channels:
                try:
                    await channel.set_permissions(jail_role, send_messages=False, add_reactions=False, speak=False)
                except:
                    pass
        return jail_role
    
    @commands.command(name="jail", aliases=["j", "سجن"])
    @commands.has_permissions(administrator=True)
    @check_permission("jail")
    async def jail(self, ctx, duration=None, *, user_input=None):
        """سجن عضو - !jail @user [duration] (30s, 10m, 1h, 1d)"""
        
        member = await self.get_member(ctx, user_input)
        if not member:
            await send_and_delete(ctx, error_embed("Invalid User", "Please mention a user, reply to their message, or provide an ID."))
            return
        
        if member == ctx.author:
            await send_and_delete(ctx, error_embed("Cannot Jail", "You cannot jail yourself!"))
            return
        
        # إزالة شرط الأدمن - يمكن سجن أي شخص
        # if member.guild_permissions.administrator:
        #     await send_and_delete(ctx, error_embed("Cannot Jail", "You cannot jail an administrator!"))
        #     return
        
        jail_role = await self.get_jail_role(ctx.guild)
        
        if jail_role in member.roles:
            await send_and_delete(ctx, error_embed("Already Jailed", f"{member.mention} is already jailed."))
            return
        
        # حفظ الرتب الحالية
        current_roles = [role.id for role in member.roles if role != ctx.guild.default_role]
        await db.save_roles(member.id, ctx.guild.id, current_roles)
        
        try:
            await member.remove_roles(*[r for r in member.roles if r != ctx.guild.default_role], reason=f"Jailed by {ctx.author}")
            await member.add_roles(jail_role, reason=f"Jailed by {ctx.author}")
            
            # تحليل المدة
            jail_duration = None
            duration_text = "permanent"
            if duration:
                match = re.match(r"(\d+)([smhd])", duration.lower())
                if match:
                    value = int(match.group(1))
                    unit = match.group(2)
                    if unit == "s":
                        jail_duration = value
                        duration_text = f"{value} second(s)"
                    elif unit == "m":
                        jail_duration = value * 60
                        duration_text = f"{value} minute(s)"
                    elif unit == "h":
                        jail_duration = value * 3600
                        duration_text = f"{value} hour(s)"
                    elif unit == "d":
                        jail_duration = value * 86400
                        duration_text = f"{value} day(s)"
            
            embed = discord.Embed(
                title=f"{EMOJIS['jail']} User Jailed",
                description=f"{member.mention} has been jailed.",
                color=COLORS["warning"]
            )
            embed.add_field(name="Duration", value=duration_text, inline=True)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            await send_and_delete(ctx, embed)
            
            if jail_duration:
                async def auto_unjail():
                    await asyncio.sleep(jail_duration)
                    await self.unjail_member(ctx.guild, member)
                
                task = asyncio.create_task(auto_unjail())
                self.jail_tasks[f"{ctx.guild.id}_{member.id}"] = task
                
        except Exception as e:
            await send_and_delete(ctx, error_embed("Jail Failed", f"Could not jail {member.mention}. Error: {str(e)}"))
    
    async def unjail_member(self, guild, member):
        """دالة فك السجن الداخلية"""
        jail_role = await self.get_jail_role(guild)
        
        if jail_role not in member.roles:
            return
        
        saved_roles = await db.get_saved_roles(member.id, guild.id)
        
        roles_to_add = []
        for role_id in saved_roles:
            role = guild.get_role(int(role_id))
            if role and role != guild.default_role:
                roles_to_add.append(role)
        
        try:
            await member.remove_roles(jail_role, reason="Auto unjail")
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Restoring roles after unjail")
            await db.delete_saved_roles(member.id, guild.id)
        except:
            pass

async def setup(bot):
    await bot.add_cog(Jail(bot))