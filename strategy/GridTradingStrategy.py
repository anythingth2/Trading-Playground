import datetime
import backtrader as bt
from indicator import LinearIndicator, HorizontalLinearIndicator
import numpy as np
import pandas as pd


class GridTradingStrategy(bt.Strategy):

    params = {
        'base_grid_price': 0.67,
        'n_grid': 8,
        'grid_size': 0.02,
        'grid_share': 500,
        'plot_grid_bar': True,
        'plot_cross_over': False
    }

    
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s position.size %s' %
              (dt.isoformat(), txt, self.position.size))

    def __init__(self):
        self.ma = bt.indicators.MovingAverageSimple(self.data.close, period=10)
        self.__create_grid_bars()
        self.order_df = pd.DataFrame(columns=['price', 'share'],
                                     index=pd.DatetimeIndex(data=[], name='time'))

    def __create_grid_bars(self):
        def create_single_grid(grid_no):
            y = self.p.base_grid_price + grid_no * self.p.grid_size
            return HorizontalLinearIndicator(y=y, plot=self.p.plot_grid_bar, plotname=f'bar_{grid_no}')

        def create_cross_over(grid_bar):
            return bt.indicators.CrossOver(self.ma, grid_bar, plot=self.p.plot_cross_over, plotname=f'cross_{grid_bar.plotinfo.plotname}')
        self.grid_bars = [create_single_grid(i) for i in range(self.p.n_grid)]
        self.cross_overs = [create_cross_over(
            grid_bar) for grid_bar in self.grid_bars]

    def next(self):
        cross_over_signals = np.array(
            [cross_over[0] for cross_over in self.cross_overs])
        if not np.all(cross_over_signals == 0):
            if np.max(cross_over_signals) > 0:  # Cross up signal
                crossed_bar_index = np.argmax(cross_over_signals)
                order = self.buy(size=self.p.grid_share, price=self.ma[0])

                # print(order)
            elif np.min(cross_over_signals) < 0:  # Cross down signal
                crossed_bar_index = np.argmin(cross_over_signals)
                existing_buy_order_df = self.order_df[self.order_df['price'] < self.ma[0]]
                print(existing_buy_order_df)
                self.order_df.drop(index=existing_buy_order_df.index, inplace=True)
                self.sell(size=existing_buy_order_df['share'].sum(), price=self.ma[0])
                

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)

                buy_order_df = pd.DataFrame([{
                    'price': order.executed.price,
                    'share': self.p.grid_share
                }], index=pd.DatetimeIndex(data=[bt.num2date(order.executed.dt)], name='time'))
                self.order_df = pd.concat([self.order_df, buy_order_df])
                # print(self.position)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)
                # print(self.position)
