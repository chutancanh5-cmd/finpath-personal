# -*- coding: utf-8 -*-
"""
update_trailstop.py -- Du lieu cho muc "Chan lai" -> docs/data/trailstop.json

Muc Chan lai trong app tinh THANG STOP ngay tren may (vi the nguoi dung nhap nam trong
localStorage cua dien thoai, may chu khong biet). De tinh duoc, app can lich su gia
tung phien ke tu ngay mua: dinh cao nhat va cac day thap nhat. File nay cung cap dung
phan do, dang nen gon.

Ro ma: 60 ma PrimeTrade (UT Bot v2 - noi phat sinh phan lon lenh mua) + danh muc theo doi
trong watchlist.txt. Ma nao khong co trong file thi app se bao nguoi dung them vao danh
muc theo doi, lan cap nhat sau se co.

THANG STOP (ket qua backtest 687 cau hinh x 620 ma, 2010-2026; xem trailstop/reports):
    Cap 1  ngay khi mua       cat lo -8% so voi gia von      -> R = 8%
    Cap 2  T+2 hang ve        dang co lai -> stop ve gia von
    Cap 3  khi lai >= +32%    stop bam theo dinh, cach dinh 25%
Tham so duoc ghi thang vao file de app va may chu khong bao gio lech nhau.

Usage:
    python update_trailstop.py
    python update_trailstop.py --push
"""
import datetime as dt
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "data", "trailstop.json")
UTBOT_CFG = os.path.join(HERE, "utbot_config.json")
WATCHLIST = os.path.join(HERE, "watchlist.txt")

VN_TZ = dt.timezone(dt.timedelta(hours=7))
SESSIONS = 320          # ~15 thang: du cho moi vi the con dang dung thang stop
PACE = 1.15             # tai khoan vnstock tra phi ~60 request/phut

THANG = dict(sl_pct=0.08, be_on_settle=True, be_buffer=0.0,
             lock_trigger_r=4.0, trail_pct=0.25, settle=2, near_stop=0.03,
             fee_buy=0.0015, fee_sell=0.0025)


def log(*a):
    print(dt.datetime.now(VN_TZ).strftime("%H:%M:%S"), *a, flush=True)


def describe_exc(e, n=110):
    """vnstock_data boc moi loi trong tenacity RetryError (khong reraise) nen str(e)
    chi ra dia chi Future. Boc ra exception that de con phan biet 429/403/timeout."""
    inner = e
    try:
        la = getattr(e, "last_attempt", None)
        if la is not None and la.failed:
            inner = la.exception() or e
    except Exception:
        inner = e
    return f"{type(inner).__name__}: {inner}"[:n]


def doc_universe():
    syms, nguon = [], {}
    try:
        cfg = json.load(open(UTBOT_CFG, encoding="utf-8"))
        for s in cfg.get("symbols", {}):
            syms.append(s)
            nguon[s] = "PrimeTrade"
    except Exception as e:
        log("khong doc duoc utbot_config.json:", e)
    try:
        txt = open(WATCHLIST, encoding="utf-8").read()
        for line in txt.splitlines():
            line = line.split("#")[0]
            for s in line.replace(",", " ").split():
                s = s.strip().upper()
                if s and s not in nguon:
                    syms.append(s)
                    nguon[s] = "danh muc"
    except Exception as e:
        log("khong doc duoc watchlist.txt:", e)
    return syms, nguon


def lay_lich_su(vs, sym, tu_ngay):
    for src in ("VCI", "KBS"):
        try:
            df = vs.Quote(symbol=sym, source=src).history(
                start=tu_ngay, end=dt.date.today().strftime("%Y-%m-%d"), interval="1D")
            if df is None or not len(df):
                continue
            df = df.rename(columns={"time": "date"})
            df["date"] = __import__("pandas").to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            df = df.sort_values("date").drop_duplicates("date")
            df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)]
            return df.tail(SESSIONS), src
        except Exception as e:
            log(f"  {sym}: nguon {src} loi -> {describe_exc(e)}")
    return None, None


def main():
    import vnstock_data as vs

    syms, nguon = doc_universe()
    log(f"Ro ma: {len(syms)} ({sum(1 for v in nguon.values() if v == 'PrimeTrade')} PrimeTrade "
        f"+ {sum(1 for v in nguon.values() if v == 'danh muc')} danh muc theo doi)")
    tu_ngay = (dt.date.today() - dt.timedelta(days=int(SESSIONS * 1.55))).strftime("%Y-%m-%d")

    ma = {}
    ngay_moi_nhat = ""
    loi = []
    t0 = time.time()
    for i, s in enumerate(syms):
        df, src = lay_lich_su(vs, s, tu_ngay)
        time.sleep(PACE)
        if df is None or len(df) < 5:
            loi.append(s)
            continue
        # Gia gui cho app la DONG (vnstock tra theo nghin) va lam tron ve so nguyen:
        # thang stop khong can le hon 1 dong, ma lam tron giup file nho di mot nua.
        # Can ca GIA MO CUA: khi gia ho xuong duoi muc stop thi lenh khop o gia mo cua
        # chu khong phai o muc stop - thieu cot nay se bao sai muc ban thuc te.
        ma[s] = dict(
            d=df["date"].tolist(),
            o=[int(round(x * 1000)) for x in df["open"]],
            h=[int(round(x * 1000)) for x in df["high"]],
            l=[int(round(x * 1000)) for x in df["low"]],
            c=[int(round(x * 1000)) for x in df["close"]],
        )
        ngay_moi_nhat = max(ngay_moi_nhat, df["date"].iloc[-1])
        if (i + 1) % 20 == 0:
            log(f"  {i+1}/{len(syms)} ({time.time()-t0:.0f}s)")

    data = dict(
        updated_at=dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
        phien_moi_nhat=ngay_moi_nhat,
        thang=THANG,
        nguon_ma=nguon,
        so_ma=len(ma),
        loi=loi,
        ma=ma,
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(OUT) / 1024
    log(f"Da ghi {OUT} — {len(ma)} ma, phien {ngay_moi_nhat}, {kb:.0f} KB"
        + (f", loi {len(loi)}: {loi[:10]}" if loi else ""))

    if "--push" in sys.argv:
        import subprocess
        msg = "data: cap nhat du lieu chan lai " + dt.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M")
        try:
            subprocess.run(["git", "-C", ROOT, "add", "docs/data/trailstop.json"], check=True)
            if subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"]).returncode != 0:
                subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)
                subprocess.run(["git", "-C", ROOT, "push"], check=True)
                log("da push len GitHub")
            else:
                log("khong co thay doi, bo qua push")
        except Exception as e:
            log("git push err:", e)


if __name__ == "__main__":
    main()
