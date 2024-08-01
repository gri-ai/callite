import asyncio
import json
import os
import threading
import logging

from callite.shared.redis_connection import RedisConnection
from callite.rpctypes.request import Request


# import pydevd_pycharm
# pydevd_pycharm.settrace('host.docker.internal', port=4444, stdoutToServer=True, stderrToServer=True)

LOG_LEVEL = os.getenv('LOG_LEVEL', 'ERROR')
LOG_LEVEL = getattr(logging, LOG_LEVEL.upper(), 'ERROR')
TIMEOUT = os.getenv('EXECUTION_TIMEOUT', 30)

def check_and_return(response):
    if response['status'] == 'error':
        raise Exception(response['error'])

    return response['data']


class RPCClient(RedisConnection):

    def __init__(self, conn_url: str, service: str, *args, **kwargs) -> None:
        super().__init__(conn_url, service, *args, **kwargs)
        self._request_pool = {}
        self._subscribe_thread = None
        self._subscribe()
        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(logging.StreamHandler())
        self._logger.setLevel(LOG_LEVEL)

    def _subscribe(self):
        self.channel = self._rds.pubsub()
        self.channel.subscribe(f'{self._queue_prefix}/response/{self._connection_id}')
        self._subscribe_thread = threading.Thread(target=self._pull_from_redis, daemon=True)
        self._subscribe_thread.start()

    def _pull_from_redis(self):
        async def _on_delivery(message):
            self._logger.info(f"Received message {message}")
            data = json.loads(message['data'].decode('utf-8'))
            request_guid = data['request_id']
            if request_guid not in self._request_pool:
                return
            lock, _ = self._request_pool.pop(request_guid)
            self._request_pool[request_guid] = (lock, data)
            lock.release()

        # TODO: handle poisonous messages from redis (e.g. non-json, old messages, etc.)
        while self._running:
            message: dict | None = self.channel.get_message(ignore_subscribe_messages=True, timeout=100)
            if not message: continue
            if not message['data']: continue
            asyncio.run(_on_delivery(message))


    def execute(self, method: str, *args, **kwargs) -> dict:
        """
        Executes a method on the service by sending a request through Redis.

        Args:
            method (str): The name of the method to execute.
            *args: Arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            dict: The response data from the service.

        Raises:
            Exception: If the request times out.
        Usage:
            1- With args
            >>> client = RPCClient('redis://localhost:6379', 'my_service')
            >>> result = client.execute('add_numbers', 1, 2)
            >>> print(result)
            2. With kwargs
            >>> client = RPCClient('redis://localhost:6379', 'my_service')
            >>> result = client.execute('add_numbers', num1=1, num2=2)
            >>> print(result)
        """
        request = Request(method, self._connection_id, None, *args, **kwargs)
        request_uuid = request.request_id

        request_lock = threading.Lock()
        self._request_pool[request_uuid] = (request_lock, None)
        request_lock.acquire()

        self._rds.xadd(f'{self._queue_prefix}/request/{self._service}', {'data': json.dumps(request.payload_json())})
        self._logger.info(f"Sent message {request_uuid} to {self._queue_prefix}/request/{self._service}")

        lock_success = request_lock.acquire(timeout=TIMEOUT)
        lock, response = self._request_pool.pop(request_uuid)
        if lock_success:
            self._logger.info(f"Received response to message {request_uuid} {type(response['data'])}")
            return check_and_return(response['data'])

        raise Exception('Timeout')

    def close(self) -> None:
        self._running = False
        if self._subscribe_thread:
            self._subscribe_thread.join()
        super().close()