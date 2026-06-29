# -*- coding: utf-8 -*-
"""
update_prices.py -- Lay bang gia watchlist + chi so tu vnstock, ghi docs/data/prices.json

Theo dung pattern HPA tracker: vnstock VCI, ep UTF-8 stdout, gio VN, optional --push.

Usage:
    python update_prices.py            # cap nhat prices.json
    python update_prices.py --push     # cap nhat + git add/commit/push (GitHub Pages)

Watchlist:
    Doc tu updater/watchlist.txt (moi dong/phay 1 ma). Neu khong co -> dung DEFAULT.
"""
import os
import sys
import io
import json
import math
import warnings
from datetime import datetime, date, timezone, timedelta

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass
warnings.filterwarnings("ignore")

SOURCE = "VCI"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "data", "prices.json")
WATCH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchlist.txt")
VN_TZ = timezone(timedelta(hours=7))
SPARK_BARS = 30  # so phien cho mini-chart

DEFAULT_WATCH = ["FPT", "HPG", "MWG", "VNM", "VCB", "ACB", "SSI", "VND", "MBB",
                 "STB", "DGC", "HSG", "VHM", "GVR", "PNJ", "VRE"]


def log(*a):
    print("[update_prices]", *a, flush=True)


def num(x):
    try:
        if x is None:
            return None
        f = float(x)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def norm_price(v):
    """VCI tra gia dang nghin (27.5) hoac VND (27500). Chuan hoa ve VND."""
    f = num(v)
    if f is None:
        return None
    return round(f * 1000) if 0 < f < 1000 else round(f)


def vn_now():
    return datetime.now(VN_TZ)


def read_watchlist():
    if os.path.exists(WATCH_FILE):
        try:
            with open(WATCH_FILE, encoding="utf-8") as f:
                raw = f.read()
            syms = [s.strip().upper() for s in raw.replace(",", "\n").split("\n")]
            syms = [s for s in syms if s and not s.startswith("#")]
            if syms:
                return syms
        except Exception as e:
            log("watchlist read err:", e)
    return DEFAULT_WATCH[:]


def setup_vnstock_key():
    key = os.getenv("VNSTOCK_API_KEY")
    if not key:
        kf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vnstock_key.txt")
        if os.path.exists(kf):
            try:
                with open(kf, encoding="utf-8") as f:
                    key = f.read().strip()
            except Exception:
                key = None
    if key and not key.startswith("#") and len(key) >= 10:
        os.environ["VNSTOCK_API_KEY"] = key
    try:
        import vnai
        st = vnai.check_api_key_status()
        log("vnstock tier:", st.get("tier"))
    except Exception:
        pass


def flatten_row(row, columns):
    """Bien 1 dong price_board (co the MultiIndex cot) thanh dict {ten_phang_thuong: gia_tri}."""
    out = {}
    for col in columns:
        if isinstance(col, tuple):
            key = "_".join(str(c) for c in col if c is not None and str(c) != "")
        else:
            key = str(col)
        out[key.lower().strip()] = row[col]
    return out


def pick(d, *keywords):
    """Lay gia tri dau tien co key chua TAT CA cac tu khoa (theo thu tu uu tien cac bo keyword)."""
    for kw_set in keywords:
        kws = kw_set if isinstance(kw_set, (list, tuple)) else [kw_set]
        for k, v in d.items():
            if all(w in k for w in kws):
                if v is not None and str(v) != "nan":
                    return v
    return None


