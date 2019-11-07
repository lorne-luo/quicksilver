import redis

import config

queue_redis = redis.StrictRedis(host=config.REDIS_HOST,
                                port=config.REDIS_PORT,
                                db=config.REDIS_DB,
                                decode_responses=True)

status_redis = queue_redis
