"""Ong & Co 4 La - modular feature."""
from .core import *
import time

@bot.command()
async def mon(ctx, *, subject="Tự do"):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Bạn phải ở Voice để chọn môn.")
        return
    subject = subject.strip()[:80] or "Tự do"
    user_subject_study[ctx.author.id] = {
        "subject": subject,
        "start_time": user_cam_start.get(ctx.author.id, time.time()),
        "channel_id": ctx.author.voice.channel.id
    }
    record_subject_choice(ctx.author.id, subject)
    await ctx.send(f"📚 Đã chọn môn **{subject}**.", delete_after=10)

# ============================================================
# 🎧 VOICE STUDY
# ============================================================

def record_camera_toggle(member_id):
    now = time.time()
    history = camera_toggle_history.setdefault(member_id, [])
    history[:] = [x for x in history if now - x <= TOGGLE_WINDOW]
    history.append(now)
    return len(history)

async def alert_camera_violation(member, voice_channel, count):
    channel = discord.utils.get(member.guild.text_channels, name=DISCIPLINE_LOG_CHANNEL)
    if not channel:
        return
    owner = discord.utils.get(member.guild.roles, name=OWNER_ROLE)
    bql = discord.utils.get(member.guild.roles, name=BQL_ROLE)
    mentions = " ".join(r.mention for r in (owner, bql) if r)
    await channel.send(
        content=mentions,
        embed=discord.Embed(
            title="🚨 CẢNH BÁO CAMERA",
            description=(
                f"👤 {member.mention}\n"
                f"🎧 Phòng: `{voice_channel.name if voice_channel else 'Không xác định'}`\n"
                f"🔄 {count} lần bật/tắt trong 5 phút.\n\n"
                "Bot chỉ cảnh báo; BQL quyết định hình thức xử lý."
            ),
            color=discord.Color.orange()
        ),
        allowed_mentions=discord.AllowedMentions(roles=True, users=True)
    )

async def finish_session(member, channel):
    start = user_cam_start.pop(member.id, None)
    if start is None:
        return
    info = user_subject_study.pop(member.id, {"subject": "Tự do"})
    subject = info.get("subject", "Tự do")

    duration, earned, streak = settle_study_session(
        member, channel, start, subject
    )

    msg = (
        f"👋 Tạm biệt {member.mention}!\n"
        f"📚 Môn: **{subject}**\n"
        f"⏱️ Thời gian: **{format_duration(duration)}**\n"
        f"🔥 Streak: **{streak} ngày**\n"
    )
    if earned:
        ratio = "4,5 phút = 1 🍀" if x2_active(member.id) else "9 phút = 1 🍀"
        msg += f"🍀 Nhận **+{earned} Cỏ** ({ratio})."
    await channel.send(msg)

