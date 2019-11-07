"""status recorder"""
import json
from datetime import datetime
from decimal import Decimal

from falcon.base.time import str_to_datetime
from redis_queue.redis import status_redis

LAST_TICK_TIME_KEY = 'LAST_TICK_TIME'
OPENING_TRADE_COUNT_KEY = 'OPENING_TRADE_COUNT'
TICK_PRICE_SUFFIX = '_LIST'
HEARTBEAT = 'HEARTBEAT'




def set_last_tick(dt):
    if isinstance(dt, datetime):
        dt = dt.strftime('%Y-%m-%d %H:%M:%S:%f')
    status_redis.set(LAST_TICK_TIME_KEY, dt)


def get_last_tick():
    return status_redis.get(LAST_TICK_TIME_KEY)


def get_tick_price(instrument):
    key = instrument.upper() + TICK_PRICE_SUFFIX
    data = status_redis.get(key)
    if data:
        price = json.loads(data)
        if 'ask' in price:
            price['ask'] = Decimal(str(price['ask']))
        if 'bid' in price:
            price['bid'] = Decimal(str(price['bid']))
        if 'time' in price:
            price['time'] = str_to_datetime(price['time'], format='%Y-%m-%d %H:%M:%S:%f')
        return price
    return None


def set_tick_price(instrument, data):
    key = instrument.upper() + TICK_PRICE_SUFFIX
    if not isinstance(data, str):
        data = json.dumps(data)
    status_redis.set(key, data)


def set_order_count(count):
    status_redis.set(OPENING_TRADE_COUNT_KEY, count)

def set_heartbeat():
    status_redis.set(HEARTBEAT, datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f'))
