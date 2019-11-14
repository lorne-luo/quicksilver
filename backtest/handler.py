from falcon.event import TickPriceEvent

from handler import TickPriceHandler


class BacktestTickPriceHandler(TickPriceHandler):
    subscription = [TickPriceEvent.type]

    def process(self, event, context):
        print('# BacktestTickPriceHandler')