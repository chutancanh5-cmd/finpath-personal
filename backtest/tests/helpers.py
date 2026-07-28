# -*- coding: utf-8 -*-
"""Ham tien ich tao du lieu gia thang tong hop (khong can mang) de kiem thu."""
from __future__ import annotations

from typing import List

import pandas as pd


def make_df(closes: List[float], start="2000-01-01") -> pd.DataFrame:
    """Tao DataFrame OHLC thang tu 1 danh sach gia dong cua; open = close cua chinh thang do
    (don gian hoa cho kiem thu -- gia thuc thi lenh = gia dong cua thang hanh dong)."""
    times = pd.date_range(start=start, periods=len(closes), freq="MS")
    return pd.DataFrame({
        "time": times,
        "open": closes,
        "high": closes,
        "low": closes,
        "close": closes,
    })
