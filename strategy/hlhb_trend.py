import logging

import talib as ta
from falcon.event import SignalEvent,  TimeFrameEvent, OrderHoldingEvent, StartUpEvent
from falcon.base.order import OrderSide, SignalAction
from falcon.base.timeframe import PERIOD_H1


from base.helper import check_cross
from base.strategy import StrategyBase


logger = logging.getLogger(__name__)


class HLHBTrendStrategy(StrategyBase):
    """
    Basically, I’m catching trends whenever the 5 EMA crosses above or below the 10 EMA.
    A trade is only valid if RSI crosses above or below the 50.00 mark when the signal pops up.
    And in this version, I’m adding ADX>25 to weed out the fakeouts.

    As for stops, I’ll continue to use a 150-pip trailing stop and a profit target of 400 pips.
    This might change in the future, but I’ll stick to this one for now.

    https://www.babypips.com/trading/forex-hlhb-system-20190128
    """
    name = 'HLHB Trend'
    version = '0.1'
    magic_number = '20190304'
    source = 'https://www.babypips.com/trading/forex-hlhb-system-20190128'

    timeframes = [PERIOD_H1]
    weekdays = [0, 1, 2, 3, 4]
    hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]  # GMT hour

    subscription = [TimeFrameEvent.type, OrderHoldingEvent.type, StartUpEvent.type]

    pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD']
    params = {'short_ema': 5,
              'long_ema': 10,
              'adx': 14,
              'rsi': 14, }

    take_profit = 50
    stop_loss = 30
    trailing_stop = 40

    def signal_pair(self, symbol):
        short_ema = self.params.get('short_ema')
        long_ema = self.params.get('long_ema')
        adx_period = self.params.get('adx')
        rsi = self.params.get('rsi')

        candles = self.data_reader.get_candle(symbol, PERIOD_H1, count=50, fromTime=None, toTime=None,
                                              price_type='M', smooth=False)

        adx = ta.ADX(candles['askhigh'], candles['bidlow'], candles['bidclose'], timeperiod=adx_period)
        ema_short = ta.EMA(candles['bidclose'], timeperiod=short_ema)
        ema_long = ta.EMA(candles['bidclose'], timeperiod=long_ema)
        mean = (candles['askhigh'] + candles['bidlow']) / 2
        rsi = ta.RSI(mean, timeperiod=rsi)
        # upper, middle, lower = ta.BBANDS(h1_candles['close'], matype=MA_Type.T3)

        if self.can_open():
            self.open(symbol, ema_short, ema_long, adx, rsi)
        self.close(symbol, ema_short, ema_long, adx, rsi)

    def open(self, symbol, ema_short, ema_long, adx, rsi):
        if adx[-1] <= 25:
            return

        side = check_cross(ema_short, ema_long, shift=0)
        logger.info('%s@%s param=%s, %0.5f, %0.5f, %0.2f, %0.2f' % (
            self.name, symbol, side, ema_short[-1], ema_long[-1], adx[-1], rsi[-1]))

        event = None
        if side == OrderSide.BUY and 70 > rsi[-1] > 50:
            event = SignalEvent(SignalAction.OPEN, self.name, self.version, self.magic_number,
                                symbol, side, trailing_stop=self.trailing_stop,
                                take_profit=self.take_profit, stop_loss=self.stop_loss)
            self.send_event(event)
        elif side == OrderSide.SELL and 50 > rsi[-1] > 30:
            event = SignalEvent(SignalAction.OPEN, self.name, self.version, self.magic_number,
                                symbol, side, trailing_stop=self.trailing_stop,
                                take_profit=self.take_profit, stop_loss=self.stop_loss)
            self.send_event(event)
        if event:
            logger.info('[ORDER_%s] %s@%s %s, param=%0.5f, %0.5f, %0.2f, %0.2f' % (
                event.action, event.strategy, event.instrument, event.to_dict(), ema_short[-1],
                ema_long[-1], adx[-1], rsi[-1]))

        return side

    def close(self, symbol, ema_short, ema_long, adx, rsi):
        pass
