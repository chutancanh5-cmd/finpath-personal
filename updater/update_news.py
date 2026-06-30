# -*- coding: utf-8 -*-
"""
update_news.py -- Tin AI + diem regime -> docs/data/news.json  (CODE GOC FinPath)

Tu lay du lieu cong khai, KHONG phu thuoc thu muc macro/:
  - RSS tieng Viet (CafeF, VnExpress) loc theo tu khoa vi mo
  - Regime score tu VNINDEX (vnstock) + FRED (CPI/Fed/10Y/USD/dau/VIX)
  - Tom tat + sentiment bang Haiku (neu co ANTHROPIC_API_KEY con credit)
Key doc tu bien moi truong: FRED_API_KEY, ANTHROPIC_API_KEY (GitHub Secrets).

Usage: python update_news.py [--push]
"""
import os
import sys
import io
import re
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import datetime as dt
from datetime import timezone, timedelta

os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "data", "news.json")
VN_TZ = timezone(timedelta(hours=7))
UA = "FinPath-VN-Bot/1.0 (+https://tradingview.com)"
FRED = "https://api.stlouisfed.org/fred/series/observations"

FEEDS = [("CafeF Vĩ mô", "https://cafef.vn/vi-mo-dau-tu.rss"),
         ("CafeF Chứng khoán", "https://cafef.vn/thi-truong-chung-khoan.rss"),
         ("VnExpress Kinh doanh", "https://vnexpress.net/rss/kinh-doanh.rss")]
KEYWORDS = ["lạm phát", "lãi suất", "tỷ giá", "cpi", "fed", "fomc", "ngân hàng nhà nước", "nhnn",
            "tăng trưởng", "gdp", "xuất khẩu", "nhập khẩu", "fdi", "trái phiếu", "vn-index", "vnindex",
            "tín dụng", "vàng", "giá dầu", "usd", "chính sách tiền tệ", "chứng khoán", "khối ngoại"]


def log(*a):
    print("[update_news]", *a, flush=True)


