from redis_queue.base import QueueBase


class BaseHandler(QueueBase):
    subscription = []
    account = None

    def __init__(self, queue, account=None, *args, **kwargs):
        super(BaseHandler, self).__init__(queue)
        self.account = account

    def process(self, event):
        raise NotImplementedError
