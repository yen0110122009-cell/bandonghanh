# 🐝 Ong & Cỏ 4 Lá — Modular Discord Bot

Bản này giữ nguyên hệ thống V2.1 nhưng tách thành các module Python để dễ bảo trì và mở rộng.

## Cấu trúc

```text
ong_co_la_bot/
├── main.py            # điểm chạy chính
├── core.py            # cấu hình, bot, DB, tiện ích dùng chung
├── study.py           # học bằng camera + chọn môn
├── reminders.py       # nhắc nhở
├── leaderboard.py     # BXH + báo cáo
├── shop.py            # shop + túi đồ + vật phẩm
├── discipline.py      # kỷ luật + giải trình/duyệt phép
├── rooms.py           # phòng học tạm thời
├── admin.py           # setup server
├── admin_tools.py     # quản lý kênh + help
└── events.py          # ready / voice / error events
```

## Dữ liệu

SQLite vẫn được giữ để không làm mất dữ liệu hiện tại. Biến môi trường `DB_PATH` cho phép đổi nơi lưu DB.

Khuyến nghị khi chạy trên hosting:
- Nếu hosting có Persistent Disk: đặt `DB_PATH` vào thư mục của disk.
- Nếu không có persistent storage, bot vẫn chạy nhưng dữ liệu SQLite có thể mất khi instance bị thay mới.

## Chạy local

```bash
pip install -r requirements.txt
export DISCORD_TOKEN="TOKEN_CUA_BAN"
python run_bot.py
```

Windows PowerShell:

```powershell
$env:DISCORD_TOKEN="TOKEN_CUA_BAN"
python run_bot.py
```

## Render / hosting 24/7

Bot có:
- Flask `/health` để kiểm tra tiến trình.
- Discord `bot.run()` tự reconnect khi kết nối Discord bị rớt.
- Reminder loop có reconnect và bắt lỗi để một lỗi tạm thời không làm chết vòng nhắc nhở.
- Phòng tạm khôi phục thời hạn sau restart/reconnect.
- DB có WAL, busy timeout và cấu hình phù hợp cho SQLite.

Tuy nhiên, code không thể tự đảm bảo máy chủ chạy 24/7 nếu hosting chủ động sleep/restart instance. Muốn 24/7 thực tế cần dùng loại dịch vụ/plan không sleep và cấu hình Persistent Disk hoặc database ngoài.

Trên Render, có thể dùng Web Service với:
- Build: `pip install -r requirements.txt`
- Start: `python run_bot.py`
- Health Check: `/health`
- Secret: `DISCORD_TOKEN`

Nếu gắn Persistent Disk, đặt `DB_PATH` tới đường dẫn mount của disk.

## Mở rộng về sau

Mỗi tiện ích mới nên thành một module riêng, ví dụ:

```text
events_feature.py
achievements.py
tasks.py
calendar.py
notifications.py
web_dashboard/
```

Không nên dồn tính năng mới vào `core.py`. `core.py` chỉ nên giữ nền tảng dùng chung.

## Lộ trình web

Khi chuyển sang cho nhiều người sử dụng:
1. Giữ Discord Bot làm backend chính.
2. Thêm Discord OAuth2 cho đăng nhập web.
3. Thêm API layer.
4. Chuyển dữ liệu quan trọng từ SQLite sang PostgreSQL.
5. Thêm dashboard thành viên, BXH, lịch học, nhiệm vụ, thành tích, phòng và khu vực quản trị.

Hiện tại chưa ép người dùng phải đăng nhập web, vì bot vẫn được dùng riêng theo nhu cầu hiện tại.
