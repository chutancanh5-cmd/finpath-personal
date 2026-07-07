# -*- coding: utf-8 -*-
"""
update_signals.py -- Sinh khuyen nghi PrimeTrade -> docs/data/signals.json

DUNG CHUNG voi bot PrimeTrade (UT Bot v2 VN long-only). Ma nay la ban goc FinPath
tai hien indicator cong khai "UT Bot v2 — ATR Trailing Stop" (QuantNomad):
  - source = hl2 (trung diem nen), ATR (RMA) rieng tung ma
  - MUA  : hl2 cat LEN duong trailing-stop (crossover)
  - BAN  : hl2 cat XUONG duong trailing-stop (crossunder) -> thoat (T+2.5)
Ro 60 ma / 18 nganh + setting mult/ATR rieng tung ma doc tu updater/utbot_config.json
(chon bang backtest robust — dong bo voi bot/utbot_discord_bot.py trong repo vn-bots).
Bo sung entry_price/entry_date de tinh lai/lo vi the dang nam (HOLD).

Usage:
    python update_signals.py            # ghi signals.json
    python update_signals.py --push     # + git commit & push (GitHub Pages)
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

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "data", "signals.json")
CONFIG = os.path.join(HERE, "utbot_config.json")
VN_TZ = timezone(timedelta(hours=7))
MIN_HOLD = 3   # T+2.5


def log(*a):
    print("[update_signals]", *a, flush=True)


def vnd(x):
    if x is None:
        return "—"
    return f"{x:,.0f}".replace(",", ".")


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


def load_config():
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    return cfg["symbols"]


def fetch(sym):
    """OHLC ngay, gia *1000 ve VND; loc bo nen rac (gia <= 0)."""
    from vnstock.api.quote import Quote
    start = (dt.date.today() - dt.timedelta(days=1200)).isoformat()
    df = Quote(symbol=sym, source="VCI").history(
        start=start, end=dt.date.today().isoformat(), interval="1D")
    df = df.rename(columns=str.lower)
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df[(df.open > 0) & (df.high > 0) & (df.low > 0) & (df.close > 0)].reset_index(drop=True)
    if len(df) and df["close"].median() < 1000:
        for c in ("open", "high", "low", "close"):
            df[c] = df[c] * 1000.0
    df["date"] = df["time"].dt.date
    return df[["date", "open", "high", "low", "close"]].reset_index(drop=True)


def pine_rma(vals, length):
    """RMA (Wilder) khop ta.atr cua Pine: seed = SMA(length)."""
    out = np.full(len(vals), np.nan)
    roll = pd.Series(vals).rolling(length).mean().to_numpy()
    alpha = 1.0 / length
    for i in range(len(vals)):
        prev = out[i - 1] if i > 0 else np.nan
        out[i] = roll[i] if np.isnan(prev) else alpha * vals[i] + (1 - alpha) * prev
    return out


def analyze(df, mult, atr_len):
    """UT Bot v2 long-only tren hl2 — tra ve trang thai + gia vao lenh vi the dang nam."""
    h, l, c = df.high.to_numpy(), df.low.to_numpy(), df.close.to_numpy()
    dates = df.date.to_numpy()
    src = (h + l) / 2.0                              # hl2
    prev_c = np.concatenate([[np.nan], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    tr[0] = h[0] - l[0]
    atr = pine_rma(tr, atr_len)
    n = len(src)
    tsl = np.full(n, np.nan)
    nl = mult * atr
    for i in range(n):
        prev = tsl[i - 1] if i > 0 else np.nan
        pnz = 0.0 if np.isnan(prev) else prev
        if np.isnan(nl[i]):
            continue
        if src[i] > pnz and (i > 0 and src[i - 1] > pnz):
            tsl[i] = max(pnz, src[i] - nl[i])
        elif src[i] < pnz and (i > 0 and src[i - 1] < pnz):
            tsl[i] = min(pnz, src[i] + nl[i])
        elif src[i] > pnz:
            tsl[i] = src[i] - nl[i]
        else:
            tsl[i] = src[i] + nl[i]
    ps, px = np.concatenate([[np.nan], tsl[:-1]]), np.concatenate([[np.nan], src[:-1]])
    with np.errstate(invalid="ignore"):
        buy = (src > tsl) & (px <= ps) & ~np.isnan(tsl) & ~np.isnan(ps)
        sell = (src < tsl) & (px >= ps) & ~np.isnan(tsl) & ~np.isnan(ps)

    pos, last_i, last_type = 0, -1, None
    entry_price, entry_date = None, None
    for i in range(n):
        if pos == 0 and buy[i]:
            pos, last_i, last_type = 1, i, "BUY"
            entry_price, entry_date = float(c[i]), str(dates[i])[:10]
        elif pos == 1 and sell[i]:
            pos, last_i, last_type = 0, i, "SELL"
    return dict(pos=pos, close=float(c[-1]), stop=float(tsl[-1]) if not np.isnan(tsl[-1]) else None,
                date=str(dates[-1])[:10], signal_today=(last_i == n - 1),
                last_type=last_type, entry_price=entry_price, entry_date=entry_date)


def build_signal(sym, meta, r):
    """Map ket qua analyze -> 1 the khuyen nghi (hoac None neu dang cho)."""
    sec = meta.get("sector", "")
    stop = vnd(r["stop"])
    if r["signal_today"] and r["last_type"] in ("BUY", "SELL"):
        if r["last_type"] == "BUY":
            note = f"{sec} · Giá cắt lên trailing-stop → MUA. Dời stop theo: {stop}."
        else:
            note = f"{sec} · Giá thủng trailing-stop ({stop}) → THOÁT vị thế (tôn trọng T+2.5)."
        return {"sym": sym, "action": r["last_type"], "price": round(r["close"]),
                "date": r["date"], "note": note, "held": False}
    if r["pos"] == 1:
        ret = None
        if r["entry_price"]:
            ret = round((r["close"] / r["entry_price"] - 1) * 100, 1)
        note = f"{sec} · Vào {r['entry_date']} @ {vnd(r['entry_price'])}; stop dời theo: {stop}."
        return {"sym": sym, "action": "HOLD", "price": round(r["close"]),
                "date": r["entry_date"], "ret": ret, "held": True, "note": note}
    return None  # pos==0, khong tin hieu -> dang cho breakout (khong hien)


def main():
    setup_vnstock_key()
    symbols = load_config()
    syms = list(symbols.keys())
    paced = 1.1 if os.getenv("VNSTOCK_API_KEY") else 3.2
    log(f"phan tich {len(syms)} ma PrimeTrade (UT Bot v2)... pace {paced}s")
    res = {}
    for s in syms:
        m = symbols[s]
        for attempt in range(3):
            try:
                r = analyze(fetch(s), float(m["mult"]), int(m["atr"]))
                res[s] = r
                log(f"{s}: pos={r['pos']} close={r['close']:.0f} today={r['signal_today']} ({r['last_type']})")
                break
            except Exception as e:
                log(f"{s}: loi ({attempt+1}/3): {str(e)[:60]}")
                time.sleep(2)
        time.sleep(paced)

    # guard partial fetch: <70% ro -> giu file cu, khong ghi de
    if len(res) < 0.7 * len(syms):
        log(f"Chi lay duoc {len(res)}/{len(syms)} ma (<70%) — GIU file cu, thoat.")
        return

    signals = []
    for s in syms:
        r = res.get(s)
        if not r:
            continue
        sig = build_signal(s, symbols[s], r)
        if sig:
            signals.append(sig)

    order = {s: i for i, s in enumerate(syms)}
    signals.sort(key=lambda x: (x["held"], order.get(x["sym"], 999)))

    n_buy = sum(1 for x in signals if x["action"] == "BUY")
    n_sell = sum(1 for x in signals if x["action"] == "SELL")
    n_hold = sum(1 for x in signals if x["held"])
    waiting = sum(1 for s in syms if res.get(s) and res[s]["pos"] == 0 and not res[s]["signal_today"])
    n_sec = len({m.get("sector", "") for m in symbols.values()})

    data = {
        "updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
        "strategy": f"PrimeTrade · UT Bot v2 · {len(syms)} mã / {n_sec} ngành",
        "note": (f"Dùng chung với bot PrimeTrade. Khung ngày, cuối phiên: MUA khi giá cắt lên trailing-stop "
                 f"(ATR riêng từng mã), BÁN khi thủng stop. Hôm nay: {n_buy} MUA · {n_sell} BÁN · "
                 f"đang nắm {n_hold} · chờ tín hiệu {waiting}."),
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
    msg = "data: cap nhat khuyen nghi PrimeTrade " + dt.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M")
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
