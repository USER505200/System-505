# database.py
import aiosqlite
from config import DB_PATH


async def _ensure_column(conn, table: str, column: str, definition: str):
    async with conn.execute(f"PRAGMA table_info({table})") as cursor:
        rows = await cursor.fetchall()
    columns = {row[1] for row in rows}
    if column not in columns:
        await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

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
        
        # جدول Temp Voice Settings
        await db.execute('''
            CREATE TABLE IF NOT EXISTS temp_voice_settings (
                guild_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL
            )
        ''')
        
        # جدول إعدادات التذاكر
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ticket_settings (
                guild_id TEXT PRIMARY KEY,
                category_id TEXT,
                logs_channel_id TEXT,
                staff_role_id TEXT,
                rating_channel_id TEXT,
                ai_admin_role_id TEXT,
                ai_owner_role_id TEXT,
                archive_category_id TEXT
            )
        ''')
        
        # جدول إعدادات أنواع التذاكر
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ticket_type_settings (
                guild_id TEXT NOT NULL,
                ticket_type TEXT NOT NULL,
                category_id TEXT,
                ai_delay_seconds INTEGER,
                PRIMARY KEY (guild_id, ticket_type)
            )
        """)

        # جدول التذاكر المفتوحة حتى لا تضيع بعد إعادة تشغيل البوت
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                ticket_type TEXT NOT NULL,
                staff_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ticket_message_id TEXT,
                ai_enabled INTEGER DEFAULT 0,
                ai_active INTEGER DEFAULT 0,
                ai_busy INTEGER DEFAULT 0,
                ai_delay_seconds INTEGER,
                ai_set_at TIMESTAMP,
                closed INTEGER DEFAULT 0
            )
        """)

        # ========== جدول Lines Channels ==========
        await db.execute('''
            CREATE TABLE IF NOT EXISTS lines_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        

        # Migrations for existing databases.
        await _ensure_column(db, "ticket_settings", "rating_channel_id", "TEXT")
        await _ensure_column(db, "ticket_settings", "ai_admin_role_id", "TEXT")
        await _ensure_column(db, "ticket_settings", "ai_owner_role_id", "TEXT")
        await _ensure_column(db, "ticket_settings", "archive_category_id", "TEXT")
        await _ensure_column(db, "ticket_type_settings", "ai_delay_seconds", "INTEGER")
        await _ensure_column(db, "active_tickets", "ticket_message_id", "TEXT")
        await _ensure_column(db, "active_tickets", "ai_enabled", "INTEGER DEFAULT 0")
        await _ensure_column(db, "active_tickets", "ai_active", "INTEGER DEFAULT 0")
        await _ensure_column(db, "active_tickets", "ai_busy", "INTEGER DEFAULT 0")
        await _ensure_column(db, "active_tickets", "ai_delay_seconds", "INTEGER")
        await _ensure_column(db, "active_tickets", "ai_set_at", "TIMESTAMP")
        await _ensure_column(db, "active_tickets", "closed", "INTEGER DEFAULT 0")
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

# ========== دوال التذاكر ==========

