import uuid

from callite.rpctypes.message_base import MessageBase


class Request(MessageBase):
    def __init__(self, method:str, client_id:str, message_id:str = None, *args, **kwargs):
        super(Request, self).__init__(message_id)
        self.request_id = message_id if message_id else uuid.uuid4().hex
        self.method = method
        self.client_id = client_id
        self.args = list(args)
        self.kwargs = kwargs


    def __str__(self):
        return "Request: request_id: %s, method: %s" % (self.request_id, self.method)