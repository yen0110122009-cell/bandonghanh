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

# --- DỮ LIỆU CỬA HÀNG (SHOP) ---
SHOP_ITEMS = {
    "1": {"name": "❄️ Thẻ Đóng Băng Streak", "price": 100, "desc": "Bảo toàn chuỗi học tập liên tục của bạn khi nghỉ 1 ngày"}
}

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

# --- ⏱️ THEO DÕI CAMERA, VOICE, CHÀO MỪNG & TẠM BIỆT ---
@bot.event
async def on_voice_state_update(member, before, after):
    # 1. Tự động tạo phòng học riêng
    if after.channel and "Tạo Phòng Học" in after.channel.name:
        guild = member.guild
        category = after.channel.category
        new_channel = await guild.create_voice_channel(name=f"🌸 Phòng Học Của {member.display_name}", category=category)
        await member.move_to(new_channel)

    # 2. Thành viên VÀO phòng voice (Gửi câu chào mừng ngọt ngào)
    if before.channel is None and after.channel is not None:
        welcome_chan = discord.utils.get(member.guild.text_channels, name="🌸·chung") or after.channel
        embed_welcome = discord.Embed(
            title="✨ CHÀO MỪNG BẠN ĐÃ ĐẾN VỚI GÓC HỌC TẬP! ✨",
            description=f"Chào mừng {member.mention} đã vào phòng voice **{after.channel.name}**! 🌸🐝\n\n"
                        f"*Chúc Ong có một buổi học tập thật năng suất, tập trung và đạt kết quả cao nha!* ( •̀ ω •́ )✧\n"
                        f"💡 *Gợi ý:* Hãy bật camera để tích lũy thời gian học, đổi Cỏ 4 Lá 🍀 và duy trì chuỗi học tập nhé!",
            color=discord.Color.gold()
        )
        try:
            await welcome_chan.send(content=f"{member.mention}", embed=embed_welcome, delete_after=60)
        except Exception:
            pass

    # 3. Khi bật camera học tập
    if not before.self_video and after.self_video and after.channel:
        user_cam_start[member.id] = time.time()
        user_subject_study[member.id] = {"subject": "Tự do", "start_time": time.time()}
        
        embed = discord.Embed(
            title="🎉 BẮT ĐẦU TÍCH LŨY GIỜ HỌC! 🎉",
            description=f"{member.mention} đã bật camera học cùng mọi người rồi nè! 🌸✨\n\n👉 **Hãy chọn môn học bên dưới bảng tương tác nhé:**",
            color=discord.Color.green()
        )
        view = SubjectSelectView(member.id)
        try:
            await after.channel.send(content=f"{member.mention}", embed=embed, view=view, delete_after=120)
        except Exception:
            pass

    # 4. Khi tắt camera hoặc RỜI phòng voice (Tổng kết, quy đổi 1:9, tính Streak & Tạm biệt)
    elif (before.self_video and not after.self_video) or (before.channel and not after.channel and member.id in user_cam_start):
        if member.id in user_cam_start:
            start_t = user_cam_start.pop(member.id)
            duration = int(time.time() - start_t)
            duration_minutes = duration // 60

            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60

            subject_info = user_subject_study.get(member.id, {"subject": "Tự do"})
            subject_name = subject_info["subject"]
            
            add_study_time(member.id, subject_name, duration)
            
            # 🍀 QUY ĐỔI CỎ 4 LÁ THEO MỐC 1:9 (Cứ 9 phút = 1 Cỏ 4 Lá)
            earned_clovers = duration_minutes // 9
            if earned_clovers > 0:
                add_clovers(member.id, earned_clovers)

            # 🔥 TÍNH TOÁN & CẬP NHẬT CHUỖI HỌC (STREAK)
            today_str = datetime.now().strftime("%d/%m/%Y")
            yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
            
            conn = sqlite3.connect("study_data.db")
            cursor = conn.cursor()
            cursor.execute("SELECT current_streak, last_study_date FROM user_streak WHERE user_id = ?", (member.id,))
            streak_row = cursor.fetchone()
            
            current_streak = 1
            if streak_row:
                last_date = streak_row[1]
                if last_date == today_str:
                    current_streak = streak_row[0]
                elif last_date == yesterday_str:
                    current_streak = streak_row[0] + 1
                else:
                    current_streak = 1
                cursor.execute("UPDATE user_streak SET current_streak = ?, last_study_date = ? WHERE user_id = ?", (current_streak, today_str, member.id))
            else:
                cursor.execute("INSERT INTO user_streak (user_id, current_streak, last_study_date) VALUES (?, ?, ?)", (member.id, 1, today_str))
            conn.commit()
            conn.close()

            chan = before.channel or after.channel
            if chan:
                time_str = f"{hours} giờ " if hours > 0 else ""
                time_str += f"{minutes} phút " if minutes > 0 or hours > 0 else ""
                time_str += f"{seconds} giây"

                msg = (
                    f"👋 Tạm biệt {member.mention}! Cảm ơn bạn vì đã nỗ lực hết mình hôm nay. "
                    f"**Chúc bạn nghỉ ngơi thật thoải mái và nạp lại năng lượng nhé!** 🌸✨ ( ˘ ³˘)♥\n\n"
                    f"📚 **Môn học đã học:** {subject_name}\n"
                    f"⏱️ **Thời gian tập trung:** **{time_str}**\n"
                    f"🔥 **Chuỗi học tập hiện tại:** **{current_streak} ngày liên tiếp**!"
                )
                if earned_clovers > 0:
                    msg += f"\n🍀 **Quy đổi (Mốc 1:9):** Nhận được **+{earned_clovers} Cỏ 4 Lá**!"
                await chan.send(msg)

    if before.channel and len(before.channel.members) == 0 and before.channel.name.startswith("🌸 Phòng Học Của"):
        await before.channel.delete()

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

