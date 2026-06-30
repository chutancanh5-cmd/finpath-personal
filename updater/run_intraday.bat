@echo off
chcp 65001 >nul
REM ============================================================
REM  FinPath - quet TRONG PHIEN (chay moi 5 phut, T2-T6).
REM  Cac script tu bo qua ngoai gio. Discord moi 5 phut; push gop & giam nhip
REM  (push_data.py chi day GitHub ~12 phut/lan -> tranh throttle Pages).
REM ============================================================
cd /d "C:\Users\chuta\finpath-personal\updater"

python update_prices.py --light
python scan_intraday.py --discord
python update_orderflow.py --discord
python check_alerts.py
python push_data.py
