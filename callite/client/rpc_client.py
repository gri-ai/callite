import os
import pickle
import threading

from callite.shared.redis_connection import RedisConnection
from callite.rpctypes.request import Request


TIMEOUT = int(os.getenv('EXECUTION_TIMEOUT', '30'))


def check_and_return(response):
    if response.status == 'error':
        raise Exception(response.error)

    return response.data


class RPCClient(RedisConnection):

    def __init__(self, conn_url: str, service: str, execution_timeout=TIMEOUT, *args, **kwargs) -> None:
        super().__init__(conn_url, service, *args, **kwargs)
        self._request_pool = {}
        self._pool_lock = threading.Lock()
        self._subscribe_thread = None
        self._subscribe()
        self.execution_timeout = execution_timeout

    def _subscribe(self):
        self.channel = self._rds.pubsub()
        self.channel.subscribe(f'{self._queue_prefix}/response/{self._connection_id}')
        self._subscribe_thread = threading.Thread(target=self._pull_from_redis, daemon=True)
        self._subscribe_thread.start()

    def _pull_from_redis(self):
        while self._running:
            message: dict | None = self.channel.get_message(ignore_subscribe_messages=True, timeout=100)
            if not message: continue
            if not message['data']: continue
            data = pickle.loads(message['data'])
            request_guid = data['request_id']
            with self._pool_lock:
                if request_guid not in self._request_pool:
                    continue
                lock, _ = self._request_pool.pop(request_guid)
                self._request_pool[request_guid] = (lock, data)
            lock.release()

    def publish(self, method: str, *args, **kwargs):
        request = Request(method, self._connection_id, None, *args, **kwargs)
        pickled_request = pickle.dumps(request)
        self._rds.xadd(f'{self._queue_prefix}/request/{self._service}', {'data': pickled_request})

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
        self._logger.debug(f'Executing method: {method}')
        request = Request(method, self._connection_id, None, *args, **kwargs)
        request_uuid = request.request_id

        request_lock = threading.Lock()
        with self._pool_lock:
            self._request_pool[request_uuid] = (request_lock, None)
        self._logger.debug(f'Acquiring lock: {request_uuid}')
        request_lock.acquire()
        pickled_request = pickle.dumps(request)
        self._logger.debug(f'Publishing request: {request_uuid}')
        self._rds.xadd(f'{self._queue_prefix}/request/{self._service}', {'data': pickled_request})

        self._logger.debug(f'Waiting for response: {request_uuid}')
        lock_success = request_lock.acquire(timeout=self.execution_timeout)
        self._logger.debug(f'Response result: {request_uuid}')
        with self._pool_lock:
            lock, data = self._request_pool.pop(request_uuid)
        if lock_success:
            self._logger.debug(f'Releasing lock: {request_uuid}')
            response = data['data']
            return check_and_return(response)
        self._logger.debug(f'Lock timeout: {request_uuid}')
        raise Exception('Timeout')

    def close(self) -> None:
        self._running = False
        if self._subscribe_thread:
            self._subscribe_thread.join()
        super().close()
