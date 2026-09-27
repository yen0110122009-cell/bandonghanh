"""Ong & Co 4 La - modular feature."""
from .core import *
from .reminders import parse_duration_seconds

@bot.command()
async def xem_phat(ctx):
    conn = db()
    rows = conn.execute("""
        SELECT level, clovers_deduct, description
        FROM dynamic_punishments ORDER BY CAST(level AS INTEGER)
    """).fetchall()
    conn.close()
    embed = discord.Embed(title="📜 CÁC MỨC KỶ LUẬT", color=discord.Color.dark_orange())
    for level, cost, desc in rows:
        embed.add_field(name=f"Mức {level} • -{cost} 🍀", value=desc, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def them_phat(ctx, muc_do: str, so_co_tru: int, *, noi_dung_phat: str):
    if not await require_special(ctx):
        return
    if so_co_tru < 0:
        await ctx.send("❌ Số Cỏ trừ không thể âm.")
        return
    conn = db()
    conn.execute("""
        INSERT INTO dynamic_punishments(level, clovers_deduct, description)
        VALUES (?, ?, ?)
        ON CONFLICT(level) DO UPDATE SET
            clovers_deduct=excluded.clovers_deduct,
            description=excluded.description
    """, (muc_do, so_co_tru, noi_dung_phat))
    conn.commit()
    conn.close()
    await ctx.send(f"✅ Đã thêm/cập nhật Mức {muc_do}.")

async def apply_discipline_permissions(member, active=True):
    role = discord.utils.get(member.guild.roles, name=DISCIPLINE_ROLE)
    if not role:
        role = await ensure_role(member.guild, DISCIPLINE_ROLE, discord.Color.dark_gray())
    if active:
        await member.add_roles(role, reason="Chấp hành kỷ luật")
    else:
        await member.remove_roles(role, reason="Kết thúc kỷ luật")

async def enforce_discipline_channels(guild):
    await ensure_fixed_channels(guild)
    role = discord.utils.get(guild.roles, name=DISCIPLINE_ROLE)
    category = discord.utils.get(guild.categories, name=DISCIPLINE_CATEGORY)
    if not role or not category:
        return

    # Các kênh khác: role phạt chỉ xem, không gửi.
    for channel in guild.channels:
        if channel.category_id == category.id:
            continue
        try:
            await channel.set_permissions(
                role,
                send_messages=False,
                add_reactions=False
            )
        except discord.Forbidden:
            pass

    confession = discord.utils.get(guild.text_channels, name=DISCIPLINE_CHANNEL)
    if confession:
        await confession.set_permissions(
            role,
            view_channel=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
            read_message_history=True
        )

@bot.command()
async def phat(ctx, member: discord.Member, muc_do: str, *, ly_do="Vi phạm nội quy"):
    if not await require_special(ctx):
        return

    conn = db()
    row = conn.execute("""
        SELECT clovers_deduct, description
        FROM dynamic_punishments WHERE level = ?
    """, (muc_do,)).fetchone()
    conn.close()

    if not row:
        await ctx.send("❌ Mức phạt không tồn tại. Dùng `!xem_phat`.")
        return

    cost, description = row
    current_clovers = get_clovers(member.id)
    deducted = min(current_clovers, int(cost))
    if deducted:
        add_clovers(member.id, -deducted)
    await apply_discipline_permissions(member, True)

    conn = db()
    conn.execute("""
        INSERT INTO user_punishments(
            guild_id, user_id, level, reason, active, created_at
        ) VALUES (?, ?, ?, ?, 1, ?)
        ON CONFLICT(guild_id, user_id)
        DO UPDATE SET level=excluded.level, reason=excluded.reason,
                      active=1, created_at=excluded.created_at
    """, (ctx.guild.id, member.id, muc_do, ly_do, iso_vn()))
    conn.commit()
    conn.close()

    await enforce_discipline_channels(ctx.guild)

    channel = discord.utils.get(ctx.guild.text_channels, name=DISCIPLINE_LOG_CHANNEL)
    if channel:
        await channel.send(
            f"🚨 {member.mention} bị áp dụng **Mức {muc_do}**.\n"
            f"📝 Lý do: {ly_do}\n"
            f"⚖️ Hình thức: {description}\n"
            f"🍀 Cỏ trừ: **-{deducted}** (mức yêu cầu: {cost})\n"
            f"🔒 Role: `{DISCIPLINE_ROLE}`\n"
            f"📜 Nộp tường trình tại {discord.utils.get(ctx.guild.text_channels, name=DISCIPLINE_CHANNEL).mention if discord.utils.get(ctx.guild.text_channels, name=DISCIPLINE_CHANNEL) else 'kênh tự thú'}"
        )
    await ctx.send(f"🚨 Đã áp dụng Mức {muc_do} cho {member.mention}.")

@bot.command()
async def duyet(ctx, member: discord.Member, *, loi_nhan="Đã hoàn thành tốt hình phạt!"):
    if not await require_special(ctx):
        return
    await apply_discipline_permissions(member, False)

    conn = db()
    conn.execute("""
        UPDATE user_punishments SET active = 0
        WHERE guild_id = ? AND user_id = ?
    """, (ctx.guild.id, member.id))
    conn.commit()
    conn.close()

    await ctx.send(
        f"🔓 Đã kết thúc kỷ luật cho {member.mention}.\n"
        f"💬 {loi_nhan}"
    )

@bot.command(aliases=["giaitrinh", "trinhbay", "duyetphep", "phep"])
async def giai_trinh(ctx, *, noi_dung: str = None):
    """Một luồng duy nhất cho giải trình/đơn phép: nội dung + chứng cứ gửi vào kênh nội bộ."""
    if not noi_dung or len(noi_dung.strip()) < 5:
        await ctx.send(
            "❌ Hãy gửi giải trình/đơn phép rõ ràng, kèm chứng cứ nếu có. "
            "Ví dụ: `!giai_trinh Em xin phép vì ...` rồi gửi ảnh/file chứng minh."
        )
        return

    conn = db()
    cur = conn.execute("""
        INSERT INTO discipline_requests(
            guild_id, user_id, request_type, content, status, created_at
        ) VALUES (?, ?, 'explanation', ?, 'pending', ?)
    """, (ctx.guild.id, ctx.author.id, noi_dung.strip(), iso_vn()))
    request_id = cur.lastrowid
    conn.commit()
    conn.close()

    log = discord.utils.get(ctx.guild.text_channels, name=DISCIPLINE_LOG_CHANNEL)
    if log:
        owner = discord.utils.get(ctx.guild.roles, name=OWNER_ROLE)
        bql = discord.utils.get(ctx.guild.roles, name=BQL_ROLE)
        mentions = " ".join(r.mention for r in (owner, bql) if r)

        embed = discord.Embed(
            title=f"📄 GIẢI TRÌNH / DUYỆT PHÉP #{request_id}",
            description=(
                f"👤 Thành viên: {ctx.author.mention}\n"
                f"🆔 ID: `{ctx.author.id}`\n\n"
                f"📝 Nội dung:\n{noi_dung.strip()}\n\n"
                "📎 Chứng cứ: xem tệp/hình ảnh được thành viên gửi kèm nếu có.\n\n"
                "⚖️ BQL/Người Sáng Lập xem xét và quyết định."
            ),
            color=discord.Color.blue()
        )
        await log.send(
            content=mentions,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True)
        )

        # Nếu người dùng gửi ảnh/file cùng command, chuyển luôn chứng cứ sang kênh nội bộ.
        if ctx.message.attachments:
            for attachment in ctx.message.attachments[:10]:
                try:
                    await log.send(
                        f"📎 Chứng cứ của {ctx.author.mention} — hồ sơ **#{request_id}**: "
                        f"{attachment.url}",
                        allowed_mentions=discord.AllowedMentions(users=True)
                    )
                except discord.HTTPException:
                    pass

    await ctx.send(
        f"📄 Đã ghi nhận **giải trình/duyệt phép #{request_id}**.\n"
        "BQL/Người Sáng Lập sẽ xem nội dung và chứng cứ tại kênh nội bộ."
    )


