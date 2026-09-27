"""Ong & Co 4 La - modular feature."""
from .core import *

@bot.command()
async def taokenh(ctx, loai: str, *, name: str):
    if not await require_special(ctx):
        return
    loai = loai.lower()
    if loai in ("voice", "v", "thoai"):
        ch = await ctx.guild.create_voice_channel(name[:100])
    elif loai in ("text", "t", "chat"):
        ch = await ctx.guild.create_text_channel(name[:100])
    else:
        await ctx.send("❌ Loại kênh: `text` hoặc `voice`.")
        return
    await ctx.send(f"✅ Đã tạo {ch.mention if hasattr(ch, 'mention') else ch.name}.")

@bot.command()
async def xoakenh(ctx, *, name: str):
    if not await require_special(ctx):
        return
    channel = discord.utils.find(lambda c: c.name == name.strip(), ctx.guild.channels)
    if not channel:
        await ctx.send("❌ Không tìm thấy kênh.")
        return
    await channel.delete(reason=f"Yêu cầu bởi {ctx.author}")
    await ctx.send(f"🗑️ Đã xóa kênh `{name}`.")

# ============================================================
# 🔄 HELP
# ============================================================

@bot.command()
async def helpme(ctx):
    embed = discord.Embed(title="🐝 HỆ THỐNG ONG & CỎ 4 LÁ", color=discord.Color.gold())
    embed.add_field(
        name="📚 Học tập",
        value="`!mon <môn>` • `!baocao` • `!top [ngay|tuan|thang|nam]`",
        inline=False
    )
    embed.add_field(
        name="⏰ Nhắc nhở",
        value="`!nhacnho ...` • `!nhacnho xem` • `!nhacnho xoa ID`",
        inline=False
    )
    embed.add_field(
        name="🛒 Shop",
        value="`!shop` • `!mua <mã>` • `!tuido` • `!dung <vật phẩm>`",
        inline=False
    )
    embed.add_field(
        name="🎧 Phòng",
        value="`!taophong` • `!dongyphong ID` • `!mo_phong` • `!dong_phong`",
        inline=False
    )
    embed.add_field(
        name="🛡️ Kỷ luật",
        value="`!xem_phat` • `!phat` • `!duyet` • `!dung giaman` • `!dung mienphat`",
        inline=False
    )
    embed.add_field(
        name="👑 Quản trị",
        value="`!setup_server` • `!taorole` • `!xoarole` • `!themrole` • `!kick` • `!ban` • `!unban` • `!camngon`",
        inline=False
    )
    await ctx.send(embed=embed)

# ============================================================
# ❗ ERROR HANDLER
# ============================================================

