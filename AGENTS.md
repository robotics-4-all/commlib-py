# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-10
**Commit:** fc0371b
**Branch:** feat/performance_a

## OVERVIEW

Python communication DSL for CyberPhysical Systems. Protocol-agnostic API (MQTT, Redis, AMQP, Kafka) implementing Pub/Sub, RPC, and Action patterns. Built on Pydantic v2 + threading. Python 3.9+.

## STRUCTURE

```
commlib-py/
├── commlib/              # Core library (see commlib/AGENTS.md)
│   └── transports/       # Transport backends (see transports/AGENTS.md)
├── tests/                # Test suite (see tests/AGENTS.md)
├── benchmark/            # Standalone + pytest benchmark scripts
├── examples/             # Usage examples per pattern (pubsub, rpc, action, bridges)
├── brokers/              # Docker configs for MQTT/Redis/AMQP/Kafka brokers
├── scripts/              # CI helpers, broker lifecycle, perf scripts
├── docs/                 # Performance docs, API guide, session summaries
│   └── development/      # Detailed development guidelines (AGENTS.md)
└── .github/workflows/    # CI: pytest, pylint, coverage, benchmarks, release
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add communication pattern | `commlib/pubsub.py`, `commlib/rpc.py`, `commlib/action.py` | Each defines base classes for endpoints |
| Add/modify transport | `commlib/transports/{protocol}.py` | Must extend `BaseTransport` from `base_transport.py` |
| Define message types | `commlib/msg.py` | All inherit from `Message(BaseModel)` |
| Node-level API | `commlib/node.py` | `Node` creates endpoints via `create_*` factory methods |
| Endpoint factory | `commlib/endpoints.py` | `endpoint_factory(etype, etransport)` for non-Node usage |
| Bridges (cross-broker) | `commlib/bridges.py` | `TopicBridge`, `RPCBridge`, `PTopicBridge` |
| Serialization | `commlib/serializer.py` | Auto-selects orjson > ujson > stdlib json |
| Custom exceptions | `commlib/exceptions.py` | All accept `(message, errors=None)` |
| Connection params | `commlib/connection.py` | `BaseConnectionParameters(BaseModel)` |
| Topic notation utils | `commlib/utils.py` | `convert_topic_notation()`, `topic_to_*`/`topic_from_*` |
| Unit tests | `tests/test_*.py` | Mock transport, no external deps |
| Integration tests | `tests/mqtt/`, `tests/redis/` | Require running brokers |
| Benchmark tests | `tests/benchmarks/` | pytest-benchmark, smoke + full markers |
| Standalone benchmarks | `benchmark/` | CLI scripts, `--transport mock` for no-broker runs |
| CI workflows | `.github/workflows/` | pytest, pylint, coverage, benchmarks, release |
| Dev guidelines | `docs/development/AGENTS.md` | Detailed coding standards, patterns, commands |

## CONVENTIONS

- **Line length**: 120 (flake8), 100 (pylint)
- **Quotes**: Double quotes preferred; triple-double for docstrings
- **Imports**: stdlib → third-party → local, blank-line separated
- **Naming**: `snake_case` modules/functions, `PascalCase` classes, `UPPER_CASE` constants
- **Type hints**: Required on all function signatures
- **Pydantic v2**: Use `model_dump()` not `dict()`. Messages inherit `Message(BaseModel)`
- **Logging**: Lazy singleton pattern via `module_logger` global + `@classmethod logger()` + `@property log`
- **Async**: Use `commlib.async_utils` wrappers (`safe_wrapper`, `safe_gather`, `safe_ensure_future`)
- **Exceptions**: Use custom exceptions from `commlib.exceptions`, not builtins
- **Transport imports**: Always lazy (inside function/conditional) — users install only needed extras
- **Serializer priority**: orjson > ujson > json (auto-detected at import time)

## ANTI-PATTERNS (THIS PROJECT)

- **Never** use `dict()` on Pydantic models — use `model_dump()`
- **Never** import transport-specific deps at module level — they're optional extras
- **Never** use `as any` type suppression (Python equivalent: avoid `# type: ignore` without reason)
- **Never** commit with failing `make ci` — run before every push
- **Python 3.14**: AMQP (pika) incompatible — tests auto-skipped
- **Kafka transport**: Partial implementation — no RPCServer, no ActionService/Client

## COMMANDS

```bash
# Development
pip install -e ".[dev]"           # Install with dev deps
make ci                           # Quick CI: unit + benchmark smoke (~15s)
make ci-strict                    # CI + linting (~20s)
make ci-full                      # Full CI with brokers (Docker required, ~2min)

# Testing
pytest --ignore=tests/mqtt --ignore=tests/redis --ignore=tests/benchmarks -v  # Unit only
pytest tests/benchmarks/ -v -m smoke                                           # Benchmark smoke
make coverage                     # Local coverage report

# Linting
flake8 commlib tests              # Primary linter
ruff check . && ruff format .     # Formatting (pre-commit)

# Benchmarks (no broker)
python benchmark/bench_scaling.py --transport mock --test all

# Build & Release
make build                        # Build package
make release                      # Bump patch + build + upload PyPI
```

## NOTES

- `build/lib/commlib/` is a stale build artifact — ignore, not source of truth
- `commlib/tcp_proxy.py` exists but TCP bridge is separate from main transport layer
- Connection pooling is Redis-specific (class-level `_connection_pools` dict)
- Mock transport in `commlib/transports/mock.py` is the primary unit-test transport
- 349+ unit tests, 13 benchmark smoke tests currently passing
- Env vars for integration: `COMMLIB_MQTT_HOST`, `COMMLIB_MQTT_PORT`
