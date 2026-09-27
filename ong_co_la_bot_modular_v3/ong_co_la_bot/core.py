
import os
import re
import time
import random
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from threading import Thread

from flask import Flask
import discord
from discord.ext import commands, tasks

# ============================================================
# 🐝 ONG & CỎ 4 LÁ — BẢN HỢP NHẤT
# ============================================================
# Giữ nguyên nguyên tắc học hiện tại:
# - Bật camera -> bắt đầu session
# - Tắt camera / rời Voice -> kết thúc session
# - 9 phút học = 1 Cỏ
# - Streak dựa trên ngày học
# - Toàn bộ mốc lịch dùng giờ Việt Nam
#
# Các hệ thống mới:
# - Reminder nhiều cái / xem / xóa / nhiều dòng
# - BXH ngày / tuần / tháng / năm
# - Shop + Túi đồ + dùng vật phẩm
# - Hộp Quà Nhân Phẩm là MỘT món trong Shop
# - X2 năng lượng
# - Freeze streak tự kích hoạt
# - Giảm án kỷ luật
# - Đổi tên phòng học tạm thời
# - Tạo phòng học/phòng họp tự do, có thời hạn
# - Phòng riêng / mở cho mọi người / mời thành viên
# - Thành viên được mời phải đồng ý
# - Role/kênh cố định cho hệ thống kỷ luật
# - Kick / Ban / Unban / Timeout
# - Setup server tự động
# - Render health endpoint dùng PORT
# ============================================================

# -----------------------------
# ⚙️ CẤU HÌNH
# -----------------------------
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
DB_PATH = os.environ.get("DB_PATH", os.path.join("data", "study_data.db"))
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
PREFIX = "!"

# Tên role đặc quyền
OWNER_ROLE = "👑 Người Sáng Lập"
BQL_ROLE = "🛡️ Ban Quản Lý"

# Role / khu vực kỷ luật
DISCIPLINE_ROLE = "🔒 Đang Chấp Hành Kỷ Luật"
DISCIPLINE_CATEGORY = "🛡️ KHU VỰC KỶ LUẬT"
DISCIPLINE_CHANNEL = "📜・tự-thú-kỷ-luật"
DISCIPLINE_LOG_CHANNEL = "⚠️・kênh-kỷ-luật"

# Category phòng do thành viên tạo
ROOM_CATEGORY = "🎧 KHU PHÒNG TỰ TẠO"

# Học
STUDY_MINUTES_PER_CLOVER = 9
X2_MINUTES_PER_CLOVER = 4.5

# Camera
TOGGLE_LIMIT = 3
TOGGLE_WINDOW = 300

# -----------------------------
# 🌐 Render health endpoint
# -----------------------------
app = Flask(__name__)

@app.get("/")
def home():
    return "Bot Ong & Cỏ 4 Lá đang hoạt động! 🌸🐝🍀"

@app.get("/health")
def health():
    return {"status": "ok", "service": "discord-study-bot"}

def run_flask():
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_flask, daemon=True).start()

# -----------------------------
# 🤖 Discord
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Session trong RAM; DB vẫn là nguồn lịch sử.
user_cam_start = {}
user_subject_study = {}
camera_toggle_history = {}

# Phòng tạm / yêu cầu tham gia
pending_room_invites = {}
room_restore_tasks = {}

DEFAULT_SUBJECTS = [
    "Toán Học", "Vật Lý", "Hóa Học", "Ngữ Văn", "Tiếng Anh",
    "Sinh Học", "Lịch Sử", "Địa Lý", "Giáo Dục Công Dân",
    "Giáo Dục Địa Phương", "Kiến Thức Chuyên Ngành (Đại học)",
    "Kỹ Năng Mềm / Tiếng Anh Chuyên Ngành", "Tự do"
]

# ============================================================
# 🗄️ DATABASE
# ============================================================

