import logging
from callite.server import RPCServer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class Main:
    def __init__(self):
        service = "service"
        redis_url = "redis://redis:6379/0"
        self.rpc_service = RPCServer(redis_url, service)

    def run(self):

        @self.rpc_service.register
        def healthcheck():
            return "OK"

        @self.rpc_service.register
        def add(a, b):
            logger.log(logging.INFO, f"Adding {a} and {b}")
            return a + b

        @self.rpc_service.register
        def subtract(a, b):
            logger.log(logging.INFO, f"Subtracting {a} and {b}")
            return a - b

        @self.rpc_service.subscribe
        def log(message):
            logger.log(logging.INFO, message)

        self.rpc_service.run_forever()

if __name__ == "__main__":
    Main().run()
