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


def don_dep_rebase_treo():
    """Neu lan chay TRUOC de lai mot rebase do dang thi don sach truoc khi lam gi.

    Rebase do dang = repo o detached HEAD; `git commit` van chay duoc nhung `git push`
    khong bao gio day duoc nhanh main -> bot chay am tham ma khong ai hay."""
    for d in (".git/rebase-merge", ".git/rebase-apply"):
        if os.path.exists(os.path.join(ROOT, d)):
            log("phat hien rebase do dang tu lan truoc -> abort de tro ve main.")
            subprocess.run(["git", "-C", ROOT, "rebase", "--abort"], check=False)
            break


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
        don_dep_rebase_treo()
        subprocess.run(["git", "-C", ROOT, "add", "docs/data"], check=True)
        if subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"]).returncode == 0:
            log("khong co thay doi du lieu.")
            return
        msg = "data: cap nhat " + now().strftime("%Y-%m-%d %H:%M")
        subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)

        # Cloud cung ghi docs/data (khi PC im lang qua nguong) nen VA CHAM LA BINH THUONG.
        # Ban cu: `pull --rebase --autostash` voi check=False, khong co chien luoc gai xung
        # dot va khong don dep khi that bai -> rebase hong nam lai, repo roi vao detached
        # HEAD, moi lan chay sau van commit tiep nhung KHONG BAO GIO push duoc. Loi bi
        # nuot nen im lang hoan toan: 2026-08-21 mat 82 commit / 7 tieng theo kieu nay, va
        # vi nhip tim khong len duoc GitHub nen cloud tuong PC chet -> cloud push -> PC cang
        # xung dot. Vong luan quan tu nuoi.
        # Nay: uu tien ban CUA PC. Luu y nguoc doi: trong `git rebase`, "ours" = upstream
        # (origin/main, tuc ban cua cloud) con "theirs" = commit dang duoc replay (ban cua
        # PC) -- nguoc voi truc giac. PC la nguon chinh nen dung -X theirs.
        # That bai thi ABORT sach roi thu lai, va bao loi to neu het luot.
        for lan in range(1, 4):
            subprocess.run(["git", "-C", ROOT, "fetch", "origin", "main"], check=False)
            r = subprocess.run(["git", "-C", ROOT, "rebase", "--autostash", "-X", "theirs",
                                "origin/main"], capture_output=True, text=True)
            if r.returncode != 0:
                subprocess.run(["git", "-C", ROOT, "rebase", "--abort"], check=False)
                log(f"rebase that bai (lan {lan}) -> da abort, thu lai.")
                continue
            if subprocess.run(["git", "-C", ROOT, "push"]).returncode == 0:
                open(MARKER, "w", encoding="utf-8").write(now().isoformat())
                log(f"da push (lan {lan}).")
                return
            log(f"push bi tu choi (lan {lan}) -> co commit moi tren origin, thu lai.")
        log("CANH BAO: khong push duoc sau 3 lan. Du lieu van nam local; nhip tim KHONG "
            "len duoc GitHub nen cloud se chay bu. Kiem tra `git status` trong repo.")
    except Exception as e:
        log("push err:", str(e)[:200])
        # Khong de lai rebase do dang cho lan chay sau (day chinh la cai gay ket 2026-08-21)
        don_dep_rebase_treo()


if __name__ == "__main__":
    main()