async def set_ticket_category(guild_id: int, category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ticket_settings (guild_id, category_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET category_id = excluded.category_id
        ''', (str(guild_id), str(category_id)))
        await db.commit()

async def set_ticket_logs(guild_id: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ticket_settings (guild_id, logs_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET logs_channel_id = excluded.logs_channel_id
        ''', (str(guild_id), str(channel_id)))
        await db.commit()

async def set_ticket_staff_role(guild_id: int, role_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ticket_settings (guild_id, staff_role_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET staff_role_id = excluded.staff_role_id
        ''', (str(guild_id), str(role_id)))
        await db.commit()

async def set_ticket_rating_channel(guild_id: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ticket_settings (guild_id, rating_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET rating_channel_id = excluded.rating_channel_id
        ''', (str(guild_id), str(channel_id)))
        await db.commit()

async def set_ticket_ai_roles(guild_id: int, admin_role_id: int = None, owner_role_id: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ticket_settings (guild_id, ai_admin_role_id, ai_owner_role_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                ai_admin_role_id = COALESCE(excluded.ai_admin_role_id, ticket_settings.ai_admin_role_id),
                ai_owner_role_id = COALESCE(excluded.ai_owner_role_id, ticket_settings.ai_owner_role_id)
        ''', (str(guild_id), str(admin_role_id) if admin_role_id else None, str(owner_role_id) if owner_role_id else None))
        await db.commit()

async def get_ticket_category(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT category_id FROM ticket_settings WHERE guild_id = ?
        ''', (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def get_ticket_logs(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT logs_channel_id FROM ticket_settings WHERE guild_id = ?
        ''', (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def get_ticket_staff_role(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT staff_role_id FROM ticket_settings WHERE guild_id = ?
        ''', (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def get_ticket_rating_channel(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT rating_channel_id FROM ticket_settings WHERE guild_id = ?
        ''', (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def get_ticket_ai_roles(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT ai_admin_role_id, ai_owner_role_id FROM ticket_settings WHERE guild_id = ?
        ''', (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            return result if result else (None, None)

async def set_ticket_archive_category(guild_id: int, category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ticket_settings (guild_id, archive_category_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET archive_category_id = excluded.archive_category_id
        ''', (str(guild_id), str(category_id)))
        await db.commit()

async def get_ticket_archive_category(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT archive_category_id FROM ticket_settings WHERE guild_id = ?
        ''', (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

# ========== دوال Lines ==========

async def add_line_channel(guild_id: int, channel_id: int):
    """إضافة قناة لنظام Lines"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO lines_channels (guild_id, channel_id)
            VALUES (?, ?)
        ''', (str(guild_id), str(channel_id)))
        await db.commit()

async def remove_line_channel(guild_id: int, channel_id: int):
    """إزالة قناة من نظام Lines"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            DELETE FROM lines_channels WHERE guild_id = ? AND channel_id = ?
        ''', (str(guild_id), str(channel_id)))
        await db.commit()

async def get_line_channels(guild_id: int):
    """جلب جميع قنوات Lines في السيرفر"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT channel_id FROM lines_channels WHERE guild_id = ?
        ''', (str(guild_id),)) as cursor:
            return [row[0] for row in await cursor.fetchall()]

async def clear_line_channels(guild_id: int):
    """مسح جميع قنوات Lines في السيرفر"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            DELETE FROM lines_channels WHERE guild_id = ?
        ''', (str(guild_id),))
        await db.commit()

# ========== دوال التذاكر الجديدة متعددة الأنواع ==========

async def set_ticket_type_category(guild_id: int, ticket_type: str, category_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ticket_type_settings (guild_id, ticket_type, category_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, ticket_type) DO UPDATE SET category_id = excluded.category_id
        ''', (str(guild_id), ticket_type, str(category_id)))
        await db.commit()

async def get_ticket_type_category(guild_id: int, ticket_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT category_id FROM ticket_type_settings WHERE guild_id = ? AND ticket_type = ?
        ''', (str(guild_id), ticket_type)) as cursor:
            result = await cursor.fetchone()
            if result and result[0]:
                return result[0]
    return await get_ticket_category(guild_id)

async def set_ticket_type_ai_delay(guild_id: int, ticket_type: str, seconds):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO ticket_type_settings (guild_id, ticket_type, ai_delay_seconds)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, ticket_type) DO UPDATE SET ai_delay_seconds = excluded.ai_delay_seconds
        ''', (str(guild_id), ticket_type, int(seconds) if seconds is not None else None))
        await db.commit()

async def get_ticket_type_ai_delay(guild_id: int, ticket_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT ai_delay_seconds FROM ticket_type_settings WHERE guild_id = ? AND ticket_type = ?
        ''', (str(guild_id), ticket_type)) as cursor:
            result = await cursor.fetchone()
            return int(result[0]) if result and result[0] else None

async def create_active_ticket(guild_id: int, channel_id: int, user_id: int, ticket_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO active_tickets (guild_id, channel_id, user_id, ticket_type)
            VALUES (?, ?, ?, ?)
        ''', (str(guild_id), str(channel_id), str(user_id), ticket_type))
        await db.commit()
        return cursor.lastrowid

async def get_active_ticket_by_user(guild_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT id, channel_id, user_id, ticket_type, staff_id, created_at
            FROM active_tickets WHERE guild_id = ? AND user_id = ? AND COALESCE(closed, 0) = 0
            ORDER BY id DESC LIMIT 1
        ''', (str(guild_id), str(user_id))) as cursor:
            return await cursor.fetchone()

async def get_active_ticket_by_user_kind(guild_id: int, user_id: int, ticket_types: list):
    if not ticket_types:
        return None
    placeholders = ','.join(['?'] * len(ticket_types))
    params = [str(guild_id), str(user_id)] + list(ticket_types)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(f'''
            SELECT id, channel_id, user_id, ticket_type, staff_id, created_at
            FROM active_tickets
            WHERE guild_id = ? AND user_id = ? AND ticket_type IN ({placeholders}) AND COALESCE(closed, 0) = 0
            ORDER BY id DESC LIMIT 1
        ''', params) as cursor:
            return await cursor.fetchone()

async def get_active_ticket_by_channel(guild_id: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT id, guild_id, channel_id, user_id, ticket_type, staff_id, created_at,
                   ticket_message_id, ai_enabled, ai_active, ai_busy, ai_delay_seconds, ai_set_at, closed
            FROM active_tickets WHERE guild_id = ? AND channel_id = ?
            ORDER BY id DESC LIMIT 1
        ''', (str(guild_id), str(channel_id))) as cursor:
            return await cursor.fetchone()

async def get_active_ticket(ticket_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT id, guild_id, channel_id, user_id, ticket_type, staff_id, created_at,
                   ticket_message_id, ai_enabled, ai_active, ai_busy, ai_delay_seconds, ai_set_at, closed
            FROM active_tickets WHERE id = ?
        ''', (int(ticket_id),)) as cursor:
            return await cursor.fetchone()

async def set_active_ticket_staff(ticket_id: int, staff_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE active_tickets SET staff_id = ?, ai_active = 0, ai_busy = 0 WHERE id = ?
        ''', (str(staff_id) if staff_id is not None else None, int(ticket_id)))
        await db.commit()

async def set_active_ticket_message(ticket_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE active_tickets SET ticket_message_id = ? WHERE id = ?
        ''', (str(message_id), int(ticket_id)))
        await db.commit()

async def set_ticket_ai_delay(ticket_id: int, seconds: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE active_tickets
            SET ai_enabled = 1, ai_delay_seconds = ?, ai_set_at = CURRENT_TIMESTAMP, ai_active = 0, ai_busy = 0
            WHERE id = ?
        ''', (int(seconds), int(ticket_id)))
        await db.commit()

async def disable_ticket_ai(ticket_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE active_tickets
            SET ai_enabled = 0, ai_active = 0, ai_busy = 0
            WHERE id = ?
        ''', (int(ticket_id),))
        await db.commit()

async def set_ticket_ai_active(ticket_id: int, active: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE active_tickets SET ai_enabled = 1, ai_active = ?, ai_busy = 0 WHERE id = ?
        ''', (1 if active else 0, int(ticket_id)))
        await db.commit()

async def set_ticket_ai_busy(ticket_id: int, busy: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE active_tickets SET ai_busy = ? WHERE id = ?
        ''', (1 if busy else 0, int(ticket_id)))
        await db.commit()

async def get_ai_pending_tickets():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT id, guild_id, channel_id, user_id, ticket_type, staff_id, created_at,
                   ticket_message_id, ai_enabled, ai_active, ai_busy, ai_delay_seconds, ai_set_at, closed
            FROM active_tickets
            WHERE ai_enabled = 1 AND ai_active = 0 AND (staff_id IS NULL OR staff_id = '') AND COALESCE(closed, 0) = 0
        ''') as cursor:
            return await cursor.fetchall()

async def set_active_ticket_closed(ticket_id: int, closed: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE active_tickets
            SET closed = ?, ai_enabled = 0, ai_active = 0, ai_busy = 0
            WHERE id = ?
        ''', (1 if closed else 0, int(ticket_id)))
        await db.commit()

async def delete_active_ticket(ticket_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM active_tickets WHERE id = ?', (int(ticket_id),))
        await db.commit()

async def delete_active_ticket_by_channel(guild_id: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            DELETE FROM active_tickets WHERE guild_id = ? AND channel_id = ?
        ''', (str(guild_id), str(channel_id)))
        await db.commit()
