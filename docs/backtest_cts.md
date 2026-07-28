# Backtest: CTS -- chien luoc 'Tich san trong Uptrend'

- Tai san: **CTS** (CTS), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2009-07-31** den **2026-07-01** (205 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 485,000,000 d | 975,000,000 d | 485,000,000 d |
| Gia tri cuoi ky | 536,735,733 d | 6,575,666,143 d | 2,747,437,673 d |
| Loi nhuan | 51,735,733 d | 5,600,666,143 d | 2,262,437,673 d |
| MOIC (x von) | 1.11x | 6.74x | 5.66x |
| XIRR (nam hoa) | -99.8% | 21.0% | 11.3% |
| Max drawdown | -19.4% | -66.2% | -68.1% |
| % thoi gian nam giu | 49.7% | 100.0% | 100.0% |
| So lenh MUA / BAN | 97 / 16 | 195 / 0 | 1 / 0 |
| So vong (round-trip) | 16 | 0 | 0 |
| Ty le vong thang | 25.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2012-03 | 2012-09 | SELL | 30,000,000 d | 26,123,731 d | -3,876,269 d | -12.9% |
| 2 | 2013-02 | 2013-04 | SELL | 10,000,000 d | 9,028,866 d | -971,134 d | -9.7% |
| 3 | 2013-06 | 2013-08 | SELL | 10,000,000 d | 9,353,147 d | -646,853 d | -6.5% |
| 4 | 2013-12 | 2015-01 | SELL | 65,000,000 d | 65,778,459 d | 778,459 d | 1.2% |
| 5 | 2015-07 | 2015-09 | SELL | 10,000,000 d | 9,011,935 d | -988,065 d | -9.9% |
| 6 | 2016-12 | 2017-11 | SELL | 55,000,000 d | 61,222,971 d | 6,222,971 d | 11.3% |
| 7 | 2017-12 | 2018-07 | SELL | 35,000,000 d | 30,306,361 d | -4,693,639 d | -13.4% |
| 8 | 2018-10 | 2018-12 | SELL | 10,000,000 d | 8,378,618 d | -1,621,382 d | -16.2% |
| 9 | 2019-09 | 2019-11 | SELL | 10,000,000 d | 9,269,767 d | -730,233 d | -7.3% |
| 10 | 2020-07 | 2020-08 | SELL | 5,000,000 d | 4,359,431 d | -640,569 d | -12.8% |
| 11 | 2020-09 | 2022-05 | SELL | 100,000,000 d | 167,485,540 d | 67,485,540 d | 67.5% |
| 12 | 2023-02 | 2023-03 | SELL | 5,000,000 d | 4,013,080 d | -986,920 d | -19.7% |
| 13 | 2023-04 | 2023-11 | SELL | 35,000,000 d | 32,181,509 d | -2,818,491 d | -8.1% |
| 14 | 2023-12 | 2024-12 | SELL | 60,000,000 d | 60,624,275 d | 624,275 d | 1.0% |
| 15 | 2025-03 | 2025-05 | SELL | 10,000,000 d | 8,408,115 d | -1,591,885 d | -15.9% |
| 16 | 2025-07 | 2026-01 | SELL | 30,000,000 d | 27,287,257 d | -2,712,743 d | -9.0% |
