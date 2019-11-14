import logging
from decimal import Decimal
from queue import Queue

from falcon.base.time import str_to_datetime
from falcon.base.timeframe import PERIOD_M1
from falcon.event import TickPriceEvent

from backtest.handler import BacktestTickPriceHandler
from base.strategy import StrategyBase
from handler import TickPriceHandler
from runner.runner import MemoryQueueRunner

logger = logging.getLogger(__name__)


class BacktestRunner(MemoryQueueRunner):
    """Backtest runner"""
    print_step = 10
    prices = []
    line_count = 0
    loop_sleep = 0
    empty_sleep = 0
    heartbeat = 0

    def create_queue(self, queue_name):
        self.test_data_path = queue_name
        self.data_file_handler = open(self.test_data_path)
        return Queue()

    def yield_event(self, block=False):
        line = self.data_file_handler.readline()
        if line:
            self.line_count += 1
            if not self.line_count % self.print_step:
                print(f'#{self.line_count} TickPriceEvent')
            return self.line_to_event(line)
        else:
            self.stop()

        return None

    def line_to_event(self, line):
        """
        GBP/USD,20181202 22:01:01.100,1.27211,1.27656
        to a TickPriceEvent
        """
        fields = line.split(',')

        event = TickPriceEvent(broker='Back test broker',
                               instrument=fields[0],
                               time=str_to_datetime(fields[1], '%Y%m%d %H:%M:%S.%f'),
                               bid=Decimal(fields[2]),
                               ask=Decimal(fields[3]))
        return event

    def loop_handlers(self, event):
        """loop handlers to process event"""
        re_put = False
        for handler in self.handlers:
            if '*' in handler.subscription:
                result = self.handle_event(handler, event)
                re_put = result or re_put
                continue
            elif event.type in handler.subscription:
                result = self.handle_event(handler, event)
                re_put = result or re_put
        if re_put:
            if event.tried > 10:
                logger.error('[EVENT_RETRY] tried to many times abort, event=%s' % event)
            else:
                event.tried += 1
                self.put_event(event)

    def stop(self):
        self.data_file_handler.close()
        print(f'{self.line_count} lines processed.')
        super(BacktestRunner, self).stop()


if __name__ == '__main__':
    """
    run example:
    python -m backtest.runner
    """


    class DebugTickPriceHandler(TickPriceHandler):
        subscription = [TickPriceEvent.type]

        def process(self, event, context):
            print(f'# BacktestTickPriceHandler')


    class DebugStrategy(StrategyBase):
        timeframes = [PERIOD_M1]
        subscription = [TickPriceEvent.type]
        pairs = ['GBPUSD']

        def signal_pair(self, symbol, event, context):
            pass


    runner = BacktestRunner('./tests/test_tick.txt', [],
                            # DebugTickPriceHandler(),
                            DebugStrategy())
    runner.print_step = 1
    print(runner.get_handler_by_type(DebugTickPriceHandler))
    print(runner.strategies)
    runner.run()
