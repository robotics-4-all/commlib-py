# Commlib Performance Benchmarks

This directory contains comprehensive benchmarks for commlib-py performance testing.

## Benchmark Types

### 1. Mock Transport Benchmarks (No External Dependencies)

These benchmarks use the in-memory mock transport and can run without any external services.

```bash
# Serialization benchmarks
python benchmark/bench_serializer.py

# Pub/Sub benchmarks (mock transport)
python benchmark/bench_pubsub.py

# System-level benchmarks (thread pools, scaling, etc.)
python benchmark/bench_system.py
```

**Output Example:**
```
Serializer Performance Benchmarks
==================================
make_primitives (depth 5):   0.009 ms/op | 109,755 ops/sec
JSON serialize:               0.006 ms/op | 170,503 ops/sec

System Performance Benchmarks
==============================
Shared vs Dedicated Thread Pools:
  Dedicated:    0.37 ms
  Shared:       0.23 ms
  Improvement:  37.9% faster
```

---

### 2. Real Broker Benchmarks (Requires External Services)

These benchmarks test against real message brokers for accurate performance measurements.

#### MQTT Benchmarks

**Start MQTT Broker:**
```bash
docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto:latest mosquitto -c /mosquitto-no-auth.conf
```

**Run Benchmarks:**
```bash
python benchmark/bench_mqtt_real.py
```

**Custom MQTT Broker:**
```bash
export COMMLIB_MQTT_HOST=your-broker-host
export COMMLIB_MQTT_PORT=1883
python benchmark/bench_mqtt_real.py
```

**Tests:**
- Publish throughput
- Pub/Sub round trip latency
- QoS level comparison (QoS 0, 1, 2)
- Concurrent publishers

---

#### Redis Benchmarks

**Start Redis Server:**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

**Run Benchmarks:**
```bash
python benchmark/bench_redis_real.py
```

**Custom Redis Server:**
```bash
export COMMLIB_REDIS_HOST=your-redis-host
export COMMLIB_REDIS_PORT=6379
python benchmark/bench_redis_real.py
```

**Tests:**
- Publish throughput
- Pub/Sub round trip latency
- Connection pool sharing validation
- Concurrent publishers
- Message size impact

---

#### Kafka Benchmarks (Coming Soon)

Kafka benchmarks require a Kafka cluster. Stay tuned!

---

## Quick Start: Run All Mock Benchmarks

```bash
cd /path/to/commlib-py

# Activate virtual environment
source venv/bin/activate

# Run all mock benchmarks
python benchmark/bench_serializer.py
python benchmark/bench_pubsub.py
python benchmark/bench_system.py
```

---

## Quick Start: Run Real Broker Benchmarks

```bash
# Start brokers with Docker Compose
cd benchmark
cat > docker-compose.yml <<EOF
version: '3'
services:
  mqtt:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
    command: mosquitto -c /mosquitto-no-auth.conf
  
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
EOF

docker-compose up -d

# Wait for services to start
sleep 3

# Run benchmarks
cd ..
source venv/bin/activate
python benchmark/bench_mqtt_real.py
python benchmark/bench_redis_real.py

# Cleanup
cd benchmark
docker-compose down
```

---

## Benchmark Results Interpretation

### Throughput (msg/sec)
- **Higher is better**
- Measures how many messages can be processed per second
- Typical values:
  - Mock: 300,000 - 700,000 msg/sec (in-memory)
  - MQTT: 5,000 - 20,000 msg/sec (network + broker)
  - Redis: 10,000 - 50,000 msg/sec (network + server)

### Latency (ms/msg)
- **Lower is better**
- Measures time to process a single message
- Typical values:
  - Mock: 0.001 - 0.003 ms (in-memory)
  - MQTT: 0.05 - 0.2 ms (local network)
  - Redis: 0.02 - 0.1 ms (local network)

