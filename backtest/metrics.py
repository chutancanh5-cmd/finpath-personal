# -*- coding: utf-8 -*-
"""metrics.py -- Cac chi so danh gia hieu qua: XIRR, max drawdown, ty le thang, MOIC..."""
from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd

from .engine import SimResult


_XIRR_GRID = (
    -0.9999, -0.999, -0.99, -0.95, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2,
    -0.1, -0.05, 0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75, 1.0,
    1.5, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0, 35.0, 50.0, 80.0, 130.0, 250.0, 500.0,
)


def xirr(cashflows: List[Tuple[pd.Timestamp, float]], tol: float = 1e-9,
         max_iter: int = 200) -> Optional[float]:
    """Suat sinh loi noi bo hang nam tu chuoi dong tien khong deu (bisection, khong can scipy).

    Chuoi giao dich DCA nhieu vong (mua/ban xen ke lap lai) co the khien NPV(r) doi dau
    NHIEU LAN (khong don dieu) -- vi du kinh dien: cashflows [-1000, +2500, -1540] co NPV am
    ca o r=-0.9999 lan r=50 du van co nghiem thuc o giua (~10%-30%). Vi vay thay vi chi thu
    mo rong 1 khoang [lo, hi] duy nhat, quet qua 1 luoi r roi bisect trong doan dau tien doi dau.
    """
    cfs = [(pd.Timestamp(d), float(v)) for d, v in cashflows if v is not None]
    if len(cfs) < 2:
        return None
    if not any(v < 0 for _, v in cfs) or not any(v > 0 for _, v in cfs):
        return None  # can it nhat 1 dong vao + 1 dong ra de co nghiem
    t0 = min(d for d, _ in cfs)

    def npv(r: float) -> float:
        total = 0.0
        for d, v in cfs:
            years = (d - t0).days / 365.0
            total += v / ((1.0 + r) ** years)
        return total

    lo = hi = None
    prev_r, prev_f = _XIRR_GRID[0], npv(_XIRR_GRID[0])
    if prev_f == 0:
        return prev_r
    for r in _XIRR_GRID[1:]:
        f = npv(r)
        if f == 0:
            return r
        if (f > 0) != (prev_f > 0):
            lo, hi = prev_r, r
            break
        prev_r, prev_f = r, f
    if lo is None:
        return None  # khong tim thay doan doi dau nao tren luoi -- khong co nghiem thuc kha di

    f_lo, f_hi = npv(lo), npv(hi)
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        f_mid = npv(mid)
        if abs(f_mid) < tol:
            return mid
        if (f_mid > 0) == (f_lo > 0):
            lo, f_lo = mid, f_mid
        else:
            hi, f_hi = mid, f_mid
    return (lo + hi) / 2.0


def max_drawdown(equity: List[float]) -> float:
    """Tra ve so am (VD -0.35 = -35%) dua tren duong equity (da gom tien mat hien thuc)."""
    if not equity:
        return 0.0
    peak = equity[0]
    mdd = 0.0
    for v in equity:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (v - peak) / peak
            mdd = min(mdd, dd)
    return mdd


def trade_rounds(result: SimResult) -> List[dict]:
    """Gom cac lenh MUA lien tiep + 1 lenh BAN dong vong thanh 1 'vong' de tinh ty le thang."""
    rounds = []
    invested = 0.0
    entry_time = None
    for t in result.trades:
        if t.action == "BUY":
            if invested == 0.0:
                entry_time = t.time
            invested += -t.cash_flow
        elif t.action in ("SELL", "FORCE_EXIT"):
            proceeds = t.cash_flow
            rounds.append({
                "entry": entry_time, "exit": t.time, "exit_type": t.action,
                "invested": invested, "proceeds": proceeds,
                "profit": proceeds - invested,
                "return_pct": (proceeds / invested - 1.0) if invested > 0 else None,
            })
            invested = 0.0
            entry_time = None
    return rounds


def summarize(result: SimResult, months_total: int) -> dict:
    equity_series = [r.equity for r in result.rows]
    rounds = trade_rounds(result)

    cashflows: List[Tuple[pd.Timestamp, float]] = [(t.time, t.cash_flow) for t in result.trades]
    if result.units_held_end > 0 and result.rows:
        cashflows.append((result.rows[-1].time, result.final_nav))
    irr = xirr(cashflows)

    months_in_market = sum(1 for r in result.rows if r.units_held > 0)
    wins = [rd for rd in rounds if rd["profit"] > 0]
    losses = [rd for rd in rounds if rd["profit"] <= 0]

    principal = result.total_contributed
    final_wealth = (equity_series[-1] if equity_series else 0.0)
    return {
        "label": result.label,
        "months_simulated": len(result.rows),
        "months_total": months_total,
        "num_trades": len(result.trades),
        "num_buy": sum(1 for t in result.trades if t.action == "BUY"),
        "num_sell": sum(1 for t in result.trades if t.action == "SELL"),
        "num_force_exit": sum(1 for t in result.trades if t.action == "FORCE_EXIT"),
        "num_rounds": len(rounds),
        "win_rounds": len(wins),
        "loss_rounds": len(losses),
        "win_rate": (len(wins) / len(rounds)) if rounds else None,
        "principal_contributed": principal,
        "final_units_held": result.units_held_end,
        "final_position_value": result.final_nav,
        "final_wealth": final_wealth,
        "profit": final_wealth - principal,
        "moic": (final_wealth / principal) if principal > 0 else None,
        "xirr_annual": irr,
        "max_drawdown": max_drawdown(equity_series),
        "time_in_market_pct": (months_in_market / len(result.rows)) if result.rows else None,
        "rounds": rounds,
    }