@bot.command(aliases=["danhsachgiaitrinh", "xemgiaitrinh"])
async def xem_giai_trinh(ctx, trang_thai: str = "pending"):
    if not await require_special(ctx):
        return
    status = trang_thai.lower()
    if status not in ("pending", "approved", "rejected"):
        await ctx.send("❌ Trạng thái: `pending`, `approved`, `rejected`.")
        return

    conn = db()
    rows = conn.execute("""
        SELECT id, user_id, request_type, content, created_at
        FROM discipline_requests
        WHERE guild_id = ? AND status = ?
        ORDER BY id DESC LIMIT 15
    """, (ctx.guild.id, status)).fetchall()
    conn.close()

    if not rows:
        await ctx.send(f"📭 Không có yêu cầu `{status}`.")
        return

    output = []
    for rid, uid, rtype, content, created in rows:
        icon = "📄" if rtype == "explanation" else "⚖️"
        output.append(f"{icon} **#{rid}** <@{uid}> — {content[:180]}\n`{created}`")
    await ctx.send("\n\n".join(output))


@bot.command(aliases=["duyetgiaitrinh", "duyetxet"])
async def duyet_suy_xet(ctx, request_id: int, ket_qua: str = "chapnhan", *, ghi_chu: str = "BQL đã xem xét"):
    if not await require_special(ctx):
        return

    normalized = ket_qua.lower()
    if normalized not in ("chapnhan", "tu_choi", "tuchoi", "tangphat", "giamphat"):
        await ctx.send("❌ Kết quả: `chapnhan`, `tu_choi`, `giamphat`, hoặc `tangphat`.")
        return

    conn = db()
    row = conn.execute("""
        SELECT user_id, request_type, content, status
        FROM discipline_requests
        WHERE id = ? AND guild_id = ?
    """, (request_id, ctx.guild.id)).fetchone()
    if not row:
        conn.close()
        await ctx.send("❌ Không tìm thấy yêu cầu.")
        return
    if row[3] != "pending":
        conn.close()
        await ctx.send("❌ Yêu cầu này đã được xử lý.")
        return

    new_status = "approved" if normalized in ("chapnhan", "giamphat") else "rejected"
    conn.execute("""
        UPDATE discipline_requests
        SET status = ?, reviewer_id = ?, reviewer_note = ?, reviewed_at = ?
        WHERE id = ? AND guild_id = ?
    """, (new_status, ctx.author.id, ghi_chu, iso_vn(), request_id, ctx.guild.id))
    conn.commit()
    conn.close()

    if normalized == "giamphat":
        conn = db()
        punishment = conn.execute("""
            SELECT level FROM user_punishments
            WHERE guild_id = ? AND user_id = ? AND active = 1
        """, (ctx.guild.id, row[0])).fetchone()
        if punishment:
            old_level = int(punishment[0])
            new_level = max(1, old_level - 1)
            conn.execute("""
                UPDATE user_punishments SET level = ?
                WHERE guild_id = ? AND user_id = ? AND active = 1
            """, (str(new_level), ctx.guild.id, row[0]))
            ghi_chu = f"{ghi_chu} | Giảm Mức {old_level} → Mức {new_level}"
        conn.commit()
        conn.close()

    await ctx.send(
        f"⚖️ Đã xử lý hồ sơ **giải trình/duyệt phép #{request_id}** của <@{row[0]}>: **{normalized}**.\n"
        f"📝 {ghi_chu}"
    )


