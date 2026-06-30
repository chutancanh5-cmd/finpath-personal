# -*- coding: utf-8 -*-
"""notify.py -- gui Discord + dedup state dung chung cho cac scanner."""
import os
import json
import glob
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "FinPath-VN-Bot/1.0 (+https://tradingview.com)"
ALERT_CFG = os.path.join(HERE, "alert_config.json")


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
    home = os.path.expanduser("~")
    for pat in (os.path.join(home, "OneDrive", "*", "Claude", "Projects", "TradingView", "bot", "bot_config.json"),
                os.path.join(home, "*", "Claude", "Projects", "TradingView", "bot", "bot_config.json")):
        for f in glob.glob(pat):
            try:
                url = (json.load(open(f, encoding="utf-8")).get("discord_webhook_url") or "").strip()
                if url.startswith("http"):
                    return url
            except Exception:
                pass
    return ""


def send_discord(webhook, content, embeds, username="FinPath · Quét"):
    payload = {"username": username, "content": content[:1900], "embeds": embeds[:10]}
    req = urllib.request.Request(
        webhook, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": UA})
    urllib.request.urlopen(req, timeout=20)


def load_sent(path):
    try:
        return set(json.load(open(path, encoding="utf-8")).get("sent", []))
    except Exception:
        return set()


def save_sent(path, sent):
    json.dump({"sent": list(sent)[-1000:]}, open(path, "w", encoding="utf-8"), ensure_ascii=False)
