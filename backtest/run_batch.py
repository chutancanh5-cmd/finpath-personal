# -*- coding: utf-8 -*-
"""
run_batch.py -- Backtest chien luoc "Tich san trong Uptrend" (MA thang + timing 26/18 thang)
tren nhieu ma CHUNG KHOAN CO SO VIET NAM cung luc: VN-Index + watchlist cua app
(updater/watchlist.txt), roi tong hop thanh 1 bang xep hang de so sanh nhanh.

Usage:
    python run_batch.py                          # VNINDEX + updater/watchlist.txt
    python run_batch.py --symbols FPT,HPG,VNINDEX
    python run_batch.py --push
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest import report
from backtest.run_backtest import ROOT, git_push, load_data, log, run, save_outputs

WATCHLIST_FILE = os.path.join(ROOT, "updater", "watchlist.txt")


def read_watchlist() -> list:
    if not os.path.exists(WATCHLIST_FILE):
        return []
    with open(WATCHLIST_FILE, encoding="utf-8") as f:
        raw = f.read()
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("#")]
    syms = [s.strip().upper() for s in ",".join(lines).replace(",", "\n").split("\n")]
    return [s for s in syms if s]


def build_cfg(symbol: str, ma: int, contribution: float, currency: str, start: str) -> dict:
    return {
        "key": symbol.lower(), "symbol": symbol, "source": "vci", "ma": ma,
        "label": "VN-Index" if symbol == "VNINDEX" else symbol,
        "currency": currency, "contribution": contribution,
        "start": start, "end": None,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--symbols", default=None,
                   help="Danh sach ma cach nhau boi dau phay (mac dinh: VNINDEX + updater/watchlist.txt).")
    p.add_argument("--ma", type=int, default=10, help="Chu ky MA thang, ap dung cho tat ca ma (mac dinh MA10).")
    p.add_argument("--contribution", type=float, default=5_000_000, help="Dong gop moi thang (VND).")
    p.add_argument("--currency", default="VND")
    p.add_argument("--start", default="2000-01-01")
    p.add_argument("--max-uptrend-months", type=int, default=26)
    p.add_argument("--rest-months", type=int, default=18)
    p.add_argument("--out-dir", default=os.path.join(ROOT, "docs"))
    p.add_argument("--push", action="store_true")
    return p


def main():
    args = build_arg_parser().parse_args()
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        watch = [s for s in read_watchlist() if s != "VNINDEX"]
        symbols = ["VNINDEX"] + watch

    rows = []
    written = []
    for sym in symbols:
        cfg = build_cfg(sym, args.ma, args.contribution, args.currency, args.start)
        log(f"=== {sym} ===")
        try:
            df = load_data(cfg, csv_path=None)
            result = run(cfg, df, args.max_uptrend_months, args.rest_months)
        except Exception as e:
            log(f"  bo qua {sym}: {e}")
            rows.append({"symbol": sym, "error": str(e)})
            continue

        json_path, md_path = save_outputs(cfg, result, args.out_dir)
        written += [json_path, md_path]
        strat = result["summaries"]["strategy"]
        rows.append({
            "symbol": sym,
            "months": result["meta"]["months_total"],
            "data_start": result["meta"]["data_start"],
            "data_end": result["meta"]["data_end"],
            "principal": strat["principal_contributed"],
            "final_wealth": strat["final_wealth"],
            "xirr": strat["xirr_annual"],
            "max_dd": strat["max_drawdown"],
            "moic": strat["moic"],
            "num_rounds": strat["num_rounds"],
            "win_rate": strat["win_rate"],
        })

    summary_md = report.format_batch_summary(rows, args.currency, args.ma, args.contribution)
    print(summary_md)

    summary_path = os.path.join(args.out_dir, "backtest_summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_md)
    log(f"Da ghi {summary_path}")
    written.append(summary_path)

    if args.push:
        git_push(written)


if __name__ == "__main__":
    main()
