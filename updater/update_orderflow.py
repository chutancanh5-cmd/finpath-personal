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
VN_TZ = timezone(timedelta(hours=7))
BIG_VND = 200e6          # 1 lenh khop >= 200tr -> "lenh lon"
RECENT_MIN = 15          # cua so "gan day"


def log(*a):
    print("[orderflow]", *a, flush=True)


def find_feed_dir():
    home = os.path.expanduser("~")
    for pat in (os.path.join(home, "OneDrive", "*", "Claude", "Projects", "TradingView", "orderflow", "feed.py"),
                os.path.join(home, "*", "Claude", "Projects", "TradingView", "orderflow", "feed.py")):
        hits = glob.glob(pat)
        if hits:
            return os.path.dirname(hits[0])
    return None


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
    feed_dir = find_feed_dir()
    if not feed_dir:
        log("Khong tim thay orderflow/feed.py. Bo qua.")
        return
    log("feed dir:", feed_dir)
    sys.path.insert(0, feed_dir)
    import feed as F

    syms = read_watchlist()
    opened = F.market_open()
    log(f"{len(syms)} ma | market_open={opened}")

    board = F.fetch_board(syms, source="vci") or {}
    out = []
    for sym in syms:
        try:
            t = F.fetch_ticks(sym, source="kbs")
            if t is None or len(t) == 0:
                continue
            a = analyze_ticks(t)
        except Exception as e:
            log(f"{sym} loi:", str(e)[:70])
            continue
        b = board.get(sym, {})
        ref = b.get("ref") or a["last_price"]
        price = a["last_price"]
        fr_net = (b.get("fr_buy_val", 0) or 0) - (b.get("fr_sell_val", 0) or 0)
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
            "bid": [[round(b.get(f"bid{l}_p", 0)), int(b.get(f"bid{l}_v", 0) or 0)] for l in (1, 2, 3)],
            "ask": [[round(b.get(f"ask{l}_p", 0)), int(b.get(f"ask{l}_v", 0) or 0)] for l in (1, 2, 3)],
        })
    # sap xep: net chu dong manh nhat len dau
    out.sort(key=lambda x: x["net_val_bn"], reverse=True)

    data = {"updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
            "market_open": opened, "symbols": out}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log(f"da ghi {OUT}: {len(out)} ma")

    if "--push" in sys.argv:
        git_push()


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
