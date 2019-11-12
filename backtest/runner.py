import logging
from decimal import Decimal
from queue import Queue

from falcon.base.time import str_to_datetime
from falcon.event import TickPriceEvent

from handler import TickPriceHandler
from runner.runner import MemoryQueueRunner

logger = logging.getLogger(__name__)


class BacktestRunner(MemoryQueueRunner):
    """Backtest runner"""

    def create_queue(self, queue_name):
        self.test_data_path = queue_name
        self.data_file_handler = open(self.test_data_path)
        self.line_count = 0
        # disable any sleep
        self.loop_sleep = 0
        self.empty_sleep = 0
        self.heartbeat = 0
        return Queue(maxsize=2000)

    def yield_event(self, block=False):
        line = self.data_file_handler.readline()
        if line:
            self.line_count += 1
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


class BacktestTickPriceHandler(TickPriceHandler):
    subscription = [TickPriceEvent.type]

    def process(self, event, context):
        print('# BacktestTickPriceHandler')
        # pprint(event.__dict__)


if __name__ == '__main__':
    # python -m event.runner

    r = BacktestRunner('./tests/test_tick.txt', [],
                       BacktestTickPriceHandler())
    r.run()
