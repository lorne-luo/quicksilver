import logging

from redis_queue.queue import RedisQueue
from runner.base import BaseRunner

logger = logging.getLogger(__name__)


class ReisQueueRunner(BaseRunner):
    """Base runner"""

    def create_queue(self, queue_name):
        return RedisQueue(queue_name)


class TestRedisRunner(ReisQueueRunner):
    """Test runner with redis"""

    def loop_handlers(self, event):
        print(f'Process event, {event.__dict__}')
        super(TestRedisRunner, self).loop_handlers(event)

    def put_event(self, event):
        print(f'Put event = {event.__dict__}')
        super(TestRedisRunner, self).put_event(event)


class StreamRunnerBase(ReisQueueRunner):
    broker = ''
    account = None

    def __init__(self, queue, pairs, *args, **kwargs):
        super(StreamRunnerBase, self).__init__(queue)
        if args:
            self.register(*args)
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()

    def _set_up_prices_dict(self):
        prices_dict = dict(
            (k, v) for k, v in [
                (p, {"bid": None, "ask": None, "time": None, "spread": None}) for p in self.pairs
            ]
        )

        return prices_dict


if __name__ == '__main__':
    # python -m event.runner
    from handler import *

    r = TestRedisRunner('test_runner', [],
                        HeartBeatHandler(),
                        TimeFramePublisher(timezone=0))
    r.run()
