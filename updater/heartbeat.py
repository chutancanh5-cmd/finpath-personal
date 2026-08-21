# -*- coding: utf-8 -*-
"""
heartbeat.py -- danh dau "PC vua chay xong" de cloud biet ma bo qua.

Ghi docs/data/pc_heartbeat.json: {"daily": "<iso>", "intraday": "<iso>"}
Chi cap nhat dung khoa duoc truyen vao, giu nguyen khoa con lai.

Dung chung khuon dang thoi gian voi truong updated_at cua moi updater
(VN_TZ hardcode +07:00) nen ci_gate.py so sanh duoc du runner chay o UTC.

    python heartbeat.py daily
    python heartbeat.py intraday
"""
import os
import sys
import json
import datetime as dt
from datetime import timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "data", "pc_heartbeat.json")
VN_TZ = timezone(timedelta(hours=7))
KINDS = ("daily", "intraday")


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else ""
    if kind not in KINDS:
        print(f"[heartbeat] can tham so: {' | '.join(KINDS)}")
        return 2

    state = {}
    if os.path.exists(OUT):
        try:
            state = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            state = {}
    if not isinstance(state, dict):
        state = {}

    state[kind] = dt.datetime.now(VN_TZ).isoformat(timespec="seconds")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[heartbeat] {kind} = {state[kind]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
