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


python update_prices.py
python update_market.py --append-hist
python update_signals.py
REM  CBTT theo ma - doc signals.json nen phai chay SAU update_signals.
python update_symbol_news.py
python update_trailstop.py
python update_market_read.py --discord
python alert.py
python scan_daily.py --discord
python update_orderflow.py --discord
python check_alerts.py
python heartbeat.py daily
python push_data.py --force

echo Done %date% %time%
