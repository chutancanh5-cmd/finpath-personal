@echo off
chcp 65001 >nul
REM ============================================================
REM  FinPath ca nhan - chay 1 lan/ngay sau 15:00 (cuoi phien VN)
REM  Cap nhat day du moi nguon + scan cuoi phien + canh bao, push 1 lan.
REM ============================================================
cd /d "C:\Users\chuta\finpath-personal\updater"

REM --- CONG NGAY GIAO DICH: ngay nghi le / cuoi tuan thi DUNG NGAY -------------
REM  Truoc day .bat nay chay theo lich T2-T6 ma KHONG biet ngay le, nen trong ky
REM  nghi no van quet du lieu cu roi ban Discord (doc thi truong / lenh lon / canh
REM  bao) - bao cao trung y het phien cuoi truoc ky nghi. Lich: vn_holidays.json.
REM  PHAM VI: cong nay CHI cho viec theo phien. Tin tuc + vi mo van chay lien tuc.
python vn_trading_calendar.py --gate
if errorlevel 1 (
    echo Ngay nghi - bo qua %date% %time%
    exit /b 0
)


REM --- TRAN THOI GIAN CHO TUNG BUOC (them 05/09/2026) -------------------------
REM  Truoc day cac dong duoi la `python <script>` tran. Mot script treo o nguon
REM  (VCI: 30s/lan x3 lan tenacity = 96s cho MOT call loi) an het quy thoi gian
REM  cua ca chuoi, Task Scheduler cat o ExecutionTimeLimit 1h30 -> HAI BUOC CUOI
REM  (heartbeat + push_data) khong bao gio chay. Do that: khoa "daily" trong
REM  docs/data/pc_heartbeat.json dung yen tu 26/08 den 04/09; ci_gate.py tuong PC
REM  chua chay nen mo cong cho cloud, ma cloud bi VCI chan nang hon -> 30' roi bi
REM  huy, khong day duoc gi. 6 phien 27/08-03/09 mat trang va IM LANG.
REM  run_step.py: het gio thi giet ca cay tien trinh roi tra 0 de buoc sau van
REM  chay, va ghi thoi gian tung buoc vao run_steps.log (truoc day task chay .bat
REM  khong redirect nen moi output deu mat). Tong tran = 79' < 1h30 cua task.
python run_step.py  300 update_prices.py
python run_step.py  300 update_market.py --append-hist
python run_step.py  900 update_signals.py
REM  CBTT theo ma - doc signals.json nen phai chay SAU update_signals.
python run_step.py  300 update_symbol_news.py
python run_step.py 1200 update_trailstop.py
python run_step.py  600 update_market_read.py --discord
python run_step.py  120 alert.py
python run_step.py  300 scan_daily.py --discord
python run_step.py  300 update_orderflow.py --discord
python run_step.py  120 check_alerts.py
REM  Hai buoc nay PHAI toi duoc: heartbeat bao cho cloud "PC da lam xong phien
REM  hom nay", push_data day ket qua len GitHub Pages.
python run_step.py   60 heartbeat.py daily
python run_step.py  240 push_data.py --force

echo Done %date% %time%
