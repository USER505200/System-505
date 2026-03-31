# utils/checks.py
import discord
from discord.ext import commands
import database as db
import config

async def has_permission(ctx, command_name: str):
    """التحقق من صلاحية المستخدم لأمر معين"""
    
    # التحقق من صلاحية Administrator في Discord
    if ctx.author.guild_permissions.administrator:
        return True
    
    # جلب صلاحيات الأمر من config
    permission_result = config.is_command_allowed(command_name, ctx.author.roles)
    
    if permission_result == "admin_only":
        return False
    
    if permission_result is True:
        return True
    
    return False

def check_permission(command_name: str):
    """Decorator للتحقق من صلاحية أمر"""
    async def predicate(ctx):
        return await has_permission(ctx, command_name)
    return commands.check(predicate)

async def is_admin(ctx):
    """التحقق من صلاحية Administrator"""
    return ctx.author.guild_permissions.administrator

async def is_allowed(ctx):
    """التحقق من الرتب المصرح بها في قاعدة البيانات"""
    if ctx.author.guild_permissions.administrator:
        return True
    
    allowed_roles = await db.get_allowed_roles(ctx.guild.id)
    for role in ctx.author.roles:
        if str(role.id) in allowed_roles:
            return True
    return False

async def is_not_blocked(ctx):
    """التحقق من أن المستخدم غير محظور من البوت"""
    return not await db.is_blocked(ctx.author.id, ctx.guild.id)

def admin_only():
    """Decorator للأوامر التي تحتاج أدمن"""
    async def predicate(ctx):
        return await is_admin(ctx)
    return commands.check(predicate)

def allowed_only():
    """Decorator للأوامر التي تحتاج رتبة مصرح بها"""
    async def predicate(ctx):
        return await is_allowed(ctx)
    return commands.check(predicate)