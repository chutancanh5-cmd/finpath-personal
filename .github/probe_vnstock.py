# -*- coding: utf-8 -*-
"""Probe vnstock tu IP GitHub Actions (nuoc ngoai) -> co lay duoc du lieu VN khong?"""
import os, datetime as dt
os.environ.setdefault("ACCEPT_TC", "tôi đồng ý")

res = {}

# 1) Lich su ngay (Quote.history)
try:
    from vnstock.api.quote import Quote
    h = Quote(symbol="FPT", source="VCI").history(
        start=(dt.date.today() - dt.timedelta(days=30)).isoformat(),
        end=dt.date.today().isoformat(), interval="1D")
    res["1_history"] = f"OK {len(h)} phien, close cuoi {float(h['close'].iloc[-1])}"
except Exception as e:
    res["1_history"] = f"FAIL {repr(e)[:180]}"

# 2) Bang gia (Trading.price_board)
try:
    from vnstock.api.trading import Trading
    pb = Trading(source="VCI").price_board(["FPT", "SSI"])
    res["2_price_board"] = f"OK shape {pb.shape}"
except Exception as e:
    res["2_price_board"] = f"FAIL {repr(e)[:180]}"

# 3) Tick order flow (kbs intraday) - quan trong nhat cho tab Dong tien
try:
    from vnstock.api.quote import Quote
    t = Quote(symbol="FPT", source="kbs").intraday(page_size=200)
    res["3_kbs_tick"] = f"OK {0 if t is None else len(t)} ticks"
except Exception as e:
    res["3_kbs_tick"] = f"FAIL {repr(e)[:180]}"

print("==================== VNSTOCK PROBE (GitHub IP) ====================")
for k, v in res.items():
    print(f"{k}: {v}")
print("===================================================================")
fails = [k for k, v in res.items() if v.startswith("FAIL")]
print("KET LUAN:", "TAT CA OK -> dung GitHub Actions duoc" if not fails else f"CO LOI o: {fails}")
