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
MARKER_CANH_BAO = os.path.join(HERE, ".last_push_alert")
VN_TZ = timezone(timedelta(hours=7))
PUSH_MIN = 12
sys.path.insert(0, HERE)

# Bao nhieu commit local chua len GitHub thi coi la UN TAC va phai keu.
# 20 commit ~ 100 phut o nhip 5 phut: du lau de khong keu vi mot lan mang chap chon,
# du som de khong de troi ca phien nhu 2026-09-09 (80 commit / 7 tieng).
NGUONG_UN_TAC = 20
# Keu lai sau ngan nay phut. Task chay 5 phut/lan nen khong co chan nay se thanh
# 12 tin nhan Discord moi gio cho cung MOT su co.
CANH_BAO_CACH_NHAU = 180


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


# --------------------------------------------------------------- chan doan loi push
# Phan loai stderr cua `git push`. Day la ly do ton tai cua ca khoi ben duoi: vong thu
# lai duoc viet cho tinh huong "origin co commit moi" -- rebase roi day lai la chua.
# Nhung loi DANG NHAP thi rebase bao nhieu lan cung vo ich, ma ban cu van quay du 3
# vong roi im lang bo qua. Ngay 2026-09-09 token gh het han: cu 5 phut task lai commit
# them mot cai va nuot loi -> 80 commit / 7 tieng nam lai local, khong ai biet cho toi
# khi mo repo ra xem.
_DAU_HIEU_AUTH = (
    "could not read username", "could not read password", "authentication failed",
    "invalid username or password", "terminal prompts disabled", "invalid credentials",
    "support for password authentication", "permission denied", "403 forbidden",
    "the requested url returned error: 403",
)
_DAU_HIEU_TU_CHOI = ("rejected", "non-fast-forward", "fetch first")
_DAU_HIEU_MANG = ("could not resolve host", "failed to connect", "unable to access",
                  "timed out", "connection reset", "operation timed out")


def loai_loi_push(txt):
    """stderr cua git push -> 'auth' | 'tu_choi' | 'mang' | 'khac'."""
    t = (txt or "").lower()
    if any(k in t for k in _DAU_HIEU_AUTH):
        return "auth"
    if any(k in t for k in _DAU_HIEU_TU_CHOI):
        return "tu_choi"
    if any(k in t for k in _DAU_HIEU_MANG):
        return "mang"
    return "khac"


def so_commit_chua_len():
    """So commit dang nam local ma origin/main chua co. 0 neu khong doc duoc."""
    r = subprocess.run(["git", "-C", ROOT, "rev-list", "--count", "origin/main..HEAD"],
                       capture_output=True, text=True)
    try:
        return int((r.stdout or "0").strip())
    except ValueError:
        return 0


