# -*- coding: utf-8 -*-
"""
ci_gate.py -- cloud co nen chay khong? (PC la chinh, cloud la du phong)

VCI (trading.vietcap.com.vn) degrade nang voi IP datacenter cua GitHub Actions
nhung binh thuong voi IP nha -- do duoc: price_board(100 ma) mat 1.6s tren PC
va timeout 30s lien tuc tren runner. Nen PC chay chinh; cloud chi chay bu khi
PC im lang.

Doc docs/data/pc_heartbeat.json (do heartbeat.py ghi), so tuoi voi nguong.
Ghi should_run=true|false ra $GITHUB_OUTPUT.

FAIL-OPEN: thieu file / hong JSON / thieu khoa -> true. Tha chay trung (bao
Discord trung mot lan) con hon mat du lieu ca ngay.

    python3 ci_gate.py --kind daily --max-age-min 240
"""
import os
import sys
import json
import argparse
import datetime as dt
from datetime import timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HB = os.path.join(ROOT, "docs", "data", "pc_heartbeat.json")
VN_TZ = timezone(timedelta(hours=7))


def decide(kind, max_age_min=None, same_day=False):
    """Tra (should_run, ly_do).

    Hai che do, chon theo NHIP cua cong viec:
    - same_day (viec 1 lan/ngay, vd daily): so NGAY. Nguong thoi gian sai o day --
      no khong phan biet duoc "PC chua chay hom nay" voi "PC chay hom qua", nen sau
      vai tieng la cong lai mo ra suot dem.
    - max_age_min (viec lap lai, vd intraday 5 phut/lan): so TUOI.
    """
    if not os.path.exists(HB):
        return True, "chua co pc_heartbeat.json"
    try:
        state = json.load(open(HB, encoding="utf-8"))
        stamp = state[kind]
        last = dt.datetime.fromisoformat(stamp)
    except Exception as e:
        return True, f"khong doc duoc heartbeat ({type(e).__name__})"

    bay_gio = dt.datetime.now(VN_TZ)
    if same_day:
        hom_nay = bay_gio.date()
        if last.date() == hom_nay:
            return False, f"PC da chay phien hom nay luc {last:%H:%M} ({hom_nay})"
        return True, f"PC chua chay hom nay (lan cuoi {last:%Y-%m-%d %H:%M}) -- cloud chay bu"

    age = (bay_gio - last).total_seconds() / 60
    if age < 0:
        return True, f"heartbeat o tuong lai ({stamp}) -- dong ho lech?"
    if age < max_age_min:
        return False, f"PC vua chay {age:.0f} phut truoc (< {max_age_min}')"
    return True, f"PC im lang {age:.0f} phut (>= {max_age_min}') -- cloud chay bu"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=["daily", "intraday"])
    ap.add_argument("--max-age-min", type=float,
                    help="che do so TUOI -- dung cho viec lap lai (intraday)")
    ap.add_argument("--same-day", action="store_true",
                    help="che do so NGAY -- dung cho viec 1 lan/ngay (daily)")
    a = ap.parse_args()
    if not a.same_day and a.max_age_min is None:
        ap.error("can --same-day hoac --max-age-min")

    # CONG NGAY GIAO DICH — chan TRUOC khi hoi den nhip tim cua PC.
    # Cron cua ca daily lan intraday la "T2-T6", ma cron khong biet ngay le. Trong ky nghi
    # san dong cua, cac updater van chay tren du lieu cu roi ban Discord (doc thi truong /
    # lenh lon / canh bao) — bao cao trung y het phien cuoi truoc ky nghi. Lich nghi nam o
    # vn_trading_calendar.py + vn_holidays.json (ban song sinh voi vn-bots/bot/).
    # PHAM VI: chi cho viec theo phien. Tin tuc (finpath-tinai) van chay 24/7 — co y.
    # FAIL-OPEN neu khong import duoc, dung tinh than san co cua file nay: tha chay trung
    # con hon mat du lieu ca ngay. Nhung khi lich noi RO day la ngay nghi thi chan that.
    try:
        sys.path.insert(0, HERE)
        import vn_trading_calendar as CAL
        d = CAL.vn_now().date()
        if not CAL.is_trading_day(d):
            ly_do = CAL.holiday_name(d) or "cuoi tuan"
            print(f"[ci_gate] {a.kind}: {d} khong phai ngay giao dich ({ly_do}) "
                  f"-> should_run=false")
            out = os.getenv("GITHUB_OUTPUT")
            if out:
                with open(out, "a", encoding="utf-8") as f:
                    f.write("should_run=false\n")
            return 0
    except Exception as e:
        print(f"[ci_gate] CANH BAO: khong dung duoc lich nghi le ({type(e).__name__}: {e}) "
              f"-> bo qua cong ngay le, quyet dinh theo nhip tim nhu cu.")

    should_run, why = decide(a.kind, a.max_age_min, a.same_day)
    print(f"[ci_gate] {a.kind}: {why} -> should_run={str(should_run).lower()}")

    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"should_run={str(should_run).lower()}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
