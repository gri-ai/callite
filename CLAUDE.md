# CLAUDE.md

## Project Overview

Callite is a lightweight Remote Procedure Call (RPC) library over Redis for distributed system communication. It uses Redis Streams for request transport and Redis Pub/Sub for response delivery, with pickle serialization. Published to PyPI as `callite`.

- **Language**: Python 3.10+
- **Package manager**: Poetry (primary), setuptools (secondary)
- **License**: MIT
- **Repository**: https://github.com/gri-ai/callite

## Repository Structure

```
callite/                    # Main Python package
  client/rpc_client.py      # RPCClient - sends RPC requests, receives responses
  server/rpc_server.py      # RPCServer - listens for requests, dispatches handlers
  rpctypes/                  # Protocol message types (Request, Response, MessageBase, RPCException)
  shared/redis_connection.py # Abstract base class for Redis connection management
  __init__.py                # Public exports: RPCClient, RPCServer, MessageBase, Request, Response, RPCException, RedisConnection
main.py                     # Example server implementation
healthcheck.py              # Example client + stress test (100 threads)
pyproject.toml              # Poetry config, project metadata, dependencies
setup.py                    # setuptools config (secondary build system)
Dockerfile                  # Python 3.10-slim with Poetry
docker-compose.yml          # Redis + server + client for local development
.github/workflows/          # CI/CD: tag-triggered PyPI publishing
```

## Build & Development Commands

```bash
# Install dependencies
poetry install

# Run type checking
poetry run mypy callite/

# Run example server (requires Redis)
poetry run python -m main

# Run example client/stress test (requires server running)
poetry run python -m healthcheck

# Build package (compiled with Cython)
python3 -m build

# Compile C extensions in-place for local development
python setup.py build_ext --inplace

# Build pure Python package (skip Cython compilation)
USE_CYTHON=0 python3 -m build

# Local development with Docker
docker-compose up
```

## Dependencies

**Runtime**: `redis` (^5.0.3), `tenacity` (^8.5.0)
**Dev**: `mypy` (^1.9.0), `setuptools` (^69.1.1), `pydevd-pycharm`, `Cython` (^3.0.0)
**Build**: `setuptools`, `wheel`, `Cython` (for compiled builds)

## Architecture & Communication Flow

1. **Server** listens on Redis Stream: `/callite/request/{service}` via consumer groups
2. **Client** sends pickled `Request` objects to the stream via `xadd`
3. Server spawns daemon threads per request, calls registered handler
4. Server publishes pickled `Response` to Pub/Sub channel: `/callite/response/{client_id}`
5. Client background thread receives response, matches by UUID, releases lock

Two call patterns:
- `register` - request/response (client calls `execute()`, waits for result)
- `subscribe` - fire-and-forget (client calls `publish()`, no response)

## Code Conventions

- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Private members**: prefixed with `_` (e.g., `_rds`, `_running`, `_request_pool`)
- **Logging**: `logging` module with `LOG_LEVEL` env var; defaults controlled via `_log_level_default` class attribute (`'ERROR'` in server, `'INFO'` in client). Logger setup is consolidated in `RedisConnection.__init__` using `logging.getLogger(type(self).__module__)`
- **Type hints**: Used on method signatures (parameters and return types), not enforced strictly
- **Imports**: Standard library first, then third-party, then local modules
- **Threading**: Daemon threads for background work (`daemon=True`)
- **Error handling**: Exceptions caught in handlers, errors returned in `Response.status`/`Response.error` fields
- **Serialization**: `pickle` for all request/response data over Redis
- **No formal test suite**: No pytest/unittest configured; manual testing via `main.py` and `healthcheck.py`

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, ERROR, etc.) | `ERROR` (server), `INFO` (client) |
| `EXECUTION_TIMEOUT` | Client-side timeout in seconds for `execute()` | `30` |

## CI/CD & Releases

- Triggered by pushing git tags
- Tags ending in `-alpha` publish only to TestPyPI
- Non-alpha tags publish to both PyPI and TestPyPI, plus create a signed GitHub Release
- Build uses `pypa/build`, publishing uses trusted OIDC publishing

## Version Management

Version is maintained in two places that must stay in sync:
- `pyproject.toml` (`tool.poetry.version`)
- `setup.py` (`version` parameter)

Current version: `0.2.11`

## Cython Compilation

The project supports Cython compilation to produce C extensions for faster execution. The build system uses setuptools with Cython as a build dependency.

- **Compiled modules**: `rpc_client.py`, `rpc_server.py`, `redis_connection.py`, `message_base.py`, `request.py`, `response.py`, `rpc_exception.py`
- **Excluded from compilation**: All `__init__.py` files (kept as pure Python for import compatibility)
- **Fallback**: If Cython is not installed, the build falls back to a pure Python package
- **Opt-out**: Set `USE_CYTHON=0` environment variable to skip compilation
- **Build backend**: `setuptools.build_meta` (switched from `poetry-core` to support C extensions)

## Key Design Decisions

- **Redis Streams + Pub/Sub hybrid**: Streams provide reliable request queuing with consumer groups; Pub/Sub provides fast response delivery
- **Pickle over JSON**: Chosen for performance; allows arbitrary Python object serialization
- **Thread-per-request**: Each incoming RPC request is processed in a new daemon thread
- **Lock-based synchronization**: Client uses `threading.Lock` to block until response arrives or timeout
- **UUID correlation**: Each request gets a UUID for matching requests to responses
