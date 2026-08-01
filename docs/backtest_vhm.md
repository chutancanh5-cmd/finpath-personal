# Backtest: VHM -- chien luoc 'Tich san trong Uptrend'

- Tai san: **VHM** (VHM), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2011-11-10** den **2026-07-01** (168 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 430,000,000 d | 790,000,000 d | 430,000,000 d |
| Gia tri cuoi ky | 908,482,790 d | 3,164,763,868 d | 2,225,900,035 d |
| Loi nhuan | 478,482,790 d | 2,374,763,868 d | 1,795,900,035 d |
| MOIC (x von) | 2.11x | 4.01x | 5.18x |
| XIRR (nam hoa) | 194.8% | 18.4% | 12.6% |
| Max drawdown | -10.0% | -81.8% | -87.6% |
| % thoi gian nam giu | 54.4% | 100.0% | 100.0% |
| So lenh MUA / BAN | 86 / 8 | 158 / 0 | 1 / 0 |
| So vong (round-trip) | 8 | 0 | 0 |
| Ty le vong thang | 25.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |
|---|---|---|---|---|
| 2012-09 | 2014-11 | 130,000,000 d | 548,792,479 d | 418,792,479 d |

## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2012-09 | 2014-11 | FORCE_EXIT | 130,000,000 d | 548,792,479 d | 418,792,479 d | 322.1% |
| 2 | 2018-06 | 2019-07 | SELL | 65,000,000 d | 62,043,163 d | -2,956,837 d | -4.5% |
| 3 | 2019-08 | 2020-01 | SELL | 25,000,000 d | 23,630,265 d | -1,369,735 d | -5.5% |
| 4 | 2020-02 | 2020-03 | SELL | 5,000,000 d | 4,753,557 d | -246,443 d | -4.9% |
| 5 | 2020-09 | 2020-10 | SELL | 5,000,000 d | 4,872,210 d | -127,790 d | -2.6% |
| 6 | 2020-11 | 2022-02 | SELL | 75,000,000 d | 81,167,685 d | 6,167,685 d | 8.2% |
| 7 | 2023-06 | 2023-10 | SELL | 20,000,000 d | 16,104,617 d | -3,895,383 d | -19.5% |
| 8 | 2024-09 | 2025-01 | SELL | 20,000,000 d | 19,276,556 d | -723,444 d | -3.6% |
