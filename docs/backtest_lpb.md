# Backtest: LPB -- chien luoc 'Tich san trong Uptrend'

- Tai san: **LPB** (LPB), nguon du lieu: `vci`
- Khung thoi gian: THANG (M1), tu **2017-10-05** den **2026-07-01** (106 thang)
- Duong trung binh: **MA10** tren gia dong cua thang
- Dong gop dinh ky: **5,000,000 d** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 240,000,000 d | 480,000,000 d | 240,000,000 d |
| Gia tri cuoi ky | 532,968,622 d | 4,128,889,300 d | 4,050,000,000 d |
| Loi nhuan | 292,968,622 d | 3,648,889,300 d | 3,810,000,000 d |
| MOIC (x von) | 2.22x | 8.60x | 16.88x |
| XIRR (nam hoa) | 100.1% | 53.7% | 42.9% |
| Max drawdown | -13.1% | -43.5% | -51.4% |
| % thoi gian nam giu | 50.0% | 100.0% | 100.0% |
| So lenh MUA / BAN | 48 / 4 | 96 / 0 | 1 / 0 |
| So vong (round-trip) | 4 | 0 | 0 |
| Ty le vong thang | 50.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |
|---|---|---|---|---|
| 2023-01 | 2025-03 | 130,000,000 d | 325,982,811 d | 195,982,811 d |

## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2020-03 | 2020-04 | SELL | 5,000,000 d | 3,886,792 d | -1,113,208 d | -22.3% |
| 2 | 2020-05 | 2022-01 | SELL | 100,000,000 d | 198,656,941 d | 98,656,941 d | 98.7% |
| 3 | 2022-02 | 2022-03 | SELL | 5,000,000 d | 4,442,078 d | -557,922 d | -11.2% |
| 4 | 2023-01 | 2025-03 | FORCE_EXIT | 130,000,000 d | 325,982,811 d | 195,982,811 d | 150.8% |
