# Backtest: Vang the gioi (XAU/USD) -- chien luoc 'Tich san trong Uptrend'

- Tai san: **XAUUSD** (Vang the gioi (XAU/USD)), nguon du lieu: `msn`
- Khung thoi gian: THANG (M1), tu **2018-07-26** den **2026-07-01** (97 thang)
- Duong trung binh: **MA21** tren gia dong cua thang
- Dong gop dinh ky: **100.00 USD** / thang khi co tin hieu MUA
- Quy tac timing: force-exit sau **26 thang** uptrend lien tuc, nghi **18 thang** (1.5 nam) sau moi lan force-exit

| Chi so | Chien luoc Tich san Uptrend (MA + timing) | Benchmark: DCA deu moi thang, khong bao gio ban | Benchmark: Dau tu 1 lan (lump-sum) cung tong von |
|---|---|---|---|
| Von da gop | 5,800.00 USD | 7,600.00 USD | 5,800.00 USD |
| Gia tri cuoi ky | 7,813.12 USD | 13,988.03 USD | 13,990.23 USD |
| Loi nhuan | 2,013.12 USD | 6,388.03 USD | 8,190.23 USD |
| MOIC (x von) | 1.35x | 1.84x | 2.41x |
| XIRR (nam hoa) | 25.6% | 19.5% | 15.1% |
| Max drawdown | -0.4% | -22.1% | -24.1% |
| % thoi gian nam giu | 76.3% | 100.0% | 100.0% |
| So lenh MUA / BAN | 58 / 5 | 76 / 0 | 1 / 0 |
| So vong (round-trip) | 5 | 0 | 0 |
| Ty le vong thang | 60.0% | n/a | n/a |

## Chi tiet cac lan force-exit theo timing (26 thang)

| Vao lenh | Force-exit | Von gop | Thu ve | Loi/lo |
|---|---|---|---|---|
| 2023-11 | 2026-01 | 2,600.00 USD | 4,631.27 USD | 2,031.27 USD |

## Tat ca cac vong giao dich cua chien luoc

| # | Vao | Ra | Kieu thoat | Von gop | Thu ve | Loi/lo | %  |
|---|---|---|---|---|---|---|---|
| 1 | 2020-04 | 2021-10 | SELL | 1,800.00 USD | 1,771.14 USD | -28.86 USD | -1.6% |
| 2 | 2022-01 | 2022-02 | SELL | 100.00 USD | 106.20 USD | 6.20 USD | 6.2% |
| 3 | 2022-03 | 2022-07 | SELL | 400.00 USD | 377.99 USD | -22.01 USD | -5.5% |
| 4 | 2023-01 | 2023-10 | SELL | 900.00 USD | 926.52 USD | 26.52 USD | 2.9% |
| 5 | 2023-11 | 2026-01 | FORCE_EXIT | 2,600.00 USD | 4,631.27 USD | 2,031.27 USD | 78.1% |
