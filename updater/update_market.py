# -*- coding: utf-8 -*-
"""
update_market.py -- Tab "Thị trường": heatmap + thanh khoản + mã tác động index, theo từng sàn.

Ghi:
  docs/data/market.json          (mỗi lần chạy — heatmap top 40/sàn, breadth, tổng GTGD,
                                  mã tác động index ước tính theo vốn hóa, đường thanh khoản trong phiên)
  docs/data/market_intraday.json (state đường GTGD lũy kế trong phiên; tự reset khi sang ngày)
  docs/data/market_hist.json     (--append-hist: chuỗi GTGD top-30/sàn theo ngày;
                                  --backfill-hist: seed ~60 phiên từ nến top-30)

Mã tác động (điểm index) = (giá - tham chiếu) x KL niêm yết / Σ(tham chiếu x KL niêm yết) x điểm index tham chiếu.
Ước tính (bỏ qua điều chỉnh free-float/quỹ) — đủ đúng để xếp hạng kéo/đè.
Đơn vị: match_accumulated_value = TRIỆU đồng -> /1000 = tỷ. Giá price_board = VND chuẩn.
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

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "data", "market.json")
INTRA = os.path.join(ROOT, "docs", "data", "market_intraday.json")
HIST = os.path.join(ROOT, "docs", "data", "market_hist.json")
UNI_CACHE = os.path.join(HERE, "market_universe.json")
VN_TZ = timezone(timedelta(hours=7))
EXCHANGES = ["HOSE", "HNX", "UPCOM"]
INDEX_SYM = {"HOSE": "VNINDEX", "HNX": "HNXINDEX", "UPCOM": "UPCOMINDEX"}
HEATMAP_N = 40
LIQ_TOP = 30


def log(*a):
    print("[update_market]", *a, flush=True)


def setup_key():
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
        return True
    return False


PACE = 1.1 if setup_key() else 3.2


def now_vn():
    return dt.datetime.now(VN_TZ)


def market_open_vn():
    n = now_vn()
    if n.weekday() >= 5:
        return False
    t = n.hour * 60 + n.minute
    return (9 * 60 <= t <= 11 * 60 + 35) or (13 * 60 <= t <= 15 * 60 + 5)


def get_universe():
    """Danh sách mã STOCK theo sàn, cache 7 ngày."""
    if os.path.exists(UNI_CACHE):
        try:
            c = json.load(open(UNI_CACHE, encoding="utf-8"))
            if (dt.date.today() - dt.date.fromisoformat(c["date"])).days < 7:
                return c["symbols"]
        except Exception:
            pass
    from vnstock.api.listing import Listing
    ex = Listing(source="VCI").symbols_by_exchange()
    time.sleep(PACE)
    ex = ex[(ex["type"] == "STOCK") & (ex["exchange"].isin(["HSX", "HNX", "UPCOM"]))]
    syms = [s for s in ex["symbol"].tolist() if isinstance(s, str) and len(s) == 3]
    json.dump({"date": dt.date.today().isoformat(), "symbols": syms},
              open(UNI_CACHE, "w", encoding="utf-8"))
    return syms


def fetch_board(symbols):
    """price_board toàn bộ, trả list dict đã chuẩn hóa."""
    from vnstock.api.trading import Trading
    tr = Trading(source="VCI")
    rows = []
    for i in range(0, len(symbols), 100):
        chunk = symbols[i:i + 100]
        try:
            pb = tr.price_board(chunk)
        except Exception as e:
            log(f"chunk {i}: loi {str(e)[:50]}")
            time.sleep(PACE)
            continue
        pb.columns = ["_".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in pb.columns]
        for _, r in pb.iterrows():
            try:
                sym = str(r["listing_symbol"])
                exch = {"HSX": "HOSE"}.get(str(r["listing_exchange"]), str(r["listing_exchange"]))
                ref = float(r.get("match_reference_price") or 0)
                price = float(r.get("match_match_price") or 0) or ref
                if not ref or not price or exch not in EXCHANGES:
                    continue
                rows.append(dict(
                    sym=sym, exch=exch, price=price, ref=ref,
                    pct=(price / ref - 1) * 100,
                    val_ty=float(r.get("match_accumulated_value") or 0) / 1000.0,
                    shares=float(r.get("listing_listed_share") or 0),
                    ceil=float(r.get("match_ceiling_price") or 0),
                    floor=float(r.get("match_floor_price") or 0),
                ))
            except Exception:
                pass
        time.sleep(PACE)
    return rows


def fetch_indices():
    """Điểm index 3 sàn: last close + prev close (bar hôm nay có thể là live trong phiên)."""
    from vnstock.api.quote import Quote
    out = {}
    start = (dt.date.today() - dt.timedelta(days=15)).isoformat()
    for exch, sym in INDEX_SYM.items():
        try:
            df = Quote(symbol=sym, source="VCI").history(
                start=start, end=dt.date.today().isoformat(), interval="1D")
            df = df.rename(columns=str.lower).sort_values("time")
            cl = df["close"].astype(float).tolist()
            if len(cl) >= 2:
                out[exch] = dict(value=round(cl[-1], 2), prev=round(cl[-2], 2),
                                 pct=round((cl[-1] / cl[-2] - 1) * 100, 2))
        except Exception as e:
            log(f"index {sym}: {str(e)[:50]}")
        time.sleep(PACE)
    return out


def build_exchange(rows, idx):
    """Tổng hợp 1 sàn từ list row + info index."""
    up = sum(1 for r in rows if r["pct"] > 0.05)
    down = sum(1 for r in rows if r["pct"] < -0.05)
    flat = len(rows) - up - down
    n_ceil = sum(1 for r in rows if r["ceil"] and r["price"] >= r["ceil"])
    n_floor = sum(1 for r in rows if r["floor"] and r["price"] <= r["floor"])
    by_val = sorted(rows, key=lambda r: -r["val_ty"])
    heat = [dict(s=r["sym"], p=round(r["pct"], 2), v=round(r["val_ty"], 1),
                 c=1 if (r["ceil"] and r["price"] >= r["ceil"]) else (-1 if (r["floor"] and r["price"] <= r["floor"]) else 0))
            for r in by_val[:HEATMAP_N] if r["val_ty"] > 0]
    total_ty = sum(r["val_ty"] for r in rows)
    liq30_ty = sum(r["val_ty"] for r in by_val[:LIQ_TOP])

    impact = {"up": [], "down": [], "method": "capweight"}
    base = sum(r["ref"] * r["shares"] for r in rows if r["shares"] > 0)
    if base > 0 and idx:
        pts = []
        for r in rows:
            if r["shares"] <= 0:
                continue
            p = (r["price"] - r["ref"]) * r["shares"] / base * idx["prev"]
            if abs(p) > 1e-4:
                pts.append((r["sym"], p))
        pts.sort(key=lambda x: -x[1])
        impact["up"] = [dict(s=s, pts=round(p, 2)) for s, p in pts[:8] if p > 0]
        impact["down"] = [dict(s=s, pts=round(p, 2)) for s, p in reversed(pts[-8:]) if p < 0]

    return dict(index=idx or {}, breadth=dict(up=up, down=down, flat=flat, ceil=n_ceil, floor=n_floor),
                total_ty=round(total_ty, 0), liq30_ty=round(liq30_ty, 0), heatmap=heat, impact=impact)


def update_intraday(totals):
    """Đường GTGD lũy kế trong phiên (chỉ ghi điểm khi thị trường mở)."""
    today = now_vn().date().isoformat()
    state = {"date": today, "points": []}
    if os.path.exists(INTRA):
        try:
            old = json.load(open(INTRA, encoding="utf-8"))
            if old.get("date") == today:
                state = old
        except Exception:
            pass
    if market_open_vn():
        t = now_vn().strftime("%H:%M")
        if not state["points"] or state["points"][-1]["t"] != t:
            state["points"].append(dict(t=t, **{e: round(totals.get(e, 0), 0) for e in EXCHANGES}))
            state["points"] = state["points"][-120:]
    json.dump(state, open(INTRA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return state


def load_hist():
    if os.path.exists(HIST):
        try:
            return json.load(open(HIST, encoding="utf-8"))
        except Exception:
            pass
    return {"method": f"top{LIQ_TOP}", "days": []}


def append_hist(liq30):
    h = load_hist()
    today = now_vn().date().isoformat()
    h["days"] = [d for d in h["days"] if d["d"] != today]
    h["days"].append(dict(d=today, **{e: round(liq30.get(e, 0), 0) for e in EXCHANGES}))
    h["days"] = sorted(h["days"], key=lambda x: x["d"])[-90:]
    json.dump(h, open(HIST, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log(f"hist: {len(h['days'])} ngày")


def backfill_hist(board_rows, days=60):
    """Seed lịch sử GTGD từ nến top-30/sàn (close nghìn x volume -> tỷ = close*vol/1e6)."""
    from vnstock.api.quote import Quote
    start = (dt.date.today() - dt.timedelta(days=int(days * 1.8))).isoformat()
    agg = {}   # date -> {exch: ty}
    for exch in EXCHANGES:
        top = sorted([r for r in board_rows if r["exch"] == exch], key=lambda r: -r["val_ty"])[:LIQ_TOP]
        log(f"backfill {exch}: {len(top)} mã...")
        for r in top:
            for attempt in range(2):
                try:
                    df = Quote(symbol=r["sym"], source="VCI").history(
                        start=start, end=dt.date.today().isoformat(), interval="1D")
                    df = df.rename(columns=str.lower)
                    for _, b in df.iterrows():
                        d = str(pd.to_datetime(b["time"]).date())
                        v = float(b["close"]) * float(b.get("volume") or 0) / 1e6  # tỷ
                        agg.setdefault(d, {e: 0.0 for e in EXCHANGES})
                        agg[d][exch] += v
                    break
                except Exception as e:
                    log(f"  {r['sym']}: {str(e)[:40]}")
                    time.sleep(2)
            time.sleep(PACE)
    h = {"method": f"top{LIQ_TOP}", "days": [dict(d=d, **{e: round(v[e], 0) for e in EXCHANGES})
                                             for d, v in sorted(agg.items())][-days:]}
    json.dump(h, open(HIST, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log(f"backfill xong: {len(h['days'])} ngày")


def main():
    syms = get_universe()
    log(f"{len(syms)} mã, pace {PACE}s")
    rows = fetch_board(syms)
    log(f"board: {len(rows)} mã có giá")
    if len(rows) < 300:   # guard partial
        log("Quá ít dữ liệu (<300 mã) — GIỮ file cũ, thoát.")
        return
    indices = fetch_indices()

    exchanges = {}
    totals, liq30 = {}, {}
    for exch in EXCHANGES:
        ex_rows = [r for r in rows if r["exch"] == exch]
        exchanges[exch] = build_exchange(ex_rows, indices.get(exch))
        totals[exch] = exchanges[exch]["total_ty"]
        liq30[exch] = exchanges[exch]["liq30_ty"]

    intra = update_intraday(totals)

    if "--backfill-hist" in sys.argv:
        backfill_hist(rows)
    if "--append-hist" in sys.argv:
        append_hist(liq30)

    data = dict(updated_at=now_vn().isoformat(timespec="seconds"),
                market_open=market_open_vn(),
                exchanges=exchanges,
                intraday=intra,
                hist=load_hist())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    log("da ghi", OUT, f"({os.path.getsize(OUT)} bytes)")
    for e in EXCHANGES:
        b = exchanges[e]["breadth"]
        log(f"  {e}: GTGD {exchanges[e]['total_ty']:,.0f} tỷ | ▲{b['up']} ▼{b['down']} ={b['flat']} | "
            f"heatmap {len(exchanges[e]['heatmap'])} | impact +{len(exchanges[e]['impact']['up'])}/-{len(exchanges[e]['impact']['down'])}")


if __name__ == "__main__":
    main()
