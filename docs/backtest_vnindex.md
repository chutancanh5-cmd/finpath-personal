# Backtest: VN-Index -- chien luoc 'Tich san trong Uptrend'

- Tai san: **VNINDEX** (VN-Index), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2004-01-05** den **2026-08-03** (272 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 780,000,000 d | 1,310,000,000 d | 780,000,000 d |
| Gia tri cuoi ky | 1,053,533,166 d | 3,881,271,760 d | 6,144,617,105 d |
| Loi nhuan | 273,533,166 d | 2,571,271,760 d | 5,364,617,105 d |
| MOIC (x von) | 1.35x | 2.96x | 7.88x |
| XIRR (nam hoa) | 119.3% | 9.0% | 9.9% |
| Max drawdown | -20.5% | -68.6% | -78.4% |
| % thoi gian nam giu | 59.5% | 100.0% | 100.0% |
| So lenh MUA / BAN | 156 / 18 | 262 / 0 | 1 / 0 |
| So vong (round-trip) | 18 | 0 | 0 |
| Ty le vong thang | 33.3% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |
|---|---|---|---|---|
| 2005-04 | 2007-06 | 130,000,000 d | 355,441,580 d | 225,441,580 d |

## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2005-04 | 2007-06 | FORCE_EXIT | 130,000,000 d | 355,441,580 d | 225,441,580 d | 173.4% |
| 2 | 2009-06 | 2010-02 | SELL | 40,000,000 d | 38,791,992 d | -1,208,008 d | -3.0% |
| 3 | 2010-05 | 2010-06 | SELL | 5,000,000 d | 4,639,118 d | -360,882 d | -7.2% |
| 4 | 2011-02 | 2011-03 | SELL | 5,000,000 d | 4,442,505 d | -557,495 d | -11.1% |
| 5 | 2011-05 | 2011-06 | SELL | 5,000,000 d | 4,376,164 d | -623,836 d | -12.5% |
| 6 | 2012-03 | 2012-08 | SELL | 25,000,000 d | 23,592,738 d | -1,407,262 d | -5.6% |
| 7 | 2013-02 | 2014-12 | SELL | 110,000,000 d | 117,482,047 d | 7,482,047 d | 6.8% |
| 8 | 2015-03 | 2015-04 | SELL | 5,000,000 d | 4,653,992 d | -346,008 d | -6.9% |
| 9 | 2015-07 | 2015-09 | SELL | 10,000,000 d | 9,341,833 d | -658,167 d | -6.6% |
| 10 | 2015-11 | 2015-12 | SELL | 5,000,000 d | 4,715,921 d | -284,079 d | -5.7% |
| 11 | 2016-01 | 2016-02 | SELL | 5,000,000 d | 4,708,478 d | -291,522 d | -5.8% |
| 12 | 2016-05 | 2018-06 | SELL | 125,000,000 d | 159,182,419 d | 34,182,419 d | 27.3% |
| 13 | 2019-03 | 2019-12 | SELL | 45,000,000 d | 44,627,790 d | -372,210 d | -0.8% |
| 14 | 2020-09 | 2022-05 | SELL | 100,000,000 d | 112,233,672 d | 12,233,672 d | 12.2% |
| 15 | 2023-07 | 2023-11 | SELL | 20,000,000 d | 17,385,282 d | -2,614,718 d | -13.1% |
| 16 | 2024-01 | 2024-12 | SELL | 55,000,000 d | 55,753,112 d | 753,112 d | 1.4% |
| 17 | 2025-01 | 2025-05 | SELL | 20,000,000 d | 19,182,045 d | -817,955 d | -4.1% |
| 18 | 2025-06 | 2026-08 | SELL | 70,000,000 d | 72,982,475 d | 2,982,475 d | 4.3% |
