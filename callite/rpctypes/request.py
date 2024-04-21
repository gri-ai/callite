import uuid

from callite.rpctypes.message_base import MessageBase


class Request(MessageBase):
    def __init__(self, method: str, client_id:str, message_id = None, *args, **kwargs):
        super(Request, self).__init__(method, message_id)
        self.request_id = message_id if message_id else uuid.uuid4().hex
        self.client_id = client_id
        self.args = args
        self.kwargs = kwargs

    def set_data(self, data):
        self.data = data
    def payload_json(self):
        return {
            'request_id': self.request_id,
            'client_id': self.client_id,
            'method': self.method,
            'params': {'args': self.args, 'kwargs': self.kwargs}
        }

    def __str__(self):
        return "Request: request_id: %s, method: %s" % (self.request_id, self.method)