# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backtest.strategy import Action, State, generate_signals
from backtest.tests.helpers import make_df


class TestUptrendTimingRule(unittest.TestCase):
    """Gia tang don dieu -> luon > MA -> phai kich hoat dung quy tac force-exit 26/18 thang."""

    def setUp(self):
        # 70 thang, gia tang don dieu 1 don vi/thang -> voi MA2, close[i] luon > MA[i]
        # (du dai vua 1 chu ky force-exit + nghi + mua lai, chua toi chu ky force-exit thu 2)
        closes = [100.0 + i for i in range(70)]
        self.df = make_df(closes)
        self.signals = generate_signals(self.df, ma_period=2, max_uptrend_months=26, rest_months=18)

    def test_exactly_one_force_exit_after_26_buys(self):
        force_exits = [s for s in self.signals if s.action == Action.FORCE_EXIT]
        self.assertEqual(len(force_exits), 1)
        fe = force_exits[0]
        # so lenh BUY truoc force-exit phai dung 26
        buys_before = [s for s in self.signals if s.action == Action.BUY and s.idx < fe.idx]
        self.assertEqual(len(buys_before), 26)

    def test_rest_period_blocks_buys_for_18_months(self):
        fe_idx = next(s.idx for s in self.signals if s.action == Action.FORCE_EXIT)
        resting = [s for s in self.signals if fe_idx < s.idx <= fe_idx + 18]
        self.assertEqual(len(resting), 18)
        self.assertTrue(all(s.action == Action.NONE for s in resting))
        self.assertTrue(all(s.state_after == State.RESTING for s in resting[:-1]))
        # thang thu 18 sau force-exit: da chuyen ve FLAT, san sang danh gia lai
        self.assertEqual(resting[-1].state_after, State.FLAT)

    def test_buying_resumes_after_rest(self):
        fe_idx = next(s.idx for s in self.signals if s.action == Action.FORCE_EXIT)
        after_rest = [s for s in self.signals if s.idx > fe_idx + 18]
        self.assertTrue(after_rest, "can du du lieu sau giai doan nghi de kiem tra")
        self.assertEqual(after_rest[0].action, Action.BUY)

    def test_no_lookahead_state_progression(self):
        # trend_months phai tang dan 1..26 lien tuc trong giai doan IN truoc force-exit
        in_phase = [s for s in self.signals if s.state_after == State.IN]
        trend_seq = [s.trend_months for s in in_phase[:26]]
        self.assertEqual(trend_seq, list(range(1, 27)))


class TestNormalSellNoRest(unittest.TestCase):
    """Gia tang roi giam cat xuong MA -> phai SELL binh thuong, KHONG buoc vao trang thai nghi."""

    def setUp(self):
        rising = [100.0 + i for i in range(10)]   # thang 0..9: 100..109
        falling = [109.0 - i for i in range(1, 10)]  # thang 10..18: giam dan manh
        recover = [100.0 + i for i in range(10)]  # thang 19..28: tang tro lai
        self.df = make_df(rising + falling + recover)
        self.signals = generate_signals(self.df, ma_period=3, max_uptrend_months=26, rest_months=18)

    def test_sell_triggered_on_ma_cross_down(self):
        sells = [s for s in self.signals if s.action == Action.SELL]
        self.assertGreaterEqual(len(sells), 1)

    def test_no_force_exit_when_trend_under_26_months(self):
        force_exits = [s for s in self.signals if s.action == Action.FORCE_EXIT]
        self.assertEqual(len(force_exits), 0)

    def test_can_buy_again_soon_after_normal_sell(self):
        sell_idx = next(s.idx for s in self.signals if s.action == Action.SELL)
        later_buys = [s for s in self.signals if s.action == Action.BUY and s.idx > sell_idx]
        self.assertTrue(later_buys)
        # khong co quy tac nghi bat buoc sau SELL thuong -> khoang cach co the < rest_months
        gap = later_buys[0].idx - sell_idx
        self.assertLess(gap, 18)


if __name__ == "__main__":
    unittest.main()
