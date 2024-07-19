import time
import logging

from callite.client.rpc_client import RPCClient


class Healthcheck():
    def __init__(self):
        self.r = RPCClient("redis://redis:6379/0", "service")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())

    def get_status(self):
        # Get high resolution current time
        start = time.perf_counter()
        status = self.r.execute('healthcheck')
        end = time.perf_counter()
        self.logger.info(f"Healthcheck took {end - start:0.4f} seconds")
        return status

    def check(self):
        return self.get_status()

    def check_add(self, a, b):
        return self.r.execute('add', a, b)

    def check_subtract(self, a, b):
        return self.r.execute('subtract', a = a, b = b)


if __name__ == "__main__":
    hc = Healthcheck()
    res = hc.check()
    hc.logger.info(f'Healthcheck status: {res}')
    res = hc.check_add(1, 2)
    hc.logger.info(f'Added 1 and 2 = {res}')
    res = hc.check_subtract(2, 1)
    hc.logger.info(f'Subtracted 1 from 2 = {res}')