# --- 🛒 CỬA HÀNG (SHOP) & ĐỔI QUÀ ---
@bot.command()
async def shop(ctx):
    embed = discord.Embed(title="🛒 CỬA HÀNG CỎ 4 LÁ 🍀", description="Dùng Cỏ 4 Lá kiếm được để đổi các phần quà đặc biệt nhé! Gõ `!mua <mã_item>` để mua.", color=discord.Color.gold())
    for code, item in SHOP_ITEMS.items():
        embed.add_field(name=f"[{code}] {item['name']} - 🍀 {item['price']} Cỏ", value=item['desc'], inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def mua(ctx, code: str):
    user_id = ctx.author.id
    if code not in SHOP_ITEMS:
        await ctx.send("⚠️ Mã món hàng không tồn tại! Gõ `!shop` để xem danh sách.")
        return
    
    item = SHOP_ITEMS[code]
    price = item['price']
    current_clovers = get_clovers(user_id)

    if current_clovers < price:
        await ctx.send(f"❌ Bạn không đủ Cỏ 4 Lá! Bạn đang có {current_clovers} 🍀 nhưng món này cần tới {price} 🍀.")
        return

    add_clovers(user_id, -price)
    add_item_to_inventory(user_id, item['name'], 1)
    await ctx.send(f"🎉 Chúc mừng {ctx.author.mention} đã mua thành công **{item['name']}**! Đã trừ -{price} 🍀. Kiểm tra kho đồ bằng lệnh `!tuido` nhé! (๑•̀ㅂ•́)و✧")

@bot.command(name="tuido")
async def tuido(ctx):
    user_id = ctx.author.id
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, amount FROM user_inventory WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    embed = discord.Embed(title=f"🎒 TÚI ĐỒ CỦA {ctx.author.display_name}", color=discord.Color.blurple())
    if rows:
        desc = ""
        for name, amt in rows:
            desc += f"• **{name}**: x{amt}\n"
        embed.description = desc
    else:
        embed.description = "Túi đồ của bạn đang trống! Hãy chăm chỉ học tập kiếm Cỏ để mua sắm nhé! 🌸"
    await ctx.send(embed=embed)
# --- ⏰ 1. TÍNH NĂNG NHẮC NHỞ TỰ ĐỘNG (!nhacnho) ---
@bot.command()
async def nhacnho(ctx, thoi_gian: int, don_vi: str, *, noi_dung: str):
    """
    Cú pháp: !nhacnho <số> <phút/giây/giờ> <nội dung>
    Ví dụ: !nhacnho 30 phút ôn bài môn Toán
    """
    seconds = 0
    don_vi = don_vi.lower()
    if "giây" in don_vi or don_vi.startswith("s"):
        seconds = thoi_gian
    elif "phút" in don_vi or don_vi.startswith("p"):
        seconds = thoi_gian * 60
    elif "giờ" in don_vi or don_vi.startswith("g") or don_vi.startswith("h"):
        seconds = thoi_gian * 3600
    else:
        await ctx.send(f"⚠️ {ctx.author.mention} ơi, đơn vị thời gian chưa đúng! Hãy dùng `giây`, `phút` hoặc `giờ` nha! (｡•́‿•̀｡)")
        return

    if seconds > 86400: # Giới hạn tối đa 24 giờ
        await ctx.send(f"⚠️ {ctx.author.mention} ơi, thời gian nhắc nhở tối đa chỉ trong vòng 24 giờ thôi nhé! 🌸")
        return

    time_str = f"{thoi_gian} {don_vi}"
    await ctx.send(f"⏳ Đã ghi nhận! Lumi sẽ nhắc {ctx.author.mention} về nội dung: *'{noi_dung}'* sau **{time_str}** nữa nha! ( •̀ ω •́ )✧")

    await asyncio.sleep(seconds)
    
    embed_remind = discord.Embed(
        title="⏰ TIN NHẮC NHỞ QUAN TRỌNG! ⏰",
        description=f"Ey {ctx.author.mention} ơi! Đã hết **{time_str}** rồi nè!\n\n📌 **Nội dung:** {noi_dung}\n\n*Cố gắng hoàn thành thật tốt nha Ong!* 💪✨ (๑•̀ㅂ•́)و✧",
        color=discord.Color.gold()
    )
    await ctx.send(content=f"{ctx.author.mention}", embed=embed_remind)


# --- 🏆 2. BẢNG XẾP HẠNG HỌC TẬP (!top hoặc !xephang) ---
@bot.command(aliases=["xephang"])
async def top(ctx):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    
    # Lấy top 10 người có nhiều Cỏ 4 Lá nhất
    cursor.execute("SELECT user_id, clovers FROM user_clovers ORDER BY clovers DESC LIMIT 10")
    clover_rows = cursor.fetchall()
    
    # Lấy top 10 người có tổng thời gian học nhiều nhất
    cursor.execute("SELECT user_id, total_time FROM user_study ORDER BY total_time DESC LIMIT 10")
    time_rows = cursor.fetchall()
    conn.close()

    embed = discord.Embed(title="🏆 BẢNG XẾP HẠNG THÀNH TÍCH (LEADERBOARD) 🍀", color=discord.Color.gold())

    # Format bảng Cỏ 4 Lá
    clover_text = ""
    for idx, (uid, clovers) in enumerate(clover_rows, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"**{idx}.**"
        clover_text += f"{medal} <@{uid}> — **{clovers} 🍀**\n"
    
    if not clover_text:
        clover_text = "Chưa có dữ liệu xếp hạng Cỏ 4 Lá!"
    embed.add_field(name="✨ Top Cỏ 4 Lá Tích Lũy", value=clover_text, inline=False)

    # Format bảng Thời gian học
    time_text = ""
    for idx, (uid, total_sec) in enumerate(time_rows, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"**{idx}.**"
        h, m = total_sec // 3600, (total_sec % 3600) // 60
        time_text += f"{medal} <@{uid}> — **{h} giờ {m} phút** ⏱️\n"
        
    if not time_text:
        time_text = "Chưa có dữ liệu thời gian học tập!"
    embed.add_field(name="⏱️ Top Thời Gian Tập Trung", value=time_text, inline=False)

    embed.set_footer(text="Cố gắng chăm chỉ mỗi ngày để leo top nha Ong ơi! 🌸 ( ˘ ³˘)♥")
    await ctx.send(embed=embed)
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
            ("🌸·tạo-phòng-học", "voice"),
            ("🎧·phòng-tập-trung-1", "voice"),
            ("🎧·phòng-tập-trung-2", "voice")
        ],
        "☕ GÓC THƯ GIÃN": [
            ("💬·trò-chuyện-chung", "text"),
            ("📸·khoảnh-khắc-mỗi-ngày", "text"),
            ("🎵·âm-nhạc-thư-giãn", "voice")
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
