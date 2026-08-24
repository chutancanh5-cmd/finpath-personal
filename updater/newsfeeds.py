# -*- coding: utf-8 -*-
"""
newsfeeds.py — lop doc RSS dung chung cho macro bot va Prime Finance.

===============================================================================
BAN SAO SONG SINH — SUA MOT BAN PHAI CHEP SANG BAN KIA
===============================================================================
File nay ton tai GIONG HET o hai repo tach roi:
    vn-bots/macro/newsfeeds.py             (macro bot)
    finpath-personal/updater/newsfeeds.py  (Prime Finance)
Hai repo chay tren hai GitHub Actions khac nhau, khong checkout cheo nhau duoc,
nen khong co cach nao import chung. Doi chieu bang dong VERSION ben duoi.

===============================================================================
VI SAO PHAI CO TANG "SUC KHOE FEED" CHU KHONG CHI LA MOT DANH SACH URL
===============================================================================
Do that ngay 2026-08-24 tren 33 feed ung vien. Ba kieu hong deu tra HTTP 200,
deu trong nhu con song, va deu se lot qua neu chi bat exception:

  1. TRA VE TRANG HTML THAY VI RSS.
     vnexpress.net/rss/kinh-doanh-chung-khoan.rss -> tra ve TRANG CHU 279KB.
     nguoiquansat.vn/rss/... -> tra ve trang 404 dong goi trong HTTP 200.
     Bat bang: doc 300 byte dau, thay <!doctype html> thi la HTML, khong phai feed.

  2. FEED CON SONG NHUNG NOI DUNG DONG BANG.
     WSJ Markets parse sach, tra ve 20 item, tin moi nhat CU 19 THANG
     (bai DeepSeek thang 1/2025). Bat bang: do TUOI tin moi nhat.
     Feed qua STALE_HOURS bi VUT BO TOAN BO ITEM — vi tin 19 thang tuoi tron vao
     ban tin hom nay con te hon la khong co tin. Nhung no duoc BAO CAO, khong
     bi im lang: xem `health` tra ve tu collect().

  3. MOC THOI GIAN O TUONG LAI.
     VTV dong dau pubDate lech mui gio -> tuoi tin ra so AM. Khong duoc coi la
     moi tinh mot cach mu quang, cung khong duoc coi la hong. Kep ve 0 va ghi chu.

Nguyen tac chung, giong _VN_DEAD_FEEDS ben sources.py: mot nguon hong thi
KHONG duoc lang le bien mat khoi ban tin. No phai xuat hien o muc canh bao.
"""
import re
import html
import urllib.request
import datetime as dt
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

VERSION = "2026-08-25"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Tin moi nhat cua mot feed cu hon nguong nay -> coi la feed dong bang, vut item.
STALE_HOURS = 48

# ---------------------------------------------------------------------------
# DANH SACH FEED — moi dong deu da test song ngay 2026-08-24
# (so trong ngoac = tuoi tin moi nhat luc test, don vi gio)
# ---------------------------------------------------------------------------
VN_FEEDS = [
    ("CafeF Vĩ mô",           "https://cafef.vn/vi-mo-dau-tu.rss"),            # 0.9h
    ("CafeF Chứng khoán",     "https://cafef.vn/thi-truong-chung-khoan.rss"),  # 0.1h
    ("CafeF Tài chính-NH",    "https://cafef.vn/tai-chinh-ngan-hang.rss"),     # 0.7h
    ("VietStock Chứng khoán", "https://vietstock.vn/830/chung-khoan/co-phieu.rss"),  # 0.7h
    ("VietStock Vĩ mô",       "https://vietstock.vn/761/kinh-te/vi-mo-dau-tu.rss"),  # 3.7h
    ("VietStock Doanh nghiệp",
     "https://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss"),        # 1.2h
    ("VnEconomy Chứng khoán", "https://vneconomy.vn/chung-khoan.rss"),         # 4.9h
    ("VnEconomy Tài chính",   "https://vneconomy.vn/tai-chinh.rss"),           # 3.2h
]

# Tin quoc te dang CHU. macro bot von rat manh phan SO LIEU the gioi (BIS/ECB/
# Yahoo) nhung khong lay mot dong tin chu nao de giai thich vi sao so lieu dong.
WORLD_FEEDS = [
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),              # 0.1h
    ("CNBC Markets",
     "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069"),  # 0.2h
    ("FT Markets",    "https://www.ft.com/markets?format=rss"),                # 3.0h
    ("SCMP Economy",  "https://www.scmp.com/rss/92/feed"),                     # 0.8h
]

