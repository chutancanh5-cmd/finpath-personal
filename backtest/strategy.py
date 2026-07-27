# -*- coding: utf-8 -*-
"""
strategy.py -- Logic "Tich san trong Uptrend" (khung thang M1).

Quy tac (theo mo ta cua nha dau tu):
  - MUA: nen thang dong cua TREN MA(N) -> dau thang sau co "luong" thi mua tich san (DCA).
  - BAN: nen thang dong cua DUOI MA(N) -> ban sach ngay dau thang sau.
  - TIMING: neu da o trong uptrend (dang mua tich luy) du 26 thang lien tuc ma chua
    bi tin hieu MA cat xuong, van chu dong ban sach (force-exit). Sau do "nghi ngoi"
    (khong giao dich, khong xem tin hieu) it nhat 18 thang (1.5 nam) roi moi quay lai
    danh gia tin hieu MUA/BAN nhu binh thuong.

Thiet ke la mot state machine chay tung thang, khong nhin truoc du lieu (no lookahead):
tin hieu duoc tinh tren nen thang i-1 (da dong cua), hanh dong (mua/ban) duoc thuc hien
ngay dau thang i (gia mo cua thang i, dung "co luong dau thang la mua").
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import pandas as pd

DEFAULT_MAX_UPTREND_MONTHS = 26
DEFAULT_REST_MONTHS = 18  # 1.5 nam


class State(str, Enum):
    FLAT = "FLAT"        # dang dung ngoai thi truong, cho tin hieu MUA
    IN = "IN"             # dang tich san trong uptrend
    RESTING = "RESTING"   # vua force-exit theo timing, dang nghi ngoi


class Action(str, Enum):
    NONE = "NONE"
    BUY = "BUY"
    SELL = "SELL"
    FORCE_EXIT = "FORCE_EXIT"


@dataclass
class MonthSignal:
    idx: int
    time: pd.Timestamp
    close: float
    ma: Optional[float]
    state_before: State
    state_after: State
    action: Action
    trend_months: int
    rest_left: int


def compute_ma(closes: pd.Series, period: int) -> pd.Series:
    return closes.rolling(window=period, min_periods=period).mean()


def generate_signals(
    df: pd.DataFrame,
    ma_period: int,
    max_uptrend_months: int = DEFAULT_MAX_UPTREND_MONTHS,
    rest_months: int = DEFAULT_REST_MONTHS,
) -> List[MonthSignal]:
    """
    df: DataFrame voi cot time,open,high,low,close (1 dong / thang, da sap xep tang dan).
    Tra ve danh sach MonthSignal, 1 phan tu / thang, tu thang co du MA tro di.
    """
    closes = df["close"].reset_index(drop=True)
    times = df["time"].reset_index(drop=True)
    ma = compute_ma(closes, ma_period)

    signals: List[MonthSignal] = []
    state = State.FLAT
    trend_months = 0
    rest_left = 0

    n = len(df)
    first_valid = ma_period - 1  # index dau tien co MA du du lieu
    if first_valid >= n - 1:
        return signals  # khong du du lieu de sinh bat ky tin hieu nao

    # i la "thang hanh dong"; tin hieu dua tren du lieu cua thang i-1
    for i in range(first_valid + 1, n):
        prev_close = closes[i - 1]
        prev_ma = ma[i - 1]
        state_before = state
        action = Action.NONE

        if state == State.RESTING:
            rest_left -= 1
            if rest_left <= 0:
                state = State.FLAT
        elif state == State.FLAT:
            if prev_close > prev_ma:
                state = State.IN
                trend_months = 1
                action = Action.BUY
        elif state == State.IN:
            if prev_close < prev_ma:
                state = State.FLAT
                trend_months = 0
                action = Action.SELL
            elif trend_months >= max_uptrend_months:
                state = State.RESTING
                rest_left = rest_months
                trend_months = 0
                action = Action.FORCE_EXIT
            else:
                trend_months += 1
                action = Action.BUY

        signals.append(MonthSignal(
            idx=i, time=times[i], close=closes[i], ma=ma[i - 1],
            state_before=state_before, state_after=state, action=action,
            trend_months=trend_months, rest_left=rest_left,
        ))

    return signals
