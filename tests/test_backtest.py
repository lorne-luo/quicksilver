from datetime import datetime
from decimal import Decimal

from falcon.base.order import OrderSide
from falcon.event import TickPriceEvent

from backtest.account import BacktestAccount
from backtest.order import BacktestOrder


def test_testback():
    order = BacktestOrder(order_id=1, instrument='EURUSD', open_time=datetime.now(), side=OrderSide.BUY,
                          lots=0.1, open_price=Decimal('1.3245'),
                          take_profit=Decimal('1.3345'), stop_loss=Decimal('1.3145'))
    assert order.pips == 0

    order.current_price = Decimal('1.32552')
    assert order.pips == Decimal('10.2')

    order.close_price = None
    assert not order.is_closed

    order.close_price = Decimal('1.32552')
    assert order.is_closed


def test_order():
    account = BacktestAccount()
    tick = TickPriceEvent(broker='Back test broker',
                          instrument='EURUSD',
                          time=datetime.now(),
                          bid=Decimal('1.1333'),
                          ask=Decimal('1.1332'))

    account.market_order('EURUSD', OrderSide.BUY, 0.1, take_profit=33, stop_loss=22, trailing_pip=20,
                         tick=tick)
    assert len(account.list_order()) == 1

    order = account.get_order('1')
    assert isinstance(order, BacktestOrder)
    assert order.open_price == tick.ask
    assert order.side == OrderSide.BUY
    assert order.lots == Decimal('0.1')
    assert order.take_profit == Decimal('1.1365')
    assert order.stop_loss == Decimal('1.1310')
    assert order.open_time == tick.time

    account.market_order('EURUSD', OrderSide.SELL, 0.1, take_profit=33, stop_loss=22, trailing_pip=20,
                         tick=tick)
    order2 = account.get_order('2')
    assert order2.open_price == tick.bid
    assert order2.side == OrderSide.SELL
    assert order2.take_profit == Decimal('1.1300')
    assert order2.stop_loss == Decimal('1.1355')
    assert order2.open_time == tick.time
