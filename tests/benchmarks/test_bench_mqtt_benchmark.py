"""
pytest-benchmark integration tests for MQTT benchmarks.

These tests use pytest-benchmark to track performance over time and
compare against historical baselines.

Requires:
    - MQTT broker running (e.g., docker run -d -p 1883:1883 eclipse-mosquitto)
    - pytest-benchmark installed (pip install pytest-benchmark)

Usage:
    # Run with benchmark tracking
    pytest tests/benchmarks/test_bench_mqtt_benchmark.py -v

    # Save baseline
    pytest tests/benchmarks/test_bench_mqtt_benchmark.py --benchmark-save=baseline

    # Compare against baseline
    pytest tests/benchmarks/test_bench_mqtt_benchmark.py --benchmark-compare=baseline

    # Generate histogram
    pytest tests/benchmarks/test_bench_mqtt_benchmark.py --benchmark-histogram
"""

import pytest
import sys
from pathlib import Path

# Add benchmark directory to Python path
benchmark_dir = Path(__file__).parent.parent.parent / "benchmark"
sys.path.insert(0, str(benchmark_dir))


@pytest.mark.mqtt
@pytest.mark.integration
@pytest.mark.benchmark
class TestMQTTBenchmarkTracking:
    """pytest-benchmark integration tests for MQTT performance tracking."""

    def test_mqtt_publish_benchmark(self, mqtt_available, benchmark):
        """Benchmark MQTT publish throughput with tracking."""
        from bench_mqtt_real import benchmark_mqtt_publish_throughput

        # Use benchmark fixture to track performance
        result = benchmark(benchmark_mqtt_publish_throughput, iterations=100, warmup=10)

        # Result is the throughput returned by the function
        assert result > 0, "Throughput should be positive"

        # pytest-benchmark will automatically track:
        # - Min, max, mean, median execution time
        # - Standard deviation
        # - Iterations per second
        # Can compare against previous runs

    def test_mqtt_pubsub_benchmark(self, mqtt_available, benchmark):
        """Benchmark MQTT pub/sub round trip with tracking."""
        from bench_mqtt_real import benchmark_mqtt_pubsub_roundtrip

        result = benchmark(benchmark_mqtt_pubsub_roundtrip, iterations=50, warmup=10)

        assert result > 0, "Throughput should be positive"

    def test_mqtt_concurrent_benchmark(self, mqtt_available, benchmark):
        """Benchmark MQTT concurrent publishers with tracking."""
        from bench_mqtt_real import benchmark_mqtt_concurrent_publishers

        result = benchmark(
            benchmark_mqtt_concurrent_publishers,
            num_publishers=5,
            iterations_per_pub=20,
            warmup=5,
        )

        assert result > 0, "Throughput should be positive"


@pytest.mark.mqtt
@pytest.mark.integration
@pytest.mark.benchmark
class TestMQTTPerformanceRegression:
    """Performance regression tests with explicit thresholds."""

    def test_mqtt_publish_performance_threshold(self, mqtt_available, benchmark):
        """Ensure MQTT publish meets minimum performance threshold."""
        from bench_mqtt_real import benchmark_mqtt_publish_throughput

        result = benchmark.pedantic(
            benchmark_mqtt_publish_throughput,
            kwargs={"iterations": 1000, "warmup": 100},
            iterations=1,
            rounds=3,  # Run 3 rounds for stable measurements
        )

        # Explicit performance requirements
        MIN_THROUGHPUT = 1000  # msg/sec
        assert result > MIN_THROUGHPUT, (
            f"MQTT publish throughput {result:.0f} msg/sec below threshold {MIN_THROUGHPUT}"
        )

    def test_mqtt_pubsub_performance_threshold(self, mqtt_available, benchmark):
        """Ensure MQTT pub/sub meets minimum performance threshold."""
        from bench_mqtt_real import benchmark_mqtt_pubsub_roundtrip

        result = benchmark.pedantic(
            benchmark_mqtt_pubsub_roundtrip,
            kwargs={"iterations": 100, "warmup": 50},
            iterations=1,
            rounds=3,
        )

        MIN_THROUGHPUT = 500  # msg/sec
        assert result > MIN_THROUGHPUT, (
            f"MQTT pub/sub throughput {result:.0f} msg/sec below threshold {MIN_THROUGHPUT}"
        )
