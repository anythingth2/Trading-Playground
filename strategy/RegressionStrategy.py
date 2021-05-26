import datetime
from indicator.LinearIndicator import HorizontalLinearIndicator
import backtrader as bt
from backtrader.order import Order
from indicator.machine_learning import RegressionIndicator
import numpy as np
import pandas as pd
import logging
from util import OrderHistoryTracker
from typing import List


class RegressionStrategy(bt.Strategy):

    params = {
        'window_size': 48,
        'model_path': None,
        'tracker': None
    }

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or bt.num2date(self.datas[0].datetime[0])
        logging.debug(f'{dt}, {txt} position.size {self.position.size:.2f}')

    def __init__(self):
        self.regression_line = RegressionIndicator(
            model_path=self.p.model_path, window_size=self.p.window_size, plotname='regression')
        self.cross_over = bt.indicators.CrossOver(
            self.regression_line.lines.regression, self.data.close)

        self.order_history_tracker = self.p.tracker

    def enter_long(self, size, price, tp_price, sl_price):

        buy_order, sl_order, tp_order = self.buy_bracket(size=size,
                                                         price=price,
                                                         exectype=bt.Order.Limit,
                                                         limitprice=tp_price,
                                                         stopprice=sl_price)

        buy_order.order_type = 'LONG'
        sl_order.order_type = 'LONG_SL'
        tp_order.order_type = 'LONG_TP'
        self.log(
            f'buy #{buy_order.ref} {price}, tp #{tp_order.ref}: {tp_price:.3f}, sl #{sl_order.ref}: {sl_price:.3f}')

    def enter_short(self, size, price, tp_price, sl_price):

        sell_order, sl_order, tp_order = self.sell_bracket(size=size,
                                                           price=price,
                                                           exectype=bt.Order.Limit,
                                                           limitprice=tp_price,
                                                           stopprice=sl_price)

        sell_order.order_type = 'SHORT'
        sl_order.order_type = 'SHORT_SL'
        tp_order.order_type = 'SHORT_TP'
        self.log(
            f'sell #{sell_order.ref} {price}, tp #{tp_order.ref}: {tp_price:.3f}, sl #{sl_order.ref}: {sl_price:.3f}')

    def order_target(self, size, target_price):
        if target_price > self.data.close[0]:
            action = 'LONG'
            parent_order = self.buy(size=size,
                                    exectype=bt.Order.Market,
                                    transmit=False)
            parent_order.order_type = action
            tp_order = self.sell(size=size,
                                 price=target_price,
                                 exectype=bt.Order.Limit,
                                 parent=parent_order,
                                 transmit=False
                                 )
            tp_order.order_type = 'LONG_TP'

            sl_order = self.sell(size=size,
                                 price=0,
                                 exectype=bt.Order.Stop,
                                 parent=parent_order,
                                 transmit=True,
                                 valid=datetime.timedelta(hours=5)
                                 )
            sl_order.order_type = 'LONG_SL'
        else:
            raise NotImplementedError
        self.log(
            f'{action} #{parent_order.ref} {target_price}, tp #{tp_order.ref}: {target_price:.3f}')

        return parent_order, tp_order

    def next(self):
        # diff_percentage_threshold = 0.0035
        diff_percentage_threshold = 0.0

        if self.cross_over > 0:
            amount = 1000
            price = self.data.close[0]
            size = amount/price

            pred_diff = abs(self.regression_line[0] - self.data.close[0])

            if pred_diff/self.data.close[0] > diff_percentage_threshold:
                parent_order, tp_order = self.order_target(size,
                                                           target_price=self.regression_line[0])

        if len(self.data) == self.data.buflen():
            self.order_history_tracker.export_result()

    def notify_order(self, order: bt.Order):

        self.order_history_tracker.notify_order(self, order)

    def notify_trade(self, trade):

        return super().notify_trade(trade)
