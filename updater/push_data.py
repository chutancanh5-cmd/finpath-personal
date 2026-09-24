# -*- coding: utf-8 -*-
"""
push_data.py -- Gop & GIAM NHIP push docs/data/*.json len GitHub Pages.

Intraday chay moi 5 phut nhung GitHub Pages chi build ~10 lan/gio. Script nay
chi push neu da >= PUSH_MIN phut tu lan push truoc (marker .last_push), tranh
throttle + va cham git. --force bo qua gioi han (dung cho run_daily).

Usage: python push_data.py [--force]

Ma thoat: 0 = da push / khong co gi de push / chua toi luot; 1 = HONG (index ket,
commit hong, push hong). run_step.py ghi "loi rc=1" vao run_steps.log thay vi "OK".
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

# Moi file TRACKED ma pipeline PC ghi ra deu phai nam trong commit. File nao bi bo
# ngoai (nhu marketread_state.json truoc 2026-09-25) se luon "dirty" -> moi lan rebase
# bi autostash -> hom nao cloud cung sua file do thi `stash pop` va cham, de lai file
# chua gop (UU) trong index, va tu do MOI `git commit` deu hong. Da ket 2026-09-23 ->
# 2026-09-25 theo dung kieu nay. Workflow finpath-daily.yml cung add dung file nay.
TEP_DAY = ["docs/data", "updater/marketread_state.json"]

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


def file_chua_gop():
    """Danh sach path dang o trang thai chua gop (UU/AA/...) trong index."""
    r = subprocess.run(["git", "-C", ROOT, "diff", "--name-only", "--diff-filter=U"],
                       capture_output=True, text=True)
    return [p for p in (r.stdout or "").splitlines() if p.strip()]


def bao_index_ket(paths, boi_canh):
    """Index co file chua gop = moi commit se hong. Bao to, khong bao gio im lang."""
    ds = "\n".join(paths[:10])
    # log() chi in ASCII (console cp1258 cua Task Scheduler vo vi dau tieng Viet)
    log(f"CANH BAO: index co {len(paths)} file chua gop: {', '.join(paths[:5])}")
    bao_discord(
        "\U0001f6d1 Repo PC kẹt: có file chưa gộp",
        f"`push_data.py` gặp **{len(paths)} file chưa gộp** "
        f"trong index ({boi_canh}). Chừng nào còn file này thì "
        "**mọi `git commit` đều hỏng**, dữ liệu PC không lên "
        "GitHub, cloud chạy bù.\n\n"
        f"```\n{ds}\n```\n"
        "Nguyên nhân hay gặp: `rebase --autostash` pop va chạm. "
        "Bản thay đổi local nằm an toàn trong `git stash list` "
        "(autostash). Sửa: chọn bản đúng cho từng file rồi `git add`, "
        f"trong `{ROOT}`.")


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
                return 0
        except Exception:
            pass
    try:
        don_dep_rebase_treo()

        # Index ket (file chua gop) -> `git commit` chac chan hong. Ban cu de CalledProcess-
        # Error rot vao `except` ben duoi, chi log mot dong roi thoat 0: run_steps.log ghi
        # "push_data.py OK 0.2s" moi 5 phut suot 2026-09-23 -> 2026-09-25 trong khi khong
        # mot commit nao duoc tao. Phai kiem TRUOC (truoc ca canh bao un tac, vi hai canh
        # bao chung mot chan nhip Discord), bao va tra ma loi.
        ket = file_chua_gop()
        if ket:
            bao_index_ket(ket, "trước khi commit")
            return 1

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
                "Kiểm tra: `ssh -T git@github.com` (remote SSH) hoặc "
                "`gh auth status` (remote HTTPS, token hết hạn là "
                "nguyên nhân hay gặp nhất), rồi "
                f"`git -C {ROOT} status`.")

        subprocess.run(["git", "-C", ROOT, "add", "--"] + TEP_DAY, check=True)
        co_moi = subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"]).returncode != 0
        if not co_moi:
            # Khong co du lieu moi nhung con commit ket tu lan truoc -> van day. Ban cu
            # return o day, nen commit ket chi di duoc khi co du lieu moi (ngoai gio thi
            # nam lai toi phien sau).
            if ton == 0:
                log("khong co thay doi du lieu.")
                return 0
            log(f"khong co du lieu moi, nhung con {ton} commit chua len -> van push.")
        msg = "data: cap nhat " + now().strftime("%Y-%m-%d %H:%M")
        c = (subprocess.run(["git", "-C", ROOT, "commit", "-m", msg],
                            capture_output=True, text=True) if co_moi else None)
        if c is not None and c.returncode != 0:
            loi = ((c.stderr or "") + (c.stdout or ""))[-600:]
            log("git commit HONG:", loi.strip()[:300])
            bao_discord(
                "\U0001f6d1 Không commit được dữ liệu trên PC",
                f"`git commit` trong `push_data.py` trả mã {c.returncode}. "
                "Dữ liệu mới không vào được lịch sử, "
                "nên cũng không lên GitHub.\n\n"
                f"```\n{loi or '(khong co thong bao loi)'}\n```\n"
                f"Kiểm tra `git -C {ROOT} status`.")
            return 1

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
            # Rebase "thanh cong" van co the de lai index ket: khi `stash pop` cua
            # --autostash va cham, git cat thay doi vao `stash list`, in mot canh bao roi
            # van tra 0. Chinh la cach 2026-09-23 bat dau. Cac commit da rebase xong nen
            # van push, nhung phai bao va tra loi vi lan chay sau se khong commit duoc.
            ket = file_chua_gop()
            p = subprocess.run(["git", "-C", ROOT, "push"], capture_output=True, text=True)
            if p.returncode == 0:
                open(MARKER, "w", encoding="utf-8").write(now().isoformat())
                log(f"da push (lan {lan}).")
                if ket:
                    bao_index_ket(ket, "autostash pop va chạm sau rebase")
                    return 1
                return 0
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
                    "Remote SSH: kiểm tra `ssh -T git@github.com` "
                    "(khoá `~/.ssh/id_ed25519`). Remote HTTPS: "
                    "`gh auth login -h github.com`. Dữ liệu "
                    "vẫn nằm local, cloud chạy bù nên app "
                    "không chết.")
                return 1
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
            f"bù. Kiểm tra `ssh -T git@github.com` và `git -C {ROOT} status`.")
        return 1
    except Exception as e:
        log("push err:", str(e)[:200])
        # Khong de lai rebase do dang cho lan chay sau (day chinh la cai gay ket 2026-08-21)
        don_dep_rebase_treo()
        bao_discord(
            "\U0001f6d1 push_data.py gặp lỗi bất ngờ",
            f"```\n{type(e).__name__}: {str(e)[:500]}\n```\n"
            f"Kiểm tra `git -C {ROOT} status`.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
