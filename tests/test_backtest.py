from datetime import datetime, timedelta
from decimal import Decimal

from falcon.base.order import OrderSide
from falcon.base.time import str_to_datetime
from falcon.base.timeframe import PERIOD_M1, PERIOD_M30, PERIOD_H4, PERIOD_H1, PERIOD_D1
from falcon.event import TickPriceEvent

from backtest.account import BacktestAccount
from backtest.order import BacktestOrder
from backtest.runner import BacktestRunner


def test_order():
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


def test_account():
    account = BacktestAccount()
    tick = TickPriceEvent(broker='Back test broker',
                          instrument='EURUSD',
                          time=datetime.now(),
                          bid=Decimal('1.1332'),
                          ask=Decimal('1.1333'))

    account.market_order('EURUSD', OrderSide.BUY, 0.1, take_profit=33, stop_loss=22, trailing_pip=20, tick=tick)
    assert len(account.list_order()) == 1

    order = account.get_order('1')
    assert isinstance(order, BacktestOrder)
    assert order.open_price == tick.ask
    assert order.side == OrderSide.BUY
    assert order.lots == Decimal('0.1')
    assert order.take_profit == Decimal('1.1366')
    assert order.stop_loss == Decimal('1.1311')
    assert order.open_time == tick.time
    assert order.is_closed == False
    assert order.max_profit == 0
    assert order.min_profit == 0

    account.market_order('EURUSD', OrderSide.SELL, 0.1, take_profit=33, stop_loss=22, trailing_pip=20, tick=tick)
    order2 = account.get_order('2')
    assert order2.open_price == tick.bid
    assert order2.side == OrderSide.SELL
    assert order2.take_profit == Decimal('1.1299')
    assert order2.stop_loss == Decimal('1.1354')
    assert order2.open_time == tick.time
    assert order2.is_closed == False

    tick2 = TickPriceEvent(broker='Back test broker',
                           instrument='EURUSD',
                           time=datetime.now() + timedelta(seconds=2),
                           bid=Decimal('1.1336'),
                           ask=Decimal('1.1338'))

    order.update_price(tick2)
    assert order.current_time == tick2.time
    assert order.current_price == tick2.bid
    assert order.max_profit == 3
    assert order.min_profit == 0

    tick3 = TickPriceEvent(broker='Back test broker',
                           instrument='EURUSD',
                           time=datetime.now() + timedelta(seconds=4),
                           bid=Decimal('1.1300'),
                           ask=Decimal('1.1301'))

    order.update_price(tick3)
    assert order.current_time == tick3.time
    assert order.current_price == tick3.bid
    assert order.max_profit == 3
    assert order.min_profit == -33

    order.close(tick3)
    assert order.close_time == tick3.time
    assert order.close_price == tick3.bid
    assert order.total_time.seconds == 4
    assert order.profit_time.seconds == 2
    assert order.profit_time_percent == 50
    assert order.profit == -33


def test_runner():
    test_time_format = '%Y%m%d %H:%M:%S.%f'
    account = BacktestAccount()
    tick = TickPriceEvent(broker='Back test broker',
                          instrument='GBPUSD',
                          time=str_to_datetime('20181203 04:41:31.577', test_time_format),
                          bid=Decimal('1.27724'),
                          ask=Decimal('1.27732'))

    account.market_order('GBPUSD', OrderSide.BUY, 0.1, take_profit=33, stop_loss=22, trailing_pip=20, tick=tick)

    runner = BacktestRunner('./tests/test_tick.csv', [account])
    runner.run()
    assert runner.line_count == 49
    order = account.get_order('1')

    assert order.open_time.strftime(test_time_format) == '20181203 04:41:31.577000'
    assert order.current_time.strftime(test_time_format) == '20181203 04:43:32.577000'
    assert order.current_price == Decimal('1.27728')
    assert order.open_price == Decimal('1.27732')
    assert order.profit_time_percent > 1
    assert order.profit_time.seconds > 1
    assert order.current_time - order.open_time == order.total_time
    assert order.max_profit > 0
    assert order.min_profit < 0

    assert len(runner.ohlc[PERIOD_M1]) == 3
    assert len(runner.ohlc[PERIOD_M30]) == 1
    assert len(runner.ohlc[PERIOD_H4]) == 1
    assert len(runner.ohlc[PERIOD_H1]) == 1
    assert len(runner.ohlc[PERIOD_D1]) == 1
