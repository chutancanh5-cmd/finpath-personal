# -*- coding: utf-8 -*-
"""
update_orderflow.py -- Dong tien THAT cho watchlist -> docs/data/orderflow.json

Tai dung orderflow/feed.py (project Order Flow Lab):
  - fetch_ticks(sym, source="kbs"): tung lenh khop + side mua/ban CHU DONG
  - fetch_board(syms, source="vci"): so lenh bid/ask 3 muc + khoi ngoai
Tinh: %mua chu dong (ca phien + 15' gan nhat), net gia tri chu dong, lenh lon
(ca map), mat can bang so lenh. Chi DOC du lieu.

Khong thay duoc lenh tung nha dau tu (rieng tu) -- chi thay HANH VI GOP.

Usage: python update_orderflow.py [--push]
"""
import os
import sys
import io
import json
import glob
import datetime as dt
from datetime import timezone, timedelta

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("ACCEPT_TC", "tôi đồng ý")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "data", "orderflow.json")
WATCHLIST = os.path.join(HERE, "watchlist.txt")
STATE = os.path.join(HERE, "orderflow_state.json")
TREND_FILE = os.path.join(HERE, "orderflow_trend.json")
TREND_MAX = 72           # so diem xu huong trong ngay (~6h moi 5')
VN_TZ = timezone(timedelta(hours=7))
BIG_VND = 200e6          # 1 lenh khop >= 200tr -> "lenh lon" (hien trong app)
SHARK_VND = 1e9          # 1 lenh khop >= 1 ty -> canh bao "ca map" Discord
RECENT_MIN = 15          # cua so "gan day"


def log(*a):
    print("[orderflow]", *a, flush=True)


def market_open(now=None):
    n = now or dt.datetime.now(VN_TZ)
    if n.weekday() >= 5:
        return False
    t = n.hour * 60 + n.minute
    return (9 * 60 <= t <= 11 * 60 + 30) or (13 * 60 <= t <= 14 * 60 + 50)


