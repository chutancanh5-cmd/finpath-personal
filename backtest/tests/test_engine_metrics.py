# -*- coding: utf-8 -*-
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.engine import simulate_always_dca, simulate_lump_sum, simulate_strategy
from backtest.metrics import summarize, xirr
from backtest.tests.helpers import make_df


class TestXirr(unittest.TestCase):
    def test_single_cashflow_pair_10pct(self):
        rate = xirr([(date(2020, 1, 1), -1000.0), (date(2021, 1, 1), 1100.0)])
        self.assertIsNotNone(rate)
        self.assertAlmostEqual(rate, 0.10, places=3)

    def test_none_when_no_sign_change(self):
        self.assertIsNone(xirr([(date(2020, 1, 1), -1000.0), (date(2021, 1, 1), -500.0)]))


class TestSimulateStrategy(unittest.TestCase):
    def setUp(self):
        closes = [100.0 + i for i in range(60)]
        self.df = make_df(closes)

    def test_contributed_matches_buy_count(self):
        result = simulate_strategy(self.df, ma_period=2, contribution=1_000_000,
                                    max_uptrend_months=26, rest_months=18)
        num_buys = sum(1 for t in result.trades if t.action == "BUY")
        self.assertEqual(result.total_contributed, num_buys * 1_000_000)

    def test_equity_continuous_across_sell(self):
        # Gia giam manh de kich hoat 1 lan SELL binh thuong, kiem tra equity lien tuc qua lan ban
        closes = [100.0 + i for i in range(15)] + [114.0 - i for i in range(1, 15)]
        df = make_df(closes)
        result = simulate_strategy(df, ma_period=3, contribution=1_000_000,
                                    max_uptrend_months=26, rest_months=18)
        sell_rows = [r for r in result.rows if r.action == "SELL"]
        self.assertTrue(sell_rows, "can co it nhat 1 lan SELL de kiem tra tinh lien tuc cua equity")
        idx = result.rows.index(sell_rows[0])
        equity_before = result.rows[idx - 1].equity if idx > 0 else 0.0
        equity_after = result.rows[idx].equity
        # equity khong duoc "boc hoi": ban sach chi chuyen nav -> tien mat, gia khong doi trong thang
        self.assertAlmostEqual(equity_before, equity_after, delta=max(1.0, abs(equity_before) * 0.05))

    def test_summarize_runs_without_error(self):
        result = simulate_strategy(self.df, ma_period=2, contribution=1_000_000,
                                    max_uptrend_months=26, rest_months=18)
        summary = summarize(result, months_total=len(self.df))
        self.assertIn("xirr_annual", summary)
        self.assertGreaterEqual(summary["num_buy"], 1)
        # gia tang don dieu suot -> chien luoc phai co lai
        self.assertGreater(summary["profit"], 0)


class TestBenchmarks(unittest.TestCase):
    def test_always_dca_invests_every_eligible_month(self):
        closes = [100.0 + i for i in range(30)]
        df = make_df(closes)
        result = simulate_always_dca(df, ma_period=2, contribution=1_000_000)
        expected_months = len(df) - 2  # tu index ma_period den het (ma_period-1=1 la first_valid)
        self.assertEqual(len(result.trades), expected_months)

    def test_lump_sum_single_entry(self):
        closes = [100.0 + i for i in range(30)]
        df = make_df(closes)
        result = simulate_lump_sum(df, ma_period=2, total_capital=10_000_000)
        self.assertEqual(len(result.trades), 1)
        self.assertAlmostEqual(result.total_contributed, 10_000_000)


if __name__ == "__main__":
    unittest.main()
