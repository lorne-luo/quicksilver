from falcon.base.order import OrderSide, OrderType, lots_to_units
from falcon.base.price import profit_pip
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
        self.close_price = None
        self.close_time = None
        self.note = ''

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


class BacktestOrderMixin(OrderBase):
    _order_sequence = 0
    _orders = {}

    def generate_order_id(self):
        self._order_sequence += 1
        return self._order_sequence

    def list_order(self, ids=None, state=None, instrument=None, count=20, beforeID=None):
        raise NotImplementedError

    def list_pending_order(self):
        raise NotImplementedError

    def get_order(self, order_id):
        return self._orders

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
        raise NotImplementedError

    def take_profit(self, trade_id, price, **kwargs):
        raise NotImplementedError

    def stop_loss(self, trade_id, price, **kwargs):
        raise NotImplementedError

    def trailing_stop_loss(self, trade_id, pips, **kwargs):
        raise NotImplementedError

    def cancel_order(self, order_id, **kwargs):
        raise NotImplementedError
