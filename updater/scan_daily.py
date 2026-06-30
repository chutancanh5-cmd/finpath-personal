# -*- coding: utf-8 -*-
"""
scan_daily.py -- Quet cuoi phien toan san: 3 loai tin hieu tu OHLCV ngay.
  breakout : vuot dinh 60 phien KEM khoi luong lon (>=2x TB20), dong gan dinh ngay
  support  : giam manh (>=4%/phien hoac >=7%/3 phien) ve sat MA50 / day 60 phien
  base     : tich luy chat nen (bien do 15 phien <=10%) + khoi luong co lai

Ghi docs/data/scan_daily.json (toan bo hit). --discord: ban hit MOI len Discord
(dedup theo ngay). --push: git commit & push.

Usage:
    python scan_daily.py [--discord] [--push] [--max N] [--symbols FPT,HPG,...]
"""
import os
import sys
import io
import json
import time
import statistics as st
import datetime as dt
from datetime import timezone, timedelta

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "data", "scan_daily.json")
STATE = os.path.join(HERE, "scan_daily_state.json")
VN_TZ = timezone(timedelta(hours=7))

LABEL = {"breakout": "🚀 Vượt đỉnh + KL lớn",
         "support": "🛟 Giảm mạnh về hỗ trợ",
         "base": "🧱 Tích lũy chặt nền"}


def log(*a):
    print("[scan_daily]", *a, flush=True)


def vnd(x):
    return f"{x:,.0f}".replace(",", ".")


def fetch_daily(sym):
    from vnstock.api.quote import Quote
    start = (dt.date.today() - dt.timedelta(days=260)).isoformat()
    df = Quote(symbol=sym, source="VCI").history(
        start=start, end=dt.date.today().isoformat(), interval="1D")
    if df is None or len(df) < 60:
        return None
    df = df.rename(columns=str.lower)
    return df


def analyze(df):
    o = [x * 1000 for x in df["open"]]
    h = [x * 1000 for x in df["high"]]
    l = [x * 1000 for x in df["low"]]
    c = [x * 1000 for x in df["close"]]
    v = [float(x) for x in df["volume"]]
    n = len(c)
    close, prev = c[-1], c[-2]
    ret1 = (close / prev - 1) * 100 if prev else 0
    ret3 = (close / c[-4] - 1) * 100 if n >= 4 and c[-4] else ret1
    ma50 = st.mean(c[-50:]) if n >= 50 else st.mean(c)
    hits = []

    # 1) breakout + volume
    hh60 = max(h[-61:-1])
    vol20 = st.mean(v[-21:-1]) if n >= 21 else st.mean(v[:-1] or v)
    volmult = v[-1] / vol20 if vol20 else 0
    near_high = (close - l[-1]) / (h[-1] - l[-1]) if h[-1] > l[-1] else 1.0
    if close > hh60 and volmult >= 2.0 and near_high >= 0.6 and ret1 > 0:
        hits.append(("breakout", f"Vượt đỉnh 60 phiên, KL {volmult:.1f}× TB20, +{ret1:.1f}%"))

    # 2) drop to support
    low60 = min(l[-60:])
    near_ma50 = ma50 and 0 <= (close - ma50) / ma50 <= 0.03
    near_low = low60 and 0 <= (close - low60) / low60 <= 0.03
    if (ret1 <= -4 or ret3 <= -7) and (near_ma50 or near_low):
        sup = "MA50" if near_ma50 else "đáy 60 phiên"
        hits.append(("support", f"Giảm {ret1:.1f}% (3 phiên {ret3:.1f}%), về sát {sup} {vnd(ma50 if near_ma50 else low60)}"))

    # 3) tight base
    win = 15
    rng = (max(h[-win:]) - min(l[-win:])) / close if close else 1
    vol5 = st.mean(v[-5:])
    vol20b = st.mean(v[-20:]) if n >= 20 else st.mean(v)
    if rng <= 0.07 and vol20b and (vol5 / vol20b) <= 0.80 and ma50 and close >= ma50 * 0.95:
        hits.append(("base", f"Biên độ 15 phiên {rng*100:.1f}%, KL co lại còn {vol5/vol20b*100:.0f}% TB20"))

    return hits, round(close), round(ret1, 2)


def get_symbols():
    if "--symbols" in sys.argv:
        raw = sys.argv[sys.argv.index("--symbols") + 1]
        return [s.strip().upper() for s in raw.split(",") if s.strip()]
    import universe
    max_n = 500
    if "--max" in sys.argv:
        max_n = int(sys.argv[sys.argv.index("--max") + 1])
    return universe.liquid_universe(max_n=max_n, log=log)


def push_discord(fresh):
    import notify
    webhook = notify.resolve_webhook()
    today = dt.datetime.now(VN_TZ).strftime("%Y-%m-%d")
    sent = notify.load_sent(STATE)
    new = [hh for hh in fresh if f"{today}|{hh['sym']}|{hh['type']}" not in sent]
    if not new:
        log("Discord: khong co hit moi.")
        return
    embeds = []
    for typ in ("breakout", "support", "base"):
        grp = [hh for hh in new if hh["type"] == typ]
        if not grp:
            continue
        lines = [f"**{hh['sym']}** {vnd(hh['price'])} ({hh['pct']:+.1f}%) — {hh['detail']}" for hh in grp[:25]]
        embeds.append({"title": f"{LABEL[typ]} ({len(grp)})",
                       "color": 0x2ecc71 if typ == "breakout" else 0xe67e22 if typ == "support" else 0x3498db,
                       "description": "\n".join(lines)[:4000]})
    if not webhook:
        log("[DRY-RUN] khong co webhook. Se gui", len(new), "hit moi:")
        for e in embeds:
            print("  ", e["title"])
    else:
        try:
            notify.send_discord(webhook, f"🔎 **Quét cuối phiên — {today}**: {len(new)} tín hiệu mới", embeds)
            log(f"Da gui {len(new)} hit len Discord.")
        except Exception as e:
            log("Loi gui Discord:", str(e)[:120]); return
    for hh in new:
        sent.add(f"{today}|{hh['sym']}|{hh['type']}")
    notify.save_sent(STATE, sent)


def main():
    syms = get_symbols()
    log(f"quet {len(syms)} ma...")
    hits = []
    for i, sym in enumerate(syms):
        try:
            df = fetch_daily(sym)
            if df is None:
                continue
            res, price, pct = analyze(df)
            for typ, detail in res:
                hits.append({"sym": sym, "type": typ, "price": price, "pct": pct, "detail": detail})
        except Exception as e:
            log(f"{sym} loi:", str(e)[:60])
        time.sleep(0.12)
        if (i + 1) % 50 == 0:
            log(f"  ...{i+1}/{len(syms)} ma")

    by = {t: sum(1 for hh in hits if hh["type"] == t) for t in LABEL}
    data = {
        "updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
        "universe_n": len(syms),
        "counts": by,
        "hits": hits,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log(f"da ghi {OUT}: {len(hits)} hit (breakout {by['breakout']} · support {by['support']} · base {by['base']})")

    if "--discord" in sys.argv:
        push_discord(hits)
    if "--push" in sys.argv:
        git_push()


def git_push():
    import subprocess
    msg = "data: scan_daily " + dt.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M")
    try:
        subprocess.run(["git", "-C", ROOT, "add", "docs/data/scan_daily.json"], check=True)
        if subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"]).returncode != 0:
            subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)
            subprocess.run(["git", "-C", ROOT, "push"], check=True)
            log("da push")
    except Exception as e:
        log("git push err:", e)


if __name__ == "__main__":
    main()
