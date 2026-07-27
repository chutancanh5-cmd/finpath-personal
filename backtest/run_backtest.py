# -*- coding: utf-8 -*-
"""
run_backtest.py -- Chay backtest chien luoc "Tich san trong Uptrend" (MA thang + timing 26/18 thang).

Usage:
    python run_backtest.py --asset vnindex
    python run_backtest.py --asset btc
    python run_backtest.py --asset gold
    python run_backtest.py --symbol FPT --source vci --ma 10 --contribution 3000000 --currency VND
    python run_backtest.py --asset vnindex --csv data_offline/vnindex_monthly.csv   # khong can mang

    them --push de commit + push ket qua vao docs/ (giong cac updater/*.py khac)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest import engine, metrics, report
from backtest.data_sources import PRESETS, fetch_monthly, load_csv_monthly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log(*a):
    print("[run_backtest]", *a, flush=True)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--asset", choices=sorted(PRESETS.keys()), default=None,
                   help="Bo tham so co san (vnindex/btc/gold). Bo qua neu dung --symbol tuy chinh.")
    p.add_argument("--symbol", default=None, help="Ma tai san tuy chinh (vd FPT, BTC, XAUUSD).")
    p.add_argument("--source", choices=["vci", "msn"], default=None, help="Nguon du lieu cho --symbol tuy chinh.")
    p.add_argument("--ma", type=int, default=None, help="Chu ky MA thang (mac dinh theo preset).")
    p.add_argument("--contribution", type=float, default=None, help="So tien dong gop moi thang.")
    p.add_argument("--currency", default=None, help="Don vi tien te hien thi (VND/USD...).")
    p.add_argument("--start", default=None, help="Ngay bat dau lay du lieu YYYY-MM-DD.")
    p.add_argument("--end", default=None, help="Ngay ket thuc lay du lieu YYYY-MM-DD.")
    p.add_argument("--max-uptrend-months", type=int, default=26, help="So thang uptrend toi da truoc khi force-exit.")
    p.add_argument("--rest-months", type=int, default=18, help="So thang nghi sau moi lan force-exit.")
    p.add_argument("--csv", default=None, help="Duong dan file CSV offline (time,open,high,low,close) thay vi goi mang.")
    p.add_argument("--out-dir", default=os.path.join(ROOT, "docs"), help="Thu muc ghi bao cao.")
    p.add_argument("--push", action="store_true", help="git add/commit/push ket qua sau khi chay.")
    return p


def resolve_config(args: argparse.Namespace) -> dict:
    if args.asset:
        cfg = dict(PRESETS[args.asset])
        cfg["key"] = args.asset
    elif args.symbol:
        cfg = {
            "key": args.symbol.lower(), "symbol": args.symbol.upper(),
            "source": args.source or "vci", "ma": 10, "label": args.symbol.upper(),
            "currency": "VND", "contribution": 1_000_000, "start": "2000-01-01",
        }
    else:
        raise SystemExit("Phai chi dinh --asset hoac --symbol.")

    if args.ma is not None:
        cfg["ma"] = args.ma
    if args.contribution is not None:
        cfg["contribution"] = args.contribution
    if args.currency is not None:
        cfg["currency"] = args.currency
    if args.start is not None:
        cfg["start"] = args.start
    cfg["end"] = args.end
    return cfg


def load_data(cfg: dict, csv_path: str):
    if csv_path:
        log(f"Nap du lieu offline tu {csv_path}")
        return load_csv_monthly(csv_path)
    log(f"Tai du lieu thang: symbol={cfg['symbol']} source={cfg['source']} "
        f"start={cfg['start']} end={cfg.get('end')}")
    try:
        return fetch_monthly(cfg["symbol"], cfg["source"], start=cfg["start"], end=cfg.get("end"))
    except Exception as e:
        raise RuntimeError(
            f"Khong lay duoc du lieu tu nguon '{cfg['source']}' cho '{cfg['symbol']}': {e}\n"
            "-> Neu moi truong nay khong co Internet ra ngoai (vd sandbox bi chan mang), "
            "hay chay lai o may/CI co mang, hoac dung --csv <file.csv> voi du lieu da co san."
        ) from e


def run(cfg: dict, df, max_uptrend_months: int, rest_months: int) -> dict:
    ma_period = int(cfg["ma"])
    contribution = float(cfg["contribution"])
    min_needed = ma_period + 1
    if len(df) < min_needed:
        raise RuntimeError(
            f"Khong du du lieu: co {len(df)} thang, can toi thieu {min_needed} thang (MA{ma_period} + 1)."
        )

    strat = engine.simulate_strategy(df, ma_period, contribution, max_uptrend_months, rest_months)
    dca = engine.simulate_always_dca(df, ma_period, contribution)
    lump = engine.simulate_lump_sum(df, ma_period, strat.total_contributed)

    summaries = {
        "strategy": metrics.summarize(strat, len(df)),
        "always_dca": metrics.summarize(dca, len(df)),
        "lump_sum": metrics.summarize(lump, len(df)),
    }
    meta = {
        "symbol": cfg["symbol"], "label": cfg["label"], "source": cfg["source"],
        "currency": cfg["currency"], "ma_period": ma_period, "contribution": contribution,
        "max_uptrend_months": max_uptrend_months, "rest_months": rest_months,
        "data_start": df.iloc[0]["time"].strftime("%Y-%m-%d"),
        "data_end": df.iloc[-1]["time"].strftime("%Y-%m-%d"),
        "months_total": len(df),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return {"meta": meta, "summaries": summaries}


def save_outputs(cfg: dict, result: dict, out_dir: str) -> tuple[str, str]:
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    json_path = os.path.join(data_dir, f"backtest_{cfg['key']}.json")
    md_path = os.path.join(out_dir, f"backtest_{cfg['key']}.md")

    payload = report.build_json(result["meta"], result["summaries"])
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    md = report.format_markdown(result["meta"], result["summaries"])
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    return json_path, md_path


def git_push(paths: list[str]):
    msg = "backtest: cap nhat ket qua " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        subprocess.run(["git", "-C", ROOT, "add", *paths], check=True)
        r = subprocess.run(["git", "-C", ROOT, "diff", "--cached", "--quiet"])
        if r.returncode != 0:
            subprocess.run(["git", "-C", ROOT, "commit", "-m", msg], check=True)
            subprocess.run(["git", "-C", ROOT, "push"], check=True)
            log("Da push len GitHub.")
        else:
            log("Khong co thay doi, bo qua push.")
    except Exception as e:
        log("git push loi:", e)


def main():
    args = build_arg_parser().parse_args()
    cfg = resolve_config(args)
    df = load_data(cfg, args.csv)
    result = run(cfg, df, args.max_uptrend_months, args.rest_months)

    md = report.format_markdown(result["meta"], result["summaries"])
    print(md)

    json_path, md_path = save_outputs(cfg, result, args.out_dir)
    log(f"Da ghi {json_path}")
    log(f"Da ghi {md_path}")

    if args.push:
        git_push([json_path, md_path])


if __name__ == "__main__":
    main()
