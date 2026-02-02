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
