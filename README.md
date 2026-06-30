# FinPath cá nhân

PWA tĩnh kiểu Finpath dùng riêng cho thị trường VN: **Bảng giá · Khuyến nghị · Tin AI · Cảnh báo**.
Cùng pattern HPA tracker: `vnstock` → JSON trong `docs/data/` → GitHub Pages → app đọc.

## Cấu trúc
```
docs/                 ← GitHub Pages serve thư mục này
  index.html app.js styles.css sw.js manifest.webmanifest icon.svg
  data/  prices.json  signals.json  news.json
updater/
  update_prices.py    ← [DONE] bảng giá + chỉ số (vnstock VCI)
  update_signals.py   ← [DONE] DC55/30 16 mã → signals.json (logic = bot/discord_signal_bot.py)
  watchlist.txt       ← danh mục theo dõi = 16 mã DC55/30 (sửa tại đây)
  update_news.py      ← [DONE] import macro/ bot → regime + RSS + Haiku → news.json
  alert.py            ← [DONE] tín hiệu MUA/BÁN mới → Discord (dedup theo ngày)
  notify.py           ← gửi Discord + dedup dùng chung cho scanner
  universe.py         ← lấy toàn sàn HOSE/HNX/UPCOM + lọc thanh khoản (cache)
  scan_daily.py       ← [DONE] cuối phiên: vượt đỉnh+KL · giảm về hỗ trợ · tích lũy nền
  scan_intraday.py    ← [DONE] trong phiên: đột biến 5 phút · cá mập (proxy khối ngoại)
  run_daily.bat       ← 4 updater + alert + scan_daily (lịch sau 15:00)
  run_intraday.bat    ← scan_intraday (lịch mỗi 5 phút, tự bỏ qua ngoài giờ)
```

## Bộ quét (scanner)
5 loại cảnh báo kiểu Finpath, quét **toàn sàn** (lọc thanh khoản ≥2 tỷ/phiên, tối đa 500 mã):
- **Cuối phiên** (`scan_daily.py`, dữ liệu OHLCV ngày): 🚀 vượt đỉnh 60 phiên + KL ≥2× TB20 · 🛟 giảm ≥4% về sát MA50/đáy 60 · 🧱 nền chặt (biên độ 15 phiên ≤7% + KL co ≤80%).
- **Trong phiên** (`scan_intraday.py`, snapshot `price_board` theo lô): ⚡ giá nhảy ≥1.5% trong ~5 phút + KL bùng · 🦈 "cá mập" = net khối ngoại ≥10 tỷ hoặc lệnh khớp TB lớn.

Hiển thị ở tab **Quét** trong app + đẩy Discord (dedup). **Lưu ý:** "cá mập" là *proxy từ khối ngoại/độ lớn lệnh* (tick API free tier hỏng); muốn chuẩn block-trade thật cần nối project Order Flow Lab. Intraday chỉ bắn Discord (không push GitHub mỗi 5 phút để tránh quá giới hạn Pages).

## Chạy thử ngay (local)
```powershell
cd docs
python -m http.server 8080
# mở http://localhost:8080
```
App chạy được với dữ liệu mẫu trong `docs/data/`.

## Lấy dữ liệu thật
```powershell
cd updater
python update_prices.py            # bảng giá → docs/data/prices.json
python update_signals.py           # khuyến nghị DC55/30 → docs/data/signals.json
python update_news.py              # tin AI + regime → docs/data/news.json
# thêm --push để commit & push lên GitHub Pages
```
Cần `vnstock` đã cài + API key (env `VNSTOCK_API_KEY` hoặc `updater/vnstock_key.txt`),
giống HPA tracker. `update_signals.py` dùng đúng logic + 16 mã của `bot/discord_signal_bot.py`.
`update_news.py` import thẳng `macro/macro_bot.py` (FRED + RSS + Haiku) — dùng chung
`macro/config.json`. **Lưu ý:** phần tóm tắt/sentiment AI cần key Anthropic còn credit;
hết credit thì tự degrade về sắc thái trung tính + headline thật (vẫn chạy).

## Tự động hoá
`updater/run_daily.bat` chạy cả 4 bước (3 updater + alert). Đăng ký Task Scheduler
chạy ~15:10 các ngày T2–T6:
```powershell
schtasks /Create /TN "FinPath Daily" /TR "C:\Users\chuta\finpath-personal\updater\run_daily.bat" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 15:10 /F
```
**Lưu ý double-post:** `alert.py` dùng chung webhook với `bot/discord_signal_bot.py`.
Nếu bot cũ vẫn còn lịch chạy, anh sẽ nhận **2 lần** mỗi tín hiệu. Chọn 1 trong:
- Tắt lịch bot cũ, để FinPath lo cả việc báo Discord, hoặc
- Trỏ `alert.py` sang kênh khác qua `updater/alert_config.json`
  `{"discord_webhook_url": "..."}`, hoặc bỏ dòng `python alert.py` khỏi `.bat` (chỉ cập nhật dữ liệu).

`--push` chỉ hoạt động sau khi `git init` + tạo repo GitHub + bật Pages (thư mục `docs/`).
Chạy local không cần push: app đọc trực tiếp `docs/data/*.json`.

## Tiến độ
- [x] Phase 1 — PWA shell + bảng giá + watchlist + alert giá tại máy
- [x] Phase 2 — Khuyến nghị DC55/30 (16 mã, tính lời/lỗ vị thế đang nắm)
- [x] Phase 3 — Tin AI: regime score + RSS + Haiku (import macro bot)
- [ ] Phase 4 — Cảnh báo Discord khi có tín hiệu mới