# ---------------------------------------------------------------------------
# CAC FEED DA TEST VA LOAI — giu lai de nguoi sau khong mat cong thu lai
# ---------------------------------------------------------------------------
REJECTED = {
    "https://vnexpress.net/rss/kinh-doanh-chung-khoan.rss":
        "HTTP 200 nhung tra ve TRANG CHU HTML",
    "https://nguoiquansat.vn/rss/chung-khoan-31.rss":
        "HTTP 200 nhung tra ve trang 404 HTML",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml":
        "WSJ: parse OK nhung tin moi nhat cu 19 thang",
    "https://vietstock.vn/rss":            "trang muc luc, khong phai feed",
    "https://thesaigontimes.vn/feed/":     "khong phai RSS",
    "https://baodautu.vn/rss/tai-chinh-ngan-hang.rss": "0 item",
    "https://www.tinnhanhchungkhoan.vn/rss/chung-khoan.rss":
        "404 (ban song la /rss/home.rss)",
    "https://dantri.com.vn/kinh-doanh.rss": "404 (ban song la /rss/kinh-doanh.rss)",
    "https://feeds.reuters.com/reuters/businessNews": "Reuters da bo RSS, DNS chet",
    "https://www.bis.org/list/press_rss.xml":         "404",
    "https://www.imf.org/en/News/RSS?Language=ENG":   "403",
    "https://www.bls.gov/feed/bls_latest.rss":        "403",
    "https://tradingeconomics.com/vietnam/rss":       "403",
    "https://www.ecb.europa.eu/rss/press.html":
        "SSL CERTIFICATE_VERIFY_FAILED tu Windows",
    "https://asia.nikkei.com/rss/feed/nar":           "0 item",
    "https://vietstock.vn/143/tai-chinh/ngan-hang.rss":
        "song nhung cap nhat ~6 ngay/lan, qua thua",
}

VN_KEYWORDS = [
    "lạm phát", "lãi suất", "tỷ giá", "cpi", "fed", "fomc", "ngân hàng nhà nước",
    "nhnn", "tăng trưởng", "gdp", "xuất khẩu", "nhập khẩu", "fdi", "trái phiếu",
    "vn-index", "vnindex", "tín dụng", "vàng", "giá dầu", "usd", "chính sách tiền tệ",
    "chứng khoán", "khối ngoại", "cổ phiếu", "thị trường",
]

WORLD_KEYWORDS = [
    "fed", "fomc", "rate", "rates", "inflation", "cpi", "pce", "treasury", "yield",
    "dollar", "tariff", "trade", "gdp", "recession", "jobs", "payroll", "unemployment",
    "ecb", "boj", "china", "stocks", "market", "markets", "oil", "gold", "bond",
    "earnings", "economy", "growth", "central bank", "stimulus", "export", "import",
]

# Tu nhieu — bo ra khi so trung tin. Giu ngan: chi can du de hai ban tin cung mot
# su kien co chung phan LOI, khong can chuan hoa ngon ngu.
_STOP = set("""
va và của cho với từ trong ra vào lên xuống về được các những một hai này đó là
có không sẽ đã đang bị bởi khi nếu thì mà nên do tại trên dưới sau trước hơn nhất
tăng giảm the a an and or of to in on for with from at by as is are was were be
been will has have had it its this that these those new
""".split())


def log(*a):
    print("[newsfeeds]", *a, flush=True)


