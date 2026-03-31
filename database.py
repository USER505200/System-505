# database.py
import aiosqlite
from config import DB_PATH

async def init_db():
    """تهيئة قاعدة البيانات"""
    async with aiosqlite.connect(DB_PATH) as db:
        # جدول التحذيرات
        await db.execute('''
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                reason TEXT,
                warned_by TEXT,
                warned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول الرتب المصرح بها
        await db.execute('''
            CREATE TABLE IF NOT EXISTS allowed_roles (
                guild_id TEXT NOT NULL,
                role_id TEXT NOT NULL,
                PRIMARY KEY (guild_id, role_id)
            )
        ''')
        
        # جدول الرتب المحفوظة
        await db.execute('''
            CREATE TABLE IF NOT EXISTS saved_roles (
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                roles TEXT,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        
        # جدول الزواج
        await db.execute('''
            CREATE TABLE IF NOT EXISTS marriages (
                user1_id TEXT NOT NULL,
                user2_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                married_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user1_id, user2_id)
            )
        ''')
        
        # جدول المحظورين من البوت
        await db.execute('''
            CREATE TABLE IF NOT EXISTS blocked_users (
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                blocked_by TEXT,
                blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        
        # جدول حظر IP
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ip_bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                reason TEXT,
                banned_by TEXT,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول حظر HWID
        await db.execute('''
            CREATE TABLE IF NOT EXISTS hwid_bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                reason TEXT,
                banned_by TEXT,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ========== جدول Temp Voice Settings (مهم جداً) ==========
        await db.execute('''
            CREATE TABLE IF NOT EXISTS temp_voice_settings (
                guild_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL
            )
        ''')
        
        await db.commit()

# ========== دوال التحذيرات ==========

async def add_warn(user_id: int, guild_id: int, reason: str, warned_by: int):
    """إضافة تحذير لمستخدم"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO warns (user_id, guild_id, reason, warned_by) VALUES (?, ?, ?, ?)",
            (str(user_id), str(guild_id), reason, str(warned_by))
        )
        await db.commit()

async def get_warns(user_id: int, guild_id: int):
    """جلب جميع تحذيرات المستخدم"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, reason, warned_by, warned_at FROM warns WHERE user_id = ? AND guild_id = ? ORDER BY warned_at DESC",
            (str(user_id), str(guild_id))
        ) as cursor:
            return await cursor.fetchall()

async def get_warns_count(user_id: int, guild_id: int):
    """جلب عدد تحذيرات المستخدم"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id = ? AND guild_id = ?",
            (str(user_id), str(guild_id))
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def remove_warn(warn_id: int, guild_id: int):
    """حذف تحذير محدد"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM warns WHERE id = ? AND guild_id = ?",
            (warn_id, str(guild_id))
        )
        await db.commit()

async def clear_warns(user_id: int, guild_id: int):
    """حذف جميع تحذيرات المستخدم"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM warns WHERE user_id = ? AND guild_id = ?",
            (str(user_id), str(guild_id))
        )
        await db.commit()

# ========== دوال الرتب المصرح بها ==========

async def add_allowed_role(guild_id: int, role_id: int):
    """إضافة رتبة مسموح لها"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO allowed_roles (guild_id, role_id) VALUES (?, ?)",
            (str(guild_id), str(role_id))
        )
        await db.commit()

async def remove_allowed_role(guild_id: int, role_id: int):
    """إزالة رتبة مسموح لها"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM allowed_roles WHERE guild_id = ? AND role_id = ?",
            (str(guild_id), str(role_id))
        )
        await db.commit()

async def get_allowed_roles(guild_id: int):
    """جلب الرتب المصرح بها"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role_id FROM allowed_roles WHERE guild_id = ?",
            (str(guild_id),)
        ) as cursor:
            return [row[0] for row in await cursor.fetchall()]

# ========== دوال الرتب المحفوظة ==========

