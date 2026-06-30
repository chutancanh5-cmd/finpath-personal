# -*- coding: utf-8 -*-
"""
check_alerts.py -- Canh bao gia SERVER-SIDE (chay ca khi dong app).

Doc updater/price_alerts.json (nguong do ban tu dat) + docs/data/prices.json
(gia moi nhat) -> ban Discord khi cham nguong. Dedup qua check_alerts_state.json
(moi nguong bao 1 lan/ngay).

price_alerts.json:
  {"alerts": [
     {"sym": "FPT", "dir": "above", "price": 75000},
     {"sym": "HPG", "dir": "below", "price": 22000}
  ]}

Usage: python check_alerts.py
"""
import os
import sys
import io
import json
import datetime as dt
from datetime import timezone, timedelta

os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ALERTS_FILE = os.path.join(HERE, "price_alerts.json")
PRICES = os.path.join(ROOT, "docs", "data", "prices.json")
STATE = os.path.join(HERE, "check_alerts_state.json")
VN_TZ = timezone(timedelta(hours=7))


def log(*a):
    print("[check_alerts]", *a, flush=True)


def vnd(x):
    return f"{x:,.0f}".replace(",", ".")


def main():
    try:
        alerts = json.load(open(ALERTS_FILE, encoding="utf-8")).get("alerts", [])
    except Exception:
        log("Khong co price_alerts.json -> bo qua.")
        return
    if not alerts:
        return
    try:
        rows = json.load(open(PRICES, encoding="utf-8")).get("rows", [])
    except Exception:
        log("Chua co prices.json.")
        return
    price = {r["sym"]: r.get("price") for r in rows}

    import notify
    today = dt.datetime.now(VN_TZ).strftime("%Y-%m-%d")
    sent = notify.load_sent(STATE)
    embeds, newkeys = [], []
    for a in alerts:
        sym, d, lvl = a.get("sym", "").upper(), a.get("dir", "above"), a.get("price")
        p = price.get(sym)
        if p is None or lvl is None:
            continue
        hit = (d == "above" and p >= lvl) or (d == "below" and p <= lvl)
        key = f"{today}|{sym}|{d}|{lvl}"
        if hit and key not in sent and key not in newkeys:
            newkeys.append(key)
            embeds.append({
                "title": f"🔔 {sym} {'≥' if d == 'above' else '≤'} {vnd(lvl)}",
                "color": 0x2ecc71 if d == "above" else 0xe74c3c,
                "description": f"Giá hiện tại: **{vnd(p)}** (ngưỡng {vnd(lvl)})",
                "footer": {"text": f"Cảnh báo giá • {today}"}})
    if not embeds:
        log(f"Khong co nguong cham ({len(alerts)} nguong).")
        return
    webhook = notify.resolve_webhook()
    if not webhook:
        log("[DRY-RUN]", len(embeds), "canh bao:")
        for e in embeds:
            print("  ", e["title"])
    else:
        try:
            notify.send_discord(webhook, f"🔔 **{len(embeds)} cảnh báo giá** — {today}", embeds, username="FinPath · Cảnh báo")
            log(f"Da gui {len(embeds)} canh bao.")
        except Exception as e:
            log("Loi gui:", str(e)[:120]); return
    for k in newkeys:
        sent.add(k)
    notify.save_sent(STATE, sent)


if __name__ == "__main__":
    main()
