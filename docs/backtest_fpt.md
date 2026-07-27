# Backtest: FPT -- chien luoc 'Tich san trong Uptrend'

- Tai san: **FPT** (FPT), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2006-12-13** den **2026-07-01** (236 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 670,000,000 d | 1,130,000,000 d | 670,000,000 d |
| Gia tri cuoi ky | 789,072,907 d | 8,289,466,784 d | 4,022,586,873 d |
| Loi nhuan | 119,072,907 d | 7,159,466,784 d | 3,352,586,873 d |
| MOIC (x von) | 1.18x | 7.34x | 6.00x |
| XIRR (nam hoa) | 15.7% | 18.6% | 10.0% |
| Max drawdown | -8.1% | -51.5% | -81.5% |
| % thoi gian nam giu | 59.3% | 100.0% | 100.0% |
| So lenh MUA / BAN | 134 / 11 | 226 / 0 | 1 / 0 |
| So vong (round-trip) | 11 | 0 | 0 |
| Ty le vong thang | 45.5% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |
|---|---|---|---|---|
| 2015-05 | 2017-07 | 130,000,000 d | 173,510,000 d | 43,510,000 d |

## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2009-05 | 2011-01 | SELL | 100,000,000 d | 107,435,140 d | 7,435,140 d | 7.4% |
| 2 | 2012-03 | 2012-09 | SELL | 30,000,000 d | 27,427,684 d | -2,572,316 d | -8.6% |
| 3 | 2013-02 | 2013-03 | SELL | 5,000,000 d | 4,638,826 d | -361,174 d | -7.2% |
| 4 | 2013-06 | 2014-12 | SELL | 90,000,000 d | 104,967,446 d | 14,967,446 d | 16.6% |
| 5 | 2015-05 | 2017-07 | FORCE_EXIT | 130,000,000 d | 173,510,000 d | 43,510,000 d | 33.5% |
| 6 | 2019-03 | 2020-04 | SELL | 65,000,000 d | 54,374,320 d | -10,625,680 d | -16.3% |
| 7 | 2020-06 | 2020-07 | SELL | 5,000,000 d | 4,790,419 d | -209,581 d | -4.2% |
| 8 | 2020-09 | 2022-10 | SELL | 125,000,000 d | 165,411,375 d | 40,411,375 d | 32.3% |
| 9 | 2023-02 | 2023-03 | SELL | 5,000,000 d | 4,732,143 d | -267,857 d | -5.4% |
| 10 | 2023-06 | 2025-04 | SELL | 110,000,000 d | 137,424,905 d | 27,424,905 d | 24.9% |
| 11 | 2026-02 | 2026-03 | SELL | 5,000,000 d | 4,360,648 d | -639,352 d | -12.8% |
