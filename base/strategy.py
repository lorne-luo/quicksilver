import logging
from datetime import datetime

from falcon.event import TimeFrameEvent, OrderHoldingEvent, StartUpEvent, TickPriceEvent

from handler import BaseHandler

logger = logging.getLogger(__name__)


class StrategyBase(BaseHandler):
    name = None
    version = None
    magic_number = None
    source = None
    queue = None

    weekdays = [0, 1, 2, 3, 4]  # Mon to Fri
    timeframes = []
    hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]  # GMT hour

    pairs = []
    data_reader = None
    params = {}
    subscription = [TimeFrameEvent.type, OrderHoldingEvent.type]

    stop_loss = 100
    take_profit = None
    trailing_stop = None

    def __str__(self):
        return '%s v%s #%s' % (self.name, self.version, self.magic_number)

    def signal(self, event, context):
        for symbol in self.pairs:
            try:
                self.signal_pair(symbol, event, context)
            except Exception as ex:
                logger.error(f'[STRATEGY_SIGNAL] {symbol}={ex}')

    def signal_pair(self, symbol, event, context):
        raise NotImplementedError

    def can_open(self):
        now = datetime.utcnow()
        if now.weekday() not in self.weekdays:
            return False
        if now.hour not in self.hours:
            return False
        return True

    def process(self, event, context):
        if event.type == TickPriceEvent.type:
            self.signal(event, context)
        elif event.type == TimeFrameEvent.type and event.timeframe in self.timeframes:
            self.signal(event, context)
        elif event.type == OrderHoldingEvent.type:
            self.signal(event, context)
        elif event.type == StartUpEvent.type:
            self.signal(event, context)

    def send_event(self, event, context):
        context.put_event(event)
