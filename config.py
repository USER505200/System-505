import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
DB_PATH = "bot.db"

# ========== AI / OpenRouter ==========
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "https://discord.com")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "Drive 505 Ticket AI")
AI_RESPONSE_MAX_CHARS = int(os.getenv("AI_RESPONSE_MAX_CHARS", "700"))
AI_HISTORY_LIMIT = int(os.getenv("AI_HISTORY_LIMIT", "18"))

EMOJIS = {
    "success": "<:80012verified:1485901284719460403>",
    "error": "<:6426error:1485901393075376179>",
    "warning": "<:3warnings:1485901486511624262>",
    "loading": "<:3536timeout:1485901553490595870>",
    "ban": "<:ban:1485901519525253173>",
    "kick": "<:Kick:1485901574344806550>",
    "mute": "<:servermute:1485901606464520312>",
    "unmute": "<:6859unmute:1485901623128752189>",
    "jail": "<:142Jail:1485901641520779366>",
    "timeout": "<:3536timeout:1485901553490595870>",
    "warn_1": "<:1warning:1485901428328501308>",
    "warn_2": "<:2warnings:1485901458179362916>",
    "warn_3": "<:3warnings:1485901486511624262>",
    "warns": "<:warnings:1485901661099659325>",
    "clear": "<:Clear:1485901795824898078>",
    "save": "<:save:1485901739994513429>",
    "security": "<:security:1485901778896556063>",
    "pause": "<:pause:1485901706880614515>",
    "marry": "<:Marry:1485901683027480596>",
    "request_marry": "<:Request_Marry:1485901761892847636>",
    "info": "<:warnings:1485901661099659325>",
}

COLORS = {
    "default": 0x000000, "success": 0x00FF00, "error": 0xFF0000,
    "warning": 0xFFA500, "ban": 0xFF0000, "kick": 0xFF0000,
    "unban": 0x00FF00, "unmute": 0x00FF00, "unjail": 0x00FF00, "info": 0x000000,
}

DELETE_RESPONSE_DELAY = 10

# ========== الصلاحيات ==========
# رتبة الحظر والطرد (ID: 1485542654644060252)
BAN_KICK_ROLE = "1485542654644060252"
# رتبة الإدارة العادية (ID: 1485545453603913838)
STAFF_ROLE = "1485545225802875002"

COMMAND_PERMISSIONS = {
    # ========== أوامر الحظر والطرد - فقط رتبة معينة ==========
    "ban": {"allowed_roles": [BAN_KICK_ROLE], "description": "حظر عضو"},
    "kick": {"allowed_roles": [BAN_KICK_ROLE], "description": "طرد عضو"},
    "ipban": {"allowed_roles": [BAN_KICK_ROLE], "description": "حظر IP"},
    "hwidban": {"allowed_roles": [BAN_KICK_ROLE], "description": "حظر Hardware ID"},
    "unban": {"allowed_roles": [BAN_KICK_ROLE], "description": "فك الحظر"},
    
    # ========== أوامر الإدارة - أدمن + رتبة STAFF_ROLE ==========
    "mute": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "كتم عضو"},
    "unmute": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "فك الكتم"},
    "clear": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "مسح الشات (حد أقصى 20 للرتبة)"},
    "clearuser": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "مسح رسائل شخص"},
    "warn": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "إضافة تحذير"},
    "checkwarn": {"allowed_roles": [], "description": "عرض التحذيرات"},
    "removewarn": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "حذف تحذير"},
    "resetwarn": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "مسح كل التحذيرات"},
    "jail": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "سجن عضو"},
    "unjail": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "فك السجن"},
    "saveroles": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "حفظ الرتب"},
    "restoreroles": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "استرجاع الرتب"},
    "nickname": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "تغيير النيك نيم"},
    "timeout": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "تقييد عضو"},
    
    # ========== أوامر الحماية - أدمن فقط ==========
    "lock": {"allowed_roles": ["admin_only"], "description": "قفل روم"},
    "unlock": {"allowed_roles": ["admin_only"], "description": "فتح روم"},
    "lockdown": {"allowed_roles": ["admin_only"], "description": "غلق السيرفر"},
    "unlockdown": {"allowed_roles": ["admin_only"], "description": "فتح السيرفر"},
    "block": {"allowed_roles": ["admin_only"], "description": "حظر من البوت"},
    "unblock": {"allowed_roles": ["admin_only"], "description": "إلغاء حظر البوت"},
    "addrole": {"allowed_roles": ["admin_only"], "description": "إضافة رتبة"},
    "removerole": {"allowed_roles": ["admin_only"], "description": "إزالة رتبة"},
    "addallowedrole": {"allowed_roles": ["admin_only"], "description": "إضافة رتبة مصرح بها"},
    "removeallowedrole": {"allowed_roles": ["admin_only"], "description": "إزالة رتبة مصرح بها"},
    
    # ========== أوامر Temp Voice ==========
    "temp": {"allowed_roles": ["admin_only"], "description": "أوامر نظام الصوت المؤقت"},
    "panel": {"allowed_roles": ["admin_only"], "description": "إرسال لوحة التحكم"},
    
    # ========== أوامر التذاكر ==========
    "ticket": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "نظام التذاكر - setup/panel/logs/staff/category/archive/ratings/airoles"},
    "ai-time": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "تفعيل AI مؤقت للتكت"},
    "set-ai": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "ضبط AI تلقائي لكل نوع تكت"},
    
    # ========== أوامر ترفيهية - الجميع ==========
    "marry": {"allowed_roles": [], "description": "الارتباط"},
    "divorce": {"allowed_roles": [], "description": "الطلاق"},
    "goodnight": {"allowed_roles": [], "description": "تصبح على خير"},
    "ez": {"allowed_roles": ["admin_only"], "description": "أمر ترول"},
    "setgif": {"allowed_roles": ["admin_only"], "description": "تخصيص GIF"},
    
    # ========== أوامر المعلومات - الجميع ==========
    "avatar": {"allowed_roles": [], "description": "عرض الصورة"},
    "banner": {"allowed_roles": [], "description": "عرض البانر"},
    "userinfo": {"allowed_roles": [], "description": "معلومات العضو"},
    "serverinfo": {"allowed_roles": [], "description": "معلومات السيرفر"},
    "roleinfo": {"allowed_roles": [], "description": "معلومات الرتبة"},
    "botinfo": {"allowed_roles": [], "description": "معلومات البوت"},
    "help": {"allowed_roles": [], "description": "قائمة المساعدة"},
    
    # ========== أوامر أخرى ==========
    "come": {"allowed_roles": ["admin_only", STAFF_ROLE], "description": "إرسال دعوة لمستخدم مع رسالة مخصصة"},
    "line": {"allowed_roles": ["admin_only"], "description": "إضافة قناة لنظام Lines"},
    "lines": {"allowed_roles": ["admin_only"], "description": "عرض جميع قنوات Lines"},
    "removeline": {"allowed_roles": ["admin_only"], "description": "إزالة قناة من نظام Lines"},
    "clearlines": {"allowed_roles": ["admin_only"], "description": "مسح جميع قنوات Lines"},
}

def get_command_permission(command_name: str) -> list:
    return COMMAND_PERMISSIONS.get(command_name, {}).get("allowed_roles", [])

def is_command_allowed(command_name: str, user_roles: list) -> bool:
    permissions = get_command_permission(command_name)
    if not permissions:
        return True
    if "admin_only" in permissions:
        return "admin_only"
    for role in user_roles:
        if str(role.id) in permissions:
            return True
    return False