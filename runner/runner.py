import json
import logging
import sys
import time
import traceback

import config
from handler.base import BaseHandler
from redis_queue.redis import RedisQueue

logger = logging.getLogger(__name__)


class BaseRunner(object):

    def __init__(self, queue_name, account, *args, **kwargs):
        self.handlers = []
        self.running = False
        self.halt = False
        self.loop_interval = 1
        self.account = account
        self.queue_name = queue_name

    def register(self, *args):
        """register handlers"""
        for handler in args:
            if isinstance(handler, BaseHandler):
                self.handlers.append(handler)

    def launch(self):
        """before actcul run event bus"""
        logger.info('%s statup.' % self.__class__.__name__)
        logger.info('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))
        self.running = True
        self.halt = False

    def loop_start(self):
        pass

    def loop_end(self):
        pass

    def yield_event(self, block=False):
        raise NotImplementedError

    def put_event(self, event):
        raise NotImplementedError

    def handle_event(self, handler, event):
        """process event by single handler"""
        try:
            return handler.process(event, self)
        except Exception as ex:
            logger.error('[EVENT_PROCESS] %s, event=%s' % (ex, event.__dict__))
            # print trace stack
            extracted_list = traceback.extract_tb(ex.__traceback__)
            for item in traceback.StackSummary.from_list(extracted_list).format()[:8]:
                logger.error(item.strip())
            self.handle_error(ex)

    def stop(self):
        del self.queue
        self.running = False
        sys.exit(0)


class ReisQueueRunner(BaseRunner):
    """Base runner"""

    def __init__(self, queue_name, account, *args, **kwargs):
        super(ReisQueueRunner, self).__init__(queue_name, account, *args, **kwargs)
        self.queue = RedisQueue(queue_name)

    def run(self):
        self.launch()

        while self.running:
            self.loop_start()
            if not self.halt:
                event = self.yield_event()
                if not event:
                    break
                self.loop_handlers(event)
            else:
                time.sleep(10)

            time.sleep(self.loop_interval)

            self.loop_end()
        raise NotImplementedError

    def yield_event(self, block=False):
        try:
            data = self.queue.get(block)
            if data:
                data = json.loads(data)
                return Event.from_dict(data)
        except queue.Empty:
            return None
        except Exception as ex:
            logger.error('queue get error=%s' % ex)
        return None

    def put_event(self, event):
        try:
            data = json.dumps(event.to_dict())
            self.queue.put(data)
        except Exception as ex:
            logger.error('queue put error=%s' % ex)

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

    def handle_error(self, ex):
        pass

    def print(self):
        print(self.handlers)


class TestRedisRunner(ReisQueueRunner):
    """Test runner with redis"""
    def __init__(self, queue, heartbeat=5, *args, **kwargs):
        super(TestRedisRunner, self).__init__(queue)
        self.heartbeat = heartbeat or 5  # seconds
        self.register(*args)

    def run(self):
        logger.info('%s statup.' % self.__class__.__name__)
        logger.info('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))
        logger.info('\n')

        while True:
            try:
                event = self.yield_event(False)
            except queue.Empty:
                time.sleep(self.heartbeat)
                self.put_event(HeartBeatEvent())
            else:
                if event:
                    if config.DEBUG:
                        logger.info("New %sEvent: %s", (event.type, event.__dict__))
                    else:
                        logger.debug("New %sEvent: %s", (event.type, event.__dict__))

                    self.loop_handlers(event)


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
    from event.handler import *
    import queue

    q = queue.Queue(maxsize=2000)
    d = DebugHandler(q)
    t = TimeFrameTicker(q)
    r = TestRedisRunner(q, 5, d, t)
    r.run()