def fetch_ticks(sym):
    """Lenh khop trong phien + side mua/ban CHU DONG (nguon kbs). Code goc FinPath,
    goi truc tiep vnstock public API (khong copy feed.py)."""
    import pandas as pd
    from vnstock.api.quote import Quote
    df = Quote(symbol=sym, source="kbs").intraday(page_size=5000)
    if df is None or len(df) == 0:
        return None
    df = df.rename(columns={"match_type": "side"})
    df["time"] = pd.to_datetime(df["time"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
    df["side"] = df["side"].astype(str).str.lower().str.strip()
    df = df.dropna(subset=["price"]).sort_values("time").reset_index(drop=True)
    return df[["time", "price", "volume", "side"]]


def read_watchlist():
    try:
        raw = open(WATCHLIST, encoding="utf-8").read()
        syms = [s.strip().upper() for s in raw.replace(",", "\n").split("\n")]
        return [s for s in syms if s and not s.startswith("#")]
    except Exception:
        return []


def analyze_ticks(df):
    """df [time, price, volume, side] -> cac chi so dong tien (gia *1000 = VND)."""
    import pandas as pd
    df = df.copy()
    df["val"] = df["price"] * 1000.0 * df["volume"]
    buy = df[df.side == "buy"]
    sell = df[df.side == "sell"]
    buy_val, sell_val = float(buy.val.sum()), float(sell.val.sum())
    tot = buy_val + sell_val
    buy_pct = buy_val / tot * 100 if tot else 50.0

    # 15 phut gan nhat
    tmax = df.time.max()
    rec = df[df.time >= tmax - pd.Timedelta(minutes=RECENT_MIN)]
    rb = float(rec[rec.side == "buy"].val.sum())
    rs = float(rec[rec.side == "sell"].val.sum())
    recent_buy_pct = rb / (rb + rs) * 100 if (rb + rs) else buy_pct

    # lenh lon (ca map)
    big = df[df.val >= BIG_VND].sort_values("val", ascending=False).head(6)
    big_trades = [{"time": t.strftime("%H:%M"), "price": round(p * 1000),
                   "vol": int(v), "val_bn": round(val / 1e9, 2), "side": s}
                  for t, p, v, val, s in zip(big.time, big.price, big.volume, big.val, big.side)]
    big_buy = float(big[big.side == "buy"].val.sum())
    big_sell = float(big[big.side == "sell"].val.sum())

    return {
        "last_price": round(float(df.price.iloc[-1]) * 1000),
        "buy_pct": round(buy_pct, 1),
        "recent_buy_pct": round(recent_buy_pct, 1),
        "net_val_bn": round((buy_val - sell_val) / 1e9, 2),
        "total_val_bn": round(tot / 1e9, 2),
        "n_ticks": len(df),
        "big_trades": big_trades,
        "big_net_bn": round((big_buy - big_sell) / 1e9, 2),
    }


def main():
    import universe
    syms = read_watchlist()
    opened = market_open()
    log(f"{len(syms)} ma | market_open={opened}")

    snap = universe.price_board_snapshot(syms)
    out = []
    for sym in syms:
        try:
            t = fetch_ticks(sym)
            if t is None or len(t) == 0:
                continue
            a = analyze_ticks(t)
        except Exception as e:
            log(f"{sym} loi:", str(e)[:70])
            continue
        d = snap.get(sym, {})
        ref = d.get("ref") or a["last_price"]
        price = a["last_price"]
        fr_net = (d.get("fbval") or 0) - (d.get("fsval") or 0)
        out.append({
            "sym": sym,
            "price": price,
            "pct": round((price / ref - 1) * 100, 2) if ref else 0,
            "buy_pct": a["buy_pct"],
            "recent_buy_pct": a["recent_buy_pct"],
            "net_val_bn": a["net_val_bn"],
            "total_val_bn": a["total_val_bn"],
            "n_ticks": a["n_ticks"],
            "big_trades": a["big_trades"],
            "big_net_bn": a["big_net_bn"],
            "foreign_net_bn": round(fr_net / 1e9, 2),
            "bid": d.get("bid") or [],
            "ask": d.get("ask") or [],
        })
    # sap xep: net chu dong manh nhat len dau
    out.sort(key=lambda x: x["net_val_bn"], reverse=True)

    update_trend(out)
    breadth = market_breadth(out)
    data = {"updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
            "market_open": opened, "market": breadth, "symbols": out}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log(f"da ghi {OUT}: {len(out)} ma")

    if "--discord" in sys.argv:
        alert_sharks(out)
    if "--push" in sys.argv:
        git_push()


def update_trend(out):
    """Tich luy chuoi %mua chu dong trong ngay; gan s['trend'] cho moi ma."""
    today = dt.datetime.now(VN_TZ).strftime("%Y-%m-%d")
    hm = dt.datetime.now(VN_TZ).strftime("%H:%M")
    try:
        tr = json.load(open(TREND_FILE, encoding="utf-8"))
    except Exception:
        tr = {}
    if tr.get("date") != today:
        tr = {"date": today, "points": {}}
    pts = tr["points"]
    for s in out:
        arr = pts.get(s["sym"], [])
        arr.append([hm, s["buy_pct"]])
        pts[s["sym"]] = arr[-TREND_MAX:]
        s["trend"] = [p[1] for p in pts[s["sym"]]]
    json.dump(tr, open(TREND_FILE, "w", encoding="utf-8"), ensure_ascii=False)


def market_breadth(out):
    """Dong tien toan watchlist: bao nhieu ma tien vao/ra, TB mua chu dong, net."""
    if not out:
        return {}
    buy = sum(1 for s in out if s["net_val_bn"] > 0)
    return {"n": len(out), "buy_count": buy, "sell_count": len(out) - buy,
            "avg_buy_pct": round(sum(s["buy_pct"] for s in out) / len(out), 1),
            "total_net_bn": round(sum(s["net_val_bn"] for s in out), 1)}


def alert_sharks(symbols):
    """Bao Discord cac LENH LON THAT (>=1 ty/lenh) chua tung bao trong ngay."""
    import notify
    webhook = "" if "--dry" in sys.argv else notify.resolve_webhook()  # --dry: khong dang that
    today = dt.datetime.now(VN_TZ).strftime("%Y-%m-%d")
    sent = notify.load_sent(STATE)
    embeds, newkeys = [], []
    for s in symbols:
        for t in s.get("big_trades", []):
            if t["val_bn"] < SHARK_VND / 1e9:
                continue
            key = f"{today}|{s['sym']}|{t['time']}|{t['val_bn']}"
            if key in sent or key in newkeys:
                continue
            newkeys.append(key)
            buy = t["side"] == "buy"
            embeds.append({
                "title": f"🦈 Lệnh lớn {'MUA' if buy else 'BÁN'} — {s['sym']}",
                "color": 0x2ecc71 if buy else 0xe74c3c,
                "description": (f"💥 **{t['vol']:,} cp = {t['val_bn']} tỷ** @ {t['price']:,} lúc {t['time']}\n"
                               f"Mua chủ động phiên **{s['buy_pct']}%** · net {s['net_val_bn']:+} tỷ · ngoại {s['foreign_net_bn']:+} tỷ").replace(",", "."),
                "footer": {"text": "Order flow thật (kbs) • lệnh khớp đơn lẻ ≥ 1 tỷ"}})
    if not embeds:
        log("Discord: khong co lenh lon moi.")
        return
    embeds = embeds[:10]
    if not webhook:
        log("[DRY-RUN] se gui", len(embeds), "ca map:")
        for e in embeds:
            print("  ", e["title"], "|", e["description"].replace("\n", " "))
    else:
        try:
            notify.send_discord(webhook, f"🦈 **{len(embeds)} lệnh lớn (cá mập)** — {today}", embeds, username="FinPath · Dòng tiền")
            log(f"Da gui {len(embeds)} ca map len Discord.")
        except Exception as e:
            log("Loi gui Discord:", str(e)[:120]); return
    for k in newkeys[:10]:
        sent.add(k)
    notify.save_sent(STATE, sent)


def git_push():
    import subprocess
    msg = "data: orderflow " + dt.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M")
    try:
        subprocess.run(["git", "-C", ROOT, "add", "docs/data/orderflow.json"], check=True)
        if subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"]).returncode != 0:
            subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)
            subprocess.run(["git", "-C", ROOT, "push"], check=True)
            log("da push")
    except Exception as e:
        log("git push err:", e)


if __name__ == "__main__":
    main()
