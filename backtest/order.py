from datetime import timedelta
from decimal import Decimal

from falcon.base.order import OrderSide, OrderType
from falcon.base.price import profit_pip, calculate_price, pip
from hulk.base.models import OrderBase


class BacktestOrder:

    def __init__(self, order_id, instrument, open_time, side, lots, open_price, take_profit, stop_loss):
        self.order_type = OrderType.MARKET
        self.order_id = order_id
        self.instrument = instrument
        self.open_time = open_time
        self.side = side
        self.lots = lots
        self.open_price = open_price
        self.order_id = order_id
        self.take_profit = take_profit
        self.stop_loss = stop_loss

        self.current_price = self.open_price
        self.current_time = self.open_time
        self.close_price = None
        self.close_time = None
        self.note = ''
        self.max_profit = 0
        self.min_profit = 0
        self.profit_time = timedelta(seconds=0)

    @property
    def is_closed(self):
        return bool(self.close_price)

    @property
    def pips(self):
        if self.close_price:
            return profit_pip(self.instrument, self.open_price, self.close_price, self.side)
        return profit_pip(self.instrument, self.open_price, self.current_price, self.side)

    @property
    def profit(self):
        if self.is_closed:
            return self.pips * self.lots * 10
        return None

    def update_price(self, tick):
        if not tick.instrument == self.instrument:
            return
        # todo update max_profit, min_profit, profit_time

        if self.side == OrderSide.BUY:
            self.current_price = tick.bid
            profit = self.current_price - self.open_price
        elif self.side == OrderSide.SELL:
            self.current_price = tick.ask
            profit = self.open_price - self.current_price
        else:
            raise Exception(f'Side {self.side} incorrect.')

        profit = pip(self.instrument, profit)
        if profit > self.max_profit:
            self.max_profit = profit
        elif profit < self.min_profit:
            self.min_profit = profit

        if profit > 0:
            self.profit_time += tick.time - self.current_time
        self.current_time = tick.time

    @property
    def total_time(self):
        return self.current_time - self.open_time

    @property
    def profit_time_percent(self):
        percent = self.profit_time / self.total_time
        percent = Decimal(str(percent)) * 100
        return percent.quantize(Decimal('0.01'))

    def close(self, tick):
        if not tick.instrument == self.instrument:
            return
        self.close_time = tick.time
        if self.side == OrderSide.BUY:
            self.close_price = tick.bid
        elif self.side == OrderSide.SELL:
            self.close_price = tick.ask


class BacktestOrderMixin(OrderBase):
    _order_sequence = 0

    def _generate_order_id(self):
        self._order_sequence += 1
        return self._order_sequence

    def list_order(self, ids=None, state=None, instrument=None, count=20, beforeID=None):
        return self.orders

    def list_pending_order(self):
        return {}

    def get_order(self, order_id):
        return self.orders.get(int(order_id))

    def limit_order(self, instrument, side, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        raise NotImplementedError

    def limit_buy(self, instrument, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        return self.limit_order(instrument=instrument, side=OrderSide.BUY, price=price,
                                lots=lots,
                                take_profit=take_profit,
                                stop_loss=stop_loss,
                                trailing_pip=trailing_pip,
                                **kwargs)

    def limit_sell(self, instrument, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        return self.limit_order(instrument=instrument, side=OrderSide.SELL, price=price,
                                lots=lots,
                                take_profit=take_profit,
                                stop_loss=stop_loss,
                                trailing_pip=trailing_pip,
                                **kwargs)

    def stop_order(self, instrument, side, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        raise NotImplementedError

    def stop_buy(self, instrument, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        """buy shortcut for stop order"""
        return self.stop_order(instrument=instrument, side=OrderSide.BUY, price=price, lots=lots,
                               take_profit=take_profit,
                               stop_loss=stop_loss, trailing_pip=trailing_pip, **kwargs)

    def stop_sell(self, instrument, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        """sell shortcut for stop order"""
        return self.stop_order(instrument=instrument, side=OrderSide.SELL, price=price, lots=lots,
                               take_profit=take_profit, stop_loss=stop_loss, trailing_pip=trailing_pip, **kwargs)

    def market_order(self, instrument, side, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        order_id = self._generate_order_id()
        tick = kwargs.get('tick')
        open_time = tick.time
        open_price = tick.ask if side == OrderSide.BUY else tick.bid

        lots = Decimal(str(lots))

        if '.' not in str(take_profit):
            # using pips
            take_profit = calculate_price(open_price, side, take_profit, instrument)
        if '.' not in str(stop_loss):
            # using pips
            stop_loss = calculate_price(open_price, OrderSide.reverse(side), stop_loss, instrument)

        order = BacktestOrder(order_id, instrument, open_time, side, lots, open_price, take_profit, stop_loss)

        self.orders[order_id] = order
        return order

    def take_profit(self, trade_id, price, **kwargs):
        raise NotImplementedError

    def stop_loss(self, trade_id, price, **kwargs):
        raise NotImplementedError

    def trailing_stop_loss(self, trade_id, pips, **kwargs):
        raise NotImplementedError

    def cancel_order(self, order_id, **kwargs):
        raise NotImplementedError

    def close_order(self, order_id, lots=None, percent=None, **kwargs):
        tick = kwargs.get('tick')
        order = self.orders.get(order_id)
        if order:
            order.close(tick)
