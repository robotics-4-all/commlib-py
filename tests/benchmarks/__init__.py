"""
Benchmark integration tests for commlib-py.

These tests validate that benchmark scripts work correctly and provide
performance regression detection through warning-based thresholds.

Test Markers:
- @pytest.mark.benchmark: Performance benchmark tests (may be slow)
- @pytest.mark.smoke: Quick smoke tests (<30 seconds)
- @pytest.mark.mqtt: Requires MQTT broker
- @pytest.mark.redis: Requires Redis broker
- @pytest.mark.amqp: Requires AMQP broker (RabbitMQ)

Usage:
    # Quick smoke tests (~30 seconds)
    pytest tests/benchmarks/ -v -m smoke

    # Full benchmarks (~2-5 minutes)
    pytest tests/benchmarks/ -v -m benchmark

    # Specific transport
    pytest tests/benchmarks/test_bench_mqtt.py -v
    pytest tests/benchmarks/test_bench_redis.py -v
    pytest tests/benchmarks/test_bench_amqp.py -v
"""
