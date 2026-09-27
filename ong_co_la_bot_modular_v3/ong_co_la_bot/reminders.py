"""Ong & Co 4 La - modular feature."""
from .core import *

def parse_duration_seconds(text):
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(s|giây|m|phút|h|giờ|d|ngày)\s*", text.lower())
    if not m:
        return 0
    value = float(m.group(1))
    unit = m.group(2)
    if unit in ("s", "giây"):
        return int(value)
    if unit in ("m", "phút"):
        return int(value * 60)
    if unit in ("h", "giờ"):
        return int(value * 3600)
    return int(value * 86400)

def insert_reminder(user_id, guild_id, when, content):
    conn = db()
    cur = conn.execute("""
        INSERT INTO reminders(user_id, guild_id, reminder_time, content, completed, created_at)
        VALUES (?, ?, ?, ?, 0, ?)
    """, (user_id, guild_id, when.isoformat(), content, iso_vn()))
    reminder_id = cur.lastrowid
    conn.commit()
    conn.close()
    return reminder_id

@bot.command()
async def nhacnho(ctx, action=None, gio_or_id=None, *, noi_dung=None):
    if action and action.lower() == "xem":
        conn = db()
        rows = conn.execute("""
            SELECT id, reminder_time, content
            FROM reminders
            WHERE user_id = ? AND guild_id = ? AND completed = 0
            ORDER BY reminder_time
        """, (ctx.author.id, ctx.guild.id)).fetchall()
        conn.close()

        embed = discord.Embed(title="⏰ NHẮC NHỞ CỦA BẠN", color=discord.Color.gold())
        if not rows:
            embed.description = "Bạn chưa có nhắc nhở nào đang chờ."
        else:
            for rid, raw_dt, content in rows:
                try:
                    dt = datetime.fromisoformat(raw_dt).astimezone(VN_TZ)
                    display = dt.strftime("%d/%m/%Y • %H:%M")
                except Exception:
                    display = raw_dt
                embed.add_field(
                    name=f"⏰ #{rid} • {display}",
                    value=f"{content}\n🗑️ `!nhacnho xoa {rid}`",
                    inline=False
                )
        await ctx.send(embed=embed)
        return

    if action and action.lower() == "xoa":
        try:
            rid = int(gio_or_id)
        except Exception:
            await ctx.send("❌ Dùng `!nhacnho xoa ID`.")
            return

        conn = db()
        row = conn.execute("""
            SELECT content FROM reminders
            WHERE id = ? AND user_id = ? AND guild_id = ? AND completed = 0
        """, (rid, ctx.author.id, ctx.guild.id)).fetchone()
        if not row:
            conn.close()
            await ctx.send("❌ Không tìm thấy nhắc nhở của bạn.")
            return
        conn.execute("UPDATE reminders SET completed = 1 WHERE id = ?", (rid,))
        conn.commit()
        conn.close()
        await ctx.send(f"🗑️ Đã xóa nhắc nhở **#{rid}**.")
        return

    # Hỗ trợ:
    # !nhacnho 28/09/2026 20:30 Ôn Toán
    # !nhacnho 30 phút nữa Ôn bài
    if not action:
        await ctx.send(
            "⏰ Cách dùng:\n"
            "`!nhacnho 28/09/2026 20:30 Ôn Toán`\n"
            "`!nhacnho 30 phút nữa Ôn bài`\n"
            "`!nhacnho xem`\n"
            "`!nhacnho xoa ID`\n\n"
            "Có thể gửi **nhiều dòng lệnh !nhacnho** trong một tin nhắn."
        )
        return

    content = noi_dung
    when = None

    # Dạng ngày + giờ.
    if gio_or_id and content:
        try:
            when = parse_vn_datetime(f"{action} {gio_or_id}")
        except ValueError:
            when = None

    # Dạng tương đối: action=30, gio_or_id=phút, content=...
    if when is None and gio_or_id and content:
        sec = parse_duration_seconds(f"{action} {gio_or_id}")
        if sec > 0:
            when = now_vn() + timedelta(seconds=sec)

    if when is None or not content:
        await ctx.send("❌ Không đọc được thời gian. Ví dụ `!nhacnho 30 phút nữa Ôn Toán`.")
        return

    if when <= now_vn():
        await ctx.send("⚠️ Thời gian nhắc phải ở tương lai.")
        return

    rid = insert_reminder(ctx.author.id, ctx.guild.id, when, content)
    await ctx.send(
        f"⏰ Đã đặt **#{rid}**: **{when.strftime('%d/%m/%Y %H:%M')}** — {content}"
    )

@tasks.loop(seconds=5, reconnect=True)
async def reminder_loop():
    # Vòng lặp được thiết kế để khôi phục sau reconnect Discord.
    if not bot.is_ready():
        return

    conn = None
    try:
        conn = db()
        rows = conn.execute("""
            SELECT id, user_id, guild_id, reminder_time, content
            FROM reminders
            WHERE completed = 0
            ORDER BY id
        """).fetchall()

        for rid, user_id, guild_id, raw_dt, content in rows:
            try:
                when = datetime.fromisoformat(raw_dt)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=VN_TZ)
            except Exception:
                continue

            if when > now_vn():
                continue

            guild = bot.get_guild(guild_id)
            member = guild.get_member(user_id) if guild else None
            delivered = False

            if member:
                try:
                    await member.send(
                        f"⏰ **ĐẾN GIỜ NHẮC NHỞ RỒI!**\n"
                        f"📝 {content}\n"
                        f"🕐 {when.astimezone(VN_TZ).strftime('%d/%m/%Y %H:%M')}"
                    )
                    delivered = True
                except discord.Forbidden:
                    pass
                except discord.HTTPException as exc:
                    print(f"[REMINDER DM ERROR] {exc!r}")

            if not delivered and guild:
                channel = discord.utils.get(guild.text_channels, name="🌸·chung")
                if channel and member:
                    try:
                        await channel.send(
                            f"⏰ {member.mention} **đến giờ nhắc nhở:** {content}"
                        )
                        delivered = True
                    except discord.Forbidden:
                        pass
                    except discord.HTTPException as exc:
                        print(f"[REMINDER CHANNEL ERROR] {exc!r}")

            if delivered:
                conn.execute(
                    "UPDATE reminders SET completed = 1 WHERE id = ?", (rid,)
                )

        conn.commit()
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        # Một lỗi DB/API không được phép làm chết vòng lặp nhắc nhở vĩnh viễn.
        print(f"[REMINDER LOOP ERROR] {exc!r}")
    finally:
        if conn is not None:
            conn.close()

@reminder_loop.before_loop
async def before_reminder_loop():
    await bot.wait_until_ready()


# ============================================================
# 🏆 LEADERBOARD
# ============================================================

