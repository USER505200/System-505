# main.py
import discord
from discord.ext import commands
import asyncio
import config
import database as db
import re
from utils.checks import has_permission

# ========== تعريف الـ Intents أولاً ==========
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

# ========== تعريف البوت ==========
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents, case_insensitive=True)

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
                if await has_permission(ctx, "nickname"):
                    cog = bot.get_cog("Nickname")
                    if cog:
                        new_name = content[1:].strip() if len(content) > 1 else None
                        await cog.nickname(ctx, user_input=new_name)
                else:
                    await message.reply("❌ You don't have permission to change nicknames!", delete_after=5)
            
            # ========== التحذير ==========
            elif content_lower in ["ت", "تحذير", "w"]:
                if await has_permission(ctx, "warn"):
                    cog = bot.get_cog("Warn")
                    if cog:
                        await cog.warn(ctx, user_input=None)
                else:
                    await message.reply("❌ You don't have permission to warn members!", delete_after=5)
            
            # ========== Timeout ==========
            elif content_lower in ["تايم", "to", "time"]:
                if await has_permission(ctx, "timeout"):
                    cog = bot.get_cog("Timeout")
                    if cog:
                        await cog.timeout(ctx, duration=None, user_input=None)
                else:
                    await message.reply("❌ You don't have permission to timeout members!", delete_after=5)
            
            elif content_lower.startswith("تايم "):
                if await has_permission(ctx, "timeout"):
                    cog = bot.get_cog("Timeout")
                    if cog:
                        duration = content[5:].strip()
                        await cog.timeout(ctx, duration=duration, user_input=None)
                else:
                    await message.reply("❌ You don't have permission to timeout members!", delete_after=5)
            
            # ========== الكتم ==========
            elif content_lower in ["م", "كتم", "m"]:
                if await has_permission(ctx, "mute"):
                    cog = bot.get_cog("Mute")
                    if cog:
                        await cog.mute(ctx, user_input=None)
                else:
                    await message.reply("❌ You don't have permission to mute members!", delete_after=5)
            
            # ========== فك الكتم ==========
            elif content_lower in ["فك", "فك_كتم", "um"]:
                if await has_permission(ctx, "unmute"):
                    cog = bot.get_cog("Unmute")
                    if cog:
                        await cog.unmute(ctx, user_input=None)
                else:
                    await message.reply("❌ You don't have permission to unmute members!", delete_after=5)
            
            # ========== الطرد ==========
            elif content_lower in ["ط", "طرد", "k"]:
                if await has_permission(ctx, "kick"):
                    cog = bot.get_cog("Kick")
                    if cog:
                        await cog.kick(ctx, user_input=None)
                else:
                    await message.reply("❌ You don't have permission to kick members!", delete_after=5)
            
            # ========== الحظر ==========
            elif content_lower in ["ب", "حظر", "b"]:
                if await has_permission(ctx, "ban"):
                    cog = bot.get_cog("Ban")
                    if cog:
                        await cog.ban(ctx, user_input=None)
                else:
                    await message.reply("❌ You don't have permission to ban members!", delete_after=5)
            
            # ========== السجن ==========
            elif content_lower in ["س", "سجن", "j"]:
                if await has_permission(ctx, "jail"):
                    cog = bot.get_cog("Jail")
                    if cog:
                        await cog.jail(ctx, duration=None, user_input=None)
                else:
                    await message.reply("❌ You don't have permission to jail members!", delete_after=5)
            
            elif content_lower.startswith("سجن "):
                if await has_permission(ctx, "jail"):
                    cog = bot.get_cog("Jail")
                    if cog:
                        parts = content[4:].strip().split(maxsplit=1)
                        duration = parts[0] if parts else None
                        user_input = parts[1] if len(parts) > 1 else None
                        await cog.jail(ctx, duration=duration, user_input=user_input)
                else:
                    await message.reply("❌ You don't have permission to jail members!", delete_after=5)
            
            # ========== فك السجن ==========
            elif content_lower in ["فك_سجن", "uj"]:
                if await has_permission(ctx, "unjail"):
                    cog = bot.get_cog("Unjail")
                    if cog:
                        await cog.unjail(ctx, user_input=None)
                else:
                    await message.reply("❌ You don't have permission to unjail members!", delete_after=5)
            
        except Exception as e:
            print(f"Reply error: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot is ready!")
    print(f"📡 Logged in as {bot.user.name}")
    print(f"🔗 Connected to {len(bot.guilds)} servers")
    
    await db.init_db()
    print("💾 Database initialized")
    
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
        "cogs.tickets.tickets",
        "cogs.moderation.come",
        "cogs.moderation.lines",
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

# ========== أمر اختبار الصلاحيات ==========
@bot.command(name="checkperm")
async def check_perm(ctx, command_name: str):
    """اختبار الصلاحيات - !checkperm nickname"""
    from utils.checks import has_permission
    has_perm = await has_permission(ctx, command_name)
    roles = [role.mention for role in ctx.author.roles]
    await ctx.send(f"Command: `{command_name}`\nHas permission: `{has_perm}`\nYour roles: {', '.join(roles)}")

# ========== أمر عرض الرتب ==========
@bot.command(name="myroles")
async def show_roles(ctx):
    """عرض الرتب الخاصة بك مع IDs"""
    roles = [f"{role.name} (`{role.id}`)" for role in ctx.author.roles if role.name != "@everyone"]
    await ctx.send(f"Your roles:\n" + "\n".join(roles))

if __name__ == "__main__":
    bot.run(config.TOKEN)