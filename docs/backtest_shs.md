# Backtest: SHS -- chien luoc 'Tich san trong Uptrend'

- Tai san: **SHS** (SHS), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2009-06-25** den **2026-08-03** (207 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 435,000,000 d | 985,000,000 d | 435,000,000 d |
| Gia tri cuoi ky | 680,536,024 d | 6,426,605,437 d | 1,642,874,109 d |
| Loi nhuan | 245,536,024 d | 5,441,605,437 d | 1,207,874,109 d |
| MOIC (x von) | 1.56x | 6.52x | 3.78x |
| XIRR (nam hoa) | 29.4% | 20.4% | 8.5% |
| Max drawdown | -16.2% | -72.9% | -85.4% |
| % thoi gian nam giu | 44.2% | 100.0% | 100.0% |
| So lenh MUA / BAN | 87 / 8 | 197 / 0 | 1 / 0 |
| So vong (round-trip) | 8 | 0 | 0 |
| Ty le vong thang | 50.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2010-05 | 2010-06 | SELL | 5,000,000 d | 4,365,427 d | -634,573 d | -12.7% |
| 2 | 2012-03 | 2012-10 | SELL | 35,000,000 d | 27,072,020 d | -7,927,980 d | -22.7% |
| 3 | 2013-02 | 2013-08 | SELL | 30,000,000 d | 24,934,985 d | -5,065,015 d | -16.9% |
| 4 | 2014-01 | 2015-02 | SELL | 65,000,000 d | 72,709,020 d | 7,709,020 d | 11.9% |
| 5 | 2017-03 | 2018-05 | SELL | 70,000,000 d | 104,390,886 d | 34,390,886 d | 49.1% |
| 6 | 2020-05 | 2022-04 | SELL | 115,000,000 d | 329,922,641 d | 214,922,641 d | 186.9% |
| 7 | 2023-05 | 2024-07 | SELL | 70,000,000 d | 73,634,372 d | 3,634,372 d | 5.2% |
| 8 | 2025-05 | 2026-02 | SELL | 45,000,000 d | 43,506,674 d | -1,493,326 d | -3.3% |