@bot.command(aliases=["giam_phat", "giamphat"])
async def giam_an(ctx, member: discord.Member, *, ly_do: str = "Được suy xét giảm án"):
    if not await require_special(ctx):
        return

    conn = db()
    row = conn.execute("""
        SELECT level FROM user_punishments
        WHERE guild_id = ? AND user_id = ? AND active = 1
    """, (ctx.guild.id, member.id)).fetchone()
    if not row:
        conn.close()
        await ctx.send("❌ Thành viên này không có án đang hoạt động.")
        return

    old_level = int(row[0])
    new_level = max(1, old_level - 1)
    conn.execute("""
        UPDATE user_punishments SET level = ?, reason = reason || ?
        WHERE guild_id = ? AND user_id = ? AND active = 1
    """, (str(new_level), f" | Giảm án: {ly_do}", ctx.guild.id, member.id))
    conn.commit()
    conn.close()
    await ctx.send(f"⚖️ {member.mention} được **giảm Mức {old_level} → Mức {new_level}**.\n📝 {ly_do}")


@bot.command(aliases=["tang_phat", "tangphat"])
async def tang_an(ctx, member: discord.Member, muc_do: str, *, ly_do: str = "Tái phạm/không đủ căn cứ khoan hồng"):
    if not await require_special(ctx):
        return

    conn = db()
    row = conn.execute("SELECT description FROM dynamic_punishments WHERE level = ?", (muc_do,)).fetchone()
    active = conn.execute("""
        SELECT 1 FROM user_punishments
        WHERE guild_id = ? AND user_id = ? AND active = 1
    """, (ctx.guild.id, member.id)).fetchone()
    if not row or not active:
        conn.close()
        await ctx.send("❌ Cần có mức phạt hợp lệ và thành viên đang có án.")
        return

    conn.execute("""
        UPDATE user_punishments SET level = ?, reason = reason || ?
        WHERE guild_id = ? AND user_id = ? AND active = 1
    """, (muc_do, f" | Tăng án: {ly_do}", ctx.guild.id, member.id))
    conn.commit()
    conn.close()
    await ctx.send(
        f"⚠️ {member.mention} được điều chỉnh lên **Mức {muc_do}**.\n"
        f"📝 {ly_do}\n"
        f"⚖️ Hình thức: {row[0]}"
    )


