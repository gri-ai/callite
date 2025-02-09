import logging
import os
import uuid
import redis
from abc import ABC

log_level = os.getenv('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level.upper(), 'INFO')


class RedisConnection(ABC):
    def __init__(self, conn_url: str, service: str, *args, **kwargs):
        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(logging.StreamHandler())
        self._logger.setLevel(log_level)
        self._methods = {}
        self._service = service
        self._running = True
        self._running_threads = []
        self._connection_id = uuid.uuid4().hex
        self._queue_prefix = kwargs.get('queue_prefix', '/callite')
        self._conn_url = conn_url
        self._connect()

    def _connect(self):
        self._rds = redis.Redis.from_url(self._conn_url)

    def close(self) -> None:
        self._running = False
        self._keep_alive_thread.join()