def fetch_board(syms):
    from vnstock import Vnstock
    stock = Vnstock().stock(symbol=syms[0], source=SOURCE)
    try:
        df = stock.trading.price_board(syms)
    except TypeError:
        # mot so phien ban: price_board(symbols_list=...)
        df = stock.trading.price_board(symbols_list=syms)
    rows = []
    cols = list(df.columns)
    name_map = company_names(syms)
    for _, r in df.iterrows():
        d = flatten_row(r, cols)
        sym = pick(d, ["symbol"], ["ticker"])
        sym = str(sym).upper() if sym else None
        if not sym:
            continue
        ref = norm_price(pick(d, ["ref"], ["reference"]))
        price = norm_price(pick(d, ["match", "price"], ["last"], ["close"], ["price"]))
        if price is None:
            price = ref
        ceil = norm_price(pick(d, ["ceiling"], ["ceil"]))
        floor = norm_price(pick(d, ["floor"]))
        high = norm_price(pick(d, ["high"]))
        low = norm_price(pick(d, ["low"]))
        vol = num(pick(d, ["accumulated", "volume"], ["total", "volume"], ["volume"]))
        fb = num(pick(d, ["foreign", "buy", "volume"], ["foreign", "buy"]))
        fs = num(pick(d, ["foreign", "sell", "volume"], ["foreign", "sell"]))
        change = (price - ref) if (price is not None and ref) else None
        pctv = round(change / ref * 100, 2) if (change is not None and ref) else None
        rows.append({
            "sym": sym, "name": name_map.get(sym, ""),
            "price": price, "ref": ref, "change": change, "pct": pctv,
            "vol": int(vol) if vol else None, "ceil": ceil, "floor": floor,
            "high": high, "low": low,
            "fb": int(fb) if fb else None, "fs": int(fs) if fs else None,
            "spark": [],
        })
    return rows


def company_names(syms):
    """Ten ngan gon cho moi ma (best-effort, khong fail neu loi)."""
    out = {}
    try:
        from vnstock import Vnstock
        listing = Vnstock().stock(symbol=syms[0], source=SOURCE).listing
        df = listing.all_symbols()
        col_sym = "ticker" if "ticker" in df.columns else ("symbol" if "symbol" in df.columns else None)
        col_nm = next((c for c in ("organ_short_name", "organ_name", "company_name") if c in df.columns), None)
        if col_sym and col_nm:
            for _, r in df.iterrows():
                out[str(r[col_sym]).upper()] = str(r[col_nm])
    except Exception as e:
        log("names err (bo qua):", e)
    return out


def add_sparklines(rows):
    from vnstock import Vnstock
    start = (date.today() - timedelta(days=80)).isoformat()
    end = date.today().isoformat()
    for r in rows:
        try:
            h = Vnstock().stock(symbol=r["sym"], source=SOURCE).quote.history(
                start=start, end=end, interval="1D")
            closes = [num(x) for x in h["close"].tolist() if num(x) is not None]
            r["spark"] = [round(c, 2) for c in closes[-SPARK_BARS:]]
        except Exception as e:
            log("spark", r["sym"], "skip:", e)


def fetch_index(symbol):
    from vnstock import Vnstock
    try:
        h = Vnstock().stock(symbol=symbol, source=SOURCE).quote.history(
            start=(date.today() - timedelta(days=15)).isoformat(),
            end=date.today().isoformat(), interval="1D")
        closes = [num(x) for x in h["close"].tolist() if num(x) is not None]
        if len(closes) >= 2:
            cur, prev = closes[-1], closes[-2]
            return {"value": round(cur, 2), "change": round(cur - prev, 2),
                    "pct": round((cur - prev) / prev * 100, 2)}
    except Exception as e:
        log("index", symbol, "err:", e)
    return None


def main():
    syms = read_watchlist()
    log("watchlist:", len(syms), "ma")
    setup_vnstock_key()

    rows = fetch_board(syms)
    log("board:", len(rows), "dong")
    add_sparklines(rows)

    market = {}
    for key, sym in (("vnindex", "VNINDEX"), ("vn30", "VN30"), ("hnxindex", "HNXINDEX")):
        d = fetch_index(sym)
        if d:
            market[key] = d
    log("indices:", list(market.keys()))

    data = {
        "updated_at": vn_now().isoformat(timespec="seconds"),
        "market": market,
        "rows": rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    log("da ghi", OUT, f"({os.path.getsize(OUT)} bytes)")

    if "--push" in sys.argv:
        git_push()


def git_push():
    import subprocess
    msg = "data: cap nhat bang gia " + vn_now().strftime("%Y-%m-%d %H:%M")
    try:
        subprocess.run(["git", "-C", ROOT, "add", "docs/data/prices.json"], check=True)
        r = subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"])
        if r.returncode != 0:
            subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)
            subprocess.run(["git", "-C", ROOT, "push"], check=True)
            log("da push len GitHub")
        else:
            log("khong co thay doi, bo qua push")
    except Exception as e:
        log("git push err:", e)


if __name__ == "__main__":
    main()
