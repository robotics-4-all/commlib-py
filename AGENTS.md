# Agent Guidelines for commlib-py

This document provides guidelines for AI agents working on the commlib-py codebase.

## Repository Overview

A Python communication library implementing common patterns (Pub/Sub, RPC, Action) for CyberPhysical Systems. Supports multiple transports: MQTT, Redis, AMQP, Kafka.

- **Language**: Python 3.9+
- **Package**: `commlib`
- **Source**: `/home/klpanagi/Development/commlib/commlib-py/commlib/`
- **Tests**: `/home/klpanagi/Development/commlib/commlib-py/tests/`

## Configuration Files

- `.flake8` - Flake8 linting configuration (max-line-length: 120)
- `.pylintrc` - Pylint analysis configuration (max-line-length: 100, naming conventions)
- `.pre-commit-config.yaml` - Ruff pre-commit hooks for linting/formatting
- `pytest.ini` - Pytest marker definitions (mqtt, redis, integration, unit)
- `tox.ini` - Multi-Python version testing (3.9-3.13)
- `.coveragerc` - Coverage reporting configuration
- `.bumpversion.cfg` - Version management

## Build/Test/Lint Commands

### Testing

```bash
# Run all unit tests (excludes integration tests)
pytest --ignore=tests/mqtt --ignore=tests/redis -v

# Run a single test
pytest tests/test_msgs.py::TestMessages::test_header_message -v

# Run tests with coverage
coverage run -m pytest --ignore=tests/mqtt --ignore=tests/redis
coverage report -m

# Run tests with coverage (local)
make coverage                # Run tests and show coverage report

# Run tests in Docker (isolated environment)
make test                    # Unit tests
make test-integration        # Integration tests (requires brokers)
make cov                     # Coverage report (Docker)

# Run tests across Python versions
tox
```

### Linting

```bash
# Run flake8 linting (primary linter)
make lint
# Or: flake8 commlib tests

# Run pylint analysis
pylint $(git ls-files '*.py')

# Run ruff (formatting, via pre-commit)
ruff check .
ruff format .
```

### Building/Installing

```bash
# Install for development
make install-dev
# Or: pip install -e ".[dev]"

# Build package
make build
# Or: python -m build

# Clean build artifacts
make clean
```

## Code Style Guidelines

### Formatting

- **Line length**: 120 characters (flake8), 100 for pylint
- **Indentation**: 4 spaces

### Quote Style

- **Docstrings**: Triple double quotes (`"""`)
- **Strings**: Double quotes preferred (`"hello"`)
- Single quotes acceptable but double quotes are the project standard

### Imports

Order: stdlib → third-party → local (separated by blank lines):

```python
import time
from typing import Optional

from pydantic import BaseModel

from commlib.utils import get_timestamp_ns
```

### Naming Conventions

- **Modules**: `snake_case` (e.g., `base_transport.py`)
- **Classes**: `PascalCase` (e.g., `Message`, `BaseModel`)
- **Functions/Methods**: `snake_case` (e.g., `from_json`, `model_dump`)
- **Variables**: `snake_case`
- **Constants**: `UPPER_CASE`
- **Private**: Prefix with underscore (e.g., `_internal_method`)

### Type Hints

Use type hints for all function signatures and variable declarations where beneficial:

```python
def from_json(cls, json_str: str) -> "Message":
    data: Dict[str, Any] = JSONSerializer.deserialize(json_str)
```

### Documentation

- Use triple-quoted docstrings for classes and public methods
- Docstrings not strictly required for private methods (starting with `_`)
- Include type info in docstrings where not obvious

### Pydantic Model Patterns

- All messages inherit from `Message(BaseModel)`
- Use `model_dump()` instead of `dict()` (Pydantic v2)
- Implement `from_json()` classmethod for deserialization
- Implement `to_json()` method for serialization
- Nested message classes for RPC Request/Response, Action Goal/Result/Feedback

```python
class MyMessage(Message):
    class Request(Message):
        field: int = 0
    
    class Response(Message):
        result: str = ""

# Usage
req = MyMessage.Request(field=42)
json_data = req.to_json()
restored = MyMessage.Request.from_json(json_data)
```

### Logging Conventions

