# Backtest: ACB -- chien luoc 'Tich san trong Uptrend'

- Tai san: **ACB** (ACB), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2006-11-21** den **2026-07-01** (237 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 630,000,000 d | 1,135,000,000 d | 630,000,000 d |
| Gia tri cuoi ky | 698,536,812 d | 6,549,566,635 d | 3,273,672,055 d |
| Loi nhuan | 68,536,812 d | 5,414,566,635 d | 2,643,672,055 d |
| MOIC (x von) | 1.11x | 5.77x | 5.20x |
| XIRR (nam hoa) | 10.9% | 16.4% | 9.1% |
| Max drawdown | -7.7% | -38.7% | -74.1% |
| % thoi gian nam giu | 55.5% | 100.0% | 100.0% |
| So lenh MUA / BAN | 126 / 15 | 227 / 0 | 1 / 0 |
| So vong (round-trip) | 15 | 0 | 0 |
| Ty le vong thang | 33.3% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2007-10 | 2008-02 | SELL | 20,000,000 d | 16,546,546 d | -3,453,454 d | -17.3% |
| 2 | 2009-04 | 2009-12 | SELL | 40,000,000 d | 37,124,249 d | -2,875,751 d | -7.2% |
| 3 | 2011-01 | 2011-02 | SELL | 5,000,000 d | 4,800,725 d | -199,275 d | -4.0% |
| 4 | 2012-01 | 2012-09 | SELL | 40,000,000 d | 33,285,460 d | -6,714,540 d | -16.8% |
| 5 | 2013-06 | 2013-09 | SELL | 15,000,000 d | 14,045,692 d | -954,308 d | -6.4% |
| 6 | 2014-02 | 2014-07 | SELL | 25,000,000 d | 24,437,607 d | -562,393 d | -2.2% |
| 7 | 2015-02 | 2016-02 | SELL | 60,000,000 d | 61,414,537 d | 1,414,537 d | 2.4% |
| 8 | 2016-11 | 2018-07 | SELL | 100,000,000 d | 141,406,873 d | 41,406,873 d | 41.4% |
| 9 | 2018-09 | 2018-10 | SELL | 5,000,000 d | 5,038,640 d | 38,640 d | 0.8% |
| 10 | 2019-10 | 2020-01 | SELL | 15,000,000 d | 14,623,401 d | -376,599 d | -2.5% |
| 11 | 2020-02 | 2020-04 | SELL | 10,000,000 d | 6,905,001 d | -3,094,999 d | -30.9% |
| 12 | 2020-06 | 2022-04 | SELL | 110,000,000 d | 153,003,043 d | 43,003,043 d | 39.1% |
| 13 | 2023-02 | 2023-11 | SELL | 45,000,000 d | 44,561,715 d | -438,285 d | -1.0% |
| 14 | 2023-12 | 2025-05 | SELL | 85,000,000 d | 86,903,519 d | 1,903,519 d | 2.2% |
| 15 | 2025-07 | 2026-04 | SELL | 45,000,000 d | 44,228,161 d | -771,839 d | -1.7% |
