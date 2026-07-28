# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest import run_batch
from backtest.report import format_batch_summary


class TestWatchlistParsing(unittest.TestCase):
    def test_reads_real_watchlist_file(self):
        syms = run_batch.read_watchlist()
        self.assertIn("FPT", syms)
        self.assertIn("VHM", syms)
        self.assertTrue(all(s == s.upper() for s in syms))
        self.assertTrue(all(not s.startswith("#") for s in syms))


class TestBuildCfg(unittest.TestCase):
    def test_vnindex_gets_special_label(self):
        cfg = run_batch.build_cfg("VNINDEX", ma=10, contribution=5_000_000,
                                   currency="VND", start="2000-01-01")
        self.assertEqual(cfg["label"], "VN-Index")
        self.assertEqual(cfg["source"], "vci")
        self.assertEqual(cfg["ma"], 10)

    def test_stock_label_is_symbol_itself(self):
        cfg = run_batch.build_cfg("FPT", ma=10, contribution=5_000_000,
                                   currency="VND", start="2000-01-01")
        self.assertEqual(cfg["label"], "FPT")


class TestBatchSummary(unittest.TestCase):
    def test_sorts_by_xirr_desc_and_lists_errors_separately(self):
        rows = [
            {"symbol": "A", "months": 50, "data_start": "2020-01-01", "data_end": "2024-01-01",
             "principal": 1000.0, "final_wealth": 1100.0, "xirr": 0.05, "max_dd": -0.1,
             "moic": 1.1, "num_rounds": 2, "win_rate": 0.5},
            {"symbol": "B", "months": 50, "data_start": "2020-01-01", "data_end": "2024-01-01",
             "principal": 1000.0, "final_wealth": 1500.0, "xirr": 0.20, "max_dd": -0.05,
             "moic": 1.5, "num_rounds": 3, "win_rate": 0.66},
            {"symbol": "C", "error": "Khong du du lieu"},
        ]
        md = format_batch_summary(rows, currency="VND", ma_period=10, contribution=5_000_000)
        pos_b = md.index("**B**")
        pos_a = md.index("**A**")
        self.assertLess(pos_b, pos_a, "B (XIRR cao hon) phai xep truoc A")
        self.assertIn("**C**", md)
        self.assertIn("Khong du du lieu", md)


if __name__ == "__main__":
    unittest.main()
