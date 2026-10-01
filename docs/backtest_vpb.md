# Backtest: VPB -- chien luoc 'Tich san trong Uptrend'

- Tai san: **VPB** (VPB), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2017-08-17** den **2026-10-01** (111 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 285,000,000 d | 505,000,000 d | 285,000,000 d |
| Gia tri cuoi ky | 298,202,038 d | 1,197,334,616 d | 948,642,857 d |
| Loi nhuan | 13,202,038 d | 692,334,616 d | 663,642,857 d |
| MOIC (x von) | 1.05x | 2.37x | 3.33x |
| XIRR (nam hoa) | 8.9% | 20.2% | 15.5% |
| Max drawdown | -29.7% | -35.4% | -41.0% |
| % thoi gian nam giu | 56.4% | 100.0% | 100.0% |
| So lenh MUA / BAN | 57 / 9 | 101 / 0 | 1 / 0 |
| So vong (round-trip) | 9 | 0 | 0 |
| Ty le vong thang | 11.1% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2019-09 | 2020-04 | SELL | 35,000,000 d | 27,446,547 d | -7,553,453 d | -21.6% |
| 2 | 2020-06 | 2020-07 | SELL | 5,000,000 d | 4,370,861 d | -629,139 d | -12.6% |
| 3 | 2020-09 | 2022-06 | SELL | 105,000,000 d | 131,990,220 d | 26,990,220 d | 25.7% |
| 4 | 2023-02 | 2023-03 | SELL | 5,000,000 d | 4,307,520 d | -692,480 d | -13.8% |
| 5 | 2023-04 | 2023-11 | SELL | 35,000,000 d | 33,929,461 d | -1,070,539 d | -3.1% |
| 6 | 2024-03 | 2024-05 | SELL | 10,000,000 d | 9,396,204 d | -603,796 d | -6.0% |
| 7 | 2024-07 | 2025-02 | SELL | 35,000,000 d | 34,035,187 d | -964,813 d | -2.8% |
| 8 | 2025-03 | 2025-04 | SELL | 5,000,000 d | 4,948,910 d | -51,090 d | -1.0% |
| 9 | 2025-08 | 2026-04 | SELL | 40,000,000 d | 37,439,708 d | -2,560,292 d | -6.4% |
