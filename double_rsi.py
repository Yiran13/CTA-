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


class DoubleRsi(CtaTemplate):
    """"""
    author = "yiran"

    rsi_window = 11
    long_threshold_l_window = 50
    long_threshold_s_window = 80
    fixed_size = 1

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

    parameters = ["rsi_window",
                  "long_threshold_l_window", "long_threshold_s_window", 'exit_return',
                  'exit_loss', "fixed_size"]

    variables = ["rsi_value_l_window ", "rsi_value_s_window", "ma_trend"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.rsi_long_l = self.long_threshold_l_window
        self.rsi_long_s = self.long_threshold_s_window
        self.rsi_short_l = 100-self.long_threshold_l_window
        self.rsi_short_s = 100-self.long_threshold_s_window

        self.bg5 = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.am5 = ArrayManager()

        self.bg15 = BarGenerator(self.on_bar, 15, self.on_15min_bar)
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
            self.long_entered = (self.rsi_value_s_window > self.rsi_long_s) and (self.rsi_value_l_window > self.rsi_long_l)
            self.short_entered = (self.rsi_value_s_window < self.rsi_short_s) and (self.rsi_value_l_window < self.rsi_short_l)
        else:
            return

        if self.start_time <= bar.datetime.time() < self.exit_time:
            if self.pos == 0:
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
        if not self.am15.inited:
            return
        self.rsi_value_l_window = self.am15.rsi(self.rsi_window)

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
