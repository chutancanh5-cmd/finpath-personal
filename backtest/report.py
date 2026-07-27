# -*- coding: utf-8 -*-
"""report.py -- Dinh dang ket qua backtest thanh bao cao doc duoc + JSON de luu/commit."""
from __future__ import annotations

import json
from typing import Any, Dict

import pandas as pd


def _fmt_money(v: float, currency: str) -> str:
    if v is None:
        return "n/a"
    if currency == "VND":
        return f"{v:,.0f} d"
    return f"{v:,.2f} {currency}"


def _fmt_pct(v, digits: int = 1) -> str:
    if v is None:
        return "n/a"
    return f"{v * 100:.{digits}f}%"


def _clean_for_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_for_json(v) for v in obj]
    if isinstance(obj, pd.Timestamp):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, float):
        return round(obj, 6)
    return obj


def build_json(meta: Dict[str, Any], summaries: Dict[str, dict]) -> Dict[str, Any]:
    return _clean_for_json({"meta": meta, "results": summaries})


def format_markdown(meta: Dict[str, Any], summaries: Dict[str, dict]) -> str:
    cur = meta["currency"]
    lines = []
    lines.append(f"# Backtest: {meta['label']} -- chien luoc 'Tich san trong Uptrend'\n")
    lines.append(
        f"- Tai san: **{meta['symbol']}** ({meta['label']}), nguon du lieu: `{meta['source']}`\n"
        f"- Khung thoi gian: THANG (M1), tu **{meta['data_start']}** den **{meta['data_end']}** "
        f"({meta['months_total']} thang)\n"
        f"- Duong trung binh: **MA{meta['ma_period']}** tren gia dong cua thang\n"
        f"- Dong gop dinh ky: **{_fmt_money(meta['contribution'], cur)}** / thang khi co tin hieu MUA\n"
        f"- Quy tac timing: force-exit sau **{meta['max_uptrend_months']} thang** uptrend lien tuc, "
        f"nghi **{meta['rest_months']} thang** ({meta['rest_months']/12:.1f} nam) sau moi lan force-exit\n"
    )

    order = [("strategy", "Chien luoc Tich san Uptrend (MA + timing)"),
             ("always_dca", "Benchmark: DCA deu moi thang, khong bao gio ban"),
             ("lump_sum", "Benchmark: Dau tu 1 lan (lump-sum) cung tong von")]

    lines.append("| Chi so | " + " | ".join(name for _, name in order) + " |")
    lines.append("|---|" + "---|" * len(order))

    def row(title, fn):
        vals = [fn(summaries[key]) for key, _ in order]
        lines.append(f"| {title} | " + " | ".join(vals) + " |")

    row("Von da gop", lambda s: _fmt_money(s["principal_contributed"], cur))
    row("Gia tri cuoi ky", lambda s: _fmt_money(s["final_wealth"], cur))
    row("Loi nhuan", lambda s: _fmt_money(s["profit"], cur))
    row("MOIC (x von)", lambda s: f"{s['moic']:.2f}x" if s["moic"] else "n/a")
    row("XIRR (nam hoa)", lambda s: _fmt_pct(s["xirr_annual"]))
    row("Max drawdown", lambda s: _fmt_pct(s["max_drawdown"]))
    row("% thoi gian nam giu", lambda s: _fmt_pct(s["time_in_market_pct"]))
    row("So lenh MUA / BAN", lambda s: f"{s['num_buy']} / {s['num_sell']+s['num_force_exit']}")
    row("So vong (round-trip)", lambda s: str(s["num_rounds"]))
    row("Ty le vong thang", lambda s: _fmt_pct(s["win_rate"]) if s["win_rate"] is not None else "n/a")

    strat = summaries["strategy"]
    lines.append("\n## Chi tiet cac lan force-exit theo timing (26 thang)\n")
    fe_rounds = [rd for rd in strat["rounds"] if rd["exit_type"] == "FORCE_EXIT"]
    if not fe_rounds:
        lines.append("_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._\n")
    else:
        lines.append("| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |")
        lines.append("|---|---|---|---|---|")
        for rd in fe_rounds:
            lines.append(
                f"| {rd['entry']:%Y-%m} | {rd['exit']:%Y-%m} | "
                f"{_fmt_money(rd['invested'], cur)} | {_fmt_money(rd['proceeds'], cur)} | "
                f"{_fmt_money(rd['profit'], cur)} |"
            )

    lines.append("\n## Tat ca cac vong giao dich cua chien luoc\n")
    if strat["rounds"]:
        lines.append("| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for i, rd in enumerate(strat["rounds"], 1):
            pct = _fmt_pct(rd["return_pct"]) if rd["return_pct"] is not None else "n/a"
            lines.append(
                f"| {i} | {rd['entry']:%Y-%m} | {rd['exit']:%Y-%m} | {rd['exit_type']} | "
                f"{_fmt_money(rd['invested'], cur)} | {_fmt_money(rd['proceeds'], cur)} | "
                f"{_fmt_money(rd['profit'], cur)} | {pct} |"
            )
    else:
        lines.append("_Chua co vong nao dong (co the con dang giu vi the den cuoi du lieu)._\n")

    return "\n".join(lines) + "\n"
