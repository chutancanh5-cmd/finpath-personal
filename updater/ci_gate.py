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


def decide(kind, max_age_min):
    """Tra (should_run, ly_do)."""
    if not os.path.exists(HB):
        return True, "chua co pc_heartbeat.json"
    try:
        state = json.load(open(HB, encoding="utf-8"))
        stamp = state[kind]
        last = dt.datetime.fromisoformat(stamp)
    except Exception as e:
        return True, f"khong doc duoc heartbeat ({type(e).__name__})"

    age = (dt.datetime.now(VN_TZ) - last).total_seconds() / 60
    if age < 0:
        return True, f"heartbeat o tuong lai ({stamp}) -- dong ho lech?"
    if age < max_age_min:
        return False, f"PC vua chay {age:.0f} phut truoc (< {max_age_min}')"
    return True, f"PC im lang {age:.0f} phut (>= {max_age_min}') -- cloud chay bu"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=["daily", "intraday"])
    ap.add_argument("--max-age-min", type=float, required=True)
    a = ap.parse_args()

    should_run, why = decide(a.kind, a.max_age_min)
    print(f"[ci_gate] {a.kind}: {why} -> should_run={str(should_run).lower()}")

    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"should_run={str(should_run).lower()}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
