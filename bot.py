import os
import time
import random
import sqlite3
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands

# --- 🌐 TẠO WEB SERVER ĐỂ RENDER HEALTH CHECK 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Ong & Cỏ 4 Lá đang hoạt động 24/7! 🌸🐝🍀"

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

# Biến lưu thời gian học:
user_voice_start = {}
user_subject_study = {}

# --- KHỞI TẠO DATABASE SQLITE ---
def init_db():
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    # Bảng Ví Cỏ 4 Lá
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_clovers (
            user_id INTEGER PRIMARY KEY,
            clovers INTEGER DEFAULT 0
        )
    """)
    # Bảng Tổng Giờ Học (giây)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_study (
            user_id INTEGER PRIMARY KEY,
            total_time INTEGER DEFAULT 0
        )
    """)
    # Bảng Thời Gian Học Theo Từng Môn (giây)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_study (
            user_id INTEGER,
            subject TEXT,
            duration INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, subject)
        )
    """)
    # Bảng Streak & Thẻ Đóng Băng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_streaks (
            user_id INTEGER PRIMARY KEY,
            streak_days INTEGER DEFAULT 0,
            freeze_cards INTEGER DEFAULT 0
        )
    """)
    # Bảng Kỷ Luật / Vi Phạm
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_penalties (
            user_id INTEGER PRIMARY KEY,
            warnings INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- CÁC HÀM XỬ LÝ DATABASE ---
def get_clovers(user_id):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT clovers FROM user_clovers WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def add_clovers(user_id, amount):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_clovers (user_id, clovers) 
        VALUES (?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET clovers = clovers + ?
    """, (user_id, amount, amount))
    conn.commit()
    conn.close()

def add_study_time(user_id, seconds, subject=None):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_study (user_id, total_time) 
        VALUES (?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET total_time = total_time + ?
    """, (user_id, seconds, seconds))
    
    if subject:
        cursor.execute("""
            INSERT INTO subject_study (user_id, subject, duration) 
            VALUES (?, ?, ?) 
            ON CONFLICT(user_id, subject) DO UPDATE SET duration = duration + ?
        """, (user_id, subject, seconds, seconds))
        
    conn.commit()
    conn.close()

def add_warning(user_id, amount=1):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_penalties (user_id, warnings) 
        VALUES (?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET warnings = warnings + ?
    """, (user_id, amount, amount))
    conn.commit()
    conn.close()

def get_warnings(user_id):
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT warnings FROM user_penalties WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

# --- SỰ KIỆN KHI BOT ONLINE ---
@bot.event
async def on_ready():
    print(f"🎉 Bot {bot.user.name} đã sẵn sàng hoạt động cùng Ong! ( •̀ ω •́ )✧")

# --- 1. TÍNH NĂNG JOIN-TO-CREATE & THEO DÕI BẬT CAM PHÒNG VOICE ---
@bot.event
async def on_voice_state_update(member, before, after):
    # Kênh Voice "➕ Tạo Phòng Học"
    if after.channel and "Tạo Phòng Học" in after.channel.name:
        guild = member.guild
        category = after.channel.category
        new_channel = await guild.create_voice_channel(
            name=f"🌸 Phòng Học Của {member.display_name}",
            category=category
        )
        await member.move_to(new_channel)

    # Tính thời gian cày giờ khi tham gia/rời phòng voice
    if not before.channel and after.channel:
        user_voice_start[member.id] = time.time()
    elif before.channel and not after.channel:
        if member.id in user_voice_start:
            start_time = user_voice_start.pop(member.id)
            duration = int(time.time() - start_time)
            add_study_time(member.id, duration)
            
            # Tích lũy Cỏ 4 Lá (Mỗi 30 phút cày giờ tặng 5 Cỏ 4 Lá)
            earned_clovers = (duration // 1800) * 5
            if earned_clovers > 0:
                add_clovers(member.id, earned_clovers)
                
            # Xóa phòng tự tạo nếu không còn ai trong phòng
            if len(before.channel.members) == 0 and before.channel.name.startswith("🌸 Phòng Học Của"):
                await before.channel.delete()

# --- 2. XỬ LÝ CẢM XÚC TỰ ĐỘNG CHO KÊNH GÓP Ý ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Tự động thả cảm xúc ở kênh "góp-ý-xây-dựng"
    if message.channel.name == "góp-ý-xây-dựng":
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        await message.add_reaction("❤️")

    await bot.process_commands(message)

# --- 3. 🎁 HỆ THỐNG CÂU LỆNH THƯỞNG (DÀNH CHO BQL / ONGBEE) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def thuong(ctx, member: discord.Member, so_co: int, *, ly_do: str = "Tuyên dương thành tích học tập"):
    """Lệnh thưởng Cỏ 4 Lá cho thành viên (Chỉ Admin/BQL dùng được)"""
    add_clovers(member.id, so_co)
    
    # Gửi thông báo đến kênh "bảng-vinh-danh" nếu có
    vinh_danh_chan = discord.utils.get(ctx.guild.text_channels, name="bảng-vinh-danh")
    embed = discord.Embed(
        title="🎉 THƯỞNG CỎ 4 LÁ TUYÊN DƯƠNG 🎉",
        description=f"Chúc mừng {member.mention} đã nhận được **+{so_co} Cỏ 4 Lá 🍀**!\n**Lý do:** {ly_do} 🌸✨ ( •̀ ω •́ )✧",
        color=discord.Color.green()
    )
    
    if vinh_danh_chan:
        await vinh_danh_chan.send(embed=embed)
    await ctx.send(f"✅ Đã thưởng **{so_co} Cỏ 4 Lá 🍀** cho {member.mention} thành công!")

# --- 4. ⚖️ HỆ THỐNG CÂU LỆNH KỶ LUẬT & XỬ PHẠT (DÀNH CHO BQL / ONGBEE) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def phat(ctx, member: discord.Member, tru_co: int, *, ly_do: str = "Vi phạm kỷ luật học tập"):
    """Lệnh phạt trừ Cỏ + tính 1 lần cảnh báo (Chỉ Admin/BQL dùng được)"""
    add_clovers(member.id, -tru_co)
    add_warning(member.id, 1)
    tong_warn = get_warnings(member.id)
    
    # Gửi thông báo đến kênh "kênh-kỷ-luật" hoặc "sổ-lỗi-sai"
    ky_luat_chan = discord.utils.get(ctx.guild.text_channels, name="kênh-kỷ-luật")
    embed = discord.Embed(
        title="⚠️ THÔNG BÁO XỬ PHẠT KỶ LUẬT ⚠️",
        description=f"Thành viên {member.mention} đã bị xử phạt!\n"
                    f"• **Trừ:** {tru_co} Cỏ 4 Lá 🍀\n"
                    f"• **Số lần vi phạm:** {tong_warn} lần 🚨\n"
                    f"• **Lý do:** {ly_do}\n\n"
                    f"*Hãy chép lại lỗi sai vào kênh `sổ-lỗi-sai` để rút kinh nghiệm nhé!* (ง'̀-'́)ง",
        color=discord.Color.red()
    )
    
    if ky_luat_chan:
        await ky_luat_chan.send(embed=embed)
    await ctx.send(f"🚨 Đã xử phạt {member.mention} (Trừ {tru_co} Cỏ 🍀, +1 Vi phạm).")

# --- 5. ⏱️ LỆNH BẮT ĐẦU VÀ KẾT THÚC HỌC THEO MÔN CỤ THỂ ---
@bot.command()
async def hoctap(ctx, *, ten_mon: str):
    """Bắt đầu tính giờ học cho một môn cụ thể (Ví dụ: !hoctap Toán)"""
    user_id = ctx.author.id
    if user_id in user_subject_study:
        current_mon = user_subject_study[user_id]["subject"]
        await ctx.send(f"⚠️ {ctx.author.mention} đang trong phiên học môn **{current_mon}** rồi nha! Hãy gõ `!dung_hoc` trước khi sang môn mới nè! ( •̀ ω •́ )✧")
        return

    user_subject_study[user_id] = {
        "subject": ten_mon,
        "start_time": time.time()
    }
    await ctx.send(f"📚 {ctx.author.mention} đã bắt đầu phiên học môn **{ten_mon}**! Chúc Ong học tập thật tốt nha! 🌸✨ (๑•̀ㅂ•́)و✧")

@bot.command()
async def dung_hoc(ctx):
    """Dừng phiên học môn hiện tại và lưu kết quả"""
    user_id = ctx.author.id
    if user_id not in user_subject_study:
        await ctx.send(f"❌ {ctx.author.mention} chưa bấm bắt đầu học môn nào cả! Gõ `!hoctap <Tên_Môn>` để bắt đầu nha!")
        return

    study_data = user_subject_study.pop(user_id)
    ten_mon = study_data["subject"]
    duration = int(time.time() - study_data["start_time"])
    minutes = round(duration / 60, 1)

    add_study_time(user_id, duration, subject=ten_mon)
    
    earned_clovers = (duration // 1800) * 5
    if earned_clovers > 0:
        add_clovers(user_id, earned_clovers)

    await ctx.send(f"🎉 **HOÀN THÀNH PHIÊN HỌC!** {ctx.author.mention} đã học xong môn **{ten_mon}** trong **{minutes} phút**! Tích lũy thêm **+{earned_clovers} Cỏ 4 Lá 🍀**! 🌸✨ (⁠≧⁠▽⁠≧⁠)")

# --- 6. 📊 LỆNH BÁO CÁO TỔNG HỢP, MÔN HỌC & KỶ LUẬT ---
@bot.command()
async def baocao(ctx):
    """Xem báo cáo tổng hợp kết quả học tập và tình trạng kỷ luật cá nhân"""
    user_id = ctx.author.id
    clovers = get_clovers(user_id)
    warnings = get_warnings(user_id)
    
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT total_time FROM user_study WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    total_seconds = row[0] if row else 0
    total_hours = round(total_seconds / 3600, 1)
    
    cursor.execute("SELECT subject, duration FROM subject_study WHERE user_id = ?", (user_id,))
    subject_rows = cursor.fetchall()
    
    cursor.execute("SELECT streak_days FROM user_streaks WHERE user_id = ?", (user_id,))
    streak_row = cursor.fetchone()
    streak_days = streak_row[0] if streak_row else 0
    conn.close()

    embed = discord.Embed(
        title=f"📊 BÁO CÁO HỌC TẬP CỦA {ctx.author.display_name.upper()} 📊",
        description=f"Dưới đây là kết quả hành trình rèn luyện kỷ luật của bạn nè! 🌸✨",
        color=discord.Color.teal()
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.add_field(name="⏱️ Tổng Giờ Học", value=f"**{total_hours} Giờ**", inline=True)
    embed.add_field(name="🔥 Chuỗi Streak", value=f"**{streak_days} Ngày**", inline=True)
    embed.add_field(name="🍀 Ví Cỏ 4 Lá", value=f"**{clovers} Cỏ**", inline=True)
    embed.add_field(name="🚨 Cảnh Báo Lỗi", value=f"**{warnings} Lần**", inline=True)

    if subject_rows:
        subject_text = ""
        for sub, dur in subject_rows:
            sub_hours = round(dur / 3600, 1)
            subject_text += f"• **{sub}:** {sub_hours} giờ ({dur // 60} phút)\n"
        embed.add_field(name="📚 Chi Tiết Theo Môn Học", value=subject_text, inline=False)
    else:
        embed.add_field(name="📚 Chi Tiết Theo Môn Học", value="*Chưa có dữ liệu học theo môn cụ thể.*", inline=False)

    embed.set_footer(text="Cố gắng duy trì thói quen cày giờ mỗi ngày nha Ong! 🐝💛")
    await ctx.send(embed=embed)

# --- 7. 🛍️ SHOP ĐỔI QUÀ CỎ 4 LÁ ---
@bot.command()
async def shop(ctx):
    """Xem danh sách phần thưởng học tập trong Shop Cỏ 4 Lá"""
    embed = discord.Embed(
        title="🛍️ SHOP ĐỔI QUÀ CỎ 4 LÁ 🍀",
        description="Học tập chăm chỉ, tích Cỏ 4 Lá để đổi các phần thưởng học tập cốt lõi nha! 🌸✨ (๑•̀ㅂ•́)و✧",
        color=discord.Color.gold()
    )
    embed.add_field(name="`1` ❄️ Thẻ Đóng Băng Chuỗi", value="Giá: **30 Cỏ 4 Lá 🍀**\n*Giữ chuỗi Streak khi bận không học được.*", inline=False)
    embed.add_field(name="`2` 👑 Voucher Gỡ Cảnh Báo", value="Giá: **120 Cỏ 4 Lá 🍀**\n*Xóa 1 lần vi phạm kỷ luật nhẹ.*", inline=False)
    embed.add_field(name="`3` 🎁 Hộp Quà May Mắn", value="Giá: **35 Cỏ 4 Lá 🍀**\n*Mở ngẫu nhiên nhận 10-80 Cỏ hoặc 1 Thẻ Đóng Băng ❄️.*", inline=False)
    embed.add_field(name="`4` 🍯 Hũ Mật Chăm Chỉ (x2 Cỏ 3 Ngày)", value="Giá: **60 Cỏ 4 Lá 🍀**\n*Nhân đôi Cỏ 4 Lá nhận được khi làm trắc nghiệm.*", inline=False)
    embed.set_footer(text="Gõ !doiqua <Mã_Quà> để tiến hành đổi quà nha! (Ví dụ: !doiqua 3)")
    await ctx.send(embed=embed)

@bot.command()
async def doiqua(ctx, ma_qua: int):
    """Đổi Cỏ 4 Lá lấy phần thưởng cốt lõi trong Shop"""
    prices = {1: 30, 2: 120, 3: 35, 4: 60}
    names = {
        1: "❄️ Thẻ Đóng Băng Chuỗi",
        2: "👑 Voucher Gỡ Cảnh Báo",
        3: "🎁 Hộp Quà May Mắn",
        4: "🍯 Hũ Mật Chăm Chỉ"
    }

    if ma_qua not in prices:
        await ctx.send("❌ Mã quà không hợp lệ! Gõ `!shop` để xem lại bảng mã quà nha!")
        return

    cost = prices[ma_qua]
    current = get_clovers(ctx.author.id)

    if current < cost:
        await ctx.send(f"🥺 {ctx.author.mention} chưa đủ Cỏ 4 Lá rồi! Cần **{cost} 🍀** nhưng bạn chỉ có **{current} 🍀** thôi.")
        return

    add_clovers(ctx.author.id, -cost)

    if ma_qua == 1:
        conn = sqlite3.connect("study_data.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_streaks (user_id, freeze_cards) VALUES (?, 1) ON CONFLICT(user_id) DO UPDATE SET freeze_cards = freeze_cards + 1", (ctx.author.id,))
        conn.commit()
        conn.close()
        await ctx.send(f"🎉 **ĐỔI QUÀ THÀNH CÔNG!** {ctx.author.mention} đã nhận **1 Thẻ Đóng Băng Chuỗi ❄️**! ( •̀ ω •́ )✧")

    elif ma_qua == 2:
        # Xóa 1 vi phạm nếu có
        curr_warn = get_warnings(ctx.author.id)
        if curr_warn > 0:
            add_warning(ctx.author.id, -1)
        bql_chan = discord.utils.get(ctx.guild.text_channels, name="kênh-xét-duyệt-bql")
        if bql_chan:
            await bql_chan.send(f"🛍️ **YÊU CẦU ĐỔI QUÀ:** {ctx.author.mention} đã dùng Cỏ 4 Lá đổi: **Voucher Gỡ Cảnh Báo**! Đã giảm 1 lần vi phạm cho bạn ấy! 🌸✨")
        await ctx.send(f"🎉 **ĐỔI QUÀ THÀNH CÔNG!** {ctx.author.mention} đã dùng Voucher gỡ 1 lần cảnh báo! 🌸☘️ (⁠≧⁠▽⁠≧⁠)")

    elif ma_qua == 4:
        bql_chan = discord.utils.get(ctx.guild.text_channels, name="kênh-xét-duyệt-bql")
        if bql_chan:
            await bql_chan.send(f"🛍️ **YÊU CẦU ĐỔI QUÀ:** {ctx.author.mention} đã dùng Cỏ 4 Lá đổi: **{names[ma_qua]}**! BQL vui lòng kích hoạt x2 Cỏ cho bạn ấy nhé! 🌸✨")
        await ctx.send(f"🎉 **ĐỔI QUÀ THÀNH CÔNG!** {ctx.author.mention} đã đổi món **{names[ma_qua]}**! 🌸☘️ (⁠≧⁠▽⁠≧⁠)")

    elif ma_qua == 3:
        luck = random.choice(["clovers", "freeze"])
        if luck == "clovers":
            bonus = random.randint(10, 80)
            add_clovers(ctx.author.id, bonus)
            await ctx.send(f"🎁 **HỘP QUÀ MAY MẮN!** {ctx.author.mention} đã trúng thưởng **+{bonus} Cỏ 4 Lá 🍀**! 🌸✨ (⁠≧⁠▽⁠≧⁠)")
        else:
            conn = sqlite3.connect("study_data.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user_streaks (user_id, freeze_cards) VALUES (?, 1) ON CONFLICT(user_id) DO UPDATE SET freeze_cards = freeze_cards + 1", (ctx.author.id,))
            conn.commit()
            conn.close()
            await ctx.send(f"🎁 **HỘP QUÀ MAY MẮN!** {ctx.author.mention} trúng ngay **1 Thẻ Đóng Băng Chuỗi ❄️**! 🌿💖 ( •̀ ω •́ )✧")

# --- 8. ❓ GÓC TRẮC NGHIỆM TỰ ĐỘNG ---
class QuizView(discord.ui.View):
    def __init__(self, correct_option, user_id):
        super().__init__(timeout=60)
        self.correct_option = correct_option
        self.user_id = user_id

    async def check_answer(self, interaction: discord.Interaction, option: str):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Đây không phải lượt trả lời của bạn!", ephemeral=True)
            return

        if option == self.correct_option:
            add_clovers(interaction.user.id, 10)
            await interaction.response.send_message("🎉 **ĐÚNG RỒI!** Bạn nhận được **+10 Cỏ 4 Lá 🍀**! ( •̀ ω •́ )✧")
        else:
            await interaction.response.send_message("🥺 Rất tiếc, câu trả lời chưa đúng rồi! Cố gắng ở câu sau nhé! 💪", ephemeral=True)
        self.stop()

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def button_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, "A")

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
    async def button_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, "B")

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
    async def button_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, "C")

    @discord.ui.button(label="D", style=discord.ButtonStyle.primary)
    async def button_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, "D")

@bot.command()
async def danganh(ctx):
    """Đăng câu hỏi trắc nghiệm tương tác"""
    embed = discord.Embed(
        title="❓ CÂU HỎI TRẮC NGHIỆM HẰNG NGÀY ❓",
        description="Trả lời đúng câu hỏi dưới đây để nhận **10 Cỏ 4 Lá 🍀** nha!\n\n**Câu hỏi:** Đơn vị đo cường độ dòng điện trong hệ SI là gì?\n**A.** Volt (V)\n**B.** Ampere (A)\n**C.** Ohm (Ω)\n**D.** Watt (W)",
        color=discord.Color.blue()
    )
    view = QuizView(correct_option="B", user_id=ctx.author.id)
    await ctx.send(embed=embed, view=view)

# --- 9. 🍀 LỆNH XEM SỐ CỎ 4 LÁ ---
@bot.command()
async def co(ctx):
    """Xem số Cỏ 4 Lá hiện tại của bản thân"""
    clovers = get_clovers(ctx.author.id)
    await ctx.send(f"🍀 {ctx.author.mention} hiện đang có **{clovers} Cỏ 4 Lá** trong ví nha! (⁠≧⁠▽⁠≧⁠)")

# --- RUN BOT ---
keep_alive()

TOKEN = os.environ.get("DISCORD_TOKEN")

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Lỗi: Chưa tìm thấy DISCORD_TOKEN trong phần cài đặt biến môi trường!")
