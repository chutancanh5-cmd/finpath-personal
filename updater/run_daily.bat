@echo off
chcp 65001 >nul
REM ============================================================
REM  FinPath ca nhan - chay 1 lan/ngay sau 15:00 (cuoi phien VN)
REM  Cap nhat 3 nguon du lieu + ban canh bao Discord neu co tin hieu moi.
REM  --push: tu commit & push len GitHub Pages (can git init + remote truoc).
REM ============================================================
cd /d "C:\Users\chuta\finpath-personal\updater"

python update_prices.py  --push
python update_signals.py --push
python update_news.py    --push
python alert.py
python scan_daily.py --discord --push

echo Done %date% %time%
