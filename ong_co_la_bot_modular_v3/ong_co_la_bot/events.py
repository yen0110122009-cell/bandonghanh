"""Discord lifecycle/event handlers for Ong & Co 4 La."""
from .core import *
from .reminders import reminder_loop
from .discipline import ensure_fixed_channels
from .rooms import restore_room_tasks

@bot.event
async def on_ready():
    print(f"✅ Đăng nhập Discord: {bot.user} ({bot.user.id})")
    print(f"🌏 Giờ Việt Nam: {now_vn().strftime('%d/%m/%Y %H:%M:%S')}")
    if not reminder_loop.is_running():
        reminder_loop.start()

    for guild in bot.guilds:
        try:
            await ensure_fixed_channels(guild)
        except Exception as e:
            print(f"[SETUP ERROR] {guild.name}: {e!r}")

    try:
        await restore_room_tasks()
    except Exception as e:
        print(f"[ROOM RESTORE ERROR] {e!r}")

@bot.event
async def on_voice_state_update(member, before, after):
    from .study import finish_session, record_camera_toggle, alert_camera_violation
    if before.channel and after.channel is None and member.id in user_cam_start:
        await finish_session(member, before.channel)
        return

    if before.channel and after.channel and before.channel.id != after.channel.id and member.id in user_cam_start:
        await finish_session(member, before.channel)

    if after.channel and not before.self_video and after.self_video:
        if member.id not in user_cam_start:
            now = time.time()
            user_cam_start[member.id] = now
            user_subject_study[member.id] = {
                "subject": "Tự do",
                "start_time": now,
                "channel_id": after.channel.id
            }
            count = record_camera_toggle(member.id)
            await after.channel.send(
                f"🎉 {member.mention} đã bắt đầu tích lũy giờ học!\n"
                "📚 Môn mặc định: **Tự do**. Có thể dùng `!mon <môn>`."
            )
            if count >= TOGGLE_LIMIT:
                await alert_camera_violation(member, after.channel, count)

    if before.channel and before.self_video and not after.self_video and member.id in user_cam_start:
        await finish_session(member, before.channel)
        count = record_camera_toggle(member.id)
        if count >= TOGGLE_LIMIT:
            await alert_camera_violation(member, before.channel, count)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Thiếu tham số. Gõ `!helpme` để xem hướng dẫn.")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ Tham số không hợp lệ. Gõ `!helpme` để xem hướng dẫn.")
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send("🔒 Bạn không có quyền dùng lệnh này.")
        return
    print(f"[ERROR] {error!r}")
    try:
        await ctx.send("⚠️ Bot gặp lỗi khi thực hiện lệnh. Lỗi đã được ghi vào log.")
    except Exception:
        pass
