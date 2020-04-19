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


class RsiDollarRsi(CtaTemplate):
    """"""
    author = "yiran"

    dollar_threshold = 1_00_00_00_0
    rsi_window = 10
    rsi_up_threshold = 70
    sma_short_window = 5
    sma_long_window = 20
    long_trend_cum_threshold = 10
    short_trend_cum_threshold = 10
    cross_over_day = 10
    bbands_window = 14
    exit_return = 0.04
    exit_loss = 0.02
    fixed_size = 1

    long_order_record = []
    short_order_record = []


    init_dollar_bar_num = 100
    rsi_value = 0
    rsi_cum_value = 0
    long_trend_cum = 0
    short_trend_cum = 0
    long_trend_days = np.inf
    short_trend_days =np.inf

    cum_filtered = False
    dollar_bar_finished = False
    long_trend = False
    short_trend = False
    rsi_long = False
    rsi_short = False

    # cum_filtered_cci_value = 0
    parameters = ['rsi_window', 'rsi_up_threshold',
                  'long_trend_cum_threshold', 'short_trend_cum_threshold',
                  'bbands_window', 'exit_return', 'exit_loss', 'sma_short_window', 'sma_long_window']

    variables = ['rsi_value', 'long_trend_cum', 'short_trend_cum']

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

        #dollar-bar
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
        dollar_amount = np.sum(np.array(self.one_minute_bar_price_list)*np.array(self.one_minute_bar_volume_list))

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
            self.one_minute_bar_num_list.append(len(self.one_minute_bar_price_list))

            self.one_minute_bar_volume_list = []
            self.one_minute_bar_price_list = []
            # 交易策略信号计算在dollar合成之后
            self.dollar_bar_finished = True

        if len(self.high_list) < self.init_dollar_bar_num:
            return

        if self.dollar_bar_finished:
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
            elif self.rsi_value < 100-self.rsi_up_threshold:
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

                if len(self.cum_open_list) < self.bbands_window:
                    self.dollar_bar_finished = False
                    self.cum_filtered = False
                    self.long_trend_cum = 0
                    self.short_trend_cum = 0
                    return

                cum_close_array = np.array(self.cum_close_list)
                cum_high_array = np.array(self.cum_high_list)
                cum_low_array = np.array(self.cum_low_list)
                cum_open_array = np.array(self.cum_open_list)
                sma_short_window_array = talib.SMA(cum_close_array,self.sma_short_window)
                sma_long_window_array = talib.SMA(cum_close_array,self.sma_long_window)
                rsi_window_array = talib.RSI(cum_close_array, self.rsi_window)
                if sma_long_window_array[-2] > sma_short_window_array [-2] and sma_long_window_array[-1] < sma_short_window_array[-1]:
                    self.long_trend = True
                    self.long_trend_days = 0
                if sma_long_window_array[-2] < sma_short_window_array [-2] and sma_long_window_array[-1] > sma_short_window_array[-1]:
                    self.short_trend = True
                    self.short_trend_days = 0

                if rsi_window_array[-2] < 100-self.rsi_up_threshold < rsi_window_array[-1]:
                    self.rsi_long = True
                elif rsi_window_array[-2] > self.rsi_up_threshold > rsi_window_array[-1]:
                    self.rsi_short = True
                else:
                    self.rsi_long = False
                    self.rsi_short = False

                if self.short_trend_days != np.inf:
                    self.short_trend_days += 1
                elif self.long_trend_days != np.inf:
                    self.long_trend_days += 1


                if self.pos == 0:

                    if self.short_trend and self.short_trend_days < self.cross_over_day and self.rsi_short:
                        self.short(bar.close_price - 5, self.fixed_size)
                        self.short_order_record.append(bar.close_price - 5)

                    elif self.long_trend and self.long_trend_days < self.cross_over_day and self.rsi_long:
                        self.buy(bar.close_price+5, self.fixed_size)
                        self.long_order_record.append(bar.close_price + 5)

                elif self.pos > 0:
                    self.long_trend = False
                    self.long_trend_days = np.inf
                    buy_order_price = self.long_order_record[-1]
                    if bar.close_price >= buy_order_price * (1 + self.exit_return):
                        self.sell(bar.close_price * 0.99, abs(self.pos))
                    elif bar.close_price <= buy_order_price * (1 - self.exit_loss):
                        self.sell(bar.close_price * 0.99, abs(self.pos))

                elif self.pos < 0:
                    self.short_trend = False
                    self.short_trend_days = np.inf
                    sell_order_price = self.short_order_record[-1]
                    if bar.close_price >= sell_order_price * (1 + self.exit_loss):
                        self.cover(bar.close_price * 1.01, abs(self.pos))
                    elif bar.close_price <= sell_order_price * (1 - self.exit_return):
                        self.cover(bar.close_price * 1.01, abs(self.pos))

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
