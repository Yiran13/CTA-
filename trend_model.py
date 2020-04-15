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


class TrendModelStrategy(CtaTemplate):
    """"""

    author = "yiran"

    fixed_size = 1

    fast_ma_macd = 9
    slow_ma_macd = 26
    signal_macd = 4
    true_range_window = 4
    true_range_influence_multiplier = 0.5

    cross_over_record_max_num = 50
    cross_over_slice_window = 4
    trail_bar_window = 6

    bar_num = 0
    bar_num_after_crossover = 0

    mdif = 0
    cross_above_0 = False
    cross_under_0 = False
    cross_over_record_array = np.zeros(shape=(4, cross_over_record_max_num))
    cross_over_slice_window_highest = 0
    cross_over_slice_window_lowest = 0
    last_cross_over_interval = 0
    last_cross_over_side = 0

    long_open_stop_order_price = 0
    long_close_stop_order_price = 0
    short_open_stop_order_price = 0
    short_close_stop_order_price = 0

    parameters = [
        'fast_ma_macd',
        'slow_ma_macd',
        'signal_macd',
        'true_range_window',
        'cross_over_record_max_num',
        'true_range_influence_multiplier',
        'cross_over_slice_window',
        'trail_bar_window']

    variables = [
        'bar_num',
        'bar_num_after_crossover',
        'mdif',
        'cross_above_0',
        'cross_under_0'
        'cross_over_slice_window_highest',
        'cross_over_slice_window_lowest',
        'last_cross_over_interval',
        'long_open_stop_order_price',
        'lass_cross_over_side',
        'short_open_stop_order_price',
        'short_close_stop_order_price']

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.bars = []

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
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()
        self.am.update_bar(bar)
        self.bar_num += 1
        if not self.am.inited:
            return

        am = self.am
        self.mdif, signal, hist = am.macd(
            self.fast_ma_macd, self.slow_ma_macd, self.signal_macd, array=True)
        self.long_close_stop_order_price = am.low[-self.trail_bar_window:].min()
        self.short_close_stop_order_price = am.high[-self.trail_bar_window:].max()

        if self.mdif[-2] < 0 < self.mdif[-1]:
            self.cross_above_0 = True
        elif self.mdif[-2] > 0 > self.mdif[-1]:
            self.cross_under_0 = True

        if self.cross_under_0 or self.cross_above_0:
            # bar_num
            self.cross_over_record_array[0, :-
                                         1] = self.cross_over_record_array[0, 1:]
            # high
            self.cross_over_record_array[1, :-
                                         1] = self.cross_over_record_array[1, 1:]
            # low
            self.cross_over_record_array[2, :-
                                         1] = self.cross_over_record_array[2, 1:]
            # cross_over_side
            self.cross_over_record_array[3, :-
                                         1] = self.cross_over_record_array[3, 1:]

            self.cross_over_record_array[0, -1] = self.bar_num
            self.cross_over_record_array[1, -1] = am.high[-1]
            self.cross_over_record_array[2, -1] = am.low[-1]
            if self.cross_above_0:
                side = 1
            elif self.cross_under_0:
                side = -1
            self.cross_over_record_array[3, -1] = side
            self.cross_above_0, self.cross_under_0 = False, False

        self.cross_over_slice_window_highest = np.max(
            self.cross_over_record_array[1, -self.cross_over_slice_window:])
        self.cross_over_slice_window_lowest = np.min(
            self.cross_over_record_array[2, -self.cross_over_slice_window:])
        self.last_cross_over_interval = self.bar_num - \
            self.cross_over_record_array[0, -1]
        self.last_cross_over_side = self.cross_over_record_array[3, -1]
        true_range_influence = np.mean(am.trange(
            array=True)[-self.true_range_window:]) * self.true_range_influence_multiplier
        self.long_open_stop_order_price = self.cross_over_slice_window_highest + \
            true_range_influence
        self.short_open_stop_order_price = self.cross_over_slice_window_lowest + \
            true_range_influence

        if self.pos == 0:
            if self.last_cross_over_interval <= self.cross_over_record_max_num:
                if self.last_cross_over_side == 1:
                    self.buy(
                        self.long_open_stop_order_price,
                        self.fixed_size,
                        stop=True)
                if self.last_cross_over_side == -1:
                    self.short(
                        self.short_close_stop_order_price,
                        self.fixed_size,
                        stop=True)
        elif self.pos > 0:
            self.sell(self.long_close_stop_order_price, self.pos, stop=True)
        elif self.pos < 0:
            self.cover(
                self.short_close_stop_order_price, np.abs(
                    self.pos), stop=True)

        self.put_event()

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
