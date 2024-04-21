from callite.server import RPCServer


class Main:
    def __init__(self):
        self.service = "service"
        self.redis_url = "redis://redis:6379/0"
        self.rpc_service = RPCServer(self.redis_url, self.service)

    def run(self):

        @self.rpc_service.register
        def healthcheck():
            return "OK"

        self.rpc_service.run_forever()

if __name__ == "__main__":
    Main().run()
