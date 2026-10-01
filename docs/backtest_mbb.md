# Backtest: MBB -- chien luoc 'Tich san trong Uptrend'

- Tai san: **MBB** (MBB), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2011-11-01** den **2026-10-01** (180 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 550,000,000 d | 850,000,000 d | 550,000,000 d |
| Gia tri cuoi ky | 713,071,690 d | 4,505,982,427 d | 7,074,013,158 d |
| Loi nhuan | 163,071,690 d | 3,655,982,427 d | 6,524,013,158 d |
| MOIC (x von) | 1.30x | 5.30x | 12.86x |
| XIRR (nam hoa) | 18.8% | 21.5% | 19.9% |
| Max drawdown | -6.7% | -40.5% | -48.4% |
| % thoi gian nam giu | 64.7% | 100.0% | 100.0% |
| So lenh MUA / BAN | 110 / 10 | 170 / 0 | 1 / 0 |
| So vong (round-trip) | 10 | 0 | 0 |
| Ty le vong thang | 50.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |
|---|---|---|---|---|
| 2023-07 | 2025-09 | 130,000,000 d | 245,446,441 d | 115,446,441 d |

## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2012-09 | 2012-10 | SELL | 5,000,000 d | 4,736,842 d | -263,158 d | -5.3% |
| 2 | 2013-02 | 2014-08 | SELL | 90,000,000 d | 94,350,148 d | 4,350,148 d | 4.8% |
| 3 | 2014-11 | 2014-12 | SELL | 5,000,000 d | 4,760,638 d | -239,362 d | -4.8% |
| 4 | 2015-01 | 2016-04 | SELL | 75,000,000 d | 77,733,144 d | 2,733,144 d | 3.6% |
| 5 | 2016-05 | 2016-12 | SELL | 35,000,000 d | 32,605,530 d | -2,394,470 d | -6.8% |
| 6 | 2017-03 | 2018-07 | SELL | 80,000,000 d | 94,618,209 d | 14,618,209 d | 18.3% |
| 7 | 2019-04 | 2019-06 | SELL | 10,000,000 d | 9,469,214 d | -530,786 d | -5.3% |
| 8 | 2019-08 | 2020-01 | SELL | 25,000,000 d | 23,825,689 d | -1,174,311 d | -4.7% |
| 9 | 2020-10 | 2022-05 | SELL | 95,000,000 d | 125,525,834 d | 30,525,834 d | 32.1% |
| 10 | 2023-07 | 2025-09 | FORCE_EXIT | 130,000,000 d | 245,446,441 d | 115,446,441 d | 88.8% |
