# -*- coding: utf-8 -*-
"""
universe.py -- Vu tru ma toan san (HOSE/HNX/UPCOM) + loc thanh khoan + snapshot
price_board dung chung cho scan_daily.py va scan_intraday.py.

vnstock price_board tra gia da la VND (khong x1000). Ngoai gio giao dich,
cac truong match__* = 0 -> loc thanh khoan se rong, ham tu fallback ve cache /
watchlist de cac scanner van chay.
"""
import os
import json
import time
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "universe_cache.json")
WATCHLIST = os.path.join(HERE, "watchlist.txt")
EXCHANGES = {"HOSE", "HSX", "HNX", "UPCOM"}   # vnstock dung "HSX" cho HOSE
CHUNK = 50


def _num(x):
    try:
        f = float(x)
        return f if f == f else None   # loai NaN
    except (TypeError, ValueError):
        return None


def _round(x):
    return round(x) if x else 0


def all_stock_symbols():
    """Tat ca ma co phieu tren HOSE/HNX/UPCOM -> list dict {sym, exch, name}."""
    from vnstock.api.listing import Listing
    df = Listing(source="VCI").symbols_by_exchange()
    out = []
    for _, r in df.iterrows():
        typ = str(r.get("type", "")).lower()
        exch = str(r.get("exchange", "")).upper()
        sym = str(r.get("symbol", "")).upper()
        if typ == "stock" and exch in EXCHANGES and len(sym) == 3:
            out.append({"sym": sym, "exch": "HOSE" if exch == "HSX" else exch,
                        "name": str(r.get("organ_name", ""))})
    return out


def _flat(row, cols):
    d = {}
    for c in cols:
        key = "__".join(str(x) for x in c) if isinstance(c, tuple) else str(c)
        d[key] = row[c]
    return d


def price_board_snapshot(symbols):
    """Snapshot price_board cho 1 danh sach ma -> {sym: {...}}. Chia lo, boc try.
    Gia tri VND. Tra ve cac truong dung chung cho ca 2 scanner."""
    from vnstock.api.trading import Trading
    T = Trading(source="VCI")
    out = {}
    for i in range(0, len(symbols), CHUNK):
        part = symbols[i:i + CHUNK]
        for attempt in range(2):
            try:
                pb = T.price_board(part)
                cols = list(pb.columns)
                for _, r in pb.iterrows():
                    d = _flat(r, cols)
                    sym = str(d.get("listing__symbol", "")).upper()
                    if not sym:
                        continue
                    out[sym] = {
                        "price": _num(d.get("match__match_price")) or _num(d.get("listing__ref_price")),
                        "ref": _num(d.get("listing__ref_price")) or _num(d.get("match__reference_price")),
                        "ceil": _num(d.get("listing__ceiling")),
                        "floor": _num(d.get("listing__floor")),
                        "high": _num(d.get("match__highest")),
                        "low": _num(d.get("match__lowest")),
                        "open": _num(d.get("match__open_price")),
                        "acc_vol": _num(d.get("match__accumulated_volume")) or 0,
                        "acc_val": _num(d.get("match__accumulated_value")) or 0,
                        "fbv": _num(d.get("match__foreign_buy_volume")) or 0,
                        "fsv": _num(d.get("match__foreign_sell_volume")) or 0,
                        "fbval": _num(d.get("match__foreign_buy_value")) or 0,
                        "fsval": _num(d.get("match__foreign_sell_value")) or 0,
                        "buy_ord": _num(d.get("match__total_buy_orders")) or 0,
                        "sell_ord": _num(d.get("match__total_sell_orders")) or 0,
                        "exch": str(d.get("listing__exchange", "")).upper(),
                        "name": str(d.get("listing__organ_name", "")),
                        "bid": [[_round(_num(d.get(f"bid_ask__bid_{l}_price"))),
                                 int(_num(d.get(f"bid_ask__bid_{l}_volume")) or 0)] for l in (1, 2, 3)],
                        "ask": [[_round(_num(d.get(f"bid_ask__ask_{l}_price"))),
                                 int(_num(d.get(f"bid_ask__ask_{l}_volume")) or 0)] for l in (1, 2, 3)],
                    }
                break
            except Exception as e:
                if attempt == 0:
                    time.sleep(1.5)
                else:
                    print("[universe] price_board lo loi:", str(e)[:80], flush=True)
        time.sleep(0.25)
    return out


def _read_watchlist():
    try:
        raw = open(WATCHLIST, encoding="utf-8").read()
        syms = [s.strip().upper() for s in raw.replace(",", "\n").split("\n")]
        return [s for s in syms if s and not s.startswith("#")]
    except Exception:
        return []


def load_cache():
    try:
        return json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        return {}


def liquid_universe(min_value_bn=2.0, max_n=500, refresh_days=7, log=print):
    """Danh sach ma thanh khoan tot toan san.
    - Uu tien snapshot price_board (gio/sau phien co accumulated_value).
    - Ngoai gio (acc_val toan 0) -> dung cache con han, hoac watchlist.
    Cache: updater/universe_cache.json.
    """
    cache = load_cache()
    today = dt.date.today().isoformat()
    if cache.get("date") and cache.get("symbols"):
        age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(cache["date"])).days
        if 0 <= age < refresh_days:
            log(f"[universe] dung cache ({len(cache['symbols'])} ma, {age} ngay tuoi)")
            return cache["symbols"]

    log("[universe] dung danh sach ma toan san...")
    try:
        syms = [x["sym"] for x in all_stock_symbols()]
    except Exception as e:
        log("[universe] khong lay duoc danh sach:", str(e)[:80])
        syms = []
    if not syms:
        return cache.get("symbols") or _read_watchlist()

    # probe nhanh: neu feed chua co thanh khoan (ngoai gio/chua mo) -> fallback ngay,
    # khoi quet vo ich ca nghin ma.
    probe_syms = (_read_watchlist() or syms)[:12]
    probe = price_board_snapshot(probe_syms)
    if not any((d.get("acc_val") or 0) > 0 for d in probe.values()):
        log("[universe] feed chua co thanh khoan (ngoai gio) -> fallback cache/watchlist")
        return cache.get("symbols") or _read_watchlist() or syms[:max_n]

    log(f"[universe] {len(syms)} ma -> snapshot loc thanh khoan...")
    snap = price_board_snapshot(syms)
    ranked = sorted(((s, d.get("acc_val") or 0) for s, d in snap.items()),
                    key=lambda kv: kv[1], reverse=True)
    liquid = [s for s, v in ranked if v >= min_value_bn * 1e9][:max_n]

    if not liquid:
        # ngoai gio giao dich: acc_val = 0 -> fallback
        log("[universe] thanh khoan toan 0 (ngoai gio) -> fallback cache/watchlist")
        return cache.get("symbols") or _read_watchlist() or syms[:max_n]

    json.dump({"date": today, "symbols": liquid}, open(CACHE, "w", encoding="utf-8"),
              ensure_ascii=False)
    log(f"[universe] {len(liquid)} ma thanh khoan >= {min_value_bn} ty (da cache)")
    return liquid
