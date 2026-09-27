"""Ong & Co 4 La - modular feature."""
from .core import *
from .reminders import parse_duration_seconds
from .study import finish_session

def room_privacy_overwrites(guild, owner, invited_members=None, public=False):
    invited_members = invited_members or []
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=public,
            connect=public,
            speak=public
        ),
        owner: discord.PermissionOverwrite(
            view_channel=True, connect=True, speak=True,
            manage_channels=True, move_members=True
        )
    }
    for member in invited_members:
        # Lời mời chưa được chấp nhận -> chưa được vào phòng.
        overwrites[member] = discord.PermissionOverwrite(
            view_channel=False, connect=False, speak=False
        )
    # BQL + Người sáng lập luôn quản lý được.
    for role_name in (OWNER_ROLE, BQL_ROLE):
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, connect=True, speak=True, manage_channels=True
            )
    return overwrites

@bot.command()
async def taophong(ctx, *, spec: str = None):
    if not spec:
        await ctx.send(
            "🎧 Dùng:\n"
            "`!taophong Tên phòng | 2h | rieng`\n"
            "`!taophong Tên phòng | 3h | moi`\n"
            "`!taophong Tên phòng | 2h | @Ong1 @Ong2`"
        )
        return

    parts = [p.strip() for p in spec.split("|")]
    name = parts[0][:90]
    duration_text = parts[1] if len(parts) > 1 else "2h"
    privacy_text = parts[2].lower() if len(parts) > 2 else "rieng"
    seconds = parse_duration_seconds(duration_text)
    if seconds <= 0:
        await ctx.send("❌ Thời hạn không hợp lệ.")
        return

    _, _, _, _, _, room_cat = await ensure_fixed_channels(ctx.guild)

    invited = list(ctx.message.mentions)
    public = privacy_text in ("mo", "moi", "public", "tatca", "tất cả")

    # Nếu privacy là riêng và không mention ai -> chỉ chủ phòng.
    overwrites = room_privacy_overwrites(ctx.guild, ctx.author, invited, public=public)
    channel = await ctx.guild.create_voice_channel(
        name=name,
        category=room_cat,
        overwrites=overwrites,
        reason=f"Phòng tự tạo bởi {ctx.author}"
    )

    expires = now_vn() + timedelta(seconds=seconds)
    conn = db()
    conn.execute("""
        INSERT INTO room_records(
            channel_id, guild_id, owner_id, original_name,
            expires_at, privacy, active
        ) VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (channel.id, ctx.guild.id, ctx.author.id, name, expires.isoformat(),
          "public" if public else ("invite" if invited else "private")))
    for member in invited:
        conn.execute("""
            INSERT OR IGNORE INTO room_members(channel_id, user_id)
            VALUES (?, ?)
        """, (channel.id, member.id))
    conn.commit()
    conn.close()

    # Lời mời phải được đồng ý: bot gửi nút/command riêng.
    if invited:
        for member in invited:
            try:
                await member.send(
                    f"🎧 {ctx.author.display_name} mời bạn vào phòng **{name}**.\n"
                    f"⏱️ Thời hạn: {duration_text}\n"
                    f"👉 Dùng `!dongyphong {channel.id}` để đồng ý."
                )
            except discord.Forbidden:
                pass

    await ctx.send(
        f"🎧 Đã tạo {channel.mention}\n"
        f"⏱️ Tự động hết hạn sau **{duration_text}**\n"
        f"🔐 Chế độ: **{'Mọi người' if public else ('Mời thành viên' if invited else 'Chỉ mình bạn')}**"
    )

    task = asyncio.create_task(expire_room(channel.id, seconds))
    room_restore_tasks[channel.id] = task

@bot.command()
async def dongyphong(ctx, channel_id: int):
    conn = db()
    row = conn.execute("""
        SELECT guild_id FROM room_records
        WHERE channel_id = ? AND active = 1
    """, (channel_id,)).fetchone()
    if not row:
        conn.close()
        await ctx.send("❌ Phòng không còn hoạt động.")
        return

    allowed = conn.execute("""
        SELECT 1 FROM room_members
        WHERE channel_id = ? AND user_id = ?
    """, (channel_id, ctx.author.id)).fetchone()
    conn.close()

    if not allowed:
        await ctx.send("❌ Bạn không có lời mời vào phòng này.")
        return

    channel = ctx.guild.get_channel(channel_id)
    if not channel:
        await ctx.send("❌ Không tìm thấy phòng.")
        return

    await channel.set_permissions(
        ctx.author,
        view_channel=True, connect=True, speak=True
    )
    await ctx.send(f"🤝 {ctx.author.mention} đã đồng ý tham gia **{channel.name}**.")

@bot.command()
async def mo_phong(ctx, *, name: str = None):
    if not name:
        await ctx.send("❌ Dùng `!mo_phong Tên phòng`.")
        return
    channel = discord.utils.find(
        lambda c: isinstance(c, discord.VoiceChannel) and c.name == name,
        ctx.guild.channels
    )
    if not channel:
        await ctx.send("❌ Không tìm thấy phòng.")
        return
    if not await room_owner_or_special(ctx, channel):
        return
    await channel.edit(
        overwrites=room_privacy_overwrites(ctx.guild, ctx.author, public=True),
        reason=f"Mở phòng bởi {ctx.author}"
    )
    await ctx.send(f"🔓 Đã mở **{channel.name}** cho tất cả thành viên.")

@bot.command()
async def dong_phong(ctx, *, name: str = None):
    if not name:
        await ctx.send("❌ Dùng `!dong_phong Tên phòng`.")
        return
    channel = discord.utils.find(
        lambda c: isinstance(c, discord.VoiceChannel) and c.name == name,
        ctx.guild.channels
    )
    if not channel:
        await ctx.send("❌ Không tìm thấy phòng.")
        return
    if not await room_owner_or_special(ctx, channel):
        return
    overwrites = room_privacy_overwrites(ctx.guild, ctx.author, public=False)
    await channel.edit(overwrites=overwrites, reason=f"Khóa phòng bởi {ctx.author}")
    await ctx.send(f"🔒 Đã khóa **{channel.name}** — chỉ chủ phòng/BQL/người sáng lập truy cập.")

async def room_owner_or_special(ctx, channel):
    if is_owner_or_bql(ctx.author):
        return True
    conn = db()
    row = conn.execute("""
        SELECT owner_id FROM room_records
        WHERE channel_id = ? AND active = 1
    """, (channel.id,)).fetchone()
    conn.close()
    if row and row[0] == ctx.author.id:
        return True
    await ctx.send("🔒 Bạn không phải chủ phòng và không có đặc quyền.")
    return False

async def close_temporary_room(channel_id, reason="Phòng tự tạo hết thời hạn"):
    conn = db()
    row = conn.execute("""
        SELECT privacy, original_name FROM room_records
        WHERE channel_id = ? AND active = 1
    """, (channel_id,)).fetchone()
    conn.close()

    channel = bot.get_channel(channel_id)
    if channel:
        try:
            if row and row[0] == "rename":
                await channel.edit(name=row[1], reason=reason)
            else:
                # Chốt giờ học trước khi xóa phòng để thành viên vẫn nhận đủ
                # thời gian học đã tích lũy trong phòng.
                for member in list(channel.members):
                    if member.id in user_cam_start:
                        await finish_session(member, channel)
                await channel.delete(reason=reason)
        except (discord.NotFound, discord.Forbidden):
            pass

    conn = db()
    conn.execute("UPDATE room_records SET active = 0 WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

    task = room_restore_tasks.pop(channel_id, None)
    if task and task is not asyncio.current_task():
        task.cancel()


async def expire_room(channel_id, seconds):
    try:
        await asyncio.sleep(max(1, seconds))
        await close_temporary_room(channel_id)
    except asyncio.CancelledError:
        return


@bot.command(aliases=["xoa_phong"])
async def xoaphong(ctx):
    channel = ctx.author.voice.channel if ctx.author.voice else None
    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send("❌ Bạn phải đang ở phòng Voice muốn xóa.")
        return
    if not await room_owner_or_special(ctx, channel):
        return

    conn = db()
    row = conn.execute("""
        SELECT privacy FROM room_records
        WHERE channel_id = ? AND active = 1
    """, (channel.id,)).fetchone()
    conn.close()

    if not row or row[0] == "rename":
        await ctx.send("❌ Đây không phải phòng học tạm do bot quản lý.")
        return

    name = channel.name
    await close_temporary_room(
        channel.id,
        reason=f"Xóa phòng theo yêu cầu của {ctx.author}"
    )
    await ctx.send(f"🗑️ Phòng **{name}** đã được xóa.")


@bot.command(aliases=["giahan_phong", "giahanphong"])
async def giahanphong(ctx, thoi_gian: str = None):
    channel = ctx.author.voice.channel if ctx.author.voice else None
    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send("❌ Bạn phải đang ở phòng Voice muốn gia hạn.")
        return
    if not await room_owner_or_special(ctx, channel):
        return

    seconds = parse_duration_seconds(thoi_gian or "")
    if seconds <= 0:
        await ctx.send("❌ Ví dụ: `!giahanphong 30m` hoặc `!giahanphong 2h`.")
        return

    conn = db()
    row = conn.execute("""
        SELECT expires_at, privacy FROM room_records
        WHERE channel_id = ? AND active = 1
    """, (channel.id,)).fetchone()
    conn.close()

    if not row or row[1] == "rename":
        await ctx.send("❌ Đây không phải phòng học tạm do bot quản lý.")
        return

    now = now_vn()
    try:
        current_expiry = datetime.fromisoformat(row[0])
    except Exception:
        current_expiry = now

    new_expiry = max(now, current_expiry) + timedelta(seconds=seconds)

    conn = db()
    conn.execute(
        "UPDATE room_records SET expires_at = ? WHERE channel_id = ? AND active = 1",
        (new_expiry.isoformat(), channel.id)
    )
    conn.commit()
    conn.close()

    old_task = room_restore_tasks.get(channel.id)
    if old_task:
        old_task.cancel()

    delay = max(1, int((new_expiry - now).total_seconds()))
    room_restore_tasks[channel.id] = asyncio.create_task(expire_room(channel.id, delay))

    await ctx.send(
        f"⏳ Đã gia hạn **{channel.name}** thêm **{thoi_gian}**.\n"
        f"🕒 Hết hạn lúc **{new_expiry.strftime('%d/%m/%Y %H:%M:%S')}** (VN)."
    )


@bot.command(aliases=["phonginfo", "thongtinphong"])
async def thongtinphong(ctx):
    channel = ctx.author.voice.channel if ctx.author.voice else None
    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send("❌ Bạn phải ở trong một phòng Voice.")
        return

    conn = db()
    row = conn.execute("""
        SELECT owner_id, expires_at, privacy, active
        FROM room_records WHERE channel_id = ?
    """, (channel.id,)).fetchone()
    conn.close()

    if not row or not row[3]:
        await ctx.send("ℹ️ Đây không phải phòng tạm do bot quản lý.")
        return

    try:
        expiry = datetime.fromisoformat(row[1])
        remaining = max(0, int((expiry - now_vn()).total_seconds()))
    except Exception:
        remaining = 0

    await ctx.send(
        f"🎧 **{channel.name}**\n"
        f"👤 Chủ phòng: <@{row[0]}>\n"
        f"🔐 Chế độ: **{row[2]}**\n"
        f"⏳ Còn khoảng: **{format_duration(remaining)}**\n"
        f"🗑️ Xóa: `!xoaphong`\n"
        f"➕ Gia hạn: `!giahanphong 30m`"
    )

# ============================================================
# 👑 ĐỔI TÊN PHÒNG — có lý do + thời hạn + trả tên cũ
# ============================================================

async def temporary_rename_channel(channel, new_name, seconds, reason, member):
    conn = db()
    row = conn.execute("""
        SELECT original_name FROM room_records
        WHERE channel_id = ? AND active = 1
    """, (channel.id,)).fetchone()

    original = row[0] if row else channel.name

    await channel.edit(name=new_name[:100], reason=f"{member}: {reason}")

    expires = now_vn() + timedelta(seconds=seconds)
    conn.execute("""
        INSERT INTO room_records(
            channel_id, guild_id, owner_id, original_name,
            expires_at, privacy, active
        ) VALUES (?, ?, ?, ?, ?, 'rename', 1)
        ON CONFLICT(channel_id) DO UPDATE SET
            original_name=excluded.original_name,
            expires_at=excluded.expires_at,
            active=1
    """, (channel.id, channel.guild.id, member.id, original, expires.isoformat()))
    conn.commit()
    conn.close()

    old_task = room_restore_tasks.get(channel.id)
    if old_task:
        old_task.cancel()

    async def restore():
        await asyncio.sleep(seconds)
        ch = bot.get_channel(channel.id)
        if ch:
            try:
                await ch.edit(name=original, reason="Hết thời hạn đổi tên phòng")
            except (discord.NotFound, discord.Forbidden):
                pass
        conn2 = db()
        conn2.execute("UPDATE room_records SET active = 0 WHERE channel_id = ?", (channel.id,))
        conn2.commit()
        conn2.close()

    room_restore_tasks[channel.id] = asyncio.create_task(restore())

# ============================================================
# 🧰 TẠO KÊNH / XÓA KÊNH
# ============================================================