@bot.command(aliases=["taophat", "taomucphat"])
async def tao_phat(ctx, muc_do: str, so_co_tru: int, *, hinh_thuc: str):
    if not await require_special(ctx):
        return
    if so_co_tru < 0:
        await ctx.send("❌ Số Cỏ trừ không thể âm.")
        return

    conn = db()
    conn.execute("""
        INSERT INTO dynamic_punishments(level, clovers_deduct, description)
        VALUES (?, ?, ?)
        ON CONFLICT(level) DO UPDATE SET
            clovers_deduct=excluded.clovers_deduct,
            description=excluded.description
    """, (muc_do, so_co_tru, hinh_thuc.strip()))
    conn.commit()
    conn.close()
    await ctx.send(
        f"✅ Đã tạo/cập nhật **Mức {muc_do}**.\n"
        f"🍀 Trừ: **{so_co_tru}**\n"
        f"⚖️ Hình thức: {hinh_thuc.strip()}"
    )


# ============================================================
# 👮 ADMIN COMMANDS
# ============================================================

@bot.command()
async def taorole(ctx, *, name: str):
    if not await require_special(ctx):
        return
    role = await ensure_role(ctx.guild, name.strip())
    await ctx.send(f"✅ Đã tạo role {role.mention}.")

@bot.command()
async def xoarole(ctx, *, name: str):
    if not await require_special(ctx):
        return
    role = discord.utils.get(ctx.guild.roles, name=name.strip())
    if not role:
        await ctx.send("❌ Không tìm thấy role.")
        return
    if role >= ctx.guild.me.top_role:
        await ctx.send("❌ Bot không thể xóa role cao hơn hoặc ngang role cao nhất của bot.")
        return
    await role.delete(reason=f"Yêu cầu bởi {ctx.author}")
    await ctx.send(f"🗑️ Đã xóa role `{name}`.")

@bot.command()
async def themrole(ctx, member: discord.Member, *, role_name: str):
    if not await require_special(ctx):
        return
    role = discord.utils.get(ctx.guild.roles, name=role_name.strip())
    if not role:
        role = await ensure_role(ctx.guild, role_name.strip())
    if role >= ctx.guild.me.top_role:
        await ctx.send("❌ Role nằm trên role bot.")
        return
    await member.add_roles(role, reason=f"Yêu cầu bởi {ctx.author}")
    await ctx.send(f"✅ Đã thêm `{role.name}` cho {member.mention}.")

@bot.command()
async def kick(ctx, member: discord.Member, *, reason="Không nêu lý do"):
    if not await require_special(ctx):
        return
    await member.kick(reason=reason)
    await ctx.send(f"👢 Đã kick {member.mention}. Lý do: {reason}")

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="Không nêu lý do"):
    if not await require_special(ctx):
        return
    await member.ban(reason=reason, delete_message_days=0)
    await ctx.send(f"🔨 Đã ban {member.mention}. Lý do: {reason}")

@bot.command()
async def unban(ctx, user_id: int):
    if not await require_special(ctx):
        return
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=f"Yêu cầu bởi {ctx.author}")
        await ctx.send(f"🔓 Đã unban `{user}`.")
    except discord.NotFound:
        await ctx.send("❌ Không tìm thấy user trong danh sách ban.")

@bot.command()
async def camngon(ctx, member: discord.Member, duration: str = "10m", *, reason="Không nêu lý do"):
    if not await require_special(ctx):
        return
    seconds = parse_duration_seconds(duration)
    if seconds <= 0:
        await ctx.send("❌ Ví dụ: `!camngon @Ong 30m Lý do`.")
        return
    await member.timeout(timedelta(seconds=seconds), reason=reason)
    await ctx.send(f"🔇 {member.mention} bị cấm ngôn trong **{duration}**. Lý do: {reason}")

@bot.command()
async def bo_camngon(ctx, member: discord.Member):
    if not await require_special(ctx):
        return
    await member.timeout(None, reason=f"Gỡ cấm ngôn bởi {ctx.author}")
    await ctx.send(f"🔊 Đã gỡ cấm ngôn cho {member.mention}.")

# ============================================================
# 🎧 ROOMS — TỰ TẠO, TỰ CHỌN QUYỀN RIÊNG TƯ
# ============================================================

