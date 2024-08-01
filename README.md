# Callite

callite is a lightweight Remote Procedure Call (RPC) implementation over Redis, designed to facilitate communication between different components of a distributed system. It minimizes dependencies and offers a simple yet effective solution for decoupling complex systems, thus alleviating potential library conflicts.

## Setting up Callite

Before using callite, ensure you have a Redis instance running. You can start a Redis server using the default settings or configure it as per your requirements.

## Implementing the Server

To implement the Callite server, follow these steps:

1. Import the `RPCService` class from `server.rpc_server`.
2. Define your main class and initialize the RPC service with the Redis URL and service name.
3. Register your functions with the RPC service using the `register` decorator.
4. Run the RPC service indefinitely.

Here's an example implementation:

```python
from callite.server import RPCService


class Main:
    def __init__(self):
        service = "service"
        redis_url = "redis://redis:6379/0"
        self.rpc_service = RPCService(redis_url, service)

    def run(self):
        @self.rpc_service.register
        def healthcheck():
            return "OK"

        @self.rpc_service.register
        def foo(paramX, paramY):
            // Do something with paramX and paramY
            return "OK"

        
        self.rpc_service.run_forever()


if __name__ == "__main__":
    Main().run()
```

## Calling the Function from Client

Once the server is set up, you can call functions remotely from the client side. Follow these steps to call functions:

1. Import the `RPCClient` class from `client.rpc_client`.
2. Define your client class and initialize the RPC client with the Redis URL and service name.
3. Call the function using the `execute` method of the RPC client.
4. Optionally, you can pass arguments and keyword arguments to the function.

Here's an example client implementation:

```python
import time
from callite.client.rpc_client import RPCClient


class Healthcheck():
    def __init__(self):
        self.r = RPCClient("redis://redis:6379/0", "service")

    def get_status(self):
        status = self.r.execute('healthcheck')
        return status

    def foo(self. paramX, paramY):
        status = self.r.execute('foo', paramX = paramX, paramY = paramY)
        return status

    def check(self):
        return self.get_status()


if __name__ == "__main__":
    Healthcheck().check()
```

You can pass arguments and keyword arguments to the `execute` method as follows:

```python
client = RPCClient('redis://localhost:6379', 'my_service')
...
...
...
response = client.execute('foo', paramX = 1, paramY = 2)
# or
response = client.execute('foo', 1, 2)
```
This setup allows for efficient communication between components of a distributed system, promoting modularity and scalability.
