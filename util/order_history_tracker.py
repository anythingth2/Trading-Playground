import backtrader as bt
import logging
import datetime
import pandas as pd


class OrderHistoryTracker:
    STATUS_VALUE_LABEL = {
        bt.Order.Created: 'CREATED',
        bt.Order.Accepted: 'ACCEPTED',
        bt.Order.Completed: 'EXECUTED',
        bt.Order.Rejected: 'REJECTED',
        bt.Order.Canceled: 'CANCELED'
    }

    def __init__(self, history_path, allow_order_status=None) -> None:
        self.history_path = history_path
        self.history: list = []

        if allow_order_status is None:
            allow_order_status = [bt.Order.Created, bt.Order.Accepted,
                                  bt.Order.Rejected, bt.Order.Completed,
                                  bt.Order.Canceled]
        self.allow_order_status = allow_order_status

    def notify_order(self, strategy: bt.Strategy, order: bt.Order):
        dt = bt.num2date(strategy.datas[0].datetime[0])

        if order.status not in self.allow_order_status:
            return

        status_label = self.STATUS_VALUE_LABEL.get(order.status, None)

        if order.isbuy():
            order_action_label = 'BUY'
        elif order.issell():
            order_action_label = 'SELL'

        if order.status == bt.Order.Completed:
            price = order.executed.price
        else:
            price = order.created.price

        order_history = {
            'time': dt,
            'order_ref': order.ref,
            'parent_order_ref': order.parent.ref if order.parent is not None else None,
            'action': order_action_label,
            'status': status_label,
            'order_type': order.order_type,
            'price': price,
            'position': f'{strategy.position.size:.3f}'
        }
        self.history.append(order_history)

    def export_result(self):
        df = pd.DataFrame(self.history)
        df.index.name = 'id'
        df.to_csv(self.history_path, index=True)
