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
from datetime import time
import numpy as np


class TrendModelDoubleRsi(CtaTemplate):
    """"""
    author = "yiran"

    s_window = 5
    l_window = 15

    rsi_window = 11
    long_threshold_l_window = 50
    long_threshold_s_window = 80
    fixed_size = 1

    fast_ma_macd = 9
    slow_ma_macd = 26
    signal_macd = 4
    true_range_window = 4
    true_range_influence_multiplier = 0.5

    cross_over_record_max_num = 50
    cross_over_slice_window = 4
    trail_bar_window = 6

    mdif = 0
    cross_above_0 = False
    cross_under_0 = False
    cross_over_record_array = np.zeros(shape=(4, cross_over_record_max_num))
    cross_over_slice_window_highest = 0
    cross_over_slice_window_lowest = 0
    last_cross_over_interval = 0
    last_cross_over_side = 0

    bar_num = 0
    bar_num_after_crossover = 0


    start_time = time(hour=10)
    exit_time = time(hour=14, minute=55)

    long_order_record = []
    short_order_record = []

    rsi_value_l_window = -9999
    rsi_value_s_window = -9999
    exit_return = 0.02
    exit_loss = 0.02

    long_entered = False
    short_entered = False
    intra_trade_high = 0
    intra_trade_low = 0
    trailing_percent = 0.8
    parameters = [
        's_window',
        'l_window',
        "rsi_window",
        "long_threshold_l_window",
        "long_threshold_s_window",
        'exit_return',
        'exit_loss',
        "fixed_size"]

    variables = ["rsi_value_l_window ", "rsi_value_s_window", "ma_trend"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.rsi_long_l = self.long_threshold_l_window
        self.rsi_long_s = self.long_threshold_s_window
        self.rsi_short_l = 100 - self.long_threshold_l_window
        self.rsi_short_s = 100 - self.long_threshold_s_window

        self.bg5 = BarGenerator(self.on_bar, self.s_window, self.on_5min_bar)
        self.am5 = ArrayManager()

        self.bg15 = BarGenerator(self.on_bar, self.l_window, self.on_15min_bar)
        self.am15 = ArrayManager()
        self.long_order_record = []
        self.short_order_record = []

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

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg5.update_bar(bar)
        self.bg15.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        self.am5.update_bar(bar)
        if not self.am5.inited:
            return

        self.rsi_value_s_window = self.am5.rsi(self.rsi_window)

        if self.long_threshold_l_window != -9999:
            self.long_entered = (
                self.rsi_value_s_window > self.rsi_long_s) and (
                self.rsi_value_l_window > self.rsi_long_l)
            self.short_entered = (
                self.rsi_value_s_window < self.rsi_short_s) and (
                self.rsi_value_l_window < self.rsi_short_l)
        else:
            return

        if self.start_time <= bar.datetime.time() < self.exit_time:
            time_constraint = self.last_cross_over_interval <= self.cross_over_record_max_num
            if self.pos == 0 and time_constraint:

                if self.long_entered:
                    self.buy(bar.close_price + 5, self.fixed_size)
                    self.long_order_record.append(bar.close_price + 5)
                elif self.short_entered:
                    self.short(bar.close_price - 5, self.fixed_size)
                    self.short_order_record.append(bar.close_price - 5)
            elif self.pos > 0:
                buy_order_price = self.long_order_record[-1]
                if bar.close_price >= buy_order_price*(1+self.exit_return):
                    self.sell(bar.close_price * 0.99, abs(self.pos))
                elif bar.close_price <= buy_order_price*(1-self.exit_loss):
                    self.sell(bar.close_price * 0.99, abs(self.pos))
            elif self.pos < 0:
                sell_order_price = self.short_order_record[-1]
                if bar.close_price >= sell_order_price*(1+self.exit_loss):
                    self.cover(bar.close_price * 1.01, abs(self.pos))
                elif bar.close_price <= sell_order_price*(1-self.exit_return):
                    self.cover(bar.close_price * 1.01, abs(self.pos))
        elif bar.datetime.time() > self.exit_time:
            if self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))

        self.put_event()

    def on_15min_bar(self, bar: BarData):
        """"""
        self.am15.update_bar(bar)
        self.bar_num += 1
        if not self.am15.inited:
            return
        self.rsi_value_l_window = self.am15.rsi(self.rsi_window)
        am = self.am15
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
                self.cross_over_record_array[1, -self.cross_over_slice_window :])
            self.cross_over_slice_window_lowest = np.min(
                self.cross_over_record_array[2, -self.cross_over_slice_window :])
            self.last_cross_over_interval = self.bar_num - \
                                            self.cross_over_record_array[0, -1]
            self.last_cross_over_side = self.cross_over_record_array[3, -1]
            true_range_influence = np.mean(am.trange(
                array=True)[-self.true_range_window:]) * self.true_range_influence_multiplier
            self.long_open_stop_order_price = self.cross_over_slice_window_highest + \
                                              true_range_influence
            self.short_open_stop_order_price = self.cross_over_slice_window_lowest + \
                                               true_range_influence



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
