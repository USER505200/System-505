# cogs/utility/help.py
import discord
from discord.ext import commands
from config import COLORS, EMOJIS, COMMAND_PERMISSIONS
from utils.helpers import send_permanent
from utils.checks import has_permission

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if bot.get_command("help"):
            bot.remove_command("help")
    
    @commands.command(name="help", aliases=["مساعدة", "h", "helps"])
    async def help_cmd(self, ctx, command_name=None):
        """عرض قائمة المساعدة - !help أو !help [command]"""
        
        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                embed = discord.Embed(
                    title=f"{EMOJIS['error']} Command Not Found",
                    description=f"`{command_name}` is not a valid command.",
                    color=COLORS["error"]
                )
                await send_permanent(ctx, embed)
                return
            
            perms = COMMAND_PERMISSIONS.get(cmd.name, {}).get("allowed_roles", [])
            if not perms:
                perm_text = "✅ Everyone"
            elif "admin_only" in perms:
                perm_text = "🔒 Administrators Only"
            else:
                perm_text = f"👑 Roles: {', '.join(perms)}"
            
            embed = discord.Embed(
                title=f"{EMOJIS['info']} Help: {cmd.name}",
                description=cmd.help or "No description provided.",
                color=COLORS["info"]
            )
            
            aliases = []
            for alias in cmd.aliases:
                aliases.append(f"`!{alias}`")
            if aliases:
                embed.add_field(name="Aliases (اختصارات)", value=", ".join(aliases), inline=False)
            
            embed.add_field(name="Usage (طريقة الاستخدام)", value=f"`!{cmd.name} <@user> [reason]`", inline=True)
            embed.add_field(name="Permissions (الصلاحيات)", value=perm_text, inline=True)
            await send_permanent(ctx, embed)
            return
        
        # القائمة الرئيسية
        embed = discord.Embed(
            title=f"{EMOJIS['info']} Drive 505 Bot Commands",
            description="**كل الأوامر تدعم:**\n✅ المنشن | ✅ الريبلاي | ✅ الـ ID\n\n**اختصارات الأوامر:**",
            color=COLORS["info"]
        )
        
        commands_list = [
            ("🛡️ Moderation", ["ban/b/حظر", "kick/k/طرد", "mute/m/كتم", "unmute/um/فك_كتم", "clear/c/مسح", "clearuser/cu/مسح_شخص", "timeout/to/تايم"]),
            ("⚠️ Warnings", ["warn/w/تحذير/ت", "checkwarn/cw/تحذيرات", "removewarn/rw1/مسح_تحذير", "resetwarn/rw/مسح_الكل"]),
            ("🔒 Jail", ["jail/j/سجن", "unjail/uj/فك_سجن", "saveroles/save/حفظ", "restoreroles/restore/استرجاع"]),
            ("🛡️ Protection", ["lock/قفل", "unlock/فتح", "lockdown/غلق", "unlockdown/فتح_السيرفر", "block/حظر_بوت", "unblock/الغاء_حظر"]),
            ("👑 Role", ["addrole/ar/رول", "removerole/rr/شيل_رول", "addallowedrole/add/اضف_رتبة", "removeallowedrole/remove/شيل_رتبة"]),
            ("🔨 Advanced Ban", ["ban/b/حظر", "ipban/banip/حظر_ايبي", "hwidban/banhwid/حظر_هردوير", "unban/ub/فك_حظر"]),
            ("📡 Lines System", ["line #channel", "lines", "removeline #channel", "clearlines"]),
            ("🎙️ Temp Voice", ["temp set <channel>", "temp remove", "temp info", "panel #channel"]),
            ("🎫 Tickets", ["ticket setup", "ticket panel #channel", "ticket logs #channel", "ticket staff @role", "ticket category <id>"]),
            ("🔔 Come", ["come @user <message>", "تعال @user <message>"]),
            ("💍 Marriage", ["marry/ارتبط", "divorce/طلاق"]),
            ("🎭 Fun", ["goodnight/gn/تصبح_على_خير", "ez/ارزع", "setgif/تعيين_جيف"]),
            ("ℹ️ Info", ["avatar/a/صورتي", "banner/bu/بنر", "userinfo/ui/معلومات_عضو", "serverinfo/si/معلومات_سيرفر", "roleinfo/ri/معلومات_رتبة", "botinfo/bi/معلومات_بوت", "nickname/nick/n/اسم"]),
            ("🆘 Help", ["help/h/helps/مساعدة"])
        ]
        
        for category, cmds in commands_list:
            embed.add_field(
                name=category,
                value="\n".join([f"`!{c}`" for c in cmds]),
                inline=False
            )
        
        embed.add_field(
            name="📌 ريبلاي (بدون !)",
            value="**ارد على رسالة الشخص واكتب:**\n"
                  "`ت` - تحذير\n"
                  "`تايم 30s` - Timeout\n"
                  "`ن اسم` - تغيير النيك\n"
                  "`ن` - مسح النيك\n"
                  "`م` - كتم\n"
                  "`فك` - فك الكتم\n"
                  "`ط` - طرد\n"
                  "`ب` - حظر\n"
                  "`سجن 10m` - سجن\n"
                  "`فك_سجن` - فك السجن",
            inline=False
        )
        
        embed.add_field(
            name="💍 Marriage System",
            value="**كيفية الزواج:**\n"
                  "1. `!marry @user` - إرسال طلب زواج\n"
                  "2. الشخص المستهدف يضغط **Accept** أو **Reject**\n"
                  "3. بعد القبول، يتم الزواج فوراً\n\n"
                  "**للطلاق:** `!divorce`",
            inline=False
        )
        
        embed.add_field(
            name="📡 Lines System",
            value="**الأوامر:**\n"
                  "• `!line #channel` - إضافة قناة\n"
                  "• `!lines` - عرض القنوات\n"
                  "• `!removeline #channel` - إزالة قناة\n"
                  "• `!clearlines` - مسح كل القنوات\n\n"
                  "**كيف يعمل:**\n"
                  "أي رسالة في القنوات المضافة → يبعت صورة ثابتة لباقي القنوات",
            inline=False
        )
        
        embed.add_field(
            name="🎫 Ticket System",
            value="**الإعداد:**\n"
                  "1. `!ticket setup` - إعداد النظام\n"
                  "2. `!ticket staff @role` - تعيين رتبة الإدارة\n"
                  "3. `!ticket logs #channel` - تعيين روم اللوجات\n"
                  "4. `!ticket category <id>` - تعيين كاتيجوري\n"
                  "5. `!ticket panel #channel` - إرسال لوحة التذاكر\n\n"
                  "**المميزات:**\n"
                  "• 6 أنواع تذاكر\n"
                  "• أزرار Accept, Close, Invite\n"
                  "• Transcript وتقييم بعد الإغلاق",
            inline=False
        )
        
        embed.add_field(
            name="🔔 Come Command",
            value="**الاستخدام:**\n"
                  "• `!come @user رسالتك` - إرسال دعوة\n"
                  "• بالريبلاي: ارد على رسالة الشخص واكتب `!come رسالتك`\n\n"
                  "**النتيجة:**\n"
                  "المستخدم يستقبل رسالة خاصة تحتوي الرسالة والروم",
            inline=False
        )
        
        embed.set_footer(text="Type !help <command> for more details | Prefix: !")
        await send_permanent(ctx, embed)

async def setup(bot):
    bot.add_cog(Help(bot))