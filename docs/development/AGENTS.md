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

### CI Commands (Local Testing)

Run the full CI pipeline locally before pushing to GitHub:

```bash
# Quick CI check (unit tests + benchmarks, ~15s)
make ci

# Strict CI check (includes linting, ~20s)
make ci-strict

# Full CI with broker tests (requires Docker, ~2min)
make ci-full
```

**Individual CI steps:**
```bash
make ci-setup       # Check environment (Python, venv, dependencies)
make ci-unit        # Run unit tests only
make ci-lint        # Run linting only (flake8)
make ci-benchmarks  # Run benchmark smoke tests (mock transport)
```

**When to use:**
- `make ci` - Before every commit (fast validation)
- `make ci-strict` - Before creating PR (adds linting)
- `make ci-full` - Before merging to master (full validation with brokers)

**Features:**
- ✅ Auto-cleanup of Docker containers (no manual intervention needed)
- ✅ Proper error handling (brokers stopped even on failure)
- ✅ Excludes AMQP tests on Python 3.14 (pika compatibility)
- ✅ Simulates exact GitHub Actions workflow locally

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
- `@pytest.mark.smoke` - Quick smoke tests (for CI)
- `@pytest.mark.benchmark` - Full benchmark tests

### Benchmark Testing

**Run scaling benchmarks (no broker needed):**
```bash
python benchmark/bench_scaling.py --transport mock --test all
python benchmark/bench_scaling.py --transport mock --test publishers
python benchmark/bench_scaling.py --transport mock --test message_size
python benchmark/bench_scaling.py --transport mock --test memory
```

**Run broker-based benchmarks (requires Docker):**
```bash
# Start brokers
./scripts/start_benchmark_brokers.sh

# Run smoke tests (quick validation)
pytest tests/benchmarks/ -v -m smoke

# Run full benchmarks
pytest tests/benchmarks/ -v -m benchmark

# Stop brokers
./scripts/stop_benchmark_brokers.sh
```

**Using pytest-benchmark for performance tracking:**
```bash
# Run with tracking
pytest tests/benchmarks/test_bench_mqtt_benchmark.py -v

# Save baseline
pytest tests/benchmarks/ --benchmark-save=baseline

# Compare against baseline
pytest tests/benchmarks/ --benchmark-compare=baseline

# Fail if >10% degradation
pytest tests/benchmarks/ --benchmark-compare-fail=mean:10%
```

**Benchmark organization:**
- `benchmark/` - Standalone benchmark scripts
- `tests/benchmarks/` - pytest-integrated benchmark tests
- Smoke tests: Quick validation (~30s)
- Full tests: Comprehensive benchmarks (~2-5min)

See [benchmark/README.md](benchmark/README.md) for detailed documentation.

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

---

## Common Issues & Solutions

### Docker Container Conflicts

**Problem:** `Error: The container name "/benchmark-mqtt" is already in use`

**Solution:**
```bash
# Automatic cleanup (handled by scripts)
./scripts/start_benchmark_brokers.sh  # Auto-cleans before starting

# Manual cleanup if needed
docker rm -f benchmark-mqtt benchmark-redis benchmark-amqp
```

### Transport API Errors

**Problem:** `TypeError: run() got an unexpected keyword argument 'wait'`

**Solution:** Fixed in commit `148b825`. All transports now support:
```python
publisher.run(wait=True)   # Wait for connection
publisher.run(wait=False)  # Don't wait
```

### Redis Connection Pool Issues

**Problem:** Benchmark shows "Connection pools: 0"

**Solution:** Fixed in commit `5291b9c`. Pool cleanup now properly resets class variables.

### Python 3.14 Compatibility

**Note:** Python 3.14 is not officially supported yet. AMQP tests are automatically skipped due to pika library compatibility issues. Use Python 3.9-3.13 for full test suite.

---

## Recent Updates (February 2026)

### Phase C: CI Stabilization

Three critical fixes for reliable CI execution:

1. **Docker Cleanup (`8c18481`)** - Auto-cleanup containers, error handling
2. **Transport API (`148b825`)** - Fixed run() signatures in AMQP/Kafka
3. **Redis Pool (`5291b9c`)** - Fixed connection pool benchmark

**Current Status:**
- ✅ 349 unit tests passing
- ✅ 13 smoke benchmark tests passing
- ✅ `make ci-full` fully operational
- ✅ 0 critical linting errors
