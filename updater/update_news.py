# -*- coding: utf-8 -*-
"""
update_news.py -- Tin AI + diem regime -> docs/data/news.json

TAI DUNG macro regime bot (macro/macro_bot.py): import truc tiep cac module
'macro_bot', 'sources', 'analysis' va goi lai gather() + regime_score() +
ai_digest() (Haiku). Khong chep lai logic, khong tao them secret -- dung
chung macro/config.json (FRED key + Anthropic key).

Python doc filesystem THAT nen khong vuong Unicode-twin cua "Tai lieu";
thu muc macro duoc do bang glob wildcard de ne luon van de encoding.

Usage:
    python update_news.py            # ghi news.json
    python update_news.py --push     # + git commit & push
"""
import os
import sys
import io
import re
import json
import glob
import datetime as dt
from datetime import timezone, timedelta

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "data", "news.json")
VN_TZ = timezone(timedelta(hours=7))


def log(*a):
    print("[update_news]", *a, flush=True)


def find_macro_dir():
    """Do thu muc macro/ cua project TradingView (ne Unicode-twin bang wildcard)."""
    home = os.path.expanduser("~")
    pats = [
        os.path.join(home, "OneDrive", "*", "Claude", "Projects", "TradingView", "macro", "macro_bot.py"),
        os.path.join(home, "*", "Claude", "Projects", "TradingView", "macro", "macro_bot.py"),
        os.path.join(home, "OneDrive", "**", "TradingView", "macro", "macro_bot.py"),
    ]
    for p in pats:
        hits = glob.glob(p, recursive=("**" in p))
        if hits:
            return os.path.dirname(hits[0])
    return None


def vn_today():
    return dt.datetime.now(VN_TZ).strftime("%Y-%m-%d")


def best_link(title, raw):
    """Khop tin AI voi tin RSS goc (token overlap) de lay source + url that."""
    tw = set(re.findall(r"\w+", title.lower()))
    best, score = None, 0
    for it in raw:
        ov = len(tw & set(re.findall(r"\w+", it["title"].lower())))
        if ov > score:
            best, score = it, ov
    return best if score >= 3 else None


def build(reg, dig, items, cyc):
    today = vn_today()
    # ----- regime -----
    pos = [name for name, d, _ in reg["rows"] if d > 0]
    neg = [name for name, d, _ in reg["rows"] if d < 0]
    note = ""
    if pos:
        note += "Hỗ trợ: " + ", ".join(pos[:4]) + ". "
    if neg:
        note += "Cản trở: " + ", ".join(neg[:4]) + "."
    if not note and cyc and cyc.get("phase"):
        note = "Chu kỳ: " + cyc["phase"] + "."
    regime = {"score": reg["score"], "label": reg["label"], "note": note.strip()}

    # ----- summary -----
    if dig and dig.get("summary_vi"):
        summary = dig["summary_vi"]
    else:
        summary = reg.get("narrative", "").replace("**", "")

    # ----- items -----
    out = []
    if dig and dig.get("top"):
        for t in dig["top"][:8]:
            imp = t.get("impact", "→")
            sent = "+" if imp == "↑" else "-" if imp == "↓" else ""
            m = best_link(t.get("title", ""), items)
            out.append({
                "title": t.get("title", ""),
                "sentiment": sent,
                "note": t.get("note", ""),
                "source": (m["source"] if m else "Tổng hợp AI"),
                "url": (m["link"] if m else ""),
                "date": today,
            })
    else:
        for it in items[:10]:
            out.append({"title": it["title"], "sentiment": "", "note": "",
                        "source": it["source"], "url": it["link"], "date": today})

    return {
        "updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
        "regime": regime,
        "summary": summary,
        "items": out,
    }


def main():
    macro_dir = find_macro_dir()
    if not macro_dir:
        log("Khong tim thay thu muc macro/. Bo qua (giu news.json cu).")
        return
    log("macro dir:", macro_dir)
    sys.path.insert(0, macro_dir)
    import macro_bot as MB
    import analysis as A

    cfg = MB.load_config()
    log("FRED key:", "co" if cfg.get("fred_api_key") else "khong",
        "| Anthropic key:", "co" if cfg.get("anthropic_api_key") else "khong",
        "| model:", cfg.get("model"))

    sig, items, _ = MB.gather(cfg)
    log("RSS:", len(items), "tin |",
        "VNINDEX:", (sig.get("vnindex") or {}).get("last"),
        "| world:", len(sig.get("world") or []))

    dig = A.ai_digest(items, cfg)
    if dig:
        sig["news_sent"] = dig.get("overall_sentiment")
        log("AI digest:", dig.get("overall_sentiment"), "|", len(dig.get("top", [])), "tin nổi bật")
    else:
        log("Khong co AI digest (thieu key/anthropic hoac khong co tin).")

    reg = A.regime_score(sig)
    log("regime:", reg["score"], reg["label"], f"({reg['n']} tín hiệu)")

    data = build(reg, dig, items, sig.get("cycle"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    log("da ghi", OUT, f"({len(data['items'])} tin, {os.path.getsize(OUT)} bytes)")

    if "--push" in sys.argv:
        git_push()


def git_push():
    import subprocess
    msg = "data: cap nhat tin AI " + dt.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M")
    try:
        subprocess.run(["git", "-C", ROOT, "add", "docs/data/news.json"], check=True)
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