def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_clovers (
            user_id INTEGER PRIMARY KEY,
            clovers INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_study (
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            subject TEXT NOT NULL,
            duration INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, date, subject)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subject_study (
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            duration INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, subject)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_study (
            user_id INTEGER PRIMARY KEY,
            total_time INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_inventory (
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, item_name)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subject_freq (
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, subject)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_streak (
            user_id INTEGER PRIMARY KEY,
            current_streak INTEGER NOT NULL DEFAULT 0,
            last_study_date TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            reminder_time TEXT NOT NULL,
            content TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_punishments (
            level TEXT PRIMARY KEY,
            clovers_deduct INTEGER NOT NULL DEFAULT 0,
            description TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_punishments (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            level TEXT NOT NULL,
            reason TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            PRIMARY KEY (guild_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS discipline_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            request_type TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            reviewer_id INTEGER,
            reviewer_note TEXT,
            created_at TEXT NOT NULL,
            reviewed_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS room_records (
            channel_id INTEGER PRIMARY KEY,
            guild_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            original_name TEXT NOT NULL,
            expires_at TEXT,
            privacy TEXT NOT NULL DEFAULT 'private',
            active INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS room_members (
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (channel_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bot_config (
            guild_id INTEGER PRIMARY KEY,
            discipline_category_id INTEGER,
            discipline_channel_id INTEGER,
            discipline_log_channel_id INTEGER,
            room_category_id INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gift_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            message TEXT,
            anonymous INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_x2 (
            user_id INTEGER PRIMARY KEY,
            expires_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_freeze (
            user_id INTEGER PRIMARY KEY,
            expires_date TEXT NOT NULL
        )
    """)

    defaults = [
        ("1", 5, "📝 Viết bản tường trình ngắn."),
        ("2", 10, "✍️ Viết bản kiểm điểm và cam kết không tái phạm."),
        ("3", 15, "🎥 Gửi bài thực hiện hình thức phạt theo nội quy."),
        ("4", 20, "🏋️ Hình thức phạt nâng cao + bản kiểm điểm.")
    ]
    cur.executemany("""
        INSERT OR IGNORE INTO dynamic_punishments(level, clovers_deduct, description)
        VALUES (?, ?, ?)
    """, defaults)

    conn.commit()
    conn.close()

init_db()

# ============================================================
# 🕐 TIME HELPERS
# ============================================================

def now_vn():
    return datetime.now(VN_TZ)

def iso_vn(dt=None):
    return (dt or now_vn()).isoformat()

def today_vn():
    return now_vn().date()

def date_key(d=None):
    return (d or today_vn()).isoformat()

def parse_vn_datetime(value):
    # DD/MM/YYYY HH:MM
    dt = datetime.strptime(value, "%d/%m/%Y %H:%M")
    return dt.replace(tzinfo=VN_TZ)

def format_duration(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h} giờ {m} phút {s} giây"
    if m:
        return f"{m} phút {s} giây"
    return f"{s} giây"

# ============================================================
# 🍀 CLOVER / INVENTORY
# ============================================================

def get_clovers(user_id):
    conn = db()
    row = conn.execute(
        "SELECT clovers FROM user_clovers WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return int(row[0]) if row else 0

def add_clovers(user_id, amount):
    conn = db()
    conn.execute("""
        INSERT INTO user_clovers(user_id, clovers)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET clovers = MAX(0, clovers + excluded.clovers)
    """, (user_id, amount))
    conn.commit()
    row = conn.execute(
        "SELECT clovers FROM user_clovers WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return int(row[0])

def add_item(user_id, item_name, amount=1):
    conn = db()
    conn.execute("""
        INSERT INTO user_inventory(user_id, item_name, amount)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, item_name)
        DO UPDATE SET amount = amount + excluded.amount
    """, (user_id, item_name, amount))
    conn.commit()
    conn.close()

def remove_item(user_id, item_name, amount=1):
    conn = db()
    row = conn.execute("""
        SELECT amount FROM user_inventory
        WHERE user_id = ? AND item_name = ?
    """, (user_id, item_name)).fetchone()
    if not row or row[0] < amount:
        conn.close()
        return False
    conn.execute("""
        UPDATE user_inventory SET amount = amount - ?
        WHERE user_id = ? AND item_name = ?
    """, (amount, user_id, item_name))
    conn.commit()
    conn.close()
    return True

def get_inventory(user_id):
    conn = db()
    rows = conn.execute("""
        SELECT item_name, amount
        FROM user_inventory
        WHERE user_id = ? AND amount > 0
        ORDER BY item_name
    """, (user_id,)).fetchall()
    conn.close()
    return rows

# ============================================================
# 📚 STUDY DATA
# ============================================================

def record_subject_choice(user_id, subject):
    conn = db()
    conn.execute("""
        INSERT INTO subject_freq(user_id, subject, count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, subject)
        DO UPDATE SET count = count + 1
    """, (user_id, subject))
    conn.commit()
    conn.close()

def get_sorted_subjects(user_id):
    conn = db()
    rows = conn.execute("""
        SELECT subject FROM subject_freq
        WHERE user_id = ? ORDER BY count DESC
    """, (user_id,)).fetchall()
    conn.close()

    result = [r[0] for r in rows]
    for sub in DEFAULT_SUBJECTS:
        if sub not in result:
            result.append(sub)
    return result

def add_study_time(user_id, subject, seconds):
    today = date_key()
    conn = db()
    conn.execute("""
        INSERT INTO daily_study(user_id, date, subject, duration)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, date, subject)
        DO UPDATE SET duration = duration + excluded.duration
    """, (user_id, today, subject, seconds))

    conn.execute("""
        INSERT INTO subject_study(user_id, subject, duration)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, subject)
        DO UPDATE SET duration = duration + excluded.duration
    """, (user_id, subject, seconds))

    conn.execute("""
        INSERT INTO user_study(user_id, total_time)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET total_time = total_time + excluded.total_time
    """, (user_id, seconds))

    conn.commit()
    conn.close()

def streak_update(user_id):
    today = today_vn()
    yesterday = today - timedelta(days=1)

    conn = db()
    row = conn.execute("""
        SELECT current_streak, last_study_date
        FROM user_streak WHERE user_id = ?
    """, (user_id,)).fetchone()

    if not row:
        streak = 1
    else:
        streak, last_str = row
        try:
            last = datetime.fromisoformat(last_str).date()
        except Exception:
            last = None

        if last == today:
            streak = int(streak)
        elif last == yesterday:
            streak = int(streak) + 1
        else:
            # Freeze chỉ bảo vệ một ngày nghỉ.
            freeze = conn.execute("""
                SELECT expires_date FROM active_freeze
                WHERE user_id = ?
            """, (user_id,)).fetchone()
            if freeze:
                try:
                    freeze_date = datetime.fromisoformat(freeze[0]).date()
                except Exception:
                    freeze_date = None
            else:
                freeze_date = None

            if freeze_date and freeze_date >= today:
                streak = int(streak)
                conn.execute("DELETE FROM active_freeze WHERE user_id = ?", (user_id,))
            else:
                streak = 1

    conn.execute("""
        INSERT INTO user_streak(user_id, current_streak, last_study_date)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET current_streak = excluded.current_streak,
                      last_study_date = excluded.last_study_date
    """, (user_id, streak, today.isoformat()))

    conn.commit()
    conn.close()
    return streak

def x2_active(user_id):
    conn = db()
    row = conn.execute(
        "SELECT expires_at FROM active_x2 WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    try:
        expires = datetime.fromisoformat(row[0])
        return now_vn() < expires
    except Exception:
        return False

def clovers_for_study(user_id, seconds):
    # Dựa đúng session study. Không làm tròn duration trước khi quy đổi.
    minutes = seconds / 60
    ratio = X2_MINUTES_PER_CLOVER if x2_active(user_id) else STUDY_MINUTES_PER_CLOVER
    return int(minutes // ratio)

def settle_study_session(member, channel, start_time, subject_name):
    duration = max(0, int(time.time() - start_time))
    add_study_time(member.id, subject_name, duration)
    earned = clovers_for_study(member.id, duration)
    if earned:
        add_clovers(member.id, earned)
    streak = streak_update(member.id)
    return duration, earned, streak

# ============================================================
# 🛒 SHOP
# ============================================================

SHOP_ITEMS = {
    "hopqua": {
        "name": "🎁 Hộp Quà Nhân Phẩm",
        "price": 50,
        "desc": "Mua xong mở ngay. Tỷ lệ thưởng được giữ bí mật."
    },
    "x2": {
        "name": "⚡ Thẻ X2 Năng Lượng",
        "price": 80,
        "desc": "Tích trữ. Dùng bằng !dung x2. Hiệu lực 2 giờ."
    },
    "giaman": {
        "name": "🛡️ Thẻ Giảm Án Kỷ Luật",
        "price": 150,
        "desc": "Tích trữ. Dùng để hạ mức phạt hiện tại 1 bậc."
    },
    "doiten": {
        "name": "👑 Thẻ Đổi Tên Phòng Học",
        "price": 120,
        "desc": "Tích trữ. Dùng để đổi tên Voice tạm thời, có thời hạn."
    },
    "gift": {
        "name": "🤝 Thẻ Tặng Quà",
        "price": 10,
        "desc": "Phí giao dịch. Dùng trực tiếp với !mua gift @Ong số_cỏ lời_nhắn."
    },
    "freeze": {
        "name": "❄️ Thẻ Đóng Băng Streak",
        "price": 100,
        "desc": "Tự động kích hoạt ngay khi nhận được."
    },
    "vephat": {
        "name": "🎫 Vé Miễn Phạt",
        "price": 200,
        "desc": "Tích trữ trong túi, dùng bằng !dung mienphat."
    }
}

def mystery_reward():
    roll = random.uniform(0, 100)
    if roll < 45:
        return {"type": "message", "text": "🌸 Chúc Ong học thật tốt, hôm nay chiến thắng chính mình nhé!"}
    if roll < 75:
        return {"type": "clover", "amount": random.randint(10, 30)}
    if roll < 90:
        return {"type": "clover", "amount": random.randint(31, 60)}
    if roll < 96:
        return {"type": "clover", "amount": random.randint(61, 100)}
    if roll < 99:
        return {"type": "item", "item": "🎫 Vé Miễn Phạt"}
    return {"type": "freeze"}

# ============================================================
# 👑 ROLE HELPERS
# ============================================================

def has_special_role(member):
    if member.guild_permissions.administrator:
        return True
    names = {r.name for r in member.roles}
    return OWNER_ROLE in names or BQL_ROLE in names

def is_owner_or_bql(member):
    return has_special_role(member)

async def require_special(ctx):
    if not ctx.guild or not is_owner_or_bql(ctx.author):
        await ctx.send("🔒 Lệnh này chỉ dành cho **Người Sáng Lập / Ban Quản Lý**.")
        return False
    return True

async def ensure_role(guild, name, color=None):
    role = discord.utils.get(guild.roles, name=name)
    if role:
        return role
    return await guild.create_role(
        name=name,
        color=color or discord.Color.default(),
        reason="Bot tự thiết lập hệ thống"
    )

# ============================================================
# 🏗️ FIXED SERVER SETUP
# ============================================================

async def ensure_fixed_channels(guild):
    owner = await ensure_role(guild, OWNER_ROLE, discord.Color.red())
    bql = await ensure_role(guild, BQL_ROLE, discord.Color.orange())
    discipline = await ensure_role(guild, DISCIPLINE_ROLE, discord.Color.dark_gray())

    category = discord.utils.get(guild.categories, name=DISCIPLINE_CATEGORY)
    if not category:
        category = await guild.create_category(DISCIPLINE_CATEGORY)

    bot_member = guild.me
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        discipline: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        bql: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        owner: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }
    if bot_member:
        overwrites[bot_member] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            attach_files=True, embed_links=True
        )

    confession = discord.utils.get(guild.text_channels, name=DISCIPLINE_CHANNEL)
    if not confession:
        confession = await guild.create_text_channel(
            DISCIPLINE_CHANNEL, category=category, overwrites=overwrites
        )

    log_overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        bql: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        owner: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
    }
    if bot_member:
        log_overwrites[bot_member] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            attach_files=True, embed_links=True
        )
    log_channel = discord.utils.get(guild.text_channels, name=DISCIPLINE_LOG_CHANNEL)
    if not log_channel:
        log_channel = await guild.create_text_channel(
            DISCIPLINE_LOG_CHANNEL, category=category, overwrites=log_overwrites
        )

    room_cat = discord.utils.get(guild.categories, name=ROOM_CATEGORY)
    if not room_cat:
        room_cat = await guild.create_category(ROOM_CATEGORY)

    conn = db()
    conn.execute("""
        INSERT INTO bot_config(
            guild_id, discipline_category_id, discipline_channel_id,
            discipline_log_channel_id, room_category_id
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            discipline_category_id=excluded.discipline_category_id,
            discipline_channel_id=excluded.discipline_channel_id,
            discipline_log_channel_id=excluded.discipline_log_channel_id,
            room_category_id=excluded.room_category_id
    """, (guild.id, category.id, confession.id, log_channel.id, room_cat.id))
    conn.commit()
    conn.close()

    return owner, bql, discipline, confession, log_channel, room_cat

