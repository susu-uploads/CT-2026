"""Worker RQ; потерянные задания помечаются failed без повторения."""
import os
from redis import Redis
from rq import Worker

if __name__ == '__main__':
    connection = Redis.from_url(os.environ.get('REDIS_URL', 'redis://redis:6379/0'))
    Worker(['csv'], connection=connection, maintenance_interval=5).work()
