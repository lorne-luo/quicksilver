import json
import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from queue import Queue, Empty

from falcon.base.event import BaseEvent
from falcon.base.symbol import get_mt4_symbol
from falcon.base.time import str_to_datetime
from falcon.base.timeframe import PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_M30, PERIOD_H1, PERIOD_H4, \
    PERIOD_D1, PERIOD_W1, PERIOD_TICK
from falcon.event import TickPriceEvent

from backtest.handler import BacktestTickPriceHandler
from base.strategy import StrategyBase
from handler import TickPriceHandler
from runner.runner import MemoryQueueRunner

logger = logging.getLogger(__name__)


class BacktestRunner(MemoryQueueRunner):
    """Backtest runner"""
    print_step = 10000

    line_count = 0
    loop_sleep = 0
    empty_sleep = 0
    heartbeat = 0
    start_time = None

    handlers = [BacktestTickPriceHandler()]
    ohlc = defaultdict(list)
    max_tick_keep = 2000
    max_ohlc_keep = 50

    def __init__(self, queue_name, accounts, strategies, *args, **kwargs):
        super(BacktestRunner, self).__init__(queue_name, accounts, strategies, *args, **kwargs)
        self.start_time = datetime.utcnow()

    def create_queue(self, queue_name):
        self.test_data_path = queue_name
        self.data_file_handler = open(self.test_data_path)
        return Queue()

    def yield_event(self, block=False):
        try:
            # read from quque first
            data = self.queue.get(block)
            if data:
                data = json.loads(data)
                return BaseEvent.from_dict(data)
        except Empty:
            pass

        line = self.data_file_handler.readline()
        if line:
            self.line_count += 1
            if not self.line_count % self.print_step:
                print(f'# {self.line_count} TickPriceEvent processed.')
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
                               instrument=get_mt4_symbol(fields[0]),
                               time=str_to_datetime(fields[1], '%Y%m%d %H:%M:%S.%f'),
                               bid=Decimal(fields[2]),
                               ask=Decimal(fields[3]))
        return event

    def loop_handlers(self, event):
        """loop handlers to process event"""
        re_put = False
        for strategy in self.strategies:
            # loop strategies
            if event.type in strategy.subscription:
                self.handle_event(strategy, event)

        for handler in self.handlers:
            # loop handlers
            if '*' in handler.subscription:
                result = self.handle_event(handler, event)
                re_put = result or re_put
                continue
            elif event.type in handler.subscription:
                result = self.handle_event(handler, event)
                re_put = result or re_put

        if event.type == TickPriceEvent.type:
            for account in self.accounts:
                account.update_tick(event)

        if re_put:
            if event.tried > 10:
                logger.error('[EVENT_RETRY] tried to many times abort, event=%s' % event)
            else:
                event.tried += 1
                self.put_event(event)

    def stop(self):
        self.data_file_handler.close()
        print('=' * 40)
        print(f'{self.line_count} lines processed.')
        print(f'{len(self.ohlc[PERIOD_TICK])} lines processed.')
        # pprint(self.candle_time)
        print(
            f'PERIOD_M1={len(self.ohlc[PERIOD_M1])}\nPERIOD_M5={len(self.ohlc[PERIOD_M5])}\nPERIOD_M15={len(self.ohlc[PERIOD_M15])}\nPERIOD_M30={len(self.ohlc[PERIOD_M30])}\nPERIOD_H1={len(self.ohlc[PERIOD_H1])}\nPERIOD_H4={len(self.ohlc[PERIOD_H4])}\nPERIOD_D1={len(self.ohlc[PERIOD_D1])}\nPERIOD_W1={len(self.ohlc[PERIOD_W1])}')

        print(f'Time spend {datetime.utcnow()-self.start_time}')
        del self.queue
        self.running = False


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


    # ./tests/test_tick.csv
    # ./tests/GBPUSD-2018-12-tick.csv

    runner = BacktestRunner('./tests/test_tick.csv', [], [DebugStrategy()],
                            []  # DebugTickPriceHandler()
                            )
    print(runner.get_handler_by_type(DebugTickPriceHandler))
    print(runner.strategies)

    runner.run()
