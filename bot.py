import os
import time
import random
import sqlite3
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from discord.ui import View, Select, Modal, TextInput

# --- 🌐 SERVER KEEP-ALIVE RENDER 24/7 ---
app = Flask('')
@app.route('/')
def home():
    return "Bot Ong & Cỏ 4 Lá đang hoạt động! 🌸🐝🍀"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- CẤU HÌNH BOT DISCORD ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

user_cam_start = {}
user_subject_study = {}
BQL_ROLES = ["Chủ Server", "Quản Trị Viên"]

# Danh sách môn học mặc định ban đầu
DEFAULT_SUBJECTS = [
    "Toán Học", "Vật Lý", "Hóa Học", "Ngữ Văn", "Tiếng Anh",
    "Sinh Học", "Lịch Sử", "Địa Lý", "Giáo Dục Công Dân",
    "Giáo Dục Địa Phương", "Kiến Thức Chuyên Ngành (Đại học)",
    "Kỹ Năng Mềm / Tiếng Anh Chuyên Ngành", "Tự do"
]

# ============================================================
# 📦 MYSTERY GACHA BOX - HỘP QUÀ NHÂN PHẨM
# ============================================================

import random


# ============================================================
# 🛒 DỮ LIỆU CỬA HÀNG
# ============================================================

SHOP_ITEMS = {
    "1": {
        "name": "❄️ Thẻ Đóng Băng Streak",
        "price": 100,
        "desc": "Bảo toàn chuỗi học tập liên tục của bạn khi nghỉ 1 ngày."
    },

    "gacha": {
        "name": "📦 Hộp Quà Nhân Phẩm",
        "price": 50,
        "desc": "🎲 Mở ngay để nhận một phần thưởng ngẫu nhiên. Nhân phẩm quyết định tất cả!"
    }
}


# ============================================================
# 🎲 BẢNG PHẦN THƯỞNG GACHA
# ============================================================
#
# TỶ LỆ KHÔNG HIỂN THỊ CHO THÀNH VIÊN
#
# 🌸 Lời chúc:              45%
# 🍀 10-30 Cỏ:              30%
# 🍀 31-60 Cỏ:              15%
# 🍀 61-100 Cỏ:               6%
# 🎫 Vé Miễn Phạt:            3%
# ❄️ Thẻ Đóng Băng Streak:    1%
#
# Tổng = 100%
# ============================================================


def open_mystery_gacha():

    roll = random.uniform(
        0,
        100
    )

    # ========================================================
    # 🌸 45% - LỜI CHÚC
    # ========================================================

    if roll < 45:

        return {
            "type": "message",
            "title": "🌸 NHÂN PHẨM HƠI ĐAU...",
            "description": (
                "Ong mở hộp ra...\n\n"
                "📦✨ *Phụt!*\n\n"
                "🌸 **Chúc Ong học tập thật tốt nhé!**\n"
                "Nhưng hôm nay chưa có phần thưởng vật chất nào cả. 😭\n\n"
                "💪 Đừng buồn, biết đâu hộp tiếp theo "
                "lại là hàng cực phẩm!"
            )
        }


    # ========================================================
    # 🍀 30% - 10 ĐẾN 30 CỎ
    # ========================================================

    elif roll < 75:

        clovers = random.randint(
            10,
            30
        )

        return {
            "type": "clover",
            "amount": clovers,
            "title": "🍀 NHẶT ĐƯỢC CỎ 4 LÁ!",
            "description": (
                f"✨ Nhân phẩm hôm nay cũng khá ổn!\n\n"
                f"🍀 **+{clovers} Cỏ 4 Lá**"
            )
        }


    # ========================================================
    # 🍀 15% - 31 ĐẾN 60 CỎ
    # ========================================================

    elif roll < 90:

        clovers = random.randint(
            31,
            60
        )

        return {
            "type": "clover",
            "amount": clovers,
            "title": "💚 NHÂN PHẨM KHÁ TỐT!",
            "description": (
                f"🎉 Hộp quà phát sáng!\n\n"
                f"🍀 **+{clovers} Cỏ 4 Lá**\n\n"
                f"🔥 Hôm nay Ong có vẻ được "
                f"vũ trụ phù hộ rồi!"
            )
        }


    # ========================================================
    # 🍀 6% - 61 ĐẾN 100 CỎ
    # ========================================================

    elif roll < 96:

        clovers = random.randint(
            61,
            100
        )

        return {
            "type": "clover",
            "amount": clovers,
            "title": "💎 ĐẠI PHÁT TÀI!",
            "description": (
                f"🎲 **NHÂN PHẨM BÙNG NỔ!**\n\n"
                f"🍀 **+{clovers} Cỏ 4 Lá**\n\n"
                f"👑 Một trong những phần thưởng "
                f"hiếm của Hộp Quà Nhân Phẩm!"
            )
        }


    # ========================================================
    # 🎫 3% - VÉ MIỄN PHẠT
    # ========================================================

    elif roll < 99:

        return {
            "type": "item",
            "item_name": "🎫 Vé Miễn Phạt",
            "title": "🎫 NHẬN ĐƯỢC VÉ MIỄN PHẠT!",
            "description": (
                "😳 **NHÂN PHẨM TỐT!**\n\n"
                "Bạn đã nhận được:\n"
                "🎫 **Vé Miễn Phạt**\n\n"
                "📦 Vật phẩm đã được đưa thẳng "
                "vào **🎒 Túi đồ** của bạn."
            )
        }


    # ========================================================
    # ❄️ 1% - THẺ ĐÓNG BĂNG STREAK
    # ========================================================

    else:

        return {
            "type": "item",
            "item_name": "❄️ Thẻ Đóng Băng Streak",
            "title": "❄️ NHÂN PHẨM CỰC PHẨM!!!",
            "description": (
                "🌟🌟🌟 **1% NHÂN PHẨM!** 🌟🌟🌟\n\n"
                "😱 Ong vừa mở được:\n"
                "❄️ **Thẻ Đóng Băng Streak**\n\n"
                "📦 Vật phẩm đã được đưa thẳng "
                "vào **🎒 Túi đồ** của bạn.\n\n"
                "🔥 Đây là một trong những phần thưởng "
                "hiếm nhất của Hộp Quà Nhân Phẩm!"
            )
        }


# ============================================================
# 🛒 LỆNH MUA HÀNG
# ============================================================

