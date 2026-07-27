# Backtest: FTS -- chien luoc 'Tich san trong Uptrend'

- Tai san: **FTS** (FTS), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2017-01-13** den **2026-07-01** (115 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 330,000,000 d | 525,000,000 d | 330,000,000 d |
| Gia tri cuoi ky | 537,206,142 d | 1,366,185,486 d | 2,429,670,330 d |
| Loi nhuan | 207,206,142 d | 841,185,486 d | 2,099,670,330 d |
| MOIC (x von) | 1.63x | 2.60x | 7.36x |
| XIRR (nam hoa) | 53.0% | 21.4% | 25.9% |
| Max drawdown | -23.6% | -65.5% | -68.2% |
| % thoi gian nam giu | 62.9% | 100.0% | 100.0% |
| So lenh MUA / BAN | 66 / 6 | 105 / 0 | 1 / 0 |
| So vong (round-trip) | 6 | 0 | 0 |
| Ty le vong thang | 50.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2018-01 | 2019-06 | SELL | 85,000,000 d | 90,762,822 d | 5,762,822 d | 6.8% |
| 2 | 2020-03 | 2020-04 | SELL | 5,000,000 d | 4,040,921 d | -959,079 d | -19.2% |
| 3 | 2020-06 | 2022-05 | SELL | 115,000,000 d | 289,644,857 d | 174,644,857 d | 151.9% |
| 4 | 2023-05 | 2025-02 | SELL | 105,000,000 d | 136,132,570 d | 31,132,570 d | 29.7% |
| 5 | 2025-03 | 2025-05 | SELL | 10,000,000 d | 7,737,807 d | -2,262,193 d | -22.6% |
| 6 | 2025-08 | 2025-10 | SELL | 10,000,000 d | 8,887,165 d | -1,112,835 d | -11.1% |
