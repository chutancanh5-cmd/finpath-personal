# Backtest: VN-Index -- chien luoc 'Tich san trong Uptrend'

- Tai san: **VNINDEX** (VN-Index), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2018-07-30** den **2026-07-01** (97 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 300,000,000 d | 435,000,000 d | 300,000,000 d |
| Gia tri cuoi ky | 309,029,501 d | 617,210,331 d | 511,542,587 d |
| Loi nhuan | 9,029,501 d | 182,210,331 d | 211,542,587 d |
| MOIC (x von) | 1.03x | 1.42x | 1.71x |
| XIRR (nam hoa) | 5.7% | 9.7% | 7.7% |
| Max drawdown | -3.5% | -19.8% | -33.7% |
| % thoi gian nam giu | 69.0% | 100.0% | 100.0% |
| So lenh MUA / BAN | 60 / 5 | 87 / 0 | 1 / 0 |
| So vong (round-trip) | 5 | 0 | 0 |
| Ty le vong thang | 40.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

_Khong co lan nao du 26 thang uptrend lien tuc trong du lieu nay._


## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2019-05 | 2019-12 | SELL | 35,000,000 d | 34,673,501 d | -326,499 d | -0.9% |
| 2 | 2020-09 | 2022-05 | SELL | 100,000,000 d | 112,233,672 d | 12,233,672 d | 12.2% |
| 3 | 2023-07 | 2023-11 | SELL | 20,000,000 d | 17,385,282 d | -2,614,718 d | -13.1% |
| 4 | 2024-01 | 2024-12 | SELL | 55,000,000 d | 55,753,112 d | 753,112 d | 1.4% |
| 5 | 2025-01 | 2025-05 | SELL | 20,000,000 d | 19,182,045 d | -817,955 d | -4.1% |
