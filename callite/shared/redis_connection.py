import logging
import uuid
import redis
from abc import ABC



class RedisConnection(ABC):
    def __init__(self, conn_url: str, service: str, *args, **kwargs):
        self._methods = {}
        self._service = service
        self._running = True
        self._running_threads = []
        self._connection_id = uuid.uuid4().hex
        self._queue_prefix = kwargs.get('queue_prefix', '/callite')
        self._rds = redis.Redis.from_url(conn_url)
        self._rds.ping()
        self._logger = logging.getLogger(f'RPC{service}')
        self._logger.setLevel(logging.INFO)

    def close(self) -> None:
        self._running = False