from environs import Env

env = Env()

env.read_env('.env')

DEBUG = env.bool('DEBUG', True)

REDIS_HOST = env.str('REDIS_HOST', default='127.0.0.1')
REDIS_PORT = env.str('REDIS_PORT', default=6379)
REDIS_DB = env.str('REDIS_DB', default=7)

LOOP_SLEEP = env.float('LOOP_SLEEP', default=0.1)
EMPTY_SLEEP = env.float('EMPTY_SLEEP', default=1)
HEARTBEAT = env.float('HEARTBEAT', default=5)

JARVIS_HOST = env.str('JARVIS_HOST', default='localhost')
JARVIS_PORT = env.int('JARVIS_PORT', default=54321)
