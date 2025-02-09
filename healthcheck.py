import asyncio
import os
import threading
import time
import logging

from callite.client.rpc_client import RPCClient

log_level = os.getenv('LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level.upper(), 'INFO')


class Healthcheck():
    def __init__(self):
        self.r = RPCClient("redis://redis:6379/0", "service")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
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
    for i in range(100):
        thread = threading.Thread(target=hc.add, args=(i, 0))
        threads.append(thread)
        thread.start()
    print('Start')
    for thread in threads:
        thread.join()

    print(hc.check())

    print('End')