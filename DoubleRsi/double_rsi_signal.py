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


class DoubleSignalGenerator(CtaTemplate):
    """"""
    author = "yiran"

    rsi_value_recorder_l_window = []
    rsi_time_recorder_l_window = []
    rsi_value_recorder_s_window = []
    rsi_time_recorder_s_window = []

    rsi_window = 11
    long_threshold_l_window = 60
    long_threshold_s_window = 75
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

    parameters = []

    variables = []

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

        self.rsi_value_recorder_l_window = []
        self.rsi_time_recorder_l_window = []
        self.rsi_value_recorder_s_window = []
        self.rsi_time_recorder_s_window = []

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
        self.rsi_time_recorder_s_window.append(bar.datetime)
        self.rsi_value_recorder_s_window.append(self.rsi_value_s_window)

    def on_15min_bar(self, bar: BarData):
        """"""
        self.am15.update_bar(bar)
        if not self.am15.inited:
            return
        self.rsi_value_l_window = self.am15.rsi(self.rsi_window)
        self.rsi_time_recorder_l_window.append(bar.datetime)
        self.rsi_value_recorder_l_window.append(self.rsi_value_l_window)

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
