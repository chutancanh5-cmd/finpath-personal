# -*- coding: utf-8 -*-
"""
update_news.py -- Tin AI + diem regime -> docs/data/news.json  (CODE GOC FinPath)

Tu lay du lieu cong khai, KHONG phu thuoc thu muc macro/:
  - RSS tieng Viet: 8 feed (CafeF x3, VietStock x3, VnEconomy x2) qua newsfeeds.py,
    co do tuoi feed va khu trung theo noi dung. Truoc 25/08/2026 chi co 3 feed,
    trong do 2 la CafeF -> CafeF hong mot buoi la muc tin trong tron.
  - Regime score tu VNINDEX (vnstock) + FRED (CPI/Fed/10Y/USD/dau/VIX)
  - Tom tat + sentiment bang Sonnet 5 (neu co ANTHROPIC_API_KEY con credit)
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

import newsfeeds as NF   # ban sao song sinh cua vn-bots/macro/newsfeeds.py

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

# Danh sach feed + tu khoa nam trong newsfeeds.py (dung chung voi macro bot).
FEEDS = NF.VN_FEEDS
KEYWORDS = NF.VN_KEYWORDS

# Suc khoe feed cua lan quet gan nhat — ghi vao news.json de trang Prime Finance
# noi duoc "muc tin ngan di vi nguon hong", thay vi de nguoi doc hieu nham thanh
# "hom nay it tin". Xem newsfeeds.py de biet ba kieu feed hong deu tra HTTP 200.
LAST_HEALTH = []


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
    """Tin vi mo tu 8 feed, da loc tu khoa, khu trung va chia deu theo nguon."""
    global LAST_HEALTH
    try:
        items, LAST_HEALTH = NF.collect(NF.VN_FEEDS, NF.VN_KEYWORDS,
                                        per_feed=25, max_items=limit)
    except Exception as e:
        log("fetch_rss loi:", str(e)[:100])
        items, LAST_HEALTH = [], []
        return items
    log("feed:", NF.health_summary(LAST_HEALTH))
    # Khuon {title, link, source, desc} -- desc them 2026-09-04 de Discord tin moi
    # co the hien tom tat, khong chi tieu de+link. Cac ham doc theo khuon nay
    # (loc_tin_moi, best_link, bao_discord_tin_moi) deu dung .get() nen truong moi
    # khong lam vo cai gi dang doc theo khuon cu.
    return [{"title": it["title"], "link": it.get("link", ""),
             "source": it.get("source", ""), "desc": it.get("desc", "")} for it in items]


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
        try:
            from vnstock_data.api.quote import Quote
        except Exception:
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


# ---------------------------------------------------------------- AI digest (Sonnet 5)
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
    # Kem mo ta bai (RSS/meta) chu khong chi tieu de: "note" viet tu tieu de khong thi
    # chi la doan tieu de viet lai, khong phai thong tin tu bai bao.
    headlines = "\n".join(
        f"- [{it['source']}] {it['title']}"
        + (f"\n  ({it['desc']})" if it.get("desc") else "") for it in items)
    prompt = ("Bạn là chuyên gia phân tích vĩ mô cho TTCK Việt Nam. Dưới đây là tin hôm nay (tiêu đề + mô tả bài nếu có). Hãy:\n"
              "1) Đánh giá sắc thái CHUNG tới TTCK VN (Tích cực/Trung tính/Tiêu cực).\n"
              "2) summary_vi 3-5 câu tiếng Việt súc tích.\n"
              "3) top tối đa 6 tin tác động mạnh nhất: title ngắn, impact (↑ tốt/→ trung "
              "tính/↓ xấu), note 1-2 câu nêu THÔNG TIN CỤ THỂ trong tin (số liệu, ai làm "
              "gì, mốc thời gian) chứ không diễn đạt lại tiêu đề.\n\n"
              f"TIN:\n{headlines}")
    try:
        client = anthropic.Anthropic(api_key=key, timeout=60.0, max_retries=1)
        resp = client.messages.create(
            # Tin tuc -> Haiku 4.5 (quyet dinh 2026-09-09). Cac phan can suy luan nang
            # (phan tich ky thuat, vi mo) van giu Opus 5.
            model="claude-haiku-4-5-20251001", max_tokens=2000,
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


def load_regime_cu():
    """Doc regime da ghi trong news.json truoc do -- dung THAY khi lan chay nay
    khong co FRED_API_KEY.

    Cung tinh than voi load_opus_digest() o tren: khong co nang luc thi GIU ban cu,
    dung ghi de bang ban nghe hon. Can thiet tu 2026-08-21 khi PC thanh nguon chinh:
    PC KHONG co FRED_API_KEY (khoa chi nam trong GitHub secrets) nen regime() chi lay
    duoc 1/6 chi bao -> diem 40 'Trung tinh' gia. Cloud co khoa nhung cong chan
    (ci_gate.py) lai cho cloud bo qua khi PC con tuoi -> ban nghe cua PC se la ban
    duy nhat app nhin thay."""
    p = os.path.join(ROOT, "docs", "data", "news.json")
    try:
        r = (json.load(open(p, encoding="utf-8")) or {}).get("regime") or {}
        if r.get("score") is not None and r.get("label"):
            return r
    except Exception:
        pass
    return None


SEEN_PATH = os.path.join(HERE, "news_seen.json")


def loc_tin_moi(items):
    """-> (danh sach tin CHUA TUNG THAY, co_phai_lan_dau).

    Khoa dedup dung `link` vi fetch_rss() da dedup theo link trong cung mot lan chay,
    va link on dinh hon title (bao hay sua tit sau khi dang).

    Lan DAU (chua co news_seen.json): coi nhu KHONG co tin moi va chi ghi nhan toan bo
    tin hien tai vao state. Neu khong lam vay thi lan chay dau se ban ~14 tin cu mot luc
    vao Discord."""
    from notify import load_sent
    lan_dau = not os.path.exists(SEEN_PATH)
    da_thay = load_sent(SEEN_PATH)
    moi = [it for it in items if it["link"] not in da_thay]
    return ([], True) if lan_dau else (moi, False)


def ghi_nhan_da_thay(items):
    from notify import load_sent, save_sent
    da_thay = load_sent(SEEN_PATH)
    da_thay.update(it["link"] for it in items)
    save_sent(SEEN_PATH, da_thay)


def xuat_github_output(khoa, gia_tri):
    """Ghi output cho step sau doc qua steps.<id>.outputs.<khoa> (chi khi chay trong CI)."""
    p = os.environ.get("GITHUB_OUTPUT")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"{khoa}={gia_tri}\n")


# Doc mo ta / than bai cua trang bao: dung CHUNG voi macro bot qua newsfeeds.py
# (ban sao song sinh o hai repo). De ben do vi ca hai bot deu can, va vi hai chi
# tiet trong do phai do thuc te moi biet: VnEconomy tra ve than nen gzip ma urllib
# khong tu giai, va menu cua trang bao co the nam gon trong MOT the <p> dai 3.387
# ky tu, dai hon ca bai bao.
fetch_article_desc = NF.article_desc
fetch_article_text = NF.article_text


def lay_ngu_canh(items):
    """Do day du lieu cho AI tom tat: than bai (song song) > mo ta meta > desc RSS.

    Chi doc the meta cho tin nao KHONG co ca than bai lan desc RSS -- truoc do moi tin
    ton hai luot tai trang, trong khi da co than bai thi the meta khong them gi.
    """
    NF.bo_sung_noi_dung(items)
    for it in items:
        if not it.get("noi_dung") and not it.get("desc"):
            it["desc"] = fetch_article_desc(it.get("link", ""))
    return items


# Sac thai tung tin: app Prime Finance da hien (sentiment +/-/"" trong news.json ->
# app.js renderNews) nhung Discord thi chua, nen doc tin tren Discord khong biet tin
# tot hay xau neu khong doc het tom tat. Dung DUNG 3 nhan app dang hien de hai noi
# khong lech chu.
_SAC_THAI = ["Tích cực", "Trung tính", "Tiêu cực"]

# Huy hieu + mau vien embed theo sac thai.
_BADGE = {"Tích cực": ("🟢", 0x2ecc71), "Tiêu cực": ("🔴", 0xe74c3c),
          "Trung tính": ("⚪", 0x95a5a6)}

_SUM_SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {
        "title": {"type": "string"}, "y_chinh": {"type": "string"},
        "sac_thai": {"type": "string", "enum": _SAC_THAI}},
        "required": ["title", "y_chinh", "sac_thai"], "additionalProperties": False}}},
    "required": ["items"], "additionalProperties": False}


MOI_RAW = os.path.join(ROOT, "docs", "data", "_moi_raw.json")
MOI_SUM = os.path.join(ROOT, "docs", "data", "_moi_summaries.json")


def dump_moi_for_ai(all_items, toi_da=6):
    """Ghi cac tin MOI sap ban Discord ra file, de buoc CLI `claude -p` (Claude thue bao,
    khong ton API credit) doc va viet 'y chinh' cho tung tin -- cung co che voi
    load_opus_digest()/ai_prompt_ci.txt ben tren, chi khac muc tieu la tung tin rieng
    le thay vi ban tom tat chung.

    Chi goi trong buoc --rawdump (job digest), TRUOC step CLI trong workflow. Khong
    ghi state (khong dung ghi_nhan_da_thay) vi day chi la doc truoc de chuan bi du
    lieu cho AI -- --discord ben sau moi la noi tinh 'moi' that su va ghi state."""
    moi, lan_dau = loc_tin_moi(all_items)
    if lan_dau or not moi:
        return
    chon = lay_ngu_canh(moi[:toi_da])
    json.dump({"date": today(), "items": [
        {"title": it["title"], "source": it["source"], "desc": it.get("desc", ""),
         "noi_dung": it.get("noi_dung", "")}
        for it in chon]}, open(MOI_RAW, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"da ghi {MOI_RAW}: {len(chon)} tin cho AI tom tat")


def _chuan_hoa_tom_tat(x):
    """Mot muc AI tra ve -> {y_chinh, sac_thai}. Sac thai la nhan khong hop le thi bo
    han (roi ve Trung tinh) thay vi de chu la lot vao huy hieu tren Discord."""
    y = (x.get("y_chinh") or "").strip()
    st = (x.get("sac_thai") or "").strip()
    return {"y_chinh": y, "sac_thai": st if st in _SAC_THAI else "Trung tính"}


def load_moi_summaries():
    """Doc tom tat do buoc CLI (Claude thue bao) viet san vao MOI_SUM -- dung
    KHI KHONG co ANTHROPIC_API_KEY (truong hop thuong gap, xem finpath-tinai.yml).

    -> {title: {"y_chinh": ..., "sac_thai": ...}}. Ban ghi cu (y_chinh la chuoi tran)
    van doc duoc: coi nhu Trung tinh, de mot file _moi_summaries.json con sot lai tu
    lan chay truoc khong lam vo buoc ban Discord."""
    try:
        d = json.load(open(MOI_SUM, encoding="utf-8"))
        items = d.get("items") if isinstance(d, dict) else d
        if isinstance(items, list):
            return {x["title"]: _chuan_hoa_tom_tat(x) for x in items if x.get("title")}
        if isinstance(items, dict):
            return {k: (_chuan_hoa_tom_tat(v) if isinstance(v, dict)
                        else {"y_chinh": str(v), "sac_thai": "Trung tính"})
                    for k, v in items.items()}
    except Exception:
        pass
    return {}


# Yeu cau dat ra cho AI -- dung CHUNG cho duong API (ham duoi) va duong CLI thue bao
# (updater/ai_prompt_discord_ci.txt). Sua o day thi PHAI sua ca file prompt kia, neu
# khong hai duong se cho ra hai kieu tom tat khac nhau tuy hom do chay duong nao.
YEU_CAU_TOM_TAT = (
    "Bạn tóm tắt tin tài chính cho nhà đầu tư chứng khoán Việt Nam.\n\n"
    "Với MỖI tin dưới đây, dựa vào NỘI DUNG BÀI (nếu có) chứ không chỉ tiêu đề:\n"
    "1) y_chinh: 2-3 câu tiếng Việt (40-70 từ) TÓM TẮT BÀI BÁO — nêu số liệu cụ thể, "
    "ai quyết định gì, mốc thời gian, và hàm ý cho thị trường/cổ phiếu liên quan. "
    "TUYỆT ĐỐI không chép lại hay diễn đạt vòng vo chính tiêu đề: người đọc đã thấy "
    "tiêu đề rồi nên phần tóm tắt phải nói THÊM thông tin từ bài báo.\n"
    "2) sac_thai: đánh giá tác động tới thị trường chứng khoán Việt Nam, chọn đúng 1 "
    "trong 3 nhãn: Tích cực | Trung tính | Tiêu cực.\n\n"
    "Giữ đúng thứ tự và số lượng tin, trường title trả về Y NGUYÊN tiêu đề gốc.")


def _khoi_tin_cho_ai(items):
    """Khoi van ban mo ta tung tin cho AI -- dung chung o ca hai duong (API/CLI)."""
    lines = []
    for i, it in enumerate(items, 1):
        than = (it.get("noi_dung") or "").strip()
        ctx = than or it.get("desc") or "(không lấy được nội dung, chỉ có tiêu đề)"
        nhan = "Nội dung bài" if than else "Mô tả"
        lines.append(f"{i}. [{it['source']}] {it['title']}\n   {nhan}: {ctx}")
    return "\n\n".join(lines)


def ai_diem_chinh(items, key):
    """AI tom tat + cham sac thai cho tung tin sap ban Discord, goi truc tiep qua API
    SDK (ton credit). Tin tuc dung HAIKU 4.5 (quyet dinh 2026-09-09: phan tin tuc do
    Haiku tom tat, phan can suy luan nang -- ky thuat, vi mo -- moi dung Opus 5).

    -> dict {title: {"y_chinh", "sac_thai"}}; rong neu khong co key hoac AI loi --
    nguoi goi roi ve load_moi_summaries() (Claude thue bao qua CLI) roi moi toi desc tho."""
    if not key or not items:
        return {}
    try:
        import anthropic
    except ImportError:
        log("chua cai anthropic -> bo qua AI tom tat")
        return {}
    prompt = YEU_CAU_TOM_TAT + "\n\nTIN:\n" + _khoi_tin_cho_ai(items)
    try:
        client = anthropic.Anthropic(api_key=key, timeout=60.0, max_retries=1)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": _SUM_SCHEMA}})
        text = next((b.text for b in resp.content if b.type == "text"), "")
        data = json.loads(text).get("items", [])
        return {it["title"]: _chuan_hoa_tom_tat(d) for it, d in zip(items, data)}
    except Exception as e:
        log("ai_diem_chinh loi:", str(e)[:120])
        return {}


def bao_discord_tin_moi(moi, anthropic_key=None, toi_da=6):
    """Ban cac tin MOI vao kenh tin tuc. Chi goi khi that su co tin moi.

    -> True neu coi nhu DA XU LY XONG (ban thanh cong, HOAC kenh chua cau hinh nen
       khong the ban) -> nguoi goi ghi nhan state.
    -> False chi khi ban THAT BAI (mang/Discord loi) -> giu state de lan sau bao lai.

    Phan biet nay quan trong: neu coi 'chua cau hinh webhook' la that bai thi state khong
    bao gio duoc ghi nhan, va o nhip 5 phut se goi Claude LAI VO HAN cho cung mot tin."""
    hook = (os.environ.get("DISCORD_WEBHOOK_NEWS") or "").strip()
    if not hook.startswith("http"):
        log("chua co DISCORD_WEBHOOK_NEWS -> bo qua Discord (van ghi nhan tin de khong "
            "goi Claude lap lai vo han cho cung mot tin)")
        return True
    from notify import send_discord
    # Doc than bai (roi ve meta trang bao) truoc khi nho AI tom tat -- xem
    # fetch_article_text(): khong co than bai thi AI chi viet lai duoc tieu de.
    chon = moi[:toi_da]
    # Ban CLI (Claude thue bao) da viet san o buoc --rawdump + `claude -p` trong
    # workflow -> co san thi KHONG tai lai trang bao nua (buoc --rawdump vua tai xong,
    # tien trinh nay la tien trinh khac nen items khong con noi_dung).
    tom_tat = load_moi_summaries()
    thieu = [it for it in chon if not (tom_tat.get(it["title"]) or {}).get("y_chinh")]
    if thieu:
        # Chi doc than bai cho tin CHUA co tom tat, roi goi API SDK (ton credit) neu
        # co key. Khong co key thi than bai/desc van la van du phong cho embed.
        lay_ngu_canh(thieu)
        tom_tat.update(ai_diem_chinh(thieu, anthropic_key))

    # Tin nhan chinh CHI con dong tieu de. Truoc day no liet ke lai "• [nguon] tieu de"
    # cho tung tin, ma ngay ben duoi moi embed da in dung tieu de do lam title -> doc
    # thay hai lan cung mot chu (nguoi dung phan anh 2026-09-09).
    noi_dung = f"📰 **{len(moi)} tin mới** — {today()}"
    if len(moi) > toi_da:
        noi_dung += f"  ·  hiển thị {toi_da}, còn {len(moi) - toi_da} tin khác"

    embeds = []
    for it in chon:
        t = tom_tat.get(it["title"]) or {}
        sac = t.get("sac_thai")
        than = (t.get("y_chinh") or it.get("desc") or "").strip()
        if sac:
            huy_hieu, mau = _BADGE.get(sac, _BADGE["Trung tính"])
            mo_ta, chan = f"{huy_hieu} **{sac}**\n\n{than}", it["source"]
        else:
            # KHONG co AI (het quota / CLI loi) -> KHONG duoc in "Trung tính": do la mot
            # danh gia chua ai dua ra. Noi thang la chua cham, giong cach news.json khai
            # bao nguon tin hong thay vi im lang de nguoi doc hieu nham.
            mau = _BADGE["Trung tính"][1]
            mo_ta, chan = than, f"{it['source']} · chưa chấm sắc thái (không gọi được AI)"
        embeds.append({
            "title": it["title"][:250], "url": it["link"], "color": mau,
            "description": mo_ta[:600], "footer": {"text": chan}})
    try:
        send_discord(hook, noi_dung, embeds, username="FinPath · Tin tức")
        log(f"da ban Discord {len(moi)} tin moi"
            + (f" ({len(tom_tat)} co AI tom tat)" if tom_tat else " (khong co AI tom tat)"))
        return True
    except Exception as e:
        log("Discord loi:", str(e)[:120])
        return False


def best_link(title, raw):
    tw = set(re.findall(r"\w+", title.lower()))
    best, sc = None, 0
    for it in raw:
        ov = len(tw & set(re.findall(r"\w+", it["title"].lower())))
        if ov > sc:
            best, sc = it, ov
    return best if sc >= 3 else None


def main():
    # --check-new: quet RSS, bao cho workflow biet CO tin moi hay khong roi dung.
    # Cac buoc sau (goi Claude, ghi news.json, commit, Discord) deu bi chan neu khong co
    # tin moi -> chay moi 5 phut nhung hau het cac lan thoat trong vai giay, khong ton
    # quota Claude, khong ban Discord, khong day gi len Prime Finance.
    # KHONG cap nhat state o day: phai de --discord ghi nhan SAU KHI ban thanh cong,
    # neu khong lan chay nay se "nuot" tin moi ma chua he bao ai.
    if "--check-new" in sys.argv:
        items = fetch_rss()
        out = os.path.join(ROOT, "docs", "data", "_rss_raw.json")
        json.dump({"date": today(), "items": items}, open(out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        moi, lan_dau = loc_tin_moi(items)
        if lan_dau:
            ghi_nhan_da_thay(items)
            log(f"lan dau chay -> ghi nhan {len(items)} tin hien co, KHONG bao (tranh ban don)")
        elif moi:
            log(f"co {len(moi)} tin moi / {len(items)} tin quet duoc")
        else:
            log(f"khong co tin moi ({len(items)} tin deu da thay) -> dung")
        xuat_github_output("has_new", "true" if (moi and not lan_dau) else "false")
        return

    if "--rawdump" in sys.argv:
        items = fetch_rss()
        out = os.path.join(ROOT, "docs", "data", "_rss_raw.json")
        json.dump({"date": today(), "items": items}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        log("rawdump:", len(items), "tin ->", out)
        dump_moi_for_ai(items)
        return
    fred_key = (os.getenv("FRED_API_KEY") or "").strip()
    anthropic_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    items = fetch_rss()
    log("RSS:", len(items), "tin")
    moi, lan_dau = loc_tin_moi(items)
    if "--discord" in sys.argv:
        if lan_dau:
            ghi_nhan_da_thay(items)
            log("lan dau chay -> ghi nhan tin hien co, khong bao Discord")
        elif moi:
            # Chi ghi nhan SAU KHI ban thanh cong: ban that bai thi lan sau bao lai,
            # tin moi khong bi mat lang le.
            if bao_discord_tin_moi(moi, anthropic_key):
                ghi_nhan_da_thay(moi)
        else:
            log("khong co tin moi -> khong ban Discord")
    reg = regime(fred_key)
    if not fred_key:
        cu = load_regime_cu()
        if cu:
            log(f"khong co FRED_API_KEY -> GIU regime cu ({cu['score']} {cu['label']}) "
                f"thay vi ghi de bang ban 1 chi bao ({reg['score']})")
            reg = cu
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

    # Suc khoe nguon tin di kem du lieu. Neu mot feed chet, trang phai noi ra —
    # muc tin ngan di la vi nguon hong, khong phai vi hom nay khong co tin.
    feeds_bad = [{"source": h["source"], "state": h["state"], "note": h["note"]}
                 for h in LAST_HEALTH if h.get("state") in ("dead", "stale")]
    data = {"updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
            "regime": {"score": reg["score"], "label": reg["label"], "note": reg["note"]},
            "summary": summary, "items": out_items,
            "feeds": {"total": len(LAST_HEALTH),
                      "ok": len(LAST_HEALTH) - len(feeds_bad),
                      "bad": feeds_bad}}
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
