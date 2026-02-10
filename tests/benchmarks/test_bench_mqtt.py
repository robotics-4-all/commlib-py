"""
Integration tests for MQTT benchmarks.

These tests validate that MQTT benchmark scripts work correctly with a real broker.
They use warning-based thresholds (not hard assertions) to detect performance regressions
without causing test failures due to system load variations.

Requires:
    - MQTT broker running (e.g., docker run -d -p 1883:1883 eclipse-mosquitto)
    - Set COMMLIB_MQTT_HOST and COMMLIB_MQTT_PORT if not localhost:1883
"""

import pytest
import warnings
import sys
from pathlib import Path

# Add benchmark directory to Python path
benchmark_dir = Path(__file__).parent.parent.parent / "benchmark"
sys.path.insert(0, str(benchmark_dir))

# Import will be done inside tests after ensuring broker availability


@pytest.mark.mqtt
@pytest.mark.integration
@pytest.mark.benchmark
class TestMQTTBenchmarks:
    """Integration tests for MQTT benchmarks."""

    @pytest.mark.smoke
    def test_mqtt_broker_available(self, mqtt_available):
        """Verify MQTT broker is available before running benchmarks."""
        # mqtt_available fixture will skip if broker not available
        assert mqtt_available is True

    @pytest.mark.smoke
    def test_mqtt_benchmark_imports(self, mqtt_available):
        """Verify benchmark script can be imported without errors."""
        try:
            import bench_mqtt_real

            assert hasattr(bench_mqtt_real, "benchmark_mqtt_publish_throughput")
            assert hasattr(bench_mqtt_real, "benchmark_mqtt_pubsub_roundtrip")
            assert hasattr(bench_mqtt_real, "benchmark_mqtt_concurrent_publishers")
        except ImportError as e:
            pytest.fail(f"Failed to import bench_mqtt_real: {e}")

    def test_mqtt_publish_benchmark_exists(self, mqtt_available):
        """Verify MQTT publish benchmark function exists and is callable."""
        import bench_mqtt_real

        # Verify function exists
        assert callable(bench_mqtt_real.benchmark_mqtt_publish_throughput)

        # Note: Not running the actual benchmark in this test
        # Full benchmark execution is tested in manual/CI runs

    def test_mqtt_pubsub_benchmark_exists(self, mqtt_available):
        """Verify MQTT pub/sub benchmark function exists and is callable."""
        import bench_mqtt_real

        # Verify function exists
        assert callable(bench_mqtt_real.benchmark_mqtt_pubsub_roundtrip)

    def test_mqtt_concurrent_benchmark_exists(self, mqtt_available):
        """Verify MQTT concurrent publishers benchmark exists and is callable."""
        import bench_mqtt_real

        # Verify function exists
        assert callable(bench_mqtt_real.benchmark_mqtt_concurrent_publishers)

    @pytest.mark.smoke
    def test_mqtt_publish_smoke(self, mqtt_available):
        """Quick MQTT publish smoke test - 100 messages."""
        from bench_mqtt_real import benchmark_mqtt_publish_throughput

        throughput = benchmark_mqtt_publish_throughput(iterations=100, warmup=10)

        # Warning-based threshold - doesn't fail on slow systems
        if throughput < 1000:
            warnings.warn(
                f"MQTT publish slow: {throughput:.0f} msg/sec (expected >1000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    def test_mqtt_publish_full(self, mqtt_available):
        """Full MQTT publish benchmark - 1000 messages."""
        from bench_mqtt_real import benchmark_mqtt_publish_throughput

        throughput = benchmark_mqtt_publish_throughput(iterations=1000, warmup=100)

        # Warning-based threshold
        if throughput < 5000:
            warnings.warn(
                f"MQTT publish below expected: {throughput:.0f} msg/sec (expected >5000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    @pytest.mark.smoke
    def test_mqtt_pubsub_smoke(self, mqtt_available):
        """Quick MQTT pub/sub smoke test - 50 messages."""
        from bench_mqtt_real import benchmark_mqtt_pubsub_roundtrip

        throughput = benchmark_mqtt_pubsub_roundtrip(iterations=50, warmup=10)

        # Warning-based threshold
        if throughput < 500:
            warnings.warn(
                f"MQTT pub/sub slow: {throughput:.0f} msg/sec (expected >500)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    def test_mqtt_pubsub_full(self, mqtt_available):
        """Full MQTT pub/sub benchmark - 100 messages."""
        from bench_mqtt_real import benchmark_mqtt_pubsub_roundtrip

        throughput = benchmark_mqtt_pubsub_roundtrip(iterations=100, warmup=50)

        # Warning-based threshold
        if throughput < 1000:
            warnings.warn(
                f"MQTT pub/sub below expected: {throughput:.0f} msg/sec (expected >1000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    @pytest.mark.smoke
    def test_mqtt_concurrent_smoke(self, mqtt_available):
        """Quick MQTT concurrent publishers smoke test."""
        from bench_mqtt_real import benchmark_mqtt_concurrent_publishers

        throughput = benchmark_mqtt_concurrent_publishers(
            num_publishers=5, iterations_per_pub=20, warmup=5
        )

        # Warning-based threshold
        if throughput < 1000:
            warnings.warn(
                f"MQTT concurrent slow: {throughput:.0f} msg/sec (expected >1000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"

    def test_mqtt_concurrent_full(self, mqtt_available):
        """Full MQTT concurrent publishers benchmark."""
        from bench_mqtt_real import benchmark_mqtt_concurrent_publishers

        throughput = benchmark_mqtt_concurrent_publishers(
            num_publishers=10, iterations_per_pub=100, warmup=10
        )

        # Warning-based threshold
        if throughput < 5000:
            warnings.warn(
                f"MQTT concurrent below expected: {throughput:.0f} msg/sec (expected >5000)"
            )

        # Basic sanity check
        assert throughput > 0, "Throughput should be positive"
