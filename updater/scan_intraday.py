# -*- coding: utf-8 -*-
"""
scan_intraday.py -- Quet TRONG PHIEN (chay lap moi ~5 phut). 2 loai tin hieu
tu snapshot price_board theo lo (khong can tick tung ma):
  spike : gia nhay >= 1.5% trong ~5 phut (so voi snapshot lan truoc) + KL bung
  shark : "ca map" -- net gia tri ngoai lon (>=5 ty) HOAC lenh khop TB lon
          (gia tri/lenh >= 100tr) => co dau hieu to chuc gom/xa. (PROXY, khong phai tick)

Ghi docs/data/scan_intraday.json. Luu snapshot truoc -> scan_intraday_prev.json.
Ngoai gio giao dich: bao "thi truong dong", khong tao tin hieu.

Usage:
    python scan_intraday.py [--discord] [--push] [--symbols FPT,HPG,...]
"""
import os
import sys
import io
import json
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
OUT = os.path.join(ROOT, "docs", "data", "scan_intraday.json")
PREV = os.path.join(HERE, "scan_intraday_prev.json")
STATE = os.path.join(HERE, "scan_intraday_state.json")
VN_TZ = timezone(timedelta(hours=7))

SPIKE_PCT = 1.5          # |%| nhay trong khoang giua 2 lan chay
SPIKE_MIN_VOL = 50000    # CP khop trong khoang -> du thanh khoan
SHARK_FOREIGN_VND = 10e9  # net ngoai >= 10 ty (giam nhieu)
SHARK_ORDER_VND = 100e6  # gia tri TB/lenh >= 100 tr -> lenh lon

LABEL = {"spike": "⚡ Giá đột biến 5 phút", "shark": "🦈 Cá mập lệnh lớn"}


def log(*a):
    print("[scan_intraday]", *a, flush=True)


def vnd(x):
    return f"{x:,.0f}".replace(",", ".")


def now_vn():
    return dt.datetime.now(VN_TZ)


def market_open():
    n = now_vn()
    if n.weekday() >= 5:
        return False
    t = n.hour * 60 + n.minute
    return (9 * 60 <= t <= 11 * 60 + 30) or (13 * 60 <= t <= 15 * 60)


def get_symbols():
    if "--symbols" in sys.argv:
        raw = sys.argv[sys.argv.index("--symbols") + 1]
        return [s.strip().upper() for s in raw.split(",") if s.strip()]
    import universe
    return universe.liquid_universe(log=log)


def load_prev():
    try:
        return json.load(open(PREV, encoding="utf-8"))
    except Exception:
        return {}


def detect(snap, prev):
    today = now_vn().strftime("%Y-%m-%d")
    prev_same_day = prev.get("date") == today
    prows = prev.get("rows", {}) if prev_same_day else {}
    hits = []
    for sym, d in snap.items():
        price = d.get("price")
        if not price:
            continue
        # ----- spike (can snapshot truoc cung ngay) -----
        p = prows.get(sym)
        if p and p.get("price"):
            move = (price / p["price"] - 1) * 100
            vol_delta = (d.get("acc_vol") or 0) - (p.get("acc_vol") or 0)
            if abs(move) >= SPIKE_PCT and vol_delta >= SPIKE_MIN_VOL:
                hits.append({"sym": sym, "type": "spike", "price": round(price),
                             "pct": round(move, 2), "dir": "up" if move > 0 else "down",
                             "detail": f"{'Tăng' if move>0 else 'Giảm'} {move:+.1f}% ~5 phút, KL {vnd(vol_delta)} CP"})
        # ----- shark (tu snapshot hien tai) -----
        net_f = (d.get("fbval") or 0) - (d.get("fsval") or 0)
        orders = (d.get("buy_ord") or 0) + (d.get("sell_ord") or 0)
        val_per_order = (d.get("acc_val") or 0) / orders if orders else 0
        if abs(net_f) >= SHARK_FOREIGN_VND:
            hits.append({"sym": sym, "type": "shark", "price": round(price),
                         "pct": round((price / d["ref"] - 1) * 100, 2) if d.get("ref") else 0,
                         "dir": "buy" if net_f > 0 else "sell",
                         "detail": f"Khối ngoại {'mua' if net_f>0 else 'bán'} ròng {vnd(abs(net_f)/1e9)} tỷ"})
        elif val_per_order >= SHARK_ORDER_VND and (d.get("acc_val") or 0) >= 20e9:
            hits.append({"sym": sym, "type": "shark", "price": round(price),
                         "pct": round((price / d["ref"] - 1) * 100, 2) if d.get("ref") else 0,
                         "dir": "buy",
                         "detail": f"Lệnh khớp TB {vnd(val_per_order/1e6)} tr/lệnh (lớn) · GT {vnd((d['acc_val'])/1e9)} tỷ"})
    return hits


