# -*- coding: utf-8 -*-
"""
run_step.py -- chay MOT buoc cua pipeline voi tran thoi gian + ghi nhat ky.

VI SAO CAN:
  run_daily.bat / run_intraday.bat goi lien tiep ~12 script python. Neu mot script
  treo o nguon du lieu (VCI 30s/lan x3 lan tenacity = 96s cho MOT call loi, va tu
  cuoi 08/2026 VCI chap chon ca voi IP nha) thi no an het quy thoi gian cua CA
  chuoi. Task Scheduler cat o ExecutionTimeLimit -> nhung buoc CUOI khong bao gio
  chay: heartbeat.py va push_data.py. Hau qua that da xay ra:

    docs/data/pc_heartbeat.json khoa "daily" dung yen tu 26/08 den 04/09.
    Cong ci_gate.py thay "PC chua chay hom nay" nen mo cho cloud chay bu, ma cloud
    lai bi VCI chan nang hon -> 30 phut roi bi huy, khong day duoc gi.
    => 6 phien 27/08 - 03/09 khong co du lieu cuoi phien nao, va IM LANG.

CACH LAM:
  - Het gio thi giet CA CAY tien trinh (taskkill /T) chu khong chi tien trinh con
    truc tiep: python goi tiep requests/urllib3 va co the de lai tien trinh chau.
  - LUON tra ve 0. Buoc sau van chay -- giong y `|| true` ben workflow cloud.
    Muon .bat dung khi loi thi dung `--strict`.
  - Ghi mot dong tong ket vao run_steps.log de con truy duoc buoc nao an thoi gian.
    Truoc day task chay .bat KHONG redirect nen moi output deu mat.

DUNG:
    python run_step.py <giay> <script.py> [tham so...]
    python run_step.py --strict <giay> <script.py> [tham so...]
"""
import os
import sys
import time
import subprocess
import datetime as dt
from datetime import timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "run_steps.log")
VN_TZ = timezone(timedelta(hours=7))
MAX_LOG_BYTES = 512 * 1024


def ghi_log(dong):
    """Ghi mot dong vao run_steps.log, tu cat bot khi qua to."""
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > MAX_LOG_BYTES:
            with open(LOG, encoding="utf-8", errors="replace") as f:
                giu = f.readlines()[-2000:]
            with open(LOG, "w", encoding="utf-8") as f:
                f.writelines(giu)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(dong + "\n")
    except Exception:
        pass  # nhat ky hong thi cung khong duoc lam sap pipeline


def giet_cay(proc):
    """Giet ca cay tien trinh. proc.kill() chi giet tien trinh con truc tiep."""
    try:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=30)
    except Exception:
        pass
    try:
        proc.kill()
    except Exception:
        pass


def main(argv):
    strict = False
    if argv and argv[0] == "--strict":
        strict = True
        argv = argv[1:]
    if len(argv) < 2:
        print(__doc__)
        return 2

    try:
        tran = float(argv[0])
    except ValueError:
        print(f"[run_step] tham so giay khong hop le: {argv[0]!r}")
        return 2

    lenh = [sys.executable] + argv[1:]
    ten = " ".join(argv[1:])
    bat_dau = time.monotonic()
    dau_gio = dt.datetime.now(VN_TZ)

    proc = subprocess.Popen(lenh, cwd=HERE)
    try:
        ma = proc.wait(timeout=tran)
        het_gio = False
    except subprocess.TimeoutExpired:
        giet_cay(proc)
        try:
            proc.wait(timeout=15)
        except Exception:
            pass
        ma, het_gio = -1, True

    giay = time.monotonic() - bat_dau
    trang_thai = f"HET GIO >{tran:.0f}s" if het_gio else ("OK" if ma == 0 else f"loi rc={ma}")
    dong = f"[{dau_gio:%Y-%m-%d %H:%M:%S}] {giay:7.1f}s  {trang_thai:<16} {ten}"
    print(dong)
    ghi_log(dong)

    # Mac dinh nuot loi de buoc sau (nhat la heartbeat + push_data o cuoi chuoi)
    # van chac chan duoc chay.
    return ma if (strict and ma != 0) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
