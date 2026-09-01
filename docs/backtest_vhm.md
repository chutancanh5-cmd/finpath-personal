# Backtest: VHM -- chien luoc 'Tich san trong Uptrend'

- Tai san: **VHM** (VHM), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2011-11-10** den **2026-08-03** (169 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 435,000,000 d | 795,000,000 d | 435,000,000 d |
| Gia tri cuoi ky | 911,519,164 d | 3,125,446,838 d | 2,220,629,371 d |
| Loi nhuan | 476,519,164 d | 2,330,446,838 d | 1,785,629,371 d |
| MOIC (x von) | 2.10x | 3.93x | 5.10x |
| XIRR (nam hoa) | 194.8% | 18.1% | 12.4% |
| Max drawdown | -10.0% | -81.8% | -87.6% |
| % thoi gian nam giu | 54.7% | 100.0% | 100.0% |
| So lenh MUA / BAN | 87 / 8 | 159 / 0 | 1 / 0 |
| So vong (round-trip) | 8 | 0 | 0 |
| Ty le vong thang | 25.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |
|---|---|---|---|---|
| 2012-09 | 2014-11 | 130,000,000 d | 549,027,535 d | 419,027,535 d |

## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2012-09 | 2014-11 | FORCE_EXIT | 130,000,000 d | 549,027,535 d | 419,027,535 d | 322.3% |
| 2 | 2018-06 | 2019-07 | SELL | 65,000,000 d | 62,044,110 d | -2,955,890 d | -4.5% |
| 3 | 2019-08 | 2020-01 | SELL | 25,000,000 d | 23,631,008 d | -1,368,992 d | -5.5% |
| 4 | 2020-02 | 2020-03 | SELL | 5,000,000 d | 4,752,710 d | -247,290 d | -4.9% |
| 5 | 2020-09 | 2020-10 | SELL | 5,000,000 d | 4,872,210 d | -127,790 d | -2.6% |
| 6 | 2020-11 | 2022-02 | SELL | 75,000,000 d | 81,157,145 d | 6,157,145 d | 8.2% |
| 7 | 2023-06 | 2023-10 | SELL | 20,000,000 d | 16,108,284 d | -3,891,716 d | -19.5% |
| 8 | 2024-09 | 2025-01 | SELL | 20,000,000 d | 19,275,425 d | -724,575 d | -3.6% |
