from environs import Env

env = Env()

env.read_env('.env')

DEBUG = env.bool('DEBUG', True)

REDIS_HOST = env.str('REDIS_HOST', default='127.0.0.1')
REDIS_PORT = env.str('REDIS_PORT', default=6379)
REDIS_DB = env.str('REDIS_DB', default=7)

