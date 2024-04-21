import json
import threading
import logging

from callite.shared.redis_connection import RedisConnection
from callite.rpctypes.request import Request


# import pydevd_pycharm
# pydevd_pycharm.settrace('host.docker.internal', port=4444, stdoutToServer=True, stderrToServer=True)


class RPCClient(RedisConnection):

    def __init__(self, conn_url: str, service: str, *args, **kwargs) -> None:
        super().__init__(conn_url, service, *args, **kwargs)
        self._request_pool = {}
        self._subscribe()
        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(logging.StreamHandler())
        self._logger.setLevel(logging.INFO)

    def _subscribe(self):
        self.channel = self._rds.pubsub()
        self.channel.subscribe(f'{self._queue_prefix}/response/{self._connection_id}')
        thread = threading.Thread(target=self._pull_from_redis, daemon=True)
        thread.start()

    def _pull_from_redis(self):
        def _on_delivery(message):
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
            _on_delivery(message)


    def execute(self, method: str, *args, **kwargs) -> dict:
        request = Request(method, self._connection_id, None, *args, **kwargs)
        request_uuid = request.request_id

        request_lock = threading.Lock()
        self._request_pool[request_uuid] = (request_lock, None)
        request_lock.acquire()

        self._rds.xadd(f'{self._queue_prefix}/request/{self._service}', {'data': json.dumps(request.payload_json())})
        self._logger.info(f"Sent message {request_uuid} to {self._queue_prefix}/request/{self._service}")
        # TODO: parameterize timeout
        lock_success = request_lock.acquire(timeout=30)
        lock, response = self._request_pool.pop(request_uuid)
        if lock_success:
            self._logger.info(f"Received response to message {request_uuid} {type(response['data'])}")
            return response['data']
        raise Exception('Timeout')