def _http(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def today():
    return dt.datetime.now(VN_TZ).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- RSS
def fetch_rss(limit=14):
    kws = [k.lower() for k in KEYWORDS]
    seen, out = set(), []
    for source, url in FEEDS:
        try:
            root = ET.fromstring(_http(url, 20))
        except Exception as e:
            log(f"RSS {source} loi:", str(e)[:50])
            continue
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            if title and any(k in title.lower() for k in kws) and link not in seen:
                seen.add(link)
                out.append({"title": title, "link": link, "source": source})
    return out[:limit]


# ---------------------------------------------------------------- FRED
def fred(series_id, key, limit=40):
    if not key:
        return []
    q = urllib.parse.urlencode({"series_id": series_id, "api_key": key, "file_type": "json",
                                "sort_order": "desc", "limit": limit})
    try:
        data = json.loads(_http(f"{FRED}?{q}").decode("utf-8", "replace"))
    except Exception as e:
        log(f"FRED {series_id} loi:", str(e)[:50])
        return []
    out = []
    for o in data.get("observations", []):
        v = o.get("value", ".")
        if v not in (".", "", None):
            try:
                out.append(float(v))
            except ValueError:
                pass
    return out   # moi nhat truoc


# ---------------------------------------------------------------- VNINDEX
def vnindex():
    try:
        from vnstock.api.quote import Quote
        h = Quote(symbol="VNINDEX", source="VCI").history(
            start=(dt.date.today() - dt.timedelta(days=400)).isoformat(),
            end=dt.date.today().isoformat(), interval="1D")
        c = [float(x) for x in h["close"].tolist() if x == x]
        if len(c) < 50:
            return None
        ma50 = sum(c[-50:]) / 50
        ma200 = sum(c[-200:]) / min(200, len(c))
        return {"last": c[-1], "ma50": ma50, "ma200": ma200}
    except Exception as e:
        log("vnindex loi:", str(e)[:60])
        return None


# ---------------------------------------------------------------- regime
def regime(fred_key):
    rows = []   # (ten, dir +1/-1/0, note)

    def add(name, d, note):
        rows.append((name, d, note))

    cpi = fred("CPIAUCSL", fred_key, 40)
    if len(cpi) >= 14:
        yoy = (cpi[0] / cpi[12] - 1) * 100
        yoy_prev = (cpi[1] / cpi[13] - 1) * 100
        accel = yoy - yoy_prev
        add("Lạm phát Mỹ", 1 if accel < -0.05 else -1 if accel > 0.05 else 0,
            f"CPI {yoy:.1f}% YoY ({'hạ nhiệt' if accel < 0 else 'tăng tốc' if accel > 0 else 'đi ngang'})")
    fed = fred("FEDFUNDS", fred_key, 6)
    if len(fed) >= 4:
        ch = fed[0] - fed[3]
        add("Lãi suất Fed", 1 if ch < -0.05 else -1 if ch > 0.05 else 0, f"Fed {fed[0]:.2f}%")
    t10 = fred("DGS10", fred_key, 30)
    if len(t10) >= 22:
        ch = t10[0] - t10[21]
        add("Lợi suất 10Y", 1 if ch <= -0.15 else -1 if ch >= 0.15 else 0, f"10Y {t10[0]:.2f}% ({ch:+.2f}đ/th)")
    usd = fred("DTWEXBGS", fred_key, 30)
    if len(usd) >= 22 and usd[21]:
        p = (usd[0] / usd[21] - 1) * 100
        add("Sức mạnh USD", 1 if p <= -0.5 else -1 if p >= 0.5 else 0, f"USD {p:+.1f}%/th")
    oil = fred("DCOILBRENTEU", fred_key, 30)
    if len(oil) >= 22 and oil[21]:
        p = (oil[0] / oil[21] - 1) * 100
        add("Giá dầu", 1 if p <= -8 else -1 if p >= 8 else 0, f"Dầu {oil[0]:.0f} USD ({p:+.0f}%/th)")
    vix = fred("VIXCLS", fred_key, 5)
    if vix:
        add("Biến động (VIX)", 1 if vix[0] < 16 else -1 if vix[0] > 25 else 0, f"VIX {vix[0]:.1f}")
    vni = vnindex()
    if vni:
        above = vni["last"] > vni["ma50"] and vni["last"] > vni["ma200"]
        below = vni["last"] < vni["ma50"] and vni["last"] < vni["ma200"]
        add("Xu hướng VNINDEX", 1 if above else -1 if below else 0,
            f"VNINDEX {vni['last']:.0f} ({'trên' if above else 'dưới' if below else 'quanh'} MA50/200)")

    if not rows:
        return {"score": 50, "label": "Trung tính", "note": "Chưa đủ dữ liệu vĩ mô.", "rows": []}
    n = len(rows)
    conf = min(1.0, n / 5)   # it tin hieu -> keo ve trung tinh (tranh diem cuc doan)
    score = round(50 + (50 * sum(d for _, d, _ in rows) / n) * conf)
    label = "Risk-On" if score >= 65 else "Risk-Off" if score <= 35 else "Trung tính"
    pos = [n for n, d, _ in rows if d > 0]
    neg = [n for n, d, _ in rows if d < 0]
    note = (("Hỗ trợ: " + ", ".join(pos[:4]) + ". ") if pos else "") + (("Cản trở: " + ", ".join(neg[:4]) + ".") if neg else "")
    return {"score": score, "label": label, "note": note.strip(), "rows": rows}


# ---------------------------------------------------------------- AI digest (Haiku)
_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_sentiment": {"type": "string", "enum": ["Tích cực", "Trung tính", "Tiêu cực"]},
        "summary_vi": {"type": "string"},
        "top": {"type": "array", "items": {"type": "object", "properties": {
            "title": {"type": "string"}, "impact": {"type": "string", "enum": ["↑", "→", "↓"]},
            "note": {"type": "string"}}, "required": ["title", "impact", "note"], "additionalProperties": False}},
    }, "required": ["overall_sentiment", "summary_vi", "top"], "additionalProperties": False}


