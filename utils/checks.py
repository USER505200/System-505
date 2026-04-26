# utils/checks.py
import discord
from discord.ext import commands
import database as db
import config

async def has_permission(ctx, command_name: str):
    """التحقق من صلاحية المستخدم لأمر معين"""
    
    # 1. التحقق من صلاحية Administrator
    if ctx.author.guild_permissions.administrator:
        return True
    
    # 2. جلب صلاحيات الأمر
    permissions = config.get_command_permission(command_name)
    
    # 3. لو مفيش صلاحيات
    if not permissions:
        return True
    
    # 4. التحقق من الرتب المحددة حتى لو الأمر يحتوي admin_only
    # admin_only تعني أن Administrator مسموح له، لكنها لا تمنع الرتب المحددة بجانبها.
    user_role_ids = [str(role.id) for role in ctx.author.roles]

    for allowed_role in permissions:
        if allowed_role == "admin_only":
            continue
        if allowed_role in user_role_ids:
            return True

    return False

def check_permission(command_name: str):
    async def predicate(ctx):
        return await has_permission(ctx, command_name)
    return commands.check(predicate)

async def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

def admin_only():
    async def predicate(ctx):
        return await is_admin(ctx)
    return commands.check(predicate)