def bao_discord(tieu_de, than):
    """Bao su co day du lieu ve Discord, co chan nhip de khong spam.

    That bai o day KHONG duoc lam hong luong chinh -- day chi la lop keu cuu."""
    try:
        if os.path.exists(MARKER_CANH_BAO):
            truoc = dt.datetime.fromisoformat(
                open(MARKER_CANH_BAO, encoding="utf-8").read().strip())
            if (now() - truoc).total_seconds() / 60 < CANH_BAO_CACH_NHAU:
                log("da canh bao gan day -> khong ban lai (tranh spam).")
                return
    except Exception:
        pass
    try:
        import notify
        hook = notify.resolve_webhook()
        if not hook:
            log("khong tim thay webhook Discord -> chi ghi log.")
            return
        notify.send_discord(hook, "", [{"title": tieu_de, "color": 0xe74c3c,
                                        "description": than[:3900]}],
                            username="FinPath · Đẩy dữ liệu")
        open(MARKER_CANH_BAO, "w", encoding="utf-8").write(now().isoformat())
        log("da bao Discord ve su co day du lieu.")
    except Exception as e:
        log("bao Discord that bai:", str(e)[:120])


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

        # Canh bao UN TAC truoc khi lam gi them. Chan nay khong quan tam nguyen nhan la
        # gi (token, mang, rebase treo, remote doi) -- no chi do MOT thu duy nhat dang
        # tin cay: bao nhieu commit da nam lai local. Nho vay no bat duoc ca nhung kieu
        # hong chua tung gap, thay vi chi nhung kieu da liet ke o _DAU_HIEU_* ben tren.
        ton = so_commit_chua_len()
        if ton >= NGUONG_UN_TAC:
            log(f"CANH BAO: {ton} commit chua len origin/main.")
            bao_discord(
                f"⚠️ {ton} commit dữ liệu chưa lên "
                f"được GitHub",
                f"`push_data.py` trên PC đã commit **{ton}** lần mà "
                "chưa đẩy lên origin/main được. "
                "Dữ liệu vẫn nằm local, và vì nhịp tim "
                "không lên được GitHub nên cloud sẽ "
                "chạy bù — app không chết, nhưng PC "
                "đang chạy không.\n\n"
                "Kiểm tra: `gh auth status` (token hết hạn là "
                "nguyên nhân hay gặp nhất), rồi "
                f"`git -C {ROOT} status`.")

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
        loi_cuoi = ""
        for lan in range(1, 4):
            subprocess.run(["git", "-C", ROOT, "fetch", "origin", "main"], check=False)
            r = subprocess.run(["git", "-C", ROOT, "rebase", "--autostash", "-X", "theirs",
                                "origin/main"], capture_output=True, text=True)
            if r.returncode != 0:
                subprocess.run(["git", "-C", ROOT, "rebase", "--abort"], check=False)
                log(f"rebase that bai (lan {lan}) -> da abort, thu lai.")
                loi_cuoi = ((r.stderr or "") + (r.stdout or ""))[-500:]
                continue
            p = subprocess.run(["git", "-C", ROOT, "push"], capture_output=True, text=True)
            if p.returncode == 0:
                open(MARKER, "w", encoding="utf-8").write(now().isoformat())
                log(f"da push (lan {lan}).")
                return
            loi_cuoi = ((p.stderr or "") + (p.stdout or ""))[-500:]
            loai = loai_loi_push(loi_cuoi)
            if loai == "auth":
                # Thu lai la vo ich: khong thao tac nao trong script nay sua duoc thong
                # tin dang nhap. Keu NGAY thay vi quay du 3 vong roi im lang.
                log("push hong vi DANG NHAP -> thu lai vo ich, bao ngay.")
                bao_discord(
                    "\U0001f511 Không đẩy được dữ "
                    "liệu: lỗi đăng nhập GitHub",
                    "`git push` từ PC hỏng vì **không xác "
                    "thực được** — thử lại bao "
                    "nhiêu lần cũng vô ích, nên bot "
                    "dừng ở đây.\n\n"
                    f"```\n{loi_cuoi[-600:]}\n```\n"
                    "Sửa: chạy `gh auth login -h github.com` rồi "
                    "kiểm tra bằng `gh auth status`. Dữ liệu "
                    "vẫn nằm local, cloud chạy bù nên app "
                    "không chết.")
                return
            log(f"push that bai (lan {lan}, loai {loai}) -> thu lai.")
        log("CANH BAO: khong push duoc sau 3 lan. Du lieu van nam local; nhip tim KHONG "
            "len duoc GitHub nen cloud se chay bu. Kiem tra `git status` trong repo.")
        bao_discord(
            "⚠️ Không đẩy được dữ liệu "
            "lên GitHub (3 lần đều hỏng)",
            "`push_data.py` trên PC thử 3 lần đều không "
            "đẩy được.\n\n"
            f"```\n{loi_cuoi[-600:] or '(khong co thong bao loi)'}\n```\n"
            "Dữ liệu vẫn nằm local, cloud sẽ chạy "
            f"bù. Kiểm tra `gh auth status` và `git -C {ROOT} status`.")
    except Exception as e:
        log("push err:", str(e)[:200])
        # Khong de lai rebase do dang cho lan chay sau (day chinh la cai gay ket 2026-08-21)
        don_dep_rebase_treo()


if __name__ == "__main__":
    main()
