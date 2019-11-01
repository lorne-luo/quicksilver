import json
import logging
from queue import Empty

logger = logging.getLogger(__name__)

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
