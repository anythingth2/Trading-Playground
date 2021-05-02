import backtrader as bt


class GoldenCrossStrategy(bt.Strategy):
    params = (('fast', 30), ('slow', 60))

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s position.size %s' % (dt.isoformat(), txt, self.position.size))

    def __init__(self):
        self.fast_signal = bt.indicators.MovingAverageSimple(period=self.params.fast)
        self.slow_signal = bt.indicators.MovingAverageSimple(period=self.params.slow)
        self.cross_over = bt.indicators.CrossOver(self.fast_signal, self.slow_signal)
        self.diff = bt.indicators.NonZeroDifference(self.fast_signal, self.slow_signal)

    def next(self):

        if self.diff > 0:
            self.log('buy')
            self.buy()
            # print(self.position)
        elif self.cross_over < 0:
            self.log('close position')
            print(self.position)
            self.close()
            # print(self.position)
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)
                print(self.position)