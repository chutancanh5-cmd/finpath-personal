# -*- coding: utf-8 -*-
"""
push_data.py -- Gop & GIAM NHIP push docs/data/*.json len GitHub Pages.

Intraday chay moi 5 phut nhung GitHub Pages chi build ~10 lan/gio. Script nay
chi push neu da >= PUSH_MIN phut tu lan push truoc (marker .last_push), tranh
throttle + va cham git. --force bo qua gioi han (dung cho run_daily).

Usage: python push_data.py [--force]
"""
import os
import sys
import subprocess
import datetime as dt
from datetime import timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MARKER = os.path.join(HERE, ".last_push")
VN_TZ = timezone(timedelta(hours=7))
PUSH_MIN = 12


def log(*a):
    print("[push_data]", *a, flush=True)


def now():
    return dt.datetime.now(VN_TZ)


def main():
    force = "--force" in sys.argv
    if not force and os.path.exists(MARKER):
        try:
            last = dt.datetime.fromisoformat(open(MARKER, encoding="utf-8").read().strip())
            mins = (now() - last).total_seconds() / 60
            if mins < PUSH_MIN:
                log(f"moi push {mins:.0f} phut truoc (< {PUSH_MIN}') -> bo qua")
                return
        except Exception:
            pass
    try:
        subprocess.run(["git", "-C", ROOT, "add", "docs/data"], check=True)
        if subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"]).returncode == 0:
            log("khong co thay doi du lieu.")
            return
        msg = "data: cap nhat " + now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)
        # keo ve truoc (phong khi co commit khac) roi push
        subprocess.run(["git", "-C", ROOT, "pull", "--rebase", "--autostash"], check=False)
        subprocess.run(["git", "-C", ROOT, "push"], check=True)
        open(MARKER, "w", encoding="utf-8").write(now().isoformat())
        log("da push.")
    except Exception as e:
        log("push err:", str(e)[:120])


if __name__ == "__main__":
    main()
