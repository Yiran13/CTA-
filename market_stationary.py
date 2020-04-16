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
class MarketStationary(CtaTemplate):
    """"""
    author = ""

    stationary_threshold = 4 / 1000

    market_open_time = time(hour=9, minute=30)
    start_record_time_m = time(hour=9, minute=30)
    start_trade_time_m = time(hour=10, minute=20)
    exit_time_m = time(hour=11, minute=30)
    start_trade_time_a = time(hour=13, minute=33)
    exit_time_a = time(hour=14, minute=55)

    fixed_size = 1
    pct_array_m = []
    pct_array_a = []
    open_price = 0
    draw_back_mean_m = 0
    draw_back_inverse_mean_m = 0
    draw_back_inverse_mean_a = 0
    stationary_value_m = 0
    draw_back_mean_a = 0
    draw_back_inverse_a = 0
    stationary_value_m = 0
    stationary_value_a = 0
    exit_loss = 5 / 1000
    bar_num = 0

    long_order_record_m = []
    short_order_record_m = []
    long_order_record_a = []
    short_order_record_a = []


    trend_bool_m = False
    trend_bool_a = False
    first_time_m = True
    first_time_a = True


    parameters = ['stationary_threshold']
    variables = ['stationary_value_m', 'stationary_value_a', 'trend_bool']

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(size=300)

        self.long_order_record_m = []
        self.short_order_record_m = []
        self.long_order_record_a = []
        self.short_order_record_a = []
        self.pct_array_m = []
        self.pct_array_a = []
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

        if not self.am.inited:
            return

        am = self.am

        if bar.datetime.time() == self.market_open_time:
            self.open_price = bar.close_price
        if bar.datetime.time() == self.start_trade_time_m:
            self.bar_num = 0
        elif bar.datetime.time() < self.start_trade_time_a:
            self.bar_num += 1
        elif bar.datetime.time() >= self.exit_time_a:
            self.bar_num = 0

        if self.open_price > 0:

            if bar.datetime.time() == self.start_trade_time_m:

                price_array = am.close[-self.bar_num:]
                draw_back_record = []
                draw_back_inverse_record = []
                for ind in range(self.bar_num):
                    if ind < self.bar_num-1:

                        self.pct_array_m = (price_array-price_array[ind])/price_array[ind]
                        print(self.pct_array_m)
                        draw_back = max(self.pct_array_m[ind+1:])
                        draw_back_inverse = -min(self.pct_array_m[ind+1:])
                        draw_back_record.append(draw_back)
                        draw_back_inverse_record.append(draw_back_inverse)


                self.draw_back_mean_m = np.mean(draw_back_record)
                self.draw_back_inverse_mean_m = np.mean(draw_back_inverse_record)
                self.stationary_value_m = np.min([self.draw_back_mean_m, self.draw_back_inverse_mean_m])

                if self.stationary_value_m < self.stationary_threshold:
                    self.trend_bool_m = True

            elif bar.datetime.time() < self.exit_time_m:
                if self.trend_bool_m:
                    if self.pos == 0 and self.first_time_m:
                        if bar.close_price > self.open_price:
                            self.buy(bar.close_price + 5, self.fixed_size)
                            self.long_order_record_m.append(bar.close_price + 5)
                        elif bar.close_price < self.open_price:
                            self.short(bar.close_price - 5, self.fixed_size)
                            self.short_order_record_m.append(bar.close_price - 5)

                    elif self.pos > 0:
                        self.first_time_m = False
                        buy_order_price = self.long_order_record_m[-1]
                        if bar.close_price <= buy_order_price * (1 - self.exit_loss):
                            self.sell(bar.close_price * 0.99, abs(self.pos))

                    elif self.pos < 0:
                        self.first_time_m = False
                        sell_order_price = self.short_order_record_m[-1]
                        if bar.close_price >= sell_order_price * (1 + self.exit_loss):
                            self.cover(bar.close_price * 1.01, abs(self.pos))

            elif self.exit_time_m <= bar.datetime.time() < self.start_trade_time_a:
                if self.pos > 0:
                    self.sell(bar.close_price * 0.99, abs(self.pos))
                elif self.pos < 0:
                    self.cover(bar.close_price * 1.01, abs(self.pos))
                self.trend_bool_m = False
                self.first_time_m = True
            elif bar.datetime.time() == self.start_trade_time_a:
                price_array = am.close[-self.bar_num:]
                draw_back_record = []
                draw_back_inverse_record = []
                for ind in range(self.bar_num):
                    if ind < self.bar_num-1:
                        self.pct_array_a = (price_array-price_array[ind])/price_array[ind]
                        draw_back = max(self.pct_array_a[ind+1:])
                        draw_back_inverse = -min(self.pct_array_a[ind+1:])
                        draw_back_record.append(draw_back)
                        draw_back_inverse_record.append(draw_back_inverse)

                self.draw_back_mean_a = np.mean(draw_back_record)
                self.draw_back_inverse_mean_a = np.mean(draw_back_inverse_record)
                self.stationary_value_a = np.min([self.draw_back_mean_a, self.draw_back_inverse_mean_a])
                if self.stationary_value_a < self.stationary_threshold:
                    self.trend_bool_a = True
            elif self.start_trade_time_a <= bar.datetime.time() < self.exit_time_a:
                if self.trend_bool_a:
                    if self.pos == 0 and self.first_time_a:
                        if bar.close_price > self.open_price:
                            self.buy(bar.close_price + 5, self.fixed_size)
                            self.long_order_record_a.append(bar.close_price + 5)
                        elif bar.close_price < self.open_price:
                            self.short(bar.close_price - 5, self.fixed_size)
                            self.short_order_record_a.append(bar.close_price - 5)

                    elif self.pos > 0:
                        self.first_time_a = False
                        buy_order_price = self.long_order_record_a[-1]
                        if bar.close_price <= buy_order_price * (1 - self.exit_loss):
                            self.sell(bar.close_price * 0.99, abs(self.pos))

                    elif self.pos < 0:
                        self.first_time_a = False
                        sell_order_price = self.short_order_record_a[-1]
                        if bar.close_price >= sell_order_price * (1 + self.exit_loss):
                            self.cover(bar.close_price * 1.01, abs(self.pos))
            elif bar.datetime.time() >= self.exit_time_a:
                if self.pos > 0:
                    self.sell(bar.close_price * 0.99, abs(self.pos))
                elif self.pos < 0:
                    self.cover(bar.close_price * 1.01, abs(self.pos))
                self.trend_bool_a = False
                self.first_time_a = True
                self.open_price = 0
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
