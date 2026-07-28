# -*- coding: utf-8 -*-
"""
data_sources.py -- Nap du lieu gia THANG (monthly OHLC) cho backtest.

Nguon:
  - "vci": chung khoan / chi so VN (VD: VNINDEX) qua vnstock (mien phi, khong can API key)
  - "msn": tai san toan cau (BTC, XAUUSD, chi so the gioi...) qua vnstock (nguon MSN)
  - "csv": file offline co cot time,open,high,low,close (dung khi khong co mang)

Ca "vci" va "msn" deu di qua lop Quote hop nhat cua vnstock:
    from vnstock.api.quote import Quote
    Quote(source="VCI"|"MSN", symbol=...).history(start=, end=, interval="1M")
"""
from __future__ import annotations

import os
from typing import Optional

import pandas as pd

REQUIRED_COLS = ["time", "open", "high", "low", "close"]


def _clean_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Chuan hoa DataFrame OHLC ve dung 5 cot, thoi gian tz-naive, sap xep tang dan."""
    if df is None or len(df) == 0:
        raise ValueError("Du lieu tra ve rong.")
    df = df.rename(columns={c: str(c).lower() for c in df.columns})
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Thieu cot {missing} trong du lieu tra ve: {list(df.columns)}")
    df = df[REQUIRED_COLS].copy()
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce").dt.tz_localize(None)
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["time", "close"])
    df = df.sort_values("time").drop_duplicates(subset="time", keep="last")
    # Chi giu 1 dong / thang (phong khi nguon tra ve nham ban ngay le)
    df["_ym"] = df["time"].dt.to_period("M")
    df = df.groupby("_ym", as_index=False).agg(
        time=("time", "first"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
    )
    df = df.drop(columns=[c for c in df.columns if c == "_ym"], errors="ignore")
    return df.reset_index(drop=True)


def fetch_monthly(symbol: str, source: str, start: str = "2000-01-01",
                   end: Optional[str] = None) -> pd.DataFrame:
    """Lay du lieu gia thang tu vnstock (source = 'vci' hoac 'msn').

    Uu tien vnstock_data (ban tra phi, can VNSTOCK_API_KEY -- xem updater/update_prices.py
    de cung 1 pattern fallback), lui ve vnstock (mien phi) neu chua cai/chua co key. Ban tra
    phi cho lich su dai hon nhieu (VD VN-Index tu 2000) so voi ban mien phi (~8 nam gan nhat).

    Luon xin du lieu NGAY (interval='1D') roi tu resample ve thang trong _clean_monthly,
    thay vi nho provider resample ho -- endpoint crypto cua MSN (BTC, ban mien phi) da quan
    sat thay cat du lieu rat ngan (~12 thang) khi xin thang truc tiep qua interval='1M',
    trong khi xin ngay + tu resample thi lay duoc day du hon.
    """
    try:
        from vnstock_data.api.quote import Quote  # ban tra phi, neu da cai + co key
    except Exception:
        from vnstock.api.quote import Quote  # import tre de tranh loi khi chi dung --csv offline

    q = Quote(source=source.upper(), symbol=symbol)
    df = q.history(start=start, end=end, interval="1D", count_back=100000)
    return _clean_monthly(df)


def load_csv_monthly(path: str) -> pd.DataFrame:
    """Nap du lieu offline tu CSV (cot: time,open,high,low,close)."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    return _clean_monthly(df)


# Bo tham so mac dinh cho tung tai san, dung dung mo ta chien thuat:
#   VN-Index dung MA10; BTC/Vang dung MA13, MA21.
PRESETS = {
    "vnindex": {
        "source": "vci", "symbol": "VNINDEX", "ma": 10,
        "label": "VN-Index", "currency": "VND", "contribution": 5_000_000,
        "start": "2000-01-01",
    },
    "btc": {
        "source": "msn", "symbol": "BTC", "ma": 13,
        "label": "Bitcoin (BTC/USD)", "currency": "USD", "contribution": 100,
        "start": "2014-01-01",
    },
    "gold": {
        "source": "msn", "symbol": "XAUUSD", "ma": 21,
        "label": "Vang the gioi (XAU/USD)", "currency": "USD", "contribution": 100,
        "start": "2000-01-01",
    },
}
