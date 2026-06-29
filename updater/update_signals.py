# -*- coding: utf-8 -*-
"""
update_signals.py -- Sinh khuyen nghi DC55/30 -> docs/data/signals.json

Tai dung NGUYEN logic cua bot/discord_signal_bot.py (deployed):
  MUA  : close > dinh cao nhat 55 phien truoc (breakout)
  BAN  : close < day thap nhat 30 phien truoc (thoat)
Khung ngay (1D), san HOSE, ro 16 ma. Chay sau 15:00 (cuoi phien).
Bo sung: tinh lai/lo cho vi the dang nam (HOLD) tu gia vao lenh.

Usage:
    python update_signals.py            # ghi signals.json
    python update_signals.py --push     # + git commit & push (GitHub Pages)
"""
import os
import sys
import io
import json
import time
import math
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

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "data", "signals.json")
VN_TZ = timezone(timedelta(hours=7))

# Ro 16 ma + tham so DC55/30 -- dong bo voi bot/discord_signal_bot.py
BASKET = ["PDR", "VIB", "SSI", "TCB", "MWG", "SIP", "DIG", "GEX",
          "KDH", "LPB", "FPT", "FRT", "FTS", "HPG", "VSC", "PVT"]
SECTOR = {"PDR": "BĐS", "VIB": "Ngân hàng", "SSI": "Chứng khoán", "TCB": "Ngân hàng",
          "MWG": "Bán lẻ", "SIP": "KCN", "DIG": "BĐS", "GEX": "Tập đoàn", "KDH": "BĐS",
          "LPB": "Ngân hàng", "FPT": "Công nghệ", "FRT": "Bán lẻ", "FTS": "Chứng khoán",
          "HPG": "Thép", "VSC": "Cảng", "PVT": "Vận tải"}
UP, DN = 55, 30


def log(*a):
    print("[update_signals]", *a, flush=True)


def vnd(x):
    return f"{x:,.0f}".replace(",", ".")


def setup_vnstock_key():
    key = os.getenv("VNSTOCK_API_KEY")
    if not key:
        kf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vnstock_key.txt")
        if os.path.exists(kf):
            try:
                key = open(kf, encoding="utf-8").read().strip()
            except Exception:
                key = None
    if key and not key.startswith("#") and len(key) >= 10:
        os.environ["VNSTOCK_API_KEY"] = key


def fetch(sym):
    """Copy tu bot: OHLC ngay, gia *1000 ve VND."""
    from vnstock.api.quote import Quote
    start = (dt.date.today() - dt.timedelta(days=900)).isoformat()
    df = Quote(symbol=sym, source="VCI").history(
        start=start, end=dt.date.today().isoformat(), interval="1D")
    df = df.rename(columns=str.lower)
    for c in ("open", "high", "low", "close"):
        df[c] = df[c] * 1000.0
    df["date"] = pd.to_datetime(df["time"]).dt.date
    return df[["date", "open", "high", "low", "close"]].reset_index(drop=True)


def analyze(df):
    """Nhu bot, bo sung entry_price/entry_date de tinh lai/lo vi the dang nam."""
    df = df.copy()
    df["hh"] = df.high.rolling(UP).max().shift(1)
    df["ll"] = df.low.rolling(DN).min().shift(1)
    pos, last_i, last_type = 0, -1, None
    entry_price, entry_date = None, None
    h, l, c = df.hh.values, df.ll.values, df.close.values
    dates = df.date.values
    for i in range(len(df)):
        if pos == 0 and not np.isnan(h[i]) and c[i] > h[i]:
            pos, last_i, last_type = 1, i, "BUY"
            entry_price, entry_date = float(c[i]), str(dates[i])[:10]
        elif pos == 1 and not np.isnan(l[i]) and c[i] < l[i]:
            pos, last_i, last_type = 0, i, "SELL"
    last = df.iloc[-1]
    return dict(pos=pos, close=float(last.close), entry=float(last.hh) if not np.isnan(last.hh) else None,
                exit=float(last.ll) if not np.isnan(last.ll) else None,
                date=str(last.date)[:10], signal_today=(last_i == len(df) - 1),
                last_type=last_type, entry_price=entry_price, entry_date=entry_date)


