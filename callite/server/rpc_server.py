import pickle
import threading
import time
from typing import Callable

import redis
from tenacity import retry

from callite.rpctypes.response import Response
from callite.shared.redis_connection import RedisConnection


class RPCServer(RedisConnection):
    _log_level_default = 'ERROR'

    def __init__(self, conn_url: str, service: str, *args, **kwargs):
        super().__init__(conn_url, service, *args, **kwargs)
        self._registered_methods = {}
        self._xread_groupname = kwargs.get('xread_groupname', 'generic')

        self._subscribe_redis_thread = threading.Thread(target=self._subscribe_redis, daemon=True)
        self._subscribe_redis_thread.start()
        self._logger.debug("Server started")

    @property
    def _request_stream(self) -> str:
        return f'{self._queue_prefix}/request/{self._service}'

    def subscribe(self, handler: Callable, method_name: str | None = None) -> None:
        self.register_method(handler, method_name, False)

    def register(self, handler: Callable, method_name: str | None = None) -> Callable:
        return self.register_method(handler, method_name, True)

    def register_method(self, handler: Callable, method_name: str | None = None, returns: bool = True) -> Callable:
        method_name = method_name or handler.__name__
        self._logger.debug(f"Registering method {method_name}")
        self._registered_methods[method_name] = {'func': handler, 'returns': returns}
        return handler

    def run_forever(self) -> None:
        while self._running:
            time.sleep(1000000)

    @retry
    def _subscribe_redis(self):
        while self._running:
            if not self._check_connection():
                self._connect()
            self._ensure_consumer_group()
            self._logger.debug("Checking for messages")
            messages = self._read_messages_from_redis()
            self._logger.debug(f"Received {len(messages)} messages")
            self._process_messages(messages)

    def _check_connection(self):
        try:
            self._rds.ping()
            return True
        except redis.exceptions.ConnectionError:
            return False

    def _ensure_consumer_group(self):
        try:
            self._rds.xgroup_create(self._request_stream, self._xread_groupname, mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e) and "already exists" not in str(e):
                raise

    def _read_messages_from_redis(self):
        messages = self._rds.xreadgroup(
            self._xread_groupname, self._connection_id,
            {self._request_stream: '>'}, count=1, block=1000
        )
        self._logger.debug(f"{len(messages)} messages received from {self._request_stream}")
        return messages

    def _process_messages(self, messages):
        for _, message_list in messages:
            for _message in message_list:
                message_id, message_data = _message
                request = pickle.loads(message_data[b'data'])
                self._logger.info(f"Processing message {message_id} with data: {request}")
                threading.Thread(target=self._process_single, args=(request, message_id), daemon=True).start()

    def _process_single(self, request, message_id):
        self._rds.xack(self._request_stream, self._xread_groupname, message_id)

        if request.method not in self._registered_methods:
            self._logger.error(f"Method {request.method} not registered")
            error_response = Response(self._service, message_id, status='error', error=f"Method {request.method} not registered")
            payload = pickle.dumps({'data': error_response, 'request_id': request.request_id})
            self._rds.publish(f'{self._queue_prefix}/response/{request.client_id}', payload)
            return

        method_info = self._registered_methods[request.method]
        if method_info['returns']:
            response = self._call_method(request.method, message_id, *request.args, **request.kwargs)
            payload = pickle.dumps({'data': response, 'request_id': request.request_id})
            self._rds.publish(f'{self._queue_prefix}/response/{request.client_id}', payload)
            self._logger.info(f"Processed message {message_id} and response published to {self._queue_prefix}/response/{request.request_id}")
        else:
            self._call_method(request.method, message_id, *request.args, **request.kwargs)
            self._logger.info(f"Processed message {message_id} without response")

    def _call_method(self, method: str, message_id, *args, **kwargs) -> Response:
        try:
            message_id = message_id.decode('utf-8') if isinstance(message_id, bytes) else message_id
            data = self._registered_methods[method]['func'](*args, **kwargs)
            response = Response(self._service, message_id)
            response.data = data
            return response
        except Exception as e:
            self._logger.error(e)
            return Response(self._service, message_id, status='error', error=str(e))
