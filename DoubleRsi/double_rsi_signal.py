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

    atr_window = 20
    obv_window = 10
    minus_dm_window = 10
    mfi_window = 20
    ad_window = 20
    adosc_window = 20
    plus_dm_window = 20
    dx_window = 20
    adx_window = 20

    s_window = 5
    l_window = 15
    atr_multiplier = 0.05
    rsi_window = 11
    long_threshold_l_window = 50
    long_threshold_s_window = 80
    exit_return = 0.02
    exit_loss = 0.02
    exit_return_soft_long = -0.1
    exit_loss_soft_long = -0.2
    exit_return_soft_short = 0.2
    exit_loss_soft_short = 0.1

    fixed_size = 1

    start_time = time(hour=10)
    exit_time = time(hour=14, minute=55)

    long_order_record = []
    short_order_record = []

    rsi_value_l_window = -9999
    rsi_value_s_window = -9999
    atr_value = 0
    minus_dm_value = 0
    obv_value = 0
    mfi_value = 0
    ad_value = 0
    adosc_value = 0
    plus_dm_value = 0
    dx_value = 0
    adx_value = 0

    position_hold = 0
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

        self.bg5 = BarGenerator(self.on_bar, self.s_window, self.on_5min_bar)
        self.am5 = ArrayManager()

        self.bg15 = BarGenerator(self.on_bar, self.l_window, self.on_15min_bar)
        self.am15 = ArrayManager()
        self.long_order_record = []
        self.short_order_record = []
        # 指标计算容器
        self.rsi_value_recorder_l_window = []
        self.rsi_time_recorder_l_window = []
        self.rsi_value_recorder_s_window = []
        self.rsi_time_recorder_s_window = []
        self.atr_time_recorder = []
        self.atr_value_recorder = []
        self.obv_time_recorder = []
        self.obv_value_recorder = []
        self.minus_dm_time_recorder = []
        self.minus_dm_value_recorder = []
        self.mfi_time_recorder = []
        self.mfi_value_recorder = []
        self.ad_time_recorder = []
        self.ad_value_recorder = []
        self.adosc_time_recorder = []
        self.adosc_value_recorder = []
        self.plus_dm_time_recorder = []
        self.plus_dm_value_recorder = []
        self.dx_time_recorder = []
        self.dx_value_recorder = []
        self.adx_time_recorder = []
        self.adx_value_recorder = []


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
        self.atr_value = self.am5.atr(self.atr_window)
        self.obv_value = self.am5.obv(self.obv_window)
        self.minus_dm_value = self.am5.minus_dm(self.minus_dm_window)
        self.mfi_value = self.am5.mfi(self.mfi_window)
        self.ad_value = self.am5.ad(self.ad_window)
        self.adosc_value = self.am5.adosc(self.adosc_window)
        self.plus_dm_value = self.am5.adosc(self.plus_dm_window)
        self.dx_value = self.am5.adosc(self.dx_window)
        self.adx_value = self.am5.adosc(self.adx_window)

        self.rsi_time_recorder_s_window.append(bar.datetime)
        self.rsi_value_recorder_s_window.append(self.rsi_value_s_window)

        self.atr_time_recorder.append(bar.datetime)
        self.atr_value_recorder.append(self.atr_value)

        self.obv_time_recorder.append(bar.datetime)
        self.obv_value_recorder.append(self.obv_value)

        self.minus_dm_time_recorder.append(bar.datetime)
        self.minus_dm_value_recorder.append(self.minus_dm_value)

        self.mfi_time_recorder.append(bar.datetime)
        self.mfi_value_recorder.append(self.mfi_value)

        self.ad_time_recorder.append(bar.datetime)
        self.ad_value_recorder.append(self.ad_value)

        self.adosc_time_recorder.append(bar.datetime)
        self.adosc_value_recorder.append(self.adosc_value)

        self.plus_dm_time_recorder.append(bar.datetime)
        self.plus_dm_value_recorder.append(self.plus_dm_value)

        self.dx_time_recorder.append(bar.datetime)
        self.dx_value_recorder.append(self.dx_value)

        self.adx_time_recorder.append(bar.datetime)
        self.adx_value_recorder.append(self.adx_value)




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
