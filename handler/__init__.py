import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from falcon.base.market import is_market_open
from falcon.base.timeframe import PERIOD_CHOICES, get_candle_time, PERIOD_H1
from falcon.event import DebugEvent, TickPriceEvent, HeartBeatEvent, TimeFrameEvent, TradeOpenEvent, TradeCloseEvent
# from jarvis.rpyc.client import JarvisClient

import config
from redis_queue import runtime

logger = logging.getLogger(__name__)


class BaseHandler(object):
    subscription = ()

    def process(self, event, context):
        raise NotImplementedError


class DebugHandler(BaseHandler):
    subscription = [DebugEvent.type]

    def process(self, event, context):
        if event.type == DebugEvent.type and context.accounts:
            if event.action.lower() == 'account':
                for account in context.accounts:
                    account.log_account()
            elif event.action.lower() == 'trade':
                for account in context.accounts:
                    account.log_trade()
            elif event.action.lower() == 'order':
                for account in context.accounts:
                    account.log_order()
            elif event.action.lower() == 'test_message':
                print('Test message')
        else:
            print('[%s] %s' % (event.type, event.__dict__))


class EventLoggerHandler(DebugHandler):
    def __init__(self, queue, events=None, *args, **kwargs):
        super(EventLoggerHandler, self).__init__(queue, events, *args, **kwargs)

    def process(self, event, context):
        logger.info('[%s] %s' % (event.type, event.__dict__))


class TickPriceHandler(BaseHandler):
    subscription = [TickPriceEvent.type]

    def process(self, event, context):
        if config.DEBUG:
            print(event.__dict__)
        else:
            runtime.set_last_tick(event.time.strftime('%Y-%m-%d %H:%M:%S:%f'))


class HeartBeatHandler(BaseHandler):
    subscription = (HeartBeatEvent.type,)

    def process(self, event, context):
        if config.DEBUG:
            print('HeartBeat: %s' % datetime.now())
        else:
            runtime.set_heartbeat()

        if not event.counter % (120 / context.heartbeat):
            last_tick = runtime.get_last_tick()
            logger.info('[HeartBeatHandler] %s, last_tick=%s' % (event.time.strftime('%Y-%m-%d %H:%M:%S:%f'),
                                                                 last_tick))


class TimeFramePublisher(BaseHandler):
    subscription = [HeartBeatEvent.type, TickPriceEvent.type]
    candle_time = {}
    market_open = False
    timezone = 0

    def __init__(self, timezone=0):
        self.timezone = timezone
        self.market_open = is_market_open()
        now = self.get_now()
        for timeframe in PERIOD_CHOICES:
            self.candle_time[timeframe] = get_candle_time(now, timeframe)

    def is_nfp(self):
        # is day of USA NFP
        pass

    def get_now(self):
        now = datetime.utcnow() + relativedelta(hours=self.timezone)
        return now

    def process(self, event, context):
        now = self.get_now()
        for timeframe in PERIOD_CHOICES:
            new = get_candle_time(now, timeframe)
            if self.candle_time[timeframe] != new:
                event = TimeFrameEvent(timeframe, new, self.candle_time[timeframe], self.timezone, now)
                print(f'TimeFramePublisher {event.__dict__}')
                context.put_event(event)
                # print(self.candle_time[timeframe], new)
                self.candle_time[timeframe] = new

                if timeframe == PERIOD_H1:
                    last_tick = runtime.get_last_tick()
                    logger.info('TimeFrame H1 , market_open=%s, last_tick=%s' % (self.market_open, last_tick))


# class PriceAlertHandler(BaseHandler):
#     subscription = [TickPriceEvent.type, TimeFrameEvent.type, HeartBeatEvent.type]
#     resistance_suffix = ['R1', 'R2', 'R3', 'R']
#     support_suffix = ['S1', 'S2', 'S3', 'S']
#     instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'XAUUSD']
#     prices = {}
#
#     def __init__(self, queue, account=None, instruments=None, *args, **kwargs):
#         super(PriceAlertHandler, self).__init__(queue)
#         if instruments:
#             self.instruments = [get_mt4_symbol(ins) for ins in instruments]
#         self.update_price()
#
#     def process(self, event):
#         if event.type == TickPriceEvent.type:
#             if event.instrument in self.instruments:
#                 self.price_alert(event)
#         elif event.type == TimeFrameEvent.type:
#             if event.timeframe == PERIOD_D1:
#                 self.reset_rs(event)
#         elif event.type == HeartBeatEvent.type:
#             if not event.counter % (settings.HEARTBEAT / settings.LOOP_SLEEP):
#                 self.update_price()
#
#     def update_price(self):
#         for ins in self.instruments:
#             for suffix in self.resistance_suffix + self.support_suffix:
#                 key = '%s_%s' % (ins, suffix)
#                 self.prices[key] = price_redis.get(key)
#
#     def price_alert(self, event):
#         symbol = get_mt4_symbol(event.instrument)
#         for resistance_level in self.resistance_suffix:
#             key = '%s_%s' % (symbol, resistance_level)
#             resistance = self.prices.get(key)
#             if not resistance:
#                 continue
#
#             price = Decimal(str(resistance))
#             if event.bid > price:
#                 msg = '%s up corss %s = %s' % (symbol, resistance_level, price)
#                 logger.info('[PRICE_ALERT] %s' % msg)
#                 send_to_admin(msg)
#                 tg.send_me(msg)
#                 self.remove(key)
#
#         for support_level in self.support_suffix:
#             key = '%s_%s' % (symbol, support_level)
#             support = self.prices.get(key)
#             if not support:
#                 continue
#
#             price = Decimal(str(support))
#             if event.ask < price:
#                 msg = '%s down corss %s = %s' % (symbol, support_level, price)
#                 logger.info('[PRICE_ALERT] %s' % msg)
#                 send_to_admin(msg)
#                 tg.send_me(msg)
#                 self.remove(key)
#
#     def remove(self, key):
#         price_redis.delete(key)
#         self.prices.pop(key)
#
#     def reset_rs(self, event):
#         suffix = self.resistance_suffix + self.support_suffix
#         suffix.remove('R')
#         suffix.remove('S')
#         for instrument in self.instruments:
#             for su in suffix:
#                 key = '%s_%s' % (instrument, su)
#                 self.remove(key)
#                 # todo reset resistance and support


class TelegramHandler(BaseHandler):
    subscription = [TradeOpenEvent.type, TradeCloseEvent.type]

    def __init__(self):
        self.client = JarvisClient(port=config.JARVIS_PORT, hostname=config.JARVIS_HOST)

    # def process(self, event, context):
    #     self.client.telegram_jarvis(event.to_text())
