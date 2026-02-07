import logging
import os
import uuid
import redis
from abc import ABC


class RedisConnection(ABC):
    _log_level_default = 'INFO'

    def __init__(self, conn_url: str, service: str, *args, **kwargs):
        log_level_str = os.getenv('LOG_LEVEL', self._log_level_default)
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)

        self._logger = logging.getLogger(type(self).__module__)
        if not self._logger.handlers:
            self._logger.addHandler(logging.StreamHandler())
        self._logger.setLevel(log_level)

        self._service = service
        self._running = True
        self._connection_id = uuid.uuid4().hex
        self._queue_prefix = kwargs.get('queue_prefix', '/callite')
        self._conn_url = conn_url
        self._connect()

    def _connect(self):
        self._rds = redis.Redis.from_url(self._conn_url)

    def close(self) -> None:
        self._running = False