# ------------------------------------------------------------------ doc & parse
def _http(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _clean(s):
    """Bo tag, giai ma entity.

    unescape HAI LAN vi mot so bao (Thanh Nien) dong goi entity hai tang:
    &amp;agrave; -> &agrave; -> a-huyen. Mot lan unescape se de lai '&agrave;'
    nguyen van trong tieu de.
    """
    if not s:
        return ""
    s = html.unescape(html.unescape(s))
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_date(raw):
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _age_hours(d):
    if d is None:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    return (now - d.astimezone(dt.timezone.utc)).total_seconds() / 3600


def fetch_feed(source, url, timeout=20):
    """Doc mot feed. Tra ve (items, status).

    status["state"] la mot trong:
      ok      — co tin, tin moi nhat con trong STALE_HOURS
      stale   — co tin nhung tin moi nhat qua cu  -> items da bi VUT (tra ve [])
      nodate  — co tin nhung khong doc duoc moc thoi gian -> van giu items
      dead    — loi HTTP / tra ve HTML / 0 item   -> items rong
    """
    st = {"source": source, "url": url, "state": "dead", "n": 0,
          "age_h": None, "note": "", "kept": 0}
    try:
        raw = _http(url, timeout)
    except Exception as e:
        st["note"] = f"{type(e).__name__}: {str(e)[:70]}"
        return [], st

    # Bay so 1: trang HTML doi lot feed, tra ve kem HTTP 200.
    head = raw.lstrip()[:300].lower()
    if b"<!doctype html" in head or head.startswith(b"<html"):
        st["note"] = f"tra ve trang HTML ({len(raw)}B), khong phai RSS"
        return [], st

    try:
        root = ET.fromstring(raw)
    except Exception as e:
        st["note"] = f"XML hong ({len(raw)}B): {str(e)[:60]}"
        return [], st

    nodes = list(root.iter("item")) or [e for e in root.iter() if e.tag.endswith("}entry")]
    if not nodes:
        st["note"] = "0 item"
        return [], st

    items, newest = [], None
    for nd in nodes:
        title = link = pub = ""
        for ch in nd:
            tag = ch.tag.split("}")[-1]
            if tag == "title" and not title:
                title = _clean(ch.text)
            elif tag == "link" and not link:
                link = _clean(ch.text) or (ch.attrib.get("href") or "")
            elif tag in ("pubDate", "published", "updated", "date") and not pub:
                pub = (ch.text or "").strip()
        if not title:
            continue
        d = _parse_date(pub)
        if d and (newest is None or d > newest):
            newest = d
        items.append({"title": title, "link": link, "source": source,
                      "time": pub, "_dt": d})

    st["n"] = len(items)
    age = _age_hours(newest)

    if age is None:
        st["state"] = "nodate"
        st["note"] = "khong doc duoc moc thoi gian -> khong do duoc do tuoi"
        return items, st

    # Bay so 3: moc thoi gian o tuong lai (lech mui gio ben bao).
    if age < 0:
        st["note"] = f"moc thoi gian o TUONG LAI {abs(age):.1f}h (bao dong dau lech mui gio)"
        age = 0.0
    st["age_h"] = round(age, 1)

    # Bay so 2: feed dong bang.
    if age > STALE_HOURS:
        st["state"] = "stale"
        st["note"] = (f"tin moi nhat cu {age / 24:.1f} ngay -> VUT toan bo "
                      f"{len(items)} tin, khong dua vao ban tin")
        return [], st

    st["state"] = "ok"
    return items, st


# --------------------------------------------------------------------- khu trung
def _norm(title):
    t = _clean(title).lower()
    t = re.sub(r"[^0-9a-zà-ỹ\s]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _tokens(title):
    return {w for w in _norm(title).split() if len(w) > 1 and w not in _STOP}


def _same_story(a, b, thr=0.60, min_share=4):
    """Hai tieu de co phai cung mot su kien khong (Jaccard tren tu co nghia).

    Can thiet vi bay gio co 8 nguon: CafeF, VietStock va VnEconomy thuong xuyen
    viet lai cung mot thong cao. Khu trung theo LINK khong bat duoc truong hop
    nay — moi bao mot link khac nhau.

    NGUONG 0.60 LA SO DO, KHONG PHAI SO DOAN. Hieu chinh 2026-08-25 tren 86 tin
    that gom tu ca 8 feed:
      0.75  bat 5 cap — 4 cap VnEconomy dang mot bai nam o hai chuyen muc (J=1.00)
            + 1 cap bang lai suat ngan hang 24/8 vs 23/8. Dung ca 5, nhung SOT.
      0.60  bat them cap bang gia vang trong ngay (J=0.68). Dung. Khong cap nao sai.
      0.50  bat them "Theo dau dong tien ca map 24/08" vs "21/08" (J=0.50) — SAI,
            do la hai bai phan tich cua HAI NGAY khac nhau, gop lai la mat bai
            hom nay.
      0.40  bat them "vang nhan bat tang 8,5 trieu" vs "vang nhan tang 3-4 trieu"
            (J=0.46) — SAI, hai tin khac nhau.
    Nen 0.60 la nguong cao nhat con bat het cap trung THAT ma chua gop nham cap nao.
    Muon sua thi chay lai phep do o tren, dung chinh tay theo cam giac.

    Luu y: cac cot dinh ky ("lai suat ngan hang ngay X") bi gop la CO Y. pool da
    sap xep tin moi truoc, nen ban duoc giu lai luon la ban moi nhat.
    """
    if not a or not b:
        return False
    share = len(a & b)
    if share < min_share:
        return False
    return share / len(a | b) >= thr


def dedupe(items):
    """Khu trung theo link, roi theo noi dung tieu de. Giu ban XUAT HIEN TRUOC
    (thu tu feed trong VN_FEEDS = thu tu uu tien nguon)."""
    out, seen_links, sigs = [], set(), []
    for it in items:
        link = (it.get("link") or "").strip()
        if link and link in seen_links:
            continue
        tk = _tokens(it.get("title", ""))
        if any(_same_story(tk, s) for s in sigs):
            continue
        if link:
            seen_links.add(link)
        sigs.append(tk)
        out.append(it)
    return out


# --------------------------------------------------------------------- diem vao
def balance_by_source(items, max_items):
    """Chia deu suat theo nguon thay vi cat thang tu dau danh sach.

    VI SAO CAN: xep thuan theo do moi thi mot nguon dang bai day se an het cho.
    Do that 2026-08-25: Yahoo Finance chiem 13/18 suat quoc te, CafeF chiem 9/18
    suat trong nuoc — dung ra la doc mot bao, khong phai tam nguon. Ma them nguon
    chinh la de KHONG bi phu thuoc mot bao.

    Cach lam: vong tron qua tung nguon, moi vong lay 1 tin moi nhat con lai. Nguon
    het tin thi bo qua, khong de trong suat.
    """
    by = {}
    for it in items:
        by.setdefault(it.get("source", "—"), []).append(it)
    out, order = [], list(by)
    while len(out) < max_items and any(by[s] for s in order):
        for s in order:
            if not by[s]:
                continue
            out.append(by[s].pop(0))
            if len(out) >= max_items:
                break
    return out


def collect(feeds=None, keywords=None, per_feed=25, max_items=18, timeout=20,
            balance=True):
    """Doc toan bo feed, loc theo tu khoa, khu trung. Tra ve (items, health).

    `health` la danh sach status cua TUNG feed, KE CA feed hong. Nguoi goi phai
    dua no vao bao cao — do la ca diem cua ham nay.
    """
    feeds = feeds or VN_FEEDS
    kws = [k.lower() for k in (keywords if keywords is not None else VN_KEYWORDS)]
    pool, health = [], []
    for source, url in feeds:
        items, st = fetch_feed(source, url, timeout)
        health.append(st)
        if st["state"] in ("dead", "stale"):
            log(f"CANH BAO {source}: {st['state'].upper()} — {st['note']}")
            continue
        kept = 0
        for it in items[:per_feed]:
            if not kws or any(k in it["title"].lower() for k in kws):
                pool.append(it)
                kept += 1
        st["kept"] = kept

    # Tin moi truoc. Tin khong co ngay xep cuoi thay vi bi vut.
    _floor = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    pool.sort(key=lambda x: (x.get("_dt") is not None, x.get("_dt") or _floor),
              reverse=True)
    before = len(pool)
    pool = dedupe(pool)
    picked = balance_by_source(pool, max_items) if balance else pool[:max_items]
    log(f"gom {before} tin -> khu trung con {len(pool)} -> lay {len(picked)}"
        + (" (chia deu theo nguon)" if balance else ""))

    out = []
    for it in picked:
        it = dict(it)
        it.pop("_dt", None)
        out.append(it)
    return out, health


def health_summary(health):
    """Mot dong tom tat cho log/footer."""
    ok = sum(1 for h in health if h["state"] in ("ok", "nodate"))
    bad = [h for h in health if h["state"] in ("dead", "stale")]
    s = f"{ok}/{len(health)} feed sống"
    if bad:
        s += " · hỏng: " + ", ".join(f"{h['source']} ({h['state']})" for h in bad)
    return s


if __name__ == "__main__":
    import sys
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass
    which = sys.argv[1] if len(sys.argv) > 1 else "vn"
    fs, kw = (WORLD_FEEDS, WORLD_KEYWORDS) if which == "world" else (VN_FEEDS, VN_KEYWORDS)
    items, health = collect(fs, kw)
    print("\n=== SUC KHOE FEED ===")
    for h in health:
        age = f"{h['age_h']}h" if h.get("age_h") is not None else "—"
        print(f"  {h['state']:<7} {h['source']:<24} {h['n']:>3} tin  tuoi {age:>7}  "
              f"lay {h.get('kept', 0):>2}  {h['note']}")
    print(f"\n{health_summary(health)}")
    print(f"\n=== {len(items)} TIN SAU KHU TRUNG ===")
    for it in items:
        print(f"  [{it['source']}] {it['title'][:78]}")
