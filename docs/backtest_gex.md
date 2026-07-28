# Backtest: GEX -- chien luoc 'Tich san trong Uptrend'

- Tai san: **GEX** (GEX), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2015-10-26** den **2026-07-01** (130 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 355,000,000 d | 600,000,000 d | 355,000,000 d |
| Gia tri cuoi ky | 414,281,673 d | 1,193,201,247 d | 1,222,322,900 d |
| Loi nhuan | 59,281,673 d | 593,201,247 d | 867,322,900 d |
| MOIC (x von) | 1.17x | 1.99x | 3.44x |
| XIRR (nam hoa) | 28.8% | 13.4% | 13.3% |
| Max drawdown | -17.5% | -70.1% | -73.8% |
| % thoi gian nam giu | 59.2% | 100.0% | 100.0% |
| So lenh MUA / BAN | 71 / 7 | 120 / 0 | 1 / 0 |
| So vong (round-trip) | 7 | 0 | 0 |
| Ty le vong thang | 42.9% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2016-08 | 2016-09 | SELL | 5,000,000 d | 4,695,222 d | -304,778 d | -6.1% |
| 2 | 2017-04 | 2018-11 | SELL | 95,000,000 d | 119,112,685 d | 24,112,685 d | 25.4% |
| 3 | 2019-09 | 2019-12 | SELL | 15,000,000 d | 14,151,486 d | -848,514 d | -5.7% |
| 4 | 2020-08 | 2022-05 | SELL | 105,000,000 d | 145,377,140 d | 40,377,140 d | 38.5% |
| 5 | 2023-06 | 2024-05 | SELL | 55,000,000 d | 53,643,100 d | -1,356,900 d | -2.5% |
| 6 | 2024-06 | 2024-09 | SELL | 15,000,000 d | 13,862,551 d | -1,137,449 d | -7.6% |
| 7 | 2025-03 | 2026-02 | SELL | 55,000,000 d | 56,901,977 d | 1,901,977 d | 3.5% |
