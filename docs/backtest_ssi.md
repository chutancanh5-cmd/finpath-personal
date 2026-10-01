# Backtest: SSI -- chien luoc 'Tich san trong Uptrend'

- Tai san: **SSI** (SSI), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2006-12-15** den **2026-10-01** (239 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 585,000,000 d | 1,145,000,000 d | 585,000,000 d |
| Gia tri cuoi ky | 643,509,893 d | 4,485,892,525 d | 1,305,398,671 d |
| Loi nhuan | 58,509,893 d | 3,340,892,525 d | 720,398,671 d |
| MOIC (x von) | 1.10x | 3.92x | 2.23x |
| XIRR (nam hoa) | 8.0% | 12.9% | 4.3% |
| Max drawdown | -22.5% | -67.2% | -86.9% |
| % thoi gian nam giu | 51.1% | 100.0% | 100.0% |
| So lenh MUA / BAN | 117 / 17 | 229 / 0 | 1 / 0 |
| So vong (round-trip) | 17 | 0 | 0 |
| Ty le vong thang | 23.5% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2007-10 | 2008-03 | SELL | 25,000,000 d | 13,080,679 d | -11,919,321 d | -47.7% |
| 2 | 2009-05 | 2010-06 | SELL | 65,000,000 d | 68,484,324 d | 3,484,324 d | 5.4% |
| 3 | 2012-03 | 2012-10 | SELL | 35,000,000 d | 28,539,539 d | -6,460,461 d | -18.5% |
| 4 | 2013-02 | 2013-09 | SELL | 35,000,000 d | 33,959,112 d | -1,040,888 d | -3.0% |
| 5 | 2013-12 | 2015-01 | SELL | 65,000,000 d | 72,852,066 d | 7,852,066 d | 12.1% |
| 6 | 2015-07 | 2016-02 | SELL | 35,000,000 d | 30,598,097 d | -4,401,903 d | -12.6% |
| 7 | 2016-08 | 2016-09 | SELL | 5,000,000 d | 4,678,988 d | -321,012 d | -6.4% |
| 8 | 2016-10 | 2016-12 | SELL | 10,000,000 d | 9,527,469 d | -472,531 d | -4.7% |
| 9 | 2017-03 | 2017-11 | SELL | 40,000,000 d | 38,604,690 d | -1,395,310 d | -3.5% |
| 10 | 2017-12 | 2018-07 | SELL | 35,000,000 d | 29,590,687 d | -5,409,313 d | -15.5% |
| 11 | 2018-10 | 2018-11 | SELL | 5,000,000 d | 4,424,020 d | -575,980 d | -11.5% |
| 12 | 2020-09 | 2022-04 | SELL | 95,000,000 d | 173,505,455 d | 78,505,455 d | 82.6% |
| 13 | 2023-02 | 2023-03 | SELL | 5,000,000 d | 4,217,805 d | -782,195 d | -15.6% |
| 14 | 2023-04 | 2024-08 | SELL | 80,000,000 d | 87,100,842 d | 7,100,842 d | 8.9% |
| 15 | 2024-10 | 2024-11 | SELL | 5,000,000 d | 4,733,400 d | -266,600 d | -5.3% |
| 16 | 2025-03 | 2025-04 | SELL | 5,000,000 d | 4,981,253 d | -18,747 d | -0.4% |
| 17 | 2025-08 | 2026-04 | SELL | 40,000,000 d | 34,631,466 d | -5,368,534 d | -13.4% |
