
import backtrader as bt
from indicator import LinearIndicator, HorizontalLinearIndicator
import numpy as np
import pandas as pd
import math

class GridBar:
    def __init__(self,
                 grid_no,
                 grid_price,
                 grid_tp,
                 grid_sl,
                 grid_indicator
                 ):
        self.grid_no = grid_no
        self.grid_price = grid_price
        self.grid_tp = grid_tp
        self.grid_sl = grid_sl
        self.grid_indicator = grid_indicator
        self.is_opened = False
        self.buy_order = None
        self.tp_order = None
        self.sl_order = None

    def open_order(self, buy_order, tp_order, sl_order):
        self.is_opened = True
        self.buy_order = buy_order
        self.tp_order = tp_order
        self.sl_order = sl_order
    
    def close_order(self):
        self.is_opened = False
        self.buy_order = None
        self.tp_order = None
        self.sl_order = None

class GridAdaptiveZoneStrategy(bt.Strategy):

    params = {
        'n_grid': 32,
        'zone': {
            'start_price': 8000,
            'high_side_ratio': 0.3,
            'low_side_ratio': 0.7
        },
        'position': {
            'type': 'FIX_CASH',
            'position_cash': 10000
        },
        'plot': {
            'plot_grid_bar': True,
            'plot_cross_over': False
        }
    }

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt} position.size {self.position.size:.5f}')

    def __init__(self):
        self.__create_grid_bars()

    def __create_grid_bars(self):
        self.base_grid_price = self.p.zone['start_price']
        self.top_grid_price = self.base_grid_price * (1 + self.p.zone['high_side_ratio'])
        self.bottom_grid_price = self.base_grid_price * (1 - self.p.zone['low_side_ratio'])
        

        grid_size = (self.top_grid_price -
                     self.bottom_grid_price) / (self.p.n_grid+1)
        self.grids = []
        for grid_no in range(self.p.n_grid):
            price = self.bottom_grid_price + grid_size*grid_no
            # Take profit at next grid bar
            tp_price = self.bottom_grid_price + grid_size*(grid_no+1)
            grid_line = HorizontalLinearIndicator(
                y=price, plot=self.p.plot['plot_grid_bar'], plotname=f'bar_{grid_no}')

            grid = GridBar(
                grid_no=grid_no,
                grid_price=price,
                grid_tp=tp_price,
                grid_sl=1, # Never stop loss
                grid_indicator=grid_line
            )

            self.open_grid(grid)

            self.grids.append(grid)

    def create_new_zone(self, new_base_grid_price):
        self.base_grid_price = new_base_grid_price
        self.top_grid_price = self.base_grid_price * (1 + self.p.zone['high_side_ratio'])
        self.bottom_grid_price = self.base_grid_price * (1 - self.p.zone['low_side_ratio'])
        
        grid_size = (self.top_grid_price -
                     self.bottom_grid_price) / (self.p.n_grid+1)
        
        for grid in self.grids:
            grid_no = grid.grid_no
            price = self.bottom_grid_price + grid_size*grid_no
            # Take profit at next grid bar
            tp_price = self.bottom_grid_price + grid_size*(grid_no+1)

            grid.grid_price = price
            grid.grid_indicator.update_y(price)
            grid.grid_tp = tp_price

            # FIXME: DO something before close order
            grid.close_order()

    def open_grid(self, grid):

        size = self.p.position['position_cash'] / grid.grid_price
        buy_order, sl_order, tp_order = self.buy_bracket(size=size,
                                                         price=grid.grid_price,
                                                         exectype=bt.Order.Limit,
                                                         limitprice=grid.grid_tp,
                                                         limitexec=bt.Order.Limit,
                                                         stopprice=grid.grid_sl,
                                                         stopexec=bt.Order.StopLimit
                                                         )
        grid.open_order(buy_order, tp_order, sl_order)
        self.log(
            f'open buy #{buy_order.ref} {grid.grid_price:.3f}, tp #{tp_order.ref}: {grid.grid_tp:.3f}, sl #{sl_order.ref}: {grid.grid_sl}')

    
    def next(self):

        # Create new zone if price goes over our current zone
        if self.data.close[0] < self.bottom_grid_price or self.data.close[0] > self.top_grid_price:
            self.create_new_zone(self.data.close[0])
        
        available_grids = filter(lambda grid: not grid.is_opened, self.grids)
        for grid in available_grids:
            self.open_grid(grid)
            
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, #{order.ref} {order.executed.price:.3f}')

                # buy_order_df = pd.DataFrame([{
                #     'price': order.executed.price,
                #     'share': self.p.grid_share
                # }], index=pd.DatetimeIndex(data=[bt.num2date(order.executed.dt)], name='time'))
                # self.order_df = pd.concat([self.order_df, buy_order_df])
                # print(self.position)
            elif order.issell():
                self.log(
                    f'SELL EXECUTED, #{order.ref} {order.executed.price:.3f}')
                
                grid = next(filter(lambda grid: grid.is_opened and grid.tp_order.ref == order.ref, self.grids), None)
                if grid:
                    grid.close_order()

                # print(self.position)
        pass
    
    def notify_trade(self, trade):
        pass