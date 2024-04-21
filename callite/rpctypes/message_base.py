class MessageBase(object):
    def __init__(self, method, message_id):
        self.message_id: str = message_id
        self.method: str = method

    def __str__(self):
        return "MessageBase: message_id: %s, method: %s, message_data: %s %s" % (self.message_id, self.method, self.args, self.kwargs)