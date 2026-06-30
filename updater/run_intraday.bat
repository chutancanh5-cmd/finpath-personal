@echo off
chcp 65001 >nul
REM ============================================================
REM  FinPath - quet TRONG PHIEN (chay moi 5 phut, T2-T6).
REM  scan_intraday.py tu bo qua ngoai gio giao dich (re, khong goi mang).
REM  Chi ban Discord (khong --push de tranh spam commit / gioi han Pages).
REM ============================================================
cd /d "C:\Users\chuta\finpath-personal\updater"
python scan_intraday.py --discord