def ai_digest(items, key):
    if not key or not items:
        return None
    try:
        import anthropic
    except ImportError:
        log("chua cai anthropic -> bo qua AI")
        return None
    headlines = "\n".join(f"- [{it['source']}] {it['title']}" for it in items)
    prompt = ("Bạn là chuyên gia phân tích vĩ mô cho TTCK Việt Nam. Dưới đây là tiêu đề tin hôm nay. Hãy:\n"
              "1) Đánh giá sắc thái CHUNG tới TTCK VN (Tích cực/Trung tính/Tiêu cực).\n"
              "2) summary_vi 3-5 câu tiếng Việt súc tích.\n"
              "3) top tối đa 6 tin tác động mạnh nhất: title ngắn, impact (↑ tốt/→ trung tính/↓ xấu), note 1 câu.\n\n"
              f"TIN:\n{headlines}")
    try:
        client = anthropic.Anthropic(api_key=key)
        resp = client.messages.create(
            model="claude-haiku-4-5", max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": _SCHEMA}})
        text = next((b.text for b in resp.content if b.type == "text"), "")
        return json.loads(text)
    except Exception as e:
        log("ai_digest loi:", str(e)[:120])
        return None


def load_opus_digest():
    """Doc ban phan tich do Opus 4.8 viet san (docs/data/ai_digest.json) -- dung
    THAY cho Claude API khi het credit. Cung schema voi ai_digest()."""
    p = os.path.join(ROOT, "docs", "data", "ai_digest.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
        if d.get("summary_vi") and d.get("top"):
            return d
    except Exception:
        pass
    return None


def best_link(title, raw):
    tw = set(re.findall(r"\w+", title.lower()))
    best, sc = None, 0
    for it in raw:
        ov = len(tw & set(re.findall(r"\w+", it["title"].lower())))
        if ov > sc:
            best, sc = it, ov
    return best if sc >= 3 else None


def main():
    if "--rawdump" in sys.argv:
        items = fetch_rss()
        out = os.path.join(ROOT, "docs", "data", "_rss_raw.json")
        json.dump({"date": today(), "items": items}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        log("rawdump:", len(items), "tin ->", out)
        return
    fred_key = (os.getenv("FRED_API_KEY") or "").strip()
    anthropic_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    items = fetch_rss()
    log("RSS:", len(items), "tin")
    reg = regime(fred_key)
    log("regime:", reg["score"], reg["label"])
    dig = ai_digest(items, anthropic_key) or load_opus_digest()
    src = "API" if (anthropic_key and dig and "_opus" not in dig) else ("Opus" if dig else "khong co")
    log("AI digest:", (dig.get("overall_sentiment") + f" (nguon {src})") if dig else "khong co (regime fallback)")

    t = today()
    if dig and dig.get("top"):
        out_items = []
        for x in dig["top"][:8]:
            imp = x.get("impact", "→")
            m = best_link(x.get("title", ""), items)
            out_items.append({"title": x.get("title", ""),
                              "sentiment": "+" if imp == "↑" else "-" if imp == "↓" else "",
                              "note": x.get("note", ""),
                              "source": m["source"] if m else "Tổng hợp AI",
                              "url": m["link"] if m else "", "date": t})
        summary = dig.get("summary_vi", "")
    else:
        out_items = [{"title": it["title"], "sentiment": "", "note": "",
                      "source": it["source"], "url": it["link"], "date": t} for it in items[:10]]
        summary = f"{reg['label']} ({reg['score']}/100). " + reg["note"]

    data = {"updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
            "regime": {"score": reg["score"], "label": reg["label"], "note": reg["note"]},
            "summary": summary, "items": out_items}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log(f"da ghi {OUT}: {len(out_items)} tin")

    if "--push" in sys.argv:
        import subprocess
        try:
            subprocess.run(["git", "-C", ROOT, "add", "docs/data/news.json"], check=True)
            if subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"]).returncode != 0:
                subprocess.run(["git", "-C", ROOT, "commit", "-m", "data: tin AI " + t], check=True)
                subprocess.run(["git", "-C", ROOT, "push"], check=True)
        except Exception as e:
            log("push err:", e)


if __name__ == "__main__":
    main()