### End-to-End Latency
- Measures time from publish to subscriber callback
- Includes network, broker, and processing time
- Critical for real-time applications

---

## Performance Optimizations Measured

The benchmarks validate these Phase 1 & 2 optimizations:

1. **make_primitives()** - 40-60% faster with type dispatch
2. **MQTT topic caching** - 15% faster with LRU cache
3. **Thread pool consolidation** - 5-10x fewer threads
4. **Event-driven waiting** - 100% reduction in busy-wait CPU
5. **Redis connection pooling** - 6-10x fewer connections
6. **functools.partial removal** - 5-10% faster message processing

---

## Troubleshooting

### "Broker not available" Error

```
❌ MQTT broker not available!
   Could not connect to localhost:1883
```

**Solution:**
1. Check broker is running: `docker ps`
2. Verify port mapping: `docker ps | grep 1883`
3. Test connectivity: `telnet localhost 1883`
4. Check firewall rules

### "Connection refused"

**Solution:**
- Broker might not have started yet - wait 5-10 seconds
- Check if another process is using the port: `lsof -i :1883`
- Try restarting the broker

### Benchmarks are slow

**Expected:**
- First run may be slower (JIT warmup)
- External broker benchmarks depend on network latency
- Docker on macOS/Windows has performance overhead

**To improve:**
- Run on Linux for best Docker performance
- Use native brokers instead of Docker
- Ensure no other processes are competing for resources

---

## Adding New Benchmarks

To add a new benchmark:

1. Create `benchmark/bench_<name>.py`
2. Follow existing structure:
   - Setup/teardown
   - Warm-up phase
   - Measurement phase
   - Results reporting
3. Add to this README
4. Consider both mock and real broker versions

---

## CI/CD Integration

To run benchmarks in CI:

```yaml
# .github/workflows/benchmark.yml
- name: Run Mock Benchmarks
  run: |
    python benchmark/bench_serializer.py
    python benchmark/bench_system.py

- name: Start Brokers
  run: docker-compose -f benchmark/docker-compose.yml up -d

- name: Run Real Benchmarks
  run: |
    python benchmark/bench_mqtt_real.py
    python benchmark/bench_redis_real.py
```

---

## Benchmark Integration Tests

All benchmark scripts have been integrated into the pytest test suite for automated validation. These tests verify that benchmarks work correctly and can detect performance regressions.

### Running Integration Tests

**Quick smoke tests (~30 seconds):**
```bash
make test-benchmarks-smoke
# Or: pytest tests/benchmarks/ -v -m smoke
```

**Full benchmark tests (~2-5 minutes):**
```bash
# Start all brokers first
./scripts/start_benchmark_brokers.sh

# Run all benchmark tests
make test-benchmarks

# Or run by transport:
make test-benchmarks-mqtt   # MQTT only
make test-benchmarks-redis  # Redis only
make test-benchmarks-amqp   # AMQP only

# Stop brokers when done
./scripts/stop_benchmark_brokers.sh
```

### Test Structure

