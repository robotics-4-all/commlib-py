# tests/ — Test Suite

## OVERVIEW

Unit tests (mock transport, no deps), integration tests (broker-specific), and pytest-benchmark performance tests. Uses `unittest.TestCase` style with pytest runner.

## STRUCTURE

```
tests/
├── __init__.py
├── test_msgs.py              # Message serialization, from_json/to_json, nested types
├── test_pubsub.py            # Publisher/Subscriber with mock transport
├── test_rpc.py               # RPC service/client with mock transport
├── test_node.py              # Node lifecycle, endpoint creation, heartbeats
├── test_timer.py             # Timer utility tests
├── test_bridges.py           # TopicBridge, RPCBridge, PTopicBridge (mock transport)
├── test_topic_conversion.py  # topic_to_*/topic_from_* conversion functions
├── test_amqp_optimizations.py # AMQP-specific optimization validation
├── test_*.py                 # Other unit tests
├── mqtt/                     # MQTT integration tests (requires broker)
│   ├── test_mqtt_pubsub.py   # MQTT pub/sub integration
│   └── test_mqtt_task_queue.py # MQTT task queue integration
├── redis/                    # Redis integration tests (requires broker)
│   ├── test_redis_pubsub.py  # Redis pub/sub integration
│   └── test_redis_task_queue.py # Redis task queue integration
├── kafka/                    # Kafka integration tests (requires broker)
│   ├── test_kafka_pubsub.py  # Kafka pub/sub integration
│   ├── test_kafka_rpc.py     # Kafka RPC integration
│   └── test_kafka_task_queue.py # Kafka task queue integration
└── benchmarks/               # pytest-benchmark tests
    ├── conftest.py           # Broker availability fixtures (mqtt, redis, amqp, kafka)
    ├── test_bench_scaling.py # Scaling tests (mock transport, no broker)
    ├── test_bench_task_queue.py # Task queue benchmarks (mock transport)
    ├── test_bench_mqtt*.py   # MQTT benchmark tests
    ├── test_bench_redis*.py  # Redis benchmark tests
    └── test_bench_amqp*.py   # AMQP benchmark tests
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add unit test | `tests/test_{module}.py` | Use mock transport: `from commlib.transports.mock import ConnectionParameters` |
| Add integration test | `tests/{protocol}/` | Mark with `@pytest.mark.{protocol}` |
| Add benchmark test | `tests/benchmarks/` | Mark `@pytest.mark.smoke` (fast) or `@pytest.mark.benchmark` (full) |
| Test fixtures | `tests/benchmarks/conftest.py` | Broker connection params, cleanup helpers |

## CONVENTIONS

- **Test style**: `unittest.TestCase` classes with `test_` methods, `setUp`/`tearDown`
- **Mock transport**: Always use `commlib.transports.mock.ConnectionParameters()` for unit tests
- **Markers**: `@pytest.mark.mqtt`, `redis`, `amqp`, `kafka`, `integration`, `unit`, `smoke`, `benchmark`
- **Integration env vars**: `COMMLIB_MQTT_HOST`, `COMMLIB_MQTT_PORT`, `COMMLIB_REDIS_HOST`, `COMMLIB_REDIS_PORT`, `COMMLIB_KAFKA_HOST`, `COMMLIB_KAFKA_PORT`

## COMMANDS

```bash
# Unit tests only (no brokers)
pytest --ignore=tests/mqtt --ignore=tests/redis --ignore=tests/kafka --ignore=tests/benchmarks -v

# Single test
pytest tests/test_msgs.py::TestMessages::test_header_message -v

# Benchmark smoke (no brokers)
pytest tests/benchmarks/test_bench_scaling.py -v -m smoke

# Full benchmarks (needs brokers via Docker)
./scripts/start_benchmark_brokers.sh
pytest tests/benchmarks/ -v -m benchmark
./scripts/stop_benchmark_brokers.sh
```

## ANTI-PATTERNS

- **Never** require running brokers in `test_*.py` unit tests — use mock transport
- **Never** run `pytest` without `--ignore` flags unless brokers are available
- **AMQP tests**: Auto-skipped on Python 3.14 (pika incompatibility)
