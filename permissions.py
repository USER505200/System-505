# config/permissions.py
"""
ملف التحكم بالصلاحيات - حدد هنا الرتب المسموح لها بكل أمر
"""

# ========== إعدادات عامة ==========
# الرتب التي لها صلاحية Administrator (تجاوز كل الصلاحيات)
ADMIN_ROLES = [
    # "role_id",  # ضع هنا ID رتبة الأدمن
]

# ========== صلاحيات الأوامر ==========
# كل أمر له قائمة رتب مسموح لها
# لو القائمة فاضية، الأمر متاح للكل
# لو القائمة فيها "admin_only"، الأمر للأدمن فقط

COMMAND_PERMISSIONS = {
    # ========== أوامر الإدارة (Moderation) ==========
    "ban": {
        "allowed_roles": ["admin_only"],  # أدمن فقط
        "description": "حظر عضو"
    },
    "kick": {
        "allowed_roles": ["admin_only"],
        "description": "طرد عضو"
    },
    "mute": {
        "allowed_roles": ["admin_only"],
        "description": "كتم عضو"
    },
    "unmute": {
        "allowed_roles": ["admin_only"],
        "description": "فك الكتم"
    },
    "clear": {
        "allowed_roles": ["admin_only"],
        "description": "مسح الشات"
    },
    "clearuser": {
        "allowed_roles": ["admin_only"],
        "description": "مسح رسائل شخص"
    },
    
    # ========== أوامر التحذيرات (Warns) ==========
    "warn": {
        "allowed_roles": ["admin_only"],
        "description": "إضافة تحذير"
    },
    "checkwarn": {
        "allowed_roles": [],  # متاح للكل
        "description": "عرض التحذيرات"
    },
    "removewarn": {
        "allowed_roles": ["admin_only"],
        "description": "حذف تحذير"
    },
    "resetwarn": {
        "allowed_roles": ["admin_only"],
        "description": "مسح كل التحذيرات"
    },
    
    # ========== أوامر السجن (Jail) ==========
    "jail": {
        "allowed_roles": ["admin_only"],
        "description": "سجن عضو"
    },
    "unjail": {
        "allowed_roles": ["admin_only"],
        "description": "فك السجن"
    },
    "saveroles": {
        "allowed_roles": ["admin_only"],
        "description": "حفظ الرتب"
    },
    "restoreroles": {
        "allowed_roles": ["admin_only"],
        "description": "استرجاع الرتب"
    },
    
    # ========== أوامر الحماية (Protection) ==========
    "lock": {
        "allowed_roles": ["admin_only"],
        "description": "قفل روم"
    },
    "unlock": {
        "allowed_roles": ["admin_only"],
        "description": "فتح روم"
    },
    "lockdown": {
        "allowed_roles": ["admin_only"],
        "description": "غلق السيرفر"
    },
    "unlockdown": {
        "allowed_roles": ["admin_only"],
        "description": "فتح السيرفر"
    },
    "block": {
        "allowed_roles": ["admin_only"],
        "description": "حظر من البوت"
    },
    "unblock": {
        "allowed_roles": ["admin_only"],
        "description": "إلغاء حظر البوت"
    },
    "addallowedrole": {
        "allowed_roles": ["admin_only"],
        "description": "إضافة رتبة مصرح بها"
    },
    "removeallowedrole": {
        "allowed_roles": ["admin_only"],
        "description": "إزالة رتبة مصرح بها"
    },
    
    # ========== أوامر إدارة الرتب (Role Management) ==========
    "addrole": {
        "allowed_roles": ["admin_only"],
        "description": "إضافة رتبة لعضو"
    },
    "removerole": {
        "allowed_roles": ["admin_only"],
        "description": "إزالة رتبة من عضو"
    },
    
    # ========== أوامر ترفيهية (Fun) ==========
    "marry": {
        "allowed_roles": [],  # متاح للكل
        "description": "الارتباط"
    },
    "divorce": {
        "allowed_roles": [],  # متاح للكل
        "description": "الطلاق"
    },
    "goodnight": {
        "allowed_roles": [],  # متاح للكل
        "description": "تصبح على خير"
    },
    "ez": {
        "allowed_roles": ["admin_only"],
        "description": "أمر ترول (يحتاج تأكيد)"
    },
    "setgif": {
        "allowed_roles": ["admin_only"],
        "description": "تخصيص GIF"
    },
    
    # ========== أوامر المعلومات (Info) ==========
    "avatar": {
        "allowed_roles": [],  # متاح للكل
        "description": "عرض الصورة"
    },
    "banner": {
        "allowed_roles": [],  # متاح للكل
        "description": "عرض البانر"
    },
    "userinfo": {
        "allowed_roles": [],  # متاح للكل
        "description": "معلومات العضو"
    },
    "serverinfo": {
        "allowed_roles": [],  # متاح للكل
        "description": "معلومات السيرفر"
    },
    "roleinfo": {
        "allowed_roles": [],  # متاح للكل
        "description": "معلومات الرتبة"
    },
    "botinfo": {
        "allowed_roles": [],  # متاح للكل
        "description": "معلومات البوت"
    },
    "nickname": {
        "allowed_roles": ["admin_only"],
        "description": "تغيير النيك نيم"
    },
    "help": {
        "allowed_roles": [],  # متاح للكل
        "description": "قائمة المساعدة"
    },
}

# ========== دوال مساعدة ==========
def is_admin(role_id: str) -> bool:
    """التحقق مما إذا كانت الرتبة من رتب الأدمن"""
    return role_id in ADMIN_ROLES or role_id == "admin_only"

def get_command_permission(command_name: str) -> list:
    """جلب صلاحيات أمر معين"""
    return COMMAND_PERMISSIONS.get(command_name, {}).get("allowed_roles", [])

def is_command_allowed(command_name: str, user_roles: list) -> bool:
    """التحقق مما إذا كان المستخدم مسموح له باستخدام أمر"""
    permissions = get_command_permission(command_name)
    
    # لو مفيش صلاحيات محددة، الأمر متاح للكل
    if not permissions:
        return True
    
    # لو الأمر للأدمن فقط
    if "admin_only" in permissions:
        # التحقق من صلاحية Administrator في Discord
        # هتتعامل معاها في الـ Check
        return "admin_only"
    
    # التحقق من الرتب المحددة
    for role in user_roles:
        if str(role.id) in permissions:
            return True
    
    return False