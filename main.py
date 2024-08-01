from concurrent.futures import thread

from callite.server import RPCServer


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
            return a + b

        @self.rpc_service.register
        def subtract(a, b):
            return a - b

        self.rpc_service.run_forever()

if __name__ == "__main__":
    Main().run()
