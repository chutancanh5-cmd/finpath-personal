# -*- coding: utf-8 -*-
"""
alert.py -- Doc docs/data/signals.json, ban tin hieu MUA/BAN MOI len Discord.

Chay SAU update_signals.py. Chi bao tin hieu moi trong ngay (held=false,
action BUY/SELL); dedup qua updater/alert_state.json de chay lai khong spam.

Webhook (uu tien tu tren xuong):
  1. bien moi truong DISCORD_WEBHOOK_URL
  2. updater/alert_config.json  {"discord_webhook_url": "..."}
  3. bot/bot_config.json cua discord_signal_bot.py (dung chung kenh)
Khong co webhook -> DRY-RUN (in ra man hinh).

Usage:
    python alert.py            # ban tin hieu moi (neu co)
    python alert.py --test     # chen 1 tin hieu mau de kiem tra dinh dang
"""
import os
import sys
import io
import json
import glob
import datetime as dt
from datetime import timezone, timedelta
import urllib.request

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SIGNALS = os.path.join(ROOT, "docs", "data", "signals.json")
STATE = os.path.join(HERE, "alert_state.json")
ALERT_CFG = os.path.join(HERE, "alert_config.json")
VN_TZ = timezone(timedelta(hours=7))
UA = "FinPath-VN-Bot/1.0 (+https://tradingview.com)"


def log(*a):
    print("[alert]", *a, flush=True)


def resolve_webhook():
    url = (os.environ.get("DISCORD_WEBHOOK_URL") or "").strip()
    if url.startswith("http"):
        return url
    if os.path.exists(ALERT_CFG):
        try:
            url = (json.load(open(ALERT_CFG, encoding="utf-8")).get("discord_webhook_url") or "").strip()
            if url.startswith("http"):
                return url
        except Exception:
            pass
    # dung chung webhook cua discord_signal_bot.py
    home = os.path.expanduser("~")
    for pat in (os.path.join(home, "OneDrive", "*", "Claude", "Projects", "TradingView", "bot", "bot_config.json"),
                os.path.join(home, "*", "Claude", "Projects", "TradingView", "bot", "bot_config.json")):
        for f in glob.glob(pat):
            try:
                url = (json.load(open(f, encoding="utf-8")).get("discord_webhook_url") or "").strip()
                if url.startswith("http"):
                    log("dung webhook tu", f)
                    return url
            except Exception:
                pass
    return ""


def load_signals():
    with open(SIGNALS, encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE, encoding="utf-8"))
        except Exception:
            pass
    return {"sent": []}


def save_state(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)


def send_discord(webhook, content, embeds):
    payload = {"username": "FinPath · DC55/30", "content": content[:1900], "embeds": embeds[:10]}
    req = urllib.request.Request(
        webhook, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": UA})
    urllib.request.urlopen(req, timeout=20)


def vnd(x):
    return f"{x:,.0f}".replace(",", ".")


def make_embed(s):
    buy = s["action"] == "BUY"
    return {
        "title": f"{'🟢 MUA' if buy else '🔴 BÁN'} — {s['sym']}",
        "color": 0x2ecc71 if buy else 0xe74c3c,
        "description": f"💵 Giá đóng cửa: **{vnd(s['price'])}**\n{s.get('note','')}",
        "footer": {"text": f"DC55/30 • {s.get('date','')} • công cụ hỗ trợ, không phải khuyến nghị chắc chắn"},
    }


def main():
    test = "--test" in sys.argv
    data = load_signals()
    sigs = [s for s in data.get("signals", []) if not s.get("held") and s.get("action") in ("BUY", "SELL")]
    if test:
        sigs.append({"sym": "TEST", "action": "BUY", "price": 12345,
                     "date": dt.datetime.now(VN_TZ).strftime("%Y-%m-%d"),
                     "note": "Công nghệ · Phá đỉnh 55 phiên (12.000). Dời stop về đáy 30: 11.000."})
        log("che do --test: chen 1 tin hieu mau")

    st = load_state()
    sent = set(st.get("sent", []))
    today = dt.datetime.now(VN_TZ).strftime("%Y-%m-%d")
    fresh = [s for s in sigs if f"{today}|{s['sym']}|{s['action']}" not in sent]

    if not fresh:
        log(f"Khong co tin hieu moi ({len(sigs)} tin hieu trong ngay, da gui het).")
        return

    embeds = [make_embed(s) for s in fresh]
    n_buy = sum(1 for s in fresh if s["action"] == "BUY")
    n_sell = sum(1 for s in fresh if s["action"] == "SELL")
    content = f"📨 **{len(fresh)} tín hiệu DC55/30 mới** — {today} ({n_buy} MUA · {n_sell} BÁN)"

    webhook = "" if test else resolve_webhook()  # --test luon dry-run, khong dung kenh that
    if not webhook:
        log("[DRY-RUN]" + (" (--test ep dry-run)" if test else " khong co webhook") + ". Se gui:")
        print(" ", content)
        for e in embeds:
            print("  EMBED:", e["title"], "|", e["description"].replace("\n", " "))
    else:
        try:
            send_discord(webhook, content, embeds)
            log(f"Da gui {len(embeds)} tin hieu len Discord.")
        except Exception as e:
            log("Loi gui Discord:", str(e)[:120])
            return

    # luu state (khong luu tin hieu --test)
    for s in fresh:
        if s["sym"] != "TEST":
            sent.add(f"{today}|{s['sym']}|{s['action']}")
    st["sent"] = list(sent)[-500:]
    save_state(st)
    log("Da cap nhat alert_state.json")


if __name__ == "__main__":
    main()
