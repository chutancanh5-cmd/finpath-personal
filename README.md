# FinPath cá nhân

PWA tĩnh kiểu Finpath dùng riêng cho thị trường VN: **Bảng giá · Đọc hiểu · Khuyến nghị · Tin AI · Quét · Dòng tiền · Cảnh báo**.
Cùng pattern HPA tracker: `vnstock` → JSON trong `docs/data/` → GitHub Pages → app đọc.

## Cấu trúc
```
docs/                 ← GitHub Pages serve thư mục này
  index.html app.js styles.css sw.js manifest.webmanifest icon.svg
  data/  prices.json  signals.json  news.json
updater/
  update_prices.py    ← [DONE] bảng giá + chỉ số (vnstock VCI)
  update_signals.py   ← [DONE] DC55/30 16 mã → signals.json (logic = bot/discord_signal_bot.py)
  update_market_read.py ← [DONE] Đọc hiểu thị trường (Wyckoff/Stage) → market_read.json + Discord
  watchlist.txt       ← danh mục theo dõi = 16 mã DC55/30 (sửa tại đây)
  update_news.py      ← [DONE] import macro/ bot → regime + RSS + Haiku → news.json
  alert.py            ← [DONE] tín hiệu MUA/BÁN mới → Discord (dedup theo ngày)
  notify.py           ← gửi Discord + dedup dùng chung cho scanner
  universe.py         ← lấy toàn sàn HOSE/HNX/UPCOM + lọc thanh khoản (cache)
  scan_daily.py       ← [DONE] cuối phiên: vượt đỉnh+KL · giảm về hỗ trợ · tích lũy nền
  scan_intraday.py    ← [DONE] trong phiên: đột biến 5 phút · cá mập (proxy khối ngoại)
  update_orderflow.py ← [DONE] dòng tiền THẬT (kbs tick mua/bán chủ động) từ orderflow/feed.py
  run_daily.bat       ← 4 updater + alert + scan_daily (lịch sau 15:00)
  run_intraday.bat    ← scan_intraday + update_orderflow (lịch mỗi 5 phút)
```

## Đọc hiểu thị trường (tab "Đọc hiểu")
Đọc **chiến dịch của tay to qua nhiều tháng** (Wyckoff / Weinstein Stage) — không phải khuyến nghị mua bán:
- Mỗi mã (~64 mã theo ngành + watchlist) được phân pha: **Tích lũy → Đẩy giá → Phân phối → Đè giá**
  (MA150 ~30 tuần + độ dốc; pha làm mượt 12 phiên để câu chuyện sạch).
- Dấu chân dòng tiền: OBV 3 tháng (tiền âm thầm vào/ra), vị trí trong range 6 tháng, KL khô hạn.
- Regime VNINDEX>MA50 (risk-on/off) làm đèn nền toàn thị trường.
- Discord (webhook riêng `DISCORD_WEBHOOK_MARKETREAD`): run đầu gửi bản đồ pha; sau đó **chỉ báo khi
  mã CHUYỂN pha** (vào Đẩy giá = cơ hội 🟢, vào Phân phối/Đè giá = cảnh giác 🟠🔴) — dedup qua
  `updater/marketread_state.json` (được commit để persist qua các lần chạy cloud).
- Nguồn gốc: chưng cất từ project Market Reader (backtest 59 mã 2018–2026; kết luận trung thực:
  dùng để ĐỌC + cảnh báo rủi ro, không phải máy tự sinh lời).
- ⚠️ vnstock Guest = **20 request/phút** → updater giãn 3.2s/mã (~5 phút cho cả rổ) + guard:
  đọc được <70% rổ thì giữ file cũ, không ghi đè.

