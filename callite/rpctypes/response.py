import json

from callite.rpctypes.message_base import MessageBase


class Response(MessageBase):
    def __init__(self, method: str, message_id = None, status = None, error = None, data = None):
        super(Response, self).__init__(method, message_id)
        self.data = data
        self.status = status
        self.error = error


    def response_json(self):
        # get the json string of the current instance
        response_data = json.dumps(self).encode('utf-8')
        return response_data

    def __str__(self):
        return "Response: message_id: %s, response_data: %s" % (self.message_id, self.data)