- Module-level logger initialization with lazy singleton pattern
- Use classmethod `logger()` that returns cached logger
- Access via `self.log.debug()`, `self.log.error()`, etc.

```python
module_logger = None

class MyClass:
    @classmethod
    def logger(cls) -> logging.Logger:
        global module_logger
        if module_logger is None:
            module_logger = logging.getLogger(__name__)
        return module_logger
    
    @property
    def log(self):
        return self.logger()
```

### Exception Handling

- Use custom exceptions from `commlib.exceptions` (not built-in exceptions)
- Custom exceptions accept `(message, errors=None)` signature
- Use `ValueError` for input validation errors
- Use `RuntimeError` for state/connection errors
- Use `NotImplementedError` for abstract base methods

```python
from commlib.exceptions import RPCClientError, PublisherError

# For validation errors
if invalid_condition:
    raise ValueError(f"Invalid topic: {topic}")

# For state errors
if not self._connected:
    raise RuntimeError("Transport not initialized")

# For RPC errors
raise RPCClientError("Request timed out")
```

### Async Patterns

- Use utilities from `commlib.async_utils` for safe async operations
- Wrap coroutines with `safe_wrapper()` for exception handling
- Use `safe_gather()` instead of `asyncio.gather()`
- Use `safe_ensure_future()` for task creation

```python
from commlib.async_utils import safe_wrapper, safe_gather

async def my_async_method(self):
    try:
        result = await safe_wrapper(some_coroutine())
        results = await safe_gather(*coroutines)
    except (CancelledError, TimeoutError):
        self.log.warning("Operation cancelled or timed out")
```

### Resource Management

- Use context managers (`with` statements) for all resource management
- File operations: `with open(...) as f:`
- Socket operations: `with socket.socket(...) as sock:`
- No manual resource cleanup in finally blocks

## Testing Patterns

### Test Structure

- Use `unittest.TestCase` for test classes
- Name test methods with `test_` prefix
- Use `setUp()` and `tearDown()` for fixtures

### Testing Utilities

- **Mock Transport**: Use `commlib.transports.mock.ConnectionParameters` for unit tests
- **Integration Tests**: 
  - Require running brokers (MQTT, Redis)
  - Use environment variables: `COMMLIB_MQTT_HOST`, `COMMLIB_MQTT_PORT`
  - Run via `make test-integration` (starts Docker containers)
- **Test Organization**:
  - Unit tests in `tests/test_*.py` (no external dependencies)
  - Integration tests in `tests/mqtt/`, `tests/redis/`
  - Scripts in `scripts/` for manual testing

### Pytest Markers

Mark integration tests with appropriate markers:

- `@pytest.mark.mqtt` - Requires MQTT broker
- `@pytest.mark.redis` - Requires Redis broker
- `@pytest.mark.integration` - External services required
- `@pytest.mark.unit` - No external services

## Project Structure

```
commlib/
├── __init__.py           # Package entry point
├── msg.py                # Message types (Pydantic models)
├── pubsub.py             # Pub/Sub implementation
├── rpc.py                # RPC implementation
├── action.py             # Action pattern implementation
├── node.py               # Node abstraction
├── endpoints.py          # Endpoint definitions
├── serializer.py         # Serialization utilities
├── compression.py        # Compression utilities
├── timer.py              # Timer utilities
├── utils.py              # General utilities
├── async_utils.py        # Async utilities
├── exceptions.py         # Custom exceptions
├── connection.py         # Connection management
├── bridges.py            # Transport bridges
├── tcp_bridge.py         # TCP bridge implementation
├── aggregation.py        # Message aggregation
└── transports/           # Transport implementations
    ├── base_transport.py
    ├── mock.py
    ├── mqtt.py
    ├── redis.py
    ├── amqp.py
    └── kafka.py

tests/
├── test_*.py             # Unit tests
├── mqtt/                 # MQTT integration tests
└── redis/                # Redis integration tests
```

## Dependencies

Key dependencies:
- `pydantic>=2.0.0` - Data validation
- `ujson>=5.7.0` - JSON serialization
- `rich>=13.7.0` - Terminal formatting

Optional extras: `mqtt`, `redis`, `amqp`, `kafka`, `all`, `performance`

## Pre-commit Hooks

The project uses ruff for formatting and linting:

```bash
pre-commit install
pre-commit run --all-files
```
