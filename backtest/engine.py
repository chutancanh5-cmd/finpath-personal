# -*- coding: utf-8 -*-
"""
engine.py -- Mo phong dong tien: chien luoc "Tich san Uptrend" + 2 benchmark doi chieu.

  - strategy   : DCA theo tin hieu MA thang + timing 26/18 thang (xem strategy.py)
  - always_dca : DCA moi thang, khong bao gio ban (mua deu, giu mai) -- cung mot khoan
                 dong gop C moi thang nhu chien luoc, de so sanh cong bang tren cung nhip von.
  - lump_sum   : dau tu 1 lan toan bo von da dong gop cua chien luoc, ngay thang dau tien
                 co tin hieu, giu den het du lieu.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from .strategy import Action, MonthSignal, State, generate_signals


@dataclass
class Trade:
    time: pd.Timestamp
    action: str
    price: float
    units: float
    cash_flow: float  # am = dong tien ra (mua), duong = dong tien vao (ban)


@dataclass
class MonthRow:
    time: pd.Timestamp
    close: float
    ma: Optional[float]
    state: str
    action: str
    units_held: float
    contributed_cum: float
    nav: float  # gia tri danh muc dang nam giu (units_held * close)
    equity: float  # tong tai san = tien mat da hien thuc tu cac lan ban + nav hien tai


@dataclass
class SimResult:
    label: str
    rows: List[MonthRow] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    total_contributed: float = 0.0
    units_held_end: float = 0.0
    final_nav: float = 0.0


def _exec_price(df: pd.DataFrame, i: int) -> float:
    row = df.iloc[i]
    o = row.get("open")
    if o is not None and o == o and o > 0:  # not NaN
        return float(o)
    return float(row["close"])


def simulate_strategy(df: pd.DataFrame, ma_period: int, contribution: float,
                       max_uptrend_months: int = 26, rest_months: int = 18) -> SimResult:
    signals = generate_signals(df, ma_period, max_uptrend_months, rest_months)
    result = SimResult(label="strategy")
    units_held = 0.0
    contributed_cum = 0.0
    realized_cash_cum = 0.0

    for sig in signals:
        price = _exec_price(df, sig.idx)
        if sig.action == Action.BUY:
            units = contribution / price
            units_held += units
            contributed_cum += contribution
            result.trades.append(Trade(sig.time, "BUY", price, units, -contribution))
        elif sig.action in (Action.SELL, Action.FORCE_EXIT):
            proceeds = units_held * price
            result.trades.append(Trade(sig.time, sig.action.value, price, units_held, proceeds))
            units_held = 0.0
            realized_cash_cum += proceeds

        nav = units_held * sig.close
        result.rows.append(MonthRow(
            time=sig.time, close=sig.close, ma=sig.ma, state=sig.state_after.value,
            action=sig.action.value, units_held=units_held,
            contributed_cum=contributed_cum, nav=nav, equity=realized_cash_cum + nav,
        ))

    result.total_contributed = contributed_cum
    result.units_held_end = units_held
    result.final_nav = units_held * float(df.iloc[-1]["close"]) if len(df) else 0.0
    return result


def simulate_always_dca(df: pd.DataFrame, ma_period: int, contribution: float) -> SimResult:
    """Mua deu moi thang tu khi co du MA, khong ban -- benchmark 'tich san mu quang'."""
    result = SimResult(label="always_dca")
    units_held = 0.0
    contributed_cum = 0.0
    first_valid = ma_period - 1
    n = len(df)
    for i in range(first_valid + 1, n):
        price = _exec_price(df, i)
        units = contribution / price
        units_held += units
        contributed_cum += contribution
        result.trades.append(Trade(df.iloc[i]["time"], "BUY", price, units, -contribution))
        nav = units_held * float(df.iloc[i]["close"])
        result.rows.append(MonthRow(
            time=df.iloc[i]["time"], close=float(df.iloc[i]["close"]), ma=None,
            state="IN", action="BUY", units_held=units_held,
            contributed_cum=contributed_cum, nav=nav, equity=nav,
        ))
    result.total_contributed = contributed_cum
    result.units_held_end = units_held
    result.final_nav = units_held * float(df.iloc[-1]["close"]) if n else 0.0
    return result


def simulate_lump_sum(df: pd.DataFrame, ma_period: int, total_capital: float) -> SimResult:
    """Dau tu 1 lan toan bo von (= tong von chien luoc da gop) tai thang dau tien co du MA."""
    result = SimResult(label="lump_sum")
    first_valid = ma_period - 1
    n = len(df)
    if first_valid + 1 >= n or total_capital <= 0:
        return result
    entry_i = first_valid + 1
    price = _exec_price(df, entry_i)
    units = total_capital / price
    result.trades.append(Trade(df.iloc[entry_i]["time"], "BUY", price, units, -total_capital))
    for i in range(entry_i, n):
        nav = units * float(df.iloc[i]["close"])
        result.rows.append(MonthRow(
            time=df.iloc[i]["time"], close=float(df.iloc[i]["close"]), ma=None,
            state="IN", action=("BUY" if i == entry_i else "NONE"), units_held=units,
            contributed_cum=total_capital, nav=nav, equity=nav,
        ))
    result.total_contributed = total_capital
    result.units_held_end = units
    result.final_nav = units * float(df.iloc[-1]["close"])
    return result
