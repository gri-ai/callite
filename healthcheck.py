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

    def check(self):
        start = time.perf_counter()
        status = self.r.execute('healthcheck')
        end = time.perf_counter()
        self.logger.info(f"Healthcheck took {end - start:0.4f} seconds")
        return status

    def add(self, a, b):
        self.r.publish('log', f"Logging {a} + {b}")
        result = self.r.execute('add', a, b)
        return result

if __name__ == "__main__":
    hc = Healthcheck()
    threads = []
    for i in range(200):
        thread = threading.Thread(target=hc.add, args=(i, 0))
        threads.append(thread)
        thread.start()
    print('Start')
    for thread in threads:
        thread.join()

    print(hc.check())

    print('End')