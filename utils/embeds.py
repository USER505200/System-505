# utils/embeds.py
import discord
from config import EMOJIS, COLORS

def success_embed(title: str, description: str = None):
    """إيمبد للنجاح"""
    embed = discord.Embed(
        title=f"{EMOJIS['success']} {title}",
        description=description,
        color=COLORS["success"]
    )
    return embed

def error_embed(title: str, description: str = None):
    """إيمبد للخطأ"""
    embed = discord.Embed(
        title=f"{EMOJIS['error']} {title}",
        description=description,
        color=COLORS["error"]
    )
    return embed

def warning_embed(title: str, description: str = None):
    """إيمبد للتحذير"""
    embed = discord.Embed(
        title=f"{EMOJIS['warning']} {title}",
        description=description,
        color=COLORS["warning"]
    )
    return embed

def ban_embed(title: str, description: str = None):
    """إيمبد للحظر"""
    embed = discord.Embed(
        title=f"{EMOJIS['ban']} {title}",
        description=description,
        color=COLORS["ban"]
    )
    return embed

def kick_embed(title: str, description: str = None):
    """إيمبد للطرد"""
    embed = discord.Embed(
        title=f"{EMOJIS['kick']} {title}",
        description=description,
        color=COLORS["kick"]
    )
    return embed

def info_embed(title: str, description: str = None):
    """إيمبد للمعلومات"""
    embed = discord.Embed(
        title=f"{EMOJIS['info']} {title}",
        description=description,
        color=COLORS["info"]
    )
    return embed

def punishment_embed(action: str, member: discord.Member, moderator: discord.Member, reason: str):
    """إيمبد للعقوبات"""
    emojis = {
        "ban": EMOJIS["ban"],
        "kick": EMOJIS["kick"],
        "mute": EMOJIS["mute"],
        "jail": EMOJIS["jail"]
    }
    
    colors = {
        "ban": COLORS["ban"],
        "kick": COLORS["kick"],
        "mute": COLORS["warning"],
        "jail": COLORS["warning"]
    }
    
    embed = discord.Embed(
        title=f"{emojis.get(action, EMOJIS['warning'])} User {action.title()}ed",
        description=f"{member.mention} has been {action}ed.",
        color=colors.get(action, COLORS["warning"])
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Moderator", value=moderator.mention, inline=True)
    return embed