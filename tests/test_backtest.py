from datetime import datetime
from decimal import Decimal

from falcon.base.order import OrderSide

from backtest.order import BacktestOrder


def test_testback():
    order = BacktestOrder(order_id=1, instrument='EURUSD', open_time=datetime.now(), side=OrderSide.BUY,
                          lots=0.1, open_price=Decimal('1.3245'),
                          take_profit=Decimal('1.3345'), stop_loss=Decimal('1.3145'))
    assert order.pips == 0

    order.current_price = Decimal('1.32552')
    assert order.pips == Decimal('10.2')
