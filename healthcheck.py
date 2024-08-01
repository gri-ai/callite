import asyncio
import threading
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
    threads = []
    for i in range(100):
        thread = threading.Thread(target=hc.r.execute, args=('add', i, 0))
        threads.append(thread)
        thread.start()
    print('Start')
    for thread in threads:
        thread.join()