@bot.command()
async def mua(ctx, code: str):

    user_id = ctx.author.id

    code = code.lower().strip()


    # ========================================================
    # ❌ KIỂM TRA MÃ SẢN PHẨM
    # ========================================================

    if code not in SHOP_ITEMS:

        await ctx.send(
            "⚠️ **Mã món hàng không tồn tại!**\n\n"
            "🛒 Gõ `!shop` để xem danh sách "
            "các món hàng hiện có."
        )

        return


    item = SHOP_ITEMS[code]

    price = item["price"]

    current_clovers = get_clovers(
        user_id
    )


    # ========================================================
    # 💰 KIỂM TRA SỐ DƯ
    # ========================================================

    if current_clovers < price:

        await ctx.send(
            f"❌ {ctx.author.mention} **không đủ Cỏ 4 Lá!**\n\n"
            f"🍀 Bạn đang có: **{current_clovers} Cỏ**\n"
            f"💰 Cần: **{price} Cỏ**\n"
            f"📉 Thiếu: **{price - current_clovers} Cỏ**"
        )

        return


    # ========================================================
    # 📦 MYSTERY GACHA
    # ========================================================

    if code == "gacha":

        # ----------------------------------------------------
        # Trừ tiền trước khi mở hộp
        # ----------------------------------------------------

        add_clovers(
            user_id,
            -price
        )


        # ----------------------------------------------------
        # 🎲 RANDOM PHẦN THƯỞNG
        # ----------------------------------------------------

        reward = open_mystery_gacha()


        # ====================================================
        # 🌸 TRƯỜNG HỢP LỜI CHÚC
        # ====================================================

        if reward["type"] == "message":

            embed = discord.Embed(
                title=reward["title"],
                description=(
                    f"{ctx.author.mention}\n\n"
                    f"{reward['description']}\n\n"
                    f"💸 **Đã sử dụng:** "
                    f"50 🍀"
                ),
                color=discord.Color.light_grey()
            )


        # ====================================================
        # 🍀 TRƯỜNG HỢP TRÚNG CỎ
        # ====================================================

        elif reward["type"] == "clover":

            add_clovers(
                user_id,
                reward["amount"]
            )

            new_balance = get_clovers(
                user_id
            )

            embed = discord.Embed(
                title=reward["title"],
                description=(
                    f"{ctx.author.mention}\n\n"
                    f"{reward['description']}\n\n"
                    f"💸 **Giá hộp:** -50 🍀\n"
                    f"💰 **Số dư hiện tại:** "
                    f"**{new_balance} 🍀**"
                ),
                color=discord.Color.green()
            )


        # ====================================================
        # 🎫 / ❄️ TRƯỜNG HỢP TRÚNG VẬT PHẨM
        # ====================================================

        elif reward["type"] == "item":

            add_item_to_inventory(
                user_id,
                reward["item_name"],
                1
            )

            embed = discord.Embed(
                title=reward["title"],
                description=(
                    f"{ctx.author.mention}\n\n"
                    f"{reward['description']}\n\n"
                    f"💸 **Giá hộp:** -50 🍀\n"
                    f"🎒 Kiểm tra vật phẩm bằng "
                    f"`!tuido`"
                ),
                color=discord.Color.gold()
            )


        # ====================================================
        # 🎲 HIỂN THỊ KẾT QUẢ
        # ====================================================

        embed.set_footer(
            text=(
                "📦 Mystery Gacha Box • "
                "Nhân phẩm quyết định tất cả 🎲"
            )
        )

        await ctx.send(
            embed=embed
        )

        return


    # ========================================================
    # 🛍️ MUA VẬT PHẨM THÔNG THƯỜNG
    # ========================================================

    add_clovers(
        user_id,
        -price
    )

    add_item_to_inventory(
        user_id,
        item["name"],
        1
    )

    await ctx.send(
        f"🎉 Chúc mừng {ctx.author.mention} "
        f"đã mua thành công **{item['name']}**!\n\n"
        f"💸 Đã trừ: **-{price} 🍀**\n"
        f"🎒 Vật phẩm đã được đưa vào túi đồ.\n\n"
        f"📦 Kiểm tra bằng lệnh `!tuido` nhé! "
        f"(๑•̀ㅂ•́)و✧"
    )


# --- DATABASE TỔNG HỢP ---
def init_db():
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE IF NOT EXISTS user_clovers (user_id INTEGER PRIMARY KEY, clovers INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS daily_study (user_id INTEGER, date TEXT, subject TEXT, duration INTEGER, PRIMARY KEY (user_id, date, subject))")
    cursor.execute("CREATE TABLE IF NOT EXISTS subject_study (user_id INTEGER, subject TEXT, duration INTEGER DEFAULT 0, PRIMARY KEY (user_id, subject))")
    cursor.execute("CREATE TABLE IF NOT EXISTS user_study (user_id INTEGER PRIMARY KEY, total_time INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS quiz_limits (user_id INTEGER, date TEXT, attempts INTEGER DEFAULT 0, PRIMARY KEY (user_id, date))")
    cursor.execute("CREATE TABLE IF NOT EXISTS user_inventory (user_id INTEGER, item_name TEXT, amount INTEGER DEFAULT 0, PRIMARY KEY (user_id, item_name))")
    cursor.execute("CREATE TABLE IF NOT EXISTS subject_freq (user_id INTEGER, subject TEXT, count INTEGER DEFAULT 0, PRIMARY KEY (user_id, subject))")
    cursor.execute("CREATE TABLE IF NOT EXISTS dynamic_punishments (level TEXT PRIMARY KEY, clovers_deduct INTEGER DEFAULT 0, description TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS user_streak (user_id INTEGER PRIMARY KEY, current_streak INTEGER DEFAULT 0, last_study_date TEXT)")
    
    cursor.execute("SELECT COUNT(*) FROM dynamic_punishments")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ("1", 5, "📝 **Viết bản tường trình:** Giải thích lý do AFK / Vi phạm ngắn hạn."),
            ("2", 10, "✍️ **Viết bản kiểm điểm:** Trình bày lỗi sai và cam kết không tái phạm."),
            ("3", 15, "🏃‍♀️ **Phạt thể lực nhẹ:** Quay video nhảy dây 20 cái, gửi lên kênh kỷ luật."),
            ("4", 20, "🏋️‍♀️ **Phạt thể lực nặng:** Quay video nhảy dây 50 cái + Viết bản kiểm điểm nghiêm túc.")
        ]
        cursor.executemany("INSERT INTO dynamic_punishments VALUES (?, ?, ?)", defaults)
    
    conn.commit()
    conn.close()

init_db()

# --- HÀM HỖ TRỢ ---
def is_bql(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    user_roles = [r.name for r in ctx.author.roles]
    return any(role in user_roles for role in BQL_ROLES)

def add_clovers(user_id, amount):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_clovers (user_id, clovers) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET clovers = clovers + ?", (user_id, amount, amount))
    conn.commit()
    conn.close()

def get_clovers(user_id):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT clovers FROM user_clovers WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def record_subject_choice(user_id, subject):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subject_freq (user_id, subject, count) VALUES (?, ?, 1) ON CONFLICT(user_id, subject) DO UPDATE SET count = count + 1", (user_id, subject))
    conn.commit()
    conn.close()

def get_sorted_subjects(user_id):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT subject FROM subject_freq WHERE user_id = ? ORDER BY count DESC", (user_id,))
    frequent = [row[0] for row in cursor.fetchall()]
    conn.close()

    sorted_list = []
    for sub in frequent:
        if sub not in sorted_list:
            sorted_list.append(sub)
    for sub in DEFAULT_SUBJECTS:
        if sub not in sorted_list:
            sorted_list.append(sub)
    return sorted_list

def add_study_time(user_id, subject, seconds):
    today = datetime.now().strftime("%d/%m/%Y")
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO daily_study (user_id, date, subject, duration) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, date, subject) DO UPDATE SET duration = duration + ?", (user_id, today, subject, seconds, seconds))
    cursor.execute("INSERT INTO user_study (user_id, total_time) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET total_time = total_time + ?", (user_id, seconds, seconds))
    if subject:
        cursor.execute("INSERT INTO subject_study (user_id, subject, duration) VALUES (?, ?, ?) ON CONFLICT(user_id, subject) DO UPDATE SET duration = duration + ?", (user_id, subject, seconds, seconds))
    conn.commit()
    conn.close()

