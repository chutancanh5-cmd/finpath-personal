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


REM --- TRAN THOI GIAN CHO TUNG BUOC (them 05/09/2026) -------------------------
REM  Xem giai thich day du trong run_daily.bat. Rieng .bat nay lap 5 phut/lan ma
REM  do duoc no dang chay ~20-25 phut/lan (cac commit "data: cap nhat" cach nhau
REM  dung 25 phut chu khong phai 5): Task Scheduler bo qua 4 nhip ke tiep vi ban
REM  truoc chua xong, roi cat o ExecutionTimeLimit 20' (LastTaskResult 267014 =
REM  SCHED_S_TASK_TERMINATED). Tong tran duoi = 15,5' < 20' cua task.
REM  Xem run_steps.log de biet buoc nao an thoi gian roi siet tiep con so cho vua
REM  nhip 5 phut.
python run_step.py 150 update_prices.py --light
python run_step.py 150 update_market.py
python run_step.py 120 scan_intraday.py --discord
python run_step.py 180 update_orderflow.py --discord
python run_step.py  90 check_alerts.py
REM  Hai buoc cuoi phai toi duoc: nhip tim cho ci_gate + day du lieu len Pages.
python run_step.py  60 heartbeat.py intraday
python run_step.py 180 push_data.py
