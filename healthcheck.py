import time
import logging

from callite.client.rpc_client import RPCClient


class Healthcheck():
    def __init__(self):
        self.status = "OK"
        self.r = RPCClient("redis://redis:6379/0", "service")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())

    def get_status(self):
        # Get high resolution current time
        start = time.perf_counter()
        self.status = self.r.execute('healthcheck')
        end = time.perf_counter()
        self.logger.info(f"Healthcheck took {end - start:0.4f} seconds")
        return self.status

    def check(self):
        return self.get_status()


if __name__ == "__main__":
    Healthcheck().check()