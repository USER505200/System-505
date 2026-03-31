# main.py
import discord
from discord.ext import commands
import asyncio
import config
import database as db
import re

# ========== تعريف الـ Intents أولاً ==========
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

# ========== تعريف البوت ==========
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

# ========== نظام الريبلاي بدون بريفكس ==========
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # معالجة الأوامر العادية أولاً
    await bot.process_commands(message)
    
    # ========== نظام الريبلاي ==========
    if message.reference:
        try:
            ref_msg = await message.channel.fetch_message(message.reference.message_id)
            target = ref_msg.author
            if target.bot:
                return
            
            content = message.content
            content_lower = content.lower()
            
            # إنشاء Context
            ctx = await bot.get_context(message)
            
            # ========== النيك نيم ==========
            if content_lower.startswith("n"):
                cog = bot.get_cog("Nickname")
                if cog:
                    if len(content) > 1:
                        new_name = content[1:].strip()
                        await cog.nickname.callback(cog, ctx, user_input=new_name if new_name else None)
                    else:
                        await cog.nickname.callback(cog, ctx, user_input=None)
            
            # ========== التحذير ==========
            elif content_lower in ["ت", "تحذير", "w"]:
                cog = bot.get_cog("Warn")
                if cog:
                    await cog.warn.callback(cog, ctx, user_input=None)
            
            # ========== Timeout ==========
            elif content_lower in ["تايم", "to", "time"]:
                cog = bot.get_cog("Timeout")
                if cog:
                    await cog.timeout.callback(cog, ctx, duration=None, user_input=None)
            
            elif content_lower.startswith("تايم "):
                cog = bot.get_cog("Timeout")
                if cog:
                    duration = content[5:].strip()
                    await cog.timeout.callback(cog, ctx, duration=duration, user_input=None)
            
            # ========== الكتم ==========
            elif content_lower in ["م", "كتم", "m"]:
                cog = bot.get_cog("Mute")
                if cog:
                    await cog.mute.callback(cog, ctx, user_input=None)
            
            # ========== فك الكتم ==========
            elif content_lower in ["فك", "فك_كتم", "um"]:
                cog = bot.get_cog("Unmute")
                if cog:
                    await cog.unmute.callback(cog, ctx, user_input=None)
            
            # ========== الطرد ==========
            elif content_lower in ["ط", "طرد", "k"]:
                cog = bot.get_cog("Kick")
                if cog:
                    await cog.kick.callback(cog, ctx, user_input=None)
            
            # ========== الحظر ==========
            elif content_lower in ["ب", "حظر", "b"]:
                cog = bot.get_cog("Ban")
                if cog:
                    await cog.ban.callback(cog, ctx, user_input=None)
            
            # ========== السجن ==========
            elif content_lower in ["س", "سجن", "j"]:
                cog = bot.get_cog("Jail")
                if cog:
                    await cog.jail.callback(cog, ctx, duration=None, user_input=None)
            
            elif content_lower.startswith("سجن "):
                cog = bot.get_cog("Jail")
                if cog:
                    parts = content[4:].strip().split(maxsplit=1)
                    duration = parts[0] if parts else None
                    user_input = parts[1] if len(parts) > 1 else None
                    await cog.jail.callback(cog, ctx, duration=duration, user_input=user_input)
            
            # ========== فك السجن ==========
            elif content_lower in ["فك_سجن", "uj"]:
                cog = bot.get_cog("Unjail")
                if cog:
                    await cog.unjail.callback(cog, ctx, user_input=None)
            
        except Exception as e:
            print(f"Reply error: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot is ready!")
    print(f"📡 Logged in as {bot.user.name}")
    print(f"🔗 Connected to {len(bot.guilds)} servers")
    
    await db.init_db()
    print("💾 Database initialized")
    
    # تحميل جميع الـ Cogs
    cogs_list = [
        "cogs.moderation.ban",
        "cogs.moderation.kick",
        "cogs.moderation.mute",
        "cogs.moderation.unmute",
        "cogs.moderation.clear",
        "cogs.moderation.clearuser",
        "cogs.moderation.timeout",
        "cogs.moderation.ipban",
        "cogs.moderation.hwidban",
        "cogs.moderation.unban",
        "cogs.warns.warn",
        "cogs.warns.checkwarn",
        "cogs.warns.removewarn",
        "cogs.warns.resetwarn",
        "cogs.jail.jail",
        "cogs.jail.unjail",
        "cogs.jail.saveroles",
        "cogs.jail.restoreroles",
        "cogs.protection.lock",
        "cogs.protection.unlock",
        "cogs.protection.lockdown",
        "cogs.protection.unlockdown",
        "cogs.protection.block",
        "cogs.protection.unblock",
        "cogs.protection.addrole",
        "cogs.protection.removerole",
        "cogs.fun.marry",
        "cogs.fun.divorce",
        "cogs.fun.goodnight",
        "cogs.fun.ez",
        "cogs.fun.setgif",
        "cogs.utility.avatar",
        "cogs.utility.banner",
        "cogs.utility.userinfo",
        "cogs.utility.serverinfo",
        "cogs.utility.roleinfo",
        "cogs.utility.botinfo",
        "cogs.utility.nickname",
        "cogs.utility.help",
        "cogs.tempvoice.tempvoice",
    ]
    
    for cog in cogs_list:
        try:
            await bot.load_extension(cog)
            print(f"📦 Loaded: {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")
    
    print("🎉 Bot is fully ready!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title=f"{config.EMOJIS['error']} Permission Error",
            description="You don't have permission to use this command!",
            color=config.COLORS["error"]
        )
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=f"{config.EMOJIS['error']} Missing Argument",
            description=f"Usage: `!help {ctx.command.name}`",
            color=config.COLORS["error"]
        )
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title=f"{config.EMOJIS['error']} Invalid Argument",
            description="Please provide valid arguments.",
            color=config.COLORS["error"]
        )
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"⚠️ Error: {error}")

if __name__ == "__main__":
    bot.run(config.TOKEN)