## Dòng tiền (tab "Dòng tiền")
Order flow THẬT cho watchlist, nối thẳng `orderflow/feed.py` (`source="kbs"`):
- **Lệnh chủ động Mua/Bán gộp** của cả thị trường (%mua cả phiên + 15' gần nhất, net tỷ VND).
- 🦈 **Lệnh lớn** (cá mập): tick khớp đơn lẻ ≥200tr — hiện giá/KL/giờ.
- **Sổ lệnh** bid/ask + khối ngoại ròng.
- *Không* thấy lệnh từng nhà đầu tư (dữ liệu đó riêng tư, không nguồn nào có) — chỉ hành vi gộp.
Đây là bản order flow thật, thay cho proxy khối ngoại ở tab Quét.

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

## Cải tiến (v2)
- **Cá mập THẬT**: `update_orderflow.py --discord` bắn lệnh khớp đơn lẻ ≥1 tỷ (bỏ proxy khối ngoại ở scan).
- **Cảnh báo giá server-side**: `check_alerts.py` đọc `price_alerts.json` → Discord cả khi đóng app.
- **Biểu đồ giá**: tap mã ở Bảng giá → modal chart 120 phiên (`hist` trong prices.json).
- **Giá cập nhật trong phiên**: `update_prices.py --light` (1 lần price_board, không tải lại lịch sử).
- **Badge "dữ liệu cũ"** trong app khi task lỗi (trong giờ giao dịch, >25′).
- **Giảm nhịp Pages**: `push_data.py` gộp + chỉ push ≥12′/lần (tránh throttle + va chạm git).

## Backtest chiến thuật "Tích sản trong Uptrend"
Hệ thống backtest độc lập ở `backtest/`, hiện thực đúng chiến thuật CMT (Trend + Amplitude
qua MA, Timing theo chu kỳ) mà nhà đầu tư mô tả — khung thời gian **THÁNG (M1)**, **tập trung
cho chứng khoán CƠ SỞ Việt Nam** (VN-Index + watchlist cổ phiếu của app):
- **MUA**: nến tháng đóng cửa > MA(N) → đầu tháng sau có lương là mua tích sản (DCA).
- **BÁN**: nến tháng đóng cửa < MA(N) → bán sạch ngay đầu tháng sau.
- **TIMING**: giữ vị thế đủ **26 tháng** uptrend liên tục mà chưa bị tín hiệu MA cắt xuống thì
  vẫn chủ động bán sạch (force-exit), sau đó **nghỉ 18 tháng (1,5 năm)** mới đánh giá lại tín hiệu.
- MA10 áp dụng đồng nhất cho VN-Index và toàn bộ cổ phiếu (đúng quy tắc mô tả cho VN-Index).
  BTC/Vàng (MA13/MA21) vẫn chạy được qua `run_backtest.py --asset btc|gold` nhưng không còn
  nằm trong workflow tự động (đã tập trung lại cho thị trường VN).

```
backtest/
  strategy.py       ← state machine sinh tín hiệu MUA/BÁN/FORCE_EXIT (không nhìn trước dữ liệu)
  engine.py         ← mô phỏng dòng tiền DCA + 2 benchmark (DCA đều/không bán, lump-sum)
  metrics.py        ← XIRR, max drawdown, MOIC, tỷ lệ vòng thắng...
  data_sources.py   ← nạp giá tháng: vnstock_data (trả phí) ưu tiên, lùi về vnstock (miễn phí) / CSV offline
  report.py         ← xuất báo cáo Markdown + JSON, kèm bảng xếp hạng tổng hợp nhiều mã
  run_backtest.py   ← CLI chạy backtest 1 mã
  run_batch.py      ← CLI chạy backtest VN-Index + watchlist.txt cùng lúc, ra bảng xếp hạng
  tests/            ← unit test (python -m unittest discover -s backtest/tests)
```

Chạy thử:
```bash
pip install -r requirements.txt
python backtest/run_batch.py                       # VN-Index + updater/watchlist.txt, MA10
python backtest/run_batch.py --symbols FPT,HPG,VNINDEX
python backtest/run_backtest.py --asset vnindex     # 1 mã, MA10
# offline (không cần mạng), CSV cột time,open,high,low,close:
python backtest/run_backtest.py --asset vnindex --csv data.csv
```
Kết quả (JSON `docs/data/backtest_<ma>.json` + Markdown `docs/backtest_<ma>.md`, cộng bảng tổng hợp
`docs/backtest_summary.md`) được workflow `.github/workflows/backtest.yml` tự chạy đầu mỗi tháng
(và có thể bấm chạy tay qua workflow_dispatch).

**Dữ liệu:** `data_sources.py` ưu tiên `vnstock_data` (bản trả phí, cùng `VNSTOCK_API_KEY` mà
`finpath-daily.yml` đã dùng) để có lịch sử đầy đủ; nếu chưa cài/chưa có key thì tự lùi về
`vnstock` miễn phí. Đã xác nhận qua CI thật (tier "golden"): dùng `vnstock_data` trả phí, VN-Index
lấy được **271 tháng (2004-01 → 2026-07)** thay vì chỉ ~97 tháng (từ 2018) như bản miễn phí; các
cổ phiếu trong watchlist có lịch sử 106–237 tháng tùy mã (theo ngày niêm yết). Xem
`docs/backtest_summary.md` để có bảng xếp hạng đầy đủ.

## Tiến độ
- [x] Phase 1 — PWA shell + bảng giá + watchlist + alert giá tại máy
- [x] Phase 2 — Khuyến nghị DC55/30 (16 mã, tính lời/lỗ vị thế đang nắm)
- [x] Phase 3 — Tin AI: regime score + RSS + Haiku (import macro bot)
- [ ] Phase 4 — Cảnh báo Discord khi có tín hiệu mới