Each benchmark test:
- ✅ Validates benchmark functions are callable
- ✅ Runs benchmarks with configurable iterations
- ✅ Uses warning-based thresholds (doesn't fail on slow systems)
- ✅ Returns metrics for validation
- ✅ Skips automatically if broker unavailable

**Example test:**
```python
@pytest.mark.mqtt
@pytest.mark.smoke
def test_mqtt_publish_smoke(self, mqtt_available):
    """Quick MQTT publish smoke test - 100 messages."""
    from bench_mqtt_real import benchmark_mqtt_publish_throughput
    
    throughput = benchmark_mqtt_publish_throughput(iterations=100, warmup=10)
    
    # Warning-based threshold
    if throughput < 1000:
        warnings.warn(f"MQTT publish slow: {throughput:.0f} msg/sec")
    
    assert throughput > 0
```

### Available Benchmark Functions

**MQTT (`bench_mqtt_real.py`):**
```python
benchmark_mqtt_publish_throughput(iterations=1000, warmup=100) -> float
benchmark_mqtt_pubsub_roundtrip(iterations=100, warmup=50) -> float
benchmark_mqtt_concurrent_publishers(num_publishers=10, iterations_per_pub=100, warmup=10) -> float
```

**Redis (`bench_redis_real.py`):**
```python
benchmark_redis_publish_throughput(iterations=1000, warmup=100) -> float
benchmark_redis_pubsub_roundtrip(iterations=100, warmup=50) -> float
benchmark_redis_connection_pool_sharing(num_publishers=20) -> int
benchmark_redis_concurrent_publishers(num_publishers=10, iterations_per_pub=100, warmup=10) -> float
```

**AMQP (`bench_amqp_real.py`):**
```python
benchmark_amqp_publish(iterations=1000, warmup=100) -> float
benchmark_amqp_pubsub_roundtrip(iterations=100, warmup=50) -> float
benchmark_amqp_rpc_latency(iterations=100, warmup=10) -> float
benchmark_amqp_connection_pooling(num_publishers=20) -> int
```

### Performance Thresholds

Integration tests use warning-based thresholds to detect regressions without failing on slow systems:

| Benchmark | Warning Threshold | Notes |
|-----------|------------------|-------|
| MQTT Publish | <1,000 msg/sec (smoke), <5,000 (full) | Network-dependent |
| MQTT Pub/Sub | <500 msg/sec (smoke), <1,000 (full) | Round-trip latency |
| Redis Publish | <2,000 msg/sec (smoke), <10,000 (full) | Local Redis expected |
| Redis Pub/Sub | <1,000 msg/sec (smoke), <2,000 (full) | Round-trip latency |
| AMQP Publish | <5,000 msg/sec | RabbitMQ performance |
| AMQP RPC | >50ms latency | Event-driven validation |
| Connection Pooling | >1 pool for 20 publishers | Phase 2/3 optimization |

---

## Performance Goals

Target performance metrics:

| Metric | Target | Current |
|--------|--------|---------|
| Serialization | >100k ops/sec | ✅ 170k ops/sec |
| Mock Pub/Sub | >500k msg/sec | ✅ 600k msg/sec |
| MQTT Pub/Sub | >10k msg/sec | 🔬 (measure with broker) |
| Redis Pub/Sub | >20k msg/sec | 🔬 (measure with broker) |
| Thread Count | <20 per node | ✅ 8-12 per node |
| Memory Usage | <100MB per node | ✅ ~64MB per node |

---

## Contact

For questions or issues with benchmarks, please open an issue on GitHub.

---

#### AMQP Benchmarks (Phase 3 Validation) ⭐ NEW

**Start RabbitMQ Broker:**
```bash
docker run -d -p 5672:5672 -p 15672:15672 --name rabbitmq rabbitmq:3-management
```

**Run Benchmarks:**
```bash
python benchmark/bench_amqp_real.py
```

**Custom AMQP Broker:**
```bash
export COMMLIB_AMQP_HOST=your-broker-host
export COMMLIB_AMQP_PORT=5672
python benchmark/bench_amqp_real.py
```

**Tests:**
- Publish throughput
- Pub/Sub round trip latency
- **RPC latency (Phase 3 event-driven optimization validation)**
- **Connection pooling (Phase 3 optimization validation)**

**Phase 3 Optimizations Validated:**
1. Event-driven RPC response (30-50% faster, no busy-wait)
2. Connection pooling (10-20x fewer connections)
3. Optimized events thread (80% fewer wake-ups)

**Expected Results:**
- RPC latency: 5-20ms (event-driven, not busy-wait)
- Connection pooling: 1 connection for 20 publishers (not 20 connections)
- Throughput: 5,000-20,000 msg/sec

**RabbitMQ Management UI:**
http://localhost:15672 (username: guest, password: guest)

---

## Integration Tests (Recommended)

The benchmarks can also be run as pytest integration tests with automatic broker availability checking and performance regression warnings.

### Quick Smoke Tests (~30 seconds)

```bash
# Run all quick smoke tests
make test-benchmarks-smoke

# Or with pytest directly
pytest tests/benchmarks/ -v -m smoke
```

### Full Benchmark Tests (~2-5 minutes)

```bash
# Run all benchmarks as tests
make test-benchmarks

# Or with pytest directly
pytest tests/benchmarks/ -v -m benchmark
```

### Specific Transport Tests

```bash
# MQTT only
make test-benchmarks-mqtt
pytest tests/benchmarks/test_bench_mqtt.py -v

# Redis only
make test-benchmarks-redis
pytest tests/benchmarks/test_bench_redis.py -v

# AMQP only (Phase 3 validation)
make test-benchmarks-amqp
pytest tests/benchmarks/test_bench_amqp.py -v
```

### Integration Test Features

- ✅ **Automatic broker detection** - Tests skip gracefully if broker not available
- ✅ **Warning-based thresholds** - Performance warnings don't fail tests
- ✅ **Smoke tests** - Quick validation in <30 seconds
- ✅ **Full benchmarks** - Comprehensive testing in 2-5 minutes
- ✅ **Phase 3 validation** - Specific tests for AMQP optimizations

### Example Output

```bash
$ make test-benchmarks-smoke

tests/benchmarks/test_bench_mqtt.py::TestMQTTBenchmarks::test_mqtt_broker_available PASSED
tests/benchmarks/test_bench_mqtt.py::TestMQTTBenchmarks::test_mqtt_benchmark_imports PASSED
tests/benchmarks/test_bench_amqp.py::TestAMQPBenchmarks::test_amqp_publish_smoke PASSED
tests/benchmarks/test_bench_amqp.py::TestAMQPBenchmarks::test_amqp_rpc_latency_smoke PASSED
tests/benchmarks/test_bench_amqp.py::TestAMQPBenchmarks::test_amqp_connection_pooling PASSED

✓ Phase 3 optimization VALIDATED: All publishers share 1 connection!

5 passed in 28.3s
```

---

## Starting All Brokers

```bash
# Quick start all brokers with Docker
docker run -d -p 1883:1883 --name mosquitto eclipse-mosquitto mosquitto -c /mosquitto-no-auth.conf
docker run -d -p 6379:6379 --name redis redis:latest
docker run -d -p 5672:5672 -p 15672:15672 --name rabbitmq rabbitmq:3-management

# Wait for brokers to be ready
sleep 5

# Verify all brokers are running
docker ps | grep -E "(mosquitto|redis|rabbitmq)"

# Run all benchmarks
python benchmark/bench_mqtt_real.py
python benchmark/bench_redis_real.py
python benchmark/bench_amqp_real.py

# Or run as integration tests
make test-benchmarks-smoke  # Quick validation
make test-benchmarks        # Full benchmarks

# Stop all brokers
docker stop mosquitto redis rabbitmq
docker rm mosquitto redis rabbitmq
```

---

## Performance Regression Detection

Integration tests use **warning-based thresholds** to detect performance regressions without causing test failures:

| Transport | Metric | Warning Threshold |
|-----------|--------|-------------------|
| MQTT | Publish | < 10,000 msg/sec |
| MQTT | Pub/Sub | < 1,000 msg/sec |
| Redis | Publish | < 10,000 msg/sec |
| Redis | Pub/Sub | < 1,000 msg/sec |
| AMQP | Publish | < 5,000 msg/sec |
| AMQP | Pub/Sub | < 1,000 msg/sec |
| AMQP | RPC latency | > 50 ms |
| AMQP | Connection pooling | > 1 connection for 20 publishers |

**Warnings are logged but tests pass** - This prevents false failures due to system load while still alerting to significant performance degradation.