def add_item_to_inventory(user_id, item_name, amount=1):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_inventory (user_id, item_name, amount) VALUES (?, ?, ?) ON CONFLICT(user_id, item_name) DO UPDATE SET amount = amount + ?", (user_id, item_name, amount, amount))
    conn.commit()
    conn.close()

# --- MODAL & MENU CHỌN MÔN HỌC ---
class CustomSubjectModal(Modal, title="✍️ Nhập Môn Học Mới"):
    custom_sub = TextInput(label="Tên môn học của bạn:", placeholder="Ví dụ: Triết học, Giải tích...", min_length=1, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        chosen = self.custom_sub.value.strip()
        user_subject_study[interaction.user.id] = {"subject": chosen, "start_time": time.time()}
        record_subject_choice(interaction.user.id, chosen)
        await interaction.response.send_message(f"🎯 Đã chọn môn: **{chosen}**. Cùng tập trung học nào! 🌸✨ (๑•̀ㅂ•́)و✧", ephemeral=True)

class SubjectSelect(Select):
    def __init__(self, user_id):
        sorted_subjects = get_sorted_subjects(user_id)
        options = []
        for idx, sub in enumerate(sorted_subjects[:23]):
            prefix = "⭐ " if idx < 3 and sub != "Tự do" else "📚 "
            if sub == "Tự do": prefix = "🎨 "
            options.append(discord.SelectOption(label=sub, value=sub, emoji=prefix.strip()))
        options.append(discord.SelectOption(label="➕ Tự thêm môn khác...", value="CUSTOM_SUBJECT", emoji="✍️"))
        super().__init__(placeholder="👉 Bấm vào đây để chọn môn học của bạn...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        chosen = self.values[0]
        if chosen == "CUSTOM_SUBJECT":
            await interaction.response.send_modal(CustomSubjectModal())
        else:
            user_subject_study[interaction.user.id] = {"subject": chosen, "start_time": time.time()}
            record_subject_choice(interaction.user.id, chosen)
            await interaction.response.send_message(f"✅ Đã lưu môn học: **{chosen}**! Chúc bạn học tốt nhé! ⏱️🔥 ( •̀ ω •́ )✧", ephemeral=True)

class SubjectSelectView(View):
    def __init__(self, user_id, timeout=120):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.add_item(SubjectSelect(user_id))

# ============================================================
# 🌸 HỆ THỐNG VOICE HỌC TẬP
# - Không tự tạo phòng
# - Không tự xóa phòng
# - Vào phòng -> chào trong Voice Chat
# - Bật camera -> bắt đầu học
# - Tắt camera -> kết thúc học ngay
# - Rời phòng khi đang bật camera -> kết thúc học
# - 9 phút = 1 Cỏ 4 Lá
# - Tính Streak
# - Bật/tắt camera 3 lần trong 5 phút -> cảnh báo
# - Cảnh báo -> tag BQL + Chủ Server tại kênh kỷ luật
# - Không tự động xử phạt
# ============================================================


# ============================================================
# 📦 BIẾN HỆ THỐNG
# ============================================================

user_cam_start = {}
user_subject_study = {}
camera_toggle_history = {}

# 3 lần bật/tắt trong 5 phút -> cảnh báo
TOGGLE_LIMIT = 3
TOGGLE_WINDOW = 300


# ============================================================
# 📢 GỬI CẢNH BÁO CHO BQL + CHỦ SERVER
# ============================================================

async def alert_camera_violation(
    member,
    voice_channel,
    toggle_count
):

    guild = member.guild

    # Role Quản Trị Viên
    role_bql = discord.utils.get(
        guild.roles,
        name="🛡️ Quản Trị Viên (BQL)"
    )

    # Role Chủ Server
    role_owner = discord.utils.get(
        guild.roles,
        name="👑 Chủ Server"
    )

    # Kênh kỷ luật
    ky_luat_chan = discord.utils.get(
        guild.text_channels,
        name="⚠️·kênh-kỷ-luật"
    )

    if not ky_luat_chan:
        print(
            "⚠️ Không tìm thấy kênh "
            "⚠️·kênh-kỷ-luật"
        )
        return

    # Tạo danh sách role cần tag
    mentions = []

    if role_bql:
        mentions.append(
            role_bql.mention
        )

    if role_owner:
        mentions.append(
            role_owner.mention
        )

    role_mentions = " ".join(
        mentions
    )

    channel_name = (
        voice_channel.name
        if voice_channel
        else "Không xác định"
    )

    # Embed cảnh báo
    embed = discord.Embed(
        title="🚨 CẢNH BÁO HÀNH VI CAMERA BẤT THƯỜNG",
        description=(
            f"⚠️ Hệ thống phát hiện thành viên "
            f"có hành vi **bật/tắt camera liên tục**.\n\n"

            f"👤 **Thành viên:** "
            f"{member.mention}\n"

            f"🎧 **Phòng học:** "
            f"`{channel_name}`\n"

            f"🔄 **Số lần ghi nhận:** "
            f"`{toggle_count}` lần\n"

            f"⏱️ **Khoảng thời gian:** "
            f"`5 phút`\n\n"

            f"📌 **Trạng thái:** "
            f"Chưa tự động xử phạt.\n\n"

            f"🛡️ BQL vui lòng kiểm tra và quyết định "
            f"hình thức xử lý nếu cần."
        ),
        color=discord.Color.red()
    )

    embed.set_footer(
        text=(
            "Hệ thống giám sát học tập "
            "• Cảnh báo tự động"
        )
    )

    await ky_luat_chan.send(
        content=role_mentions,
        embed=embed,
        allowed_mentions=discord.AllowedMentions(
            roles=True,
            users=True
        )
    )


# ============================================================
# 🔄 GHI NHẬN BẬT/TẮT CAMERA
# ============================================================

def record_camera_toggle(member_id):

    now = time.time()

    if member_id not in camera_toggle_history:
        camera_toggle_history[member_id] = []

    # Chỉ giữ những lần xảy ra trong 5 phút
    camera_toggle_history[member_id] = [
        timestamp
        for timestamp in camera_toggle_history[member_id]
        if now - timestamp <= TOGGLE_WINDOW
    ]

    camera_toggle_history[member_id].append(
        now
    )

    return len(
        camera_toggle_history[member_id]
    )


# ============================================================
# 🎧 GỬI TIN NHẮN VÀO CHAT CỦA VOICE CHANNEL
# ============================================================

async def send_voice_chat(
    channel,
    content=None,
    embed=None,
    view=None,
    delete_after=None
):

    if channel is None:
        return None

    try:

        # Voice Channel hỗ trợ send()
        if hasattr(channel, "send"):

            return await channel.send(
                content=content,
                embed=embed,
                view=view,
                delete_after=delete_after
            )

    except Exception as e:

        print(
            f"[VOICE CHAT ERROR] "
            f"{channel.name}: {e}"
        )

    return None


# ============================================================
# 🎧 THEO DÕI VOICE STATE
# ============================================================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    # ========================================================
    # 1️⃣ THÀNH VIÊN VÀO VOICE
    # ========================================================

    if (
        before.channel is None
        and after.channel is not None
    ):

        voice_channel = after.channel

        embed_welcome = discord.Embed(
            title=(
                "✨ CHÀO MỪNG BẠN ĐÃ ĐẾN "
                "VỚI GÓC HỌC TẬP! ✨"
            ),

            description=(
                f"Chào mừng {member.mention} "
                f"đã vào phòng voice "
                f"**{voice_channel.name}**! 🌸🐝\n\n"

                f"*Chúc Ong có một buổi học tập "
                f"thật năng suất, tập trung "
                f"và đạt kết quả cao nha!* "
                f"( •̀ ω •́ )✧\n\n"

                f"💡 *Gợi ý:* Hãy bật camera "
                f"để tích lũy thời gian học, "
                f"đổi Cỏ 4 Lá 🍀 và duy trì "
                f"chuỗi học tập nhé!"
            ),

            color=discord.Color.gold()
        )

        await send_voice_chat(
            voice_channel,
            content=member.mention,
            embed=embed_welcome,
            delete_after=60
        )


    # ========================================================
    # 2️⃣ BẬT CAMERA
    # ========================================================

    if (
        not before.self_video
        and after.self_video
        and after.channel
    ):

        # Không tạo phiên thứ hai
        if member.id not in user_cam_start:

            now = time.time()

            user_cam_start[
                member.id
            ] = now

            user_subject_study[
                member.id
            ] = {
                "subject": "Tự do",
                "start_time": now,
                "channel_id": after.channel.id
            }

            # Ghi nhận bật camera
            toggle_count = record_camera_toggle(
                member.id
            )

            embed_start = discord.Embed(
                title=(
                    "🎉 BẮT ĐẦU TÍCH LŨY "
                    "GIỜ HỌC! 🎉"
                ),

                description=(
                    f"{member.mention} đã bật "
                    f"camera học cùng mọi người "
                    f"rồi nè! 🌸✨\n\n"

                    f"👉 **Hãy chọn môn học "
                    f"bên dưới bảng tương tác nhé!**"
                ),

                color=discord.Color.green()
            )

            view = SubjectSelectView(
                member.id
            )

            await send_voice_chat(
                after.channel,
                content=member.mention,
                embed=embed_start,
                view=view,
                delete_after=120
            )

            # ------------------------------------------------
            # 🚨 CẢNH BÁO NẾU BẬT/TẮT QUÁ NHIỀU
            # ------------------------------------------------

            if toggle_count >= TOGGLE_LIMIT:

                await alert_camera_violation(
                    member,
                    after.channel,
                    toggle_count
                )

                warning_embed = discord.Embed(
                    title="⚠️ CẢNH BÁO CAMERA",

                    description=(
                        f"{member.mention}, hệ thống "
                        f"ghi nhận bạn đã bật/tắt camera "
                        f"**{toggle_count} lần trong 5 phút "
                        f"gần đây**.\n\n"

                        f"📌 Vui lòng hạn chế bật/tắt "
                        f"camera liên tục để thời gian "
                        f"học được ghi nhận chính xác.\n\n"

                        f"🛡️ BQL và Chủ Server "
                        f"đã được thông báo.\n\n"

                        f"📌 Bot **không tự động trừ Cỏ "
                        f"hoặc xử phạt**."
                    ),

                    color=discord.Color.orange()
                )

                await send_voice_chat(
                    after.channel,
                    embed=warning_embed
                )


    # ========================================================
    # 3️⃣ TẮT CAMERA
    # → KẾT THÚC PHIÊN HỌC NGAY
    # ========================================================

    if (
        before.self_video
        and not after.self_video
        and member.id in user_cam_start
    ):

        start_t = user_cam_start.pop(
            member.id
        )

        duration = int(
            time.time() - start_t
        )

        duration_minutes = (
            duration // 60
        )

        hours = duration // 3600

        minutes = (
            duration % 3600
        ) // 60

        seconds = duration % 60

        subject_info = user_subject_study.pop(
            member.id,
            {"subject": "Tự do"}
        )

        subject_name = subject_info.get(
            "subject",
            "Tự do"
        )

        study_channel = (
            before.channel
            or after.channel
        )


        # ====================================================
        # 📚 LƯU GIỜ HỌC
        # ====================================================

        add_study_time(
            member.id,
            subject_name,
            duration
        )


        # ====================================================
        # 🍀 QUY ĐỔI CỎ
        # 9 PHÚT = 1 CỎ
        # ====================================================

        earned_clovers = (
            duration_minutes // 9
        )

        if earned_clovers > 0:

            add_clovers(
                member.id,
                earned_clovers
            )


        # ====================================================
        # 🔥 TÍNH STREAK
        # ====================================================

        today_str = datetime.now().strftime(
            "%d/%m/%Y"
        )

        yesterday_str = (
            datetime.now()
            - timedelta(days=1)
        ).strftime(
            "%d/%m/%Y"
        )

        conn = sqlite3.connect(
            "study_data.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT current_streak, last_study_date
            FROM user_streak
            WHERE user_id = ?
            """,
            (member.id,)
        )

        streak_row = cursor.fetchone()

        current_streak = 1

        if streak_row:

            last_date = streak_row[1]

            if last_date == today_str:

                current_streak = streak_row[0]

            elif last_date == yesterday_str:

                current_streak = (
                    streak_row[0] + 1
                )

            else:

                current_streak = 1

            cursor.execute(
                """
                UPDATE user_streak
                SET current_streak = ?,
                    last_study_date = ?
                WHERE user_id = ?
                """,
                (
                    current_streak,
                    today_str,
                    member.id
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO user_streak
                (
                    user_id,
                    current_streak,
                    last_study_date
                )
                VALUES (?, ?, ?)
                """,
                (
                    member.id,
                    1,
                    today_str
                )
            )

        conn.commit()
        conn.close()


        # ====================================================
        # ⏱️ HIỂN THỊ THỜI GIAN
        # ====================================================

        time_str = ""

        if hours > 0:

            time_str += (
                f"{hours} giờ "
            )

        if minutes > 0 or hours > 0:

            time_str += (
                f"{minutes} phút "
            )

        time_str += (
            f"{seconds} giây"
        )


        # ====================================================
        # 👋 TẠM BIỆT
        # ====================================================

        msg = (
            f"👋 Tạm biệt {member.mention}! "
            f"Cảm ơn bạn vì đã nỗ lực hết mình "
            f"hôm nay. **Chúc bạn nghỉ ngơi thật "
            f"thoải mái và nạp lại năng lượng nhé!** "
            f"🌸✨ ( ˘ ³˘)♥\n\n"

            f"📚 **Môn học đã học:** "
            f"{subject_name}\n"

            f"⏱️ **Thời gian tập trung:** "
            f"**{time_str}**\n"

            f"🔥 **Chuỗi học tập hiện tại:** "
            f"**{current_streak} ngày liên tiếp**!"
        )

        if earned_clovers > 0:

            msg += (
                f"\n🍀 **Quy đổi (Mốc 1:9):** "
                f"Nhận được **+{earned_clovers} "
                f"Cỏ 4 Lá**!"
            )

        if study_channel:

            await send_voice_chat(
                study_channel,
                content=msg
            )


        # ====================================================
        # 🚨 KIỂM TRA BẬT/TẮT CAMERA LIÊN TỤC
        # ====================================================

        toggle_count = record_camera_toggle(
            member.id
        )

        if toggle_count >= TOGGLE_LIMIT:

            await alert_camera_violation(
                member,
                study_channel,
                toggle_count
            )

            warning_embed = discord.Embed(
                title="⚠️ CẢNH BÁO CAMERA",

                description=(
                    f"{member.mention}, hệ thống ghi nhận "
                    f"**{toggle_count} lần bật/tắt camera "
                    f"trong 5 phút**.\n\n"

                    f"🛡️ BQL và Chủ Server đã được "
                    f"thông báo tại kênh kỷ luật.\n\n"

                    f"📌 Bot **không tự động xử phạt**. "
                    f"BQL sẽ xem xét nếu cần."
                ),

                color=discord.Color.orange()
            )

            await send_voice_chat(
                study_channel,
                embed=warning_embed
            )


    # ========================================================
    # 4️⃣ RỜI VOICE KHI CAMERA VẪN ĐANG BẬT
    # ========================================================

    if (
        before.channel
        and after.channel is None
        and member.id in user_cam_start
    ):

        start_t = user_cam_start.pop(
            member.id
        )

        duration = int(
            time.time() - start_t
        )

        duration_minutes = (
            duration // 60
        )

        hours = duration // 3600

        minutes = (
            duration % 3600
        ) // 60

        seconds = duration % 60

        subject_info = user_subject_study.pop(
            member.id,
            {"subject": "Tự do"}
        )

        subject_name = subject_info.get(
            "subject",
            "Tự do"
        )

        study_channel = before.channel


        # ====================================================
        # 📚 LƯU GIỜ HỌC
        # ====================================================

        add_study_time(
            member.id,
            subject_name,
            duration
        )


        # ====================================================
        # 🍀 QUY ĐỔI CỎ
        # ====================================================

        earned_clovers = (
            duration_minutes // 9
        )

        if earned_clovers > 0:

            add_clovers(
                member.id,
                earned_clovers
            )


        # ====================================================
        # 🔥 TÍNH STREAK
        # ====================================================

        today_str = datetime.now().strftime(
            "%d/%m/%Y"
        )

        yesterday_str = (
            datetime.now()
            - timedelta(days=1)
        ).strftime(
            "%d/%m/%Y"
        )

        conn = sqlite3.connect(
            "study_data.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT current_streak, last_study_date
            FROM user_streak
            WHERE user_id = ?
            """,
            (member.id,)
        )

        streak_row = cursor.fetchone()

        current_streak = 1

        if streak_row:

            last_date = streak_row[1]

            if last_date == today_str:

                current_streak = streak_row[0]

            elif last_date == yesterday_str:

                current_streak = (
                    streak_row[0] + 1
                )

            else:

                current_streak = 1

            cursor.execute(
                """
                UPDATE user_streak
                SET current_streak = ?,
                    last_study_date = ?
                WHERE user_id = ?
                """,
                (
                    current_streak,
                    today_str,
                    member.id
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO user_streak
                (
                    user_id,
                    current_streak,
                    last_study_date
                )
                VALUES (?, ?, ?)
                """,
                (
                    member.id,
                    1,
                    today_str
                )
            )

        conn.commit()
        conn.close()


        # ====================================================
        # ⏱️ FORMAT THỜI GIAN
        # ====================================================

        time_str = ""

        if hours > 0:

            time_str += (
                f"{hours} giờ "
            )

        if minutes > 0 or hours > 0:

            time_str += (
                f"{minutes} phút "
            )

        time_str += (
            f"{seconds} giây"
        )


        # ====================================================
        # 👋 TẠM BIỆT KHI RỜI PHÒNG
        # ====================================================

        msg = (
            f"👋 Tạm biệt {member.mention}! "
            f"Cảm ơn bạn vì đã nỗ lực hết mình "
            f"hôm nay. 🌸✨\n\n"

            f"📚 **Môn học đã học:** "
            f"{subject_name}\n"

            f"⏱️ **Thời gian tập trung:** "
            f"**{time_str}**\n"

            f"🔥 **Chuỗi học tập hiện tại:** "
            f"**{current_streak} ngày liên tiếp**!"
        )

        if earned_clovers > 0:

            msg += (
                f"\n🍀 **Quy đổi (Mốc 1:9):** "
                f"Nhận được **+{earned_clovers} "
                f"Cỏ 4 Lá**!"
            )

        await send_voice_chat(
            study_channel,
            content=msg
        )

# --- 📊 HỆ THỐNG BÁO CÁO HỌC TẬP LINH HOẠT ---
@bot.command()
async def baocao(ctx, mode: str = "ngay", *, target: str = None):
    user_id = ctx.author.id
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()

    today_str = datetime.now().strftime("%d/%m/%Y")
    current_month = datetime.now().strftime("/%m/%Y")
    current_year = datetime.now().strftime("%Y")

    embed = discord.Embed(title=f"📊 BÁO CÁO HỌC TẬP CỦA {ctx.author.display_name.upper()}", color=discord.Color.teal())

    if mode == "ngay":
        cursor.execute("SELECT subject, duration FROM daily_study WHERE user_id = ? AND date = ?", (user_id, today_str))
        rows = cursor.fetchall()
        total_sec = sum(r[1] for r in rows)
        h, m, s = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
        desc = f"📅 **Ngày:** {today_str}\n⏱️ **Tổng thời gian:** {h}h {m}m {s}s\n\n"
        for sub, dur in rows:
            sh, sm = dur // 3600, (dur % 3600) // 60
            desc += f"• **{sub}**: {sh}h {sm}m\n"
        embed.description = desc

    elif mode == "tuan":
        cursor.execute("SELECT date, subject, duration FROM daily_study WHERE user_id = ? ORDER BY rowid DESC LIMIT 30", (user_id,))
        rows = cursor.fetchall()
        total_sec = sum(r[2] for r in rows)
        h, m, _ = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
        embed.description = f"📅 **Báo cáo Tuần (7 ngày gần nhất)**\n⏱️ **Tổng thời gian:** {h}h {m}m\n\n"
        sub_dict = {}
        for _, sub, dur in rows:
            sub_dict[sub] = sub_dict.get(sub, 0) + dur
        for sub, dur in sub_dict.items():
            sh, sm = dur // 3600, (dur % 3600) // 60
            embed.add_field(name=sub, value=f"{sh}h {sm}m", inline=True)

    elif mode == "thang":
        cursor.execute("SELECT subject, duration FROM daily_study WHERE user_id = ? AND date LIKE ?", (user_id, f"%{current_month}%"))
        rows = cursor.fetchall()
        total_sec = sum(r[1] for r in rows)
        h, m, _ = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
        embed.description = f"📅 **Tháng:** {datetime.now().strftime('%m/%Y')}\n⏱️ **Tổng thời gian:** {h}h {m}m\n\n"
        sub_dict = {}
        for sub, dur in rows:
            sub_dict[sub] = sub_dict.get(sub, 0) + dur
        for sub, dur in sub_dict.items():
            sh, sm = dur // 3600, (dur % 3600) // 60
            embed.add_field(name=sub, value=f"{sh}h {sm}m", inline=True)

    elif mode == "nam":
        cursor.execute("SELECT subject, duration FROM daily_study WHERE user_id = ? AND date LIKE ?", (user_id, f"%{current_year}"))
        rows = cursor.fetchall()
        total_sec = sum(r[1] for r in rows)
        h, m, _ = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
        embed.description = f"📅 **Năm:** {current_year}\n⏱️ **Tổng thời gian:** {h}h {m}m\n\n"
        sub_dict = {}
        for sub, dur in rows:
            sub_dict[sub] = sub_dict.get(sub, 0) + dur
        for sub, dur in sub_dict.items():
            sh, sm = dur // 3600, (dur % 3600) // 60
            embed.add_field(name=sub, value=f"{sh}h {sm}m", inline=True)

    elif mode == "mon" and target:
        cursor.execute("SELECT duration FROM subject_study WHERE user_id = ? AND subject = ?", (user_id, target))
        row = cursor.fetchone()
        total_sec = row[0] if row else 0
        h, m, s = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
        embed.description = f"📚 **Môn học:** {target}\n⏱️ **Tổng tích lũy từ trước đến nay:** {h}h {m}m {s}s"

    else:
        cursor.execute("SELECT total_time FROM user_study WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        total_sec = row[0] if row else 0
        clovers = get_clovers(user_id)
        h, m, s = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
        embed.description = f"🍀 **Cỏ 4 Lá hiện có:** {clovers}\n⏱️ **Tổng thời gian học toàn bộ:** {h}h {m}m {s}s\n\n💡 *Gợi ý cú pháp:* `!baocao ngay`, `!baocao tuan`, `!baocao thang`, `!baocao nam`, hoặc `!baocao mon <Tên môn>`"

    conn.close()
    await ctx.send(embed=embed)

# --- 📝 HỆ THỐNG TRẮC NGHIỆM HẰNG NGÀY ---
@bot.command()
async def tracnghiem(ctx):
    user_id = ctx.author.id
    today = datetime.now().strftime("%d/%m/%Y")

    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT attempts FROM quiz_limits WHERE user_id = ? AND date = ?", (user_id, today))
    row = cursor.fetchone()
    attempts = row[0] if row else 0

    if attempts >= 3:
        await ctx.send(f"⚠️ {ctx.author.mention} ơi, hôm nay bạn đã hoàn thành tối đa 3 lượt trắc nghiệm rồi! Hãy nghỉ ngơi hoặc ôn tập thêm nhé! 🌸 (｡•́‿•̀｡)")
        conn.close()
        return

    questions = [
        {"q": "Đâu là một môn khoa học tự nhiên?", "options": ["A. Vật Lý", "B. Ngữ Văn", "C. Lịch Sử", "D. Địa Lý"], "answer": "A"},
        {"q": "Thủ đô của Việt Nam là gì?", "options": ["A. TP. Hồ Chí Minh", "B. Hà Nội", "C. Đà Nẵng", "D. Hải Phòng"], "answer": "B"},
        {"q": "Công thức tính diện tích hình chữ nhật là gì?", "options": ["A. Dài + Rộng * 2", "B. Dài * Rộng", "C. Cạnh nhân bốn", "D. Đáy nhân cao chia hai"], "answer": "B"},
        {"q": "Trong tiếng Anh, từ nào có nghĩa là 'Quả táo'?", "options": ["A. Banana", "B. Orange", "C. Apple", "D. Grape"], "answer": "C"}
    ]

    q_data = random.choice(questions)
    
    cursor.execute("INSERT INTO quiz_limits (user_id, date, attempts) VALUES (?, ?, 1) ON CONFLICT(user_id, date) DO UPDATE SET attempts = attempts + 1", (user_id, today))
    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="🧠 TRẮC NGHIỆM HẰNG NGÀY 📚",
        description=f"**Câu hỏi:** {q_data['q']}\n\n" + "\n".join(q_data['options']) + f"\n\n👉 *Hãy gõ chữ cái đáp án của bạn (A, B, C hoặc D) trong vòng 30 giây nhé!* ( •̀ ω •́ )✧",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.upper() in ["A", "B", "C", "D"]

    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
        user_ans = msg.content.upper()
        if user_ans == q_data['answer']:
            add_clovers(user_id, 10)
            await ctx.send(f"🎉 Chính xác tuyệt vời! Chúc mừng {ctx.author.mention} nhận được **+10 Cỏ 4 Lá 🍀**! (๑•̀ㅂ•́)و✧")
        else:
            await ctx.send(f"❌ Tiếc quá, đáp án đúng phải là **{q_data['answer']}** cơ. Lần sau cố gắng hơn nha Ong! 💪🌸")
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ Hết giờ mất rồi {ctx.author.mention} ơi! Lần sau nhanh tay hơn nhé! (｡•́︿•̀｡)")


# ============================================================
# ⏰ HỆ THỐNG NHẮC NHỞ CÁ NHÂN
# ============================================================
# Cách dùng:
#
# !nhacnho 28/09/2026 20:30 Ôn Toán
# !nhacnho 29/09/2026 07:00 Học từ vựng
#
# Xem các nhắc nhở:
# !nhacnho xem
#
# Xóa nhắc nhở:
# !nhacnho xoa 1
#
# ============================================================

import asyncio
import sqlite3
from datetime import datetime


# ============================================================
# 📦 TẠO BẢNG REMINDER
# ============================================================

def init_reminder_database():

    conn = sqlite3.connect(
        "study_data.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            reminder_time TEXT NOT NULL,
            content TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
        """
    )

    conn.commit()
    conn.close()


init_reminder_database()


# ============================================================
# ➕ THÊM NHẮC NHỞ
# ============================================================

@bot.command(
    name="nhacnho"
)
async def nhacnho(
    ctx,
    action_or_date: str = None,
    gio_or_id: str = None,
    *,
    noi_dung: str = None
):

    # ========================================================
    # 📋 !nhacnho xem
    # ========================================================

    if action_or_date and action_or_date.lower() == "xem":

        conn = sqlite3.connect(
            "study_data.db"
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                reminder_time,
                content
            FROM reminders
            WHERE user_id = ?
            AND guild_id = ?
            AND completed = 0
            ORDER BY reminder_time ASC
            """,
            (
                ctx.author.id,
                ctx.guild.id
            )
        )

        reminders = cursor.fetchall()

        conn.close()

        if not reminders:

            await ctx.send(
                f"📋 {ctx.author.mention}, "
                f"bạn hiện không có nhắc nhở nào."
            )

            return

        embed = discord.Embed(
            title="⏰ NHẮC NHỞ CỦA BẠN",
            description=(
                "🌸 Đây là toàn bộ lịch nhắc nhở "
                "mà bạn đang đặt:"
            ),
            color=discord.Color.gold()
        )

        for reminder_id, reminder_time, content in reminders:

            try:

                dt = datetime.strptime(
                    reminder_time,
                    "%Y-%m-%d %H:%M:%S"
                )

                time_display = dt.strftime(
                    "%d/%m/%Y • %H:%M"
                )

            except:

                time_display = reminder_time

            embed.add_field(
                name=(
                    f"⏰ Nhắc nhở #{reminder_id}"
                ),
                value=(
                    f"📅 **{time_display}**\n"
                    f"📝 {content}\n"
                    f"🗑️ Xóa bằng: "
                    f"`!nhacnho xoa {reminder_id}`"
                ),
                inline=False
            )

        embed.set_footer(
            text=(
                "Không xóa thì bot sẽ tự động "
                "nhắc bạn đúng thời gian."
            )
        )

        await ctx.send(
            embed=embed
        )

        return


    # ========================================================
    # 🗑️ !nhacnho xoa ID
    # ========================================================

    if action_or_date and action_or_date.lower() == "xoa":

        if not gio_or_id:

            await ctx.send(
                "❌ Bạn chưa nhập ID nhắc nhở!\n\n"
                "Ví dụ:\n"
                "`!nhacnho xoa 3`"
            )

            return

        try:

            reminder_id = int(
                gio_or_id
            )

        except ValueError:

            await ctx.send(
                "❌ ID nhắc nhở phải là số.\n\n"
                "Ví dụ:\n"
                "`!nhacnho xoa 3`"
            )

            return

        conn = sqlite3.connect(
            "study_data.db"
        )

        cursor = conn.cursor()

        # Chỉ cho phép người đặt lịch
        # xóa lịch của chính mình
        cursor.execute(
            """
            SELECT reminder_time, content
            FROM reminders
            WHERE id = ?
            AND user_id = ?
            AND guild_id = ?
            AND completed = 0
            """,
            (
                reminder_id,
                ctx.author.id,
                ctx.guild.id
            )
        )

        reminder = cursor.fetchone()

        if not reminder:

            conn.close()

            await ctx.send(
                f"❌ Không tìm thấy nhắc nhở "
                f"**#{reminder_id}** của bạn."
            )

            return

        cursor.execute(
            """
            DELETE FROM reminders
            WHERE id = ?
            AND user_id = ?
            AND guild_id = ?
            """,
            (
                reminder_id,
                ctx.author.id,
                ctx.guild.id
            )
        )

        conn.commit()
        conn.close()

        await ctx.send(
            f"🗑️ Đã xóa nhắc nhở "
            f"**#{reminder_id}** thành công!\n\n"
            f"📝 Nội dung: **{reminder[1]}**"
        )

        return


    # ========================================================
    # ❌ KIỂM TRA CÚ PHÁP
    # ========================================================

    if (
        not action_or_date
        or not gio_or_id
        or not noi_dung
    ):

        await ctx.send(
            "❌ **Cách sử dụng lệnh `!nhacnho`:**\n\n"

            "⏰ **Đặt nhắc nhở:**\n"
            "`!nhacnho DD/MM/YYYY HH:MM Nội dung`\n\n"

            "📋 **Xem nhắc nhở:**\n"
            "`!nhacnho xem`\n\n"

            "🗑️ **Xóa nhắc nhở:**\n"
            "`!nhacnho xoa ID`\n\n"

            "🌸 **Ví dụ:**\n"
            "`!nhacnho 28/09/2026 20:30 Ôn Toán`"
        )

        return


    # ========================================================
    # 📅 PHÂN TÍCH NGÀY + GIỜ
    # ========================================================

    try:

        reminder_datetime = datetime.strptime(
            f"{action_or_date} {gio_or_id}",
            "%d/%m/%Y %H:%M"
        )

    except ValueError:

        await ctx.send(
            "❌ Ngày hoặc giờ không đúng định dạng!\n\n"

            "📌 Đúng:\n"
            "`!nhacnho 28/09/2026 20:30 Ôn Toán`\n\n"

            "📅 Ngày: `DD/MM/YYYY`\n"
            "🕐 Giờ: `HH:MM`"
        )

        return


    # ========================================================
    # ⛔ KHÔNG CHO ĐẶT LỊCH TRONG QUÁ KHỨ
    # ========================================================

    if reminder_datetime <= datetime.now():

        await ctx.send(
            "⚠️ Thời gian nhắc nhở phải nằm "
            "ở tương lai nha Ong! 🐝"
        )

        return


    # ========================================================
    # 💾 LƯU DATABASE
    # ========================================================

    conn = sqlite3.connect(
        "study_data.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reminders
        (
            user_id,
            guild_id,
            reminder_time,
            content,
            completed
        )
        VALUES (?, ?, ?, ?, 0)
        """,
        (
            ctx.author.id,
            ctx.guild.id,
            reminder_datetime.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            noi_dung
        )
    )

    reminder_id = cursor.lastrowid

    conn.commit()
    conn.close()


    # ========================================================
    # ✅ THÔNG BÁO ĐẶT THÀNH CÔNG
    # ========================================================

    embed = discord.Embed(
        title="⏰ ĐẶT NHẮC NHỞ THÀNH CÔNG!",
        description=(
            f"{ctx.author.mention}, bot đã lưu "
            f"nhắc nhở của bạn rồi! 🌸🐝\n\n"

            f"🆔 **Mã nhắc nhở:** "
            f"`#{reminder_id}`\n"

            f"📅 **Ngày:** "
            f"{reminder_datetime.strftime('%d/%m/%Y')}\n"

            f"🕐 **Giờ:** "
            f"{reminder_datetime.strftime('%H:%M')}\n"

            f"📝 **Nội dung:** "
            f"{noi_dung}\n\n"

            f"💡 Muốn xem lại:\n"
            f"`!nhacnho xem`\n\n"

            f"🗑️ Muốn xóa:\n"
            f"`!nhacnho xoa {reminder_id}`"
        ),
        color=discord.Color.green()
    )

    await ctx.send(
        embed=embed
    )


# ============================================================
# 🔔 VÒNG KIỂM TRA NHẮC NHỞ
# ============================================================

async def reminder_loop():

    await bot.wait_until_ready()

    while not bot.is_closed():

        try:

            now = datetime.now()

            conn = sqlite3.connect(
                "study_data.db"
            )

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    guild_id,
                    reminder_time,
                    content
                FROM reminders
                WHERE completed = 0
                """
            )

            reminders = cursor.fetchall()

            for (
                reminder_id,
                user_id,
                guild_id,
                reminder_time,
                content
            ) in reminders:

                try:

                    reminder_datetime = datetime.strptime(
                        reminder_time,
                        "%Y-%m-%d %H:%M:%S"
                    )

                except ValueError:

                    continue


                # ============================================
                # ⏰ ĐÃ ĐẾN GIỜ
                # ============================================

                if reminder_datetime <= now:

                    guild = bot.get_guild(
                        guild_id
                    )

                    if not guild:
                        continue

                    member = guild.get_member(
                        user_id
                    )

                    if not member:
                        continue

                    # ========================================
                    # GỬI NHẮC NHỞ
                    # ========================================

                    try:

                        await member.send(
                            content=(
                                f"⏰ **ĐẾN GIỜ NHẮC NHỞ RỒI NÈ ONG!** "
                                f"{member.mention} 🌸🐝"
                            ),
                            embed=discord.Embed(
                                title="⏰ NHẮC NHỞ HỌC TẬP",
                                description=(
                                    f"🔔 **Nội dung:** "
                                    f"{content}\n\n"

                                    f"📅 **Ngày:** "
                                    f"{reminder_datetime.strftime('%d/%m/%Y')}\n"

                                    f"🕐 **Giờ:** "
                                    f"{reminder_datetime.strftime('%H:%M')}\n\n"

                                    f"💪 Đừng quên hoàn thành "
                                    f"việc mà Ong đã đặt lịch nhé! "
                                    f"🌸✨"
                                ),
                                color=discord.Color.gold()
                            )
                        )

                    except discord.Forbidden:

                        # Nếu không gửi DM được,
                        # gửi vào kênh chung
                        channel = discord.utils.get(
                            guild.text_channels,
                            name="🌸·chung"
                        )

                        if channel:

                            await channel.send(
                                content=(
                                    f"⏰ {member.mention} "
                                    f"**đến giờ nhắc nhở rồi!** 🌸"
                                ),
                                embed=discord.Embed(
                                    title="⏰ NHẮC NHỞ",
                                    description=content,
                                    color=discord.Color.gold()
                                )
                            )


                    # ========================================
                    # ĐÁNH DẤU ĐÃ HOÀN THÀNH
                    # ========================================

                    cursor.execute(
                        """
                        UPDATE reminders
                        SET completed = 1
                        WHERE id = ?
                        """,
                        (reminder_id,)
                    )

            conn.commit()
            conn.close()

        except Exception as e:

            print(
                f"[REMINDER LOOP ERROR] {e}"
            )

        # Kiểm tra mỗi 10 giây
        await asyncio.sleep(10)


# ============================================================
# 🚀 KHỞI ĐỘNG REMINDER LOOP
# ============================================================

@bot.event
async def on_ready():

    # Tránh tạo nhiều loop nếu Discord reconnect
    if not hasattr(
        bot,
        "reminder_loop_started"
    ):

        bot.reminder_loop_started = True

        bot.loop.create_task(
            reminder_loop()
        )

    print(
        f"✅ Reminder system đã hoạt động "
        f"với tài khoản {bot.user}"
    )

# --- 🛠️ LỆNH REFRESH / TẠO SERVER & KỶ LUẬT ---
@bot.command()
async def setup_server(ctx):
    if not is_bql(ctx): return
    guild = ctx.guild
    
    roles_to_create = [
        ("👑 Chủ Server", discord.Color.red()),
        ("🛡️ Quản Trị Viên (BQL)", discord.Color.orange()),
        ("⭐ Ong Chăm Chỉ", discord.Color.gold()),
        ("📚 Thành Viên Học Tập", discord.Color.blue()),
        ("🚨 Vi Phạm Kỷ Luật", discord.Color.dark_gray())
    ]
    
    for r_name, r_color in roles_to_create:
        if not discord.utils.get(guild.roles, name=r_name):
            await guild.create_role(name=r_name, color=r_color)

    categories_structure = {
        "📌 THÔNG TIN CHUNG": [
            ("📢·thông-báo", "text"),
            ("📜·nội-quy-server", "text"),
            ("🛒·shop-cỏ-4-lá", "text")
        ],
        "🌸 KHU VỰC HỌC TẬP": [
            ("🌸·chung", "text"),
            ("📚·chia-sẻ-tài-liệu", "text"),
            ("🧠·trắc-nghiệm-mỗi-ngày", "text"),
            ("🎧·phòng-tập-trung-1", "voice"),
            ("🎧·phòng-tập-trung-2", "voice")
        ],
        "🛡️ HỆ THỐNG KỶ LUẬT": [
            ("⚠️·kênh-kỷ-luật", "text")
        ]
    }

    role_ky_luat = discord.utils.get(guild.roles, name="🚨 Vi Phạm Kỷ Luật")

    for cat_name, channels in categories_structure.items():
        category = discord.utils.get(guild.categories, name=cat_name)
        if not category:
            category = await guild.create_category(cat_name)
        
        for c_name, c_type in channels:
            existing = discord.utils.get(guild.channels, name=c_name)
            if not existing:
                if c_type == "voice":
                    await guild.create_voice_channel(c_name, category=category)
                else:
                    chan = await guild.create_text_channel(c_name, category=category)
                    if c_name == "⚠️·kênh-kỷ-luật" and role_ky_luat:
                        await chan.set_permissions(role_ky_luat, read_messages=True, send_messages=True)
                        await chan.set_permissions(guild.default_role, read_messages=False)

    await ctx.send("✅ Đã thiết lập hoàn tất toàn bộ **Role quan trọng** và **Hệ thống kênh chuyên nghiệp** için Server! 🚀✨ ( •̀ ω •́ )✧")

@bot.command()
async def xem_phat(ctx):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT level, clovers_deduct, description FROM dynamic_punishments")
    rules = cursor.fetchall()
    conn.close()

    if not rules:
        await ctx.send("📜 Hiện chưa có mức phạt nào!")
        return

    embed = discord.Embed(title="📜 BẢNG CÁC MỨC PHẠT VÀ KỶ LUẬT", color=discord.Color.dark_orange())
    for lvl, clovers, desc in rules:
        embed.add_field(name=f"🛑 Mức {lvl} (Trừ {clovers} Cỏ 🍀)", value=desc, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def them_phat(ctx, muc_do: str, so_co_tru: int, *, noi_dung_phat: str):
    if not is_bql(ctx): return
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO dynamic_punishments (level, clovers_deduct, description) VALUES (?, ?, ?)", (muc_do, so_co_tru, noi_dung_phat))
    conn.commit()
    conn.close()
    await ctx.send(f"✅ Đã thêm/cập nhật thành công **Mức phạt {muc_do}** (Trừ {so_co_tru} Cỏ 🍀)! 🌸✨ ( •̀ ω •́ )✧")

@bot.command()
async def phat(ctx, member: discord.Member, muc_do: str, *, ly_do: str = "Vi phạm nội quy / AFK"):
    if not is_bql(ctx): return

    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT clovers_deduct, description FROM dynamic_punishments WHERE level = ?", (muc_do,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await ctx.send("⚠️ Mức phạt này chưa tồn tại! Gõ `!xem_phat` để xem các mức có sẵn.")
        return

    clovers_deduct, hinh_phat = row
    add_clovers(member.id, -clovers_deduct)

    role_ky_luat = discord.utils.get(ctx.guild.roles, name="🚨 Vi Phạm Kỷ Luật")
    if not role_ky_luat:
        role_ky_luat = await ctx.guild.create_role(name="🚨 Vi Phạm Kỷ Luật", color=discord.Color.dark_gray())

    await member.add_roles(role_ky_luat)

    ky_luat_chan = discord.utils.get(ctx.guild.text_channels, name="⚠️·kênh-kỷ-luật")
    embed = discord.Embed(
        title="🛑 THÔNG BÁO CÁCH LY & XỬ PHẠT 🛑",
        description=f"Thành viên {member.mention} đã vi phạm!\n\n📌 **Lý do:** {ly_do}\n📊 **Mức độ:** Mức {muc_do}\n💸 **Trừ:** -{clovers_deduct} Cỏ 4 Lá 🍀\n⚖️ **Hình phạt:**\n{hinh_phat}",
        color=discord.Color.red()
    )

    if ky_luat_chan:
        await ky_luat_chan.send(f"{member.mention}", embed=embed)
    await ctx.send(f"🚨 Đã xử phạt {member.mention} thành công! 🎯")

@bot.command()
async def duyet(ctx, member: discord.Member, *, loi_nhan: str = "Đã hoàn thành tốt hình phạt!"):
    if not is_bql(ctx): return
    role_ky_luat = discord.utils.get(ctx.guild.roles, name="🚨 Vi Phạm Kỷ Luật")
    if role_ky_luat in member.roles:
        await member.remove_roles(role_ky_luat)
        embed = discord.Embed(
            title="🔓 DUYỆT HÌNH PHẠT THÀNH CÔNG",
            description=f"Ban Quản Lý đã duyệt bài của {member.mention}!\n💬 **Lời nhắn:** {loi_nhan}\n\n🌸 *Bạn đã được gỡ kỷ luật!* ٩(ˊᗜˋ*)و",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"⚠️ Thành viên này hiện không bị dính kỷ luật nha Ong!")

# --- RUN BOT ---
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
