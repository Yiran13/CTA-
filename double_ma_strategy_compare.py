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


class DoubleMaStrategyforcompare(CtaTemplate):
    author = "compare with rsi filter bar "

    fast_window = 5
    slow_window = 20
    fixed_size = 1

    fast_ma0 = 0.0
    fast_ma1 = 0.0

    slow_ma0 = 0.0
    slow_ma1 = 0.0

    exit_return = 0.04
    exit_loss = 0.02


    parameters = ["fast_window", "slow_window",'exit_return', 'exit_loss']
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
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
        self.put_event()

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

        self.put_event()

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        fast_ma = am.sma(self.fast_window, array=True)
        self.fast_ma0 = fast_ma[-1]
        self.fast_ma1 = fast_ma[-2]

        slow_ma = am.sma(self.slow_window, array=True)
        self.slow_ma0 = slow_ma[-1]
        self.slow_ma1 = slow_ma[-2]

        cross_over = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 < self.slow_ma1
        cross_below = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 > self.slow_ma1

        if self.pos == 0 :
            if cross_below:
                self.short(bar.close_price - 5, self.fixed_size)
                self.short_order_record.append(bar.close_price - 5)

            elif cross_over :
                self.buy(bar.close_price + 5, self.fixed_size)
                self.long_order_record.append(bar.close_price + 5)

        elif self.pos > 0:
            buy_order_price = self.long_order_record[-1]
            if bar.close_price >= buy_order_price * (1 + self.exit_return) :
                self.sell(bar.close_price * 0.99, abs(self.pos))
            elif bar.close_price <= buy_order_price * (1 - self.exit_loss) :
                self.sell(bar.close_price * 0.99, abs(self.pos))
        elif self.pos < 0:
            sell_order_price = self.short_order_record[-1]
            if bar.close_price >= sell_order_price * (1 + self.exit_loss) :
                self.cover(bar.close_price * 1.01, abs(self.pos))
            elif bar.close_price <= sell_order_price * (1 - self.exit_return) :
                self.cover(bar.close_price * 1.01, abs(self.pos))

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
