"""Ong & Co 4 La - modular feature."""
from .core import *
from .reminders import parse_duration_seconds
from .rooms import temporary_rename_channel

@bot.command()
async def shop(ctx):
    embed = discord.Embed(
        title="🛒 SHOP CỎ 4 LÁ",
        description="Tất cả vật phẩm đều mua từ đây. Tỷ lệ Hộp Quà Nhân Phẩm không hiển thị.",
        color=discord.Color.green()
    )
    for code, item in SHOP_ITEMS.items():
        embed.add_field(
            name=f"`{code}` • {item['name']} — {item['price']} 🍀",
            value=item["desc"],
            inline=False
        )
    embed.set_footer(text="Mua: !mua <mã> • Túi: !tuido")
    await ctx.send(embed=embed)

@bot.command()
async def tuido(ctx):
    rows = get_inventory(ctx.author.id)
    embed = discord.Embed(
        title=f"🎒 TÚI ĐỒ CỦA {ctx.author.display_name}",
        color=discord.Color.gold()
    )
    if not rows:
        embed.description = "🎒 Túi đồ hiện đang trống."
    else:
        embed.description = "\n".join(f"• {name}: **{amount}**" for name, amount in rows)
    embed.add_field(name="🍀 Số dư", value=f"**{get_clovers(ctx.author.id)} 🍀**", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def mua(ctx, code: str, *args):
    code = code.lower().strip()
    if code not in SHOP_ITEMS:
        await ctx.send("❌ Mã không tồn tại. Gõ `!shop` để xem cửa hàng.")
        return

    # Gift: dùng trực tiếp khi mua.
    if code == "gift":
        if len(args) < 2 or not isinstance(ctx.message.mentions[0] if ctx.message.mentions else None, discord.Member):
            await ctx.send("🤝 Dùng: `!mua gift @Ong 50 Chúc bạn học tốt nhé`")
            return
        receiver = ctx.message.mentions[0]
        if receiver.bot or receiver.id == ctx.author.id:
            await ctx.send("❌ Không thể tặng cho chính mình hoặc bot.")
            return

        # Loại mention khỏi phần args nếu có.
        amount = None
        raw = " ".join(args)
        nums = re.findall(r"\b\d+\b", raw)
        if not nums:
            await ctx.send("❌ Bạn cần ghi số Cỏ muốn tặng.")
            return
        amount = int(nums[0])
        if amount <= 0:
            await ctx.send("❌ Số Cỏ phải lớn hơn 0.")
            return
        if get_clovers(ctx.author.id) < amount + 10:
            await ctx.send(f"❌ Cần **{amount + 10} 🍀** gồm tiền tặng + phí 10 🍀.")
            return

        message = raw
        message = re.sub(r"<@!?\d+>", "", message).strip()
        message = re.sub(r"\b\d+\b", "", message).strip()
        if not message:
            message = "Chúc bạn học tốt nhé! 🌸"

        add_clovers(ctx.author.id, -(amount + 10))
        add_clovers(receiver.id, amount)

        conn = db()
        conn.execute("""
            INSERT INTO gift_transactions(
                guild_id, sender_id, receiver_id, amount, message, anonymous, created_at
            ) VALUES (?, ?, ?, ?, ?, 0, ?)
        """, (ctx.guild.id, ctx.author.id, receiver.id, amount, message, iso_vn()))
        conn.commit()
        conn.close()

        await ctx.send(
            f"🤝 {ctx.author.mention} đã tặng **{amount} 🍀** cho {receiver.mention}.\n"
            f"💸 Phí giao dịch: **10 🍀**\n"
            f"💌 Lời nhắn: {message}"
        )
        return

    item = SHOP_ITEMS[code]
    price = item["price"]

    if get_clovers(ctx.author.id) < price:
        await ctx.send(f"❌ Không đủ Cỏ. Bạn có **{get_clovers(ctx.author.id)} 🍀**, cần **{price} 🍀**.")
        return

    add_clovers(ctx.author.id, -price)

    if code == "hopqua":
        reward = mystery_reward()
        if reward["type"] == "message":
            result = f"🌸 **Lời chúc học tốt!**\n{reward['text']}"
        elif reward["type"] == "clover":
            new_balance = add_clovers(ctx.author.id, reward["amount"])
            result = f"🍀 Bạn nhận **+{reward['amount']} Cỏ**.\n💰 Số dư: **{new_balance} 🍀**"
        elif reward["type"] == "item":
            add_item(ctx.author.id, reward["item"], 1)
            result = f"🎫 Bạn nhận **{reward['item']}** và vật phẩm đã vào `!tuido`."
        else:
            # Freeze tự động kích hoạt: bảo vệ một ngày nghỉ.
            expires = today_vn() + timedelta(days=1)
            conn = db()
            conn.execute("""
                INSERT INTO active_freeze(user_id, expires_date)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET expires_date=excluded.expires_date
            """, (ctx.author.id, expires.isoformat()))
            conn.commit()
            conn.close()
            result = "❄️ **Thẻ Đóng Băng Streak đã tự động kích hoạt!**"

        await ctx.send(
            f"🎁 **HỘP QUÀ NHÂN PHẨM**\n\n"
            f"💸 Đã trừ: **50 🍀**\n"
            f"🎉 Kết quả:\n{result}"
        )
        return

    if code == "freeze":
        # Mua trực tiếp cũng tự kích hoạt.
        expires = today_vn() + timedelta(days=1)
        conn = db()
        conn.execute("""
            INSERT INTO active_freeze(user_id, expires_date)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET expires_date=excluded.expires_date
        """, (ctx.author.id, expires.isoformat()))
        conn.commit()
        conn.close()
        await ctx.send("❄️ Thẻ Đóng Băng Streak đã **tự động kích hoạt**.")
        return

    # Các món còn lại vào túi.
    add_item(ctx.author.id, item["name"], 1)
    await ctx.send(
        f"🎉 Mua thành công **{item['name']}**!\n"
        f"💸 Đã trừ **{price} 🍀**\n"
        f"🎒 Vật phẩm đã vào `!tuido`."
    )

# ============================================================
# 🎒 DÙNG VẬT PHẨM
# ============================================================

@bot.command()
async def dung(ctx, item: str, *args):
    key = item.lower().strip()

    if key in ("x2", "nangluong"):
        name = "⚡ Thẻ X2 Năng Lượng"
        if not remove_item(ctx.author.id, name):
            await ctx.send("❌ Bạn không có Thẻ X2 trong túi.")
            return
        expires = now_vn() + timedelta(hours=2)
        conn = db()
        conn.execute("""
            INSERT INTO active_x2(user_id, expires_at)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET expires_at=excluded.expires_at
        """, (ctx.author.id, expires.isoformat()))
        conn.commit()
        conn.close()
        await ctx.send("⚡ **X2 Năng Lượng đã kích hoạt trong 2 giờ!**\n📚 4,5 phút học = 1 🍀.")
        return

    if key in ("giaman", "giamanphat", "giam_an"):
        name = "🛡️ Thẻ Giảm Án Kỷ Luật"
        if not remove_item(ctx.author.id, name):
            await ctx.send("❌ Bạn không có Thẻ Giảm Án Kỷ Luật.")
            return

        conn = db()
        row = conn.execute("""
            SELECT level FROM user_punishments
            WHERE guild_id = ? AND user_id = ? AND active = 1
        """, (ctx.guild.id, ctx.author.id)).fetchone()

        if not row:
            conn.close()
            add_item(ctx.author.id, name, 1)
            await ctx.send("❌ Bạn hiện không có án đang hoạt động.")
            return

        old_level = int(row[0])
        new_level = max(1, old_level - 1)
        conn.execute("""
            UPDATE user_punishments SET level = ?
            WHERE guild_id = ? AND user_id = ? AND active = 1
        """, (str(new_level), ctx.guild.id, ctx.author.id))
        conn.commit()
        conn.close()

        await ctx.send(f"🛡️ Đã giảm mức phạt từ **Mức {old_level} → Mức {new_level}**.")
        return

    if key in ("mienphat", "vephat"):
        name = "🎫 Vé Miễn Phạt"
        if not remove_item(ctx.author.id, name):
            await ctx.send("❌ Bạn không có Vé Miễn Phạt.")
            return

        conn = db()
        row = conn.execute("""
            SELECT level FROM user_punishments
            WHERE guild_id = ? AND user_id = ? AND active = 1
        """, (ctx.guild.id, ctx.author.id)).fetchone()
        if not row:
            conn.close()
            add_item(ctx.author.id, name, 1)
            await ctx.send("❌ Bạn hiện không có án đang hoạt động.")
            return

        conn.execute("""
            UPDATE user_punishments SET active = 0
            WHERE guild_id = ? AND user_id = ?
        """, (ctx.guild.id, ctx.author.id))
        conn.commit()
        conn.close()

        role = discord.utils.get(ctx.guild.roles, name=DISCIPLINE_ROLE)
        if role and role in ctx.author.roles:
            await ctx.author.remove_roles(role, reason="Dùng Vé Miễn Phạt")
        await ctx.send("🎫 Vé Miễn Phạt đã được dùng. Án hiện tại đã được xóa.")
        return

    if key in ("doiten", "room", "roommaster"):
        if not args:
            await ctx.send(
                "👑 Dùng: `!dung doiten Tên mới | 2h | Lý do`\n"
                "Ví dụ: `!dung doiten 🔥・Cày Deadline | 2h | Ôn thi`"
            )
            return

        if not isinstance(ctx.author.voice.channel if ctx.author.voice else None, discord.VoiceChannel):
            await ctx.send("❌ Bạn phải đang ở Voice Channel để đổi tên phòng.")
            return

        name = "👑 Thẻ Đổi Tên Phòng Học"
        if not remove_item(ctx.author.id, name):
            await ctx.send("❌ Bạn không có Thẻ Đổi Tên Phòng Học.")
            return

        raw = " ".join(args)
        parts = [p.strip() for p in raw.split("|")]
        new_name = parts[0]
        duration_text = parts[1] if len(parts) > 1 else "2h"
        reason = parts[2] if len(parts) > 2 else "Đổi tên phòng học"

        seconds = parse_duration_seconds(duration_text)
        if seconds <= 0:
            add_item(ctx.author.id, name, 1)
            await ctx.send("❌ Thời gian không hợp lệ.")
            return

        channel = ctx.author.voice.channel
        await temporary_rename_channel(channel, new_name, seconds, reason, ctx.author)
        await ctx.send(
            f"👑 Đã đổi tên **{channel.name}** → **{new_name}**\n"
            f"⏱️ Thời hạn: **{duration_text}**\n"
            f"📝 Lý do: **{reason}**"
        )
        return

    await ctx.send("❌ Vật phẩm chưa đúng. Ví dụ: `!dung x2`, `!dung giaman`, `!dung doiten ...`.")

# ============================================================
# ⏰ REMINDERS
# ============================================================

