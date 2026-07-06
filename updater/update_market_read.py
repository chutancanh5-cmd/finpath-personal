# -*- coding: utf-8 -*-
"""
update_market_read.py -- "Doc hieu thi truong" -> docs/data/market_read.json

Doc CHIEN DICH cua tay to qua nhieu thang (khung dai), khong doan tung cay nen:
  Giai doan (Weinstein Stage / Wyckoff) theo MA150 (~30 tuan) + do doc:
    1 Tich luy (day, gom hang)   2 Day gia (markup)
    3 Phan phoi (dinh, xa hang)  4 De gia (markdown)
  Dau chan dong tien: OBV (tien am tham vao/ra), vi tri trong range 6 thang, vol kho han.
  Tin hieu: MARKUP (pha base 6 thang + vol bung) / ACCUM (dang tich luy, OBV vao rong).

Ma nguon goc cua FinPath (khong sao chep tu du an khac). Khung NGAY, chay cuoi phien.

Usage:
  python update_market_read.py                 # ghi market_read.json
  python update_market_read.py --discord       # + ban Discord (chuyen pha dang chu y)
  python update_market_read.py --push          # + git commit & push
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
os.environ.setdefault("ACCEPT_TC", "tôi đồng ý")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

import notify

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "data", "market_read.json")
STATE = os.path.join(HERE, "marketread_state.json")
CFG = os.path.join(HERE, "marketread_config.json")
VN_TZ = timezone(timedelta(hours=7))

# Ro rong theo nganh de "doc thi truong" (them watchlist cua user o runtime)
SECTORS = {
    "Ngân hàng":   ["ACB", "VCB", "BID", "CTG", "MBB", "VPB", "VIB", "MSB", "OCB", "HDB", "LPB", "STB"],
    "Chứng khoán": ["SSI", "VCI", "VND", "HCM", "VIX", "SHS", "MBS", "CTS", "FTS"],
    "Hàng không":  ["HVN", "VJC"],
    "Dầu khí":     ["GAS", "PLX", "BSR", "PVD", "PVS", "PVT"],
    "Bất động sản":["VIC", "VHM", "NVL", "CEO", "TCH", "DXG"],
    "Điện":        ["GEG", "PC1", "TV2"],
    "Đầu tư công": ["VCG", "HHV", "CTD", "CII"],
    "Bán lẻ":      ["MWG", "DGW", "PET", "VNM", "FRT", "PNJ"],
    "Công nghệ":   ["FPT", "VGI", "FOX"],
    "Vận tải":     ["VTP", "GMD", "VSC", "VOS"],
    "Khác":        ["GEE", "GEX", "MSR"],
}
SECTOR_OF = {s: sec for sec, syms in SECTORS.items() for s in syms}

MA_LONG, BASE_WIN, SLOPE_WIN = 150, 120, 20
STAGE_VI = {1: "Tích lũy", 2: "Đẩy giá", 3: "Phân phối", 4: "Đè giá", 0: "Chưa rõ"}
STAGE_FULL = {1: "Tích lũy (đáy — tay to gom)", 2: "Đẩy giá (markup — xu hướng tăng)",
              3: "Phân phối (đỉnh — tay to xả)", 4: "Đè giá (markdown — xu hướng giảm)", 0: "Chưa rõ"}


def log(*a):
    print("[market_read]", *a, flush=True)


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


def fetch(sym, days=900, is_index=False):
    from vnstock.api.quote import Quote
    start = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    df = Quote(symbol=sym, source="VCI").history(
        start=start, end=dt.date.today().isoformat(), interval="1D")
    df = df.rename(columns=str.lower)
    scale = 1.0 if is_index else 1000.0   # chi so tinh theo diem, khong x1000
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce") * scale
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
    else:
        df["volume"] = 0.0                # chi so co the khong co volume
    df["time"] = pd.to_datetime(df["time"])
    return df.dropna(subset=["close"]).sort_values("time").reset_index(drop=True)


def _smooth_stage(stage, persist=12):
    """Chi doi pha khi trang thai tho duy tri >= persist phien -> cau chuyen sach."""
    out, cur, run_val, run_len = [], int(stage[0]), int(stage[0]), 0
    for s in stage:
        s = int(s)
        run_len = run_len + 1 if s == run_val else 1
        run_val = s if run_len == 1 else run_val
        if run_len >= persist:
            cur = run_val
        out.append(cur)
    return out


def read_one(df):
    """Tra ve dict doc chien dich cho 1 ma (dung nen cuoi cung)."""
    if df is None or len(df) < MA_LONG + 40:
        return None
    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
    sma_long = c.rolling(MA_LONG).mean()
    slope = (sma_long / sma_long.shift(SLOPE_WIN) - 1.0)
    hh6 = h.rolling(BASE_WIN).max()
    ll6 = l.rolling(BASE_WIN).min()
    range_w = (hh6 - ll6) / ll6
    pos_in_range = (c - ll6) / (hh6 - ll6)
    dirn = np.sign(c.diff().fillna(0))
    obv = (dirn * v).cumsum()
    obv_norm = (obv - obv.shift(60)) / (v.rolling(60).mean() * 60 + 1e-9)
    vol_dry = v.rolling(20).mean() / (v.rolling(BASE_WIN).mean() + 1e-9)
    ma50 = c.rolling(50).mean()

    above = c > sma_long
    flat = slope.abs() < 0.02
    rising = slope >= 0.02
    falling = slope <= -0.02
    stage = np.where(above & rising, 2,
             np.where(~above & falling, 4,
              np.where(above & ~rising, 3,
               np.where(~above & ~falling, 1, 0))))
    stage_c = _smooth_stage(stage, persist=12)

    i = len(df) - 1
    st = int(stage_c[i])
    obv_n = float(obv_norm.iloc[i]) if np.isfinite(obv_norm.iloc[i]) else 0.0
    pir = float(pos_in_range.iloc[i]) if np.isfinite(pos_in_range.iloc[i]) else 0.5
    vd = float(vol_dry.iloc[i]) if np.isfinite(vol_dry.iloc[i]) else 1.0
    slp = float(slope.iloc[i]) if np.isfinite(slope.iloc[i]) else 0.0

    # tin hieu chien dich
    warm = i > MA_LONG + BASE_WIN
    vavg = v.rolling(50).mean().iloc[i]
    sig_markup = bool(warm and c.iloc[i] > hh6.iloc[i - 1] and v.iloc[i] > 1.5 * vavg
                      and above.iloc[i] and range_w.iloc[i - 1] < 0.80)
    sig_accum = bool(warm and st == 1 and obv_n > 0.15 and pir < 0.45 and vd < 0.9)

    # tuong thuat dien tien pha 12 thang (da lam muot)
    tail_n = 252
    seq = [int(x) for x in stage_c[max(0, i - tail_n):i + 1]]
    times = df["time"].iloc[max(0, i - tail_n):i + 1].tolist()
    trans, prev = [], None
    for k, s in enumerate(seq):
        if s != prev:
            trans.append(f"{STAGE_VI[s]} ({times[k].strftime('%m/%y')})")
            prev = s
    story = " → ".join(trans[-5:])

    obv_txt = "vào ròng (tích lũy)" if obv_n > 0.1 else ("ra ròng (phân phối)" if obv_n < -0.1 else "cân bằng")
    vol_txt = "khô hạn" if vd < 0.85 else ("sôi động" if vd > 1.2 else "bình thường")

    return {"stage": st, "obv_norm": round(obv_n, 2), "obv_txt": obv_txt,
            "pos": round(pir * 100), "vol_dry": round(vd, 2), "vol_txt": vol_txt,
            "slope": round(slp * 100, 1), "price": round(float(c.iloc[i])),
            "sig": "markup" if sig_markup else ("accum" if sig_accum else None),
            "story": story}


def load_watchlist():
    wl = os.path.join(HERE, "watchlist.txt")
    out = []
    if os.path.exists(wl):
        txt = open(wl, encoding="utf-8").read()
        for tok in txt.replace("\n", ",").split(","):
            t = tok.strip().upper()
            if t and not t.startswith("#") and t.isalpha():
                out.append(t)
    return out


def main():
    setup_vnstock_key()
    # co key tra phi (~60 req/phut) -> pace 1.1s; khong key (Guest 20 req/phut) -> 3.2s
    pace = 1.1 if os.environ.get("VNSTOCK_API_KEY") else 3.2
    log(f"vnstock tier: {'TRA PHI (pace 1.1s)' if pace < 2 else 'Guest (pace 3.2s)'}")
    watch = load_watchlist()
    universe = list(dict.fromkeys([s for syms in SECTORS.values() for s in syms] + watch))
    log(f"doc {len(universe)} ma ({len(watch)} trong watchlist)...")

    # regime VNINDEX > MA50 -- LAY DAU TIEN khi API con tuoi (goi sau 60+ fetch se bi throttle)
    regime = {"riskon": None, "vnindex": None, "ma50": None, "note": ""}
    for attempt in range(4):
        try:
            vc = fetch("VNINDEX", is_index=True)["close"]
            ma = vc.rolling(50).mean()
            riskon = bool(vc.iloc[-1] > ma.iloc[-1])
            norm = lambda x: x / 1000.0 if x > 100000 else x   # phong thu: chi so theo diem (~1862)
            regime = {"riskon": riskon, "vnindex": round(norm(float(vc.iloc[-1])), 1),
                      "ma50": round(norm(float(ma.iloc[-1])), 1),
                      "note": ("Thị trường chung RISK-ON (VNINDEX trên MA50) — ưu tiên mã đang/sắp đẩy giá."
                               if riskon else
                               "Thị trường chung RISK-OFF (VNINDEX dưới MA50) — thận trọng, ưu tiên phòng thủ.")}
            break
        except Exception as e:
            log(f"regime loi ({attempt+1}/4):", str(e)[:50])
            time.sleep(3)
    time.sleep(0.5)

    # vnstock goi Guest gioi han 20 request/PHUT -> phai gian cach >=3.2s/request,
    # neu khong bo gioi han cua vnstock se chan (co the SystemExit giua chung).
    reads = {}
    for i, s in enumerate(universe, 1):
        for attempt in range(3):
            try:
                r = read_one(fetch(s))
                if r:
                    reads[s] = r
                break
            except KeyboardInterrupt:
                raise
            except BaseException as e:   # bat ca SystemExit tu rate-limiter cua vnstock
                log(f"{s} loi ({attempt+1}/3): {str(e)[:50]}")
                time.sleep(8)
        if i % 10 == 0:
            log(f"  ... {i}/{len(universe)} ma, doc duoc {len(reads)}")
        time.sleep(pace)   # tra phi: 0.6s; Guest (khong key): 3.2s = 20 req/phut
    if not reads:
        log("Khong doc duoc ma nao. Thoat.")
        return

    # Bao ve du lieu: neu doc duoc < 70% ro (rate-limit/loi mang), GIU file cu, khong ghi de
    if len(reads) < 0.7 * len(universe) and os.path.exists(OUT):
        log(f"CHI doc duoc {len(reads)}/{len(universe)} ma (<70%) — giu nguyen file cu, khong ghi de/khong Discord.")
        return

    groups = {"markup": [], "accum": [], "distrib": [], "markdown": []}
    gkey = {2: "markup", 1: "accum", 3: "distrib", 4: "markdown"}
    for s, r in reads.items():
        g = gkey.get(r["stage"])
        if not g:
            continue
        groups[g].append({"sym": s, "sector": SECTOR_OF.get(s, "Khác"),
                          "watch": s in watch, "obv": r["obv_txt"], "pos": r["pos"],
                          "vol": r["vol_txt"], "slope": r["slope"], "sig": r["sig"]})
    for g in groups:
        groups[g].sort(key=lambda x: (not x["watch"], -x["slope"]))

    counts = {g: len(v) for g, v in groups.items()}

    # detail: ma co tin hieu (markup/accum) + ma dang day gia (uu tien watchlist)
    detail = []
    hot = [s for s, r in reads.items() if r["sig"]]
    inmk = [s for s, r in reads.items() if r["stage"] == 2 and not r["sig"]]
    inmk.sort(key=lambda s: (s not in watch, -reads[s]["slope"]))
    for s in hot + inmk[:8]:
        if any(d["sym"] == s for d in detail):
            continue
        r = reads[s]
        sig_txt = {"markup": "⚡ Vào markup (phá nền)", "accum": "⚡ Tích lũy (OBV vào ròng)"}.get(r["sig"], "")
        detail.append({"sym": s, "sector": SECTOR_OF.get(s, "Khác"), "watch": s in watch,
                       "stage_full": STAGE_FULL[r["stage"]], "sig_txt": sig_txt, "price": r["price"],
                       "obv": r["obv_txt"], "pos": r["pos"], "vol": r["vol_txt"], "slope": r["slope"],
                       "story": r["story"]})
        if len(detail) >= 14:
            break

    data = {
        "updated_at": dt.datetime.now(VN_TZ).isoformat(timespec="seconds"),
        "regime": regime, "counts": counts, "groups": groups, "detail": detail,
        "note": (f"Đọc chiến dịch tay to qua nhiều tháng (Stage/Wyckoff) trên {len(reads)} mã. "
                 f"Đẩy giá {counts['markup']} · Tích lũy {counts['accum']} · "
                 f"Phân phối {counts['distrib']} · Đè giá {counts['markdown']}."),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    log("da ghi", OUT, f"({os.path.getsize(OUT)} bytes)")
    log(f"Đẩy giá {counts['markup']} · Tích lũy {counts['accum']} · "
        f"Phân phối {counts['distrib']} · Đè giá {counts['markdown']}")

    if "--discord" in sys.argv:
        notify_transitions(reads, watch, regime)
    if "--push" in sys.argv:
        git_push()


def notify_transitions(reads, watch, regime):
    """Ban Discord: chuyen pha DANG CHU Y (moi vao markup / phan phoi / de gia). Dedup theo state."""
    webhook = resolve_market_webhook()
    if not webhook:
        log("khong co webhook market-read (env DISCORD_WEBHOOK_MARKETREAD hoac marketread_config.json) — bo qua Discord")
        return
    try:
        st = json.load(open(STATE, encoding="utf-8"))
    except Exception:
        st = {"prev": {}, "sent": []}
    prev = st.get("prev", {})
    sent = set(st.get("sent", []))
    today = dt.datetime.now(VN_TZ).strftime("%Y-%m-%d")

    up, warn = [], []
    for s, r in reads.items():
        now = r["stage"]
        old = prev.get(s)
        prev[s] = now
        if old is None or old == now:
            continue
        key = f"{today}|{s}|{now}"
        if key in sent:
            continue
        star = "⭐" if s in watch else ""
        line = f"**{s}**{star} {SECTOR_OF.get(s,'')}: {STAGE_VI[old]} → **{STAGE_VI[now]}**"
        if now == 2:               # vao day gia
            up.append((line + (" ⚡" if r["sig"] else ""), key))
        elif now in (3, 4):        # vao phan phoi / de gia
            warn.append((line, key))

    first_run = len(sent) == 0 and not any(k in st for k in ("prev_seeded",))
    force = "--test" in sys.argv
    reg = regime.get("note", "")

    # Run DAU TIEN (chua co baseline) hoac --test: gui ANH CHUP hien trang (de user thay hoat dong).
    if (first_run or force) and not up and not warn:
        cnt = {1: 0, 2: 0, 3: 0, 4: 0}
        for r in reads.values():
            cnt[r["stage"]] = cnt.get(r["stage"], 0) + 1
        def names(stage, n=10):
            xs = sorted([s for s, r in reads.items() if r["stage"] == stage],
                        key=lambda s: (s not in watch, -reads[s]["slope"]))
            return ", ".join((("⭐" + s) if s in watch else s) for s in xs[:n]) or "—"
        fields = [
            {"name": f"🟢 Đẩy giá — markup ({cnt[2]})", "value": names(2), "inline": False},
            {"name": f"🔵 Tích lũy — chờ ({cnt[1]})", "value": names(1), "inline": False},
            {"name": f"🟠 Phân phối — cảnh giác ({cnt[3]})", "value": names(3), "inline": False},
            {"name": f"🔴 Đè giá — tránh ({cnt[4]})", "value": names(4), "inline": False},
        ]
        embed = {"title": f"📖 Đọc thị trường {today} — bản đồ pha", "description": reg, "color": 0x4aa3ff,
                 "fields": fields, "footer": {"text": "FinPath · Đọc hiểu thị trường (Wyckoff/Stage khung tháng)"}}
        try:
            notify.send_discord(webhook, "", [embed], username="FinPath · Đọc thị trường")
            log("da ban Discord: anh chup hien trang (run dau/--test)")
        except Exception as e:
            log("discord loi:", str(e)[:80])
        st["prev_seeded"] = today
        json.dump({"prev": prev, "sent": list(sent)[-2000:], "prev_seeded": today},
                  open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
        return

    if not up and not warn:
        json.dump({"prev": prev, "sent": list(sent)[-2000:], "prev_seeded": today},
                  open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
        log("khong co chuyen pha dang chu y — khong ban Discord")
        return

    fields = []
    if up:
        fields.append({"name": "🟢 Vào ĐẨY GIÁ (cơ hội)", "value": "\n".join(x[0] for x in up[:12]), "inline": False})
    if warn:
        fields.append({"name": "🟠 Vào PHÂN PHỐI / ĐÈ GIÁ (cảnh giác)", "value": "\n".join(x[0] for x in warn[:12]), "inline": False})
    embed = {"title": f"📖 Đọc thị trường {today}", "description": reg, "color": 0x2bd576 if up else 0xe3b341,
             "fields": fields, "footer": {"text": "FinPath · Đọc hiểu thị trường (Stage/Wyckoff khung tháng)"}}
    try:
        notify.send_discord(webhook, "", [embed], username="FinPath · Đọc thị trường")
        for _, key in up + warn:
            sent.add(key)
        log(f"da ban Discord: {len(up)} vao markup, {len(warn)} canh giac")
    except Exception as e:
        log("discord loi:", str(e)[:80])

    json.dump({"prev": prev, "sent": list(sent)[-2000:], "prev_seeded": today},
              open(STATE, "w", encoding="utf-8"), ensure_ascii=False)


def resolve_market_webhook():
    url = (os.environ.get("DISCORD_WEBHOOK_MARKETREAD") or "").strip()
    if url.startswith("http"):
        return url
    if os.path.exists(CFG):
        try:
            url = (json.load(open(CFG, encoding="utf-8")).get("discord_webhook_url") or "").strip()
            if url.startswith("http"):
                return url
        except Exception:
            pass
    return ""


def git_push():
    import subprocess
    msg = "data: cap nhat doc hieu thi truong " + dt.datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M")
    try:
        subprocess.run(["git", "-C", ROOT, "add", "docs/data/market_read.json"], check=True)
        r = subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"])
        if r.returncode != 0:
            subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)
            subprocess.run(["git", "-C", ROOT, "push"], check=True)
            log("da push")
        else:
            log("khong co thay doi")
    except Exception as e:
        log("git push err:", e)


if __name__ == "__main__":
    main()
