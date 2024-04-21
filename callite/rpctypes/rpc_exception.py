from callite.rpctypes.request import Request


class RPCException(Exception):

    def __init__(self, message, ex):
        super().__init__(message)
        self.message = message
        self.request: Request | None = None
        self.inner_exception = ex