def build_signal(sym, r):
    """Map ket qua analyze -> 1 the khuyen nghi (hoac None neu dang cho)."""
    sec = SECTOR.get(sym, "")
    # tin hieu MOI hom nay (vao/thoat trong phien gan nhat)
    if r["signal_today"] and r["last_type"] in ("BUY", "SELL"):
        if r["last_type"] == "BUY":
            note = f"{sec} · Phá đỉnh {UP} phiên ({vnd(r['entry'])}). Dời stop về đáy {DN}: {vnd(r['exit'])}."
        else:
            note = f"{sec} · Thủng đáy {DN} phiên ({vnd(r['exit'])}) — thoát vị thế (T+2.5)."
        return {"sym": sym, "action": r["last_type"], "price": round(r["close"]),
                "date": r["date"], "note": note, "held": False}
    # dang nam giu -> HOLD
    if r["pos"] == 1:
        ret = None
        if r["entry_price"]:
            ret = round((r["close"] / r["entry_price"] - 1) * 100, 1)
        note = f"{sec} · Vào {r['entry_date']} @ {vnd(r['entry_price'])}; stop dời theo đáy {DN}: {vnd(r['exit'])}."
        return {"sym": sym, "action": "HOLD", "price": round(r["close"]),
                "date": r["entry_date"], "ret": ret, "held": True, "note": note}
    # pos==0, khong co tin hieu hom nay -> dang cho breakout (khong hien the)
    return None


def main():
    setup_vnstock_key()
    log("phan tich", len(BASKET), "ma DC55/30...")
    res = {}
    for s in BASKET:
        for attempt in range(3):
            try:
                res[s] = analyze(fetch(s))
                log(f"{s}: pos={res[s]['pos']} close={res[s]['close']:.0f} "
                    f"signal_today={res[s]['signal_today']} ({res[s]['last_type']})")
                break
            except Exception as e:
                log(f"{s}: loi ({attempt+1}/3): {str(e)[:60]}")
                time.sleep(2)
        time.sleep(0.2)

    if not res:
        log("Khong lay duoc du lieu. Thoat.")
        return

    signals = []
    for s in BASKET:
        r = res.get(s)
        if not r:
            continue
        sig = build_signal(s, r)
        if sig:
            signals.append(sig)

    # tin hieu moi (BUY/SELL) len truoc, HOLD sau; trong moi nhom giu thu tu basket
    signals.sort(key=lambda x: (x["held"], BASKET.index(x["sym"])))

    n_buy = sum(1 for x in signals if x["action"] == "BUY")
    n_sell = sum(1 for x in signals if x["action"] == "SELL")
    n_hold = sum(1 for x in signals if x["held"])
    waiting = [s for s in BASKET if res.get(s) and res[s]["pos"] == 0 and not res[s]["signal_today"]]

    data = {
        "updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
        "strategy": "DC55/30 · 16 mã HOSE",
        "note": (f"Khung ngày, cuối phiên: MUA khi phá đỉnh {UP} phiên, BÁN khi thủng đáy {DN} phiên. "
                 f"Hôm nay: {n_buy} MUA · {n_sell} BÁN · đang nắm {n_hold} · chờ breakout {len(waiting)}."),
        "signals": signals,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    log("da ghi", OUT, f"({len(signals)} the, {os.path.getsize(OUT)} bytes)")

    if "--push" in sys.argv:
        git_push()


def git_push():
    import subprocess
    msg = "data: cap nhat khuyen nghi DC55/30 " + dt.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M")
    try:
        subprocess.run(["git", "-C", ROOT, "add", "docs/data/signals.json"], check=True)
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
