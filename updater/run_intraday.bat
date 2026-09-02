@echo off
chcp 65001 >nul
REM ============================================================
REM  FinPath - quet TRONG PHIEN (chay moi 5 phut, T2-T6).
REM  Cac script tu bo qua ngoai gio. Discord moi 5 phut; push gop & giam nhip
REM  (push_data.py chi day GitHub ~12 phut/lan -> tranh throttle Pages).
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


python update_prices.py --light
python update_market.py
python scan_intraday.py --discord
python update_orderflow.py --discord
python check_alerts.py
python heartbeat.py intraday
python push_data.py
