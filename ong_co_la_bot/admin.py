"""Ong & Co 4 La - modular feature."""
from .core import *

@bot.command()
async def setup_server(ctx):
    if not await require_special(ctx):
        return
    try:
        owner, bql, discipline, confession, log_channel, room_cat = await ensure_fixed_channels(ctx.guild)
        await ctx.send(
            "✅ **Thiết lập hệ thống hoàn tất.**\n"
            f"👑 {owner.name}\n"
            f"🛡️ {bql.name}\n"
            f"🔒 {discipline.name}\n"
            f"📜 {confession.mention}\n"
            f"⚠️ {log_channel.mention}\n"
            f"🎧 `{room_cat.name}`"
        )
    except discord.Forbidden:
        await ctx.send("❌ Bot thiếu quyền quản lý role/channel. Hãy cấp Manage Roles + Manage Channels.")

# ============================================================
# 🛒 SHOP COMMANDS
# ============================================================

