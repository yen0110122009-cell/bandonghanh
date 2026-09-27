"""Ong & Co 4 La - modular feature."""
from .core import *

def period_range(period):
    now = now_vn()
    end = now
    if period == "ngay":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "tuan":
        monday = now.date() - timedelta(days=now.weekday())
        start = datetime.combine(monday, datetime.min.time(), tzinfo=VN_TZ)
    elif period == "thang":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "nam":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError("period")
    return start.date().isoformat(), end.date().isoformat()

def leaderboard_rows(start_date, end_date):
    conn = db()
    rows = conn.execute("""
        SELECT user_id, SUM(duration) AS total
        FROM daily_study
        WHERE date >= ? AND date <= ?
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT 20
    """, (start_date, end_date)).fetchall()
    conn.close()
    return rows

@bot.command(name="top", aliases=["xephang"])
async def top(ctx, period: str = "ngay"):
    period = period.lower()
    aliases = {"day": "ngay", "week": "tuan", "month": "thang", "year": "nam"}
    period = aliases.get(period, period)
    if period not in ("ngay", "tuan", "thang", "nam"):
        await ctx.send("❌ Chọn `ngay`, `tuan`, `thang` hoặc `nam`.")
        return

    start, end = period_range(period)
    rows = leaderboard_rows(start, end)

    labels = {"ngay": "NGÀY", "tuan": "TUẦN", "thang": "THÁNG", "nam": "NĂM"}
    embed = discord.Embed(
        title=f"🏆 BXH HỌC TẬP — {labels[period]}",
        description=f"📅 Dữ liệu: **{start} → {end}**\nNguồn: `daily_study`",
        color=discord.Color.gold()
    )

    if not rows:
        embed.add_field(name="Chưa có dữ liệu", value="Hãy bắt đầu học để lên BXH! 🌸", inline=False)
    else:
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, seconds) in enumerate(rows, 1):
            member = ctx.guild.get_member(uid)
            name = member.display_name if member else f"User {uid}"
            prefix = medals[i - 1] if i <= 3 else f"`#{i}`"
            lines.append(f"{prefix} **{name}** — {format_duration(seconds)}")
        embed.add_field(name="📚 Thời gian học", value="\n".join(lines), inline=False)

    await ctx.send(embed=embed)

# ============================================================
# 📊 BÁO CÁO
# ============================================================

@bot.command()
async def baocao(ctx, mode="ngay", *, target=None):
    mode = mode.lower()
    if mode in ("tuan", "thang", "nam"):
        start, end = period_range(mode)
        conn = db()
        rows = conn.execute("""
            SELECT subject, SUM(duration)
            FROM daily_study
            WHERE user_id = ? AND date >= ? AND date <= ?
            GROUP BY subject ORDER BY SUM(duration) DESC
        """, (ctx.author.id, start, end)).fetchall()
        conn.close()
        total = sum(r[1] for r in rows)
        desc = f"📅 **{start} → {end}**\n⏱️ **Tổng:** {format_duration(total)}\n\n"
        desc += "\n".join(f"• **{sub}** — {format_duration(sec)}" for sub, sec in rows) or "Chưa có dữ liệu."
        await ctx.send(embed=discord.Embed(
            title=f"📊 BÁO CÁO {mode.upper()}",
            description=desc,
            color=discord.Color.teal()
        ))
        return

    today = date_key()
    conn = db()
    rows = conn.execute("""
        SELECT subject, duration FROM daily_study
        WHERE user_id = ? AND date = ?
        ORDER BY duration DESC
    """, (ctx.author.id, today)).fetchall()
    conn.close()
    total = sum(r[1] for r in rows)
    desc = f"📅 **{today}**\n⏱️ **Tổng:** {format_duration(total)}\n\n"
    desc += "\n".join(f"• **{sub}** — {format_duration(sec)}" for sub, sec in rows) or "Chưa có dữ liệu."
    await ctx.send(embed=discord.Embed(
        title=f"📊 BÁO CÁO CỦA {ctx.author.display_name}",
        description=desc,
        color=discord.Color.teal()
    ))

# ============================================================
# 🎓 SUBJECT SELECT — dùng command đơn giản để tránh view cũ lỗi
# ============================================================

