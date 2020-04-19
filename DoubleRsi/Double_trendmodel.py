""""""

import numpy as np
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class DoubleTrendModelStrategy(CtaTemplate):
    """"""

    author = "yiran"

    fixed_size = 1
    s_window = 5
    l_window = 15

    fast_ma_macd = 9
    slow_ma_macd = 26
    signal_macd = 4
    true_range_window = 4
    true_range_influence_multiplier = 0.5

    cross_over_record_max_num_s = 50
    cross_over_slice_window_s = 4
    trail_bar_window_s = 6

    cross_over_record_max_num_l = 50
    cross_over_slice_window_l = 4
    trail_bar_window_l = 6

    bar_num_s = 0
    bar_num_after_crossover_s = 0

    bar_num_l = 0
    bar_num_after_crossover_l = 0

    mdif_s = 0
    cross_above_0_s = False
    cross_under_0_s = False
    cross_over_record_array_s = np.zeros(shape=(4, cross_over_record_max_num_s))
    cross_over_slice_window_highest_s = 0
    cross_over_slice_window_lowest_s = 0
    last_cross_over_interval_s = 0
    last_cross_over_side_s = 0

    mdif_l = 0
    cross_above_0_l = False
    cross_under_0_l = False
    cross_over_record_array_l = np.zeros(shape=(4, cross_over_record_max_num_l))
    cross_over_slice_window_highest_l = 0
    cross_over_slice_window_lowest_l = 0
    last_cross_over_interval_l = 0
    last_cross_over_side_l = 0

    long_open_stop_order_price_l = 0
    long_close_stop_order_price_l = 0
    short_open_stop_order_price_l = 0
    short_close_stop_order_price_l = 0

    long_open_stop_order_price_s = 0
    long_close_stop_order_price_s = 0
    short_open_stop_order_price_s = 0
    short_close_stop_order_price_s = 0

    parameters = [
        'fast_ma_macd',
        'slow_ma_macd',
        'signal_macd',
        'true_range_window',
        'cross_over_record_max_num_l',
        'cross_over_record_max_num_s',
        's_window','l_window',
        'true_range_influence_multiplier',
        'cross_over_slice_window_l', 'cross_over_slice_window_s',
        'trail_bar_window_l','trail_bar_window_s']

    variables = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bars = []
        self.bg5 = BarGenerator(self.on_bar, self.s_window, self.on_5min_bar)
        self.am5 = ArrayManager()

        self.bg15 = BarGenerator(self.on_bar, self.l_window, self.on_15min_bar)
        self.am15 = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg5.update_tick(tick)

    def on_bar(self, bar: BarData) :
        self.bg5.update_bar(bar)
        self.bg15.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        self.am5.update_bar(bar)
        self.bar_num_s += 1
        if not self.am5.inited:
            return

        am = self.am5
        self.mdif_s, signal, hist = am.macd(
            self.fast_ma_macd, self.slow_ma_macd, self.signal_macd, array=True)
        self.long_close_stop_order_price_s = am.low[-self.trail_bar_window_s:].min()
        self.short_close_stop_order_price_s = am.high[-self.trail_bar_window_s:].max()

        if self.mdif_s[-2] < 0 < self.mdif_s[-1]:
            self.cross_above_0_s = True
        elif self.mdif_s[-2] > 0 > self.mdif_s[-1]:
            self.cross_under_0_s = True

        if self.cross_under_0_s or self.cross_above_0_s:
            # bar_num
            self.cross_over_record_array_s[0, :-
                                         1] = self.cross_over_record_array_s[0, 1:]
            # high
            self.cross_over_record_array_s[1, :-
                                         1] = self.cross_over_record_array_s[1, 1:]
            # low
            self.cross_over_record_array_s[2, :-
                                         1] = self.cross_over_record_array_s[2, 1:]
            # cross_over_side
            self.cross_over_record_array_s[3, :-
                                         1] = self.cross_over_record_array_s[3, 1:]

            self.cross_over_record_array_s[0, -1] = self.bar_num_s
            self.cross_over_record_array_s[1, -1] = am.high[-1]
            self.cross_over_record_array_s[2, -1] = am.low[-1]
            if self.cross_above_0_s:
                side = 1
            elif self.cross_under_0_s:
                side = -1
            self.cross_over_record_array_s[3, -1] = side
            self.cross_above_0_s, self.cross_under_0_s = False, False

        self.cross_over_slice_window_highest_s = np.max(
            self.cross_over_record_array_s[1, -self.cross_over_slice_window_s:])
        self.cross_over_slice_window_lowest_s = np.min(
            self.cross_over_record_array_s[2, -self.cross_over_slice_window_s:])
        self.last_cross_over_interval_s = self.bar_num_s - \
            self.cross_over_record_array_s[0, -1]
        self.last_cross_over_side_s = self.cross_over_record_array_s[3, -1]
        true_range_influence = np.mean(am.trange(
            array=True)[-self.true_range_window:]) * self.true_range_influence_multiplier
        self.long_open_stop_order_price_s = self.cross_over_slice_window_highest_s + \
            true_range_influence
        self.short_open_stop_order_price_s = self.cross_over_slice_window_lowest_s + \
            true_range_influence

        cross_overl_l = self.last_cross_over_interval_l <= self.last_cross_over_interval_l
        if self.pos == 0 and cross_overl_l:
            if self.last_cross_over_interval_s <= self.cross_over_record_max_num_s:
                if self.last_cross_over_side_s == 1 and self.last_cross_over_side_l == 1:
                    self.buy(
                        self.long_open_stop_order_price_s,
                        self.fixed_size,
                        stop=True)
                if self.last_cross_over_side_s == -1 and self.last_cross_over_side_l == -1:
                    self.short(
                        self.short_close_stop_order_price_s,
                        self.fixed_size,
                        stop=True)
        elif self.pos > 0:
            self.sell(self.long_close_stop_order_price_s, self.pos, stop=True)
        elif self.pos < 0:
            self.cover(
                self.short_close_stop_order_price_s, np.abs(
                    self.pos), stop=True)

        self.put_event()

    def on_15min_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        self.am15.update_bar(bar)
        self.bar_num_l += 1
        if not self.am15.inited:
            return
        am = self.am15
        self.mdif_l, signal, hist = am.macd(
            self.fast_ma_macd, self.slow_ma_macd, self.signal_macd, array=True)
        self.long_close_stop_order_price_l = am.low[-self.trail_bar_window_l:].min()
        self.short_close_stop_order_price_l = am.high[-self.trail_bar_window_l:].max()

        if self.mdif_l[-2] < 0 < self.mdif_l[-1]:
            self.cross_above_0_l = True
        elif self.mdif_l[-2] > 0 > self.mdif_l[-1]:
            self.cross_under_0_l = True

        if self.cross_under_0_l or self.cross_above_0_l:
            # bar_num
            self.cross_over_record_array_l[0, :-
                                         1] = self.cross_over_record_array_l[0, 1:]
            # high
            self.cross_over_record_array_l[1, :-
                                         1] = self.cross_over_record_array_l[1, 1:]
            # low
            self.cross_over_record_array_l[2, :-
                                         1] = self.cross_over_record_array_l[2, 1:]
            # cross_over_side
            self.cross_over_record_array_l[3, :-
                                         1] = self.cross_over_record_array_l[3, 1:]

            self.cross_over_record_array_l[0, -1] = self.bar_num_l
            self.cross_over_record_array_l[1, -1] = am.high[-1]
            self.cross_over_record_array_l[2, -1] = am.low[-1]
            if self.cross_above_0_l:
                side = 1
            elif self.cross_under_0_l:
                side = -1
            self.cross_over_record_array_l[3, -1] = side
            self.cross_above_0_l, self.cross_under_0_l = False, False
            self.last_cross_over_interval_l = self.bar_num_l - \
                                              self.cross_over_record_array_l[0, -1]
            self.last_cross_over_side_l = self.cross_over_record_array_l[3, -1]

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
