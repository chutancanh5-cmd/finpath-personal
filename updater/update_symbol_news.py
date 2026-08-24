# -*- coding: utf-8 -*-
"""
update_symbol_news.py -- CBTT & tin doanh nghiep theo TUNG MA -> docs/data/symbol_news.json

VI SAO CO FILE NAY (25/08/2026)
================================
Truoc do Prime Finance co day du tin VI MO (news.json) nhung KHONG co mot dong nao
ve tung doanh nghiep. Trang bao "TCH: MUA" ma khong noi duoc TCH vua cong bo gi.
Do la khoang trong lon nhat trong phan tin cua ung dung: tin vi mo thi ai cung doc
duoc o bao, con CBTT cua dung 60 ma trong ro thi phai tu gom.

LAY MA NAO
==========
KHONG quet ca 60 ma moi lan chay. Chi lay ma DANG CO CHUYEN:
  - co tin hieu MUA/BAN hom nay, hoac
  - dang nam giu (held=true)
Ly do: moi call ~1-2s va phan lon ma khong ra tin gi trong 14 ngay. Quet ca ro la
~90s doi lay gan nhu toan dong rong.

BON GIOI HAN CUA NGUON (do that tren VPB/HPG/FPT ngay 25/08/2026)
==================================================================
  1. url LUON RONG -> khong co link de bam. File nay khong ghi truong url.
  2. category LUON None -> phan loai bang tien to tieu de: "VPB: ..." = CBTT
     chinh thuc, con lai = bai bao.
  3. Lich su chi ~3 thang, 14-33 tin/ma.
  4. Chi co TIEU DE va summary, khong co noi dung day du.

Usage:
    python update_symbol_news.py            # ghi symbol_news.json
    python update_symbol_news.py --push     # + git commit & push
"""
import os
import sys
import io
import json
import time
import warnings
import datetime as dt
from datetime import timezone, timedelta

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SIGNALS = os.path.join(ROOT, "docs", "data", "signals.json")
OUT = os.path.join(ROOT, "docs", "data", "symbol_news.json")
VN_TZ = timezone(timedelta(hours=7))

DAYS = 21          # cua so tin
PER_SYM = 5        # so tin toi da moi ma
PACE = 1.1         # ton trong rate limit vnstock tra phi (~60 req/phut)
MAX_SYMS = 60      # = ca ro. Tran nay chi de chan chay loan, khong de cat bot viec:
                   # 60 ma x ~2.5s = ~2.5 phut, chap nhan duoc cho mot lan chay/ngay.
                   # Neu co cat thi PHAI log ra (xem main) — cat am tham se doc thanh
                   # "cac ma con lai khong co tin", trong khi that ra chua he hoi.


def log(*a):
    print("[symbol_news]", *a, flush=True)


def setup_vnstock_key():
    key = os.getenv("VNSTOCK_API_KEY")
    if not key:
        kf = os.path.join(HERE, "vnstock_key.txt")
        if os.path.exists(kf):
            try:
                key = open(kf, encoding="utf-8").read().strip()
            except Exception:
                key = None
    if key and not key.startswith("#") and len(key) >= 10:
        os.environ["VNSTOCK_API_KEY"] = key


def pick_symbols():
    """Ma dang co chuyen: co tin hieu hom nay hoac dang nam giu."""
    try:
        d = json.load(open(SIGNALS, encoding="utf-8"))
    except Exception as e:
        log("khong doc duoc signals.json:", str(e)[:80])
        return []
    out = []
    for s in d.get("signals", []):
        if s.get("action") in ("BUY", "SELL") or s.get("held"):
            sym = str(s.get("sym") or "").strip().upper()
            if sym and sym not in out:
                out.append(sym)
    return out


def fetch_news(sym):
    """Tin/CBTT gan day cua mot ma. Tra [] khi loi (khong lam hong ca lan chay)."""
    try:
        from vnstock_data.api.company import Company
    except Exception:
        try:
            from vnstock.api.company import Company
        except Exception:
            log("khong co thu vien vnstock -> bo qua")
            return []
    try:
        import pandas as pd
        df = Company(symbol=sym, source="VCI").news()
    except Exception as e:
        # vnstock boc moi loi thanh RetryError -> boc lai de log ra nguyen nhan that
        ex = e
        la = getattr(getattr(e, "last_attempt", None), "exception", None)
        if la:
            try:
                ex = la()
            except Exception:
                pass
        log(f"  {sym}: loi {type(ex).__name__}: {str(ex)[:70]}")
        return []
    if df is None or len(df) == 0:
        return []
    try:
        df = df.copy()
        df["publish_time"] = pd.to_datetime(df["publish_time"], errors="coerce")
        df = df.dropna(subset=["publish_time"]).sort_values("publish_time",
                                                            ascending=False)
        cutoff = dt.datetime.now() - timedelta(days=DAYS)
        df = df[df["publish_time"] >= cutoff]
        pre = f"{sym}:"
        out = []
        for _, r in df.head(PER_SYM).iterrows():
            title = str(r.get("title") or "").strip()
            if not title:
                continue
            out.append({
                "date": r["publish_time"].strftime("%Y-%m-%d"),
                "title": title,
                "kind": "CBTT" if title.upper().startswith(pre) else "TIN",
            })
        return out
    except Exception as e:
        log(f"  {sym}: loi xu ly {str(e)[:70]}")
        return []


def main():
    setup_vnstock_key()
    syms = pick_symbols()
    if not syms:
        log("khong co ma nao dang co chuyen -> ghi file rong")
    if len(syms) > MAX_SYMS:
        log(f"co {len(syms)} ma, cat con {MAX_SYMS} (tran an toan)")
        syms = syms[:MAX_SYMS]

    log(f"quet {len(syms)} ma: {', '.join(syms) if syms else '(khong co)'}")
    by_sym, n_tin, n_cbtt = {}, 0, 0
    for i, sym in enumerate(syms):
        items = fetch_news(sym)
        if items:
            by_sym[sym] = items
            n_tin += len(items)
            n_cbtt += sum(1 for x in items if x["kind"] == "CBTT")
            log(f"  {sym}: {len(items)} tin")
        if i < len(syms) - 1:
            time.sleep(PACE)

    data = {
        "updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
        "window_days": DAYS,
        "note": (f"CBTT & tin doanh nghiệp {DAYS} ngày gần nhất của các mã đang có tín "
                 f"hiệu hoặc đang nắm giữ. Nguồn không cung cấp link bài, chỉ có tiêu đề. "
                 f"Phần lớn CBTT là thủ tục hành chính, không phải tin ảnh hưởng giá."),
        "scanned": syms,
        "count": {"symbols_with_news": len(by_sym), "items": n_tin, "cbtt": n_cbtt},
        "by_symbol": by_sym,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    log(f"da ghi {OUT}: {len(by_sym)}/{len(syms)} mã có tin, "
        f"{n_tin} tin ({n_cbtt} CBTT), {os.path.getsize(OUT)} bytes")

    if "--push" in sys.argv:
        git_push()


def git_push():
    import subprocess
    msg = ("data: cap nhat CBTT theo ma "
           + dt.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M"))
    try:
        subprocess.run(["git", "-C", ROOT, "add", "docs/data/symbol_news.json"],
                       check=True)
        r = subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"])
        if r.returncode != 0:
            subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)
            subprocess.run(["git", "-C", ROOT, "push"], check=True)
            log("da push len GitHub")
        else:
            log("khong co thay doi -> khong push")
    except Exception as e:
        log("git loi:", str(e)[:120])


if __name__ == "__main__":
    main()
