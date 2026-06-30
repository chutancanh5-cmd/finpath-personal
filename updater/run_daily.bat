@echo off
chcp 65001 >nul
REM ============================================================
REM  FinPath ca nhan - chay 1 lan/ngay sau 15:00 (cuoi phien VN)
REM  Cap nhat day du moi nguon + scan cuoi phien + canh bao, push 1 lan.
REM ============================================================
cd /d "C:\Users\chuta\finpath-personal\updater"

python update_prices.py
python update_signals.py
python update_news.py
python alert.py
python scan_daily.py --discord
python update_orderflow.py --discord
python check_alerts.py
python push_data.py --force

echo Done %date% %time%
