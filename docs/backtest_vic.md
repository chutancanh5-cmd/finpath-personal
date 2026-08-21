# Backtest: VIC -- chien luoc 'Tich san trong Uptrend'

- Tai san: **VIC** (VIC), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2007-09-19** den **2026-08-03** (228 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 620,000,000 d | 1,090,000,000 d | 620,000,000 d |
| Gia tri cuoi ky | 948,374,780 d | 22,194,592,708 d | 46,900,369,004 d |
| Loi nhuan | 328,374,780 d | 21,104,592,708 d | 46,280,369,004 d |
| MOIC (x von) | 1.53x | 20.36x | 75.65x |
| XIRR (nam hoa) | 74.0% | 28.4% | 27.0% |
| Max drawdown | -15.1% | -63.7% | -65.3% |
| % thoi gian nam giu | 56.9% | 100.0% | 100.0% |
| So lenh MUA / BAN | 124 / 13 | 218 / 0 | 1 / 0 |
| So vong (round-trip) | 13 | 0 | 0 |
| Ty le vong thang | 23.1% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |
|---|---|---|---|---|
| 2009-07 | 2011-09 | 130,000,000 d | 272,707,892 d | 142,707,892 d |

## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2008-08 | 2008-10 | SELL | 10,000,000 d | 9,060,937 d | -939,063 d | -9.4% |
| 2 | 2009-07 | 2011-09 | FORCE_EXIT | 130,000,000 d | 272,707,892 d | 142,707,892 d | 109.8% |
| 3 | 2013-04 | 2013-07 | SELL | 15,000,000 d | 14,602,173 d | -397,827 d | -2.7% |
| 4 | 2013-08 | 2013-09 | SELL | 5,000,000 d | 5,000,000 d | 0 d | 0.0% |
| 5 | 2013-11 | 2014-05 | SELL | 30,000,000 d | 27,081,855 d | -2,918,145 d | -9.7% |
| 6 | 2014-08 | 2015-04 | SELL | 40,000,000 d | 38,034,109 d | -1,965,891 d | -4.9% |
| 7 | 2015-07 | 2017-04 | SELL | 105,000,000 d | 119,971,495 d | 14,971,495 d | 14.3% |
| 8 | 2017-07 | 2019-01 | SELL | 90,000,000 d | 137,710,484 d | 47,710,484 d | 53.0% |
| 9 | 2019-02 | 2019-12 | SELL | 50,000,000 d | 49,651,860 d | -348,140 d | -0.7% |
| 10 | 2020-11 | 2021-08 | SELL | 45,000,000 d | 43,329,915 d | -1,670,085 d | -3.7% |
| 11 | 2021-12 | 2022-01 | SELL | 5,000,000 d | 4,571,429 d | -428,571 d | -8.6% |
| 12 | 2023-09 | 2023-10 | SELL | 5,000,000 d | 3,760,000 d | -1,240,000 d | -24.8% |
| 13 | 2024-09 | 2024-10 | SELL | 5,000,000 d | 4,821,101 d | -178,899 d | -3.6% |