async def save_roles(user_id: int, guild_id: int, roles: list):
    """حفظ رتب المستخدم"""
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO saved_roles (user_id, guild_id, roles) VALUES (?, ?, ?)",
            (str(user_id), str(guild_id), json.dumps(roles))
        )
        await db.commit()

async def get_saved_roles(user_id: int, guild_id: int):
    """جلب الرتب المحفوظة"""
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT roles FROM saved_roles WHERE user_id = ? AND guild_id = ?",
            (str(user_id), str(guild_id))
        ) as cursor:
            result = await cursor.fetchone()
            return json.loads(result[0]) if result else []

async def delete_saved_roles(user_id: int, guild_id: int):
    """حذف الرتب المحفوظة"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM saved_roles WHERE user_id = ? AND guild_id = ?",
            (str(user_id), str(guild_id))
        )
        await db.commit()

# ========== دوال الزواج ==========

async def marry(user1_id: int, user2_id: int, guild_id: int):
    """تسجيل زواج"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO marriages (user1_id, user2_id, guild_id) VALUES (?, ?, ?)",
            (str(user1_id), str(user2_id), str(guild_id))
        )
        await db.commit()

async def divorce(user_id: int, guild_id: int):
    """فسخ الزواج"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM marriages WHERE (user1_id = ? OR user2_id = ?) AND guild_id = ?",
            (str(user_id), str(user_id), str(guild_id))
        )
        await db.commit()

async def get_married(user_id: int, guild_id: int):
    """جلب شريك الزواج"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user1_id, user2_id FROM marriages WHERE (user1_id = ? OR user2_id = ?) AND guild_id = ?",
            (str(user_id), str(user_id), str(guild_id))
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0] if str(result[0]) != str(user_id) else result[1]
            return None

# ========== دوال الحظر من البوت ==========

async def block_user(user_id: int, guild_id: int, blocked_by: int):
    """حظر مستخدم من البوت"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO blocked_users (user_id, guild_id, blocked_by) VALUES (?, ?, ?)",
            (str(user_id), str(guild_id), str(blocked_by))
        )
        await db.commit()

async def unblock_user(user_id: int, guild_id: int):
    """إلغاء حظر مستخدم من البوت"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM blocked_users WHERE user_id = ? AND guild_id = ?",
            (str(user_id), str(guild_id))
        )
        await db.commit()

async def is_blocked(user_id: int, guild_id: int):
    """التحقق من حظر المستخدم"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM blocked_users WHERE user_id = ? AND guild_id = ?",
            (str(user_id), str(guild_id))
        ) as cursor:
            return await cursor.fetchone() is not None

# ========== دوال حظر IP و HWID ==========

async def add_ip_ban(user_id: int, guild_id: int, reason: str, banned_by: int):
    """تسجيل حظر IP"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO ip_bans (user_id, guild_id, reason, banned_by) VALUES (?, ?, ?, ?)",
            (str(user_id), str(guild_id), reason, str(banned_by))
        )
        await db.commit()

async def add_hwid_ban(user_id: int, guild_id: int, reason: str, banned_by: int):
    """تسجيل حظر HWID"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO hwid_bans (user_id, guild_id, reason, banned_by) VALUES (?, ?, ?, ?)",
            (str(user_id), str(guild_id), reason, str(banned_by))
        )
        await db.commit()

# ========== دوال Temp Voice ==========

async def set_temp_voice_channel(guild_id: int, channel_id: int):
    """حفظ روم الصيانة"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO temp_voice_settings (guild_id, channel_id)
            VALUES (?, ?)
        ''', (str(guild_id), str(channel_id)))
        await db.commit()

async def remove_temp_voice_channel(guild_id: int):
    """إزالة روم الصيانة"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            DELETE FROM temp_voice_settings WHERE guild_id = ?
        ''', (str(guild_id),))
        await db.commit()

async def get_temp_voice_channel(guild_id: int):
    """جلب روم الصيانة"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT channel_id FROM temp_voice_settings WHERE guild_id = ?
        ''', (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None