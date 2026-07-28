# Backtest: VPB -- chien luoc 'Tich san trong Uptrend'

- Tai san: **VPB** (VPB), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2017-08-17** den **2026-07-01** (108 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 275,000,000 d | 490,000,000 d | 275,000,000 d |
| Gia tri cuoi ky | 287,844,599 d | 989,280,955 d | 767,006,803 d |
| Loi nhuan | 12,844,599 d | 499,280,955 d | 492,006,803 d |
| MOIC (x von) | 1.05x | 2.02x | 2.79x |
| XIRR (nam hoa) | 8.7% | 17.0% | 13.5% |
| Max drawdown | -29.6% | -35.3% | -40.9% |
| % thoi gian nam giu | 56.1% | 100.0% | 100.0% |
| So lenh MUA / BAN | 55 / 9 | 98 / 0 | 1 / 0 |
| So vong (round-trip) | 9 | 0 | 0 |
| Ty le vong thang | 11.1% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2019-09 | 2020-04 | SELL | 35,000,000 d | 27,489,004 d | -7,510,996 d | -21.5% |
| 2 | 2020-06 | 2020-07 | SELL | 5,000,000 d | 4,363,517 d | -636,483 d | -12.7% |
| 3 | 2020-09 | 2022-06 | SELL | 105,000,000 d | 131,960,680 d | 26,960,680 d | 25.7% |
| 4 | 2023-02 | 2023-03 | SELL | 5,000,000 d | 4,311,466 d | -688,534 d | -13.8% |
| 5 | 2023-04 | 2023-11 | SELL | 35,000,000 d | 33,919,372 d | -1,080,628 d | -3.1% |
| 6 | 2024-03 | 2024-05 | SELL | 10,000,000 d | 9,395,570 d | -604,430 d | -6.0% |
| 7 | 2024-07 | 2025-02 | SELL | 35,000,000 d | 34,022,380 d | -977,620 d | -2.8% |
| 8 | 2025-03 | 2025-04 | SELL | 5,000,000 d | 4,948,676 d | -51,324 d | -1.0% |
| 9 | 2025-08 | 2026-04 | SELL | 40,000,000 d | 37,433,934 d | -2,566,066 d | -6.4% |