def push_discord(hits):
    import notify
    webhook = notify.resolve_webhook()
    today = now_vn().strftime("%Y-%m-%d")
    sent = notify.load_sent(STATE)
    new = [h for h in hits if f"{today}|{h['sym']}|{h['type']}" not in sent]
    if not new:
        log("Discord: khong co tin hieu moi.")
        return
    embeds = []
    for typ in ("spike", "shark"):
        grp = [h for h in new if h["type"] == typ]
        if not grp:
            continue
        lines = [f"**{h['sym']}** {vnd(h['price'])} — {h['detail']}" for h in grp[:25]]
        embeds.append({"title": f"{LABEL[typ]} ({len(grp)})", "color": 0xf1c40f if typ == "spike" else 0x9b59b6,
                       "description": "\n".join(lines)[:4000]})
    if not webhook:
        log("[DRY-RUN] khong co webhook.", len(new), "tin hieu moi:")
        for e in embeds:
            print("  ", e["title"])
    else:
        try:
            notify.send_discord(webhook, f"⚡ **Quét trong phiên — {now_vn():%H:%M}**: {len(new)} tín hiệu", embeds)
            log(f"Da gui {len(new)} tin hieu.")
        except Exception as e:
            log("Loi gui:", str(e)[:120]); return
    for h in new:
        sent.add(f"{today}|{h['sym']}|{h['type']}")
    notify.save_sent(STATE, sent)


def main():
    opened = market_open()
    if not opened and "--force" not in sys.argv:
        log("Thi truong dong -> bo qua quet (dung --force de ep chay).")
        data = {"updated_at": now_vn().isoformat(timespec="seconds"), "market_open": False,
                "universe_n": 0, "hits": []}
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        return

    syms = get_symbols()
    import universe
    log(f"snapshot {len(syms)} ma...")
    snap = universe.price_board_snapshot(syms)
    prev = load_prev()
    hits = detect(snap, prev)
    # luu snapshot lam moc cho lan sau
    rows = {s: {"price": d.get("price"), "acc_vol": d.get("acc_vol")} for s, d in snap.items()}
    json.dump({"date": now_vn().strftime("%Y-%m-%d"), "ts": now_vn().isoformat(timespec="seconds"), "rows": rows},
              open(PREV, "w", encoding="utf-8"), ensure_ascii=False)
    log(f"{len(hits)} tin hieu (spike {sum(1 for h in hits if h['type']=='spike')} · "
        f"shark {sum(1 for h in hits if h['type']=='shark')})")

    data = {"updated_at": now_vn().isoformat(timespec="seconds"), "market_open": opened,
            "universe_n": len(syms), "hits": hits}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log("da ghi", OUT)

    if "--discord" in sys.argv and hits:
        push_discord(hits)
    if "--push" in sys.argv:
        git_push()


def git_push():
    import subprocess
    msg = "data: scan_intraday " + now_vn().strftime("%Y-%m-%d %H:%M")
    try:
        subprocess.run(["git", "-C", ROOT, "add", "docs/data/scan_intraday.json"], check=True)
        if subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"]).returncode != 0:
            subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)
            subprocess.run(["git", "-C", ROOT, "push"], check=True)
            log("da push")
    except Exception as e:
        log("git push err:", e)


if __name__ == "__main__":
    main()
