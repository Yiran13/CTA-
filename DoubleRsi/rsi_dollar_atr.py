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
import talib


class RsiDollarATR(CtaTemplate):
    """"""
    author = "yiran"

    dollar_threshold = 1_00_00_00_0
    long_trend_cum_threshold = 10
    short_trend_cum_threshold = 10
    init_dollar_bar_num = 100

    rsi_window = 10
    atr_window = 10
    rsi_up_threshold = 70
    sma_short_window = 5
    sma_long_window = 20

    exit_loss = 0.02
    exit_return = 0.2
    atr_multiplier = 0.05
    cross_over_day = 10
    fixed_size = 1

    long_order_record = []
    short_order_record = []

    rsi_value = 0
    atr_value = 0
    long_trend_cum = 0
    short_trend_cum = 0
    stop_price = 0
    exit_price = 0
    hold_bar_num = 0

    cum_filtered = False
    dollar_bar_finished = False
    long_trend = False
    short_trend = False
    long_trend_days = np.inf
    short_trend_days = np.inf

    parameters = [
        'rsi_window',
        'rsi_up_threshold',
        'atr_window',
        'sma_short_window',
        'cross_over_day',
        'sma_long_window',
        'atr_multiplier',
        'long_trend_cum_threshold',
        'short_trend_cum_threshold',
        'exit_loss','exit_return',
        'sma_short_window',
        'sma_long_window']

    variables = ['rsi_value', 'atr_value', 'exit_price']

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        self.long_order_record = []
        self.short_order_record = []

        self.one_minute_bar_price_list = []
        self.one_minute_bar_volume_list = []
        self.time_list = []
        self.one_minute_bar_num_list = []

        # dollar-bar
        self.high_list = []
        self.low_list = []
        self.close_list = []
        self.open_list = []
        self.volume_list = []

        # cum_filter_bar
        self.cum_high_list = []
        self.cum_low_list = []
        self.cum_close_list = []
        self.cum_open_list = []
        self.cum_volume_list = []
        self.cum_time_list = []

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
        self.one_minute_bar_price_list.append(bar.close_price)
        self.one_minute_bar_volume_list.append(bar.volume)
        dollar_amount = np.sum(
            np.array(
                self.one_minute_bar_price_list) *
            np.array(
                self.one_minute_bar_volume_list))

        if dollar_amount >= self.dollar_threshold:

            high_price = np.max(self.one_minute_bar_price_list)
            close = self.one_minute_bar_price_list[-1]
            low_price = np.min(self.one_minute_bar_price_list)
            open_price = self.one_minute_bar_price_list[0]
            volume = np.sum(self.one_minute_bar_volume_list)

            self.high_list.append(high_price)
            self.close_list.append(close)
            self.open_list.append(open_price)
            self.volume_list.append(volume)
            self.low_list.append(low_price)
            self.time_list.append(bar.datetime)
            self.one_minute_bar_num_list.append(
                len(self.one_minute_bar_price_list))

            self.one_minute_bar_volume_list = []
            self.one_minute_bar_price_list = []
            # 交易策略信号计算在dollar合成之后
            self.dollar_bar_finished = True

        if len(self.high_list) < self.init_dollar_bar_num:
            return

        if self.dollar_bar_finished:
            self.cancel_all()
            close_array = np.array(self.close_list)
            high_array = np.array(self.high_list)
            low_array = np.array(self.low_list)
            open_array = np.array(self.open_list)
            volume_array = np.array(self.volume_list)

            if close_array.shape[0] < self.rsi_window:
                self.dollar_bar_finished = False
                return

            self.rsi_value = talib.RSI(close_array, self.rsi_window)[-1]
            if self.rsi_value > self.rsi_up_threshold:
                self.long_trend_cum += 1
            elif self.rsi_value < 100 - self.rsi_up_threshold:
                self.short_trend_cum += 1
            if self.long_trend_cum >= self.long_trend_cum_threshold or self.short_trend_cum >= self.short_trend_cum_threshold:
                self.cum_filtered = True

            if self.cum_filtered:
                self.cum_close_list.append(close_array[-1])
                self.cum_high_list.append(high_array[-1])
                self.cum_low_list.append(low_array[-1])
                self.cum_open_list.append(open_array[-1])
                self.cum_volume_list.append(volume_array[-1])
                self.cum_time_list.append(bar.datetime)

                if len(
                        self.cum_open_list) < max(
                        self.sma_long_window,
                        self.atr_window):
                    self.dollar_bar_finished = False
                    self.cum_filtered = False
                    self.long_trend_cum = 0
                    self.short_trend_cum = 0
                    return

                cum_close_array = np.array(self.cum_close_list)
                cum_high_array = np.array(self.cum_high_list)
                cum_low_array = np.array(self.cum_low_list)
                cum_open_array = np.array(self.cum_open_list)
                sma_short_window_array = talib.SMA(
                    cum_close_array, self.sma_short_window)
                sma_long_window_array = talib.SMA(
                    cum_close_array, self.sma_long_window)

                atr_array = talib.ATR(
                    cum_high_array,
                    cum_low_array,
                    cum_close_array,
                    self.atr_window)
                self.atr_value = atr_array[-1]

                if sma_long_window_array[-2] > sma_short_window_array[-2] and sma_long_window_array[-1] < sma_short_window_array[-1]:
                    self.long_trend = True
                    self.long_trend_days = 0
                elif sma_long_window_array[-2] < sma_short_window_array[-2] and sma_long_window_array[-1] > sma_short_window_array[-1]:
                    self.short_trend = True
                    self.short_trend_days = 0

                if self.short_trend_days != np.inf:
                    self.short_trend_days += 1
                elif self.long_trend_days != np.inf:
                    self.long_trend_days += 1

                if self.pos == 0:
                    self.stop_price = 0
                    self.exit_price = 0
                    self.hold_bar_num = 0
                    if self.short_trend and self.short_trend_days < self.cross_over_day:
                        self.short(bar.close_price - 5, self.fixed_size)
                        self.short_order_record.append(bar.close_price - 5)

                    elif self.long_trend and self.long_trend_days < self.cross_over_day:
                        self.buy(bar.close_price + 5, self.fixed_size)
                        self.long_order_record.append(bar.close_price + 5)

                elif self.pos > 0:
                    self.long_trend = False
                    self.long_trend_days = np.inf
                    buy_order_price = self.long_order_record[-1]
                    self.stop_price = buy_order_price * (1 - self.exit_loss)
                    self.exit_price = buy_order_price * \
                        (1 + self.exit_return) - self.hold_bar_num * self.atr_value * self.atr_multiplier
                    if bar.close_price <= self.exit_price:
                        self.sell(bar.close_price * 0.99, abs(self.pos))
                    elif bar.close_price >= self.exit_price:
                        self.sell(bar.close_price * 0.99, abs(self.pos))
                    self.hold_bar_num += 1

                elif self.pos < 0:
                    self.short_trend = False
                    self.short_trend_days = np.inf
                    sell_order_price = self.short_order_record[-1]
                    self.stop_price = sell_order_price * (1 + self.exit_loss)

                    self.exit_price = sell_order_price * \
                        (1 - self.exit_return) + self.hold_bar_num * self.atr_value * self.atr_multiplier
                    if bar.close_price >= self.stop_price:
                        self.cover(bar.close_price * 1.01, abs(self.pos))
                    elif bar.close_price <= self.exit_price:
                        self.cover(bar.close_price * 1.01, abs(self.pos))

                    self.hold_bar_num += 1

                self.dollar_bar_finished = False
                self.cum_filtered = False
                self.long_trend_cum = 0
                self.short_trend_cum = 0

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
