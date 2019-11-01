import json
import logging

import redis

import config

logger = logging.getLogger(__name__)


class RedisQueue(object):
    """Simple Queue with Redis Backend"""

    def __init__(self, name, db=config.REDIS_DB, host=config.REDIS_HOST,
                 port=config.REDIS_PORT):
        self.__db = redis.StrictRedis(host=host,
                                      port=port,
                                      db=db,
                                      decode_responses=True)
        self.key = 'queue:%s' % name

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def is_empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        if item:
            self.__db.rpush(self.key, item)

    def get(self, block=False, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)

        if item:
            return item
        else:
            return None

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)


class QueueBase(object):
    queue = None

    def __init__(self, queue):
        self.queue = queue

    def set_queue(self, queue):
        if not self.queue:
            self.queue = queue

    def put(self, event):
        try:
            data = json.dumps(event.to_dict())
            self.queue.put(data)
        except Exception as ex:
            logger.error('queue put error=%s' % ex)

    def get(self, block=False):
        try:
            data = self.queue.get(block)
            if data:
                data = json.loads(data)
                return Event.from_dict(data)
        except Empty:
            return None
        except Exception as ex:
            logger.error('queue get error=%s' % ex)
        return None
