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


class DoubleRsiAtr(CtaTemplate):
    """"""
    author = "yiran"

    s_window = 5
    l_window = 15
    atr_window = 20
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

    position_hold = 0
    long_entered = False
    short_entered = False

    parameters = ['s_window', 'l_window', 'atr_window', 'atr_multiplier', 'exit_return_soft_long', 'exit_loss_soft_long',
                  "rsi_window", 'exit_return_soft_short', 'exit_loss_soft_short',
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

        self.bg5 = BarGenerator(self.on_bar, self.s_window, self.on_5min_bar)
        self.am5 = ArrayManager()

        self.bg15 = BarGenerator(self.on_bar, self.l_window, self.on_15min_bar)
        self.am15 = ArrayManager()
        self.long_order_record = []
        self.short_order_record = []
        self.atr_value_array = np.array([])

        self.atr_profit_exit_recorder = []

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

        if self.long_threshold_l_window != -9999:
            self.long_entered = (self.rsi_value_s_window > self.rsi_long_s) and (self.rsi_value_l_window > self.rsi_long_l)
            self.short_entered = (self.rsi_value_s_window < self.rsi_short_s) and (self.rsi_value_l_window < self.rsi_short_l)
        else:
            return

        if self.start_time <= bar.datetime.time() < self.exit_time:
            if self.pos == 0:
                self.position_hold = 0
                if self.long_entered:
                    self.buy(bar.close_price + 5, self.fixed_size)
                    self.long_order_record.append(bar.close_price + 5)
                elif self.short_entered:
                    self.short(bar.close_price - 5, self.fixed_size)
                    self.short_order_record.append(bar.close_price - 5)
            elif self.pos > 0:
                self.position_hold += 1
                buy_order_price = self.long_order_record[-1]
                initial_profit_exit_price = buy_order_price*(1+self.exit_return)
                # 波动变大+持仓周期变长，会使得止盈的点上移
                moving_profit_exit_price = buy_order_price*(1+self.exit_return_soft_long) + self.atr_value*self.atr_multiplier*self.position_hold

                initial_loss_exit_price = buy_order_price*(1-self.exit_loss)
                # 波动变大+持仓周期变长，会使得止损的点上移
                moving_loss_exit_price = buy_order_price*(1+self.exit_loss_soft_long) + self.atr_value*self.atr_multiplier*self.position_hold
                if initial_profit_exit_price < moving_profit_exit_price:
                    self.atr_profit_exit_recorder.append((1, bar.datetime))
                else:
                    self.atr_profit_exit_recorder.append((0, bar.datetime))

                if bar.close_price >= max(initial_profit_exit_price, moving_profit_exit_price):
                    self.sell(bar.close_price * 0.99, abs(self.pos))
                elif bar.close_price <= max(initial_loss_exit_price, moving_loss_exit_price):
                    self.sell(bar.close_price * 0.99, abs(self.pos))

            elif self.pos < 0:
                self.position_hold += 1
                sell_order_price = self.short_order_record[-1]
                #初始的盈利要求比较低即空头平仓的价格比较高
                initial_profit_exit_price = sell_order_price * (1 - self.exit_return)
                # 随着持仓时间推移和波动率变大，对应盈利方向上的头寸止盈要求变高，即空头平仓价格下移
                moving_profit_exit_price = sell_order_price * (
                            1 + self.exit_return_soft_short) - self.atr_value * self.atr_multiplier * self.position_hold
                initial_loss_exit_price = sell_order_price * (1 + self.exit_loss)
                # 随着持仓时间推移和波动率变大，对应亏损方向上的头寸的平仓价格上升，即空头平仓价格上升
                moving_loss_exit_price = sell_order_price * (
                            1 + self.exit_loss_soft_short) - self.atr_value * self.atr_multiplier * self.position_hold

                if bar.close_price >= min(initial_loss_exit_price, moving_loss_exit_price):
                    self.cover(bar.close_price * 1.01, abs(self.pos))
                elif bar.close_price <= min(initial_profit_exit_price, moving_profit_exit_price):
                    self.cover(bar.close_price * 1.01, abs(self.pos))

        # 通过设置合成Bar Data的周期可以使得持仓过夜
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
