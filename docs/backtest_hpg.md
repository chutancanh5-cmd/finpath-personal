# Backtest: HPG -- chien luoc 'Tich san trong Uptrend'

- Tai san: **HPG** (HPG), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2007-11-15** den **2026-07-01** (225 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 625,000,000 d | 1,075,000,000 d | 625,000,000 d |
| Gia tri cuoi ky | 843,642,110 d | 8,604,161,982 d | 9,562,969,925 d |
| Loi nhuan | 218,642,110 d | 7,529,161,982 d | 8,937,969,925 d |
| MOIC (x von) | 1.35x | 8.00x | 15.30x |
| XIRR (nam hoa) | 29.7% | 20.4% | 16.5% |
| Max drawdown | -8.6% | -63.5% | -64.3% |
| % thoi gian nam giu | 58.1% | 100.0% | 100.0% |
| So lenh MUA / BAN | 125 / 15 | 215 / 0 | 1 / 0 |
| So vong (round-trip) | 15 | 0 | 0 |
| Ty le vong thang | 40.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |
|---|---|---|---|---|
| 2016-05 | 2018-07 | 130,000,000 d | 225,208,853 d | 95,208,853 d |

## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2008-09 | 2008-11 | SELL | 10,000,000 d | 5,107,551 d | -4,892,449 d | -48.9% |
| 2 | 2009-05 | 2010-03 | SELL | 50,000,000 d | 52,564,236 d | 2,564,236 d | 5.1% |
| 3 | 2010-05 | 2010-06 | SELL | 5,000,000 d | 4,267,516 d | -732,484 d | -14.6% |
| 4 | 2011-01 | 2011-03 | SELL | 10,000,000 d | 8,015,094 d | -1,984,906 d | -19.8% |
| 5 | 2012-04 | 2012-10 | SELL | 30,000,000 d | 25,500,825 d | -4,499,175 d | -15.0% |
| 6 | 2012-11 | 2012-12 | SELL | 5,000,000 d | 5,057,471 d | 57,471 d | 1.1% |
| 7 | 2013-01 | 2015-01 | SELL | 120,000,000 d | 199,240,238 d | 79,240,238 d | 66.0% |
| 8 | 2015-08 | 2016-01 | SELL | 25,000,000 d | 23,383,577 d | -1,616,423 d | -6.5% |
| 9 | 2016-05 | 2018-07 | FORCE_EXIT | 130,000,000 d | 225,208,853 d | 95,208,853 d | 73.2% |
| 10 | 2020-02 | 2020-03 | SELL | 5,000,000 d | 4,762,901 d | -237,099 d | -4.7% |
| 11 | 2020-06 | 2022-01 | SELL | 95,000,000 d | 154,252,587 d | 59,252,587 d | 62.4% |
| 12 | 2023-04 | 2023-11 | SELL | 35,000,000 d | 33,241,282 d | -1,758,718 d | -5.0% |
| 13 | 2023-12 | 2024-09 | SELL | 45,000,000 d | 42,588,158 d | -2,411,842 d | -5.4% |
| 14 | 2025-03 | 2025-04 | SELL | 5,000,000 d | 4,777,192 d | -222,808 d | -4.5% |
| 15 | 2025-07 | 2026-06 | SELL | 55,000,000 d | 55,674,629 d | 674,629 d | 1.2% |
