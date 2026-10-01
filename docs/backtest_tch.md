# Backtest: TCH -- chien luoc 'Tich san trong Uptrend'

- Tai san: **TCH** (TCH), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2016-10-05** den **2026-10-01** (121 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 305,000,000 d | 555,000,000 d | 305,000,000 d |
| Gia tri cuoi ky | 283,558,444 d | 637,602,580 d | 478,016,644 d |
| Loi nhuan | -21,441,556 d | 82,602,580 d | 173,016,644 d |
| MOIC (x von) | 0.93x | 1.15x | 1.57x |
| XIRR (nam hoa) | -8.7% | 3.0% | 5.0% |
| Max drawdown | -23.3% | -61.3% | -74.4% |
| % thoi gian nam giu | 55.0% | 100.0% | 100.0% |
| So lenh MUA / BAN | 61 / 7 | 111 / 0 | 1 / 0 |
| So vong (round-trip) | 7 | 0 | 0 |
| Ty le vong thang | 14.3% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2017-12 | 2018-11 | SELL | 55,000,000 d | 49,584,067 d | -5,415,933 d | -9.8% |
| 2 | 2019-03 | 2019-05 | SELL | 10,000,000 d | 9,220,710 d | -779,290 d | -7.8% |
| 3 | 2019-08 | 2020-04 | SELL | 40,000,000 d | 24,513,003 d | -15,486,997 d | -38.7% |
| 4 | 2021-01 | 2021-08 | SELL | 35,000,000 d | 30,569,205 d | -4,430,795 d | -12.7% |
| 5 | 2021-12 | 2022-05 | SELL | 25,000,000 d | 18,182,304 d | -6,817,696 d | -27.3% |
| 6 | 2023-06 | 2024-11 | SELL | 85,000,000 d | 102,937,751 d | 17,937,751 d | 21.1% |
| 7 | 2025-03 | 2026-02 | SELL | 55,000,000 d | 48,551,404 d | -6,448,596 d | -11.7% |
